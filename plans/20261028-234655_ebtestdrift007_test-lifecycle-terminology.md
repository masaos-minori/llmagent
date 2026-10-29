# Plan: consolidate eventbus test lifecycle terminology and remove schema duplication (ebtestdrift007)

## Goal
- Write one canonical test-fixture role/prefix mapping into the EventBus reference doc, build a
  mechanical audit script for `tests/eventbus/`, remove the private `CREATE TABLE` copy in
  `tests/eventbus/test_eventbus_restart_resume.py`, close the fixture-coverage gaps the audit
  finds (direct `EventBus(`/`TestClient(` constructions, `dmq`), and check the audit report into
  the repo -- without touching production code.

## Priority
Medium

## Scope
- **In-Scope**:
  - A canonical role/prefix mapping section in `docs/24_eventbus/eventbus_08_reference_api.md`,
    extending the fixture names it already lists (lines 155-157) and the naming model of
    `docs/07_governance/governance_03_issue-and-uncertainty-management.md`.
  - A new audit script `tools/audit_test_terminology.py` (ast-based, `tests/eventbus/`-scoped)
    with its own tests and its `tools/TOOL_DESCRIPTIONS.md` registration.
  - Removal of the fallback `CREATE TABLE events`/`event_dlq_offsets` block
    (`test_eventbus_restart_resume.py:276-307`) in favor of a shared production-schema loader.
  - Fixture-consolidation fixes at the audited sites: `make_test_client` helper + its 5 call
    sites, `EventBus(` → `make_event_bus_ctx` at `test_eventbus_consumer_authorization.py:27`,
    and the issue-mandated `dmq` rename at `test_eventbus_requeue_edge_cases.py:76,88`.
  - The audit report checked in under `assets/terminology_audit/`.
- **Out-of-Scope**: production code under `scripts/`/`agent/`; the two-lifecycle
  subscribe/restart scenarios (owned by `plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md`);
  bulk `x_*` identifier renames in audit-only files (deferred Phase 4 behind UNK-01); the agent
  API test layer (`tests/agent/`); CI registration of the audit script.
- **Dependencies**: This Plan implements *after* `plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md`
  for the two shared files: `tests/eventbus/eventbus_helpers.py` (ebresumetest004 adds the
  two-lifecycle fixture first; this Plan adds the schema loader and `make_test_client` on top)
  and `tests/eventbus/test_eventbus_restart_resume.py` (ebresumetest004 rewrites/rename/tests
  the file first; this Plan then deletes the fallback DDL block in the same file). Those are
  sequenced complementary edits, not design conflicts -- verified 2026-10-28. Overlap with
  `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md` on
  `docs/24_eventbus/eventbus_08_reference_api.md`: that Plan edits the audit signature rows, this
  Plan adds a new fixture-mapping section -- different sections, no conflict. Related archived
  issue: `issues/done/20260911-135626_ebsse01_subscribe-generator-never-detects-client-disconnect.md`
  (the schema-drift precedent). Related plan: the frozen-batch ebmetrics006 ADR pointer
  `plans/done/20261028-094217_ebmetrics006_agent-token-usage-metrics-and-sql-execution-time-column.md`.

## Background
`tests/eventbus/` grew file-by-file with no written naming contract. Verified 2026-10-28:
- The issue's prefix examples (`ctx_agent`, `ctx_consumer`, `agent_client`, `consumer_client`) do
  not exist; the dominant local style is `x_<role>_` (`x_evt_`, `x_cfg_`, `x_pub_`, `x_sub_`,
  `x_dlq_`, `x_ack_`, `x_ctx_`, `x_client_`, `x_auth_`) -- census: config 20,
  consumer_authorization 13, dlq 10, startup 9, requeue_edge_cases 9, ack_nack 5, dlq_pagination
  5, shutdown 4, admin_topics 3, ack_endpoint 3, dlq_promotion 3, subscribe 3, crash_ack 2,
  concurrent 2, helpers 1 (docstring example), publish 1, health 1, 18 files total.
- The fallback `CREATE TABLE` block (`test_eventbus_restart_resume.py:276-307`) is currently
  *identical* to `db/schema.sql` (confirmed via `diff` against live `PRAGMA table_info(events)`):
  the problem is a private schema copy that can diverge silently, exactly the `ebsse01` failure
  mode (archived 2026-09-11; git `163934f` later moved those columns into `db/schema.sql`).
