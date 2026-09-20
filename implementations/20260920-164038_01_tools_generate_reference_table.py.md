## Goal
Add a `"memory"` entry to `tools/generate_reference_table.py`'s five `DOMAIN_*`
dictionaries (`DOMAIN_GENERATORS`, `DOMAIN_DOCS`, `DOMAIN_GUARDS`,
`DOMAIN_WELCOME_LINES`, `DOMAIN_HEADING`), plus new `REFERENCE_DOC_MEMORY` and
`GUARD_START_MEMORY` constants, per `REQ-001` (Plan `plans/20260920-161148_plan.md`),
so `--type memory` becomes a usable CLI option mirroring the existing `agent`/
`eventbus` entries.

## Scope
In scope: adding the two new module-level constants (`REFERENCE_DOC_MEMORY`,
`GUARD_START_MEMORY`) and one new key/value pair to each of the five `DOMAIN_*`
dictionaries. Out of scope: `generate_memory_reference_table()` itself (already
implemented, confirmed at line 279 — not modified by this row); any existing
`"agent"`/`"eventbus"`/`"mcp"`/`"deployment"`/`"rag"` entry in any of the five
dictionaries; the `argparse` CLI wiring below the dictionaries (`--type`, `choices`)
— it already derives its choices from `DOMAIN_GENERATORS.keys()`, so adding a
`"memory"` key there is sufficient with no separate CLI code change needed.

## Assumptions
The file's exact current content (re-verified via Read during this document's
creation) has not shifted since the Plan was frozen — no commit has touched this file
since. `MEMORY_DIR` (line 34) and `generate_memory_reference_table()` (line 279) are
confirmed already present and correctly implemented; this row only wires them into the
dispatch dictionaries.

## Design decisions
Mirror the `"agent"`/`"eventbus"` entries in each dictionary exactly:
- `REFERENCE_DOC_MEMORY = REPO_ROOT / "docs" / "05_agent_12_07_memory-module-reference-generated.md"`,
  alongside the existing `REFERENCE_DOC_AGENT`/`REFERENCE_DOC_EVENTBUS` constants.
- `GUARD_START_MEMORY = "<!-- AUTO-GENERATED: gen_memory_reference.py class-function-reference -->"`,
  following the `gen_<domain>_reference.py` naming convention already used by
  `GUARD_START_AGENT`/`GUARD_START_EVENTBUS` (a historical naming convention for the
  guard-comment generator label; the actual generator is this same file for every
  domain).
- `DOMAIN_GENERATORS["memory"] = ("Memory module class/function reference table",
  generate_memory_reference_table)`.
- `DOMAIN_DOCS["memory"] = REFERENCE_DOC_MEMORY`.
- `DOMAIN_GUARDS["memory"] = (GUARD_START_MEMORY, GUARD_END)` (reusing the shared
  `GUARD_END` constant, as every other domain does).
