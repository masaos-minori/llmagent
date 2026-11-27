## Goal
- Make one MDQ file operation atomic across documents, chunks, trigger-driven FTS5 changes, and `index_state` under a single caller-owned transaction, delete `index_state` by exact canonical key, and classify the MDQ write tools as non-retryable so they fail closed when the durable dedup store is unavailable.

## Priority
High

## Scope
- **In-Scope**:
  - One caller owns the connection and the transaction for a file operation; lower-level writers and delete helpers no longer commit on their own.
  - `index_state` is written inside the same transaction as the document, chunk, and FTS5 changes, and only after the postconditions are checked.
  - `index_state` deletion uses the exact canonical key, not a prefix `LIKE`.
  - Forced refresh records `index_state` for the files it indexes.
  - The declared `retry_policy` of `index_paths` and `refresh_index` becomes `never`, and the reference data in `scripts/shared/tool_constants.py` moves with it.
  - Postconditions (document, chunk, FTS5, state rows) are checked before an operation reports success.
- **Out-of-Scope**: dedup ownership, lease, heartbeat, and terminal-row mechanics; keyless-key rejection; directory-deletion transaction shape (recorded as an unknown, not decided here).
- **Dependencies**: depends on the mdqmcp003 plan (per-file outcomes and the rule that `index_state` is updated only after commit — this Plan supplies the transaction that makes that rule hold and does not redefine it) and on the mdqmcp004 plan (the source-hash columns the postcondition check reads); related to the mcpai001 and mcpdd001 issues for shared dedup behavior, which is not reimplemented here. Blocks mdqmcp006, mdqmcp007, and mdqmcp008.
  - **Depends on**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md` | all | the per-file result statuses and counters this Plan's postcondition reporting uses, and the rule that state is updated only after commit; the same `indexer.py` lines would otherwise be rewritten twice
  - **Depends on**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md` | all | the postcondition check compares the stored source hash with the current file, which requires the columns that plan adds; the refresh comparison and the transaction ownership land in the same `indexer.py` functions

