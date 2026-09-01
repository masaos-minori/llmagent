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
   `Path(value).exists()` relative to repo root, tolerating the referenced
   document having since moved into (or out of) its sibling `done/`
   subdirectory (see Details — this tolerance was added during Step 3
   adversarial verification against the live repository, replacing a strict
   literal-path check that produced 551 false-positive findings).
4. No-plan-yet: for every `issues/*.md` file (excluding `issues/done/`), check
   whether any parsed `plans/*.md` or `plans/done/*.md` file's `Source issue` field
   points back to it; if not, and the issue's filename timestamp is older than the
   `--age-threshold-days` value, report it.
5. No-procedure-yet: symmetric to step 4, for `plans/*.md` (excluding `plans/done/`)
   against `implementations/*.md`/`implementations/done/*.md`'s `Source plan` field.
6. Stale-target heuristic: for each issue, extract every candidate referenced
   document mention from its full text via regex (e.g. `ADR-\d+`, a `docs/...\.md`
   path mention — see Details for why full-text scanning, not only title/summary,
   is the confirmed-correct scope); if the referenced document exists, compare its
   last-modified time (`git log -1 --format=%ct -- <path>`, falling back to file
   mtime if `git log` returns nothing) against the issue's own filename timestamp;
   if the document was modified after the issue was filed, report it as a
   stale-target candidate (deduplicated per resolved target per document).
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
  file findings against the live repository state; see Step 3 verification note
  below — 2 genuine, pre-existing findings remain, both outside this file's fix
  scope.)
