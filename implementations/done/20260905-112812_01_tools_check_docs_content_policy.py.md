## Goal

Implement `tools/check_docs_content_policy.py`, a new dedicated script that
scans `docs/*.md` for the five implementation-detail remove-categories the
docs content policy prohibits (REQ-001, REQ-002, REQ-006).

## Scope

- In-scope: this new file only — five detection functions (one per
  remove-category), file discovery, and `Issue`-object reporting.
- Out-of-scope: registering the check in
  `docs/00_governance_04_documentation-checks.md` (covered by
  `implementations/20260905-112812_02`); the test file
  (`implementations/20260905-112812_03`); `tools/TOOL_DESCRIPTIONS.md`
  (`implementations/20260905-112812_04`); rewriting any flagged `docs/*.md`
  content.

## Assumptions

- **Blocking precondition (Plan Phase 1)**: this row's detection logic
  targets the five remove-category definitions that Plan `docscope1`
  (`plans/done/20260905-101850_plan.md`) adds to `skills/DESIGN.md` Shared
  Vocabulary. Re-verified during this cycle: `skills/DESIGN.md` does not yet
  contain those subsections (`grep -n "remove-categor\|retain-categor"
  skills/DESIGN.md` returns no match) — `docscope1`'s own implementation
  procedures (`implementations/20260905-112342_01` through `_10`) are
  generated but not yet executed. This document's Method/Details below
  describe the procedure to follow once that precondition is met; do not
  execute Implementation > Method against source until `skills/DESIGN.md`
  actually contains the five remove-category definitions.
- The next available `GV-*` ID is `GV-021` (re-verified this cycle:
  `docs/00_governance_04_documentation-checks.md` line 290 is still the
  highest-numbered entry, `GV-020`) — re-check for collision immediately
  before that ID is actually inserted in
  `implementations/20260905-112812_02`, not here.

## Design decisions

New dedicated script rather than extending `tools/check_docs_quality.py`
(re-confirmed this cycle: that file is 549 lines via `wc -l`, still past
`skills/DESIGN.md` File Split Rule's 400-line trigger — confirmed unchanged
at `skills/DESIGN.md` line 37). Import the `Issue` dataclass from
`tools/_docs_consistency_lib.py` (re-confirmed present: `file`, `line_no`,
`severity`, `message` fields) rather than redefining it a third time.
Implement file discovery locally (`docs_dir.rglob("*.md")`, no `prefix`
parameter) rather than reusing `_docs_consistency_lib.py`'s
`discover_md_files(docs_dir, *, prefix: str)` — re-confirmed this cycle that
`docs/adr/` and `docs/databases/` both still exist as subdirectories
(`find docs -mindepth 1 -maxdepth 1 -type d`), which that function's
non-recursive, prefix-based glob cannot reach.

## Alternatives considered

Extending `tools/check_docs_quality.py` with five new `@register_core_check`
functions — rejected per Plan Design (file-size pressure argument, still
valid per this cycle's re-measurement). Reusing
`_docs_consistency_lib.py`'s `discover_md_files()` — rejected per Plan
Implementation intent's Shared-library reuse decision (non-recursive,
`prefix`-required, cannot see `docs/adr/`/`docs/databases/`).

## Implementation

### Target file

`tools/check_docs_content_policy.py`

### Procedure

1. Confirm `skills/DESIGN.md` contains the five remove-category definitions
   (Plan `docscope1` landed) before writing any pattern/heuristic logic
   against them — if not yet landed, stop; do not guess the heading names or
   wording.
2. Create the new file with a module docstring, imports (including `Issue`
   from `tools._docs_consistency_lib`), and a `discover_md_files(docs_dir)`
   function (`rglob`-based, no `prefix`).
3. Implement one detection function per remove-category: full file tree;
   per-file one-line description embedded in a tree or table;
   class/function/method signature-and-description index table;
   implementation-location mapping statement; literal port number in a
   heading, table, or prose.
