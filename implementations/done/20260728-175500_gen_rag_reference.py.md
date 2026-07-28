## Goal

Resolve NC-010 and NC-014 by updating `tools/gen_rag_reference.py` to stop targeting the deleted `docs/03_rag_05_configuration_and_operations.md`, keeping only the CLI-help auto-generation as a real write target, and removing the config-table auto-write path entirely.

## Scope

**In-Scope:**
- In `tools/gen_rag_reference.py`: remove `OPS_DOC` constant; add `CLI_HELP_DOC` pointing to `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md`
- Update `GUARD_START`/`GUARD_END` constants to CLI-help-specific marker strings
- Update `main()` to always write CLI-help guarded block into `CLI_HELP_DOC`; compute config-table output only for `--dry-run` display, never write to any file
- Update module docstring to reflect new single-target behavior
- Update the existing guard block in `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md` to use the new marker text (part of this implementation phase)
- Delete the stale config-table AUTO-GENERATED block from `docs/03_rag_05_7-rag-index-consistency-checks.md` (follow-up documentation edit)

**Out-of-Scope:**
- Editing NC-010/NC-014 entries in `docs/00_governance_07_needs-confirmation-inventory.md` — handled in a later governance update phase
- Restructuring `config/*.toml` files or adding description metadata to TOML keys
- Changing `check_rag_consistency()` / `/db consistency` behavior
- Making `gen_rag_reference.py` part of CI/pre-commit

## Assumptions

1. Option A (automate CLI-help, drop config-table write) is the correct resolution — confirmed by static comparison showing CLI-help content matches current argparse definitions, while config-table output cannot produce quality comparable to `docs/03_rag_05_1-configuration-reference.md`.
2. No other code references `OPS_DOC` or `03_rag_05_configuration_and_operations.md` — confirmed via `git grep`.
3. `requires/20260727-135740_require.md` (NC-014) is covered by this same plan and does not need its own cycle.
4. The two `AUTO-GENERATED` guard blocks are in different doc files, so using distinct marker strings per section prevents cross-match issues.

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether CLI-help output still matches live `--help` text of three ingestion scripts | Resolved by static comparison of argparse definitions vs. existing doc blocks — exact match found | False |

No blocking unknowns remain.

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `tools/gen_rag_reference.py` — replace `OPS_DOC` with `CLI_HELP_DOC`; update guard markers; update `main()` write logic; update module docstring
  - `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md` (lines 84-115) — update guard block marker text; remove "Needs confirmation" prose at line 86
  - `docs/03_rag_05_7-rag-index-consistency-checks.md` (lines 94-140ish) — delete config-table guard block entirely
  - `docs/00_governance_07_needs-confirmation-inventory.md` — NC-010/NC-014 Status updates (later phase)
- **Blast Radius:** Low — `tools/gen_rag_reference.py` has exactly one caller pattern: manual invocation; no other script imports it.
- **Risk Metrics:** `tools/gen_rag_reference.py` churn: 1 commit total (creation), never modified since. Both doc files have moderate churn but are actively maintained.
- **Deploy Impact:** None — standalone dev-time doc tool, not part of deploy copy list.

## Implementation Steps

1. **Phase 1: Preparation / Analysis**
   - [ ] Re-confirm no other file references `OPS_DOC` or `03_rag_05_configuration_and_operations.md`: `git grep -n "03_rag_05_configuration_and_operations\|OPS_DOC"`
   - [ ] Re-verify CLI-help block in `docs/03_rag_05_8-...md` still textually matches current argparse definitions

2. **Phase 2: Core Logic Implementation**
   - [ ] In `tools/gen_rag_reference.py`: remove `OPS_DOC` constant (line 22); add `CLI_HELP_DOC = Path("docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md")`
   - [ ] Update `GUARD_START` to `"<!-- AUTO-GENERATED: gen_rag_reference.py cli-help -->"` and `GUARD_END` to `"<!-- END AUTO-GENERATED -->"` (keep GUARD_END as-is, change GUARD_START)
   - [ ] Update `main()`:
     - Always compute `cli_section` via `generate_cli_help()` and write it into `CLI_HELP_DOC` guarded by the new markers
     - Compute `generate_config_table()` output only for `--dry-run` display (print alongside CLI-help when `--dry-run` is set, clearly labeled as informational/dry-run-only)
     - Never write config-table output to any file
   - [ ] Update module docstring (lines 1-7) to reflect new single-target, CLI-help-only write behavior
   - [ ] Update guard block in `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md` to use the new `GUARD_START` marker text (`<!-- AUTO-GENERATED: gen_rag_reference.py cli-help -->`)
   - [ ] Delete the config-table guard block from `docs/03_rag_05_7-rag-index-consistency-checks.md` (the AUTO-GENERATED block that duplicates `docs/03_rag_05_1-configuration-reference.md`)

3. **Phase 3: Deployment & Verification**
   - [ ] Run `python tools/gen_rag_reference.py --dry-run` and confirm it prints CLI-help section without error
   - [ ] Run `python tools/gen_rag_reference.py` for real against a scratch copy and diff `docs/03_rag_05_8-...md` to confirm only the guarded CLI-help block changed
   - [ ] Confirm `git grep -n "03_rag_05_configuration_and_operations"` returns no hits
   - [ ] Run `uv run ruff check tools/gen_rag_reference.py` to confirm no lint regressions
   - [ ] No deploy step required

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/gen_rag_reference.py` | Manual/dry-run smoke test | `python tools/gen_rag_reference.py --dry-run` | Prints CLI-help guarded block content with no `FileNotFoundError`; exits 0 |
| `tools/gen_rag_reference.py` | Real-run diff test in scratch copy | `python tools/gen_rag_reference.py` then `git diff docs/03_rag_05_8-...md` | Only the guarded CLI-help block changes; no other lines touched |
| `docs/03_rag_05_7-rag-index-consistency-checks.md` | Confirm tool does not touch this file | `git status` after real run | File shows no diff |
| Repo-wide | Stale-reference regression check | `git grep -n "03_rag_05_configuration_and_operations"` | No matches |
| `tools/gen_rag_reference.py` | Lint/type check | `uv run ruff check tools/gen_rag_reference.py` | 0 errors |

## Risks

- **Risk**: Retargeting `CLI_HELP_DOC` requires a guard-marker text change in `docs/03_rag_05_8-...md` — **Mitigation**: That edit belongs to the implementation phase; this plan specifies the marker text for consistency between tool code and doc file changes.
- **Risk**: Dropping automated config-table generation could let `docs/03_rag_05_1-configuration-reference.md` silently drift from `config/*.toml` — **Mitigation**: keep `generate_config_table()` available under `--dry-run` so a human can periodically diff its raw key list against `03_rag_05_1`.
- **Risk**: Environment could not execute ingestion scripts' `--help` live during verification — **Mitigation**: Implementation Phase 3 requires running `python tools/gen_rag_reference.py --dry-run` in an environment with dependencies installed before considering the change complete.
