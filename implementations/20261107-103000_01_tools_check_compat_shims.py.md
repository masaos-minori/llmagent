## Goal

- tools/check_compat_shims.py — consolidate the final no-compatibility pattern set and the production-exception-zero rule (REQ-001, REQ-002, REQ-003)

## Scope
**Release unit**: policy-finalization

- The Plan declares one unit covering Phases 1-4: the consolidated checker patterns only make sense against the post-compatrm001/002/003 tree, and validating any phase earlier would report findings the prerequisite Plans already own (Plan Release unit row, 2026-11-07).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8`; `tools/check_compat_shims.py` unchanged between the Plan freeze base `1b2dded66` and HEAD.
- Prerequisite implementations compatrm001/002/003 have landed before this unit (their checker edits — `db.store`/`eventbus.db`/auth patterns — are present in the file when this document is executed; this document supersedes them with the consolidated set).
- UNK-01 resolution used by this document: the checker's `_is_historical_context()` (line 406) scans a 10-line window for markers that include `removed`, `legacy`, `historical`, `resolved`. Supersession prose in sibling documents 08-16 keeps one of those markers on or above every line that names a retired mechanism, so the REQ-002 phrase patterns do not flag dated history.

## Design decisions

- REQ-001 symbol/import patterns land in `COMPAT_PATTERNS` (line 39, dict spans lines 39-115): always-on, applied to every scanned `*.py`/`*.md` under `scripts/`, `docs/`, `tests/`, `tools/` by `check_compat_patterns()` (line 539), subject only to the manifest allowlist.
- REQ-002 migration-claim phrase patterns land in `_REMOVED_NAME_PATTERNS` (lines 334-389): applied by `check_removed_name_reintroduction()` (line 475) to `*.md` files only, gated behind `--check-removed-names` (already passed by CI and pre-commit), with the `_is_historical_context()` exemption so supersession history passes.
- The syntax-tree rules (`check_mcp_health_reexport_import()` line 430, `check_gateless_discovery_construction()` line 451) are not touched; `COMPAT_PATTERNS` lines 81-84 already carry the `db.workflow_schema` import-regex precedent this consolidation follows.
- The `nack_event` two-argument call-shape regex is deliberately narrow: it matches exactly two simple positional arguments and therefore cannot match the new three-argument form. Strings containing commas inside two-argument calls are a known blind spot; the self-test (sibling document 03) pins the accepted boundary, matching how the existing approval-stage subset is pinned in `tests/tools/test_check_compat_shims.py` lines 88-115.

## Alternatives considered

- Put REQ-002 phrase patterns in `COMPAT_PATTERNS`: rejected — they would apply to `*.py` files too and have no historical-context exemption, flagging legitimate supersession history.
- Replace the `nack_event` regex with an AST rule: rejected for this Plan (the frozen Design row specifies a call-shape regex); the regex plus false-positive/true-positive self-tests satisfy AC-002.
- Keep `check-compat-shims-source` in `[[compatibility_exceptions]]`: rejected — the Plan's production-category-zero rule (REQ-003) makes a `compatibility` category entry impossible (sibling document 02).

## Implementation
### Target file
`tools/check_compat_shims.py`
### Procedure
1. Confirm the prerequisite Plans' edits have landed (their added pattern entries are visible in the file); this document rewrites them into the consolidated form.
2. Consolidate `COMPAT_PATTERNS` (lines 39-115): merge any prerequisite-added entries for the names below into single canonical entries, then add the final REQ-001 set following the existing entry style (`"name": r"regex"`):
   ```python
   "_TOKEN_PRINCIPAL_MAP": r"_TOKEN_PRINCIPAL_MAP",
   "_populate_token_maps": r"_populate_token_maps",
   "principal_map": r"\bprincipal_map\b",
   "verify_backup_by_path": r"\bverify_backup_by_path\b",
   "shared.db_migrations reference": r"\bshared\.db_migrations\b|db_migrations\.py",
   "db.migrations_workflow reference": r"\bdb\.migrations_workflow\b|migrations_workflow\.py",
   "eventbus.migrations reference": r"\beventbus\.migrations\b|eventbus/migrations\.py",
   "eventbus.migrate reference": r"\beventbus\.migrate\b|eventbus/migrate\.py",
   "migrate_db.py reference": r"\bmigrate_db\.py\b",
   "schema_migrations reference": r"\bschema_migrations\b",
   "workflow_schema_version reference": r"\bworkflow_schema_version\b",
   "WORKFLOW_SCHEMA_VERSION reference": r"\bWORKFLOW_SCHEMA_VERSION\b",
   "from db.store import": r"from\s+db\.store\s+import",
   "import db.store": r"\bimport\s+db\.store\b",
   "from eventbus.db import": r"from\s+eventbus\.db\s+import",
   "import eventbus.db": r"\bimport\s+eventbus\.db\b",
   "nack_event two-argument call form": r"nack_event\(\s*[\w.\[\]\"']+\s*,\s*[\w.\[\]\"']+\s*\)",
   ```
3. Add the REQ-002 migration-claim phrase entries to `_REMOVED_NAME_PATTERNS` (after line 388, before the closing brace) following the existing `re.compile` style:
   ```python
   "forward-only migration claim (removed by compatrm001/004)": re.compile(
       r"forward-only migration|registered forward-only"
   ),
   "migration ledger claim (removed by compatrm001/004)": re.compile(
       r"migration ledger|ledger migration|ledger-bearing|migration registry"
   ),
   "apply-migrations claim (removed by compatrm001/004)": re.compile(
       r"\bapply migrations\b|to apply the migration"
   ),
   "migrates-forward claim (removed by compatrm001/004)": re.compile(
       r"migrates through|migrates forward|evolve through"
   ),
   "verified-backup migration gate claim (removed by compatrm001/004)": re.compile(
       r"verified[- ]backup (?:precondition|gating|gate)|pre-migration gate"
   ),
   ```
4. In `validate_exceptions()` (line 181), after the known-category check (line 207), add the production-category-zero rule: an entry whose `category` is `compatibility`, `migration`, or `fallback` prints `invalid compatibility exception <id>: production-category entries are not permitted (<category>) under the no-compatibility policy` to stderr and `sys.exit(1)`. `_VALID_CATEGORIES` keeps its four values so an unknown-category message stays distinct from this rule.
5. In `load_exceptions()` (line 157), read a new top-level table `[checker_self_reference]` (shape mirrors `symbol_stage_allowance`, key `paths` as a string list) and merge its paths resolved against `ROOT_DIR` into the returned allowlist, so the checker's own pattern literals stay tolerated outside the production exception model (sibling document 02 adds the table).
6. In `main()`'s file selection (lines 663-685), skip any `*.md` whose relative path contains a `done` directory component for both the compat-pattern and removed-name scans (future guard: no `docs/**/done/` archives exist today, verified `find docs -type d -name done` returns zero).
7. Update the `check_compat_shims.py` rows in `tools/TOOL_DESCRIPTIONS.md` (lines 82 and 173) for: the consolidated removed set, the production-category-zero rule, and the `[checker_self_reference]` allowance table, following the repository toolchain rule that
   tool-description rows are updated whenever a `tools/` checker's behavior changes.
### Method
REQ-001 / REQ-002 / REQ-003. Today the checker file `check_compat_shims.py` splits two pattern
families: `COMPAT_PATTERNS` (line 39; already includes the approval-stage names at lines 62-74 and
the `db.workflow_schema` import regexes at lines 81-84) always-on across all scanned files, and
`_REMOVED_NAME_PATTERNS` (lines 334-389; `_update_null_fill` through
`security_lockdown_enabled`) docs-only and flag-gated with the historical-context exemption. The consolidation places each requirement in the family whose enforcement semantics it needs, so deleted production symbols are blocked everywhere while migration-claim sentences are blocked in documentation without flagging dated supersession history.
### Details
Net effect: 17 consolidated `COMPAT_PATTERNS` entries (some replacing prerequisite-added duplicates), 5 new `_REMOVED_NAME_PATTERNS` phrase entries, one new validation rule in `validate_exceptions()`, one new table read in `load_exceptions()`, one file-selection filter in `main()`, and a `tools/TOOL_DESCRIPTIONS.md` description update. No change to the two AST rules or `check_doc_symbols()`.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: the three prerequisite Plans' implementations (frozen plans `20261107-061846`, `20261107-063003`, `20261107-063921`), and sibling documents 08-16 (their rewrites must land in the same unit so the new patterns find nothing in active docs).
  - Blocks: sibling documents 02 (manifest cleanup requires the new `[checker_self_reference]` read), 03 (self-tests assert these entries), 04 (gate test runs the consolidated checker), 11-16 (their Validation gates run against these patterns).
  - Release unit: policy-finalization (Phases 1-4 land together; the prerequisite doc rewrites 11/12/14/15 precede the manifest-entry deletion in document 02 within the commit).

## Security considerations

N/A: checker pattern configuration only. New patterns tighten enforcement; no credential or input-handling change.

## Rollback considerations

- Reverting the single policy-finalization commit restores the pre-consolidation checker, manifest, docs, and tests together; the checker is never deployed (`tools/` is not deployed), so no runtime state is involved.

## Validation plan

- Command: `uv run pytest tests/tools/test_check_compat_shims.py -q`
  Expected: pass, including the sibling document 03 self-tests (true positives for every consolidated name; historical-text cases pass).
- Command: `uv run python -m tools.check_compat_shims --check-removed-names --check-doc-symbols`
  Expected: exit 0 on the final tree (run after sibling documents 02 and 08-16 land in the unit).
- Command: `grep -c "re.compile" tools/check_compat_shims.py` sanity check that the five new phrase entries exist; `grep -n "checker_self_reference" tools/check_compat_shims.py` shows the table read.
- Command: `uv run ruff check tools/check_compat_shims.py`; `uv run mypy tools/check_compat_shims.py`
  Expected: clean.

## Completion criteria

- The consolidated set is the only removed-name configuration in the checker, the production-category rule fails any `compatibility`/`migration`/`fallback` manifest entry, and the checker run is green on the final tree (AC-001, AC-002, AC-006, REQ-001, REQ-002, REQ-003).

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Consolidate COMPAT_PATTERNS, extend _REMOVED_NAME_PATTERNS, add the production-category rule and checker_self_reference read — Plan Phase 1 | Pending | — | — | policy-finalization unit: checker green only with all unit documents landed |
| 2 | Update tools/TOOL_DESCRIPTIONS.md rows 82/173 | Pending | — | — | |
| 3 | Run this document's Validation plan commands; full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Pending | — | — | |

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
- **Requirement ID**: REQ-001 / REQ-002 / REQ-003 / AC-001 / AC-002 / AC-006
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-064415_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-103000
- **Related target files**: `tools/check_compat_shims.py`
- **Companion**: `tests/tools/test_check_compat_shims.py`, `tools/compat_exceptions.toml`, `tools/TOOL_DESCRIPTIONS.md`
