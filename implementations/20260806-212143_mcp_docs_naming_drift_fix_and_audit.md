## Goal

Fix incorrect filename/import-path references in MCP documentation and perform a systematic audit of all `docs/04_mcp_*.md` files to ensure consistency with the current repository structure.

## Scope

- **In-Scope**:
  - Update `docs/04_mcp_04_01_web-search-file-read-github.md` line 184: `models.py` → `github_models.py`.
  - Update `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` lines 69, 86, 89, 117: `mdq/server.py` → `mdq/mdq_server.py`.
  - Verify `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md` line 72 (already updated per plan).
  - Audit all 45 `docs/04_mcp_*.md` files for file-path-like strings matching `scripts/mcp_servers/` and `scripts/agent/`.
- **Out-of-Scope**:
  - Fixing additional mismatches found during the audit (file as new issues).
  - Modifying source code.
  - Updating other documentation outside `docs/04_mcp_` scope.

## Assumptions

1. All `docs/04_mcp_*.md` files exist and follow standard Markdown format.
2. The `scripts/mcp_servers/` directory contains the intended module structures.

## Design decisions

- Treat the audit phase as a read-only discovery pass — no fixes during the audit.
- Use grep-based extraction for the audit rather than parsing Markdown ASTs, since we only need string-level comparison.

## Alternatives considered

- Fix all discovered errors in one pass: rejected because it violates the scope boundary and risks unintended changes.
- Use a Python script to parse Markdown links: over-engineered for a simple string-matching task.

## Compatibility considerations

- Import path corrections must reflect the actual module layout under `scripts/mcp_servers/`.
- Line-number references in docs must be verified against the current state of the referenced source files.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If audit report contains false positives, revert the specific doc edits that were made before the audit.
- If anchor links or section headings have changed since the original audit, the report may need regeneration.

## Implementation

### Target file

`docs/04_mcp_04_01_web-search-file-read-github.md`

### Procedure

1. Confirm exact line number using `grep -n "models.py"` in the GitHub context.
2. Replace `models.py` with `github_models.py` on line 184.

### Method

Direct file edit using sed.

### Details

```bash
# Verify line number
grep -n "models.py" docs/04_mcp_04_01_web-search-file-read-github.md

# Apply fix
sed -i '184s/models\.py/github_models.py/' docs/04_mcp_04_01_web-search-file-read-github.md
```

### Target file

`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

### Procedure

1. Verify line numbers for each reference using `grep -n`.
2. Replace `mdq/server.py` with `mdq/mdq_server.py` on lines 69, 86, 89, 117.

### Method

Direct file edit using sed.

### Details

```bash
# Verify line numbers first
grep -n "mdq/server\.py\|mdq_server\.py" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md

# Apply fix for each line
sed -i '69s|mdq/server\.py|mdq/mdq_server.py|' docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
sed -i '86s|mdq/server\.py|mdq/mdq_server.py|' docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
sed -i '89s|mdq/server\.py|mdq/mdq_server.py|' docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
sed -i '117s|mdq/server\.py|mdq/mdq_server.py|' docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
```

### Target file

`docs/04_mcp_05_02_auth-profiles-and-sandboxing.md`

### Procedure

1. Check line 72 for import path correctness.
2. If still incorrect, replace with correct dotted import paths for shell, git, cicd models.

### Method

Verify then direct file edit if needed.

### Details

```bash
# Verify line 72
sed -n '72p' docs/04_mcp_05_02_auth-profiles-and-sandboxing.md
```

Expected correction pattern:
- `shell.models` → `shell_shell_models` (or equivalent prefix)
- `git.models` → `git_git_models` (or equivalent prefix)
- `cicd.models` → `cicd_cicd_models` (or equivalent prefix)

### Target file

Audit report generation

### Procedure

1. Extract all `.py` file-path-like strings from all 45 `docs/04_mcp_*.md` files.
2. Cross-reference extracted paths against `scripts/mcp_servers/` and `scripts/agent/` directory structures.
3. Identify mismatches.
4. Compile audit results into a completeness report.
5. Create follow-up issues for any additional mismatches found.

### Method

Shell-based grep + diff approach.

### Details

```bash
# Extract all .py references from MCP docs
for f in docs/04_mcp_*.md; do
  grep -oP '(?:import|from)\s+\S*\.py' "$f" || true
done > /tmp/extracted_paths.txt

# Compare against actual directory structure
find scripts/mcp_servers -name '*.py' | sort > /tmp/actual_paths.txt

# Find mismatches
comm -23 <(sort /tmp/extracted_paths.txt) <(sort /tmp/actual_paths.txt)
```

### Target file

Verification

### Procedure

1. Run `check_tool_descriptions_sync.py` to ensure no drift.
2. Manually verify string replacements in the three fixed files.
3. Review audit report completeness.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify doc corrections
grep -n "github_models\.py" docs/04_mcp_04_01_web-search-file-read-github.md
grep -n "mdq/mdq_server\.py" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md

# Count processed files
ls docs/04_mcp_* | wc -l

# Run sync check
python scripts/check_tool_descriptions_sync.py
```

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Doc corrections | Manual verification of string replacement | `grep` | Strings match actual file names |
| Audit process | Completeness check | `ls docs/04_mcp_*` vs audit list | All files covered |

## Out of scope

- Source code modifications (`scripts/`).
- Fixes for errors discovered during the audit pass.
- Changes to other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-151925_require.md
- Source plan: plans/20260805-065740_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-212143
- Related target files: docs/04_mcp_04_01_web-search-file-read-github.md, docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md, docs/04_mcp_05_02_auth-profiles-and-sandboxing.md
