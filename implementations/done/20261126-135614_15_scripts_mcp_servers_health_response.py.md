## Goal
- Emit `health_schema_version`, `degraded_reasons`, and `capabilities` additively from `make_health_response()` in `scripts/mcp_servers/health_response.py`, the producer side of the shared contract (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the response payload construction in this file, plus the test companion.
- Out of scope: the contract module (seq 01); the GitHub capability values (seq 16).

## Assumptions
- Verified in Step 3a: `make_health_response()` (`health_response.py:31-65`) emits `status`, `ready`, `liveness`, `restart_recommended`, `operator_action_required`, `dependencies`, `details`, `security`; no capability or reason field exists.
- The new keys are additive only — no existing key is removed (REQ-004); servers other than GitHub keep the legacy body path through the contract's legacy branch (D-6).

## Design decisions
- The producer builds the new fields through the contract module (seq 01) so the emitted shape and the parsed shape cannot drift.

### Corrections made in Step 3b
- Corrected in Step 3b: the anti-drift guarantee is implemented as a round-trip. The new fields are built as plain JSON values and passed through `parse_health_body()`, so the emitted shape is the
  shape the Agent reads and an out-of-vocabulary state or reason code raises in the producer, not at comparison time.
- Corrected in Step 3b: "empty/absent block" is absent, not empty. When `capabilities` is omitted no new key is written at all, so the body stays a legacy body (D-6). `degraded_reasons` alone is not
  emitted: it is read only alongside the capability block.
- Corrected in Step 3b: the emitted capability block is the object form `{state, reason_code}`, which is the shape the parser accepts for a producer that carries a reason code. The parser also accepts
  a bare state string, so the round-trip stays valid for a legacy-style caller.

## Alternatives considered
- N/A: additive payload change, no signature change beyond optional parameters.

## Implementation
### Target file
`scripts/mcp_servers/health_response.py`

### Procedure
1. Add optional parameters for the capability map and degraded reason codes to `make_health_response()` (default empty, so existing callers are unchanged).
2. Emit `health_schema_version` (1), `degraded_reasons`, and `capabilities` in the payload while keeping every existing key.

### Method
- Use the contract's vocabulary constants for the states and codes; do not hardcode strings here.

### Details
- A server that passes no capabilities emits an empty/absent block, which the Agent reads as a legacy body (D-6).

### Companion test files
- `tests/mcp_servers/test_health_response.py`
  - Procedure: assert the new fields are emitted, every previous key stays, and a no-capability call keeps the legacy shape (T-04).
  - Validation: `uv run pytest tests/mcp_servers/test_health_response.py` (19 passed; 5 cases added in `TestCapabilityBlock`: the three new keys with every previous key kept, the emitted block
    round-trips through the contract parser, no capabilities keeps the legacy shape, an out-of-vocabulary reason code raises, an unknown capability state raises).

## Compatibility considerations
- Additive keys only; existing consumers of the health body are unaffected (Plan Risk mitigation: one deploy of both sides).

## Security considerations
- N/A: no secrets in the health body.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_health_response.py tests/mcp_servers/test_tool_schema.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; then the sequence in `rules/toolchain.md`.
- Ran: 27 tests passed (19 + 8); ruff format/check clean; mypy clean; lint-imports 6 contracts kept; bandit clean; `wc -c` 5350 B; check_docstrings, check_mock_patch_targets, check_module_size clean; reference table no drift; 75 cited ADR tests pass. Full suite pending at end of batch.
- Blast radius measured before the change: 13 server call sites call `make_health_response()`; all keep working because the new parameters are optional and default to no block. The whole `tests/mcp_servers/`
  run passed 3679 with 4 failures in `tests/mcp_servers/git/` that are environment-caused (no git committer identity configured in this workspace) and unrelated to this cycle.

## Completion criteria
- The three new keys appear when supplied, all old keys remain, and the producer test passes.

## Out of Scope
- The contract module and the GitHub capability reporting.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the additive payload fields | Completed | 20261126-191719 | 20261126-191719 | Changed file: scripts/mcp_servers/health_response.py. Optional capabilities and degraded_reasons parameters added; the new fields are built as plain JSON values and validated through parse_health_body() so the emitted shape is the parsed shape. When capabilities is omitted no new key is written, so the body stays a legacy body (D-6). File size 5350 B. Blast radius: 13 server call sites, all unchanged. |
| 2 | Update the companion tests | Completed | 20261126-191719 | 20261126-191719 | 5 cases added in TestCapabilityBlock in tests/mcp_servers/test_health_response.py (additive keys with every previous key kept, block round-trips through the contract parser, no capabilities keeps the legacy shape, out-of-vocabulary reason code raises, unknown capability state raises). 19 tests passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-191719 | 20261126-191719 | ruff format/check pass; mypy clean; lint-imports 6 contracts kept; bandit pass; check_docstrings, check_mock_patch_targets, check_module_size pass; reference table no drift; 75 cited ADR tests pass. tests/mcp_servers/ run: 3679 passed, 4 environment-caused git failures (no git committer identity), unrelated to this cycle. Full suite pending at end of batch. Docs: N/A, the docs rows for this module are seq 33-38. |

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
- **Requirement ID**: `REQ-004` (producer side of the shared health contract)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/mcp_servers/health_response.py`, `tests/mcp_servers/test_health_response.py`