- The hand-built lifecycle in `test_eventbus_restart_resume.py:274-342` (own temp dir, PRAGMA
  preamble, private DDL) is the only real bypass of `make_event_bus_ctx`; the issue's other two
  named files (`test_eventbus_health.py`, `test_eventbus_helpers.py`) do *not* bypass it -- the
  issue's file list is partially wrong.
- `dmq` appears only at `test_eventbus_requeue_edge_cases.py:76,88`.
- Fixture-construction audit: direct `EventBus(` outside helpers only at
  `test_eventbus_consumer_authorization.py:27`; direct `TestClient(` at 5 sites
  (`test_eventbus_publish.py:36`, `test_eventbus_requeue_edge_cases.py:169`,
  `test_eventbus_crash_ack.py:34`, `test_eventbus_dlq_promotion.py:41`,
  `test_eventbus_consumer_authorization.py:30`); direct `EventConsumer(` only inside
  `eventbus_helpers.py` itself (compliant). Existing canonical helper names:
  `make_event_bus_ctx` (:14), `open_consumer_db` (:33), `subscribe_client` (:55).
- No tool under `tools/` enforces test naming conventions; `assets/` does not exist in the repo.

## Problem
Eventbus tests have no written naming contract, duplicate fixture construction at 6 sites, and
keep a private copy of the production DDL; future schema changes would silently drift the test
copy, and identifier drift makes the test layer hard to audit mechanically.

## Reason for Change
Terminology drift and fixture duplication are maintenance debt; the private schema copy is a
known failure mode that already caused the archived `ebsse01` incident. No new incident cited;
Medium; not time-sensitive.

## Implementation Intent
Write the contract first (mapping section), make it mechanically checkable (audit script), then
fix only what is issue-mandated or structurally wrong: the private DDL, uncovered fixture
constructions, and the named `dmq` prefix. The bulk rename of readable `x_*` locals is *not*
assumed: it is deferred to a decision-gated Phase 4 (UNK-01) so the owner decides with the audit
report in hand. Production files are never touched; helper signatures (`make_event_bus_ctx`,
`open_consumer_db`, `subscribe_client`) keep their behavior.

## Requirements
- `REQ-001`: `docs/24_eventbus/eventbus_08_reference_api.md` gains one canonical mapping section:
  test role → canonical prefix → owning helper (covering at least bus/ctx/cfg/db/client/record/
  topic/subscription/dead_message_queue and the existing helper names).
- `REQ-002`: `tools/audit_test_terminology.py` mechanically compares local identifiers in
  `tests/eventbus/*.py` against the mapping (ast-based; file, line, identifier, nearest canonical
  prefix per finding), checks `EventBus(`/`EventConsumer(`/`TestClient(` construction coverage
  against helper usage, exits non-zero on findings, and writes a per-file report; it is
  registered in `tools/TOOL_DESCRIPTIONS.md` and covered by `tests/tools/test_audit_test_terminology.py`.
- `REQ-003`: `tests/eventbus/test_eventbus_restart_resume.py` no longer contains a private DDL
  block; its databases are initialized through a shared helper that applies `db/schema.sql`
  (the same source `make_event_bus_ctx` uses).
- `REQ-004`: no test constructs `EventBus`, `EventConsumer` or `TestClient` inline where a helper
  covers the pattern: `make_test_client` (new) covers the 5 `TestClient` sites;
  `make_event_bus_ctx` covers `test_eventbus_consumer_authorization.py:27`; `subscribe_client`
  already covers `EventConsumer` (no change).
- `REQ-005`: `dmq` at `test_eventbus_requeue_edge_cases.py:76,88` is renamed to a
  `dead_message_queue_`-prefixed name per the mapping.
- `REQ-006`: the audit report covering every `tests/eventbus/` file is checked in under
  `assets/terminology_audit/`.
