# Enforce MDQ foreign keys and read the workflow DB path from configuration

## Goal
- Make every MDQ read/write connection enforce SQLite foreign keys, and make the workflow database path an `agent.toml` key with at most one default in code.
- Keep the two deploy schema gates and the docs claims consistent with the new key (scope amendments recorded below).

## Priority
Medium — carried from the source issue (`issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md` §Priority).

## Scope
- **Source issue**: `issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md` (package `ADRCHK2-M07`, merged from ADRCHK-M21, M22; review findings N27, N40).
- **Task size**: Path B (Medium) — two independent production changes (MDQ FK pragmas; workflow DB path configuration) across 5 production files, 1 config file, 2 generated artifacts, 3 docs/comment files, and 5 test files.
- **Issue constraints inherited**:
  - Orphan chunks: report the count only; do not clean up (measured here: 0, see Problem P2).
  - No migrations, aliases, shims, tolerant fallbacks, or history-style comments (Current-Specification-Only).
  - Do not hand-edit generated files (`registry/manifests/*.yaml`, guarded blocks); regenerate with `tools/generate_reference_table.py`.
  - Change only Target Files; required changes outside the issue's list are recorded as scope amendments (S1–S3 in Unknowns), not silently absorbed.
  - Re-run the issue's named searches before editing (done at plan time; evidence below).
  - No ADR decision, invariant, Blocking value, or authority edge is changed by this Plan (see P5), so no approval record is required.

## Background
- `apply_connection_pragmas()` (`scripts/db/helper.py:35-54`) applies `journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout`, and — only when `write_mode=True` — `PRAGMA foreign_keys=ON` (`helper.py:53-54`). The helper's docstring states the FK/journal/synchronous statements "are write-path policy".
- MDQ opens its own `sqlite3.connect()` and calls the shared pragma helper with `write_mode=False` on every data connection (`mdq_service.py:132-133`, `db_schema.py:121-123`) and on the health probe (`health_check.py:157`).
- The workflow path has two code-level defaults: the `DbConfig` field default (`scripts/db/config.py:29`) and the `build_db_config()` fallback literal (`scripts/db/config.py:97`). `config/agent.toml` has no `workflow_db_path` key; the manifest records `in_agent_toml: false` (`registry/manifests/db_schema_versions.yaml:10-13`).
- The Agent startup path rejects unknown top-level `agent.toml` keys: `ProductionConfigValidator.validate()` calls `_check_unknown_production_keys()` (`scripts/agent/production_config_validator.py:298, 368`) against a key allowlist built at `production_config_validator.py:150-209`; `workflow_db_path` is not in it.

