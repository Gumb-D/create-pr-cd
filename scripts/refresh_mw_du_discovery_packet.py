"""Refresh the full MW DU discovery packet and immediately verify consistency."""
from __future__ import annotations

from pathlib import Path

from build_du_discovery_registry import write_registry_outputs
from build_skill_field_shortlists import write_shortlist_outputs
from build_unresolved_skill_field_review import write_review_outputs
from build_du_structure_grouping import write_grouping_outputs
from build_missing_field_bridge_review import write_bridge_outputs
from build_mw_pair_divergence_review import write_pair_outputs
from build_profile_readiness_review import write_readiness_outputs
from build_profile_action_queue import write_action_queue_outputs
from build_profile_review_matrix import write_review_matrix_outputs
from build_du_export_coverage_review import write_coverage_outputs
from build_all_du_mapping_recommendation_matrix import write_all_du_mapping_review_outputs
from build_profile_transition_review import write_transition_outputs
from build_profile_deprecation_review import write_deprecation_outputs
from build_profile_traceability_audit import write_traceability_outputs
from build_profile_rollback_readiness import write_rollback_outputs
from check_profile_status_consistency import validate_profiles_against_transition_registry
from check_discovery_packet_consistency import validate_live_discovery_packets


def refresh_discovery_packet() -> None:
    profile_root = Path("output/du-20260706-profile")
    profile_paths = [
        Path("config/du_profiles/tx_mini_pr_v1.yaml"),
        Path("config/du_profiles/mw_eos_swap_pr_v1.yaml"),
        Path("config/du_profiles/tx_rollout_2023_pr_v1.yaml"),
        Path("config/du_profiles/jendela_tx_migration_pr_v1.yaml"),
        Path("config/du_profiles/zte_tx_mini_pr_v1.yaml"),
        Path("config/du_profiles/celcomdigi_bau_2023_pr_v1.yaml"),
        Path("config/du_profiles/celcomdigi_bau_2024_pr_v1.yaml"),
        Path("config/du_profiles/celcomdigi_usp_pr_v1.yaml"),
        Path("config/du_profiles/cd_consolidation_2023_decom_pr_v1.yaml"),
        Path("config/du_profiles/cd_consolidation_2023_rollout_pr_v1.yaml"),
    ]
    priority_dirs = [
        profile_root / "A-P202202168750_D002-TX_Mini_Project-TX_Mini_PR_PO_View-20260703160246",
        profile_root / "A-P202211283695_D002-MW_EOS_Swap-MW_EOS_Swap_Rollout-20260703160307",
        profile_root / "A-P202202168750_D002-2023_TX_Rollout-TX_Rollout_PR_PO_View-20260703160446",
        profile_root / "A-P202202168750_D002-Jendela_TX_Migration-Migration_Rollout_TX_-20260703160246",
        profile_root / "A-P202211283695_D002-ZTE_TX_MINI-ZTE_TX_MINI_v1-20260703160312",
        profile_root / "A-P202202168750_D002-2023_Celcomdigi_BAU-2023_Celcomdigi_BAU__TX_-20260703160239",
        profile_root / "A-P202202168750_D002-2024_Celcomdigi_BAU-2024_BAU_Rollout_TX_-20260703160253",
        profile_root / "A-P202202168750_D002-Celcomdigi_USP-Celcomdigi_USP_TX_-20260703160234",
        profile_root / "A-P202202168750_D002-CD_consolidation_2023-CD_2023_Decom_Site-20260703160415",
        profile_root / "A-P202202168750_D002-CD_consolidation_2023-CD_consolidation_2023_Rollout-20260703160351",
    ]

    write_registry_outputs(
        profile_root,
        Path("config/registries/mw_du_model_discovery_registry.yaml"),
        Path("docs/MW_DU_Discovery_Inventory.md"),
    )
    write_shortlist_outputs(
        priority_dirs,
        Path("config/registries/mw_du_priority_skill_field_shortlists.yaml"),
        Path("docs/MW_DU_Priority_Skill_Field_Shortlists.md"),
    )
    write_review_outputs(
        profile_paths,
        Path("config/registries/mw_du_priority_skill_field_shortlists.yaml"),
        Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
        Path("docs/MW_DU_Unresolved_Skill_Field_Review.md"),
    )
    write_grouping_outputs(
        profile_root,
        Path("config/registries/mw_du_structure_grouping_review.yaml"),
        Path("docs/MW_DU_Structure_Grouping_Review.md"),
    )
    write_bridge_outputs(
        Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
        Path("config/registries/mw_du_structure_grouping_review.yaml"),
        Path("config/registries/mw_du_model_discovery_registry.yaml"),
        Path("config/registries/mw_du_missing_field_bridge_review.yaml"),
        Path("docs/MW_DU_Missing_Field_Bridge_Review.md"),
    )
    write_pair_outputs(
        Path("config/du_profiles/mw_eos_swap_pr_v1.yaml"),
        Path("config/du_profiles/zte_tx_mini_pr_v1.yaml"),
        Path("config/registries/mw_du_mw_pair_divergence_review.yaml"),
        Path("docs/MW_DU_MW_Pair_Divergence_Review.md"),
    )
    write_readiness_outputs(
        profile_paths,
        Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
        Path("config/registries/mw_du_missing_field_bridge_review.yaml"),
        Path("config/registries/mw_du_profile_readiness_review.yaml"),
        Path("docs/MW_DU_Profile_Readiness_Review.md"),
    )
    write_action_queue_outputs(
        profile_paths,
        Path("config/registries/mw_du_profile_readiness_review.yaml"),
        Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
        Path("config/registries/mw_du_missing_field_bridge_review.yaml"),
        Path("config/registries/mw_du_profile_action_queue.yaml"),
        Path("docs/MW_DU_Profile_Action_Queue.md"),
    )
    write_review_matrix_outputs(
        Path("config/registries/mw_du_profile_action_queue.yaml"),
        Path("config/registries/mw_du_profile_review_matrix.yaml"),
        Path("docs/MW_DU_Profile_Review_Matrix.md"),
    )
    write_coverage_outputs(
        Path("config/registries/mw_du_model_discovery_registry.yaml"),
        Path("config/registries/mw_du_export_coverage_review.yaml"),
        Path("docs/MW_DU_Export_Coverage_Review.md"),
    )
    write_all_du_mapping_review_outputs(
        profile_root,
        Path("config/registries/mw_du_model_discovery_registry.yaml"),
        Path("config/registries/mw_du_structure_grouping_review.yaml"),
        Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
        Path("config/registries/mw_du_missing_field_bridge_review.yaml"),
        profile_paths,
        Path("output/local_du_reference_inventory.json"),
        Path("docs/MW_DU_All_DU_Discovery_Mapping_Review.md"),
        Path("output/all_du_mapping_recommendation_matrix.json"),
        Path("output/all_du_mapping_recommendation_matrix.md"),
    )
    write_transition_outputs(
        profile_paths,
        Path("config/registries/mw_du_profile_readiness_review.yaml"),
        Path("config/registries/mw_du_profile_transition_review.yaml"),
        Path("docs/MW_DU_Profile_Transition_Review.md"),
    )
    write_deprecation_outputs(
        profile_paths,
        Path("config/registries/mw_du_profile_transition_review.yaml"),
        Path("config/registries/mw_du_profile_deprecation_review.yaml"),
        Path("docs/MW_DU_Profile_Deprecation_Review.md"),
    )
    write_rollback_outputs(
        profile_paths,
        Path("config/registries/mw_du_profile_deprecation_review.yaml"),
        Path("config/registries/mw_du_profile_rollback_readiness.yaml"),
        Path("docs/MW_DU_Profile_Rollback_Readiness.md"),
    )
    write_traceability_outputs(
        profile_paths,
        {
            "discovery": Path("config/registries/mw_du_model_discovery_registry.yaml"),
            "unresolved": Path("config/registries/mw_du_unresolved_skill_field_review.yaml"),
            "bridge": Path("config/registries/mw_du_missing_field_bridge_review.yaml"),
            "readiness": Path("config/registries/mw_du_profile_readiness_review.yaml"),
            "action_queue": Path("config/registries/mw_du_profile_action_queue.yaml"),
            "review_matrix": Path("config/registries/mw_du_profile_review_matrix.yaml"),
            "coverage": Path("config/registries/mw_du_export_coverage_review.yaml"),
            "transition": Path("config/registries/mw_du_profile_transition_review.yaml"),
            "deprecation": Path("config/registries/mw_du_profile_deprecation_review.yaml"),
            "rollback": Path("config/registries/mw_du_profile_rollback_readiness.yaml"),
        },
        Path("config/registries/mw_du_profile_traceability_audit.yaml"),
        Path("docs/MW_DU_Profile_Traceability_Audit.md"),
    )
    validate_profiles_against_transition_registry(
        profile_paths,
        Path("config/registries/mw_du_profile_transition_review.yaml"),
        Path("config/registries/mw_du_profile_deprecation_review.yaml"),
    )
    validate_live_discovery_packets()


def main() -> int:
    refresh_discovery_packet()
    print("Refreshed MW DU discovery packet and verified consistency.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
