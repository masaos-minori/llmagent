# Implementation Procedure: `scripts/shared/component_mandatoriness.py`

## Goal

Create the leaf-safe loader for the mandatoriness registry (REQ-003: loader exposing a frozen classification map and typed errors; REQ-007: `shared` stays a leaf module).

## Scope

- New module `scripts/shared/component_mandatoriness.py` (new): typed dataclass, loader, typed errors, single path constant.
- Consumed later by `scripts/agent/production_config_validator.py` (row 4) and `scripts/agent/startup_validation.py` (row 5); this row adds no callers.

## Assumptions

- Registry file content and field vocabulary follow row 1 (`20261030-115752_01_registry_component_mandatoriness.yaml.md`); a mismatch there forces matching edits here.
- Plan U-1: the file's final home may move after adrauth001; this module isolates that behind `DEFAULT_REGISTRY_PATH` (plan mitigation: one path constant).

## Design decisions

- Plain frozen dataclass + `Mapping[str, ComponentClassification]` return wrapped in MappingProxyType; no Agent DTO imports (import-linter contract `agent-mcp-config-models`, REQ-007). Imports: stdlib + `yaml` only.
- Typed error hierarchy: `ComponentMandatorinessError` (new) base; `UnknownComponentError` (new) for a component id absent from the registry; `ClassificationConflictError` (new) for a config-vs-registry disagreement. Names fixed by REQ-003 for the latter two.
- Structural validation happens at load time (unknown keys, missing fields, unknown `classification` values raise `ValueError` wrapped as `ComponentMandatorinessError` (new)), so consumers never see a half-valid map.

## Alternatives considered

- Encoding the map in `config/agent.toml` — rejected (see row 1 Alternatives).
- Pydantic-style validation — rejected: Pydantic is not a project dependency; hand validation of 10 small entries is cheaper and keeps `shared` import-light.

## Implementation

### Target file

`scripts/shared/component_mandatoriness.py` (new)

### Procedure

1. Module docstring naming ADR-004 Group 3 item 13 as the contract and the registry file as the data source.
2. Define `ComponentClassification` (new) frozen dataclass: `component_id: str`, `classification: str`, `failure_category: str`, `safety_role: str`, `safely_disableable_functions: frozenset[str]`, `startup_consequence: str`, `observability: frozenset[str]`, `owner: str`, `authority_adr: str`, `rationale: str` — one field per row-1 entry key.
3. Define `DEFAULT_REGISTRY_PATH` (new) = `Path("registry/component_mandatoriness.yaml")` relative to the repo root, plus a module comment citing plan U-1 as the reason a single constant exists.
4. Implement `load_component_mandatoriness(path: Path | None = None) -> Mapping[str, ComponentClassification]` (new): `yaml.safe_load`, validate the top-level shape (`version`, `entries`), build the map keyed by `component_id` (new), return MappingProxyType.
5. Implement `get_classification(registry: Mapping[str, ComponentClassification], component_id: str) -> ComponentClassification` (new) raising `UnknownComponentError` (new) naming the component and the registry path.
6. Implement `check_required_agreement(registry, component_id: str, config_required: bool) -> None` (new): unknown id → `UnknownComponentError` (new); `classification == "required"` while `config_required is False` → `ClassificationConflictError` (new) carrying component id, approved classification, and config value in the message (the message is what the startup fatal reports — REQ-008 observable reason).

### Method

Hand-rolled validation; every raised error includes the registry path and component id so startup output names the remediation target without extra plumbing (REQ-008: no new observability channels).

### Details

- Reject duplicate `component_id` (new) entries (load-time error) — a duplicated row is a classification conflict at the source.
- Reject an entry whose `classification` is neither `required` nor `non_required` (new) (load-time error): REQ-004's "registry entry with no classification is fatal" is enforced structurally here.
- `safely_disableable_functions` (new) and `observability` accept lists in YAML, normalize to `frozenset[str]`.
- Keep the module under the `check_module_size.py` limits (validation plan lists module-size growth).

## Compatibility considerations

- New module; no existing imports change. `shared` leaf contract: import only `yaml` and stdlib (REQ-007); `PYTHONPATH=scripts uv run lint-imports` must stay clean.

## Security considerations

- Fail-closed: any parse/validation failure raises; a missing registry file raises (the file's existence is validated in row 5's wiring — treat a missing file as the fatal "Undeterminable component mandatoriness", ADR-004 Fail-Fast list).

## Rollback considerations

- Revert the commit; no consumers land before rows 4/5.

## Validation plan

- `uv run pytest tests/shared/test_component_mandatoriness.py` (row 10's tests exercise this loader).
- Gates: `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run mypy scripts`, `uv run ruff check scripts tests tools`, `uv run bandit -r scripts`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`.

## Completion criteria

- The loader round-trips the 10 approved entries into a frozen map; unknown-id and conflict lookups raise the two typed errors with actionable messages; lint-imports reports no new `shared` violation (plan Phase 1 "Done when": loader round-trips the 10 approved entries; typed-error fixtures pass).

## Out of Scope

- Startup wiring and fatal reporting (rows 4/5), drift checking (row 8), registry content edits (row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement dataclass, loader, typed errors per Procedure/Method | Pending | — | — | |
| 2 | Tests arrive from row 10 (`tests/shared/test_component_mandatoriness.py`); this row adds none itself | Pending | — | — | Test-first: row 10 written first |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. lint-imports | Pending | — | — | |
| 4 | N/A: docs live in rows 25-27 | — | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on row 1's registry file existing with the agreed field vocabulary | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

#### Marker edit record
- `(new)` マーカー編集（この doc が導入する新規コンポーネント）は `tools/mark_new_115752.py`（冪等）に記録済み。

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (leaf-safe loader with frozen map and typed errors); REQ-007 (leaf-module constraint)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `scripts/shared/component_mandatoriness.py` (new)
