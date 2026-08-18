"""Operation Backoffice monthly entitlement runtime for Issue #94."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping

from backoffice_pr_rules import TX_DEFAULT_WARNING, resolve_backoffice_trigger, select_backoffice_pbom
from backoffice_tracker import TrackerIndex, duplicate_key
from canonical_site_validator import PR_INPUT_READY
from pr_safety_controls import set_generation_decision

BACKOFFICE_SCOPE = "BACKOFFICE"


def _text(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def _delivery_unit_code(record: Mapping[str, Any]) -> str:
    site = record.get("site", {})
    context = record.get("pr_context", {})
    return _text(site.get("du_key") or context.get("delivery_unit_code")).upper()


def _parse_trigger_date(value: object) -> date | None:
    if value is None or _text(value) == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _text(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(text)


def _month(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def load_service_registry(path: Path) -> dict[str, Any]:
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        raise ValueError(f"Invalid Backoffice service registry {path}: {error}") from error
    services = payload.get("services")
    if not isinstance(services, list):
        raise ValueError("Backoffice service registry must contain a services list.")
    return payload


def _service_for_date(registry: Mapping[str, Any], trigger_date: date) -> dict[str, str] | None:
    matches: list[dict[str, str]] = []
    for item in registry.get("services", []):
        if not isinstance(item, Mapping):
            continue
        try:
            start = date.fromisoformat(_text(item.get("effective_from")))
            raw_end = _text(item.get("effective_to"))
            end = date.fromisoformat(raw_end) if raw_end else None
        except ValueError:
            continue
        if trigger_date < start or (end is not None and trigger_date > end):
            continue
        subcontractor = _text(item.get("subcontractor"))
        contract = _text(item.get("contract_number"))
        if subcontractor and contract:
            matches.append({
                "effective_from": start.isoformat(),
                "effective_to": end.isoformat() if end else "",
                "subcontractor": subcontractor,
                "contract_number": contract,
            })
    if len(matches) != 1:
        return None
    return matches[0]


def _review(record: dict[str, Any], partitions: dict[str, list[dict[str, Any]]], code: str, reason: str) -> None:
    set_generation_decision(record, "REVIEW_REQUIRED", code, reason)
    partitions["review_required"].append(record)


def _ignored(record: dict[str, Any], partitions: dict[str, list[dict[str, Any]]], code: str, reason: str) -> None:
    set_generation_decision(record, "IGNORED", code, reason)
    partitions["ignored"].append(record)


def build_backoffice_entitlements(
    records: list[dict[str, Any]],
    billing_month: str,
    tracker_snapshot: TrackerIndex,
    service_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Resolve one-hop Backoffice entitlement for one requested calendar month."""
    try:
        requested = datetime.strptime(str(billing_month), "%Y-%m")
    except ValueError as error:
        raise ValueError("billing_month must use YYYY-MM") from error
    if requested.strftime("%Y-%m") != str(billing_month):
        raise ValueError("billing_month must use YYYY-MM")

    partitions: dict[str, list[dict[str, Any]]] = {
        "candidates": [],
        "duplicates": [],
        "ignored": [],
        "review_required": [],
    }
    accepted_current_run_keys: set[tuple[str, str]] = set()

    for record in records:
        if record.get("validation", {}).get("pr_input_classification") != PR_INPUT_READY:
            _review(record, partitions, "CANONICAL_INPUT_NOT_READY", "The canonical record is not classified PR_INPUT_READY for Backoffice generation.")
            continue

        du_code = _delivery_unit_code(record)
        if not du_code:
            _review(record, partitions, "BACKOFFICE_DELIVERY_UNIT_CODE_MISSING", "Delivery Unit Code is required for Backoffice duplicate identity.")
            continue

        identity = record.get("identity", {})
        context = record.get("pr_context", {})
        du_model = _text(identity.get("du_model_name"))
        if du_model == "CD consolidation 2023":
            sow = _text(context.get("backoffice_sow_raw"))
        else:
            sow = _text(context.get("tx_sow_raw") or context.get("tx_sow_normalized"))
        decision = resolve_backoffice_trigger(du_model, sow)
        if decision.status != "RESOLVED":
            if du_model == "CD consolidation 2023":
                possible_dates = []
                invalid_fields = []
                for field_name in ("mocn_actual_end", "decom_actual_end"):
                    raw_possible = context.get(field_name)
                    if not _text(raw_possible):
                        continue
                    try:
                        parsed_possible = _parse_trigger_date(raw_possible)
                    except ValueError:
                        invalid_fields.append(field_name)
                        continue
                    if parsed_possible is not None:
                        possible_dates.append(parsed_possible)
                if invalid_fields:
                    _review(
                        record, partitions, "BACKOFFICE_TRIGGER_DATE_INVALID",
                        "CD consolidation contains an invalid governed milestone date while SOW classification is unresolved.",
                    )
                    continue
                if not possible_dates:
                    _ignored(
                        record, partitions, "NOT_YET_ELIGIBLE",
                        "Neither governed CD consolidation Backoffice milestone has an Actual End Date.",
                    )
                    continue
                possible_months = {_month(value) for value in possible_dates}
                if billing_month not in possible_months:
                    _ignored(
                        record, partitions, "BACKOFFICE_OUTSIDE_BILLING_MONTH",
                        "Completed governed CD consolidation milestones are outside the requested billing month.",
                    )
                    continue
            _review(record, partitions, _text(decision.reason_code) or "BACKOFFICE_TRIGGER_UNRESOLVED", "Backoffice trigger could not be resolved from the approved DU/SOW rules.")
            continue

        event_code = _text(decision.event_code)
        trigger_field = _text(decision.trigger_field)
        warnings = list(decision.warning_codes)
        raw_trigger = context.get(trigger_field)

        if du_model == "2023 TX Rollout" and trigger_field == "l1_approved_actual_end" and not _text(raw_trigger):
            fallback = context.get("tx_integrated_actual_end")
            if _text(fallback):
                event_code = "TX_ROLLOUT_INTEGRATION"
                trigger_field = "tx_integrated_actual_end"
                raw_trigger = fallback
                if TX_DEFAULT_WARNING not in warnings:
                    warnings.append(TX_DEFAULT_WARNING)

        if not _text(raw_trigger):
            if du_model == "CD consolidation 2023":
                alternate_field = "decom_actual_end" if trigger_field == "mocn_actual_end" else "mocn_actual_end"
                alternate_raw = context.get(alternate_field)
                if _text(alternate_raw):
                    try:
                        alternate_date = _parse_trigger_date(alternate_raw)
                    except ValueError:
                        _review(
                            record, partitions, "BACKOFFICE_TRIGGER_DATE_INVALID",
                            f"Alternate governed CD milestone {alternate_field} does not contain a valid date.",
                        )
                        continue
                    if alternate_date is not None and _month(alternate_date) == billing_month:
                        _review(
                            record, partitions, "BACKOFFICE_CD_MILESTONE_CONFLICT",
                            "The SOW-selected CD milestone is blank while the alternate governed MOCN/Decom milestone is complete in the requested billing month.",
                        )
                        continue
            _ignored(record, partitions, "NOT_YET_ELIGIBLE", "The approved Backoffice trigger Actual End Date is blank.")
            continue
        try:
            trigger_date = _parse_trigger_date(raw_trigger)
        except ValueError:
            _review(record, partitions, "BACKOFFICE_TRIGGER_DATE_INVALID", f"Backoffice trigger field {trigger_field} does not contain a valid date.")
            continue
        assert trigger_date is not None

        trigger_month = _month(trigger_date)
        if trigger_month != billing_month:
            if du_model == "CD consolidation 2023":
                alternate_field = "decom_actual_end" if trigger_field == "mocn_actual_end" else "mocn_actual_end"
                alternate_raw = context.get(alternate_field)
                if _text(alternate_raw):
                    try:
                        alternate_date = _parse_trigger_date(alternate_raw)
                    except ValueError:
                        _review(
                            record, partitions, "BACKOFFICE_TRIGGER_DATE_INVALID",
                            f"Alternate governed CD milestone {alternate_field} does not contain a valid date.",
                        )
                        continue
                    if alternate_date is not None and _month(alternate_date) == billing_month:
                        _review(
                            record, partitions, "BACKOFFICE_CD_MILESTONE_CONFLICT",
                            "The SOW-selected CD milestone is outside the requested billing month while the alternate governed MOCN/Decom milestone is complete in the requested billing month.",
                        )
                        continue
            _ignored(record, partitions, "BACKOFFICE_OUTSIDE_BILLING_MONTH", f"Trigger month {trigger_month} is outside requested billing month {billing_month}.")
            continue

        service = _service_for_date(service_registry, trigger_date)
        if service is None:
            _review(record, partitions, "BACKOFFICE_SERVICE_CONTRACT_NOT_EFFECTIVE", "Exactly one valid Backoffice provider/contract must be effective on the trigger date.")
            continue

        key = duplicate_key(du_code, event_code)
        if key in accepted_current_run_keys:
            _review(
                record,
                partitions,
                "BACKOFFICE_CURRENT_RUN_DUPLICATE_ENTITLEMENT",
                "The current Backoffice input contains the same Delivery Unit Code + canonical event more than once.",
            )
            continue
        accepted_current_run_keys.add(key)
        if key in tracker_snapshot.duplicate_keys:
            set_generation_decision(record, "DUPLICATE_BLOCKED", "BACKOFFICE_TRACKER_DUPLICATE", "The Delivery Unit Code + canonical Backoffice event is already present in the authoritative tracker.")
            partitions["duplicates"].append(record)
            continue

        record["backoffice_selection"] = {
            "event_code": event_code,
            "trigger_field": trigger_field,
            "trigger_date": trigger_date.isoformat(),
            "billing_month": billing_month,
            "pbom_code": "",
            "quantity": 1,
            "unit": "Hop",
            "subcontractor": service["subcontractor"],
            "contract_number": service["contract_number"],
            "warnings": warnings,
        }
        record["approved_contract"] = {
            "scope": BACKOFFICE_SCOPE,
            "subcontractor": service["subcontractor"],
            "contract_number": service["contract_number"],
        }
        set_generation_decision(record, "CANDIDATE", "ELIGIBLE", "Backoffice entitlement passed trigger, month, contract and duplicate controls.")
        partitions["candidates"].append(record)

    historical_month_keys = set(tracker_snapshot.month_entitlement_keys.get(billing_month, frozenset()))
    new_candidate_keys = {
        duplicate_key(record["site"]["du_key"], record["backoffice_selection"]["event_code"])
        for record in partitions["candidates"]
    }
    known_month_keys = historical_month_keys | new_candidate_keys

    frozen = tracker_snapshot.month_pbom.get(billing_month)
    issue_type = "SUPPLEMENTARY" if frozen else "MAIN"
    pbom = frozen or select_backoffice_pbom(len(known_month_keys))
    for record in partitions["candidates"]:
        record["backoffice_selection"]["pbom_code"] = pbom
        record["backoffice_selection"]["issue_type"] = issue_type

    partitions["summary"] = {
        "billing_month": billing_month,
        "issue_type": issue_type,
        "pbom_code": pbom,
        "eligible_hops": len(known_month_keys),
        "already_issued_hops": len(historical_month_keys),
        "duplicate_blocked": len(partitions["duplicates"]),
        "not_generated": len(partitions["ignored"]),
        "review_required": len(partitions["review_required"]),
        "tier_source": "TRACKER_MAIN_FREEZE" if frozen else "CURRENT_MONTH_ENTITLEMENT",
    }
    return partitions
