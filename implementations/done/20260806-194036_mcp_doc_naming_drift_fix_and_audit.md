## Goal

Fix three confirmed filename/import-path errors in MCP documentation and conduct a comprehensive audit of all 45 `docs/04_mcp_*.md` files to identify and report any further naming-drift discrepancies.

## Scope

- **In-Scope**:
  - Correction of `docs/04_mcp_04_01_web-search-file-read-github.md:184` (`models.py` → `github_models.py`).
  - Correction of `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` (line 89 path and lines 69, 86, 117 bare names).
  - Correction of `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md:72` (three incorrect dotted import paths).
  - Mechanical audit of all 45 `docs/04_mcp_*.md` files for non-existent file/module references.
  - Filing new issues for any additional mismatches discovered during the audit.
- **Out-of-Scope**:
  - Direct fixing of any mismatches found during the audit.
  - Updating the docstring in `scripts/mcp_servers/github/github_models.py`.
  - Modifying any source code.

## Assumptions

1. The three identified errors are genuine inaccuracies.
2. The "naming-drift" pattern is consistent across the remaining MCP documentation files.
3. The set of 45 `docs/04_mcp_*.md` files represents the full relevant audit scope.

## Design decisions

- Use targeted edits for the three known errors rather than rewriting entire sections.
- Use regex-based extraction (`grep -noE`) for the mechanical audit — systematic and reproducible.
- File new issues for audit-discovered mismatches rather than fixing them directly — keeps the audit objective separate from remediation.

## Alternatives considered

- Fix all mismatches found during audit immediately: rejected because it conflates discovery with remediation; better to report first.
- Delete the audit step entirely after fixing the three known errors: rejected because the naming-drift pattern may extend beyond these three cases.

## Compatibility considerations

- Readers who previously relied on the incorrect paths will now see corrected references.
- New issues filed during the audit will provide visibility into additional problems without disrupting current workflows.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If the audit discovers new mismatches that require source code changes, those should be handled separately.
- If the three primary corrections are reverted, the audit findings remain valid and independent.

## Implementation

### Phase 1: Preparation

Re-verify the 3 specific error locations and contents in the target files to ensure they haven't shifted.

```bash
# Verify error locations
sed -n '182,186p' docs/04_mcp_04_01_web-search-file-read-github.md
sed -n '87,91p' docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
sed -n '67,74p' docs/04_mcp_05_02_auth-profiles-and-sandboxing.md
```

### Phase 2: Core Logic Implementation

#### Step 2a: Fix `docs/04_mcp_04_01_web-search-file-read-github.md:184`

Replace `models.py` with `github_models.py`.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Locate the exact line
grep -n "models\.py" docs/04_mcp_04_01_web-search-file-read-github.md
```

After verification, replace the reference from `models.py` to `github_models.py`.

#### Step 2b: Fix `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

Update line 89 path and lines 69, 86, 117 bare names.

### Method

Direct file edit.

### Details

```bash
# Locate the specific lines
sed -n '67,70p' docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
sed -n '87,91p' docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
sed -n '115,119p' docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
```

After verification:
- Update line 89 path to the correct relative path.
- Replace bare names on lines 69, 86, 117 with their fully qualified counterparts.

#### Step 2c: Fix `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md:72`

Replace three incorrect dotted import paths.

### Method

Direct file edit.

### Details

```bash
# Locate the import paths
sed -n '70,75p' docs/04_mcp_05_02_auth-profiles-and-sandboxing.md
```

After verification, replace the three incorrect dotted import paths with their correct equivalents.

### Phase 3: Deployment & Verification

#### Step 3a: Conduct mechanical audit of all `docs/04_mcp_*.md` files

Use `grep -noE '[A-Za-z0-9_./]+\.py|mcp_servers(\.[a-z_]+)+' docs/04_mcp_*.md` to extract potential paths.

### Method

Regex extraction + filesystem validation.

### Details

```bash
# Extract all potential Python file/module references
grep -noE '[A-Za-z0-9_./]+\.py|mcp_servers(\.[a-z_]+)+' docs/04_mcp_*.md > /tmp/mcp_doc_paths.txt

# Validate each extracted path against the filesystem
while IFS=: read -r file line match; do
    if ! test -f "/home/sugimoto/llmagent/$match"; then
        echo "MISSING: $file:$line -> $match"
    fi
done < /tmp/mcp_doc_paths.txt
```

#### Step 3b: Consolidate audit findings

Review the output from the audit step. Identify which references point to non-existent files/modules.

#### Step 3c: Create new issues in `issues/` for any mismatches found

For each mismatch found during the audit, create a new issue file in `issues/` following the standard issue format.

#### Step 3d: Verify all 3 primary fixes are correct and no regressions were introduced in the docs

```bash
# Verify the three primary fixes
grep -n "github_models\.py" docs/04_mcp_04_01_web-search-file-read-github.md
grep -n "correct_path\|qualified_name" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
grep -n "correct_import_path" docs/04_mcp_05_02_auth-profiles-and-sandboxing.md
```

## Validation Plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/` | Docs folder | No linting errors |
| Content | `grep` | Target files | Corrected strings present |
| Audit | Manual/Script | All 45 docs | Completeness report produced |

## Out of scope

- Source code modifications (`scripts/`).
- Direct fixing of mismatches found during the audit.
- Modifications to other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-151925_require.md
- Source plan: plans/20260804-235046_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-194036
- Related target files: docs/04_mcp_04_01_web-search-file-read-github.md, docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md, docs/04_mcp_05_02_auth-profiles-and-sandboxing.md, all docs/04_mcp_*.md
