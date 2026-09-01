## Goal
Implement `tools/check_workitem_traceability.py`, a read-only checker that walks
`issues/`, `plans/`, and `implementations/` (including `done/` subdirectories), parses
each document's Traceability section, and reports missing-source-file, no-plan-yet,
no-procedure-yet, and stale-target-heuristic findings (REQ-001, REQ-002, REQ-003,
REQ-004, REQ-005, REQ-006).

## Scope
- In scope: file discovery across the six directories; Traceability-section parsing
  tolerant of the Plan-level vs. implementation-procedure-level field-set variance;
  the four report categories; `--format json|csv` output alongside a default
  human-readable summary; a configurable age-threshold CLI flag.
- Out of scope: writing, renaming, moving, or deleting any file under `issues/`,
  `plans/`, or `implementations/` (including `done/`); auto-resolving the
  stale-target heuristic — it only surfaces a candidate, never a verdict.

## Assumptions
- `tools/generate_workitem.py` (a separately-tracked tool) is confirmed absent from
  `tools/` at this cycle's evidence-gathering time; this file does not depend on it.
- Traceability field values starting with `N/A` (case-insensitive) are not paths to
  validate, matching every sampled Traceability section's convention.
- The age threshold's concrete default (in days) is left to this implementation to
  choose (a generous value, e.g. 14 or 30) and document in `--help`/docstring — no
  repository precedent ties a specific number to this exact use case (UNK-01).

