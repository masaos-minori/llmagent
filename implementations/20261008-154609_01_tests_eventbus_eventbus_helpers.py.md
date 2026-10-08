## Goal
Let the shared EventBus test client helper take an optional SSE idle timeout, so a test module can end idle streams quickly without changing the default for other modules (REQ-001 of the Plan).

## Scope
- Add one optional parameter to the helper and apply it to the configuration after construction; change nothing else in the helper.

## Assumptions
- The configuration validates the idle timeout against the heartbeat interval in its constructor, so a short value cannot be passed to the constructor; other test modules assign the attribute after construction, which the validation does not check.
- The configuration object built by the helper is the same object the app reads (the helper patches the loader to return it).

## Design decisions
- The parameter defaults to no change; when given, it is assigned on the configuration with the same attribute-assignment technique other modules use.

## Alternatives considered
- Shortening the default for every module: rejected for this change; it can alter other tests' timing (see the Plan's UNK-02).
- Patching the production default in the transition module: rejected; the production default constant is not what the configuration uses.

## Implementation
### Target file
tests/eventbus/eventbus_helpers.py

### Procedure
1. Add the optional parameter `sse_idle_timeout: float | None = None` to the helper.
2. After the configuration object is created, assign the value when it is not None.
3. Run the modules that use the helper.

### Method
A one-parameter addition and a three-line conditional assignment.

### Details
Use `object.__setattr__` as the other modules do, because the configuration is a frozen dataclass; keep the existing arguments and their order.

## Compatibility considerations
- Default behavior is unchanged for the eight modules that use the helper.

## Security considerations
- None: test helper only.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run ruff format` and `ruff check` on the file; `uv run pytest tests/eventbus -q --timeout=60` as regression.

## Completion criteria
- Calling without the argument leaves the default; calling with a value sets it on the app's configuration (REQ-001).

## Out of scope
- Changing defaults for other modules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the optional parameter and assignment | Completed | 20261008-155818 | 20261008-155818 |  |
| 2 | Run the modules that use the helper | Completed | 20261008-155818 | 20261008-155818 |  |

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
- **Requirement ID**: REQ-001 (optional idle-timeout argument)
- **Source issue**: issues/20261008-115806_ebsubtimeout01_fix-timeouts-in-the-eventbus-subscribe-transition-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-154434_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-154609
- **Related target files**: tests/eventbus/eventbus_helpers.py