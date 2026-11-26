## Goal
- Close the remaining gaps of the dedup keyless-write gate: make `pending_timeout_minutes` explicit in every shipped `[dedup]` table, prove the shipped tables load through the typed validator, and pin keyless rejection, `trigger_workflow` classification, and the timing bounds with tests that cover every side-effecting tool, so a keyless write cannot bypass cache and durable deduplication.

## Priority
High

## Scope
- **In-Scope**:
  - Add an explicit `pending_timeout_minutes = 10` to the ten shipped `config/*_mcp_server.toml` `[dedup]` tables (the validator default, so the store fingerprint stays unchanged).
  - Add a test that reads each real shipped `[dedup]` table through `load_dedup_section()`, asserts the explicit keys, and asserts the config fingerprint equals the default fingerprint.
  - Add keyless, empty-key, and whitespace-key rejection tests over every tool in `ALL_SIDE_EFFECTING_TOOLS` for the programmatic dispatcher and for the HTTP boundary, using the real set (not an injected one).
  - Pin `trigger_workflow` as non-retryable and side-effecting by its declared `retry_policy` and the reference sets.
  - Add boundary tests (zero, negative, boolean, minimum, maximum, oversized) for `retention_days` and `pending_timeout_minutes`.
  - Correct the stale "inert until the set is defined" docstring of the HTTP idempotency boundary, and the dedup config documentation of the `[dedup]` keys and ranges.
- **Out-of-Scope**:
  - Ownership, lease, heartbeat, and attempt-history logic (already implemented by the atomic dedup state-machine work).
  - The structured execution context and dry-run contract (already implemented).
  - Redesign of the typed `DedupStoreConfig` or removal of `config/mcp_dedup.toml` (already done by the dedup config isolation work).
  - Changing the dispatcher or the middleware behavior: both already reject keyless side-effecting calls.
  - Giving server-side `pending_timeout_minutes` a runtime effect (see UNK-01).
- **Dependencies**: Every issue this one was ordered after (atomic dedup state machine, logical idempotency key replay, structured execution context, dedup config isolation, retention and capacity monitoring) is archived and merged, so no ordering dependency remains. This Plan precedes the CI/CD dispatch reconciliation and CI/CD error audit coverage issues, which assume keyless writes are impossible.

## Background
- Source: consolidated Web Search and CI/CD MCP backlog, Issue 3 (residual part).
- Step 2/3 adversarial verification found most of the issue's claims stale:
  - `config/mcp_dedup.toml` no longer exists (`ls config/mcp_dedup.toml` fails). The dedup settings are the per-server `[dedup]` tables of `config/{server}_mcp_server.toml`, validated by `load_dedup_section()` (`scripts/shared/mcp_dedup_config.py:178-250`) into an immutable `DedupStoreConfig`.
  - Keyless rejection is implemented on both entry points: the programmatic dispatcher returns `error_type="idempotency_key_required"` before the handler (`scripts/mcp_servers/dispatch.py:418-428`; `ExecutionContext.__post_init__` strips the key, `execution_context.py:47`), and the HTTP middleware returns 422 (`scripts/mcp_servers/server.py:150-177`).
  - `ALL_SIDE_EFFECTING_TOOLS` is non-empty (`scripts/shared/tool_constants.py:218-228`, includes `CICD_WRITE_TOOLS = {"trigger_workflow"}`), so the middleware's "inert while the set is empty" docstring is stale. The inert branch is behavior-neutral: with an empty set no tool name could match anyway.
  - `trigger_workflow` is already explicit: its tool declaration carries `retry_policy: "never"` (`scripts/mcp_servers/cicd/cicd_tools.py:37`), and it is absent from `RETRYABLE_TOOLS`. `RETRYABLE_TOOLS` is now reference data drift-checked against the declarations (`tests/shared/test_tool_constants.py:105-151`); the declared field is the authority.
  - Range bounds already exist: `retention_days` 1..365 and `pending_timeout_minutes` 1..1440, with boolean and non-integer rejection (`scripts/shared/mcp_dedup_config.py:38-44,134-159`). Unresolved question "bound values" is resolved by the code.
  - There is no tool-name table in any shipped config any more (the `[retry_class]` mirror was retired), so "an unknown tool name in the distributed configuration fails CI" has no object; unknown `[dedup]` keys are rejected (`test_unknown_dedup_key_rejected`) and tool-name consistency is the declared `retry_policy` drift test.
  - The truncated-result state is named `replay_unavailable` in the code (`scripts/shared/mcp_dedup_schema.py:33`), resolving that unresolved question.
