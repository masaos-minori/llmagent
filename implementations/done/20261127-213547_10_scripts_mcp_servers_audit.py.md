## Goal

Add the path-identifier helper MDQ needs to the shared audit module, because `mcp_servers` cannot import `agent.secrets_masker.redact_path()` under the import-linter contract, without changing existing behavior for the other servers (REQ-006 audit redaction).

## Scope
**Release unit**: N/A: not part of a release unit (Plan step 2 is not listed in any `### Release units` entry)

## Assumptions
- `tests/mcp_servers/test_audit_redaction.py` is a related test but not a target row, so it is not a companion; it is run unchanged as the behavior lock.
- Nine servers plus five test modules import `scripts/mcp_servers/audit.py` (re-verified 20261127); the change is additive, so no other server's audit output changes.
- The contract `mcp_servers-no-agent` in `.importlinter` forbids `mcp_servers -> agent`; `redact_path()` exists only in `scripts/agent/secrets_masker.py`.
- Cross-plan overlap on `scripts/mcp_servers/audit.py` and `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` with the CI/CD error and audit-coverage plan is compatible: that plan removes a duplicate `requested_target` assignment and records the CI/CD vocabulary; this row adds a function and changes no output.

## Design decisions
- The helper returns a root-relative identifier for a path inside an authorized root and a hash otherwise, so the persisted value stays comparable without exposing the absolute path.
- The helper takes the authorized roots as an argument rather than reading configuration, so it stays policy-only.

## Alternatives considered
- Import `redact_path()` from `scripts/agent/secrets_masker.py` — rejected: the import-linter contract forbids it.
- Put the helper in `scripts/mcp_servers/mdq/audit_target.py` — rejected: the plan's design places redaction in the shared module so the other servers get the same semantics later; MDQ is the first consumer.

## Implementation
### Target file
`scripts/mcp_servers/audit.py`

### Procedure
- Add `path_identifier()` (new) next to `hash_query_value()` (line 193) and `redact_url()` (line 214).
- Do not change `_build_audit_record()` (line 68), `_audit_log()` (line 133), or `AuditEmission` (line 238).

### Method
- The function resolves the path against the supplied roots; inside a root it returns the path relative to that root, otherwise the hash of the canonical path.
- No I/O and no logging inside the helper.
- Step 3b correction (20261128): "resolves" cannot mean `Path.resolve()`, because symlink resolution is a filesystem lookup and conflicts with the no-I/O rule. The helper normalizes textually (`os.path.expanduser` + `os.path.normpath`), so a path that reaches an authorized root only through a symlink falls back to the hash branch — the fail-closed direction.
- Step 3b correction: the root-relative identifier is returned as-is, without segment redaction. AC-4 forbids absolute paths, queries, regexes, and raw exception text, and a root-relative identifier inside an authorized root is none of those. A customer name that is part of a path segment inside an authorized root is therefore still persisted; this is the plan's stated design (`Design` > Path redaction) and is recorded here as a known limit of the helper, not as an implementation deviation.

### Details
- The hash uses the same hashing convention as `hash_query_value()` so persisted values are comparable across servers.
- Step 3b correction: the helper calls `hash_query_value()` directly rather than reimplementing SHA-256, so the convention is shared by construction.

## Compatibility considerations
- Existing servers do not call the new function, so their audit output is unchanged; `tests/mcp_servers/test_audit_redaction.py` is the guard.
- The issue's instruction is to stop and report if another server's output changes.

## Security considerations
- A root-relative identifier must not expose a path outside an authorized root; the hash branch is the fallback.

## Rollback considerations
- N/A: remove the added function and revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_audit_redaction.py tests/mcp_servers/mdq/test_audit_target.py`
- `PYTHONPATH=scripts uv run lint-imports` to confirm no `mcp_servers -> agent` import is introduced.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- The helper exists and is used by `scripts/mcp_servers/mdq/audit_target.py` (seq 03).
- No other server's audit output changes.
- The import-linter contract still passes.

## Out of Scope
- The MDQ-side use of the helper (seq 03) and the documentation of redaction (seq 29).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | `path_identifier()` and `_normalize_path()` added; textual normalization (see Method) |
| 2 | Add or update tests per Validation plan | Completed | 20261128 | 20261128 | Step 3b correction: the guard file alone does not cover a new public function, so `TestPathIdentifier` (8 tests) was added to `tests/mcp_servers/test_audit_redaction.py`; the existing assertions are unchanged and still hold as the behavior lock |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-093658 | 20261128-093658 | `uv run pytest tests/mcp_servers/test_audit_redaction.py tests/mcp_servers/mdq/test_audit_target.py` — 41 passed in the guard file; `test_audit_target.py` is seq 03's target and is not affected yet. ruff/bandit/lint-imports (6 contracts kept)/mypy/check_module_size/check_test_taxonomy Pass end-of-unit gate 20261128 as recorded in seq 01's gates row |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Documentation is a separate row (seq 29) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-006 (path redaction in the shared audit module)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `scripts/mcp_servers/audit.py`