## Background
Source issue: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md` (consolidated MDQ MCP backlog, Issue 5).

Adversarial verification against current source (evidence revision in Traceability):
- Confirmed: `scripts/mcp_servers/mdq/index_delete.py` deletes `index_state` with `LIKE 'mtime:<path>%'` (line 31), so a path whose key is a literal prefix of another key sweeps up the longer key; the behavior is pinned by `tests/mcp_servers/mdq/test_index_delete.py` (`TestIndexStateWildcardMatchIsCharacterizedAsIs`, lines 180-206) and the helper commits inside itself (line 34).
- Corrected: `config/mcp_dedup.toml` does not exist in this repository. The `[retry_class]` dispatcher mirror was removed; the declared `retry_policy` is the sole authority (`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` Decision Detail 18). `scripts/shared/tool_constants.py` `RETRYABLE_TOOLS` is reference data only, drift-checked against the declarations by `tests/shared/test_tool_constants.py` (line 142). The classification change therefore lands in `scripts/mcp_servers/mdq/mdq_tools.py` (declared `retry_policy`, lines 172 and 205) plus the reference set, not in a TOML file.
- Corrected: `scripts/mcp_servers/mdq/index_write.py` already writes documents and chunks in one `BEGIN IMMEDIATE` transaction (lines 71, 123), so per-file write atomicity is not the gap. The gap is that the writer is called through a connection it does not own: `indexer.py::_index_single_file()` opens its own connection per file (line 103) while `index_state` is written and committed on the refresh connection (`indexer.py` lines 321-325), so one file operation spans two connections and two commits.
- Confirmed: forced refresh never updates `index_state` (`indexer.py::_reindex_forced()`, lines 274-290), so a forced re-index leaves the incremental state at the pre-force value.
- Confirmed: the fail-open claim holds as current behavior. `scripts/mcp_servers/dedup_gate.py` (line 273) dispatches a retryable tool with the audited `store_error` marker, and `scripts/mcp_servers/dispatch.py` (line 293) fails closed only for non-retryable tools. Changing the classification activates the existing fail-closed path; no lease or ownership logic is added.
- Confirmed: FTS5 trigger effects are covered by the same transaction — the `chunks_ad` trigger fires on the `chunks` statements inside the transaction (`index_delete.py` line 27 comment), so the issue's stop condition is not triggered.
- Confirmed: no postcondition check exists before a file operation reports success; `_index_single_file()` logs a `sqlite3.Error` and returns, so the caller counts a failed write as indexed.

## Problem
A file operation can leave partial state across two connections; deleting `a.md` can delete `a.md.bak` state; forced refresh leaves stale incremental state; and retryable MDQ writes continue when the dedup store is unavailable.

## Reason for Change
Data integrity and retry safety: a retry contract cannot be safe over partial database operations.

## Implementation Intent
One caller owns the connection and the transaction for one file operation; the operation's rows and its `index_state` record commit together after postconditions are checked. MDQ writes are non-retryable and fail closed on dedup-store failure until operation-specific reconciliation is proven.

## Requirements
- `REQ-001`: one caller owns the connection and transaction for a file operation; writers and delete helpers do not commit inside themselves.
- `REQ-002`: documents, chunks, trigger-driven FTS5 changes, and `index_state` for one file commit in one transaction, and `index_state` is written only after the postconditions are checked.
- `REQ-003`: `index_state` is deleted by the exact canonical key.
- `REQ-004`: forced refresh records `index_state` for the files it indexes.
- `REQ-005`: `index_paths` and `refresh_index` declare `retry_policy = never`, and `RETRYABLE_TOOLS` reference data moves with the declaration.
- `REQ-006`: postconditions for documents, chunks, FTS5, and `index_state` are checked before an operation reports success.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261127; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/index_write.py` | Modify | Take the caller-owned connection; remove the internal `BEGIN IMMEDIATE`/`COMMIT` ownership and report failure to the caller instead of swallowing it | REQ-001, REQ-002, REQ-006, AC-1 | `write_document_chunks()` (line 54) runs `conn.execute("BEGIN IMMEDIATE")` (line 71) and `conn.execute("COMMIT")` (line 123) itself | `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py` | Verified |
| `scripts/mcp_servers/mdq/index_delete.py` | Modify | Remove the internal commit; delete `index_state` by the exact canonical key instead of the prefix `LIKE` | REQ-001, REQ-003, AC-2 | `DELETE FROM index_state WHERE key LIKE ?` (line 31); `conn.commit()` (line 34) inside the helper | `tests/mcp_servers/mdq/test_index_delete.py` | Verified |
| `scripts/mcp_servers/mdq/indexer.py` | Modify | Own the connection and transaction for one file operation; write `index_state` inside that transaction after the postcondition check; update state during forced refresh | REQ-001, REQ-002, REQ-004, REQ-006, AC-1, AC-2 | `_index_single_file()` opens its own connection (line 103); the state insert and commit are separate from the write (lines 321-325); `_reindex_forced()` never touches `index_state` (lines 274-290) | `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_tools.py` | Modify | Declare `retry_policy = never` for `index_paths` and `refresh_index` | REQ-005, AC-3 | Both tools declare `"retry_policy": "same_logical_call_only"` (lines 172, 205), which `shared.tool_metadata.RETRY_POLICY_RETRYABLE_VALUES` maps to the retryable class | `tests/shared/test_tool_constants.py` | Verified |
| `scripts/shared/tool_constants.py` | Modify | Remove `index_paths` and `refresh_index` from `RETRYABLE_TOOLS` so the reference data matches the declarations | REQ-005, AC-3 | `RETRYABLE_TOOLS` lists the mdq tools (lines 202-203); the comment states the declared field is the authority and this set only detects drift | `tests/shared/test_tool_constants.py` | Verified |
| `tests/mcp_servers/mdq/test_index_delete.py` | Modify | Flip the wildcard characterization to the exact canonical key; move the helper-commit pinning to caller-owned transaction behavior | REQ-001, REQ-003, AC-2 | `TestIndexStateWildcardMatchIsCharacterizedAsIs` (lines 180-206) pins the over-match; `TestCommitsTheTransaction` pins the helper commit | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` | Modify | Postcondition check and state write move into the caller-owned transaction; forced refresh now records state | REQ-002, REQ-004, REQ-006, AC-2 | The file pins the current state insert and commit order (line 486) and `_rollback_quietly` behavior (lines 639-657) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_index_serialization.py` | Modify | Serialization proof runs against the single caller-owned transaction; a mid-operation failure leaves no partial state | REQ-001, AC-1 | The file proves `_index_lock` serializes `index_paths` and `refresh_index` over the current per-file connection | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py` | Create | New file: fault injection at commit, trigger, and state-update points; a failed file operation leaves no partial state; postconditions checked before success | REQ-001, REQ-002, REQ-006, AC-1, AC-4 | Does not exist; `tests/mcp_servers/mdq/` holds 35 test files and none injects a mid-transaction failure | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_index_state_consistency.py` | Create | New file: shared-prefix, `%`, and `_` filenames resolve to one exact key; forced refresh then incremental refresh leaves correct state | REQ-003, REQ-004, AC-2 | Does not exist; the only shared-prefix coverage is the characterization test that pins the current over-match | itself | Verified |
| `tests/shared/test_tool_constants.py` | Modify | The retry-class drift check reflects the new mdq class; the mdq tools are no longer in the reference set | REQ-005, AC-3 | `TestRetryClassDriftConsistency` compares the declared policies with `RETRYABLE_TOOLS` (line 142) | itself | Verified |
| `tests/mcp_servers/test_mcp_dispatch.py` | Modify | The injected declared policies for the mdq tools change to `never`, so the overlay path mirrors the new class | REQ-005, AC-3 | The fixture injects `"index_paths"` and `"refresh_index"` as `same_logical_call_only` (lines 161-162) to mirror the real declarations | itself | Verified |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | State the transaction ownership, the postcondition check, and the temporary non-retryable classification with its reason | REQ-001, REQ-006, AC-1, AC-4 | The doc has no transaction, postcondition, or retry statement today (checked by `grep` for `transaction`, `atomic`, `retry`) | `uv run python tools/check_docs_content_policy.py` | Verified |

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
- Write every `File Path` cell, every `tests/...py` path in `Related Tests`, and every path in
  `Implementation steps` in backticks: `tools/close_procedures_batch.py` and the companion check read
  only backticked paths. `uv run python tools/backtick_plan_related_tests.py plans/{filename}.md`
  normalizes a Plan, and `tools/check_workitem_structure.py` reports a plain path
  (`plain-path-citation`).

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/tool_metadata.py` | `RETRY_POLICY_VALUES` and `RETRY_POLICY_RETRYABLE_VALUES` define what `never` means and how the class is derived | REQ-005 |
| `scripts/mcp_servers/dedup_gate.py` | The store-error branch and the non-retryable refusal are the existing fail-closed path this Plan activates; read to confirm nothing is reimplemented | REQ-005 |
| `scripts/mcp_servers/dispatch.py` | The dispatcher boundary that refuses non-retryable tools on store unavailability | REQ-005 |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Decision Detail 18 owns retry classification and records that the config mirror is removed; read to confirm no ADR decision change is needed — not modified | REQ-005, UNK-03 |
| `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md` | The dedup contract the MDQ classification must stay consistent with — not modified | REQ-005 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002, REQ-006): a failed file operation leaves no partial state, proven by fault injection at commit, trigger, and state-update points.
- `AC-2` (REQ-003, REQ-004): deleting `a.md` cannot delete `a.md.bak` state; forced refresh leaves correct incremental state.
- `AC-3` (REQ-005): MDQ writes are non-retryable and are refused when the dedup store is unavailable; the reference data and the declarations agree.
- `AC-4` (REQ-006): postconditions are checked before success, and the doc states the ownership and postcondition rule.

## Tests
- Fault injection at commit, trigger, state-update, and mid-delete points (REQ-001, REQ-002, REQ-006; `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py`).
- Shared-prefix, `%`, and `_` filenames against the exact-key delete (REQ-003; `tests/mcp_servers/mdq/test_mdq_index_state_consistency.py`, `tests/mcp_servers/mdq/test_index_delete.py`).
- Forced refresh followed by incremental refresh (REQ-004; `tests/mcp_servers/mdq/test_mdq_index_state_consistency.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`).
- Store-failure refusal for both write tools and the retry-class consistency check (REQ-005; `tests/shared/test_tool_constants.py`, `tests/mcp_servers/test_mcp_dispatch.py`).
- Run ruff, mypy, and the full test suite (`rules/toolchain.md` sequence via `uv run python tools/run_validation_gates.py`).

## Documentation Impact
Yes. Per `docs/00_index.md` "Document References by Task":
- MCP server spec row drives `docs/22_mcp/mcp_04_04_mdq.md`: transaction ownership, the postcondition check, and the temporary non-retryable classification with its reason.
- No ADR change: retry classification authority already exists (ADR-002.02 Decision Detail 18); a change to ADR-owned wording would need a maintainer approval record (governance_01, governance_05) and is not written or simulated here. The fail-open/fail-closed rule is already documented in `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` and `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md`; this Plan changes only the mdq tool's declared value, so those docs need no edit. Doc content policy applies; run `uv run python tools/check_docs_content_policy.py` per `rules/tool-gates.md`.

## Assumptions
- The temporary non-retryable classification is recorded as temporary in the mdq doc and is reconsidered only after operation-specific reconciliation is proven; no reconciliation mechanism is designed here.
- The canonical `index_state` key is `mtime:<path>` as produced by `indexer.py` (line 316); the exact-key delete uses the same string the writer stores, so no key-format change is introduced.
- Overlap with the mdqmcp003 and mdqmcp004 plans on `scripts/mcp_servers/mdq/indexer.py` and `docs/22_mcp/mcp_04_04_mdq.md` is a compatible ordering overlap: this Plan executes after both per the dependency bullets.
- Bus factor is 1 for the mdq module set (single author; `scripts/shared/tool_constants.py` shows the same author under name variants).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether directory deletion should be one transaction or structured partial success | No owner decision recorded | Plan default: keep the current per-directory structured partial success (documented in `indexer.py::_delete_stale_entries()`), and define one transaction only for a single file; confirm with the owner before widening the transaction to a directory | False |
| UNK-02 | Where the repository layer for connection ownership should live | No owner decision recorded | Plan default: the existing indexer entry points own the connection and transaction; no new repository module is created; confirm with the owner if a separate repository layer is required | False |
| UNK-03 | Whether the non-retryable classification requires an ADR change | No maintainer approval record exists for any new ADR wording | Default: no ADR change — the declared field is already the authority; only the mdq tool's declared value changes, so the ADR wording stays as is | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/index_write.py` | Modify | mdq writer path; the caller signature changes for every writer call site | 0 | 1 | None |
| `scripts/mcp_servers/mdq/index_delete.py` | Modify | mdq deletion path; key semantics change for existing `index_state` rows | 0 | 1 | None |
| `scripts/mcp_servers/mdq/indexer.py` | Modify | mdq index and refresh paths; connection ownership changes for both tools | 0 | 1 | None |
| `scripts/mcp_servers/mdq/mdq_tools.py` | Modify | Agent-side retry class for two tools; dedup gate branch changes from fail-open to fail-closed | 1 | 1 | None |
| `scripts/shared/tool_constants.py` | Modify | Reference data only; drift checks and generated docs read it | 8 | 1 | None |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Documentation only | — | 1 | None |

