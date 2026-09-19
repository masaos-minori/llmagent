## Goal
Add 6 new mechanical-content check functions to `tools/check_docs_content_policy.py`,
extract a shared guard-detection helper, apply it to every guard-aware check
(existing and new), and register everything in `main()` (`REQ-001`, `REQ-002`,
`REQ-003`, `REQ-004`).

## Scope
In scope: this one file's `check_*` functions, a new shared guard-detection
helper, and `main()`'s registration list. Out of scope: any change to existing
check functions' behavior beyond the guard-detection fix; promoting `GV-021` to
blocking; a decorator-based registry pattern (explicitly forbidden by the source
issue).

## Assumptions
- File structure unchanged since the Plan was written — re-confirmed: 5 existing
  `check_*` functions (`check_full_file_tree` 77-111, `check_per_file_description`
  114-131, `check_index_table` 134-151, `check_location_mapping` 154-171,
  `check_literal_port_number` 174-204), `main()` at line 207, guard bug at lines
  180/183, file is 222 lines total.
- The guard-format mismatch is still live: `"<!-- AUTO-GENERATED -->" in "<!--
  AUTO-GENERATED: gen_mcp_reference.py port-tool-reference -->"` still evaluates
  to `False` (string containment, not prefix match) — re-verified by inspection.
- 2 pre-existing tests in `tests/tools/test_check_docs_content_policy.py` (lines
  109-132) use the synthetic bare-string `<!-- AUTO-GENERATED -->` format and
  must keep passing after this fix (a prefix-based check still matches the bare
  string, since it starts with the same prefix) — see seq 03's document for the
  test-side implication.

## Design decisions
Extract a single shared helper, e.g. `_is_guard_start(line: str) -> bool:
return line.strip().startswith("<!-- AUTO-GENERATED")` and a matching
`_is_guard_end(line: str) -> bool: return line.strip().startswith("<!-- END
AUTO-GENERATED")`, then replace `check_literal_port_number`'s two exact-string
comparisons (lines 180, 183) with calls to these helpers, and add the same
guard-tracking loop shape (an `in_auto_generated` boolean, set/cleared by the
helpers, `continue` while inside) to `check_full_file_tree`,
`check_index_table`, and `check_location_mapping`, which currently have no
guard-awareness at all. Follow the existing module's plain-function pattern (no
decorator registry, per the source issue's explicit prohibition).

## Alternatives considered
A regex-based guard matcher (`re.compile(r"^<!--\s*AUTO-GENERATED\b")`) was
considered instead of `str.startswith`, but rejected as unnecessary — the guard
comment format is a fixed, tool-emitted string prefix, not user-authored
free-form text, so a prefix check is simpler and equally correct.

## Implementation
### Target file
tools/check_docs_content_policy.py

### Procedure
1. Add `_is_guard_start()`/`_is_guard_end()` module-level helper functions,
   placed near the existing regex constants (after line 54).
2. Rewrite `check_literal_port_number`'s guard-tracking (lines 178-187) to call
   these helpers instead of the exact-string comparisons at lines 180/183.
3. Add the same guard-tracking loop shape to `check_full_file_tree`,
   `check_index_table`, and `check_location_mapping` — each gains an
   `in_auto_generated` local, set by `_is_guard_start()`, cleared by
   `_is_guard_end()`, skipping (`continue`) matched lines while inside.
4. Add 6 new `check_*(files: list[DocFile]) -> list[Issue]` functions, each
   using the same guard-tracking pattern from the start (not retrofitted):
   `check_default_value_restatement`, `check_field_type_table`,
   `check_config_file_inventory_table`, `check_cli_command_enumeration`,
   `check_environment_setup_sequence`, `check_ddl_schema_block`.
5. Append each new function's call to `main()` (after line 215's
   `check_literal_port_number` call).

### Method
Direct code edit (`Edit` tool), following the existing file's exact
function-per-category + `main()`-registration pattern — no new dependencies, no
refactor beyond what Procedure states.

### Details
- `_is_guard_start(line)`/`_is_guard_end(line)`: pure functions, no state; each
  check function keeps its own local `in_auto_generated` boolean (mirrors the
  existing `check_literal_port_number` pattern) — do not share mutable state
  across check functions.