- Verified remaining gaps (checked in Step 3):
  - None of the ten shipped `[dedup]` tables sets `pending_timeout_minutes` (`rg "^\[dedup\]" -A8 config/*.toml`).
  - No test loads the real shipped `[dedup]` tables (`rg load_dedup_section tests`: only tmp-file and inline-dict uses).
  - Dispatcher keyless tests use one tool, `write_file` (`tests/mcp_servers/test_mcp_dispatch.py:168-187`, `tests/mcp_servers/test_dry_run_contract.py:193-211`); the HTTP boundary tests inject a synthetic set (`_SIDE_EFFECTING = {"shell_run", "delete_document"}`) and use `shell_run` for the per-app check (`tests/mcp_servers/test_server_idempotency_boundary.py:34,253-262`), so the real set is never swept.
  - Bound tests cover `lease_seconds`, `max_attempts`, and `retention_days` at 0 / 11 only (`tests/shared/test_mcp_dedup.py:805-815`); `pending_timeout_minutes`, negative, boolean, boundary, and oversized values are untested.
  - Server-side `pending_timeout_minutes` has no runtime consumer: it is validated and part of the config fingerprint (`mcp_dedup_config.py:89`), while the stale-pending sweep reads the Agent-side `AgentConfig.pending_timeout_minutes` (`scripts/agent/orchestrator.py:153`; `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md:137`). That document also names `dedup.pending_timeout_minutes` at line 178, which contradicts line 137.

## Problem
- The shipped configuration leaves `pending_timeout_minutes` implicit, and the guarantees that keyless side-effecting calls are rejected, that `trigger_workflow` is non-retryable, and that the timing bounds hold are each tested for a single sample or not at all, so a regression for any other tool or bound would pass CI.

## Reason for Change
- Correctness and external side-effect safety: the CI/CD workflow-dispatch work assumes keyless writes are impossible, and only a full sweep over the real side-effecting set can prove it.

## Implementation Intent
- Keep behavior as is. Make the one missing configuration entry explicit with the default value so the store identity does not change, and add tests that sweep the real tool set, the real shipped files, and the bound edges. Fix the two stale statements (middleware docstring, dedup config document) so they match the code.