## Design
Path B classification rationale: cross-module change (mdq layer plus `scripts/shared/`) with more than three target files, and a semantic change to the retry-class contract that other consumers read.

Design decisions (narrow `python-design` application):
- Transaction ownership: the indexer entry points (`index_paths`, `refresh_index`) own the connection and the transaction; `write_document_chunks()` and `delete_file_from_index()` become statement executors that never commit. Alternative considered — keep the writer's own transaction and make `index_state` writes part of it; rejected because the state write and the row writes would still sit on two connections, so a failure between them leaves partial state.
- Failure reporting: the writer returns or raises instead of logging and returning, so the caller can distinguish a failed operation from a successful one; this is the boundary mdqmcp003's per-file DTO consumes, and the postcondition check runs before the commit.
- Exact key: `index_state` is deleted by `key = ?` with the same canonical string the writer stores. Alternative considered — escape `%` and `_` in the `LIKE` pattern; rejected because a prefix match is not the intended identity and escaping keeps the over-match risk for shared prefixes.
- Consumer scan for `RETRYABLE_TOOLS`: consumers are `scripts/shared/tool_metadata.py` (no change), `tests/shared/test_tool_constants.py` (target row), and the docs rows named above; `scripts/agent/tool_call_identity.py::_classify_retry_class` reads the declared field, not the set, so it is unaffected.
- Consumer scan for `retry_policy` declarations: `tests/mcp_servers/test_mcp_dispatch.py` injects the mdq values as expected data (target row); `tests/agent/test_tool_approval_paths.py`, `tests/agent/test_tool_approval_repos.py`, and `tests/agent/test_tool_runner.py` build their own fixtures and do not read the mdq declarations, so they are not affected.
- Predictable fallout: module size — all target source files are under the 24576 B gate (largest `scripts/mcp_servers/mdq/indexer.py` at 14835 B) and stay under it; skill size — not affected; pinned counts — no test pins the `RETRYABLE_TOOLS` membership for mdq beyond the drift comparison, which moves with the declaration; tool inventory — not affected (no tool added or removed); generated blocks — the doc edit is prose, and `uv run python tools/generate_reference_table.py --check` is run as a validation gate.
- Import graph: `uv run lint-imports` reports 6 contracts kept; the mdq layer imports only `db` and `shared`, and no new cross-layer import is introduced by moving transaction ownership inside the mdq module. Radon: the mdq functions are grade A; the postcondition check is a small helper that keeps grade A. Vulture (min-confidence 80) and bandit on `scripts/mcp_servers/mdq/` and `scripts/shared/tool_constants.py`: no findings.
- Stop condition check: one transaction can cover the FTS5 trigger effects because the `chunks_ad` trigger fires inside the same transaction as the `chunks` statements; the issue's stop condition is not triggered.

