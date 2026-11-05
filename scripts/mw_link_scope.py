"""Approved TI new-link/reroute split; no missing evidence is defaulted."""
from __future__ import annotations
import re
from pr_helpers import optional_cell_text, normalize_ti_sow
from antenna_evidence_resolver import resolve_installation_antenna_evidence

DETAIL_FIELDS = {
    "BOQ Configuration": "BOQ Configuration Mapping Status",
    "TX SOW Details": "TX SOW Details Mapping Status",
    "NE SOW Details": "NE SOW Details Mapping Status",
    "FE SOW Details": "FE SOW Details Mapping Status",
    "TX Upgrade Scope": "TX Upgrade Scope Mapping Status",
}
DIRECT_FIELDS = {
    "MW Config Antenna Size NE": "Antenna Size NE Mapping Status",
    "MW Config Antenna Size FE": "Antenna Size FE Mapping Status",
}
COMBINED = re.compile(r"^MW NEW LINK\s*/\s*REROUTE$")
UNCERTAIN = re.compile(r"\b(?:possible|possibly|maybe|if|pending|tbc|confirm|proposed alternative)\b|\?", re.I)
NO_DECOM = re.compile(r"\b(?:no|without)\s+(?:MW\s+)?(?:dismantl(?:e|ing)|decom(?:missioning)?|removal)\b|\b(?:dismantl(?:e|ing)|decom(?:missioning)?)\s+(?:is\s+)?not\s+required\b", re.I)
DECOM = re.compile(r"\b(?:dismantl(?:e|ed|ing)|decom(?:mission(?:ed|ing)?)?|remov(?:e|ed|ing|al))\b", re.I)
MW_OBJECT = re.compile(r"\b(?:MW|microwave|antennas?|dish(?:es)?|links?)\b", re.I)
NEGATED = re.compile(r"\b(?:not|no|without|retain|retained|reuse|reused|do not|don't)\b", re.I)
NEW_ONLY = re.compile(r"\b(?:MW\s+)?new\s+link\s+only\b", re.I)


def approved_row(row):
    clean = dict(row)
    from zte_tx_mini_link_policy import applies
    if applies(row.get('DU Profile ID'), 'TI', row.get('Tx SOW')):
        clean['BOQ Configuration'] = ''
        clean['BOQ Configuration Mapping Status'] = 'NOT_APPLICABLE'
    if optional_cell_text(row.get('Antenna Evidence Governance')).upper() == 'CANONICAL_MAPPING_STATUS':
        for field, status in {**DETAIL_FIELDS, **DIRECT_FIELDS}.items():
            if optional_cell_text(row.get(status)).upper() != 'APPROVED':
                clean[field] = ''
    return clean


def clauses(text):
    # Decimal points are not clause separators. New and old antenna evidence
    # must not borrow intent across a different action in the same sentence.
    return [x.strip() for x in re.split(r'[;\r\n]|\.(?=\s|$)|\band\s+(?=(?:install|new|dismantle|decom|remove|retain|reuse)\b)', text, flags=re.I) if x.strip()]


def _classify_link_scope(row):
    clean = approved_row(row)
    sow = normalize_ti_sow(clean.get('Tx SOW'))
    combined = bool(COMBINED.fullmatch(sow))
    explicit_new = sow in {'MW NEW LINK', 'MW NEW LINK ONLY'}
    explicit_reroute = sow == 'MW REROUTE'
    evidence = []
    new_only = explicit_new
    reroute = explicit_reroute
    uncertain = False
    for field in DETAIL_FIELDS:
        for clause in clauses(optional_cell_text(clean.get(field))):
            # Repeating a combined dropdown label is not a scope decision.
            actionable = bool(NO_DECOM.search(clause) or NEW_ONLY.search(clause) or
                              (DECOM.search(clause) and MW_OBJECT.search(clause)) or
                              re.fullmatch(r'(?:MW\s+)?reroute(?:\s+only)?', clause, re.I))
            if not actionable:
                continue
            if UNCERTAIN.search(clause) or re.search(r"\b(?:do not|don't|must not|should not)\b", clause, re.I):
                uncertain = True
                evidence.append({'source': field, 'decision': 'UNCERTAIN'})
                continue
            if NO_DECOM.search(clause) or NEW_ONLY.search(clause):
                remainder = NO_DECOM.sub('', NEW_ONLY.sub('', clause))
                if NEGATED.search(remainder):
                    uncertain = True
                if DECOM.search(remainder) and MW_OBJECT.search(remainder):
                    uncertain = True
                new_only = True
                evidence.append({'source': field, 'decision': 'NEW_LINK_ONLY'})
            elif (DECOM.search(clause) and MW_OBJECT.search(clause)) or re.fullmatch(r'(?:MW\s+)?reroute(?:\s+only)?', clause, re.I):
                if NEGATED.search(clause):
                    uncertain = True
                else:
                    reroute = True
                    evidence.append({'source': field, 'decision': 'REROUTE'})
    if uncertain or (new_only and reroute) or not (combined or explicit_new or explicit_reroute):
        status = 'REVIEW_REQUIRED'
    elif reroute:
        status = 'REROUTE'
    elif new_only:
        status = 'NEW_LINK_ONLY'
    else:
        status = 'REVIEW_REQUIRED'
    return {'status': status, 'reason': None if status != 'REVIEW_REQUIRED' else 'MW_LINK_SCOPE_UNRESOLVED', 'evidence': evidence}


