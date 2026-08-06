## Goal

Correct confirmed filename and import path errors in MCP documentation and conduct a comprehensive audit of all MCP-related documentation to identify and report further instances of naming-drift caused by per-server module renaming.

## Scope

- **In-Scope**:
  - Update `docs/04_mcp_04_01_web-search-file-read-github.md` to use `github_models.py` instead of `models.py`.
  - Update `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` to use `mdq_server.py` (correcting both bare names and line-numbered references).
  - Update `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md` to use correct dotted import paths for shell, git, and cicd models.
  - Perform a mechanical audit of all 45 `docs/04_mcp_*.md` files for incorrect `.py` filenames and `mcp_servers.*` import paths.
  - Generate a completeness report of audit findings.
- **Out-of-Scope**:
  - Direct fixes for any errors discovered during the audit pass (these will be reported via new issues).
  - Modifications to any source code (`.py` files).
  - Modification of existing issue/requirement documents.

## Assumptions

1. The current filesystem structure and module names (prefixed versions) are authoritative.
2. All 45 files matching `docs/04_mcp_*.md` constitute the full set of MCP documentation to be audited.

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

1. Replace `models.py` with `github_models.py` in the GitHub model reference.

### Method

Direct file edit using sed or manual editing.

### Details

- Search for `models.py` in the context of GitHub model references.
- Replace with `github_models.py`.

### Target file

`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

### Procedure

1. Verify `scripts/mcp_servers/mdq/mdq_server.py` line number for `attach_auth_middleware` call.
2. Replace `models.py` with `mdq_server.py` in MDQ server references.
3. Correct line-numbered references to point to the correct locations.

### Method

Verify line numbers first, then direct file edit.

### Details

- Check `scripts/mcp_servers/mdq/mdq_server.py` for `attach_auth_middleware` call location.
- Replace bare `models.py` references with `mdq_server.py`.
- Update any line-number annotations in the doc to match actual positions.

### Target file

`docs/04_mcp_05_02_auth-profiles-and-sandboxing.md`

### Procedure

1. Replace incorrect dotted import paths for shell, git, and cicd models with the correct prefixed versions.

### Method

Direct file edit.

### Details

- Shell model: `shell.models` → `shell_shell_models` (or equivalent prefix).
- Git model: `git.models` → `git_git_models` (or equivalent prefix).
- CICD model: `cicd.models` → `cicd_cicd_models` (or equivalent prefix).

### Target file

Audit report generation

### Procedure

1. Run automated extraction of file-path-like strings from all 45 `docs/04_mcp_*.md` files.
2. Cross-reference extracted paths against `scripts/mcp_servers/` directory structure.
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

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Doc corrections | Manual verification of text changes | `grep` / `cat` | Strings match expected corrected values |
| Audit process | Verification of tool output completeness | `wc -l` / `ls` | All 45 files processed |

## Out of scope

- Source code modifications (`scripts/`).
- Fixes for errors discovered during the audit pass.
- Changes to other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-120000_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-192130
- Related target files: docs/04_mcp_04_01_web-search-file-read-github.md, docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md, docs/04_mcp_05_02_auth-profiles-and-sandboxing.md