## Problem
- **P1 (verified) — FK is off on every MDQ connection.** `helper.py:53-54` gates `PRAGMA foreign_keys=ON` behind `write_mode=True`; all MDQ call sites pass `write_mode=False` (`mdq_service.py:132-133`, `db_schema.py:121-123`, `health_check.py:157`). Verified with `rg` and direct reading, matching the issue's claim.
- **P2 (partially refuted) — the orphan-damage narrative does not describe current production code.** The issue claims "deleting a document leaves orphan chunks and search returns content from deleted files." No production path deletes a `documents` row without first deleting its `chunks` rows: `index_delete.py:28-29` deletes chunks then documents; `index_write.py:73-75` deletes chunks before `INSERT OR REPLACE INTO documents`. The cascade clause (`db_schema.py:40`) is therefore a safety net that never runs today, not a live data-loss bug. **Orphan count measured on this host's `/opt/llm/db/mdq.sqlite` (2026-11-18): orphan chunks = 0, orphan `index_state` mtime rows = 0** (`chunks`=2403, `documents`=172). The remaining defect is the missing write-time enforcement guarantee (a chunk row could reference a nonexistent document; an external/manual delete silently orphans chunks).
- **P3 (verified) — duplicated hard-coded workflow default.** `DbConfig.workflow_db_path` default (`config.py:29`) and `build_db_config()`'s `cfg.get("workflow_db_path", "/opt/llm/db/workflow.sqlite")` fallback (`config.py:97`) carry the same literal twice; `config/agent.toml` has no such key (`agent.toml:7-8` list only `rag_db_path`, `session_db_path`).
- **P4 (verified, scope-critical) — adding the key requires registering it in the validator.** `_check_unknown_production_keys` (`production_config_validator.py:298`) compares every top-level key against the allowlist; `workflow_db_path` is absent from the subsystem-keys block (`production_config_validator.py:186-206`, which does include `rag_db_path`, `session_db_path`). Adding the key to `agent.toml` without registration would fail every Agent startup (`config_builders.py:104`). `scripts/agent/production_config_validator.py` is not in the issue's Target Files list → scope amendment S1.
- **P5 (partially refuted) — the ADR motivation is overstated, but the change is compliant.** ADR-002 states the Agent row's Required Keys are only the keys with no built-in default: "every other key has a built-in default" (`docs/10_adr/adr_02_01_002_platform-config-isolation.md:81, 85`). A Python-level default is therefore already ADR-compliant; the issue's "ADR-002 and ADR-008 say database paths come from configuration" is a motivation, not a violated invariant. Adding an operator-facing key and collapsing two code defaults to one does not change any ADR decision, invariant, Blocking value, or authority edge, so no approval record is needed.
- **P6 (verified) — both deploy schema gates assume the key is absent and will break on a repo-level key.** `tests/deploy/test_init_db_schema_gate.py::_write_config` (`:172-191`) inserts a pinned `workflow_db_path` line "before the first table header" precisely because the repo copy lacks it; `tests/deploy/test_init_db_eventbus_schema.py` (`:107-115`) prepends the pinned key. Once `config/agent.toml` carries the key, the rewrite already re-points its `/opt/llm/db/` value via the tests' existing `replace("/opt/llm/db/", db_dir)` step (`test_init_db_schema_gate.py:181`, `test_init_db_eventbus_schema.py:102-106`), and the extra insertion creates a duplicate top-level TOML key → `tomllib` parse error. Both gates must drop the pinning step → scope amendment S2. `tests/conftest.py:129-131`'s docstring ("agent.toml does not set workflow_db_path (the production config validator rejects the key)") becomes a stale claim → scope amendment S3 (comment-only).
- **P7 (verified) — two docs claims become false.** `docs/41_db/db_01_architecture_and_schema-overview-and-config.md:34` states "`workflow.sqlite` uses a Python-level default path (`workflow_db_path` is not an `agent.toml` key)". The auto-generated DB Path Reference in `docs/90_deployment/deployment_01_deployment.md` (guarded block at `:349-359`) shows "No (Python-level default in `scripts/db/config.py`)" and must be regenerated, not hand-edited.
- **Issue's open question resolved:** `scripts/mcp_servers/mdq/indexer.py` — deletes go through `delete_file_from_index()` (`index_delete.py:21-31`, called from `indexer.py:251`) and `write_document_chunks()` (`index_write.py:56-118`), both on connections from `service._get_db_connection()` (`indexer.py:103, 410`). `indexer.py` itself needs no change.

## Reason for Change
- FK enforcement is the guarantee that the `chunks` → `documents` relationship (`db_schema.py:40`) holds at write time on every MDQ connection; today nothing enforces it (P1).
- The workflow path should be operator-configurable like `rag_db_path`/`session_db_path`, with exactly one code default (P3).
- The validator allowlist and the two deploy gates are load-bearing consumers of the current no-key state; ignoring them breaks startup and the test suite (P4, P6).

## Implementation Intent
- Enable `foreign_keys` on every MDQ data connection: pass `write_mode=True` in `mdq_service._get_db_connection()` and `db_schema.create_production_tables()`. The health probe keeps `write_mode=False` — FK is a write-path policy (`helper.py:42-46` docstring) and the probe only reads schema/stats (`health_check.py:155-166`); this deviation from the issue's "every MDQ connection" wording is recorded in Unknowns UNK-02.
- Add `workflow_db_path = "/opt/llm/db/workflow.sqlite"` to `config/agent.toml`; collapse code defaults to the single `DbConfig` field default (remove the `build_db_config()` fallback literal by omitting the argument when the key is absent).
- Register `workflow_db_path` in the validator allowlist.
- Regenerate the manifest and the deployment guarded table; fix the two deploy gates and the stale docs/comment claims.

