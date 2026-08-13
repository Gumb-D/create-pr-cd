"""Pure Operation Backoffice PR business rules for Issue #94."""
from __future__ import annotations

from dataclasses import dataclass

BACKOFFICE_PBOM_LE_800 = "350000592793"
BACKOFFICE_PBOM_GT_800 = "350000592794"
TX_DEFAULT_WARNING = "BACKOFFICE_TX_SOW_DEFAULTED_TO_INTEGRATED"

TX_DECOM_SOWS = frozenset({
    "decom - relo",
    "decom",
    "decom - decom + relo",
    "decom - decom + reroute",
    "decom - reroute",
    "decom - remain",
})
TX_INTEGRATION_SOWS = frozenset({
    "mw re-engineering",
    "mw new link / reroute",
    "mw hardware upgrade",
    "mw remote upgrade",
    "mw parallel link",
    "mw swap",
    "bbu patching",
    "mw idu relocation",
    "mw idu patching",
    "ipran port upgrade",
})
CD_MOCN_SOWS = frozenset({"swap", "modernization", "remote mocn", "gf mocn"})
CD_DECOM_SOWS = frozenset({
    "mocn decomm(dismantle passive)",
    "mocn decomm",
    "decomm",
    "maintain usp mocn(dismantle passive)",
    "decomm, mocn by other vendor",
})

_FIXED_TRIGGERS = {
    "2023 Celcomdigi BAU": ("BAU_2023_CUTOVER", "microwave_tx_cutover_date"),
    "2024 Celcomdigi BAU": ("BAU_2024_CUTOVER", "microwave_tx_cutover_date"),
    "Celcomdigi USP": ("USP_CUTOVER", "microwave_tx_cutover_date"),
    "TX Mini Project": ("TX_MINI_INTEGRATION", "tx_integrated_actual_end"),
    "Jendela TX Migration": ("JENDELA_CUTOVER", "cut_over_actual_end"),
    "MW EOS Swap": ("MW_EOS_INTEGRATION", "site_integrated_actual_end"),
    "ZTE TX MINI": ("ZTE_TX_MINI_INTEGRATION", "site_integrated_actual_end"),
}


@dataclass(frozen=True)
class BackofficeTriggerDecision:
    status: str
    event_code: str | None = None
    trigger_field: str | None = None
    warning_codes: tuple[str, ...] = ()
    reason_code: str | None = None


def _norm(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def resolve_backoffice_trigger(du_model_name: str, tx_sow: str) -> BackofficeTriggerDecision:
    du = _norm(du_model_name)
    sow = _norm(tx_sow).casefold()

    fixed = _FIXED_TRIGGERS.get(du)
    if fixed:
        return BackofficeTriggerDecision("RESOLVED", fixed[0], fixed[1])

    if du == "2023 TX Rollout":
        if sow in TX_DECOM_SOWS:
            return BackofficeTriggerDecision("RESOLVED", "TX_ROLLOUT_DECOM", "l1_approved_actual_end")
        if sow in TX_INTEGRATION_SOWS:
            return BackofficeTriggerDecision("RESOLVED", "TX_ROLLOUT_INTEGRATION", "tx_integrated_actual_end")
        return BackofficeTriggerDecision(
            "RESOLVED",
            "TX_ROLLOUT_INTEGRATION",
            "tx_integrated_actual_end",
            (TX_DEFAULT_WARNING,),
        )

    if du.casefold() == "cd consolidation 2023":
        if sow in CD_MOCN_SOWS:
            return BackofficeTriggerDecision("RESOLVED", "CD_CONSOLIDATION_MOCN", "mocn_actual_end")
        if sow in CD_DECOM_SOWS:
            return BackofficeTriggerDecision("RESOLVED", "CD_CONSOLIDATION_DECOM", "decom_actual_end")
        return BackofficeTriggerDecision("REVIEW_REQUIRED", reason_code="BACKOFFICE_CD_SOW_NOT_APPROVED")

    return BackofficeTriggerDecision("REVIEW_REQUIRED", reason_code="BACKOFFICE_DU_MODEL_NOT_APPROVED")


def select_backoffice_pbom(monthly_hops: int) -> str:
    if monthly_hops < 0:
        raise ValueError("monthly_hops must be non-negative")
    return BACKOFFICE_PBOM_LE_800 if monthly_hops <= 800 else BACKOFFICE_PBOM_GT_800

