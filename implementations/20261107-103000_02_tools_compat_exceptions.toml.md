## Goal

- tools/compat_exceptions.toml — remove the production-category exceptions and add the checker self-reference allowance table (REQ-003)

## Scope
**Release unit**: policy-finalization

- The Plan declares one unit covering Phases 1-4; this manifest cleanup must land in the same commit as the doc rewrites that remove the findings the deleted entries tolerate (Plan Release unit row, 2026-11-07).

## Assumptions

- Baseline re-verified 2026-11-07 at HEAD `1a13653e8`: 21 `[[compatibility_exceptions]]` entries — 3 `migration` (ids at lines 24, 33, 42), 1 `compatibility` (`check-compat-shims-source`, id line 204), 17 `fixture`; `[symbol_stage_allowance]` at line 219. The file is unchanged between the Plan freeze base `1b2dded66` and HEAD; the Plan's earlier 22/18 figures were a grep overcount (the header comment at line 4 matches the section syntax) and were corrected in the Plan.
- `load_exceptions()` tolerates the new `[checker_self_reference]` table only after sibling document 01 lands (its step 5 adds the read); landing this document without document 01 would drop the checker's own pattern-literal exemption and fail the checker run.

## Design decisions

- The three `migration` entries are deleted, not reclassified: their findings (`_MCP_TOOLS` naming text in the two MCP docs, `workflow_schema.py`/ledger text in `db_03`) are removed from those documents by sibling documents 12, 14, 15 (and the compatrm001 core rewrite), so no exemption is needed after the unit lands.
- `check-compat-shims-source` moves to a dedicated `[checker_self_reference]` table (same shape as `[symbol_stage_allowance]`, a `paths` list plus a `reason`), keeping the checker's pattern literals tolerated without living in the production exception model (Plan Design "Exception model split").
- All 17 `fixture` entries stay: they are negative-test data (Plan Background). If the sibling document 04 gate test ever needs to contain a removed-name literal, add exactly one new `fixture` entry for that file instead of importing literals — the frozen design is that document 04 reads names programmatically from the checker module, so no new entry is expected; recount after the sweep.

## Alternatives considered

- Keep the `migration` entries with a far-future expiry: rejected — REQ-003 and AC-001 require zero production-category entries, and the findings they tolerate are being removed by this Plan itself.
- Exempt the checker via `--allowlist`: rejected — the `--allowlist` CLI flag (defined in
  `tools/check_compat_shims.py`) replaces the whole manifest path set, not a targeted allowance.

## Implementation
### Target file
`tools/compat_exceptions.toml`
### Procedure
1. Delete the three `migration` entry blocks (ids `mcp-00-document-guide`, `mcp-07-tool-schema-export-policy`, `db-03-migration-and-scaling` — blocks at lines 23-30, 32-39, 41-48) and the `--- Migrated compatibility-exception entries` header comment's stale counts, rephrasing the comment to describe the remaining 18 fixture entries plus the allowance tables.
2. Delete the `check-compat-shims-source` entry block (lines 203-210).
3. After the `[symbol_stage_allowance]` table (line 219), add:
   ```toml
   # --- Checker self-reference allowance ------------------------------------
   # tools/check_compat_shims.py's own COMPAT_PATTERNS/_REMOVED_NAME_PATTERNS
   # literals are exempt from its self-scan through this dedicated table
   # (loaded by load_exceptions()). This is not a compatibility exception:
   # production-category entries are rejected by validate_exceptions().
   [checker_self_reference]
   reason = "The checker's own pattern literals; tolerated outside the production exception model."
   paths = ["tools/check_compat_shims.py"]
   ```
4. Land only after sibling documents 12, 14, 15 have removed the findings these entries tolerated (same commit ordering within the unit).
5. Recount: `uv run python -c "import tomllib, collections; d=tomllib.load(open('tools/compat_exceptions.toml','rb')); e=d['compatibility_exceptions']; print(len(e), collections.Counter(x['category'] for x in e))"`
   Expected at execution time: 17 entries, `{'fixture': 17}` (or 18 fixture plus one fixture-only entry if the document 04 sweep required test data — record the actual number in the Execution Status Notes).
### Method
REQ-003 / AC-001. `load_exceptions()` (checker line 157) resolves every entry `path` into the scan allowlist and `validate_exceptions()` (line 181) enforces the schema; sibling document 01's step 4 makes any `compatibility`/`migration`/`fallback` category fatal, so leaving these entries in place would itself fail every CI run. The allowance tables (`[symbol_stage_allowance]`, new `[checker_self_reference]`) are separate top-level tables and are not `[[compatibility_exceptions]]` entries, satisfying "dedicated configuration".
### Details
Manifest goes from 21 `[[compatibility_exceptions]]` entries to 17 (fixture only) plus two allowance tables. No `[[compatibility_exceptions]]` entry keeps a production category.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: sibling document 01 (the `[checker_self_reference]` read), and sibling documents 12, 14, 15 (findings removed from the tolerated docs first), plus compatrm001's `db_03` core rewrite.
  - Blocks: sibling documents 03 and 04 (both assert the manifest's final category state).
  - Release unit: policy-finalization (Phases 1-4).

## Security considerations

N/A: configuration data change; no secrets or paths outside the repository.

## Rollback considerations

- Reverting the policy-finalization commit restores the deleted entry blocks together with the checker and docs state that required them; the manifest is never deployed (`tools/` is not deployed).

## Validation plan

- Command: the recount one-liner in Procedure step 5. Expected: no `compatibility`/`migration`/`fallback` categories.
- Command: `uv run python -m tools.check_compat_shims --check-removed-names --check-doc-symbols`
  Expected: exit 0 — the previously tolerated files now pass without their exemptions.
- Command: `uv run pytest tests/tools/test_check_compat_shims.py -q`
  Expected: pass, including the updated `TestManifestParity` (sibling document 03).

## Completion criteria

- The manifest carries zero production-category entries, the checker self-reference is a dedicated table, all 17 fixture allowances remain, and the checker run is green without the deleted exemptions (AC-001, REQ-003).

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete 3 migration entries and the compatibility entry; add the checker_self_reference table — Plan Phase 1 | Pending | — | — | land after docs 12/14/15 within the unit |
| 2 | Recount entries and record the actual fixture count | Pending | — | — | |
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
- **Requirement ID**: REQ-003 / AC-001
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-064415_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-103000
- **Related target files**: `tools/compat_exceptions.toml`
- **Companion**: `tools/check_compat_shims.py`