## Design decisions
- Follow the sibling `tools/check_*.py` shape: a small set of pure functions
  (discovery, parsing, per-category checking) plus an argparse-based `main()`,
  mirroring `tools/check_compat_shims.py`'s `ROOT_DIR = Path(__file__).resolve()
  .parent.parent` resolution pattern and `tools/check_tool_descriptions_sync.py`'s
  plain-function structure.
- The four report categories are independent passes over one shared parsed graph
  (list of documents with their extracted Traceability fields), not four separate
  file-walks — avoids re-parsing the same files four times.
- `--format json|csv` serializes the same finding objects the human-readable
  summary is built from (mirroring `tools/generate_mcp_inventory.py`'s `--format`
  convention: `choices=["json", "csv"]`, `default="json"`), so output modes cannot
  drift apart in shape.

## Alternatives considered
- Treating each report category as a separate script (four `check_*.py` files):
  rejected — the categories share the same discovery/parsing pass, and the Plan's
  Implementation Target Files defines exactly one script for all four.
- Hardcoding a hidden numeric age threshold with no CLI override: rejected per the
  Plan's Risks section — an un-overridable threshold risks noisy findings against
  normal recently-filed work; the threshold must be a CLI flag.

## Implementation
### Target file
`tools/check_workitem_traceability.py`

### Procedure
1. Discover every `issues/*.md`, `issues/done/*.md`, `plans/*.md`, `plans/done/*.md`,
   `implementations/*.md`, `implementations/done/*.md` file.
2. For each file, parse its `## Traceability` section (bullet lines matching
   `- **Field Name**: value` under that heading, per `templates/traceability.md`)
   and extract `Source issue` / `Source plan` / `Source implementation procedure` /
   `Source requirement` values, skipping any value starting with `N/A`.
3. Missing-source-file: for every extracted, non-`N/A` `Source *` value, check
   `Path(value).exists()` relative to repo root; report any that do not resolve.
4. No-plan-yet: for every `issues/*.md` file (excluding `issues/done/`), check
   whether any parsed `plans/*.md` or `plans/done/*.md` file's `Source issue` field
   points back to it; if not, and the issue's filename timestamp is older than the
   `--age-threshold-days` value, report it.
5. No-procedure-yet: symmetric to step 4, for `plans/*.md` (excluding `plans/done/`)
   against `implementations/*.md`/`implementations/done/*.md`'s `Source plan` field.
6. Stale-target heuristic: for each issue, extract a candidate referenced document
   name from its title/summary via regex (e.g. `ADR-\d+`, a `docs/...\.md` path
   mention); if the referenced document exists, compare its last-modified time
   (`git log -1 --format=%ct -- <path>`, falling back to file mtime if `git log`
   returns nothing) against the issue's own filename timestamp; if the document was
   modified after the issue was filed, report it as a stale-target candidate.
7. Emit a human-readable summary by default; under `--format json|csv`, serialize
   the same finding objects as JSON or CSV.

### Method
Argparse-based CLI script (`main()` entry point), `pathlib.Path`-based repo-root
resolution (`ROOT_DIR = Path(__file__).resolve().parent.parent`, matching
`tools/check_compat_shims.py`), plain functions for discovery/parsing/each
report-category check — no classes, no persistent state beyond the in-memory parsed
graph for the duration of one invocation.

### Details
- CLI flags: `--age-threshold-days` (int, default: implementer-chosen generous
  value per UNK-01, documented in `--help`), `--format {json,csv}` (default: human-
  readable text; `json`/`csv` select machine-readable output).
- Traceability parsing must tolerate the confirmed field-set variance: Plan-level
  Traceability has no `Requirement ID` field; implementation-procedure-level
  Traceability does. The parser extracts only the four `Source *` fields regardless
  of which other fields are present.
- A per-file parse failure (malformed or missing `## Traceability` heading) is
  reported as its own finding (parse-error), not a silent skip or a hard crash of
  the whole run (per the Plan's Risks mitigation).
- `git log -1 --format=%ct -- <path>` failure (e.g. file not tracked, or `git`
  unavailable) falls back to `Path(path).stat().st_mtime`.
- Exit code: `0` when no findings requiring attention exist (missing-source-file
  findings only, since no-plan-yet/no-procedure-yet/stale-target are informational
  per the Plan's Validation plan); non-zero when at least one missing-source-file
  finding exists. (This exit-code contract governs `AC-001` — zero missing-source-
  file findings against the live repository state.)

## Compatibility considerations
New, standalone file; no existing caller. Not imported by `scripts/`, so the
`skills/DESIGN.md` import-layer contract does not apply (`tools/` is outside its
scope per `routing.md` Tools section). Read-only against `issues/`/`plans/`/
`implementations/` — no risk of altering those trees' content.

## Security considerations
- Strictly read-only against the work-item trees — no write/rename/move/delete
  call anywhere in this file (enforced by design, not merely by convention: no
  `open(..., "w")`, `Path.rename`, `Path.unlink`, or `shutil.*` call against those
  paths).
- `git log` invocation uses a fixed argument list (`shell=False`), never
  interpolating file paths into a shell string.
- `bandit -r tools/ -c pyproject.toml` baseline is 0 issues (confirmed against the
  current `tools/` directory) — the new file must not introduce a finding.
- `radon`/`vulture` are confirmed absent from this environment (`which radon
  vulture` — both not found); documented as `Tool [name] not available` per
  `skills/DESIGN.md` Tool availability guard, not invented.

## Rollback considerations
New file only; rollback is deleting `tools/check_workitem_traceability.py`. Being
read-only, it cannot have altered any other file's state, so rollback carries no
side-effect risk beyond removing the file itself.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_traceability.py -v` — once created
  (see `implementations/20260901-114312_03_tests_tools_test_check_workitem_traceability_py.md`),
  all four scenarios (valid chain, missing source, no-plan-yet, no-procedure-yet)
  must pass.
- `uv run ruff check tools/check_workitem_traceability.py`; `uv run mypy
  tools/check_workitem_traceability.py` — no new findings.
- `bandit -r tools/ -c pyproject.toml` — no new findings beyond the recorded 0/0/0
  baseline.
- `uv run python tools/check_workitem_traceability.py` against the live repository
  state — zero missing-source-file findings (AC-001).

## Completion criteria
- `tools/check_workitem_traceability.py` exists and implements all four report
  categories plus `--format json|csv`.
- AC-001: running against the current repository reports zero missing-source-file
  findings.
- AC-002: running against a fixture directory with a deliberately removed source
  file correctly reports that case.
- AC-003: age-threshold gating correctly distinguishes a recent from an old
  issue/plan.
- AC-004: the stale-target heuristic surfaces a candidate without modifying any
  file.
- AC-005: `--format json` and `--format csv` both produce parseable output
  equivalent in content to the default summary.

## Out of scope
- Auto-fixing, closing, or superseding any stale issue/plan/procedure file.
- Auto-resolving the stale-target heuristic.
- `tools/generate_workitem.py` and the three sibling tools
  (`tool004`/`tool005`/`tool006`) — tracked separately, not touched here.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by `implementations/20260901-114312_03_tests_tools_test_check_workitem_traceability_py.md` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Covered by `implementations/20260901-114312_02_tools_TOOL_DESCRIPTIONS_md.md` |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006
- **Source issue**: `issues/20260831-194739_tool003_check_workitem_traceability.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-110301_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-114312
- **Related target files**: `tools/check_workitem_traceability.py`
