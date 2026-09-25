## Goal
Add `generate_agent_reference_table()`, `generate_eventbus_reference_table()`,
`generate_memory_reference_table()` to `tools/generate_reference_table.py` and
register them under `--type agent`/`--type eventbus`/`--type memory` (`REQ-001`,
`REQ-002`, `REQ-003`, `REQ-004`).

## Scope
In scope: this one file's 3 new generator functions and their registration
across the 5 existing dispatch dicts. Out of scope: changing the existing
`rag`/`mcp`/`deployment` generators' behavior; deciding the exact "memory"
target document beyond the candidate list (`UNK-01`, unresolved — see
Assumptions).

## ⚠ Implementation gate — RESOLVED 20260919
Per the source Plan's `REQ-008`, this procedure required: (1) the Reference-class
ADR (`docs/adr/ADR-015-reference-document-class-disposition.md`) reaching
`Accepted` status with Option B chosen, and (2) the guard-detection fix landing
in `tools/check_docs_content_policy.py`. Both conditions are now satisfied:
ADR-015 is `Accepted` (Named Approval Record: Masao Sugimoto, 2026-09-19, via
chat review) and `_is_guard_start`/`_is_guard_end` exist in
`tools/check_docs_content_policy.py` (landed in commit `112367193`/`9b25e0f2f`).
Execution proceeds below.

## Assumptions
- File structure unchanged since the Plan was written — re-confirmed: 3 existing
  generator functions (`generate_rag_config_table` 62-73,
  `generate_mcp_reference_table` 117-127, `generate_deployment_reference_table`
  150-167), 5 dispatch dicts (`DOMAIN_GENERATORS` 174-181, `DOMAIN_DOCS` 183-186,
  `DOMAIN_GUARDS` 188-191, `DOMAIN_WELCOME_LINES` 193-196, `DOMAIN_HEADING`
  198-201), file is 246 lines total.
- The "memory" target document remains unresolved (`UNK-01`) — this row only
  adds the function and its `--type memory` registration; the exact
  `DOMAIN_DOCS["memory"]` target path must be confirmed (per the source Plan's
  Out of Scope allowance) before this row can actually be executed, in addition
  to the REQ-008 gate above.

## Design decisions
Follow the existing `generate_mcp_reference_table`/`generate_deployment_reference_table`
pattern exactly: each new function reads its source module's `.py` files under
`scripts/agent/`, `scripts/eventbus/`, `scripts/agent/memory/` respectively,
extracts docstrings/signatures via the same AST-light approach the existing
generators use (e.g. `_tool_names_for_config_key`'s file-globbing + regex
pattern, adapted to public class/function signatures instead of `TOOL_LIST`
entries), and returns a Markdown table string.

## Alternatives considered
Using Python's `ast` module for full signature extraction (vs. the existing
generators' simpler regex-based approach) was considered, but rejected for
consistency — none of the 3 existing generators use `ast`; introducing it only
for the 3 new ones would create two different extraction styles in the same
file for no clear benefit at this scope.

**Correction (`code-implementation` Step 3a, 20260919)**: this rejection does
not hold up under implementation. The existing 3 generators' domains are
fundamentally simpler than this one — TOML key/value pairs
(`generate_rag_config_table`) and a JSON-literal dict-key regex
(`_TOOL_LIST_NAME_RE`) — neither requires parsing Python function/class syntax.
Extracting a real Python function signature (multi-line defs, `*args`/`**kwargs`,
type hints, decorators) via regex is genuinely unreliable and would silently
mis-render or drop entries; `ast` (stdlib, already available, no new dependency)
parses this correctly. Using `ast` for this row only, while leaving the 3
existing generators' own regex/TOML approaches untouched, is not an
inconsistency — it is matching the extraction method to what each domain's data
shape actually requires, which is exactly why the 3 existing generators already
differ from each other (TOML parsing vs. regex) rather than sharing one style.

## Implementation
### Target file
tools/generate_reference_table.py

### Procedure
1. Add `GUARD_START_AGENT`, `GUARD_START_EVENTBUS` constants (after line 52's
   `GUARD_START_DEPLOYMENT`), matching the existing naming/format convention
   (`<!-- AUTO-GENERATED: gen_<domain>_reference.py <purpose> -->`).
2. Add `REFERENCE_DOC_AGENT = REPO_ROOT / "docs" / "agent_13_reference-api.md"`
   and `REFERENCE_DOC_EVENTBUS = REPO_ROOT / "docs" / "06_eventbus_06_reference-api.md"`
   (after line 55) — no `REFERENCE_DOC_MEMORY` constant yet, since `UNK-01` is
   unresolved (add it only once the target document is confirmed, per this row's
   Assumptions).
