## Goal
Implement the four new contract-guard rules in the checker's private helper `tools/_compat_leftover_phrases.py` — the dataclass-field-default guard (`REQ-001`), the optional/defaulted `lease_duration_sec` guard (`REQ-002`), the canonical `attempts` DDL nullability guard (`REQ-003`), and the current-tense `legacy age threshold` doc phrase rule with a historical allowance (`REQ-004`) — and expose them through a single aggregate entry `check_contract_guards (new)` so `tools/check_compat_shims.py` wires them with one call (`REQ-001`–`REQ-004`; plan Decision 1).

## Scope
**Release unit**: N/A: not part of a release unit. The compat002 landing gate applies to the `check_all` wiring in procedure 02, not to this helper addition (the rules are inert here until wired).

- Add the guard tables, the four check functions, and the `check_contract_guards` aggregate to `tools/_compat_leftover_phrases.py`.
- Update the module docstring so it describes the expanded responsibility (leftover phrases + contract guards).
- No change to `tools/compat_exceptions.toml`, `.pre-commit-config.yaml`, or the CI workflow (confirmed `no change needed` in plan Step 1 / `REQ-007`).

## Assumptions
- The helper MUST NOT import `tools/check_compat_shims.py` (import direction is checker→helper per `skills/DESIGN.md` Shared Vocabulary); the new historical allowance therefore mirrors the shape of `check_compat_shims.py:479` `_is_historical_context` (target line plus the 10 preceding lines) with its own marker set `removed` / `historical` / `withdrawn` (plan `REQ-004`). The checker's own two-word marker set is not changed.
- The three code guards are keyed on content (class names, parameter names, DDL table name), not on file paths, so synthetic fixtures under temp directories trigger them; only the doc phrase rule is path-scoped (`docs/`), reusing the helper's existing segment-aware `_in_scope` matcher.
- The helper stays standard-library only and under the 24576 B tools gate (5829 B today; the additions are expected to land around 10-11 KB).
- Strict end states this plan guards against: `RetryPolicy.retry_on`, `WorkflowDef.stages`, `WorkflowDef.retry_policy` without defaults (already true — `scripts/agent/workflow/models.py`, compat001 implemented); `lease_duration_sec` required in `begin_stage_if_new` and `NOT NULL owner_id` / `lease_expires_at` in the canonical `attempts` DDL (pending — owned by `implementations/20261117-011632_*`).

## Design decisions
- Aggregate entry `check_contract_guards (new)` dispatches the four rules and performs the allowlist/self-skip checks once, so procedure 02 adds exactly one call line plus the import names to `check_all` (the 36235 B ceiling constraint, `UNK-04`).
- Guard tables (module-level, typed):
  - `GUARDED_DATACLASS_DEFAULTS (new)`: `dict[str, frozenset[str]]` = `{"RetryPolicy": frozenset({"retry_on"}), "WorkflowDef": frozenset({"stages", "retry_policy"})}`.
  - `GUARDED_DEFAULTED_PARAMS (new)`: `frozenset[str]` = `frozenset({"lease_duration_sec"})`.
  - `_ATTEMPTS_DDL_BODY_RE (new)`: `re.compile(r"CREATE TABLE IF NOT EXISTS attempts\s*\((.*?)\)", re.DOTALL)`.
  - `_GUARDED_DDL_NULLABLE_RE (new)`: matches a column declaration for `owner_id` or `lease_expires_at` that lacks `NOT NULL` (and is not a `PRIMARY KEY` declaration).
  - `_HISTORICAL_EXEMPT_DOC_PHRASES (new)`: `dict[str, re.Pattern[str]]` = `{"legacy age threshold": re.compile(r"legacy[ ]age[ ]threshold")}`, scoped to `docs/` via `_in_scope`.
  - `_DOC_PHRASE_MARKERS (new)`: `tuple[str, ...]` = `("removed", "historical", "withdrawn")`.
- AST predicates (walk the shared `python_nodes` parse; no second parse):
  - Dataclass guard: for each `ast.ClassDef` named in `GUARDED_DATACLASS_DEFAULTS` that carries a `dataclass` decorator (`ast.Name` or `ast.Call`), flag a top-level `ast.AnnAssign` for a guarded field when `node.value` is not `None` (plain default), including the `field(default=...)` / `field(default_factory=...)` forms (an `ast.Call` to `field` with a `default` or `default_factory` keyword).
  - Lease-param guard: for each `ast.FunctionDef` / `ast.AsyncFunctionDef`, flag an argument named in `GUARDED_DEFAULTED_PARAMS` when it carries a default (`args.defaults` positional tail or `args.kwonly_defaults`) or a `None`-union annotation (`ast.UnionType` containing `ast.Constant(None)` or `ast.Subscript` of `Optional[...]`). A bare `lease_duration_sec: int` parameter is not flagged (this keeps `scripts/agent/workflow/attempt_ops.py:31` `lease_expires_from` passing).
  - DDL guard: applies only when the file content contains `CREATE TABLE IF NOT EXISTS attempts`; for each guarded column declaration inside that table body without `NOT NULL`, report with the source line number. Content-keyed, so non-`attempts` tables and non-DDL files are untouched.
  - Doc phrase guard: for files under a `docs/` path segment, flag a `legacy age threshold` match unless the line itself or one of the 10 preceding lines contains a marker from `_DOC_PHRASE_MARKERS` (case-insensitive).