- `DOMAIN_WELCOME_LINES["memory"] = "Generated from `scripts/agent/memory/*.py`
  top-level public classes and functions. Do not hand-edit between the guard comments;
  run `python tools/generate_reference_table.py --type memory` to refresh."` (same
  sentence template as the `"agent"`/`"eventbus"` lines, substituting the memory
  module glob).
- `DOMAIN_HEADING["memory"] = "## Module Class/Function Reference (auto-generated)"`
  (identical text to `"agent"`/`"eventbus"`, since all three domains use the same
  generation function `_generate_class_function_reference_table()` and produce the
  same table shape).

## Alternatives considered
- Point `REFERENCE_DOC_MEMORY` at one of the existing hand-curated `05_agent_12_0[1-6]`
  chapter files instead of a new file: rejected — this Plan's own `REQ-002` creates a
  new file specifically to avoid inserting generated content into an existing
  hand-curated document (see that row's own Design decisions); this row's constant
  must point at the new file for the two rows to be consistent.
- Reuse `GUARD_START_AGENT` for memory (since both are Agent-area domains per front
  matter): rejected — each domain has its own guard-comment label
  (`gen_<domain>_reference.py`) so `check_docs_content_policy.py`'s guard-exemption
  matching (and any future domain-specific regeneration tooling) can distinguish which
  domain's guarded block it is looking at; reusing `GUARD_START_AGENT` would make the
  Memory guarded block indistinguishable from Agent's in raw text.

## Implementation
### Target file
`tools/generate_reference_table.py`

### Procedure
1. Read lines 50-66 (guard/reference-doc constants) and lines 287-330 (the five
   `DOMAIN_*` dictionaries) to confirm current content matches the Plan's recorded
   evidence.
2. After `GUARD_START_EVENTBUS`'s definition (before the blank line preceding
   `REFERENCE_DOC_MCP`), add `GUARD_START_MEMORY = "<!-- AUTO-GENERATED:
   gen_memory_reference.py class-function-reference -->"`.
3. After `REFERENCE_DOC_EVENTBUS`'s definition, add `REFERENCE_DOC_MEMORY =
   REPO_ROOT / "docs" / "05_agent_12_07_memory-module-reference-generated.md"`.
4. In `DOMAIN_GENERATORS`, after the `"eventbus"` entry, add: `"memory": ("Memory
   module class/function reference table", generate_memory_reference_table),`.
5. In `DOMAIN_DOCS`, after the `"eventbus"` entry, add: `"memory":
   REFERENCE_DOC_MEMORY,`.
6. In `DOMAIN_GUARDS`, after the `"eventbus"` entry, add: `"memory":
   (GUARD_START_MEMORY, GUARD_END),`.
7. In `DOMAIN_WELCOME_LINES`, after the `"eventbus"` entry, add the `"memory"` welcome
   line per Design decisions.
8. In `DOMAIN_HEADING`, after the `"eventbus"` entry, add: `"memory": "## Module
   Class/Function Reference (auto-generated)",`.

### Method
Eight small, independently reviewable insertions (steps 2-8, each a single dictionary
entry or constant) via `Edit`, each anchored on the existing `"eventbus"`/
`GUARD_START_EVENTBUS`/`REFERENCE_DOC_EVENTBUS` line immediately preceding the
insertion point. Do not reorder or modify any existing line.

### Details
`generate_memory_reference_table` (the function, not a new one) must already be
importable/defined at module scope at the point `DOMAIN_GENERATORS` is built (it is —
confirmed at line 279, before `DOMAIN_GENERATORS` at line 287). Do not change
`argparse`'s `choices=list(DOMAIN_GENERATORS.keys())` line — it already picks up
`"memory"` automatically once step 4 lands.

## Compatibility considerations
Additive-only change to five module-level dictionaries and two new constants — no
existing `--type` value's behavior changes. `N/A` beyond that: no public interface
outside this CLI tool is affected.

## Security considerations
`N/A: no security-relevant content is touched` — this is a documentation-generation
tool with no runtime/production code path.

## Rollback considerations
Revert via `git checkout` on this one file. This row's edit is independently
revertable without affecting the other three Plan rows (the new doc file, the Plan
status update, or the NC-038 update) — though `REQ-003`'s dry-run/live generation
step depends on this row landing first (see the Plan's Implementation steps ordering).

## Validation plan
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — confirm existing
  `agent`/`eventbus`/etc. test cases still pass (Plan `AC-1`'s prerequisite: no
  regression).
- `uv run python tools/generate_reference_table.py --type memory --dry-run` — confirm
  the CLI now accepts `memory` as a `--type` value and exits 0 (Plan `AC-1`).
- `uv run ruff format tools/generate_reference_table.py`, `uv run ruff check
  tools/generate_reference_table.py`, `uv run mypy tools/generate_reference_table.py`
  — per `routing.md` "Adding a new tool"'s lighter validation sequence (this is a
  modification to an existing `tools/*.py` script; `tools/` is outside
  `pyproject.toml`'s default `mypy` `files` scope, so pass the path explicitly).

## Completion criteria
All five `DOMAIN_*` dictionaries contain a `"memory"` key with the values specified in
Design decisions; `REFERENCE_DOC_MEMORY` and `GUARD_START_MEMORY` are defined;
`--type memory --dry-run` exits 0.

## Out of scope
- `generate_memory_reference_table()`'s own implementation — already correct, not
  modified.
- Any existing domain's dictionary entries — unchanged.
- Creating `docs/05_agent_12_07_memory-module-reference-generated.md` itself — that is
  `REQ-002`'s own target-file row (a separate implementation procedure document);
  this row only points `REFERENCE_DOC_MEMORY` at that (not-yet-existing) path.
- Running the generator live to populate the guarded block — that is `REQ-003`'s
  responsibility, sequenced after both this row and `REQ-002` land.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-172045 | 20260920-172045 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-172045 | 20260920-172045 | Extend `tests/tools/test_generate_reference_table.py` with a `memory` case per REQ-003's own test-plan item, or confirm during REQ-003's implementation that this is covered there instead of duplicating All 7 tests pass including pre-existing test_memory_reference_table_extracts_public_symbols |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-172045 | 20260920-172045 | Use the `tools/*.py` lighter sequence per `routing.md` "Adding a new tool," not the full `scripts/` toolchain ruff format/check clean, mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-172045 | 20260920-172045 | N/A: this row's own change has no `docs/*.md` impact — that is REQ-002/REQ-004/REQ-005's responsibility N/A: no docs/00_index.md task-scope mapping for tools/generate_reference_table.py |

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
- **Requirement ID**: `REQ-001` — add a "memory" DOMAIN_* entry set, REFERENCE_DOC_MEMORY, and GUARD_START_MEMORY
- **Source issue**: issues/20260920-154806_memref01_resolve-nc-038-memory-reference-class-migration-target-and-wiring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-161148_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-164038
- **Related target files**: tools/generate_reference_table.py