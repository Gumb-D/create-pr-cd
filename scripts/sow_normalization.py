"""Controlled Tx SOW normalization backed by the approved canonical SOW registry.

Fail-closed by design: a raw SOW value that is blank, unknown, or ruled
REVIEW_REQUIRED never yields a PR-eligible canonical SOW. This module records
the value-level business ruling of 2026-07-07; it does not enable ECC output.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

DEFAULT_REGISTRY_PATH = Path("config/registries/canonical_sow_registry.yaml")

CLASSIFICATION_PR_TRIGGER = "PR_TRIGGER"
CLASSIFICATION_NO_PR_TRIGGER = "NO_PR_TRIGGER"
CLASSIFICATION_REVIEW_REQUIRED = "REVIEW_REQUIRED"
CLASSIFICATION_MISSING = "MISSING"

_VALID_CLASSIFICATIONS = {
    CLASSIFICATION_PR_TRIGGER,
    CLASSIFICATION_NO_PR_TRIGGER,
    CLASSIFICATION_REVIEW_REQUIRED,
}


def _normalize_key(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    if not text or text.lower() in {"nan", "<na>"}:
        return ""
    return " ".join(text.split()).upper()


def load_canonical_sow_registry(path: Path = DEFAULT_REGISTRY_PATH) -> Dict[str, Any]:
    """Load and structurally validate the registry; reject inconsistent content."""
    registry = json.loads(Path(path).read_text(encoding="utf-8"))
    if registry.get("registry_type") != "canonical_sow_registry":
        raise ValueError("Not a canonical SOW registry.")
    entries = registry.get("entries", [])
    seen: Dict[str, str] = {}
    for entry in entries:
        key = _normalize_key(entry.get("raw_value"))
        canonical = str(entry.get("canonical_sow", "")).strip()
        classification = entry.get("classification")
        if not key or not canonical:
            raise ValueError(f"Registry entry with blank raw/canonical value: {entry!r}")
        if classification not in _VALID_CLASSIFICATIONS:
            raise ValueError(f"Invalid classification for {entry.get('raw_value')!r}: {classification!r}")
        if key in seen:
            raise ValueError(f"Duplicate normalized raw value in registry: {entry.get('raw_value')!r}")
        if _normalize_key(canonical) != _normalize_key(entry.get("raw_value")):
            raise ValueError(
                f"Non-identity canonical value for {entry.get('raw_value')!r}; identity normalization "
                "is the only approved rule (JJ 2026-07-07)."
            )
        seen[key] = canonical
    return registry


def normalize_tx_sow(raw_value: Any, registry: Mapping[str, Any]) -> Dict[str, Optional[str]]:
    """Classify one raw Tx SOW value against the approved registry.

    Returns canonical_sow, classification, and normalization_status. Only
    PR_TRIGGER results carry normalization_status APPROVED; everything else is
    fail-closed for PR generation.
    """
    key = _normalize_key(raw_value)
    if not key:
        return {
            "canonical_sow": "",
            "classification": CLASSIFICATION_MISSING,
            "normalization_status": CLASSIFICATION_REVIEW_REQUIRED,
        }
    for entry in registry.get("entries", []):
        if _normalize_key(entry.get("raw_value")) == key:
            classification = entry["classification"]
            return {
                "canonical_sow": str(entry["canonical_sow"]).strip(),
                "classification": classification,
                "normalization_status": "APPROVED"
                if classification == CLASSIFICATION_PR_TRIGGER
                else CLASSIFICATION_REVIEW_REQUIRED
                if classification == CLASSIFICATION_REVIEW_REQUIRED
                else "APPROVED_NO_OUTPUT",
            }
    return {
        "canonical_sow": "",
        "classification": CLASSIFICATION_REVIEW_REQUIRED,
        "normalization_status": CLASSIFICATION_REVIEW_REQUIRED,
    }
