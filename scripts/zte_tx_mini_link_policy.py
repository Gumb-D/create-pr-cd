"""JJ-approved 2026-11-05 ZTE TX MINI TI combined-link policy."""
from typing import Any, Mapping

PROFILE_ID = "zte_tx_mini_pr_v1"
COMBINED_SOW = "MW NEW LINK / REROUTE"

def applies(profile_id: Any, scope: Any, sow: Any) -> bool:
    return (str(profile_id) == PROFILE_ID and str(scope).upper() == "TI"
            and " ".join(str(sow or "").split()).upper() in {"MW NEW LINK", COMBINED_SOW})

def record_applies(record: Mapping[str, Any], scope: Any) -> bool:
    return applies(record.get("validation", {}).get("profile_id"), scope,
                   record.get("pr_context", {}).get("tx_sow_normalized")
                   or record.get("pr_context", {}).get("tx_sow_raw"))
