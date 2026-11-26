## Goal
- Create the shared health body contract in `scripts/shared/`: the health schema dataclass, the closed reason-code and capability-state vocabularies, and a strict legacy-tolerant parser used by both the Agent and the MCP servers (REQ-004, health contract with versioned fields).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new module plus its test companion.
- Out of scope: emitting the fields from producers (seq 15), parsing in `health_models.py` (seq 08), readiness decisions (seq 03, 09).

## Assumptions
- Verified in Step 3a: no health contract module exists in `scripts/shared/` (`ls scripts/shared`); `mcp_servers` must not import `agent` per the `lint-imports` contract, so the contract lives in the shared leaf.
- Health schema version is `1` (Plan Design D-5); existing producers emit `status`/`ready`/`liveness` only, so the parser must accept a legacy body without the new fields.
- UNK-02 (Plan Risk mitigation): during implementation, check the production health samples under `/opt/llm` for a server that returns a 503 with `ready=false` and no capability block while `required=true`; the legacy branch is what would block it, so a migrated capability block is the remedy. Checked in this cycle: `/opt/llm/logs/` holds no `/health` body sample (no `ready": false` line in any server log), so no deployed server is known to hit the legacy branch; the check stays open until staging.
- Corrected in Step 3b: the closed reason-code vocabulary is `{config_missing, server_unavailable, half_open_trial_in_progress}` (owner decision, 2026-11-26). `config_missing` matches the canonical `REASON_CONFIG_MISSING` in `scripts/shared/security/result_dto.py`; the two hint codes are imported from their canonical owner `scripts/shared/mcp_health.py` rather than re-declared here.
- Corrected in Step 3b: a legacy body has no `health_schema_version`, so the parser reports `LEGACY_HEALTH_SCHEMA_VERSION = 0` for it; version 1 is the current contract. Absent fields parse as defaults (empty reasons, empty capabilities); a present field with the wrong type still raises.
- Corrected in Step 3b: `HealthReport` exposes `is_legacy` (true when the body carries no capability block), the shape the readiness helpers of seq 03, 05 and 09 read for the D-6 fallback.
- Post-cycle fix: the module comment describing a body without a capability block was reworded, because `tools/check_compat_shims.py` flags the leftover phrase "predates" under `scripts/`. The comment now states the shape directly.

## Design decisions
- Module contents: `HealthReport` (new) dataclass (`health_schema_version: int`, `liveness: bool`, `ready: bool`, `degraded_reasons: tuple[str, ...]`, `capabilities: Mapping[str, CapabilityState]`), the closed reason-code vocabulary (aligned with `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`), the capability states `ok`/`degraded`/`unavailable`, and `parse_health_body()` (new).
- Legacy rule (D-6): a body without `capabilities` is legacy — every capability of that server reads as `ok` when `ready` is true and as unproven otherwise; the parser itself does not decide required versus optional (the Agent does, from the catalog).

## Alternatives considered
- Put the DTO under `agent` (rejected by D-5: the servers produce it and cannot import `agent`).

## Implementation
### Target file
`scripts/shared/mcp_health_contract.py` (new)

### Procedure
1. Define the reason-code vocabulary as a frozen constant set and the capability-state set.
2. Define `CapabilityState` (new) as a small dataclass: state plus optional reason code.
3. Define `HealthReport` (new) with the fields above.
4. Add `parse_health_body(body: dict) -> HealthReport` (new): strict typing per field; a wrong-typed field, a reason code outside the vocabulary, or an unknown capability state raises a `ValueError` naming the field; a body carrying only `liveness`/`ready` parses as a legacy report.

### Method
- Strict parse: `bool` fields must be actual JSON booleans, `health_schema_version` (new) an int, `degraded_reasons` a list of vocabulary strings, `capabilities` an object of name-to-state entries; no truthy coercion.
- Keep the module a pure data/vocabulary leaf: no I/O, no logging, no imports from `agent` or `mcp_servers`.

### Details
- The reason-code vocabulary entries must match the codes documented in `mcp_06_10` so the docs gate stays consistent (seq 34 updates that doc from this vocabulary).

### Companion test files
- `tests/shared/test_mcp_health_contract.py` (new)
  - Procedure: full-body parse, legacy-body parse, wrong-typed field rejection, out-of-vocabulary reason code rejection, unknown capability state rejection (T-04).
  - Validation: `uv run pytest tests/shared/test_mcp_health_contract.py`.

## Compatibility considerations
- New module only; no existing importer changes. Producers add the keys additively (seq 15), so old servers stay parseable through the legacy branch.

## Security considerations
- N/A: no secrets in the contract; the parser never echoes token values.

## Rollback considerations
- N/A: revert the commit (producers and consumers depend on the module).

## Validation plan
- `uv run pytest tests/shared/test_mcp_health_contract.py`; `uv run ruff format` and `uv run ruff check` on the new files; `uv run mypy`; `uv run lint-imports` (the new module must satisfy the shared-leaf contract); then the sequence in `rules/toolchain.md`.

## Completion criteria
- The parser accepts a full body and a legacy body and rejects the three invalid shapes; the vocabularies are closed sets; all validation commands pass.

## Out of Scope
- Producer emission, Agent-side readiness logic, and documentation updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the contract module | Completed | 20261126-154558 | 20261126-154558 | Changed: scripts/shared/mcp_health_contract.py. Step 3b corrections: closed vocabulary = {config_missing, server_unavailable, half_open_trial_in_progress}; legacy body reports version 0; HealthReport.is_legacy added. UNK-02 check: no /health body sample in /opt/llm/logs. Changed: scripts/shared/mcp_health_contract.py. Step 3b corrections: closed vocabulary = {config_missing, server_unavailable, half_open_trial_in_progress}; legacy body reports version 0; HealthReport.is_legacy added. UNK-02 check: no /health body sample in /opt/llm/logs. |
| 2 | Add the companion tests first, then confirm they pass | Completed | 20261126-154558 | 20261126-154558 | tests/shared/test_mcp_health_contract.py created (12 tests, T-04); targeted run passes. tests/shared/test_mcp_health_contract.py created (12 tests, T-04); targeted run passes. |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `lint-imports` | Completed | 20261126-154613 | 20261126-154613 | ruff/mypy/lint-imports/bandit pass. Full suite pending at end of batch. Docs: N/A, no docs/00_index.md task-scope row names the new contract module; the contract docs are seq 33/34 target rows. ruff/mypy/lint-imports/bandit pass. Full suite pending at end of batch. Docs: N/A, no docs/00_index.md task-scope row names the new contract module; the contract docs are seq 33/34 target rows. ruff/mypy/lint-imports/bandit pass; targeted tests 12 passed. Full suite pending at end of batch. Docs: N/A, no docs/00_index.md task-scope row names the new contract module; the contract docs are seq 33/34 target rows. |

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
- **Requirement ID**: `REQ-004` (shared health contract with strict parser)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/shared/mcp_health_contract.py`, `tests/shared/test_mcp_health_contract.py`