4. Implement a `main()` entry point that discovers `docs/*.md` files, runs
   all five detection functions, and reports findings via the `Issue`
   convention (file + line-level granularity, per REQ-002).
5. Ensure the scan never includes `rules/env.md` (REQ-006) — trivially true
   once discovery is scoped to `docs_dir.rglob("*.md")`, since `rules/env.md`
   is outside `docs/` entirely; no special-case exclusion logic is needed.

### Method

Write new Python source at `tools/check_docs_content_policy.py`. Each
detection function takes a `DocFile`-like object (path + lines) and returns
`list[Issue]`. Follow the existing `check_docs_quality.py` core-check
function signature shape (`(docs_dir: Path, files: list[DocFile]) ->
list[Issue]`, confirmed present at that file's `check_stale_patterns`/
`check_resolved_in_active` functions) for consistency, without importing
from that file (no reusable public helper is exposed there, per Plan Design).

### Details

Detection heuristics (finalize exact regex/pattern only once the landed
`skills/DESIGN.md` wording is available, since the categories' precise
boundaries — e.g. how many tree-drawing characters constitute a "full file
tree" versus an isolated example — depend on that wording):
- Full file tree: line matching literal tree-drawing characters (`├─`, `│`,
  `└─`), confirmed as the exact characters used in this repository's known
  violation example (`docs/01_overview-files-02-rag.md` lines 28-33,
  re-confirmed present this cycle via direct grep).
- Per-file one-line description: a tree-drawing or table line followed by an
  inline `#`-prefixed or `|`-delimited description — reuse the same line
  match as the file-tree detector where the description is embedded in the
  same line.
- Class/function/method index table: a Markdown table whose header row
  contains column names matching `Function`/`Method`/`Class` alongside
  `Signature`/`Description` (confirmed present pattern:
  `docs/03_rag_02_08_ingestion_pipeline-shared.md` line 60's `| Function |
  Signature | Description |`, re-confirmed present this cycle).
- Implementation-location mapping: a line matching "(moved/implemented/
  handled by `{name}.py`)" or an inline comment naming a `.py` file as the
  actor of an action (confirmed pattern: `docs/01_overview-files-02-rag.md`
  line 30's "`# Files ingested into DB (moved by ingester.py)`", re-confirmed
  present this cycle).
- Literal port number: a heading, table cell, or prose sentence containing
  "Port \d+" (confirmed pattern:
  `docs/04_mcp_04_02_file-write-file-delete-shell.md` lines 13/47/81's "(Port
  8007)" etc., re-confirmed present this cycle) — per this Plan's own
  worked-example carve-out (mirroring `skills/DESIGN.md` "No concrete
  configuration values"), a short, explicitly-labeled illustrative example
  must not be flagged; this exemption's exact detection logic is `UNK-01` in
  the source Plan, to be resolved once `docscope1`'s landed text confirms
  whether the exemption is explicit.

## Compatibility considerations

No public/runtime-facing interface change — this is a new, independent CLI
entry point (matching every other `tools/check_*.py` script's operational
profile), not a change to any existing module's interface. No circular
import: `tools/_docs_consistency_lib.py` has no `__main__` and imports
nothing from any `check_*.py` script (re-confirmed via its docstring: "Not a
check script itself — has no `__main__` entry point").

## Security considerations

Read-only script — opens `docs/*.md` files for reading only, writes no
files, executes no subprocess, accepts no untrusted input beyond file paths
already scoped to `docs/`. No new `# nosec`/`# noqa`/`# type: ignore`
suppressions anticipated; if one becomes necessary, follow
`rules/coding.md` Suppression governance (rule/error code + em-dash
justification).

## Rollback considerations

New, standalone file under version control; revert via `git revert` if a
detection heuristic proves unreliable. Report-only (Warning) rollout (per
Plan `docscope2` REQ-004) means this file's findings never block CI even if
a heuristic is imperfect — no other file's behavior depends on this file
existing yet, since it is not yet registered anywhere (that registration is
`implementations/20260905-112812_02`'s job).

## Validation plan

- `uv run ruff check tools/check_docs_content_policy.py` — clean.
- `uv run mypy tools/check_docs_content_policy.py` — clean.
- `uv run pytest tests/tools/test_check_docs_content_policy.py` (once
  `implementations/20260905-112812_03` lands) — all tests pass.

## Completion criteria

- The file exists with one detection function per remove-category, a
  `main()` entry point, and `Issue`-based reporting imported from
  `tools/_docs_consistency_lib.py`.
- Running the script against the current `docs/*.md` corpus produces
  concrete findings without raising an exception.
- `rules/env.md` is never included in the scan (trivially true — it is
  outside `docs/*.md`).

## Out of scope

Registering this script anywhere (Automated Checks list, Governance
Verification Matrix, `TOOL_DESCRIPTIONS.md`) — those are the other 3 rows of
this Plan. Fixing any flagged `docs/*.md` file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260905 | 20260905 | Precondition met: `skills/DESIGN.md` now contains the five remove-category definitions (`implementations/done/20260905-112342_01`). Created `tools/check_docs_content_policy.py` with 5 detection functions, importing `Issue`/`report_and_exit` from `tools/_docs_consistency_lib.py`, own `rglob`-based `discover_all_md_files()`. |
| 2 | Add or update tests per Validation plan | Completed | 20260905 | 20260905 | N/A: no existing test imports this new file's symbols (new file); dedicated unit tests are a separate row's scope: `implementations/20260905-112812_03` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260905 | 20260905 | `ruff format`/`ruff check`/`mypy` all clean. Ran the script against the live corpus: 276 findings across 26 files (135 full file tree, 71 per-file description, 6 index table, 2 location mapping, 62 literal port number), exit code 0 (report-only confirmed), `rules/env.md` never flagged (0 matches). Full file list: `01_overview-arch-01-process.md`, `01_overview-files-01-build.md`, `01_overview-files-02-rag.md`, `01_overview-files-04-shared.md`, `01_overview-files-05-config.md`, `01_overview-files-06-misc.md`, `03_rag_01_system_overview.md`, `03_rag_02_04_ingestion_pipeline-ingester.md`, `03_rag_02_05_ingestion_pipeline-document-manager.md`, `03_rag_02_06_ingestion_pipeline-supporting-components.md`, `03_rag_02_07_ingestion_pipeline-utils.md`, `03_rag_02_08_ingestion_pipeline-shared.md`, `04_mcp_01_tool_ownership_matrix.md`, `04_mcp_02_service_boundaries.md`, `04_mcp_03_03_transport-and-health.md`, `04_mcp_04_01_web-search-file-read-github.md`, `04_mcp_04_02_file-write-file-delete-shell.md`, `04_mcp_04_03_rag-pipeline-and-cicd.md`, `04_mcp_04_04_mdq.md`, `04_mcp_04_05_git.md`, `04_mcp_05_04_mdq-rag-boundary.md`, `04_mcp_06_06_verification-methods.md`, `05_agent_02_runtime-architecture.md`, `05_agent_03_01_turn-processing-flow-overview.md`, `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`, `06_eventbus_05_configuration-and-operations.md`. This inventory is this Plan's REQ-005 completion evidence, and the input `docscope3` needs for its own decision. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260905 | 20260905 | N/A: registration is a separate row, `implementations/20260905-112812_02` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Plan `docscope1` (`plans/done/20260905-101850_plan.md`) not yet implemented — `skills/DESIGN.md` does not yet contain the five remove-category definitions this row's detection logic must target | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-006
- **Source issue**: issues/done/20260903-200135_docscope2_build-content-policy-detection-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-102139_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-112812
- **Related target files**: tools/check_docs_content_policy.py