- `REQ-007`: cross-cutting constraint: no production file changes; existing helper signatures and
  all existing test assertions keep their behavior (terminology/loader consolidation only).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 2026-10-29: all target rows Verified; `tools/check_workitem_structure.py` clean; `tools/check_plan_target_overlaps.py` findings reviewed as documented sequencing dependencies). Re-verified 2026-10-29 against HEAD `de896f113`: the frozen inventory is stale against the current tree and its census constructs never existed in any commit (see Verification findings and the corrected Blocker Log root cause); the Plan is referred back to `issue-to-plan` for rescope and re-freeze — no procedure documents are generated from this freeze.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| docs/24_eventbus/eventbus_08_reference_api.md | Add the canonical test-fixture role/prefix mapping section | Issue acceptance: one canonical mapping document in the repo | REQ-001; AC-1 | Fixture names already listed at lines 155-157; no naming-contract section exists (grep 2026-10-28) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| tests/eventbus/eventbus_helpers.py | Phase 1: docstring cross-reference to the mapping section. Phase 2: add `apply_production_schema(conn)` (applies `db/schema.sql` without building an EventBus). Phase 3: add `make_test_client(app)` | Helpers are the discoverable home of the contract; the schema loader and TestClient builder are the two missing helpers | REQ-003, REQ-004, REQ-007; AC-2, AC-3 | Canonical helper names at :14/:33/:55; `make_event_bus_ctx` loads schema from `db/schema.sql`; 5 duplicated `TestClient(` sites | Audit-script coverage check + touched test files | Verified |
