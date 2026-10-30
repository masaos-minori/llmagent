# Implementation Procedure: `scripts/agent/production_config_validator.py`

## Goal

Add the config-vs-registry mandatoriness cross-check so a `required` value that conflicts with the approved classification, or a configured server missing from the registry, produces validation errors the startup pipeline turns into a fatal (REQ-004: cross-validation, fatal on unknown/conflict).

## Scope

- `scripts/agent/production_config_validator.py`: new method on `ProductionConfigValidator` plus a module-level helper; no existing check changes semantics.
- Consumed by `scripts/agent/startup_validation.py` (row 5). `scripts/agent/config_builders.py` :108 `validate()` call site is untouched (plan row 5 wires the pipeline, not config_builders).

## Assumptions

- The loader API is row 2's: `load_component_mandatoriness` (new), `get_classification` (new), `check_required_agreement` (new) (all (new) until row 2 lands).
- Config input shape: `ctx` MCP server configs expose `required: bool` per server key (`scripts/shared/mcp_config.py:100` `required: bool` default `True`; normalized at :326). The validator receives the mapping of server key → effective `required`.

## Design decisions

- New method `validate_against_registry(self, mcp_required: Mapping[str, bool]) -> list[str]` (new): returns error strings in the same style as the existing checks (`_check_missing_tool_safety_tiers` :62 pattern) — the pipeline caller converts non-empty output into `pipeline.add_fatal(...)`. Keeping the return-as-strings contract avoids a new error channel (REQ-008).
- The method calls `check_required_agreement` (new) per server and catches the two typed loader errors, converting each into a message that names the component, the approved classification, the config value, and the registry path — the fatal output is self-remediating (ADR-004 Group 3 item 13: configuration cannot weaken a mandatory component).
- Unknown server (config key absent from the registry) is an error too: "Undeterminable component mandatoriness" is already on ADR-004's Fail-Fast list (:85 Fail-Fast list, Group 4 item 14).

## Alternatives considered

- Fold the check into the existing `validate()` (`:215`) — rejected: `validate()` takes a raw config mapping for production keys and is called by config_builders during reload; mandatoriness validation belongs to the startup pipeline where it must be fatal, and mixing paths would make reload-time behavior ambiguous. Needs Confirmation: whether config reload should also enforce the registry check (a reload that flips `required = false` while running); default per plan is startup-pipeline-only wiring.

## Implementation

### Target file

`scripts/agent/production_config_validator.py`

### Procedure

1. Import the loader surface from `agent`→`shared` (allowed by the import contract: `scripts/shared/tool_registry.py:10-13` documents agent modules may import shared): `component_mandatoriness` (new) functions (row 2).
2. Add `validate_against_registry` (new) to `ProductionConfigValidator` (:208 class): for each `(server_key, required)` in the input, call `check_required_agreement` (new); on `ClassificationConflictError` (new) or `UnknownComponentError` (new), append the message; return all messages.
3. Add a reverse check: registry entries with no corresponding configured server are reported as warnings, not errors — a classified-but-not-configured server does not make mandatoriness undeterminable (it cannot be used). Keep severity out of `errors` so AC-3's fatal set is exactly {conflict, unknown-configured-server}.

### Method

Reuse the module's existing `_record`-free error-string accumulation style (the `errors: list[str]` pattern in `validate` :221-236); no new result type.

### Details

- Message format (fixed here so row 23's tests can pin it): `component mandatoriness: '<server_key>' config required=<value> conflicts with registry classification '<approved>' (registry: registry/component_mandatoriness.yaml)` and `component mandatoriness: '<server_key>' is configured but absent from the mandatoriness registry (registry: registry/component_mandatoriness.yaml)`.
- Do not load the registry inside this module — the caller (row 5) loads once and passes the mapping; keeps the validator pure and testable with synthetic maps (row 23 fixtures).

## Compatibility considerations

- Production behavior unchanged for the current all-required config: all 10 configured servers match the registry (plan AC-6; `config/agent.toml` values stay `required = true`, plan Excluded row).
- Only previously unvalidated configurations can now fail (issue Constraint).

## Security considerations

- Fail-closed on drift: any conflict/unknown becomes an error string the startup pipeline marks fatal (row 5); nothing degrades to warning for the two fatal classes.

## Rollback considerations

- New method only; revert the commit. No caller exists until row 5 lands.

## Validation plan

- `uv run pytest tests/agent/test_production_config_validator.py` (row 23 adds the downgrade-rejected and unknown-fatal regressions).
- Gates: `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run mypy scripts`, `uv run ruff check scripts tests tools`, `uv run bandit -r scripts`, `PYTHONPATH=scripts uv run lint-imports` (agent→shared import stays inside the contract).

## Completion criteria

- Given the real registry and the real config, `validate_against_registry` (new) returns an empty list; given `required=false` for a registry-`required` server it returns exactly one conflict error; given a configured server absent from the registry it returns exactly one unknown-classification error (plan AC-3 precondition).

## Out of Scope

- Pipeline wiring and `add_fatal` calls (row 5), fatal fixtures (row 23), registry/loader content (rows 1-2), `config/agent.toml` values (plan Excluded).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `validate_against_registry` (new) per Procedure/Details | Pending | — | — | Needs row 2 landed first |
| 2 | Tests arrive from row 23 (fail-before/pass-after fixtures) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | N/A: docs live in rows 25-27 | — | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Loader (`scripts/shared/component_mandatoriness.py`) must exist (row 2, Phase 1 precedes Phase 3) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

#### Marker edit record
- `(new)` マーカー編集（この doc が導入する新規コンポーネント）は `tools/mark_new_115752.py`（冪等）に記録済み。

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 (startup cross-validation: unknown or conflicting classifications are fatal)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `scripts/agent/production_config_validator.py`
