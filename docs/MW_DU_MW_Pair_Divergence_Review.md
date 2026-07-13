# MW Pair Divergence Review

Discovery-only comparison between the MW EOS Swap and ZTE TX MINI DRAFT profiles. This is review guidance, not approval for shared production mappings.

## mw_eos_swap_pr_v1 vs zte_tx_mini_pr_v1

- Left profile version: `0.1.0`
- Right profile version: `0.1.0`
- Left observed header hash: `46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a`
- Right observed header hash: `a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810`
- Shared missing required fields: None

### `antenna_size_fe`

- Comparison status: `DIFFERENT_SELECTED_SOURCE`
- Left selected header: `MW Antenna Size FE`
- Right selected header: `MW Antenna Size FE`
- Reason: The two MW profiles currently select different source columns for the same canonical field.

### `antenna_size_ne`

- Comparison status: `DIFFERENT_SELECTED_SOURCE`
- Left selected header: `MW Antenna Size NE`
- Right selected header: `MW Antenna Size NE`
- Reason: The two MW profiles currently select different source columns for the same canonical field.

### `boq_configuration`

- Comparison status: `BOTH_MISSING_OPTIONAL`
- Left selected header: `None`
- Right selected header: `None`
- Reason: Neither profile currently selects a source candidate for this non-required field.

### `du_key`

- Comparison status: `MATCHING_SELECTED_SOURCE`
- Left selected header: `du code`
- Right selected header: `du code`
- Reason: Both MW-family DRAFT profiles currently select the same exact four-layer fingerprint for this canonical field.

### `existing_ti_pr_status`

- Comparison status: `ONE_SIDE_MISSING`
- Left selected header: `Subcon PR - TI`
- Right selected header: `None`
- Reason: One profile has a selected source candidate while the other still lacks one.

### `existing_tss_pr_status`

- Comparison status: `ONE_SIDE_MISSING`
- Left selected header: `Subcon PR - TSS`
- Right selected header: `None`
- Reason: One profile has a selected source candidate while the other still lacks one.

### `fe_sow_details`

- Comparison status: `BOTH_MISSING_OPTIONAL`
- Left selected header: `None`
- Right selected header: `None`
- Reason: Neither profile currently selects a source candidate for this non-required field.

### `latitude`

- Comparison status: `BOTH_MISSING_OPTIONAL`
- Left selected header: `None`
- Right selected header: `None`
- Reason: Neither profile currently selects a source candidate for this non-required field.

### `longitude`

- Comparison status: `BOTH_MISSING_OPTIONAL`
- Left selected header: `None`
- Right selected header: `None`
- Reason: Neither profile currently selects a source candidate for this non-required field.

### `ne_sow_details`

- Comparison status: `BOTH_MISSING_OPTIONAL`
- Left selected header: `None`
- Right selected header: `None`
- Reason: Neither profile currently selects a source candidate for this non-required field.

### `region`

- Comparison status: `MATCHING_SELECTED_SOURCE`
- Left selected header: `region`
- Right selected header: `region`
- Reason: Both MW-family DRAFT profiles currently select the same exact four-layer fingerprint for this canonical field.

### `site_code`

- Comparison status: `DIFFERENT_SELECTED_SOURCE`
- Left selected header: `customer site code`
- Right selected header: `customer site code`
- Reason: The two MW profiles currently select different source columns for the same canonical field.

### `site_name`

- Comparison status: `MATCHING_SELECTED_SOURCE`
- Left selected header: `customer site name`
- Right selected header: `customer site name`
- Reason: Both MW-family DRAFT profiles currently select the same exact four-layer fingerprint for this canonical field.

### `state`

- Comparison status: `BOTH_MISSING_OPTIONAL`
- Left selected header: `None`
- Right selected header: `None`
- Reason: Neither profile currently selects a source candidate for this non-required field.

### `subcontractor_planning`

- Comparison status: `MATCHING_SELECTED_SOURCE`
- Left selected header: `Subcon - Planning`
- Right selected header: `Subcon - Planning`
- Reason: Both MW-family DRAFT profiles currently select the same exact four-layer fingerprint for this canonical field.

### `subcontractor_ti`

- Comparison status: `DIFFERENT_SELECTED_SOURCE`
- Left selected header: `Subcon - TI`
- Right selected header: `Subcon - TI`
- Reason: The two MW profiles currently select different source columns for the same canonical field.

### `subcontractor_tss`

- Comparison status: `ONE_SIDE_MISSING`
- Left selected header: `Subcon - TSS`
- Right selected header: `None`
- Reason: One profile has a selected source candidate while the other still lacks one.

### `tx_sow_details`

- Comparison status: `MATCHING_SELECTED_SOURCE`
- Left selected header: `TX SOW Details`
- Right selected header: `TX SOW Details`
- Reason: Both MW-family DRAFT profiles currently select the same exact four-layer fingerprint for this canonical field.

### `tx_sow_raw`

- Comparison status: `DIFFERENT_SELECTED_SOURCE`
- Left selected header: `Microwave Tx SOW-1`
- Right selected header: `Microwave Tx SOW`
- Reason: The two MW profiles currently select different source columns for the same canonical field.

### `tx_upgrade_scope_raw`

- Comparison status: `BOTH_MISSING_OPTIONAL`
- Left selected header: `None`
- Right selected header: `None`
- Reason: Neither profile currently selects a source candidate for this non-required field.

