## Goal

Reconcile the contradictory guard comment in `scripts/shared/mcp_config.py` so it states that
non-required subprocess servers are disallowed because spawn failures must fail closed, instead of
claiming the spawn path ignores `required`. This makes the module agree with the documented
fail-closed constraint without changing any startup runtime behavior.

## Scope

- **In-Scope**:
  - Rewrite the guard comment in `_validate_startup_requirements` in `scripts/shared/mcp_config.py`
    so it states that non-required subprocess servers are disallowed because spawn failures must
    fail closed, instead of claiming the spawn path ignores `required`.
- **Out-of-Scope**:
  - Do not change the `required=false` rejection for subprocess servers (the code at
    `scripts/shared/mcp_config.py:169` is unchanged).
  - Do not alter any other validation logic.
  - No `docs/*.md` changes.

## Assumptions

- The rejection at `scripts/shared/mcp_config.py:169` (`required=false` + `startup_mode=subprocess`
  → `ValueError`) is intentional and correct (fail closed: a subprocess server that fails to spawn
  cannot degrade gracefully). Only the comment is wrong.
- The startup module (`scripts/agent/startup_mcp_starter.py`) branches on `cfg.required` and would
  disable-and-continue for a non-required server — i.e. the spawn path does NOT ignore `required`.
  The current comment falsely claims the opposite.

## Design decisions

- Comment-only change: rewrite the two-line guard comment to state the verified fact. Do not touch
  the `if self.startup_mode == StartupMode.SUBPROCESS and not self.required:` guard or its
  `raise ValueError`.

## Alternatives considered

- Changing the guard logic — rejected: REQ-003 forbids it; the rejection is correct. This is a
  documentation reconciliation only.

## Implementation

### Target file

`scripts/shared/mcp_config.py`

### Procedure

1. Locate the guard comment in `_validate_startup_requirements`
   (`scripts/shared/mcp_config.py:167-168`):
   ```python
           # ADR-004 Exceptions: the spawn path ignores `required`, so a non-required
           # subprocess server would still abort startup on a spawn failure.
   ```
2. Replace it with a comment that states the verified fact, e.g.:
   ```python
           # ADR-004 Exceptions: non-required subprocess servers are disallowed because a
           # subprocess server that fails to spawn must fail closed (cannot degrade gracefully).
   ```
3. Leave the guard (`:169-173`) and all other validation logic unchanged.
4. Run `ruff` and `mypy` on the touched file, and confirm no behavior changed. (AC-003)

### Method

- **Comment only.** Edit the two-line comment in place; do not reflow or reorder the method. Verify
  the comment is the only occurrence before editing.
- **State the verified fact.** The comment should say that non-required subprocess servers are
  disallowed because spawn failures must fail closed — matching the config rejection and ADR-004.
- **Do not** retain the false claim that "the spawn path ignores `required`".

### Details

- `REQ-003`: The `mcp_config.py` guard comment no longer asserts that the spawn path ignores
  `required`; it states that non-required subprocess servers are disallowed because spawn failures
  must fail closed.
- **AC-003:** the guard comment no longer asserts that the spawn path ignores `required`.

## Compatibility considerations

Comment-only change. No behavioral or API impact.

## Security considerations

N/A: documentation reconciliation only; no change to the fail-closed enforcement.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/shared/mcp_config.py` | Static — lint and type check | `uv run ruff check` / `uv run mypy` | Clean (no new findings) |
| `scripts/shared/mcp_config.py` | Unit — config validation | `uv run pytest tests/shared/test_mcp_config.py` | `test_subprocess_non_required_rejected` still passes; rejection unchanged |

## Completion criteria

- The `mcp_config.py` guard comment no longer asserts that the spawn path ignores `required`; it
  states that non-required subprocess servers are disallowed because spawn failures must fail
  closed (AC-003).

## Out of scope

Changing the `required=false` rejection for subprocess servers, altering any other validation
logic, and any `docs/*.md` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261019-102949 | 20261019-102949 | REQ-003 Rewrote guard comment to state fail-closed rationale |
| 2 | Add or update tests per Validation plan | Completed | 20261019-102949 | 20261019-102949 | REQ-003 N/A: comment-only change, no new tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019-102949 | 20261019-102949 | all REQs ruff/mypy clean; test_mcp_config(37) pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261019-102949 | 20261019-102949 | N/A N/A: no docs in scope |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: issues/20261018-200733_agent001_agent-startup-graceful-disable-path-for-non-required-subprocess-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-220020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261018-220020
- **Related target files**: scripts/shared/mcp_config.py