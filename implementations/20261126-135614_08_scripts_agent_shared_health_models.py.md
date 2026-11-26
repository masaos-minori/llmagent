## Goal
- Make `interpret_health_body()` in `health_models.py` parse through the shared contract and read `dependencies` as the dict servers emit, so a dict body keeps each dependency's status text (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `interpret_health_body()` and the dependency summarization path in this file, plus the test companion.
- Out of scope: the contract module (seq 01); producer emission (seq 15).

## Assumptions
- Verified in Step 3a: `health_models.py:180` casts `dependencies` to a list, so a dict body iterates keys and loses the status text; servers emit a dict (`github_server.py:185-186`); `summarize_dependencies()` (`:255`) takes a list of dict-or-str entries.
- The contract parser (seq 01) is the single strict-parse path; this file consumes its result and keeps its existing summary shape.

## Design decisions
- `HealthInterpretation` keeps its existing fields; the dict path is normalized into the same summary list (one summary per key-value pair) so downstream consumers are unchanged.

## Alternatives considered
- Change `summarize_dependencies` to accept a dict directly (rejected: keeps the public shape and the existing tests, smaller diff).

## Implementation
### Target file
`scripts/agent/shared/health_models.py`

### Procedure
1. Parse the body through `shared.mcp_health_contract.parse_health_body()` (seq 01); a parse failure keeps the existing `parse_failure_reason` fallback behavior.
2. Read `dependencies` as a dict (or list, for producers that still send a list) and summarize each entry's status text.

### Method
- Dict normalization: each `key -> value` entry becomes the existing summary form `key: value`; list entries keep the current behavior.

### Details
- The `details` and `security` handling stays unchanged; only the `dependencies` cast is corrected.

### Companion test files
- `tests/agent/shared/test_mcp_health_interpretation.py`
  - Procedure: add a dict-`dependencies` case asserting each dependency's status text survives; keep the existing list-body cases (T-04).
  - Validation: `uv run pytest tests/agent/shared/test_mcp_health_interpretation.py`.

## Compatibility considerations
- Additive behavior for dict bodies; list bodies parse as before.

## Security considerations
- N/A: no secrets in the interpretation output.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/shared/test_mcp_health_interpretation.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- A dict `dependencies` body keeps each status text in the summary; the strict parser rejects wrong-typed fields; tests pass.

## Out of Scope
- The contract module and producer changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the contract-based parse and dict dependency read | Pending | — | — | |
| 2 | Update the companion tests | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (strict contract parse, dict dependencies)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/agent/shared/health_models.py`, `tests/agent/shared/test_mcp_health_interpretation.py`