def classify_link_scope(row):
    from zte_tx_mini_link_policy import applies
    result = _classify_link_scope(row)
    if not applies(row.get('DU Profile ID'), 'TI', row.get('Tx SOW')):
        return result
    # One business category. Still reject contradictory/uncertain work evidence.
    if result['status'] == 'REVIEW_REQUIRED' and result['evidence']:
        return result
    return {'status': 'COMBINED_LINK', 'reason': None,
            'include_dismantle': result['status'] == 'REROUTE',
            'evidence': result['evidence']}


def installation_evidence(row):
    result = resolve_installation_antenna_evidence(approved_row(row))
    size = result.get('selected_size') if result.get('status') in {'RESOLVED', 'RESOLVED_COMMON'} else None
    return {'size': size, 'source': result.get('group_source'), 'confidence': 'HIGH' if size else 'LOW',
            'reason': result.get('reason_code') if result.get('status') == 'CONFLICT' else None,
            'evidence': result.get('evidence', [])}


def dismantle_evidence(row):
    """Require explicit old/dismantle diameter AND count; new config/NLOS is not old-size evidence."""
    clean = approved_row(row)
    sizes, counts, evidence = set(), set(), []
    for field in DETAIL_FIELDS:
        for clause in clauses(optional_cell_text(clean.get(field))):
            if not DECOM.search(clause) or not re.search(r'\b(?:antennas?|dish(?:es)?)\b', clause, re.I):
                continue
            if UNCERTAIN.search(clause) or NEGATED.search(clause):
                return {'size': None, 'count': None, 'reason': 'MW_REROUTE_DECOM_ANTENNA_SIZE_AMBIGUOUS', 'source': field}
            # Do not read installation targets or cable lengths as old diameter.
            if re.search(r'\b(?:install|new|target|proposed|cable|waveguide)\b', clause, re.I):
                return {'size': None, 'count': None, 'reason': 'MW_REROUTE_DECOM_ANTENNA_SIZE_AMBIGUOUS', 'source': field}
            found = []
            patterns = [r'(?<![\w.])(\d+(?:[.,]\d+)?)\s*m(?:etres?|eters?)?\s+(?:antennas?|dish(?:es)?)\b',
                        r'\b(?:antennas?|dish(?:es)?)(?:\s+(?:size|diameter))?\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*m(?:etres?|eters?)?\b']
            for pattern in patterns:
                found.extend(float(x.replace(',', '.')) for x in re.findall(pattern, clause, re.I))
            if any(not 0 < x <= 5 for x in found):
                return {'size': None, 'count': None, 'reason': 'MW_REROUTE_DECOM_ANTENNA_SIZE_AMBIGUOUS', 'source': field}
            sizes.update(found)
            counts.update(int(x) for x in re.findall(r'(?<![\w.])(\d+)\s*(?:x\s*)?(?:old\s+|existing\s+)?(?:MW\s+)?(?:antenna|dish)(?:s|es)?\b', clause, re.I))
            if found:
                evidence.append({'source': field, 'role': 'DISMANTLE'})
    if len(sizes) != 1:
        reason = 'MW_REROUTE_DECOM_ANTENNA_SIZE_MISSING' if not sizes else 'MW_REROUTE_DECOM_ANTENNA_SIZE_AMBIGUOUS'
        return {'size': None, 'count': None, 'reason': reason, 'source': None}
    if len(counts) != 1 or next(iter(counts)) not in {2, 4}:
        return {'size': next(iter(sizes)), 'count': None, 'reason': 'MW_REROUTE_DECOM_ANTENNA_COUNT_UNRESOLVED', 'source': None}
    return {'size': next(iter(sizes)), 'count': next(iter(counts)), 'reason': None, 'source': 'APPROVED_DISMANTLE_EVIDENCE', 'evidence': evidence}


def model_antenna_count(item):
    text = str(item.get('Description', ''))
    found = set(int(x) for x in re.findall(r'(?<![\w.])(\d+)\s+antenna(?:s)?\b', text, re.I))
    return next(iter(found)) if len(found) == 1 else None