| tools/audit_test_terminology.py | New ast-based audit script (identifier prefixes + construction coverage + report writer) | Issue: "write a small script that performs the comparison mechanically"; no such tool exists | REQ-002; AC-1, AC-4 | `grep` 2026-10-28: no naming-convention checker in `tools/` | tests/tools/test_audit_test_terminology.py | Verified |
| tools/TOOL_DESCRIPTIONS.md | Register the new script | `tools/`↔`TOOL_DESCRIPTIONS.md` drift is an AGENTS rule-9 failure mode | REQ-002 | File exists (598 lines); every other `tools/` script is listed | Drift review at Phase 1 gate | Verified |
| tests/tools/test_audit_test_terminology.py | New tests: clean sample → no findings; `dmq`-style violation → finding with file/line/identifier; construction coverage flags inline `TestClient(`/`EventBus(` | Repo convention: `tools/` scripts have tests under `tests/tools/` | REQ-002; AC-1 | `tests/tools/` already holds checker tests (e.g. `test_check_adr_structure.py`) | The new tests themselves | Verified |
| assets/terminology_audit/ (report file, name assigned by the Phase 3 run) | Checked-in per-file audit report of all `tests/eventbus/` files | Issue acceptance: audit output checked in | REQ-006; AC-4 | `assets/` does not exist today; the issue names this path | Audit script run at Phase 3 gate | Verified |
| tests/eventbus/test_eventbus_restart_resume.py | Delete the private DDL block (lines 276-307) and hand-written PRAGMA preamble; use `apply_production_schema` | Private schema copy can drift from `db/schema.sql` (ebsse01 precedent) | REQ-003; AC-2 | Block verified identical to `db/schema.sql` 2026-10-28; `make_event_bus_ctx` already loads the production schema | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py` | Verified |
| tests/eventbus/test_eventbus_consumer_authorization.py | Replace inline `EventBus(` with `make_event_bus_ctx` and inline `TestClient(` with `make_test_client` | Fixture-coverage acceptance | REQ-004; AC-3 | Inline sites at :27 and :30 | `uv run pytest tests/eventbus/test_eventbus_consumer_authorization.py` | Verified |
| tests/eventbus/test_eventbus_publish.py | Replace inline `TestClient(` with `make_test_client` | Fixture-coverage acceptance | REQ-004; AC-3 | Inline site at :36 | `uv run pytest tests/eventbus/test_eventbus_publish.py` | Verified |
| tests/eventbus/test_eventbus_requeue_edge_cases.py | Rename `dmq` → `dead_message_queue_*` (:76, :88); replace inline `TestClient(` (:169) | Issue names this rename explicitly; fixture coverage | REQ-004, REQ-005; AC-3 | `dmq` verified at :76,88 | `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py` | Verified |
| tests/eventbus/test_eventbus_crash_ack.py | Replace inline `TestClient(` with `make_test_client` | Fixture-coverage acceptance | REQ-004; AC-3 | Inline site at :34 | `uv run pytest tests/eventbus/test_eventbus_crash_ack.py` | Verified |
| tests/eventbus/test_eventbus_dlq_promotion.py | Replace inline `TestClient(` with `make_test_client` | Fixture-coverage acceptance | REQ-004; AC-3 | Inline site at :41 | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py` | Verified |

Audit-only files (appear in the REQ-006 report, no frozen target row; rename scope deferred to
Phase 4 / UNK-01): `test_eventbus_config.py` (20 `x_cfg_`), `test_eventbus_dlq.py` (10
`x_dlq_`), `test_eventbus_startup.py` (9), `test_eventbus_ack_nack.py` (5),
`test_eventbus_dlq_pagination.py` (5), `test_eventbus_shutdown.py` (4),
`test_eventbus_admin_topics.py` (3), `test_eventbus_ack_endpoint.py` (3),
`test_eventbus_subscribe.py` (3), `test_eventbus_concurrent.py` (2), `test_eventbus_health.py`
(1), `test_eventbus_helpers.py` (1, docstring example).

**Verification findings (2026-10-29, against HEAD `de896f113`; the 2026-10-28 census below did
not match any committed tree at any time — see the corrected Blocker Log root cause)**:
- `tests/eventbus/` holds 34 `.py` files (census said 18); files absent from the census
  include `test_eventbus_schema_version.py`, `test_eventbus_offsets.py`,
  `test_admin_topics_authorization.py`, `test_eventbus_publish_contract.py`,
  `test_eventbus_replay_subscribe.py`.
- Zero `x_<role>_` prefixed identifiers exist under `tests/eventbus/` (the census `x_cfg_`,
  `x_dlq_`, etc. are gone). `tests/eventbus/eventbus_helpers.py` was rewritten in commit
  `a82cae689` (2026-10-28 13:10 JST, before this Plan was generated); its current helpers are
  `eventbus_test_tokens` (:69), `eventbus_auth_headers` (:88), `make_eventbus_client` (:101),
  `principal_map` (:194). `make_event_bus_ctx`, `open_consumer_db` and `subscribe_client` do
  not exist anywhere in the repo, so the helper names this Plan treats as the contract are
  gone.
- Zero direct `EventBus(`/`EventConsumer(` construction sites exist under `tests/eventbus/`;
  the `test_eventbus_consumer_authorization.py` target row cites sites at `:27` and `:30` that
  do not exist (the file now builds a `_build_client` fixture).
- 43 `TestClient(` occurrences across 12+ files (12 in `test_eventbus_auth.py`, 8 in
  `test_eventbus_subscribe.py`), not the 5 cited sites.
- No `dmq` identifier exists at `test_eventbus_requeue_edge_cases.py:76,88`; the only `dmq`
  substrings are the test method names `test_requeue_non_dmq_event` (:75) and
  `test_requeue_valid_dmq_event` (:87). REQ-005 as written has no referent.
- The schema moved: `db/` does not exist; the canonical DDL is `scripts/eventbus/schema.sql`.
  In `test_eventbus_restart_resume.py`, `_create_tables` (:277) already loads the production
  `schema.sql` (:311); the private inline DDL survives only as a dead fallback branch
  (:283-309; tables `events`, `consumer_delivery`, `consumer_offsets`) — the Plan cites
  `:276-307` and `db/schema.sql`.
- New uncovered private DDL, absent from the frozen inventory: `test_eventbus_schema_version.py:64`
  executes `CREATE TABLE events`.
- `docs/24_eventbus/eventbus_08_reference_api.md` is 149 lines; the cited fixture names at
  `:155-157` do not exist.
- The governance doc lives at `docs/00_governance/governance_03_issue-and-uncertainty-management.md`;
  `docs/07_governance/` does not exist.
- `tools/TOOL_DESCRIPTIONS.md` is 227 lines (census said 598). `assets/` still does not exist
  and `tools/audit_test_terminology.py` does not exist — both census claims hold.

Conclusion: every frozen target row needs re-scoping against this census; the audit-tool and
mapping-doc requirements (REQ-001, REQ-002) remain conceptually valid but their evidence lines
are stale. Root-cause addendum (2026-10-29): `git log -S`/`-G` over `--all` shows the census
constructs (`make_event_bus_ctx`, `open_consumer_db`, `subscribe_client`, all `x_<role>_`
identifiers, a standalone `dmq`) never existed in any commit — they appear only in
`plans/`/`issues/`/`implementations/` prose, and `tests/eventbus` held 24+ `.py` files at its
creation (never 18). The census was fabricated at Plan generation, not invalidated by later
commits.

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| db/schema.sql | Canonical DDL that `apply_production_schema` must apply unchanged | REQ-003 |
| docs/07_governance/governance_03_issue-and-uncertainty-management.md | Naming model (`repo_`, `db_`, `cfg_`, `ctx_`, `client_`, `record_`) the mapping extends | REQ-001 |
| tests/eventbus/conftest.py | Autouse state resets that bound cross-test leakage; must stay untouched | REQ-007 |
| plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md | Owns the two-lifecycle fixture added to `eventbus_helpers.py` first; sequencing boundary | Scope Dependencies |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002): the mapping section exists, and the audit script runs against every
  file under `tests/eventbus/` and reports findings mechanically (file/line/identifier).
- AC-2 (REQ-003): no `CREATE TABLE` block in `tests/eventbus/` duplicates `db/schema.sql`
  (grep gate: zero private-DDL occurrences outside `eventbus_helpers.py`'s production loader).
- AC-3 (REQ-004, REQ-005): no test constructs `EventBus`, `EventConsumer` or `TestClient` where
  a helper covers the pattern; `dmq` no longer exists in `tests/eventbus/`.
- AC-4 (REQ-006): the audit report is checked in under `assets/terminology_audit/` and lists
  every `tests/eventbus/` file.
- AC-5 (REQ-007): full suite green with unchanged assertion semantics; no production file in the
  diff.

## Tests
- REQ-002: `tests/tools/test_audit_test_terminology.py` -- fixture sources: clean mapping → no
  findings; `dmq`/unknown prefix → finding with nearest canonical prefix; inline `TestClient(`/
  `EventBus(` → coverage finding; deterministic (no clocks, stable ordering).
- REQ-003: `uv run pytest tests/eventbus/test_eventbus_restart_resume.py` (existing tests
  unchanged in behavior) plus the grep gate AC-2.
- REQ-004/REQ-005: the five touched test files pass unchanged in assertion semantics after the
  helper switch; `test_eventbus_requeue_edge_cases.py` passes after the rename.
- Gates: `uv run pytest tests/eventbus tests/tools/test_audit_test_terminology.py`; then full
  `uv run pytest`; ruff on changed files; mypy on changed `tests/` files and the new tool;
  `uv run python tools/check_docs_consistency.py --domain eventbus`.

## Documentation Impact
Yes, small: `docs/24_eventbus/eventbus_08_reference_api.md` gains the mapping section (current
state only, per docs policy). The audit report is a checked-in artifact under
`assets/terminology_audit/` (outside `docs/`, so docs checkers do not apply to it; its
generation is documented in `tools/TOOL_DESCRIPTIONS.md`). `docs/00_index.md` needs no new entry:
the section lives in an already-indexed doc.

## Assumptions
- The mapping is an *extension* of the reference API doc rather than a new top-level doc, keeping
  `eventbus_08_reference_api.md` the single discoverable source for eventbus test fixtures.
- `make_test_client` counts as "an existing fixture helper covers that pattern" for the
  TestClient acceptance criterion; leaving the 5 inline sites would contradict the issue's
  consolidation goal.
- Renaming test-local identifiers cannot change behavior; the full suite green is the
  characterization gate.
- Phase 4 (bulk `x_*` renames) stays out of the frozen table until UNK-01 is answered.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Keep-if-resolvable policy for the audit-only files: strict (every non-canonical prefix renamed) or pragmatic (only unresolvable names like `dmq`, keeping readable `x_*` locals)? | Owner decision; the issue explicitly defers the choice | Owner reviews the Phase 3 audit report and decides; Phase 4 rows are added to this Plan only after the answer | False |
| UNK-02 | Is `assets/terminology_audit/` (issue wording; `assets/` does not exist today) the right home, or should the report live under `docs/` where docs checkers apply? | No repo precedent for checked-in tool reports outside `docs/` | Default is the issue's path; relocating later is a file move -- owner confirms when the Phase 3 report lands | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| docs/24_eventbus/eventbus_08_reference_api.md | New mapping section | EventBus docs readers | 18 | 2 | Yes: docs/ is rsynced by deploy.sh (copy only, no service impact) |
| tests/eventbus/eventbus_helpers.py | Docstring + two new additive helpers | All eventbus tests | 7 | 2 | Yes: tests/ is rsynced by deploy.sh (no runtime service) |
| tools/audit_test_terminology.py | New manual tool | tools/ users | 0 | 0 (new file) | No: `tools/` is not rsynced by deploy.sh |
| tools/TOOL_DESCRIPTIONS.md | One registration row | tools/ users | 73 | 2 | No: not rsynced |
| tests/tools/test_audit_test_terminology.py | New test file | Tests only | 0 | 0 (new file) | Yes: tests/ rsync (no runtime service) |
| assets/terminology_audit/ report | New checked-in artifact | Repo readers | 0 | 0 (new file) | No: `assets/` is not deployed |
| tests/eventbus/test_eventbus_restart_resume.py | DDL-block removal (loader swap) | Restart-resume tests | 11 | 2 | Yes: tests/ rsync (no runtime service) |
| tests/eventbus/test_eventbus_consumer_authorization.py | Helper switch (2 sites) | Auth tests | 5 | 2 | Yes: tests/ rsync (no runtime service) |
| tests/eventbus/test_eventbus_publish.py | Helper switch | Publish tests | 5 | 2 | Yes: tests/ rsync (no runtime service) |
| tests/eventbus/test_eventbus_requeue_edge_cases.py | Rename + helper switch | Requeue tests | 12 | 2 | Yes: tests/ rsync (no runtime service) |
| tests/eventbus/test_eventbus_crash_ack.py | Helper switch | Crash-ACK tests | 7 | 2 | Yes: tests/ rsync (no runtime service) |
| tests/eventbus/test_eventbus_dlq_promotion.py | Helper switch | DLQ promotion tests | 15 | 2 | Yes: tests/ rsync (no runtime service) |

## Design
- Mapping section shape: table of role → canonical prefix → owning helper → example; declares
  the existing helper names (`make_event_bus_ctx`, `open_consumer_db`, `subscribe_client`) as
  contract, and adds `apply_production_schema` and `make_test_client` to the same table before
  they exist in code (Phase 1 precedes Phase 2/3 code).
- Audit script: `python tools/audit_test_terminology.py [--report-dir assets/terminology_audit]`;
  ast walk over `tests/eventbus/*.py`; a local name is "mapped" if its prefix matches the mapping
  section's prefix list; findings carry file/line/name/nearest-canonical-prefix; coverage check
  flags direct `EventBus(`/`EventConsumer(`/`TestClient(` calls in files that do not import the
  covering helper; exit 1 when findings exist (so Phase 4 can rerun it as a gate). The report is
  a Markdown table, one section per file. No `--apply` rewrite mode in this Plan (Phase 4 tooling
  decision).
- Schema loader: extract the schema-application step `make_event_bus_ctx` already performs
  (reads `db/schema.sql`) into `apply_production_schema(conn)`; the restart-resume test's private
  DDL and PRAGMA preamble are replaced by calls to it (PRAGMAs centralized there too). Behavior
  of `make_event_bus_ctx` is unchanged (it calls the new helper).
- `make_test_client(app)`: thin factory returning `TestClient(app)`; the 5 sites switch from
  inline construction to the helper. No fixture-lifecycle semantics change.
- Sequencing with ebresumetest004: its fixture lands first; this Plan's helpers are appended in
  the same file afterward; the restart-file DDL removal is applied on top of its renamed tests.

## Implementation steps
1. **Phase 1: Contract + audit tooling**
   - [ ] Add the mapping section to `docs/24_eventbus/eventbus_08_reference_api.md` and the docstring cross-reference in `tests/eventbus/eventbus_helpers.py` (REQ-001; docs/24_eventbus/eventbus_08_reference_api.md, tests/eventbus/eventbus_helpers.py)
   - [ ] Write `tools/audit_test_terminology.py` + `tests/tools/test_audit_test_terminology.py`; register in `tools/TOOL_DESCRIPTIONS.md` (REQ-002; tools/audit_test_terminology.py, tests/tools/test_audit_test_terminology.py, tools/TOOL_DESCRIPTIONS.md)
2. **Phase 2: Schema-copy removal** (after ebresumetest004 Phases 1-2 are implemented)
   - [ ] Add `apply_production_schema` to `tests/eventbus/eventbus_helpers.py`; delete the private DDL block in `tests/eventbus/test_eventbus_restart_resume.py` and switch to the loader (REQ-003; tests/eventbus/eventbus_helpers.py, tests/eventbus/test_eventbus_restart_resume.py)
3. **Phase 3: Fixture consolidation + mandated rename + report check-in**
   - [ ] Add `make_test_client`; switch the 5 `TestClient(` sites and the `EventBus(` site (REQ-004; tests/eventbus/eventbus_helpers.py, tests/eventbus/test_eventbus_consumer_authorization.py, tests/eventbus/test_eventbus_publish.py, tests/eventbus/test_eventbus_requeue_edge_cases.py, tests/eventbus/test_eventbus_crash_ack.py, tests/eventbus/test_eventbus_dlq_promotion.py)
   - [ ] Rename `dmq` at `test_eventbus_requeue_edge_cases.py:76,88` (REQ-005; tests/eventbus/test_eventbus_requeue_edge_cases.py)
   - [ ] Run the audit script and check the report into `assets/terminology_audit/` (REQ-006; assets/terminology_audit/)
4. **Phase 4: Verification**
   - [ ] `uv run pytest tests/eventbus tests/tools/test_audit_test_terminology.py`, then full `uv run pytest`; ruff/mypy on changed files; `tools/check_docs_consistency.py --domain eventbus` (REQ-001..REQ-007)
   - [ ] Deployment/scripts check: no `scripts/` file changes; docs/ and tests/ rsync by the normal deploy flow, no service restart needed (REQ-007)

Deferred, not frozen: **Phase 4b (bulk `x_*` renames)** -- target rows added only after the
UNK-01 decision.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/audit_test_terminology.py | Unit (fixture sources) | `uv run pytest tests/tools/test_audit_test_terminology.py` | Clean sample → 0 findings; violations reported with file/line/name; exit codes correct |
| tests/eventbus/test_eventbus_restart_resume.py | Integration (existing tests, loader swap) | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py` | All tests pass; `grep -rn "CREATE TABLE events" tests/eventbus/` → only `eventbus_helpers.py`'s production loader |
| 5 TestClient sites + EventBus site | Existing tests unchanged | `uv run pytest tests/eventbus` | Green; no assertion edits |
| docs/24_eventbus/eventbus_08_reference_api.md | Docs consistency | `uv run python tools/check_docs_consistency.py --domain eventbus` | Clean |
| Whole suite + static gates | Regression | `uv run pytest`; ruff; mypy; bandit re-scan (3 B101 baseline, no production files touched) | 411+ passed / 0 failed; no new bandit finding |

## Risks
- **Risk**: freezing this Plan while ebresumetest004 is frozen puts
  `tests/eventbus/eventbus_helpers.py` and `tests/eventbus/test_eventbus_restart_resume.py` in
  two Frozen Plans (the overlap checker will report both) → **Mitigation**: verified 2026-10-28
  that all four edits are additive/complementary and sequenced (ebresumetest004 first; Scope
  Dependencies); the checker's finding is the documented sequencing dependency, not a design
  conflict.
- **Risk**: the grep gate (AC-2) misses private DDL in `conftest`-level helpers other than
  `eventbus_helpers.py` → **Mitigation**: the REQ-006 report enumerates every `CREATE TABLE`
  occurrence under `tests/eventbus/` for owner review.
- **Risk**: `apply_production_schema` diverges from `make_event_bus_ctx`'s current PRAGMA setup
  and changes connection semantics for the restart tests → **Mitigation**: the helper is an
  extraction of the existing code path (same PRAGMAs), pinned by the unchanged restart tests
  passing.
- **Risk**: Phase 4 never gets a decision and `x_*` locals persist → **Mitigation**: the checked-in
  report is a one-read decision artifact (UNK-01 has a target date).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Mapping section + audit tooling (REQ-001, REQ-002) | Pending | — | — | |
| 2 | Schema-copy removal (REQ-003) | Pending | — | — | After ebresumetest004 Phases 1-2 |
| 3 | Fixture consolidation + dmq rename + report check-in (REQ-004..REQ-006) | Pending | — | — | |
| 4 | Verification gates (REQ-001..REQ-007) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | No hard blocker; Phase 4b (bulk renames) is deferred on UNK-01 by design | No | — |
| All | 2026-10-29 root-cause investigation: the frozen inventory was never true of any committed tree — `make_event_bus_ctx`/`open_consumer_db`/`subscribe_client` and every `x_<role>_` identifier appear ONLY inside `plans/`/`issues/`/`implementations/` documents across the full git history (`git log -S`/`-G` over `--all`), `tests/eventbus` has had 24+ `.py` files since its creation (never 18), a standalone `dmq` identifier never existed, and the `dmq` issue was the misspelling in the two method names `test_requeue_non_dmq_event`/`test_requeue_valid_dmq_event` (:75, :87) which the plan misread as a variable at `:76,88`. The plan also cites issue sections that do not exist in `issues/done/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md` ("Prefix Style", "audit output checked in", "Naming Decision"), and its REQ-001/002/006 (mapping doc, audit script, `assets/` report) match nothing in the issue, while the issue's actual REQ-identifier-comment cleanup is absent from the plan. The same fabricated helpers propagate into `b5890746f`/`d34cf7486` (eventbus001-004); the archived `plans/done/20261029-092424_eventbus003_test-lifecycle-production-path.md` independently confirmed the fiction at its Step 2. Referred back to `issue-to-plan` to re-derive the Plan from the real issue; procedure generation refused per the Blocked-on-new-target-discovery rule | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-234655
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`, `tests/eventbus/eventbus_helpers.py`, `tools/audit_test_terminology.py`, `tools/TOOL_DESCRIPTIONS.md`, `tests/tools/test_audit_test_terminology.py`, `assets/terminology_audit/` (report), `tests/eventbus/test_eventbus_restart_resume.py`, `tests/eventbus/test_eventbus_consumer_authorization.py`, `tests/eventbus/test_eventbus_publish.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py`, `tests/eventbus/test_eventbus_crash_ack.py`, `tests/eventbus/test_eventbus_dlq_promotion.py`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullet 1 (canonical mapping document) | docs/24_eventbus/eventbus_08_reference_api.md | Phase 1 | AC-1 | Docs consistency check | Explicit in issue |
| REQ-002 | Issue Required Changes bullet 1 (mechanical audit script) + Acceptance bullet 1 | tools/audit_test_terminology.py, tests/tools/test_audit_test_terminology.py, tools/TOOL_DESCRIPTIONS.md | Phase 1 | AC-1 | Script unit tests | Explicit in issue |
| REQ-003 | Issue Required Changes bullet 2 + Acceptance bullet 2 | tests/eventbus/test_eventbus_restart_resume.py, tests/eventbus/eventbus_helpers.py | Phase 2 | AC-2 | Restart tests + grep gate | Explicit in issue |
| REQ-004 | Issue Required Changes bullet 3 + Acceptance bullet 3 | tests/eventbus/eventbus_helpers.py, tests/eventbus/test_eventbus_consumer_authorization.py, tests/eventbus/test_eventbus_publish.py, tests/eventbus/test_eventbus_requeue_edge_cases.py, tests/eventbus/test_eventbus_crash_ack.py, tests/eventbus/test_eventbus_dlq_promotion.py | Phase 3 | AC-3 | Existing tests after helper switch | Explicit in issue |
| REQ-005 | Issue Prefix Style section (`dmq` at :76,88) | tests/eventbus/test_eventbus_requeue_edge_cases.py | Phase 3 | AC-3 | Existing tests after rename | Explicit in issue |
| REQ-006 | Issue Acceptance bullet 4 (audit output checked in) | assets/terminology_audit/ (report) | Phase 3 | AC-4 | Report existence + file coverage | Explicit in issue |
| REQ-007 | Issue Constraints (production untouched, behavior-preserving) | all target files | Phases 1-4 | AC-5 | Full suite + diff scope check | Explicit in issue |
| REQ-001 (Phase 4b) | Issue Naming Decision (keep-if-resolvable deferred by the issue itself) | audit-only files (rows added post-decision) | Phase 4b (not frozen) | — | Audit script rerun as gate | Needs confirmation (UNK-01) |
