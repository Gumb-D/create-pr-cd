# MW DU Local Reference Discovery Guard

`Info/reference` is the local-only holding area for raw DU export inputs used during discovery and review. Original file names must be preserved, and raw Excel/CSV/customer export files in that tree must never be committed to GitHub.

Local discovery work may summarize metadata only, such as file paths, workbook sheet names, row and column counts, and four-layer header fingerprint evidence. Discovery output is for local review only, must be written outside `Info/reference`, and must not include raw customer rows, site lists, or generated workbooks with site-level data in committed repository docs.

This guard step does not approve any MW or DU field mapping, does not promote any profile lifecycle status, and does not change any ECC output path or enable ECC output for non-production profiles. Future mapping approval still requires four-layer header fingerprint evidence and explicit review before any profile can move beyond discovery-only status.