- `check_default_value_restatement`: flag a line matching a "default: <value>"
  or "デフォルト: <value>" pattern outside a table row and outside a guarded
  block — true positive: `` `max_retry` defaults to 3 (see config.py) `` outside
  any table; false positive to avoid: the same phrase inside a Design-rationale
  sentence explaining *why* a default was chosen (retain-category content per
  `docs/00_governance_02_documentation-metadata.md`'s Guidelines).
- `check_field_type_table`: flag a Markdown table header containing both a
  `Field`/`Key` column and a `Type`/`Default` column, not requiring
  Function/Method/Class/Signature/Description wording (the gap
  `check_index_table`'s narrower regex leaves) — true positive: a config
  dataclass field-list table; false positive to avoid: a short table with fewer
  than ~4 data rows (a "legitimately short, non-mechanical table," per the
  source issue's own false-positive caution).
- `check_config_file_inventory_table`: flag a table or bullet list mapping a
  config file/key to its location (e.g. this Plan's own "- `field` — description"
  bullet pattern, or a table titled "Configuration Fields"/"Config Reference").
- `check_cli_command_enumeration`: flag 3+ consecutive fenced ` ```bash ` blocks
  under a heading matching "CLI"/"Commands"/"Usage" (avoid flagging a single
  illustrative command example, which is retain-category).
- `check_environment_setup_sequence`: flag an ordered list (3+ items) under a
  heading matching "Setup"/"Installation"/"Getting Started"/"Environment".
- `check_ddl_schema_block`: flag a ` ```sql ` fenced block containing `CREATE
  TABLE`/`CREATE INDEX` (schema restatement), corpus-wide (not limited to
  `docs/databases/*.md` — the source Plan's own re-baseline finding
  (`plans/done/20260919-104214_plan.md`) confirmed SQL fences also appear in
  `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` and
  `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`).
- Every new function's `Issue` message must cite `skills/DESIGN.md` Docs content
  policy — remove, matching the existing 5 checks' message format exactly (e.g.
  `"... — see skills/DESIGN.md Docs content policy — remove"`).
- Keep every new check's severity `WARNING` — do not introduce a `BLOCKING`
  severity or change `GV-021`'s report-only behavior.

## Compatibility considerations
Existing checks' true-positive/false-positive behavior for content OUTSIDE a
guarded block must be unchanged — the guard-detection fix only WIDENS what is
recognized as a guarded block (exact string → prefix match), it does not narrow
detection outside one. `tools/generate_reference_table.py`'s guard-comment
constants (`GUARD_START_MCP`, `GUARD_START_DEPLOYMENT`, `GUARD_END`) are read
only, never modified by this row.

## Security considerations
No security-sensitive code path is touched (a documentation linter, no
credentials, no network/file-write beyond stdout reporting). Run `uv run bandit
tools/check_docs_content_policy.py` per Validation plan regardless, per
`routing.md` "Adding a new tool"'s standard tool-validation sequence.

## Rollback considerations
`git checkout -- tools/check_docs_content_policy.py` fully reverts this row
independently of the other 2 rows in this pass (the doc-checks-matrix update and
the test additions reference this file's behavior but do not import
internals that would break on revert, beyond the tests themselves needing the
new functions to exist — a revert here should be paired with reverting seq 03's
new test additions in the same rollback unit).

## Validation plan
- `uv run ruff format tools/check_docs_content_policy.py`
- `uv run ruff check tools/check_docs_content_policy.py --fix`, then `uv run
  ruff check tools/check_docs_content_policy.py` to confirm clean
- `uv run mypy tools/check_docs_content_policy.py`
- `uv run bandit tools/check_docs_content_policy.py`
- `uv run pytest tests/tools/test_check_docs_content_policy.py -v` (depends on
  seq 03's new tests existing in the same cycle)
- `uv run python tools/check_docs_content_policy.py` against the full `docs/`
  tree — confirm exit reflects only WARNING findings, no crash, and note the
  new finding count for follow-up scoping (out of scope to fix here, per source
  issue).

## Completion criteria
- All 6 new check functions exist, are registered in `main()`, and each passes a
  constructed true-positive and false-positive test (seq 03).
- `check_literal_port_number`, `check_full_file_tree`, `check_index_table`, and
  `check_location_mapping` all recognize the real `GUARD_START_MCP`/
  `GUARD_START_DEPLOYMENT`-shaped format via the shared helper.
- The 2 pre-existing guard-exemption tests (`tests/tools/test_check_docs_content_policy.py:109-132`)
  still pass unmodified.
- `uv run python tools/check_docs_content_policy.py` runs cleanly (no crash)
  against the full `docs/` tree.

## Out of scope
Fixing any violation the new checks surface in existing `docs/*.md` content;
promoting `GV-021` to blocking; a decorator-based check registry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | New tests live in seq 03's document (same target row, `tests/tools/test_check_docs_content_policy.py`) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `tools/`-scoped lighter sequence per `routing.md` "Adding a new tool" — no `lint-imports`/`diff-cover` gate |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | GV-021 doc row update lives in seq 02's document |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004 (6 new checks; guard-detection fix; apply to 3 existing checks; register in main())
- **Source issue**: issues/done/20260918-130159_docschk01_extend-check_docs_content_policy-instead-of-new-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-104809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114519
- **Related target files**: tools/check_docs_content_policy.py