## Implementation steps
1. **Phase 1: Characterization tests first**
   - [ ] Confirm partial state on current code with fault injection before any behavior change (REQ-001, REQ-002, AC-1; `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py`)
   - [ ] Keep the shared-prefix over-match pinned as current behavior until the exact-key change lands (REQ-003, AC-2; `tests/mcp_servers/mdq/test_index_delete.py`)
2. **Phase 2: Caller-owned transaction**
   - [ ] Make the writer and the delete helpers statement executors that never commit (REQ-001; `scripts/mcp_servers/mdq/index_write.py`, `scripts/mcp_servers/mdq/index_delete.py`)
   - [ ] Move `index_state` writes into the caller-owned transaction and check postconditions before success (REQ-002, REQ-006; `scripts/mcp_servers/mdq/indexer.py`)
   - [ ] Update `index_state` during forced refresh (REQ-004; `scripts/mcp_servers/mdq/indexer.py`)
   - [ ] Flip the helper-commit and wildcard characterizations to the exact key and the caller-owned transaction (REQ-001, REQ-003, AC-2; `tests/mcp_servers/mdq/test_index_delete.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, `tests/mcp_servers/mdq/test_mdq_index_serialization.py`)
3. **Phase 3: Non-retryable classification**
   - [ ] Declare `retry_policy = never` for `index_paths` and `refresh_index` (REQ-005; `scripts/mcp_servers/mdq/mdq_tools.py`)
   - [ ] Remove the mdq tools from `RETRYABLE_TOOLS` reference data (REQ-005; `scripts/shared/tool_constants.py`)
   - [ ] Move the drift check and the injected expected policies to the new class (REQ-005, AC-3; `tests/shared/test_tool_constants.py`, `tests/mcp_servers/test_mcp_dispatch.py`)
4. **Phase 4: Documentation and full validation**
   - [ ] State transaction ownership, postconditions, and the temporary non-retryable classification with its reason (REQ-001, REQ-006, AC-4; `docs/22_mcp/mcp_04_04_mdq.md`)
   - [ ] Store-failure refusal tests for both write tools (REQ-005, AC-3; `tests/mcp_servers/test_mcp_dispatch.py`)
   - [ ] Run the full validation sequence: `uv run python tools/run_validation_gates.py`, then `uv run pytest` (all requirements)

### Release units
N/A: no release unit — every phase passes validation alone because the classification change and its drift check land in the same phase.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/mdq/index_write.py` | Integration: fault injection at commit | `uv run pytest tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py` | A failed operation leaves no partial state |
| `scripts/mcp_servers/mdq/index_delete.py` | Unit: exact-key delete with shared-prefix, `%`, `_` names | `uv run pytest tests/mcp_servers/mdq/test_mdq_index_state_consistency.py tests/mcp_servers/mdq/test_index_delete.py` | `a.md` deletion does not remove `a.md.bak` state |
| `scripts/mcp_servers/mdq/indexer.py` | Integration: forced then incremental refresh | `uv run pytest tests/mcp_servers/mdq/test_mdq_incremental_refresh.py tests/mcp_servers/mdq/test_mdq_index_state_consistency.py` | Forced refresh leaves correct state |
| `scripts/mcp_servers/mdq/mdq_tools.py` | Unit: declared policy and store-failure refusal | `uv run pytest tests/shared/test_tool_constants.py tests/mcp_servers/test_mcp_dispatch.py` | Both tools are non-retryable and refused on store failure |
| `scripts/shared/tool_constants.py` | Unit: retry-class drift check | `uv run pytest tests/shared/test_tool_constants.py` | Declarations and reference data agree |
| `docs/22_mcp/mcp_04_04_mdq.md` | Content policy and reference-table drift | `uv run python tools/check_docs_content_policy.py`, `uv run python tools/generate_reference_table.py --check` | Pass |
| Whole module | Lint, types, security | `uv run python tools/run_validation_gates.py` | Pass |

## Risks
- **Risk**: existing `index_state` rows written by the prefix-key path may not match the exact canonical key after the change → **Mitigation**: the key string is produced by the same writer line that stores it, so existing rows keep the same form; the recreation path for `mdq.sqlite` (derived store, ADR-008) is the fallback if a drifted row is found.
- **Risk**: removing the writer's own transaction can leave an open transaction when a caller forgets to commit → **Mitigation**: one owner commits, and the existing `_rollback_quietly()` path covers the failure branch; the fault-injection tests pin both.
- **Risk**: the classification change alters behavior for callers that relied on replay → **Mitigation**: the change is temporary and recorded in the mdq doc; the existing non-retryable refusal path is used, so no new mechanism is added.
- **Risk**: overlap with the mdqmcp003 and mdqmcp004 plans on `scripts/mcp_servers/mdq/indexer.py` and `docs/22_mcp/mcp_04_04_mdq.md` → **Mitigation**: execution order fixed by the dependency bullets; Step 8b overlap check records the judgement.
- **Risk**: the mdqmcp001 plan also targets `scripts/mcp_servers/mdq/mdq_tools.py` → **Mitigation**: compatible overlap, no contradiction — that plan changes `config_dependent` and this Plan changes `retry_policy`; the fields are independent declarations.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization tests first | Pending | — | — | Partial state confirmed on current code before behavior change |
| 2 | Phase 2: caller-owned transaction | Pending | — | — | Writers and delete helpers stop committing; state written inside the transaction after postconditions |
| 3 | Phase 3: non-retryable classification | Pending | — | — | Declared policy and reference data move together |
| 4 | Phase 4: documentation and full validation | Pending | — | — | mdq doc statements; store-failure refusal tests; full validation sequence |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-171503
- **Evidence revision**: 41b423e73a5c2d98ae017a67a6059fcb3c75fd81
- **Related target files**: `scripts/mcp_servers/mdq/index_write.py`, `scripts/mcp_servers/mdq/index_delete.py`, `scripts/mcp_servers/mdq/indexer.py`, `scripts/mcp_servers/mdq/mdq_tools.py`, `scripts/shared/tool_constants.py`, `tests/mcp_servers/mdq/test_index_delete.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, `tests/mcp_servers/mdq/test_mdq_index_serialization.py`, `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py`, `tests/mcp_servers/mdq/test_mdq_index_state_consistency.py`, `tests/shared/test_tool_constants.py`, `tests/mcp_servers/test_mcp_dispatch.py`, `docs/22_mcp/mcp_04_04_mdq.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent; one caller owns the connection and transaction | `scripts/mcp_servers/mdq/index_write.py` | Phase 2 | AC-1 | `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes; remove internal commits from lower-level delete helpers | `scripts/mcp_servers/mdq/index_delete.py` | Phase 2 | AC-1 | `tests/mcp_servers/mdq/test_index_delete.py` | Confirmed by repository evidence |
| REQ-001 | Background; verified the writer is called through a connection it does not own (`indexer.py` line 103) | `scripts/mcp_servers/mdq/indexer.py` | Phase 2 | AC-1 | `tests/mcp_servers/mdq/test_mdq_index_serialization.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; include documents, chunks, FTS5 trigger effects, and `index_state` in one file transaction | `scripts/mcp_servers/mdq/indexer.py` | Phase 2 | AC-1 | `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py` | Confirmed by repository evidence |
| REQ-003 | Problem; prefix `LIKE` can delete another filename's state — verified at `index_delete.py` line 31 | `scripts/mcp_servers/mdq/index_delete.py` | Phase 2 | AC-2 | `tests/mcp_servers/mdq/test_index_delete.py` | Confirmed by repository evidence |
| REQ-003 | Testing Expectations; shared-prefix, `%`, and `_` filenames | `tests/mcp_servers/mdq/test_mdq_index_state_consistency.py` | Phase 1 | AC-2 | itself | Confirmed by repository evidence |
| REQ-004 | Problem; forced refresh can leave stale state — verified `_reindex_forced()` never updates `index_state` | `scripts/mcp_servers/mdq/indexer.py` | Phase 2 | AC-2 | `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; classify both write tools as non-retryable — verified the declarations at `mdq_tools.py` lines 172, 205 | `scripts/mcp_servers/mdq/mdq_tools.py` | Phase 3 | AC-3 | `tests/shared/test_tool_constants.py` | Confirmed by repository evidence |
| REQ-005 | Constraints; keep the reference data consistent with the declarations (CI check) | `scripts/shared/tool_constants.py` | Phase 3 | AC-3 | `tests/shared/test_tool_constants.py` | Confirmed by repository evidence |
| REQ-005 | Background; verified the fail-open branch for retryable tools at `dedup_gate.py` line 273 | `tests/mcp_servers/test_mcp_dispatch.py` | Phase 4 | AC-3 | itself | Confirmed by repository evidence |
| REQ-006 | Required Changes; check postconditions before success | `scripts/mcp_servers/mdq/indexer.py` | Phase 2 | AC-4 | `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py` | Confirmed by repository evidence |
| REQ-006 | Documentation Impact; transaction ownership and postconditions | `docs/22_mcp/mcp_04_04_mdq.md` | Phase 4 | AC-4 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |
