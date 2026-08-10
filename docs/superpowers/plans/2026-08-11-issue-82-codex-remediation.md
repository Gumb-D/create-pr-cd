# Issue #82 Codex P1 Remediation

First Codex review of PR #83 (reviewed head `bb86356751`) identified three blocking defects:

1. canonical optional antenna evidence reached the renderer without `source_evidence.mapping_status`;
2. common `TX SOW Details` fallback could overwrite a larger resolved endpoint size;
3. broad numeric context could misclassify GHz/IP/cable values as antenna sizes.

Remediation contract:

- propagate mapping status for every antenna evidence source from canonical record to renderer input;
- in canonical mode, consume only `APPROVED` sources;
- preserve the legacy direct-generator input contract when canonical governance metadata is absent;
- approve only the MW EOS optional antenna fields supported by Human UAT Issue #50 (`MW Antenna Size NE`, `MW Antenna Size FE`, `TX SOW Details`), without promoting TX Rollout Issue #80 evidence;
- select the largest supported value across already-resolved endpoint evidence plus any valid common fallback;
- require antenna-specific numeric context for broad `TX SOW Details` parsing and reject unrelated cable length, GHz/MHz, rate, and IP-like values;
- keep missing/unapproved/unsupported evidence fail-closed.

Regression coverage is in:

- `tests/test_issue_82_antenna_false_positive.py`
- `tests/test_issue_82_codex_review.py`
- existing Issue #82 and related TI/reroute/safety suites.