- Issue strings use the existing shape: `{filepath}:{lineno}: backward compatibility leftover — {label}: {snippet}`.
- Self-skip: every new function returns `[]` for the helper's own source (`resolved == _SELF_PATH`), mirroring `check_leftover_phrases`, because the helper carries the guard names and the DDL/phrase patterns as literals.

## Alternatives considered
- A second private helper module (e.g. `tools/_compat_contract_guards.py`): rejected — it is not a row of the plan's frozen `Implementation Target Files` table and would be an additional-target discovery requiring a plan amendment; the existing helper has ~18 KB headroom.
- Adding the rules directly to `tools/check_compat_shims.py`: rejected — the file sits exactly at its 36235 B baseline ceiling (plan Decision 1).
- A narrow regex for the default/parameter checks: rejected — plan Decision 2; `ast` distinguishes a real default from incidental text with no exceptions.

## Implementation
### Target file
- `tools/_compat_leftover_phrases.py` (existing file; module docstring updated in this change to describe the guard tables and the four new functions alongside the existing eleven-phrase table — the "eleven `LEFTOVER_PHRASES`" claim stays true because the doc phrase rule lives in its own table).

### Procedure
1. Extend the module docstring and imports (`ast` already imported; no new dependencies).
2. Add the guard tables listed under Design decisions.
3. Add `check_dataclass_field_defaults (new)`, `check_optional_guarded_params (new)`, `check_attempts_ddl_nullability (new)`, and `check_historical_doc_phrases (new)`, each returning issue strings in the existing format and each self-skipping the helper's own source.
4. Add `check_contract_guards (new)`: resolve the path once, return `[]` for allowlisted files and the helper itself, then return the concatenation of the four rule results (the doc phrase rule also enforces its `docs/` path scope internally).
5. Run the validation sequence (`rules/toolchain.md`) on this file.

### Method
- Additive only: no change to `LEFTOVER_PHRASES`, `python_nodes`, `_in_scope`, `_applicable_phrases`, or `check_leftover_phrases`.
- `python_nodes`' one-entry cache is reused unchanged; the AST guards must not parse separately.
- The rules are inert in the live pipeline until procedure 02 wires `check_contract_guards` into `check_all`; landing this file before procedure 02 must not change the checker's current findings (verify: the live `--check-removed-names --check-doc-symbols` run still exits 0 with zero findings after this change).

### Details
- Expected live-tree state when the rules eventually run: `REQ-001` reports nothing today (strict source landed via compat001); `REQ-002` flags `scripts/agent/workflow/idempotency_ops.py` (`begin_stage_if_new` `lease_duration_sec: int | None = None`) and the same parameter on `StateStore.begin_stage_if_new` (`scripts/agent/workflow/state_store.py`); `REQ-003` flags `scripts/db/schema_sql.py` (`owner_id TEXT,` / `lease_expires_at TEXT` in the `attempts` table); `REQ-004` flags `docs/41_db/db_07_api_and_operations-recovery-and-reference.md:92`. Those three findings are exactly the end states the pending compat002 procedures (`implementations/20261117-011632_*`) remove; procedure 02 must not wire before they land.
- Fixture compatibility: because the code guards are content-keyed, tests can exercise them with temp-path files; the doc phrase guard matches the `docs/` segment inside absolute temp paths the same way `_in_scope` already matches `scripts/` prefixes.

## Compatibility considerations
- The helper is private (`check_compat_shims.py:38` and `tests/tools/test_compat_checker_precompiled.py` import it); no existing export is renamed or removed, so no caller changes.
- `tests/tools/test_check_compat_shims.py` is already allowlisted via the `check-compat-shims-test-data` fixture entry, so procedure 03's in-file fixtures need no new manifest entry.
- `tools/compat_exceptions.toml`: no entry added or changed (`REQ-005`, plan Step 1).

## Security considerations
- Standard library only (`ast`, `re`, `pathlib`); no eval/exec, no network, no subprocess. Regexes are fixed literals over repository files; `bandit` must stay clean (no new `assert`/`exec`/`shell` surface).

## Rollback considerations
- Fully additive within one file; revert the commit. Nothing consumes the new functions until procedure 02 wires them, so a revert cannot leave the checker half-updated on its own.

## Validation plan
- `uv run ruff format` / `uv run ruff check` / `uv run mypy` / `uv run bandit` on `tools/_compat_leftover_phrases.py`.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — helper stays under 24576 B and stays unbaselined.
- `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` — still zero findings (rules not yet wired).
- Unit tests are owned by procedure 03 (`tests/tools/test_check_compat_shims.py`); run `uv run pytest tests/tools -v` once those tests exist.

## Completion criteria
- The four guard functions, the guard tables, the `check_contract_guards` aggregate, and the updated module docstring exist in `tools/_compat_leftover_phrases.py`.
- Size/lint/type/security gates pass; the live checker run is unchanged (zero findings) before procedure 02 wiring.
- Procedure 03's positive/negative/allowed-historical tests for all four rules pass against these function names.

## Out of Scope
- Wiring into `check_all` and the net-size-neutral extraction (procedure 02).
- The checker tests themselves (procedure 03).
- `tools/TOOL_DESCRIPTIONS.md` (procedure 04).
- The compat002 source changes themselves (`implementations/20261117-011632_*`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Land before procedure 02; rules inert until wired |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests owned by procedure 03 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Description update owned by procedure 04 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261116-114953_compat004_compat-regression-guards.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-235333_compat004_compat-regression-guards.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-110514
- **Related target files**: `tools/_compat_leftover_phrases.py`