3. Add `generate_agent_reference_table()`, `generate_eventbus_reference_table()`,
   `generate_memory_reference_table()` functions (after line 167, mirroring the
   existing 3 functions' structure).
4. Register `agent`/`eventbus` (not `memory`, pending `UNK-01`) in
   `DOMAIN_GENERATORS`, `DOMAIN_DOCS`, `DOMAIN_GUARDS`, `DOMAIN_WELCOME_LINES`,
   `DOMAIN_HEADING` (lines 174-201).

### Method
Direct code edit (`Edit` tool), following the existing 3 generators' structure
exactly — no new dependencies (`tomllib`, `re`, `Path` are already imported).

### Details
- `generate_agent_reference_table()`: source `scripts/agent/*.py` — non-recursive
  glob (68 top-level files; matches `generate_mcp_reference_table`'s own
  `server_dir.glob("*.py")` non-recursive convention), skipping files/symbols
  whose name starts with `_`. Extract every top-level `class`/`def`/`async def`
  node via `ast.parse()`, format the signature via `ast.unparse()` for return
  annotations, and use `ast.get_docstring()`'s first line as the summary, into a
  `| Class/Function | Signature | Summary |` table, matching
  `generate_mcp_reference_table`'s column-header style. Class methods are not
  individually listed (top-level symbols only), matching the column header's
  "Class/Function" (not "Method") scope.
- `generate_eventbus_reference_table()`: same shape, sourcing
  `scripts/eventbus/*.py` (17 files; this domain has no subdirectories besides
  `__pycache__`, so non-recursive and recursive scope are identical here).
- `generate_memory_reference_table()`: same shape, sourcing
  `scripts/agent/memory/*.py` (confirmed to exist: `count_ops.py`,
  `embedding_client.py`, `enums.py`, `exceptions.py`, `extract.py`,
  `fts_query.py`, `import_ops.py`, `ingestion.py`, and others).
- `--type memory` registration is deferred (not added by this row) until
  `UNK-01` resolves the target document — adding the function without
  registering it under `main()`'s `--type` choices keeps it inert (unreachable
  via CLI) until that decision is made, avoiding a half-wired feature.

## Compatibility considerations
Existing `--type rag|mcp|deployment` behavior must be unchanged — the 3 new
functions and dict entries are purely additive. `argparse`'s `choices=` list
(line 207) gains `agent`, `eventbus` (not `memory`, per Details above).

## Security considerations
No security-sensitive code path (reads local `.py` source files, writes to a
local `docs/*.md` file under the same repository — no network, no credentials).

## Rollback considerations
`git checkout -- tools/generate_reference_table.py` reverts this row
independently — no other row's document depends on this file's internals beyond
CLI invocation (seq 02/03 depend on this row's functions existing at execution
time, not at generation time).

## Validation plan
- `uv run ruff format tools/generate_reference_table.py`
- `uv run ruff check tools/generate_reference_table.py --fix`, then confirm
  clean
- `uv run mypy tools/generate_reference_table.py`
- `uv run bandit tools/generate_reference_table.py`
- `uv run pytest tests/tools/test_generate_reference_table.py -v` (seq 05's new
  test file)
- Manual: `python tools/generate_reference_table.py --type agent --dry-run` and
  `--type eventbus --dry-run` — confirm table output, no crash

## Completion criteria
- `generate_agent_reference_table()` and `generate_eventbus_reference_table()`
  exist, are registered under `--type agent`/`--type eventbus`, and each
  `--dry-run` invocation succeeds.
- `generate_memory_reference_table()` exists but is not yet CLI-reachable
  (pending `UNK-01`).
- Existing `--type rag|mcp|deployment` behavior is unchanged (confirmed by
  running each with `--dry-run` and diffing output against pre-change output).

## Out of scope
Registering `--type memory` (pending `UNK-01`); executing this procedure before
the REQ-008 gate is satisfied (see the gate notice above).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260919-143123 | 20260919-143123 | Gated on REQ-008 (ADR-015 Accepted/Option B; guard-detection fix landed) — see gate notice above |
| 2 | Add or update tests per Validation plan | Completed | 20260919-143123 | 20260919-143123 | Tests live in seq 05's document (`tests/tools/test_generate_reference_table.py`) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260919-143123 | 20260919-143123 | `tools/`-scoped lighter sequence per `routing.md` "Adding a new tool" |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260919-143123 | 20260919-143123 | Doc updates happen via running this tool (seq 02/03), not a direct edit |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | REQ-008 gate not satisfied: re-verified 20260919-121854 — the guard-detection fix HAS now landed in `tools/check_docs_content_policy.py` (`plans/done/20260919-104809_plan.md`'s implementation completed), but `docs/adr/ADR-015-reference-document-class-disposition.md`'s Status is still `Proposed`, not `Accepted` — the gate requires both conditions (AND), so it remains unsatisfied | Yes | 20260919 (ADR-015 Accepted via Named Approval Record, user request) |
| 1 | `_generate_class_function_reference_table()`'s `path.relative_to(REPO_ROOT)` raised `ValueError` when called against a source directory outside the repo (discovered while writing seq 05's tests with `tmp_path` fixtures) — fixed with a try/except fallback to the absolute path, preserving production behavior (real `AGENT_DIR`/`EVENTBUS_DIR`/`MEMORY_DIR` are always under `REPO_ROOT`) while making the function testable | Yes | 20260919 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| tests/tools/test_generate_reference_table.py | 2 | Test | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004 (3 new generator functions; register agent/eventbus under --type; memory function added but not yet registered)
- **Source issue**: issues/done/20260918-130225_docsref01_extend-generate_reference_table-for-agent-eventbus-memory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-105034_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114740
- **Related target files**: tools/generate_reference_table.py