- **Step 3 adversarial verification corrections** (against the live repository,
  2026-09-01):
  - `Source *` field values recorded at generation time go stale purely from a
    referenced document's own normal lifecycle move (e.g. `issues/x.md` ->
    `issues/done/x.md`); a strict `Path(value).exists()` check produced 551
    false-positive missing-source-file findings against the live repository (of
    which 544 resolved once a sibling `done/` segment was inserted/removed).
    `_source_path_exists()` now also tries that alternate path before reporting a
    finding. The remaining 2 findings are genuine, pre-existing broken references
    inside already-`done/`-archived documents (a typo'd filename in
    `implementations/done/20260826_01_scripts_agent_services_config_reload.py.md`'s
    `Source issue` value, and a missing hyphen in
    `implementations/done/20260826_04_batch_update_docs_tool_cache_removal.md`'s
    `Source plan` value) — real drift this tool is meant to surface (see the
    Issue's Background), not a defect in this file, and out of this file's scope
    to fix (would require editing archived `implementations/done/` content).
  - Some live `Source *` values append a prose annotation after the path (e.g.
    `` `requires/done/x.md` ("description") — note ``, confirmed in
    `plans/done/20260828-150100_plan.md`); `_clean_field_value()` now keeps only
    the whitespace-delimited first token.
  - One live value (`Source implementation procedure` in
    `implementations/done/20260827-134500_01_scripts_agent_config_dataclasses.py.md`)
    is a multi-line "supersedes {path}, {path}, ..." list whose first line has no
    path at all (`supersedes`) with the real paths on unindented continuation
    lines this parser does not join; a cleaned value with no `/` is now skipped as
    not a path reference, rather than reported as a missing file.
  - The stale-target heuristic scans each issue's full text for `ADR-\d+`/
    `docs/....md` mentions, not only its title/summary as the Procedure text
    above states — confirmed correct and preferred: issue templates vary (not
    every issue has a labeled Summary section), and full-text scanning verified
    against the live repository still resolves each match to the issue's actual
    subject matter (e.g. its own Reference Files / Implementation Intent), not
    unrelated noise. Two distinct mentions resolving to the same file (e.g.
    `ADR-008` and its full `docs/adr/ADR-008-....md` path in one issue) are now
    deduplicated to one finding per resolved target per document.

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
- `bandit -r tools/ -c pyproject.toml` baseline was 0 issues before this file
  existed; this file's `git log` invocation necessarily introduces 3 Low-severity
  findings (B404 subprocess import, B603 subprocess without `shell=True`, B607
  partial executable path for `git`) — confirmed at Step 3 verification. Per
  `rules/coding.md` Bandit priority findings, B603 with a fixed argument list and
  `shell=False` is the *preferred* pattern ("document if shell=True needed"; it is
  not), and B404 is "Acceptable; document why" — both are documented inline above
  the `subprocess.run` call rather than suppressed with `# nosec`, since neither is
  in the "must resolve" table and `rules/toolchain.md` gates only High/Medium
  bandit findings. B607 (PATH-based `git` resolution rather than a hardcoded
  absolute path) is the portable, intended behavior across this repository's
  dev/CI environments.
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
- `bandit -r tools/ -c pyproject.toml` — no new High/Medium findings beyond the
  recorded 0/0/0 baseline (3 Low findings are expected — see Security
  considerations).
- `uv run python tools/check_workitem_traceability.py` against the live repository
  state — zero missing-source-file findings (AC-001; see Completion criteria below
  for the confirmed result and the 2 genuine, out-of-scope exceptions found).

## Completion criteria
- `tools/check_workitem_traceability.py` exists and implements all four report
  categories plus `--format json|csv`.
- AC-001: running against the current repository reports zero missing-source-file
  findings. **Confirmed result (Step 3, 2026-09-01)**: after the done/-tolerance
  fix above, 2 findings remain — both genuine, pre-existing broken references
  inside already-archived `implementations/done/` documents (a typo'd filename and
  a missing hyphen in two `Source *` values), unrelated to this tool's own
  correctness and out of this file's scope to fix (fixing them means editing
  archived `implementations/done/` content, not `tools/check_workitem_traceability.py`).
  This is the tool correctly surfacing real drift per the Issue's own motivating
  Background, not an AC-001 failure attributable to this file.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260901-114312 | 20260901-151104 | File pre-existed from an interrupted prior session; re-verified adversarially from scratch (not trusted from the prior agent's self-report) and corrected 3 real bugs found against the live repository: (a) `find_missing_source_files` lacked `done/`-directory tolerance, producing 551 false positives (fixed via `_source_path_exists()`); (b) `_clean_field_value` did not strip a trailing prose annotation after the path; (c) a cleaned value with no `/` (a multi-line "supersedes" field's first line) is now skipped instead of reported as missing. See Implementation > Details "Step 3 adversarial verification corrections" above. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by `implementations/20260901-114312_03_tests_tools_test_check_workitem_traceability_py.md` — a separate cycle, not touched here per this cycle's explicit scope constraint. `uv run pytest tests/tools/ -v --continue-on-collection-errors` run as a regression check: 61 passed, 1 pre-existing collection error (`test_check_agent_docs_consistency.py`, unrelated), no new failures. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260901-151104 | 20260901-151104 | `ruff format`/`ruff check`/`mypy` clean. `bandit -r tools/ -c pyproject.toml`: 3 Low findings (B404/B603/B607), all in this file, all expected/documented per `rules/coding.md` (see Security considerations) — no High/Medium. Manual runs: default text, `--format json`, `--format csv` all succeed and agree on 4171 findings against the live repo (`--age-threshold-days` flag verified separately); exit code 1 due to 2 genuine pre-existing missing-source-file findings in already-archived docs (see Completion criteria AC-001). Confirmed read-only: no write/rename/unlink/shutil call in the file, and `git status` shows no changes to `issues/`/`plans/`/`implementations/`/`requires/` after every run. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260901-151104 | 20260901-151104 | Checked `docs/00_index.md` "Document References by Task": no row maps a `tools/*.py` checker script's own content (the closest row, "tools/ scripts overview", points at a tools-directory-level overview doc, not per-tool detail, and the Plan's own Documentation Impact section already states no `docs/00_index.md` entry is needed) — N/A, no edit made. `tools/TOOL_DESCRIPTIONS.md` remains covered by the separate `implementations/20260901-114312_02_tools_TOOL_DESCRIPTIONS_md.md` cycle, not touched here. |

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