## Requirements
- `REQ-001`: A keyless, empty-key, or whitespace-only-key call to every tool in `ALL_SIDE_EFFECTING_TOOLS` MUST be rejected before the handler runs, on the programmatic dispatcher (`idempotency_key_required`, `no_op`, handler uncalled) and on the HTTP boundary (422), with tests over the real set; the set MUST be asserted non-empty.
- `REQ-002`: `trigger_workflow` MUST be pinned by a test as side-effecting, declared `retry_policy="never"`, and absent from `RETRYABLE_TOOLS`.
- `REQ-003`: Every shipped `config/*_mcp_server.toml` `[dedup]` table MUST set `pending_timeout_minutes` explicitly to the default value 10, leaving the config fingerprint unchanged.
- `REQ-004`: `retention_days` (1..365) and `pending_timeout_minutes` (1..1440) MUST be tested for zero, negative, boolean, minimum, maximum, and oversized values; the existing bounds MUST NOT change.
- `REQ-005`: A test MUST load every real shipped `[dedup]` table through `load_dedup_section()` and assert the explicit keys and the default fingerprint; an unknown key in a shipped table MUST fail that test.
- `REQ-006`: The HTTP boundary docstring MUST no longer describe the boundary as inert for an empty set, and the dedup configuration document MUST describe the `[dedup]` keys with their ranges and the Agent-side ownership of the stale-pending timeout without self-contradiction.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/mcp_servers/test_mcp_dispatch.py | Modify: sweep keyless, empty, and whitespace keys over `ALL_SIDE_EFFECTING_TOOLS` | Existing test covers `write_file` only | REQ-001; AC-01 | `test_mcp_dispatch.py:168-187` (checked in Step 3) | `tests/mcp_servers/test_mcp_dispatch.py` | Verified |
| tests/mcp_servers/test_server_idempotency_boundary.py | Modify: sweep the real set through the HTTP boundary; assert the set is non-empty; update the stale module docstring | Existing tests inject a synthetic set and use `shell_run` | REQ-001, REQ-006; AC-01, AC-06 | `test_server_idempotency_boundary.py:1-14,34,253-262` (checked in Step 3) | `tests/mcp_servers/test_server_idempotency_boundary.py` | Verified |
| tests/shared/test_tool_constants.py | Modify: pin `trigger_workflow` classification | No assertion names `trigger_workflow` | REQ-002; AC-02 | `rg trigger_workflow tests/shared/test_tool_constants.py` found no match; drift test at `:105-151` (checked in Step 3) | `tests/shared/test_tool_constants.py` | Verified |
| tests/shared/test_mcp_dedup.py | Modify: bound tests for `retention_days` and `pending_timeout_minutes` | Existing bound tests stop at zero for three keys | REQ-004; AC-04 | `test_mcp_dedup.py:805-815` (checked in Step 3) | `tests/shared/test_mcp_dedup.py` | Verified |
| tests/mcp_servers/test_shipped_dedup_config.py | Create: real shipped `[dedup]` load, explicit-key, and fingerprint test | No test reads the real shipped tables | REQ-003, REQ-005; AC-03, AC-05 | `rg load_dedup_section tests` shows only tmp-file and inline uses; `tests/mcp_servers/` exists (checked in Step 3) | `tests/mcp_servers/test_shipped_dedup_config.py` | Verified |
| config/cicd_mcp_server.toml | Modify: add `pending_timeout_minutes = 10` to `[dedup]` | Implicit today | REQ-003; AC-03 | `[dedup]` at line 34 sets `retention_days`, `lease_seconds`, `max_attempts` only (checked in Step 3) | `tests/mcp_servers/test_shipped_dedup_config.py` | Verified |
| config/file_delete_mcp_server.toml | Modify: same | Implicit today | REQ-003; AC-03 | `[dedup]` table without the key (`rg`, checked in Step 3) | `tests/mcp_servers/test_shipped_dedup_config.py` | Verified |
| config/file_read_mcp_server.toml | Modify: same | Implicit today | REQ-003; AC-03 | `[dedup]` at line 24 without the key (checked in Step 3) | `tests/mcp_servers/test_shipped_dedup_config.py` | Verified |
| config/file_write_mcp_server.toml | Modify: same | Implicit today | REQ-003; AC-03 | `[dedup]` table without the key (checked in Step 3) | `tests/mcp_servers/test_shipped_dedup_config.py` | Verified |
| config/git_mcp_server.toml | Modify: same | Implicit today | REQ-003; AC-03 | `[dedup]` at line 46 without the key (checked in Step 3) | `tests/mcp_servers/test_shipped_dedup_config.py` | Verified |
| config/github_mcp_server.toml | Modify: same | Implicit today | REQ-003; AC-03 | `[dedup]` at line 62 without the key (checked in Step 3) | `tests/mcp_servers/test_shipped_dedup_config.py` | Verified |
| config/mdq_mcp_server.toml | Modify: same | Implicit today | REQ-003; AC-03 | `[dedup]` at line 66 without the key (checked in Step 3) | `tests/mcp_servers/test_shipped_dedup_config.py` | Verified |
| config/rag_pipeline_mcp_server.toml | Modify: same | Implicit today | REQ-003; AC-03 | `rg -l "^\[dedup\]" config` lists it (checked in Step 3) | `tests/mcp_servers/test_shipped_dedup_config.py` | Verified |
| config/shell_mcp_server.toml | Modify: same | Implicit today | REQ-003; AC-03 | `rg -l "^\[dedup\]" config` lists it (checked in Step 3) | `tests/mcp_servers/test_shipped_dedup_config.py` | Verified |
| config/web_search_mcp_server.toml | Modify: same | Implicit today | REQ-003; AC-03 | `rg -l "^\[dedup\]" config` lists it (checked in Step 3) | `tests/mcp_servers/test_shipped_dedup_config.py` | Verified |
| scripts/mcp_servers/server.py | Modify: docstring of `_idempotency_key_middleware` only | States the boundary is inert until the set is defined, but the set is non-empty | REQ-006; AC-06 | `server.py:150-177` docstring; `tool_constants.py:218-228` (checked in Step 2) | `tests/mcp_servers/test_server_idempotency_boundary.py` | Verified |
| docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | Modify: `[dedup]` key list with ranges; resolve the `pending_timeout_minutes` contradiction | Lines 134-138 list three keys and say Agent-side; line 178 names `dedup.pending_timeout_minutes` | REQ-006; AC-06 | `db_03_07...md:134-138,178` (checked in Step 3) | `uv run python tools/run_validation_gates.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/shared/mcp_dedup_config.py | Validator, ranges, defaults, fingerprint (`:38-44,89,178-250`) | REQ-003, REQ-004, REQ-005 |
| scripts/mcp_servers/dispatch.py | Keyless rejection at `:418-428` | REQ-001 |
| scripts/mcp_servers/execution_context.py | Key stripping in `ExecutionContext.__post_init__` (`:47`) | REQ-001 |
| scripts/shared/tool_constants.py | `ALL_SIDE_EFFECTING_TOOLS`, `RETRYABLE_TOOLS`, `CICD_WRITE_TOOLS` | REQ-001, REQ-002 |
| scripts/mcp_servers/cicd/cicd_tools.py | `trigger_workflow` declaration (`retry_policy: "never"`) | REQ-002 |
| scripts/agent/orchestrator.py | Agent-side `pending_timeout_minutes` consumer (`:153`) | REQ-006 |
| docs/22_mcp/mcp_03_01_dispatch-and-routing.md | Already records the key requirement for HTTP and programmatic dispatch (`:65`); no change needed | REQ-001 |
| deploy/deploy.sh | Confirms `config/*_mcp_server.toml` are copied individually (existing lines) | Affected areas |

## Acceptance Criteria
- `AC-01` (REQ-001): For every tool in `ALL_SIDE_EFFECTING_TOOLS`, a call with a missing, empty, or whitespace-only key returns `idempotency_key_required` with `execution_mode == "no_op"` and an uncalled handler through `dispatch_tool`, and returns 422 through the HTTP boundary; the set is asserted non-empty; a valid key still executes.
- `AC-02` (REQ-002): `trigger_workflow` is in `ALL_SIDE_EFFECTING_TOOLS`, not in `RETRYABLE_TOOLS`, and declares `retry_policy == "never"`.
- `AC-03` (REQ-003): Each shipped `[dedup]` table contains `pending_timeout_minutes = 10`, and its `DedupStoreConfig` fingerprint equals the fingerprint of the default config.
- `AC-04` (REQ-004): `retention_days` and `pending_timeout_minutes` reject 0, a negative value, a boolean, and a value one above the maximum, and accept the minimum and the maximum.
- `AC-05` (REQ-005): The real-file test loads all ten shipped tables, and a table with an extra unknown key makes `load_dedup_section()` raise `ConfigParseError`.
- `AC-06` (REQ-006): The middleware docstring and the dedup document contain no statement contradicted by the code; the documentation gates report no finding.

## Tests
- T-01 (REQ-001, AC-01): parametrized over `sorted(ALL_SIDE_EFFECTING_TOOLS)` for `dispatch_tool` (keys `""`, `"   "`, absent) and for the HTTP boundary (no header, whitespace header); plus a non-empty-set assertion and a valid-key control.
- T-02 (REQ-002, AC-02): three assertions on `trigger_workflow`.
- T-03 (REQ-003, REQ-005, AC-03, AC-05): real-file load of every `config/*_mcp_server.toml` carrying `[dedup]`, explicit-key assertion, default-fingerprint equality, unknown-key rejection on a copied table; run with `LLMAGENT_DB_DIR` unset so the canonical path matches.
- T-04 (REQ-004, AC-04): parametrized bound tests for both keys.
- T-05 (REQ-006, AC-06): documentation gates of `rules/tool-gates.md` "When to run which tool".
- Run ruff, mypy, the retry-class consistency drift test (`tests/shared/test_tool_constants.py`), and the full test suite.

## Documentation Impact
- Yes. REQ-006 drives one update, to the dedup database document selected through `docs/00_index.md` "Document References by Task" (database / dedup rows). The key requirement for HTTP and programmatic dispatch is already recorded in the MCP dispatch document, so it is not a target.

## Assumptions
- An explicit `pending_timeout_minutes = 10` equals `DEFAULT_PENDING_TIMEOUT_MINUTES`, so `_config_fingerprint` (`mcp_dedup_config.py:82-92`) and therefore the dedup store identity do not change.
- The shipped `db_path` equals `dedup_db_dir() / "mcp_dedup.sqlite"` when `LLMAGENT_DB_DIR` is unset, so the real tables pass the canonical-path check in the test.
- `config/*_mcp_server.toml` files are already copied individually by `deploy/deploy.sh`; modifying existing files needs no `deploy.sh` change.
- Overlap judgment (Step 8b): the MCP design docs update Plan (mcpai012) also modifies `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`. The two edits are compatible: that Plan adds invariant-to-test links and a runbook consistency check, while this Plan edits only the `[dedup]` config key list and the `pending_timeout_minutes` ownership statement. The implementation phases rebase onto each other and edit disjoint sections.
- Programmatic callers of `dispatch_tool` (the server modules) all build their context from the request key, and the Agent side already rejects keyless calls (merged logical-key work), so no caller needs a new key source; any caller found without one stops the implementation and is reported.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether server-side `pending_timeout_minutes` should ever drive behavior, given the stale-pending sweep is Agent-side | No server-side consumer exists; the dedup document contradicts itself (lines 137 and 178) | Implementation keeps the key validated and explicit at the default and fixes the document; a follow-up decides removal, which would change the store fingerprint | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| config/cicd_mcp_server.toml | Modify | Medium (read at server start) | 2 | 2 authors (high) | not applicable (rsynced) |
| config/file_delete_mcp_server.toml | Modify | Medium | 2 | 2 authors (high) | not applicable (rsynced) |
| config/file_read_mcp_server.toml | Modify | Medium | 2 | 2 authors (high) | not applicable (rsynced) |
| config/file_write_mcp_server.toml | Modify | Medium | 2 | 2 authors (high) | not applicable (rsynced) |
| config/git_mcp_server.toml | Modify | Medium | 2 | 2 authors (high) | not applicable (rsynced) |
| config/github_mcp_server.toml | Modify | Medium | 5 | 2 authors (high) | not applicable (rsynced) |
| config/mdq_mcp_server.toml | Modify | Medium | 2 | 2 authors (high) | not applicable (rsynced) |
| config/rag_pipeline_mcp_server.toml | Modify | Medium | 4 | 2 authors (high) | not applicable (rsynced) |
| config/shell_mcp_server.toml | Modify | Medium | 3 | 2 authors (high) | not applicable (rsynced) |
| config/web_search_mcp_server.toml | Modify | Medium | 2 | 2 authors (high) | not applicable (rsynced) |
| scripts/mcp_servers/server.py | Modify (docstring only) | Low | 12 | 3 authors | not applicable (rsynced) |
| tests/mcp_servers/test_shipped_dedup_config.py | Create | Low | N/A (new) | N/A (new) | not applicable (rsynced) |
| tests/mcp_servers/test_mcp_dispatch.py | Modify | Low | 10 | 2 authors (high) | not applicable (rsynced) |
| tests/mcp_servers/test_server_idempotency_boundary.py | Modify | Low | 2 | 2 authors (high) | not applicable (rsynced) |
| tests/shared/test_tool_constants.py | Modify | Low | 4 | 2 authors (high) | not applicable (rsynced) |
| tests/shared/test_mcp_dedup.py | Modify | Low | 12 | 2 authors (high) | not applicable (rsynced) |
| docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | Modify | Low | N/A (not measured) | N/A (not measured) | not applicable (rsynced) |

## Design
Path B by file count (17 target rows, more than 3), with no public or runtime interface change and no schema change. Baselines (checked in Step 5): `lint-imports` 6 contracts kept; `radon cc scripts/mcp_servers/server.py -n C` reports no block of complexity C or worse; `server.py` is 21580 B, below the 24576 B module size gate, and a docstring edit does not grow it materially; the repository-wide `vulture` and `bandit` findings recorded earlier this session are pre-existing and outside the target files. No Python code under `scripts/` or `tools/` changes logic, so the diff-cover baseline is `N/A: no logic change`; the new and changed lines are tests and one docstring.

Decisions:
- **D-1 Behavior stays unchanged.** Keyless rejection, bounds, and classification already exist; the Plan adds sweeps and pins. Alternative: re-implement a fail-closed dispatcher check (rejected: it already exists at `dispatch.py:418-428`).
- **D-2 Explicit `pending_timeout_minutes` at the default.** Set 10 in every shipped table. Alternative: remove the key from the validator (rejected: it changes the fingerprint and therefore the store identity of existing stores). Compatibility impact: none; fingerprint equality is asserted by test.
- **D-3 Bounds unchanged.** The unresolved bound values are the existing 1..365 and 1..1440; `retention_days` fit with the capacity-monitoring work was verified by the merged code (the retention sweep reads `retention_days` from the same validated config, unchanged).
- **D-4 CI check against canonical tool names.** The canonical-tool-name consistency is the declared `retry_policy` drift test (`test_tool_constants.py:105-151`); the real-file test adds shipped-table validity and unknown-key rejection. A separate tool-name table check has no object.
- **D-5 Real-set sweep.** Tests iterate the real `ALL_SIDE_EFFECTING_TOOLS`, not an injected set, because a synthetic set cannot detect a tool missing from the real set.

Consumer scan: no persisted schema, public API, or shared constant changes, and no symbol is removed or renamed (`not applicable`). Predictable fallout check (checked in Step 3): module size gate `not affected` (see above); pinned counts: a search of `tests/` for assertions on the `[dedup]` table content of shipped files found only the new test's own subject (`not affected`); tool inventory `not affected` (no `tools/*.py`); generated blocks `not affected` (no generated-reference domain changes; the implementation phase runs `uv run python tools/generate_reference_table.py --check` once).

Persisted schema check: `not applicable` (no DDL, schema version, or migration; the store fingerprint is unchanged).

## Implementation steps
1. **Phase 1: Tests that pin existing behavior (REQ-001, REQ-002, REQ-004)**
   - [ ] Add the programmatic dispatcher sweep (REQ-001; tests/mcp_servers/test_mcp_dispatch.py)
   - [ ] Add the HTTP boundary sweep, the non-empty-set assertion, and update the stale module docstring (REQ-001, REQ-006; tests/mcp_servers/test_server_idempotency_boundary.py)
   - [ ] Pin `trigger_workflow` (REQ-002; tests/shared/test_tool_constants.py)
   - [ ] Add the bound tests (REQ-004; tests/shared/test_mcp_dedup.py)
2. **Phase 2: Explicit configuration and its real-file test (REQ-003, REQ-005)**
   - [ ] Create the real shipped-table test first and confirm the explicit-key assertion fails on the current files (REQ-003, REQ-005; tests/mcp_servers/test_shipped_dedup_config.py)
   - [ ] Add `pending_timeout_minutes = 10` to the ten `[dedup]` tables (REQ-003; config/cicd_mcp_server.toml, config/file_delete_mcp_server.toml, config/file_read_mcp_server.toml, config/file_write_mcp_server.toml, config/git_mcp_server.toml, config/github_mcp_server.toml, config/mdq_mcp_server.toml, config/rag_pipeline_mcp_server.toml, config/shell_mcp_server.toml, config/web_search_mcp_server.toml)
3. **Phase 3: Stale statements (REQ-006)**
   - [ ] Correct the middleware docstring (REQ-006; scripts/mcp_servers/server.py)
   - [ ] Update the dedup document (REQ-006; docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md)
4. **Phase 4: Deployment & Verification**
   - [ ] Run `uv run python tools/run_validation_gates.py --full`, the retry-class drift test, and the documentation gates (REQ-001 to REQ-006; all rows)
   - [ ] Hand off to `skills/deploy/SKILL.md` once the change is committed and pushed; deploying is the user's decision and has an approval gate. `config/*_mcp_server.toml` already have `cp` lines in `deploy/deploy.sh`, so `deploy.sh` needs no change; the MCP servers restart to read the explicit key (REQ-003; config files above)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/mcp_servers/test_mcp_dispatch.py | Unit: dispatcher sweep | `uv run pytest tests/mcp_servers/test_mcp_dispatch.py -k keyless` | Pass |
| tests/mcp_servers/test_server_idempotency_boundary.py, scripts/mcp_servers/server.py | Unit: HTTP boundary sweep | `uv run pytest tests/mcp_servers/test_server_idempotency_boundary.py` | Pass |
| tests/shared/test_tool_constants.py | Unit: classification drift | `uv run pytest tests/shared/test_tool_constants.py` | Pass |
| tests/shared/test_mcp_dedup.py | Unit: bounds | `uv run pytest tests/shared/test_mcp_dedup.py -k Section` | Pass |
| config/*_mcp_server.toml, tests/mcp_servers/test_shipped_dedup_config.py | Integration: real-file load | `uv run pytest tests/mcp_servers/test_shipped_dedup_config.py` | Fails before the config edit, passes after |
| scripts/mcp_servers/server.py | Lint, type, security | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml` | No new finding |
| Full suite | Regression | `uv run python tools/run_validation_gates.py --full` | Pass |
| docs/41_db file | Documentation consistency | `rules/tool-gates.md` "When to run which tool" checkers | No finding |

## Risks
- **Risk**: Editing the shipped TOML alters a config the deploy compares or hashes (likelihood: low) → **Mitigation**: the added value equals the default, the fingerprint equality is asserted, and the full suite runs the config-consuming tests.
- **Risk**: The real-file test fails on a developer host whose `LLMAGENT_DB_DIR` is set (likelihood: medium) → **Mitigation**: the test unsets the variable with `monkeypatch.delenv`.
- **Risk**: A sweep over the real set fails because a tool in the set has no registered handler stub in the dispatcher test (likelihood: low) → **Mitigation**: the test supplies its own handler table keyed by the tool name, as the existing test does.
- **Risk**: Pinning every side-effecting tool makes future tool additions touch the sweep (likelihood: low) → **Mitigation**: the sweep iterates the real set, so an added tool is covered without edits.
- **Risk**: `test_mcp_dedup.py` and `test_mcp_dispatch.py` have high churn (12 and 10 commits in 30 days) (likelihood: medium) → **Mitigation**: rebase before each phase and add tests in new classes, not by editing existing ones.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests that pin existing behavior | Completed | — | 20261126-131049 |  |
| 2 | Explicit configuration and its real-file test | Completed | — | 20261126-131049 |  |
| 3 | Stale statements | Completed | — | 20261126-131049 |  |
| 4 | Deployment & Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261126-124822_01_tests_mcp_servers_test_mcp_dispatch.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261126-124822_03_tests_shared_test_tool_constants.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261126-124822_04_tests_shared_test_mcp_dedup.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261126-124822_05_tests_mcp_servers_test_shipped_dedup_config.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-124822_06_config_cicd_mcp_server.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-124822_07_config_file_delete_mcp_server.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-124822_08_config_file_read_mcp_server.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-124822_09_config_file_write_mcp_server.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-124822_10_config_git_mcp_server.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-124822_11_config_github_mcp_server.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-124822_12_config_mdq_mcp_server.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-124822_13_config_rag_pipeline_mcp_server.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-124822_14_config_shell_mcp_server.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-124822_15_config_web_search_mcp_server.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261126-124822_16_scripts_mcp_servers_server.py.md | 1, 3 | Procedure | Completed | — | — |
| implementations/20261126-124822_17_docs_41_db_db_03_07_mcp-dedup-and-execution-snapshot.md.md | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-113156
- **Related target files**: config/cicd_mcp_server.toml, config/file_delete_mcp_server.toml, config/file_read_mcp_server.toml, config/file_write_mcp_server.toml, config/git_mcp_server.toml, config/github_mcp_server.toml, config/mdq_mcp_server.toml, config/rag_pipeline_mcp_server.toml, config/shell_mcp_server.toml, config/web_search_mcp_server.toml, scripts/mcp_servers/server.py, tests/mcp_servers/test_shipped_dedup_config.py, tests/mcp_servers/test_mcp_dispatch.py, tests/mcp_servers/test_server_idempotency_boundary.py, tests/shared/test_tool_constants.py, tests/shared/test_mcp_dedup.py, docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; `dispatch.py:418-428`, `server.py:150-177` | tests/mcp_servers/test_mcp_dispatch.py | Phase 1 | AC-01 | T-01 | Confirmed by repository evidence |
| REQ-001 | Required Changes bullet 1; `test_server_idempotency_boundary.py:34,253-262` | tests/mcp_servers/test_server_idempotency_boundary.py | Phase 1 | AC-01 | T-01 | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 2; `cicd_tools.py:37` | tests/shared/test_tool_constants.py | Phase 1 | AC-02 | T-02 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 2 (explicit pending timeout); Acceptance Criteria bullet 5 | config/cicd_mcp_server.toml | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 2; Acceptance Criteria bullet 5 | config/file_delete_mcp_server.toml | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 2; Acceptance Criteria bullet 5 | config/file_read_mcp_server.toml | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 2; Acceptance Criteria bullet 5 | config/file_write_mcp_server.toml | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 2; Acceptance Criteria bullet 5 | config/git_mcp_server.toml | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 2; Acceptance Criteria bullet 5 | config/github_mcp_server.toml | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 2; Acceptance Criteria bullet 5 | config/mdq_mcp_server.toml | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 2; Acceptance Criteria bullet 5 | config/rag_pipeline_mcp_server.toml | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 2; Acceptance Criteria bullet 5 | config/shell_mcp_server.toml | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 2; Acceptance Criteria bullet 5 | config/web_search_mcp_server.toml | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Acceptance Criteria bullet 2 (real file loads) | tests/mcp_servers/test_shipped_dedup_config.py | Phase 2 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-004 | Required Changes bullet 3; `mcp_dedup_config.py:38-44`; `test_mcp_dedup.py:805-815` | tests/shared/test_mcp_dedup.py | Phase 1 | AC-04 | T-04 | Confirmed by repository evidence |
| REQ-005 | Required Changes bullet 4; Acceptance Criteria bullets 2-3 | tests/mcp_servers/test_shipped_dedup_config.py | Phase 2 | AC-05 | T-03 | Derived from confirmed evidence |
| REQ-006 | Documentation Impact; `server.py:150-177` stale docstring | scripts/mcp_servers/server.py | Phase 3 | AC-06 | T-05 | Confirmed by repository evidence |
| REQ-006 | Documentation Impact; `server.py` docstring cited by the boundary test module docstring | tests/mcp_servers/test_server_idempotency_boundary.py | Phase 1 | AC-06 | T-05 | Confirmed by repository evidence |
| REQ-006 | Documentation Impact; `db_03_07...md:134-138,178` | docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | Phase 3 | AC-06 | T-05 | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261126-124822 -->