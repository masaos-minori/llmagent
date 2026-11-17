## Goal

Extend `tools/_compat_leftover_phrases.py` with the compat004 guard rules (dataclass field defaults, guarded parameters, canonical `attempts` DDL nullability, historical doc phrases) and the new `HISTORICAL_DOC_PHRASES` table, so `tools/check_compat_shims.py` can enforce the removal-compatibility rules from one shared helper (procedure 02 wires them).

## Scope

- In scope:
  - Add the guard tables to `tools/_compat_leftover_phrases.py` for the guarded dataclass fields (`RetryPolicy.retry_on`, `WorkflowDef.stages`, `WorkflowDef.retry_policy`), the guarded callable parameter (`begin_stage_if_new: lease_duration_sec`), and the canonical `attempts` DDL columns (`owner_id`, `lease_expires_at`).
  - Add a new path-scoped doc-phrase table (`HISTORICAL_DOC_PHRASES (new)`) for the current-tense `legacy age threshold` wording with the `removed` / `historical` / `withdrawn` allowance. `LEFTOVER_PHRASES` (eleven regexes) is not touched.
  - Add rule functions to the helper: `check_dataclass_field_defaults`, `check_optional_guarded_params`, `check_attempts_ddl_nullability`, `check_historical_doc_phrases`.
- Out of scope:
  - Wiring the new rules into `tools/check_compat_shims.py` (covered by `20261117-110514_02_tools_check_compat_shims.py.md`).
  - Adding new CLI flags or changing existing flag behavior.
  - Changing `LEFTOVER_PHRASES` entries that already exist.
- Preconditions: the helper exists at 5829 B with `LEFTOVER_PHRASES`, `check_leftover_phrases`, `python_nodes`, and `_in_scope` (confirmed). The compat002 production changes this work guards against have already landed via commit `3bc1efd58` (`lease_duration_sec: int` required at `scripts/agent/workflow/idempotency_ops.py:41`; `NOT NULL` DDL at `scripts/db/schema_sql.py:192-193`), so the guard rules are green against the live tree from day one.

## Assumptions

- Can assume: `scripts/db/schema_sql.py` is already at `NOT NULL` for `attempts.owner_id` and `attempts.lease_expires_at` (confirmed live at `scripts/db/schema_sql.py:192-193`), so `check_attempts_ddl_nullability` is green today and guards against a future regression.
- Can assume: `lease_duration_sec` is already a required field (confirmed at `scripts/agent/workflow/idempotency_ops.py:41` and `state_store.py:117`), so `check_optional_guarded_params` is green today; it exists to catch a future re-introduction of the default.
- Can assume: the compat001 strict model contract is landed (`models.py` default-free with `__post_init__` rejecting empty `stages`), so `check_dataclass_field_defaults` is green against the current `WorkflowDef` / `RetryPolicy` definitions.
- Do not assume: existing phrase entries in `LEFTOVER_PHRASES` can be renamed or removed; downstream checks reference them by literal value.
- Do not assume: the helper's byte size can grow without limit; the helper is 5829 B with roughly 18 KB of headroom under the 24576 B tools size gate (plan Step 2), so the additions must stay concise.

## Design decisions

- The rules live in the helper, not in the checker: `check_compat_shims.py` is exactly at its 36235 B baseline ceiling, so new rule bodies must go to `tools/_compat_leftover_phrases.py` (the established precedent from the `LEFTOVER_PHRASES` extraction, `d0da368a7`).
- Guard tables are data (module path → guarded names; table.column → constraint), so procedure 02 wires one aggregate `check_contract_guards` call instead of one call per rule.

## Alternatives considered

- Putting the new rules directly in `check_compat_shims.py`: rejected — the file is at its recorded baseline ceiling and the plan's size gate forces the helper as the rule owner.
- One CLI flag per new rule: rejected — the plan requires the guards always-on under the flags CI and pre-commit already pass.

## Implementation

### Target file
- `tools/_compat_leftover_phrases.py`

### Procedure
1. Add `GUARDED_DATACLASS_DEFAULTS` seeded with `scripts/agent/workflow/models.py` fields `WorkflowDef.stages`, `WorkflowDef.retry_policy`, `RetryPolicy.retry_on`.
2. Add `GUARDED_DEFAULTED_PARAMS` seeded with `begin_stage_if_new: lease_duration_sec` for `scripts/agent/workflow/idempotency_ops.py` and `scripts/agent/workflow/state_store.py`.
3. Add the DDL nullability table seeded with `attempts.owner_id` and `attempts.lease_expires_at` against `scripts/db/schema_sql.py`.
4. Create the `HISTORICAL_DOC_PHRASES` table seeded with `legacy age threshold`, scoped to `docs/`, leaving every existing `LEFTOVER_PHRASES` entry byte-identical.
5. Add `check_dataclass_field_defaults` that parses the guarded modules' dataclass fields and emits a finding for any guarded field carrying a default or default factory (REQ-001).
6. Add `check_optional_guarded_params` that parses each guarded callable and emits a finding for any guarded parameter that is optional or defaulted (REQ-002).
7. Add `check_attempts_ddl_nullability` that reads the canonical `attempts` DDL and emits a finding for each guarded column whose definition lacks `NOT NULL` (REQ-003).
8. Add `check_historical_doc_phrases` that reports current-tense `legacy age threshold` wording under `docs/`, exempting text marked with `removed`, `historical`, or `withdrawn` via a marker allowance mirroring the checker's `_is_historical_context` shape (`tools/check_compat_shims.py:479`; the helper must not import the checker — plan `UNK-03`) (REQ-004).
9. Expose one aggregate entry point `check_contract_guards(content, filepath)` that routes a scanned file to the applicable rules and returns the combined findings, so procedure 02 wires a single call in `check_all`.