## Requirements
- **REQ-001 (test-first)**: Add a cascade-delete test built on the production connection factory (`MdqService._get_db_connection()`) that deletes a `documents` row via raw SQL without touching `chunks` and asserts the chunks are gone. It must fail before REQ-002 lands.
- **REQ-002**: `mdq_service.py:132-133` and `db_schema.py:121-123` call `apply_connection_pragmas(..., write_mode=True)`; no MDQ file writes a raw `PRAGMA foreign_keys` statement (the shared helper remains the single pragma owner).
- **REQ-003**: `config/agent.toml` gains `workflow_db_path = "/opt/llm/db/workflow.sqlite"` in the Infrastructure section (same value as today, so no physical path moves).
- **REQ-004**: `scripts/db/config.py` keeps exactly one code default — the `DbConfig` field default (`:29`); `build_db_config()` reads the key from `agent.toml` and omits the argument when absent instead of repeating the literal (`:97`).
- **REQ-005**: `scripts/agent/production_config_validator.py` adds `"workflow_db_path"` to the subsystem-keys block (`:186-206`) so `_check_unknown_production_keys` accepts it (scope amendment S1).
- **REQ-006**: Regenerate `registry/manifests/db_schema_versions.yaml` (`tools/generate_reference_table.py --manifests`) — `config_key: workflow_db_path` must flip to `in_agent_toml: true` — and the guarded DB Path Reference in `docs/90_deployment/deployment_01_deployment.md` (`--type deployment`). Never hand-edit either.
- **REQ-007**: Update the stale claims: `docs/41_db/db_01_...:34`, the two deploy gates' pinning logic and comments (S2), and `tests/conftest.py:129-131`'s docstring (S3).
- **REQ-008**: Re-measure and report the orphan chunk count from `/opt/llm/db/mdq.sqlite` at implementation time; do not clean any orphan (the issue's constraint).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_service.py` | `write_mode=False` → `write_mode=True` in `_get_db_connection()` | FK off on every service read/write connection | REQ-002 / AC-1 | `mdq_service.py:132-133`; `helper.py:53-54` | `tests/mcp_servers/mdq/test_mdq_foreign_keys.py` (new) | Verified |
| `scripts/mcp_servers/mdq/db_schema.py` | `write_mode=False` → `write_mode=True` in `create_production_tables()` | FK off on the DDL/fingerprint write path | REQ-002 / AC-1 | `db_schema.py:121-123`; `helper.py:53-54` | `tests/mcp_servers/mdq/test_mdq_foreign_keys.py` (new); existing `test_db_schema.py` error-handling patches unaffected | Verified |
| `config/agent.toml` | Add `workflow_db_path = "/opt/llm/db/workflow.sqlite"` (Infrastructure section) | Path must be operator-configurable with no duplicate literal default | REQ-003, REQ-004 / AC-2 | `agent.toml:7-8` (no such key); `config.py:29,97` (two defaults) | `tests/db/test_db_config.py` (new) | Verified |
| `scripts/db/config.py` | Remove the `build_db_config()` fallback literal; omit the argument when the key is absent | Collapse to the single `DbConfig` field default | REQ-004 / AC-2 | `config.py:29` and `config.py:97` (duplicate literal) | `tests/db/test_db_config.py` (new) | Verified |
| `scripts/agent/production_config_validator.py` | Add `"workflow_db_path"` to the subsystem-keys allowlist block | Unknown-key gate would reject the new agent.toml key and abort startup (scope amendment S1) | REQ-005 / AC-3 | `production_config_validator.py:186-206`, `:298` (`_check_unknown_production_keys` call), `:368` | `tests/agent/test_production_config_validator.py` (new acceptance test) | Verified |
| `tests/mcp_servers/mdq/test_mdq_foreign_keys.py` | New: cascade-delete test (must fail first), `PRAGMA foreign_keys` on-connection assertion, orphan-chunk INSERT rejection test | No FK test exists for MDQ today | REQ-001, REQ-002 / AC-1 | No `foreign_keys` assertion in `tests/mcp_servers/mdq/` (grep at plan time) | this file | Verified |
| `tests/db/test_db_config.py` | New: `build_db_config()` reads `workflow_db_path` from the repo `agent.toml`; no fallback literal remains | No tests/db regression covers this key | REQ-003, REQ-004 / AC-2 | `config.py:97` | this file | Verified |
| `tests/agent/test_production_config_validator.py` | Acceptance test: `workflow_db_path` in a config mapping produces no unknown-key error | Allowlist registration needs regression coverage | REQ-005 / AC-3 | existing unknown-key tests at `test_production_config_validator.py:24-45` | new test method | Verified |
| `tests/deploy/test_init_db_schema_gate.py` | Drop the key-pinning insertion in `_write_config()`; update the docstring | Repo key + inserted line = duplicate top-level TOML key → parse error (scope amendment S2) | REQ-007 / AC-3 | `:172-191` (`lines.insert(...)` with absent-key docstring at `:175`) | this file (its gate assertions stay) | Verified |
| `tests/deploy/test_init_db_eventbus_schema.py` | Drop the prepend of the pinned key; update the comment | Same duplicate-key breakage (scope amendment S2) | REQ-007 / AC-3 | `:107-115` | this file | Verified |
| `tests/conftest.py` | Docstring-only fix in `_isolate_db_config()` (comment) | Claim "agent.toml does not set workflow_db_path (the production config validator rejects the key)" becomes false (scope amendment S3) | REQ-007 / AC-3 | `conftest.py:129-131` | N/A: comment only | Verified |
| `registry/manifests/db_schema_versions.yaml` | Regenerate only (`tools/generate_reference_table.py --manifests`) | Generated manifest must show `in_agent_toml: true` | REQ-006 / AC-2 | `db_schema_versions.yaml:10-13`; `generate_reference_table.py:227` | `tools/generate_reference_table.py --check` | Verified |
| `docs/90_deployment/deployment_01_deployment.md` | Regenerate the guarded DB Path Reference only (`--type deployment`) | Generated table shows "No" for workflow today | REQ-006 / AC-4 | `deployment_01_deployment.md:349-359` (guarded block) | `tools/check_docs_consistency.py --domain deployment` | Verified |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Update the line-34 claim about the workflow path key | Claim "`workflow_db_path` is not an `agent.toml` key" becomes false | REQ-007 / AC-4 | `db_01_...:34` | `tools/check_docs_consistency.py --domain db` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/helper.py` | Single pragma owner; `write_mode` semantics (`:35-54`) decide the FK fix shape | REQ-002 |
| `scripts/mcp_servers/mdq/index_delete.py` | Delete-order evidence (`:28-31`); resolves the issue's open question | REQ-001, Problem P2 |
| `scripts/mcp_servers/mdq/index_write.py` | `DELETE chunks` before `INSERT OR REPLACE documents` ordering (`:73-75`) — the only interaction point between FK-on and the REPLACE statement; safe as ordered | REQ-002, Risks |
| `scripts/mcp_servers/mdq/indexer.py` | Issue target with no required change: its connections come from `_get_db_connection()` (`:103, 410`) and deletes from `delete_file_from_index` (`:251`) | Problem P2 (resolved question) |
| `scripts/mcp_servers/mdq/health_check.py` | Read-only probe kept at `write_mode=False` (`:155-166`); deviation recorded in UNK-02 | REQ-002 |
| `scripts/db/create_schema.py` + `scripts/agent/services/workflow_schema.py` | Workflow schema creation/health paths resolve the path through `SQLiteHelper` → `DbConfig` (`helper.py:136`); unaffected once agent.toml sets the key | REQ-003, REQ-004 |
| `tools/check_db_separation.py` | Check 3 reads the `DbConfig` field default (`:189`); stays green because the agent.toml value equals the default | REQ-004, Validation plan |
| `scripts/shared/mcp_dedup.py` | Comment at `:32-33` references "the workflow_db_path default in scripts/db/config.py" — remains accurate (the field default stays); no edit | REQ-004 |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Required-Keys semantics (`:81, 85`) proving no ADR change/approval record is needed | Problem P5 |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Names `DbConfig.workflow_db_path` as a target API (`:150`); no invariant touched. Decision #6 ("Physical foreign keys ... across DBs") scopes to cross-DB use; per-DB physical FKs are the established pattern in `scripts/db/schema_sql.py` | Problem P5, REQ-002 |

## Acceptance Criteria
- **AC-1**: The new cascade-delete test passes (and is demonstrated red before REQ-002 lands); a chunk `INSERT` with a nonexistent `doc_id` is rejected with `sqlite3.IntegrityError` on a production MDQ connection.
- **AC-2**: The manifest shows `in_agent_toml: true` for `workflow_db_path`; `tools/generate_reference_table.py --check` reports no drift; `build_db_config()` returns the agent.toml value and `config.py` contains exactly one `"/opt/llm/db/workflow.sqlite"` literal.
- **AC-3**: Full test suite green, including the two deploy gates and the validator acceptance test; `tools/check_db_separation.py` reports no violations.
- **AC-4**: `tools/check_docs_consistency.py --domain db --domain deployment` (routing docs checkers) passes; the orphan chunk count from `/opt/llm/db/mdq.sqlite` is reported in the implementation record (measured at plan time: 0).

## Tests
- New `tests/mcp_servers/mdq/test_mdq_foreign_keys.py`:
  - `test_cascade_delete_removes_chunks` — build `MdqService` on a tmp DB (fixture pattern of `tests/mcp_servers/mdq/test_index_delete.py`), insert document + chunks through the production write path, then `DELETE FROM documents` only, and assert `chunks` is empty. Must fail before REQ-002 (red-first evidence recorded in Execution Status).
  - `test_connection_pragma_foreign_keys_on` — `PRAGMA foreign_keys` returns 1 on a connection from `_get_db_connection()` and from `create_production_tables()`.
  - `test_orphan_chunk_insert_rejected` — inserting a chunk with an unknown `doc_id` raises `sqlite3.IntegrityError`.
- New `tests/db/test_db_config.py`:
  - `test_build_db_config_reads_workflow_path_from_agent_toml` against the repo `config/agent.toml`.
  - `test_single_default_literal` — `"/opt/llm/db/workflow.sqlite"` appears exactly once in `scripts/db/config.py` (grep-style source assertion mirroring the style already used in `tests/tools/test_check_docs_consistency_checks.py:53`).
- `tests/agent/test_production_config_validator.py`: new method asserting `workflow_db_path` in a config mapping produces no unknown-key error (pattern of `:24-45`).
- Deploy gates: keep existing gate assertions; only the pinning logic and its comments change.
- Targeted run: `uv run pytest tests/mcp_servers/mdq/test_mdq_foreign_keys.py tests/db/test_db_config.py tests/agent/test_production_config_validator.py tests/deploy/ -m "not integration and not production_paths_allowed and not repo_scan" -q`, then the full suite.

## Documentation Impact
- `docs/41_db/db_01_...` — manual sentence fix (path-key claim).
- `docs/90_deployment/deployment_01_deployment.md` — guarded table regeneration only.
- Run `uv run python tools/check_docs_consistency.py --domain db` and `--domain deployment` after the edits (routing.md Tools: docs touched a specific domain).

## Assumptions
- The agent.toml value stays byte-identical to the current code default, so no physical file moves and `tools/check_db_separation.py` Check 3 (`:189`, reads the field default) keeps passing.
- `MdqService` fixtures in `tests/mcp_servers/mdq/` can build a service against a tmp `db_path` without network dependencies (as `test_index_delete.py` already does).
- `build_db_config()` omitting the argument when the key is absent is acceptable per "keep a single default, or none, in code" — the single default is the dataclass field.
- Foreign-key enforcement applies to new DML only; existing rows are not retroactively validated, and measured production orphans are 0.

## Unknowns
- **UNK-01**: Orphan counts measured on this host (dev host with `/opt/llm/db/mdq.sqlite`): orphan chunks 0 / orphan `index_state` mtime rows 0. The production host's counts are unknown until re-measured there (REQ-008).
- **UNK-02**: Deviation from the issue's "Every MDQ connection enforces foreign keys" wording: `health_check.py` stays `write_mode=False` because FK is defined as write-path policy (`helper.py:42-46`) and the probe performs only reads (`health_check.py:155-166`). Needs maintainer acknowledgment if the literal reading is required.
- **UNK-03 (scope amendment S1)**: `scripts/agent/production_config_validator.py` is not in the issue's Target Files but must change (P4).
- **UNK-04 (scope amendment S2)**: `tests/deploy/test_init_db_schema_gate.py` and `tests/deploy/test_init_db_eventbus_schema.py` are not in the issue's Target Files but break without change (P6).
- **UNK-05 (scope amendment S3)**: `tests/conftest.py:129-131` docstring becomes a stale claim (comment-only edit).
- **UNK-06**: `tools/check_db_separation.py` resolves the workflow path from the dataclass default, not from agent.toml. If a future operator sets a different value in agent.toml, the tool would compare against the wrong file. Out of scope here (value identical); recorded for a possible follow-up issue.

## Affected areas
- MDQ write/read connections: one factory (`_get_db_connection`) covers indexer reads/writes (`indexer.py:103, 410`), `index_delete`, `index_write`, get/search paths; DDL path is `create_production_tables`. Blast radius of the pragma change: 2 production files.
- `workflow_db_path` consumers (measured at plan time with `rg` + `scan_change_consumers --seed workflow_db_path`): 12 files reference `DbConfig`/`build_db_config` under `scripts/` (helper.py:136, artifact_retention.py:341, rotation.py:93, recovery_drill.py:159, execution_snapshot.py:53, …); 34 test-file references, most constructing `DbConfig`/`DbConfig` kwargs directly with tmp paths — unaffected. No consumer change required beyond the deploy gates.
- Agent startup: validator allowlist (S1).
- Generated artifacts: `db_schema_versions.yaml`, deployment guarded table.

## Design
- **FK fix shape**: do not hand-write `PRAGMA foreign_keys` in MDQ; the shared `apply_connection_pragmas` stays the single pragma owner. Switching `write_mode` at the two MDQ call sites changes exactly one executed statement per connection (`helper.py:53-54` — WAL/synchronous/busy_timeout are identical either way), so behavior diff is minimal.
- **REPLACE-under-FK safety**: `INSERT OR REPLACE INTO documents` (`index_write.py:75`) with FK on cascades to remaining chunks; the transaction already deletes that document's chunks first (`index_write.py:73`), so no unintended row loss. Verified by ordering, locked by `test_cascade_delete_removes_chunks` plus the existing `test_index_delete.py` behavior lock.
- **Single-default shape**: `build_db_config()` builds kwargs and includes `workflow_db_path` only when the key is present in agent.toml; the `DbConfig` field default (`config.py:29`) is the only literal in code. Tests that construct `DbConfig` directly keep relying on the same field default (`conftest.py` isolation rewrite stays).
- **Deploy gate fix shape**: delete the key-pinning insertion/prepend entirely — the tests' existing whole-file `replace("/opt/llm/db/", db_dir)` rewrite (`test_init_db_schema_gate.py:181`, `test_init_db_eventbus_schema.py:102-106`) already re-points the new repo key into the sandbox, so no replacement pinning is introduced.
- **Validator registration**: add `"workflow_db_path"` to the existing subsystem-keys `valid_keys.update({...})` block (`production_config_validator.py:186-206`), beside `rag_db_path`/`session_db_path`; no new mechanism.
- **Ordering invariant for the config change**: validator registration (REQ-005), agent.toml key (REQ-003), config.py fallback removal (REQ-004), and the two deploy-gate fixes (REQ-007) land in one commit — splitting them either aborts Agent startup (key without registration) or breaks the deploy gates (key without gate fixes).
- Target rows: the fourteen Implementation Target Files rows.
- Reference rows: `helper.py`, `index_delete.py`, `index_write.py`, `indexer.py`, `health_check.py`, `create_schema.py`, `workflow_schema.py`, `check_db_separation.py`, `mcp_dedup.py`, ADR-002, ADR-008.
- Not affected: `tests/db/test_sqlite_helper.py:244` (error-message test about a missing path value; behavior unchanged); `tests/shared/test_execution_snapshot.py` and `tests/db/test_recovery_drill.py` (write their own synthetic configs); `tools/check_db_separation.py` (code default retained, value identical); `scripts/shared/mcp_dedup.py` comment (`:32-33`, stays accurate); `tests/tools/test_check_docs_consistency_checks.py` (synthetic fixtures).

## Implementation steps
1. **Phase 1: Test-first fixtures (FK-ENFORCE)**
   - [ ] Write `tests/mcp_servers/mdq/test_mdq_foreign_keys.py` (cascade-delete, on-connection `PRAGMA foreign_keys`, orphan-chunk INSERT rejection). (REQ-001 / AC-1)
   - [ ] Write `tests/db/test_db_config.py` (agent.toml read-back; single-literal check). (REQ-003, REQ-004 / AC-2)
   - [ ] Record the red results (cascade test fails; config test fails against today's `config.py`) in Execution Status before Phase 2. (REQ-001)
2. **Phase 2: Enable foreign keys on MDQ write paths (FK-ENFORCE)**
   - [ ] `mdq_service._get_db_connection()`: `write_mode=False` → `write_mode=True`. (REQ-002 / AC-1)
   - [ ] `db_schema.create_production_tables()`: same switch. (REQ-002 / AC-1)
3. **Phase 3: Workflow path configuration (WORKFLOW-CONFIG; one commit, see Design ordering invariant)**
   - [ ] Add `workflow_db_path = "/opt/llm/db/workflow.sqlite"` to `config/agent.toml`. (REQ-003 / AC-2)
   - [ ] `scripts/db/config.py`: drop the `build_db_config()` fallback literal; omit the argument when the key is absent. (REQ-004 / AC-2)
   - [ ] Register `"workflow_db_path"` in `production_config_validator.py` subsystem-keys block; add the acceptance test to `tests/agent/test_production_config_validator.py`. (REQ-005 / AC-3; scope amendment S1)
   - [ ] Drop the key-pinning insertion in `tests/deploy/test_init_db_schema_gate.py` and `tests/deploy/test_init_db_eventbus_schema.py`, updating their comments. (REQ-007 / AC-3; scope amendment S2)
   - [ ] Fix the stale docstring claim in `tests/conftest.py:129-131`. (REQ-007; scope amendment S3)
4. **Phase 4: Regeneration, docs, and validation (WORKFLOW-CONFIG)**
   - [ ] Regenerate `registry/manifests/db_schema_versions.yaml` (`--manifests`) and the deployment guarded table (`--type deployment`); never hand-edit. (REQ-006 / AC-2)
   - [ ] Fix the `docs/41_db/db_01_...` line-34 claim. (REQ-007 / AC-4)
   - [ ] Run docs checkers, `check_db_separation.py`, `generate_reference_table.py --check`, ruff/mypy/bandit, targeted then full suite. (AC-3, AC-4)
   - [ ] Re-measure and record the orphan chunk counts from `/opt/llm/db/mdq.sqlite`; do not clean. (REQ-008 / AC-4)

### Release units
**Unit**: FK-ENFORCE | **Phases**: 1, 2 | **Reason**: Phase 1's cascade test is required to be red before Phase 2 and green only after it; the two phases form one demonstrable test-first unit and nothing in Phase 3 depends on them.

**Unit**: WORKFLOW-CONFIG | **Phases**: 3, 4 | **Reason**: agent.toml key, validator registration, config.py default collapse, deploy-gate fixes, and manifest/doc regeneration are mutually breaking if split (startup aborts on unregistered key; gates fail on duplicate key; manifest/docs go stale without regeneration).

## Validation plan
- Red-first evidence: run the new FK tests before Phase 2 and capture the failing cascade assertion.
- Targeted: `uv run pytest tests/mcp_servers/mdq/ tests/db/ tests/deploy/ tests/agent/test_production_config_validator.py -m "not integration and not production_paths_allowed and not repo_scan" -q`.
- Full suite: `uv run pytest tests/ -n logical ... -m "not integration and not production_paths_allowed and not repo_scan"` (baseline at plan time: 12794 passed, 7 skipped).
- Static: ruff, mypy, bandit per `rules/toolchain.md` (issue's Testing Expectations).
- Repo gates: `uv run python tools/check_db_separation.py`, `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_docs_consistency.py --domain db`, `--domain deployment`.
- Data: `sqlite3 /opt/llm/db/mdq.sqlite "SELECT COUNT(*) FROM chunks WHERE doc_id NOT IN (SELECT doc_id FROM documents);"` — report, never clean.

## Risks
- **FK ON + `INSERT OR REPLACE`**: analyzed as safe by write ordering (`index_write.py:73-75`); mitigated by the cascade test and existing `test_index_delete.py` lock. Residual: any future write path that replaces documents without deleting chunks first would silently cascade — the new orphan-insert rejection test documents the enforcement.
- **Deploy-gate rewrite**: removing pinning assumes the whole-file `replace` covers the new key line; both tests verified by reading at plan time (`test_init_db_schema_gate.py:181`, `test_init_db_eventbus_schema.py:102-106`); gate run results confirm.
- **Production orphan data**: unknown until re-measured (UNK-01); FK enforcement does not validate existing rows, so deploy is non-destructive either way.
- **check_db_separation divergence** (UNK-06): acceptable while values stay identical; flagged for follow-up.
- **Full-suite blast**: 34 test files reference `workflow_db_path` but only the two deploy gates read the repo `agent.toml`; scope contained.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Test-first fixtures (`tests/mcp_servers/mdq/test_mdq_foreign_keys.py`, `tests/db/test_db_config.py`); red results recorded before Phase 2 | In Progress | — | — |  |
| 2 | Phase 2: `write_mode=True` in `mdq_service.py` / `db_schema.py` (FK-ENFORCE) | In Progress | — | — | Lands with Phase 1 (release unit) |
| 3 | Phase 3: WORKFLOW-CONFIG one-commit unit (`config/agent.toml`, `scripts/db/config.py`, validator + acceptance test, deploy-gate fixes, conftest docstring) | In Progress | — | — |  |
| 4 | Phase 4: regeneration (`db_schema_versions.yaml`, deployment guarded table), `docs/41_db/db_01_...` claim fix, docs checkers, orphan re-measure report (REQ-008) | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker at plan time | N/A: no blocker | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-162732_01_scripts_mcp_servers_mdq_mdq_service.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261118-162732_02_scripts_mcp_servers_mdq_db_schema.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261118-162732_03_config_agent.toml.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-162732_04_scripts_db_config.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-162732_05_scripts_agent_production_config_validator.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-162732_06_tests_mcp_servers_mdq_test_mdq_foreign_keys.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-162732_07_tests_db_test_db_config.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-162732_09_tests_deploy_test_init_db_schema_gate.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-162732_10_tests_deploy_test_init_db_eventbus_schema.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-162732_11_tests_conftest.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-162732_12_registry_manifests_db_schema_versions.yaml.md | 4 | Procedure | Pending | — | — |
| implementations/20261118-162732_13_docs_90_deployment_deployment_01_deployment.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261118-162732_14_docs_41_db_db_01_architecture_and_schema-overview-and-config.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md`
- **Source requirement**: N/A: no standalone requirement document
- **Source plan**: N/A: this document is the plan
- **Source implementation procedure**: N/A: to be generated by `plan-to-implementation-procedure`
- **Generated at**: 20261118-155712
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source (issue section / finding) | Target file rows | Acceptance criterion |
|---|---|---|---|
| REQ-001 | Required Changes bullet 1 ("must fail first") | `tests/mcp_servers/mdq/test_mdq_foreign_keys.py` | AC-1 |
| REQ-002 | Required Changes bullet 2; Problem P1 | `mdq_service.py`, `db_schema.py`, FK test | AC-1 |
| REQ-003 | Required Changes bullet 3; Problem P3 | `config/agent.toml`, `tests/db/test_db_config.py` | AC-2 |
| REQ-004 | Required Changes bullet 3 ("single default"); Problem P3 | `scripts/db/config.py`, `tests/db/test_db_config.py` | AC-2 |
| REQ-005 | Constraint "Change only Target Files" → scope amendment S1; Problem P4 | `production_config_validator.py`, `test_production_config_validator.py` | AC-3 |
| REQ-006 | Required Changes bullet 4; Constraint 7 (no hand-edit); Acceptance Criteria | manifest row, `deployment_01_deployment.md` row | AC-2, AC-4 |
| REQ-007 | Problem P6, P7 (scope amendments S2/S3) | deploy-gate rows, `conftest.py`, `db_01` | AC-3, AC-4 |
| REQ-008 | Constraints bullet 1; AI Implementation Instruction | Validation plan (data step) | AC-4 |