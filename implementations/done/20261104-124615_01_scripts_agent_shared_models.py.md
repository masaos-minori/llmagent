## Goal
- Correct the `ToolExecEvent.idempotency_key` field comment so it says the value is the workflow-scoped logical-call identity recorded for the audit log and that it differs from the transport `X-Idempotency-Key` (`REQ-001`: stop the audit field being read as a deduplication key).

## Scope
**Release unit**: N/A: not part of a release unit

- Comment-only change to one field of `ToolExecEvent` in `scripts/agent/shared/models.py`. No value, type, default, field order, or caller changes.

## Assumptions
- No code reads `ToolExecEvent.idempotency_key` back: a repository search over `scripts/` finds only the writers (the runner's `audit_tool_exec` call and `tool_audit.audit_tool_exec`), so a comment change cannot alter behavior (checked in Step 3a).
- The audit value is built by `_idempotency_key` in `scripts/agent/tool_runner.py` as `{workflow_id}:{task_id}:{turn_id}:{call_id}` and is passed only to the audit call; the transport key is a different, deterministic hash derived in `HttpTransport.call` (checked in Step 3a).
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it; the `prose-dependency` warning names an already archived Plan.
- The Plan's line-number citations were stale and were replaced by symbol references in the same cycle (Step 3a); this document cites symbols only.

## Design decisions
- Replace the trailing inline comment with a short comment block above the field, so the wording fits the 88-character limit of `rules/coding.md` and the field line itself keeps its code unchanged.
- Describe the value by its composition, not by file or function names, so the comment does not go stale.

## Alternatives considered
N/A: single comment edit; the Plan's DD-1 already chose to correct both documentation sites (Option A).

## Implementation
### Target file
`scripts/agent/shared/models.py`

### Procedure
1. Find the `idempotency_key: str = ""` field of `ToolExecEvent`; it carries the trailing comment `# stable, retry-invariant key for deduplication`.
2. Remove that trailing comment and add the comment block below immediately above the field.

### Method
Edit comment text only. New comment block, each line within 88 characters:

```text
    # Workflow-scoped logical-call identity ({workflow_id}:{task_id}:{turn_id}:
    # {call_id}) recorded for the audit log. Distinct from the transport
    # X-Idempotency-Key, which drives server-side deduplication; nothing
    # deduplicates on this value.
    idempotency_key: str = ""
```

### Details
- The field's type, default, position, and every other field stay as they are.
- The audit call in `scripts/agent/tool_runner.py` and `scripts/shared/http_transport.py` are reference files only and are not modified.

## Compatibility considerations
N/A: comment-only; no runtime, schema, or log-format change (the logged field name and value are unchanged).

## Security considerations
N/A: no behavior change; the comment names no secret and no configuration value.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run ruff format --check scripts/agent/shared/models.py` and `uv run ruff check scripts/agent/shared/models.py` report no findings.
- Comment-only proof, exit 0: `git show HEAD:scripts/agent/shared/models.py | uv run python -c "import ast,sys; a=ast.dump(ast.parse(sys.stdin.read())); b=ast.dump(ast.parse(open('scripts/agent/shared/models.py').read())); sys.exit(a != b)"`.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus` shows no new errors.
- `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_audit_log_format.py tests/agent/test_tool_runner.py -q` passes unchanged.
- `uv run python tools/generate_reference_table.py --check` exits 0.

## Completion criteria
- The field comment names the workflow-scoped logical-call identity, says it is recorded for the audit log, and says it differs from the transport `X-Idempotency-Key` (`AC-1`).
- No wording attributes deduplication to this field, and the AST comparison shows no code change.

## Out of Scope
- Which key the audit event records, the transport key derivation, the `tool_call_state` key, the dispatcher cache, and any other audit field.
- The two documentation rows of the Plan (separate procedure documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the field comment as described in Implementation > Procedure/Method | Completed | 20261104-125245 | 20261104-125256 | Changed: scripts/agent/shared/models.py (comment only). Step 2 stale check: clean |
| 2 | Run the validation plan: format, lint, comment-only check, mypy, existing audit tests | Completed | 20261104-125330 | 20261104-130400 | ruff format/check, AST comment-only check, mypy (491 files), bandit, lint-imports, gates: pass. Targeted 164 passed; full suite 11445 passed; diff-cover 100%. Step 5/6 N/A: no docs/00_index.md task-scope mapping for scripts/agent/shared/models.py |

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
- **Requirement ID**: `REQ-001` (audit field comment states the logical-call identity, distinct from the transport key)
- **Source issue**: `issues/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-165600_idemaudit001_audit-idempotency-key-mismatch.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-124615
- **Related target files**: `scripts/agent/shared/models.py`