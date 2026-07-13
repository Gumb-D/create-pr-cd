# 2023 Celcomdigi BAU Audit Execution Correction

This correction is binding for execution of:

- `docs/superpowers/specs/2026-07-13-celcomdigi-bau-2023-cross-view-evidence-audit-design.md`
- `docs/superpowers/plans/2026-07-13-celcomdigi-bau-2023-cross-view-evidence-audit.md`

It supersedes only the branch-checkout and tracked-sensitive-path preflight/final-verification wording. All other design and plan requirements remain unchanged.

## 1. Local Tracking Branch Creation

The documentation branch exists on `origin`, but a local branch may not exist yet. After confirming the current working tree is clean, use this PowerShell flow:

```powershell
$Branch = "docs/celcomdigi-bau-2023-evidence-audit-design"

git fetch origin --prune

$LocalBranch = git branch --list $Branch
if ($LocalBranch) {
    git switch $Branch
} else {
    git switch --track -c $Branch "origin/$Branch"
}

git pull --ff-only origin $Branch
```

Creating the local tracking branch from the existing remote branch is expected and permitted. Do not recreate or force-update the remote branch.

## 2. Existing Tracked `Info/reference` Assets

The repository intentionally contains these pre-existing tracked reference/runtime assets:

```text
Info/reference/SABAH_SARAWAK_BOUNDARY_DATA.md
Info/reference/SIMPLE_PACKING_UNRESOLVED_DECISION_PACK.md
Info/reference/geography_mapping.json
Info/reference/sabah_sarawak_adm2.geojson
```

They are not local iEPMS customer export workbooks and must not be removed, untracked, rewritten, or treated as an audit blocker.

Use this exact allowlist check:

```powershell
$AllowedTrackedReference = @(
    "Info/reference/SABAH_SARAWAK_BOUNDARY_DATA.md",
    "Info/reference/SIMPLE_PACKING_UNRESOLVED_DECISION_PACK.md",
    "Info/reference/geography_mapping.json",
    "Info/reference/sabah_sarawak_adm2.geojson"
)

$TrackedReference = @(git ls-files "Info/reference/**")
$UnexpectedTrackedReference = @(
    $TrackedReference | Where-Object { $_ -notin $AllowedTrackedReference }
)
if ($UnexpectedTrackedReference) {
    $UnexpectedTrackedReference
    throw "Unexpected tracked file exists under Info/reference."
}

$TrackedCustomerExports = @(
    $TrackedReference | Where-Object {
        [System.IO.Path]::GetExtension($_).ToLowerInvariant() -in ".xlsx", ".xlsm", ".xls", ".csv"
    }
)
if ($TrackedCustomerExports) {
    $TrackedCustomerExports
    throw "A customer export file is tracked under Info/reference."
}

$TrackedOutput = @(git ls-files "output/**")
if ($TrackedOutput) {
    $TrackedOutput
    throw "Generated output is tracked."
}
```

The safety requirement is that no additional `Info/reference` file becomes tracked, no customer workbook/CSV is tracked there, no `output` file is tracked, and the existing allowlisted files remain unchanged.

## 3. Baseline and Final Comparison

Before audit execution, record:

```powershell
$TrackedReferenceBefore = @(git ls-files "Info/reference/**" | Sort-Object)
$TrackedFilesBefore = @(git ls-files | Sort-Object)
$TrackedReferenceHashesBefore = @{}
foreach ($Path in $TrackedReferenceBefore) {
    $TrackedReferenceHashesBefore[$Path] = (Get-FileHash $Path -Algorithm SHA256).Hash
}
```

After audit execution, verify:

```powershell
$Dirty = git status --short
if ($Dirty) {
    $Dirty
    throw "Audit changed tracked repository state."
}

$TrackedReferenceAfter = @(git ls-files "Info/reference/**" | Sort-Object)
$TrackedFilesAfter = @(git ls-files | Sort-Object)

if (Compare-Object $TrackedReferenceBefore $TrackedReferenceAfter) {
    throw "Tracked Info/reference file set changed during audit."
}
if (Compare-Object $TrackedFilesBefore $TrackedFilesAfter) {
    throw "Tracked repository file set changed during audit."
}

foreach ($Path in $TrackedReferenceBefore) {
    $AfterHash = (Get-FileHash $Path -Algorithm SHA256).Hash
    if ($AfterHash -ne $TrackedReferenceHashesBefore[$Path]) {
        throw "Tracked reference asset changed during audit: $Path"
    }
}

$TrackedOutput = @(git ls-files "output/**")
if ($TrackedOutput) {
    $TrackedOutput
    throw "Generated output became tracked."
}
```

## 4. Source Documents

The approved spec and implementation plan are available on the remote documentation branch. They must be read after switching to the branch. Their absence on an unrelated local branch is not a blocker.

## 5. Safety Ruling

Proceed with the local-only evidence audit after the corrected preflight passes. Do not modify tracked files during execution. Do not commit or push anything generated under `output/` or any local customer export under `Info/reference/`.
