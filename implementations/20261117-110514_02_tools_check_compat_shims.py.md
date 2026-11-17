## Goal
Wire the new contract guards into `check_all` in `tools/check_compat_shims.py` as always-on rules, keeping the file at or below its 36235 B baseline ceiling by extracting the existing `check_mcp_health_reexport_import` AST rule into the helper first (`UNK-04`), and keep the `db.store` / `eventbus.db` prohibitions unchanged (`REQ-001`–`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit — but this document is landing-gated: its wiring MUST NOT be implemented before the compat002 source changes (`implementations/20261117-011632_*`) are implemented, because `REQ-002`/`REQ-003`/`REQ-004` findings against `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/state_store.py`, `scripts/db/schema_sql.py`, and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` would then fail the live `check_compat_shims` run, the CI `backward-compat-check` job, and the `test_no_compatibility_policy_gate.py` repo-scan gate. `REQ-001` is not gated (compat001 already landed).

- `tools/check_compat_shims.py`: extraction of one existing AST rule into the helper, one new `check_all` call line, and a concise docstring update.

## Assumptions
- Procedure 01 (helper rules) is already implemented; this document wires `check_contract_guards (new)` from it.
- Import direction stays checker→helper: `tools/check_compat_shims.py:38` extends to import `check_contract_guards (new)` and `check_mcp_health_reexport_import` from `tools._compat_leftover_phrases`.
- The extraction is verbatim: the `_MCP_HEALTH_REEXPORT_NAMES` frozenset and `check_mcp_health_reexport_import` move to the helper unchanged; the `check_all` call site keeps the same name, so tests importing `checker.check_mcp_health_reexport_import` still resolve the name through the checker module's imports.
- The pre-commit `files` filter and the CI `paths` filter already cover both tool modules and all scanned trees (plan Step 1, `REQ-007`): no change to `.pre-commit-config.yaml` or `.github/workflows/backward-compat-check.yml`.

## Design decisions
- `UNK-04` resolved concretely: extract `check_mcp_health_reexport_import` + `_MCP_HEALTH_REEXPORT_NAMES` (~1 KB) out of `check_compat_shims.py` into the helper — the helper already exposes the shared `python_nodes` parse that this rule uses — then add `issues += check_contract_guards(content, filepath)` to `check_all`. Net effect is a shrink of several hundred bytes, so the 36235 B ceiling is met without a baseline bump.
- Always-on wiring (not behind an opt-in flag): the new rules must block locally and in CI, matching the two existing always-on AST rules (plan `REQ-005` context, Acceptance Criteria).
- Baseline tightening: after the shrink, `check_module_size.py` reports the file as an IMPROVED BASELINE ENTRY; re-record with `--update-baseline` so the recorded ceiling follows the file down (`tools/check_module_size_tools_baseline.txt` "only shrinks" rule).

## Alternatives considered
- Bumping the `check_compat_shims.py` ceiling via `--update-baseline` without shrinking: rejected — the baseline is a shrinking ratchet, and a shrink is achievable via the extraction, so no bump is needed.
- Wiring each new rule as a separate `issues +=` line: rejected — one aggregate call keeps the byte cost minimal and centralizes allowlist/self-skip handling in the helper (`check_contract_guards (new)`).
- Wiring behind a new CLI flag: rejected — the plan requires the guards blocking in CI and pre-commit, which pass no new flag.

## Implementation
### Target file
- `tools/check_compat_shims.py`

### Procedure
1. Gate check before coding: confirm the compat002 end state is in source — `owner_id` / `lease_expires_at` are `NOT NULL` in the `attempts` DDL of `scripts/db/schema_sql.py`, `lease_duration_sec` is required (no default, no `None` union) in `begin_stage_if_new` of `scripts/agent/workflow/idempotency_ops.py` and `scripts/agent/workflow/state_store.py`, and the current-tense `legacy age threshold` wording is gone from `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`. If not, stop: this document is blocked until `implementations/20261117-011632_*` lands.
2. Move `_MCP_HEALTH_REEXPORT_NAMES` and `check_mcp_health_reexport_import` from `tools/check_compat_shims.py` into `tools/_compat_leftover_phrases.py` verbatim (docstring notes it was moved here from the checker); import both back at the `tools/check_compat_shims.py` import block, extending the existing `from tools._compat_leftover_phrases import` line with `check_contract_guards`.
3. In `check_all`, add `issues += check_contract_guards(content, filepath)` next to the existing `check_leftover_phrases` line; update the `check_all` docstring rules paragraph to name the contract guards concisely (dataclass defaults, lease-parameter, attempts-DDL nullability, historical-exempt doc phrase) instead of the current "Two syntax-tree rules" wording, keeping the prose tight for the byte budget.
4. Keep `COMPAT_PATTERNS`' `db.store` / `eventbus.db` entries and `check_removed_name_reintroduction` untouched (`REQ-005`); add no entry to `tools/compat_exceptions.toml` (the fixture allowance for checker test data already exists).
5. Run `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`; tighten the improved `check_compat_shims.py` row with `--update-baseline`.
6. Update `tools/TOOL_DESCRIPTIONS.md` in the same change per procedure 04 (`REQ-008`), then run the validation sequence (`rules/toolchain.md`).

### Method
- Pure relocation + one added call: no logic in this file beyond wiring; the guard logic lives in the helper.
- `check_all` signature unchanged; the new rules run on every `*.py`/`*.md` file the checker already scans, always-on.

### Details
- Expected byte math: removal ≈ 1000 B; additions (import names, one call line, docstring paragraph) ≈ 300 B; net shrink, final file under 36235 B and the tightened baseline records the new lower size.
- `tests/tools/test_compat_checker_precompiled.py` mirrors `COMPAT_PATTERNS`/`ADR_PROHIBITED_PATTERNS` tables only; the extracted rule is not a table mirror, so that test is unaffected.
- Post-wiring live scan must report zero findings: `REQ-001` passes today; `REQ-002`/`REQ-003`/`REQ-004` pass only because compat002's source landed (step 1 gate).

## Compatibility considerations
- No public behavior changes for existing flags: `--check-removed-names` and `--check-doc-symbols` keep their meaning; CI and pre-commit already pass them, so the new rules block wherever the checker runs today — no filter or workflow edits (`REQ-007`).
- `checker.check_mcp_health_reexport_import` and `checker._MCP_HEALTH_REEXPORT_NAMES` remain importable attributes of `tools.check_compat_shims` via the import; verify `tests/tools/test_check_compat_shims.py` references still resolve.
- Landing order with the helper: procedure 01 must be implemented before this wiring; procedure 04's description update must ship in the same change as this one.

## Security considerations
- No new attack surface: the extracted rule is byte-identical logic; the new call delegates to the helper's AST/regex checks over repository files. Bandit stays clean (no eval/exec/subprocess).

## Rollback considerations
- Revert the commit restores the extracted rule in place and removes the `check_contract_guards` call in one step. If only the wiring is reverted (helper kept), the rules go inert without breaking anything — the helper is private.
- Baseline tightening must be reverted together with the code revert (`check_module_size.py` stale/failed-entry checks catch a mismatch).

## Validation plan
- `uv run pytest tests/tools -v` and `uv run pytest -m repo_scan -v` — checker tests (procedure 03) and the policy gate test pass.
- `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` — exits 0, zero findings, on the post-compat002 tree.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — passes with the tightened `check_compat_shims.py` row.
- `uv run ruff format` / `uv run ruff check` / `uv run mypy` / `uv run bandit` on `tools/check_compat_shims.py`.
- `uv run python tools/check_tool_descriptions_sync.py` — passes with procedure 04's rows updated in the same change.

## Completion criteria
- `check_all` runs the contract guards always-on; the file is under 36235 B with the baseline row tightened to the new size; the `db.store` / `eventbus.db` patterns are byte-unchanged; the live checker run exits 0 with zero findings; procedure 03's tests and the repo-scan gate test pass.

## Out of Scope
- The helper rule implementations (procedure 01), the checker tests (procedure 03), `tools/TOOL_DESCRIPTIONS.md` rows (procedure 04), and the compat002 source changes (`implementations/20261117-011632_*`).
- Any change to `.pre-commit-config.yaml` or `.github/workflows/backward-compat-check.yml` (confirmed "no change needed").

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated on compat002 source landing (procedure step 1 gate); procedure 01 must land first |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests owned by procedure 03; live-tree assertions valid only after the gate clears |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Includes `check_module_size.py --scripts-dir tools`; the improved `check_compat_shims.py` baseline row is re-recorded downward with `--update-baseline` (tool data, not a design target) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `tools/TOOL_DESCRIPTIONS.md` update owned by procedure 04, same change |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Wiring fails the live scan until `implementations/20261117-011632_*` (compat002) is implemented | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`–`REQ-005` (always-on wiring of the guards with the existing prohibitions unchanged)
- **Source issue**: `issues/20261116-114953_compat004_compat-regression-guards.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-235333_compat004_compat-regression-guards.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-110514
- **Related target files**: `tools/check_compat_shims.py`
