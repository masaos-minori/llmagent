## Goal
- Correct the one line of the agent runtime-architecture document that says `ensure_ready`, `start_http_subprocess`, and `restart` are guarded against being ignored once shutdown has started, so it matches the new contract: the first and last are ignored, and `start_http_subprocess` raises a typed suppression error (`REQ-007`: documentation matches the corrected shutdown guard).

## Scope
**Release unit**: N/A: not part of a release unit

- Documentation only: one line in `docs/23_agent/agent_02_runtime-architecture.md`.

## Assumptions
- The current line reads: `ensure_ready`/`start_http_subprocess`/`restart` are guarded against being ignored once shutdown has started. (checked in Step 3a)
- After the production procedures, `ensure_ready` and `restart` still return without acting once shutdown has started, and `start_http_subprocess` raises `StartSuppressedError`.
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it.

## Design decisions
- Keep the line as one sentence in the same register and use the same backticked names; state the two behaviors instead of the vague "guarded".

## Alternatives considered
N/A: single-line correction.

## Implementation
### Target file
`docs/23_agent/agent_02_runtime-architecture.md`

### Procedure
Replace the one line below with the corrected line; do not edit the surrounding paragraph about the lifecycle contract.

### Method
Before:

```text
`ensure_ready`/`start_http_subprocess`/`restart` are guarded against being ignored once shutdown has started.
```

After:

```text
Once shutdown has started, `ensure_ready` and `restart` are ignored, and `start_http_subprocess` raises a typed suppression error instead of returning silently.
```

### Details
- The line is replaced as a whole; keep the blank lines around it.
- Do not add a file path, symbol location, or concrete value.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no secret or concrete configuration value.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `git diff -U0 docs/23_agent/agent_02_runtime-architecture.md` shows exactly one removed and one added line.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_02_runtime-architecture.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, and `uv run python tools/check_docs_consistency.py --domain agent` report no findings.

## Completion criteria
- The line states that `ensure_ready` and `restart` are ignored and that `start_http_subprocess` raises a typed suppression error once shutdown has started (`AC-6`).
- The docs checkers are clean and no other line changed.

## Out of Scope
- Any other line of the document, the other two documents of the Plan, and any code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the line as described in Implementation > Procedure/Method | Pending | — | — | |
| 2 | Run the documentation checkers named in the Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (documentation matches the corrected shutdown guard)
- **Source issue**: `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095204_startretry001_startup-retry-blocked-cooldown.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-140850
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`
