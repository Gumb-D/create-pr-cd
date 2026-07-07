# MW DU Discovery Inventory

This inventory is discovery-only metadata derived from profiler artifacts. It does not approve any DU profile, field mapping, or header hash for production use.

| Project Key | DU Model | DU Model ID | View Label | View ID | Header Hash | Profile ID | PR Input Status |
|---|---|---|---|---|---|---|---|
| Malaysia_CelcomDigi_Project | 2023 Celcomdigi BAU | `8296022438223590261` | 2023 Celcomdigi BAU_(TX) | `6611960521271999255` | `77fa728c7a4105d9062378a999228cf24575e56e82ee97bce3ab9be630d7b313` | celcomdigi_bau_2023_pr_v1 | PR_INPUT_QUARANTINED |
| Malaysia_CelcomDigi_Project | 2023 TX Rollout | `1027190858144623081` | TX Rollout PR_PO View | `8530399820526021092` | `8aab4c2da2dc133e0a65b9203c62e6db1ebeb30430f9f63f5c5de1673703c320` | tx_rollout_2023_pr_v1 | PR_INPUT_QUARANTINED |
| Malaysia_CelcomDigi_Project | 2024 Celcomdigi BAU | `7278317398457076992` | 2024 BAU Rollout (TX) | `1090541706000906451` | `b3677457da49e5de484976c3fdb7ad6f5dc19055f5339ec616407f5cbde89a86` | celcomdigi_bau_2024_pr_v1 | PR_INPUT_QUARANTINED |
| Malaysia_CelcomDigi_Project | CD consolidation 2023 | `8359047522524182050` | CD 2023 Decom Site | `702960351133798763` | `b86cbc349db66154324092c843593137e83908c3b4b55c09305d6cf6046c7a16` | cd_consolidation_2023_decom_pr_v1 | PR_INPUT_QUARANTINED |
| Malaysia_CelcomDigi_Project | CD consolidation 2023 | `8359047522524182050` | CD consolidation 2023 Rollout | `8359047522524230651` | `d16d92debc1cc59aacd548a100d407462c7733f1894453b195abc9d3072ec9a1` | cd_consolidation_2023_rollout_pr_v1 | PR_INPUT_QUARANTINED |
| Malaysia_CelcomDigi_Project | Celcomdigi USP | `3765504705612341090` | Celcomdigi USP (TX) | `703232142435130905` | `79084b19ff9685eb74e3cfb4c07af8c48de871328884618e63969a623fb384cf` | celcomdigi_usp_pr_v1 | PR_INPUT_QUARANTINED |
| Malaysia_CelcomDigi_Project | Jendela TX Migration | `4972593269368006257` | Migration Rollout (TX) | `4026888666764910245` | `904f30b6c4278c0d4c20d7898f4ad3d805e9d2ca2167499ea4e9418b1a16ffe3` | jendela_tx_migration_pr_v1 | PR_INPUT_QUARANTINED |
| Malaysia_CelcomDigi_Project | TX Mini Project | `4188808420049567786` | TX Mini PR_PO View | `2477626672974883536` | `167645031ac3ebb90da748c42fe3188ef4a67604eb0ce2c3df446df1142b5221` | tx_mini_pr_v1 | PR_INPUT_QUARANTINED |
| CelcomDigi_MW | MW EOS Swap | `5440935430300168497` | MW EOS Swap Rollout | `7476572371505372260` | `46e50e91db7b29f9e875fabfffdd170c75739aaa39b19542a42eecf1e3d88a1a` | mw_eos_swap_pr_v1 | PR_INPUT_QUARANTINED |
| CelcomDigi_MW | ZTE TX MINI | `8638668101234290847` | ZTE TX MINI v1 | `2279585426760368522` | `a1b2f9d28ca32e38c7dbd0064602a30b9727548dfce1f1f583a961781c9be810` | zte_tx_mini_pr_v1 | PR_INPUT_QUARANTINED |

## Notes

- `PR_INPUT_QUARANTINED` here means discovery-only; it is not a production approval state.
- `Profile ID` is populated only where the repository already contains a corresponding profile file.
- The observed header hashes came from local profiler runs against external source files and remain subject to sanitization and business approval.
