## Goal

Make the MDQ audit target carry hashed query and regex values and root-relative path identifiers instead of raw values, and carry persisted path counts and root identities rather than raw paths (REQ-006 audit redaction).

## Scope
**Release unit**: boundary-characterization-tests (Plan step 4 cites this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- Companion test row (SKILL.md conditions 1-4 hold): `tests/mcp_servers/mdq/test_audit_target.py`.
- `tests/mcp_servers/test_mdq_audit.py` is named by this row but keeps its own document (seq 15) because its redaction test design is its own decision.
- The path-identifier helper is added by seq 10 in `scripts/mcp_servers/audit.py`; this document consumes it and does not define it, because `mcp_servers` cannot import `agent.secrets_masker.redact_path()` under the `mcp_servers-no-agent` contract.
- Cross-plan overlap on `docs/22_mcp/mcp_04_04_mdq.md` is a documentation-sequencing dependency, not a conflict.

## Design decisions
- Values that must stay comparable across calls are hashed (`hash_query_value()` already exists in `scripts/mcp_servers/audit.py`); paths inside an authorized root become root-relative identifiers, and paths outside become hashes.
- The 80-character truncation is replaced by hashed or relative values, so truncation no longer leaks a prefix of a customer path.

## Alternatives considered
- Import `redact_path()` from `scripts/agent/secrets_masker.py` — rejected: the import-linter contract `mcp_servers-no-agent` forbids `mcp_servers -> agent`.

## Implementation
### Target file
`scripts/mcp_servers/mdq/audit_target.py`

### Procedure
- In `extract_audit_target()` (line 15), replace `str(args.get("query"))` and `str(args.get("pattern"))` with the hashed form.
- Replace `str(paths[0])[:80]` (line 28), `str(args.get("path", ""))[:80]` (line 25), and `str(args.get("chunk_id", ""))[:80]` (line 23) with the root-relative identifier or hash from the shared helper.
- Add the persisted path counts and root identity to the returned target for the indexing tools.

### Method
- The helper is called with the authorized roots the service already holds, so the root-relative form is computed from the same roots the authorization decision used.
- The function stays pure: no I/O, no logging, no path resolution beyond the helper call.

### Details
- `stats` keeps its fixed label `mdq-mcp` (line 32); it carries no path.
- The unknown-tool and empty-tool-name branches stay returning an empty string.

### Companion test files
- `tests/mcp_servers/mdq/test_audit_target.py`
  - Procedure: replace the raw-value assertions in `test_query_only`, `test_returns_path`, and `test_returns_pattern` with hashed and root-relative expectations; the truncation tests are replaced by hashed-length expectations.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_audit_target.py`

## Compatibility considerations
- The audit target value is persisted, so existing log rows keep the old raw form; the change affects new records only.
- `tests/mcp_servers/test_audit_redaction.py` is run unchanged and must stay passing.

## Security considerations
- Raw absolute paths, customer names, and secrets must not reach persistent logs (AC-4); the hashed form is the intended replacement.
- Root-relative identifiers must not expose a path outside an authorized root.

## Rollback considerations
- Revert the commit; the Phase 1 redaction assertions in the companion test fail again.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_audit_target.py tests/mcp_servers/test_mdq_audit.py tests/mcp_servers/test_audit_redaction.py`
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- No raw query, regex, or absolute path appears in a persisted audit record.
- Path counts and root identities are present for the indexing tools.

## Out of Scope
- The path-identifier helper itself (seq 10) and the single emission boundary (seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion test file is covered by this document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Documentation is a separate row (seq 27) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-006 (audit target redaction)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `scripts/mcp_servers/mdq/audit_target.py`, `tests/mcp_servers/mdq/test_audit_target.py`
