## Goal

Remove the literal port number from the EventBus configuration document and replace with prose describing what the setting controls rather than its current value.

## Scope

Modify `docs/06_eventbus_05_configuration-and-operations.md`: remove the literal port number "8010" at line 95 and confirm the surrounding sentence still reads coherently.

## Assumptions

- Line 95 contains a literal port number "8010" that duplicates `config/agent.toml` (or the relevant EventBus config surface) and goes stale when the port changes.
- Removing the port number does not break the sentence structure.
- The surrounding prose ("Or `uvicorn eventbus.app:app --host 127.0.0.1`") remains coherent after removal.

## Design decisions

- Replace the literal port number with a description of what the setting controls rather than its current value.
- Preserve the rest of the sentence describing the start command.

## Alternatives considered

- Retain the port number with a note that it is illustrative: rejected because the policy targets literal port numbers in prose regardless of intent.
- Remove the entire sentence about the uvicorn start command: rejected because the sentence describes operational behavior, which is retain-category content.

## Implementation

### Target file

`docs/06_eventbus_05_configuration-and-operations.md`

### Procedure

1. Read line 95 and its surrounding paragraph to confirm the context of the literal port number.
2. Remove the literal port number.
3. Confirm the surrounding sentence still reads coherently.
4. Run `uv run python tools/check_docs_content_policy.py` to verify zero findings.

### Method

Read line 95: "Or `uvicorn eventbus.app:app --host 127.0.0.1 --port 8010`."

The literal port number "8010" appears as part of an alternative start command using uvicorn. This is a concrete configuration value that duplicates the EventBus config surface and goes stale when the port changes.

Replace "--port 8010" with prose describing the host/port binding without referencing the specific port assignment. The sentence remains grammatically coherent without the explicit port number. The EventBus server's identity is established by its module path; the specific port is an implementation detail best sourced from the configuration file.

### Details

Line 95 currently reads:
```
Or `uvicorn eventbus.app:app --host 127.0.0.1 --port 8010`.
```

The literal port number "8010" appears as part of an alternative start command using uvicorn. This is a concrete configuration value that duplicates the EventBus config surface and goes stale when the port changes.

Replace with:
```
Or `uvicorn eventbus.app:app --host 127.0.0.1`.
```

The sentence remains grammatically coherent without the explicit port number. The EventBus server's identity is established by its module path; the specific port is an implementation detail best sourced from the configuration file.

## Compatibility considerations

- The replacement must maintain the same information coverage as the original sentence. The EventBus server's identity is preserved; only the concrete port number is removed.
- Cross-references to other documents must be preserved.

## Security considerations

- None identified. This is a documentation-only change removing a literal port number.

## Rollback considerations

- If the prose replacement loses critical identification of the EventBus server's binding address, the original sentence can be restored temporarily while a better replacement is drafted.
- The rollback path is straightforward: revert the edit and restore the original sentence.

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/06_eventbus_05_configuration-and-operations.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/06_eventbus_05_configuration-and-operations.md` | Zero literal-port-number findings; structure check passes |

## Completion criteria

- The literal port number at line 95 has been removed.
- The surrounding sentence remains coherent and still describes what the setting controls.
- `check_docs_content_policy.py` reports zero literal-port-number findings for this file.

## Out of scope

- Modifying any other content in this file beyond the flagged port number and its immediate sentence.
- Any other file or section of this document.
- Any file outside the EventBus domain.

## execution status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read line 95 and its surrounding paragraph | Pending | — | — | |
| 2 | Remove the literal port number and replace with prose | Pending | — | — | |
| 3 | Run validation checks | Pending | — | — | |

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
- **Requirement ID**: REQ-001: Remove the literal port number at line 95 (and any other occurrence in the same paragraph/section not caught by the single-line finding)
- **Source issue**: issues/20260905-153715_dcp006_eventbus_docs_content_policy_cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-211931_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-000740
- **Related target files**: docs/06_eventbus_05_configuration-and-operations.md
