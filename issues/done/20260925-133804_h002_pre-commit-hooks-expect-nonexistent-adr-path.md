# Pre-commit hooks expect non-existent docs/10_adr/adr-index.md path

## Priority
High

## Summary
Fix the path mismatch in pre-commit hooks `adr-invariant-matrix` and `adr-reference-scoped` which hardcode `docs/10_adr/adr-index.md` as the expected ADR index location, while the actual file resides at `docs/adr-index.md`. This causes both hooks to fail every time any markdown file is committed, blocking the entire pre-commit pipeline unless `--no-verify` is used.

## Background
Two local pre-commit hooks invoke Python tools that check ADR infrastructure:
- `adr-invariant-matrix` runs `tools/check_adr_invariant_matrix.py`
- `adr-reference-scoped` runs `tools/check_adr_reference.py`

Both tools contain a hardcoded path check for `docs/10_adr/adr-index.md` (see `check_adr_invariant_matrix.py` line 116 and `check_adr_reference.py` line 163). When the file is not found at that path, each tool emits `"docs/10_adr/adr-index.md not found"` and fails. The actual ADR index file exists at `docs/adr-index.md` (confirmed present on filesystem). The directory `docs/10_adr/` does not exist.

This mismatch has been causing silent CI degradation: developers commit with `--no-verify` to bypass failures, or the hooks fail and get ignored. Neither outcome provides the intended ADR invariant checking.

## Problem
The pre-commit hooks enforce ADR-related invariants but cannot do so because they reference a non-existent file path. Every commit involving markdown files triggers hook failures, making the governance guardrails effectively disabled. This violates the principle that automated checks should block incorrect commits, not silently fail or require workarounds.

## Reason for Change
The hooks are designed to provide real governance value (verifying ADR invariant matrices and scoped ADR references). Fixing the path restores their functionality. Without this fix, the ADR governance layer has no automated enforcement at commit time.

## Implementation Intent
Choose one of two approaches:
1. **Move the file** (minimal disruption): Create `docs/10_adr/` directory, move `docs/adr-index.md` to `docs/10_adr/adr-index.md`. Update any other references to `docs/adr-index.md` across the codebase to point to the new location. This aligns the filesystem with the hooks' expectations.
2. **Update the hooks** (minimal filesystem change): Edit `tools/check_adr_invariant_matrix.py` and `tools/check_adr_reference.py` to use `docs/adr-index.md` instead of `docs/10_adr/adr-index.md`. Update the error messages accordingly.

Approach 1 is preferred if `docs/10_adr/` was the intended canonical ADR directory all along (the naming convention `10_*` matches other numbered doc directories like `00_governance/`). Approach 2 is preferred if `docs/adr-index.md` is the established location and the hooks were written against an outdated assumption.

## Target Files or Areas
- `.pre-commit-config.yaml` (hooks config, may not need changes)
- `tools/check_adr_invariant_matrix.py` (line 116)
- `tools/check_adr_reference.py` (line 163)
- `docs/adr-index.md` (if moving)
- Any other file referencing `docs/adr-index.md` or `docs/10_adr/adr-index.md`

## Required Changes
- Resolve the path mismatch so that exactly one canonical ADR index location exists and all references agree on it
- If moving the file: create `docs/10_adr/`, move `adr-index.md`, update all cross-references
- If updating hooks: change both tool files to reference `docs/adr-index.md`
- Ensure pre-commit hooks pass on a clean commit without `--no-verify`
- Search the entire repository for any other references to either path and unify them

## Constraints
- Do not create duplicate copies of `adr-index.md` — choose one canonical location
- Preserve the existing content of `adr-index.md` regardless of which approach is chosen
- Do not modify the logic of the invariant checks themselves — only the path they resolve
- If creating `docs/10_adr/`, follow the repo's numbering convention for doc directories

## Acceptance Criteria
- [ ] Exactly one canonical ADR index file exists at a known location
- [ ] Both `check_adr_invariant_matrix.py` and `check_adr_reference.py` locate the file without emitting "not found" errors
- [ ] Pre-commit hooks `adr-invariant-matrix` and `adr-reference-scoped` pass on a clean commit
- [ ] No remaining references in the codebase point to the discarded path
- [ ] `uv run python -m tools.check_adr_invariant_matrix` completes successfully
- [ ] `uv run python -m tools.check_adr_reference` completes successfully

## Testing Expectations
- Run both tools directly via `uv run python -m tools.check_adr_invariant_matrix` and `uv run python -m tools.check_adr_reference` and verify zero errors
- Run `pre-commit run adr-invariant-matrix --all-files` and `pre-commit run adr-reference-scoped --all-files` to confirm hooks pass
- Verify no broken cross-references to the old path in any markdown or Python file

## Documentation Impact
If the file is moved (Approach 1), any documentation referencing `docs/adr-index.md` should be updated to the new path. If only hooks are updated (Approach 2), no documentation changes are needed since the file location remains unchanged.

## Out of Scope
- Restructuring the ADR directory layout beyond resolving this specific path mismatch
- Adding new ADR-related hooks or checks
- Modifying the content or schema of `adr-index.md`

## Dependencies
- None

## Unresolved Questions
- Was `docs/10_adr/` ever the intended location and the file was misplaced during a prior reorganization? Or was `docs/adr-index.md` always correct and the hooks were written against a planned-but-unexecuted directory structure?
- Are there other tools or scripts that reference either path?

## AI Implementation Instruction
Step 1: Search the entire repository for references to `docs/adr-index.md` and `docs/10_adr/adr-index.md` using grep. Step 2: Determine which path is more widely referenced — if `docs/10_adr/adr-index.md` appears in more places, choose Approach 1 (move file); otherwise choose Approach 2 (update hooks). Step 3: Execute the chosen approach. Step 4: Run both tools directly and via pre-commit to verify hooks pass. Report which approach was taken and why.

## Traceability
- **Workflow phase**: issue-creator
- **Source finding**: H-2 from governance folder audit (2026-09-25)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-133804
- **Related target files**: tools/check_adr_invariant_matrix.py, tools/check_adr_reference.py, docs/adr-index.md