### Method
- Direct extension of the existing module: reuse the established `_Finding`-style result shape, the shared `python_nodes` AST parse, and the `_in_scope` allowlist pattern; new rule functions follow the existing `check_leftover_phrases` return-a-list-of-findings pattern.

### Details
- `LEFTOVER_PHRASES` currently holds 11 entries (confirmed against the live module) and stays at 11: the new doc-phrase rule uses its own `HISTORICAL_DOC_PHRASES` table dispatched through `check_contract_guards`, so `check_leftover_phrases` behavior is unchanged.
- The new doc-phrase rule must report zero findings on the live tree: the `legacy age threshold` claim was removed from `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` by commit `3bc1efd58` (zero current-tense matches under `docs/` at verification time). If a current-tense hit is found during execution, fix the wording (production fix, in scope of the guard's purpose) — never add a permanent production exception (REQ-005 boundary).
- The phrase tables and `python_nodes` walk cover `scripts/` and `agent/` trees; `docs/` phrasing is scanned by the doc-side rule over the same file set `check_all` already iterates.
- The helper keeps its import direction: helper imports nothing from `tools.check_compat_shims` (import-layer contract in `skills/DESIGN.md` Shared Vocabulary).

## Compatibility considerations

- `check_compat_shims.py` imports `LEFTOVER_PHRASES`, `check_leftover_phrases`, `python_nodes`, and `_in_scope` from this helper (current import at `tools/check_compat_shims.py:38`); none of those names or signatures change.
- Adding phrases to `LEFTOVER_PHRASES` is explicitly NOT done here; `check_leftover_phrases` findings are unchanged. The new doc-phrase rule produces findings only through `check_contract_guards`, which is the intended effect.
- The helper is private (`_` prefix) and consumed only by `tools/check_compat_shims.py` and its tests.

## Security considerations

- No new attack surface: the rules only parse repository files with `ast` and plain string matching; Bandit stays clean (no eval/exec/subprocess).

## Rollback considerations

- All additions are additive: revert this file restores the pre-expansion helper. Procedure 02's import of the new names must be reverted in the same commit; nothing else references the new functions.

## Validation plan

- `uv run pytest tests/tools/test_check_compat_shims.py -v` — rule-level tests (owned by procedure 03) pass against the new helper functions.
- `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` — exits 0, zero findings, on the post-compat002 tree.
- Plan-batch gates (run once for the whole compat004 batch at batch end, per `rules/workflow-lifecycle.md`): `uv run pytest`, coverage gate, and `diff-cover`.

## Completion criteria

- The helper exposes the guard tables, the `HISTORICAL_DOC_PHRASES` table, the four rule functions, and the aggregate `check_contract_guards` entry point.
- The live checker run exits 0 with zero findings with the doc-phrase guard active.
- Procedure 03's rule-level tests pass.

## Out of Scope
- Wiring the new rules into `tools/check_compat_shims.py` (procedure 02), the checker tests (procedure 03), and `tools/TOOL_DESCRIPTIONS.md` rows (procedure 04).
- Adding new CLI flags or changing existing flag behavior.
- Changing `LEFTOVER_PHRASES` entries that already exist.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117 | 20261117 | compat002 gate cleared 20261117 (commit `3bc1efd58`, verified); rules are green by construction guard tables + four rule functions + check_contract_guards shipped; smoke and lint green |
| 2 | Add or update tests per Validation plan | N/A | — | — | Tests owned by procedure 03 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261117-120000 | Helper byte growth checked against the 24576 B tools gate helper lint/mypy/bandit/module-size and live compat scan green; pytest gate runs with procedure 03 tests |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261117-120000 | `tools/TOOL_DESCRIPTIONS.md` update owned by procedure 04, same change |

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
- **Requirement ID**: `REQ-001`–`REQ-004` (the helper-owned guard rules and doc-phrase table)
- **Source issue**: `issues/20261116-114953_compat004_compat-regression-guards.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-235333_compat004_compat-regression-guards.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-110514
- **Related target files**: `tools/_compat_leftover_phrases.py`