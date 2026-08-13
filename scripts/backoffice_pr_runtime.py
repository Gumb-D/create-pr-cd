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
        sow = _text(context.get("tx_sow_raw") or context.get("tx_sow_normalized"))
        decision = resolve_backoffice_trigger(du_model, sow)
        if decision.status != "RESOLVED":
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
            _ignored(record, partitions, "BACKOFFICE_OUTSIDE_BILLING_MONTH", f"Trigger month {trigger_month} is outside requested billing month {billing_month}.")
            continue

        service = _service_for_date(service_registry, trigger_date)
        if service is None:
            _review(record, partitions, "BACKOFFICE_SERVICE_CONTRACT_NOT_EFFECTIVE", "Exactly one valid Backoffice provider/contract must be effective on the trigger date.")
            continue

        key = duplicate_key(du_code, event_code)
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

    frozen = tracker_snapshot.month_pbom.get(billing_month)
    issue_type = "SUPPLEMENTARY" if frozen else "MAIN"
    pbom = frozen or select_backoffice_pbom(len(partitions["candidates"]))
    for record in partitions["candidates"]:
        record["backoffice_selection"]["pbom_code"] = pbom
        record["backoffice_selection"]["issue_type"] = issue_type

    partitions["summary"] = {
        "billing_month": billing_month,
        "issue_type": issue_type,
        "pbom_code": pbom,
        "eligible_hops": len(partitions["candidates"]),
        "duplicate_blocked": len(partitions["duplicates"]),
        "not_generated": len(partitions["ignored"]),
        "review_required": len(partitions["review_required"]),
        "tier_source": "TRACKER_MAIN_FREEZE" if frozen else "CURRENT_MONTH_ENTITLEMENT",
    }
    return partitions
