## Goal

Remove stale POST /ack compatibility alias reference from Event Bus document guide routing table.

## Scope

- Update `docs/06_eventbus_00_document-guide.md` — remove POST /ack reference from routing table (line 79)

## Assumptions

1. The existing documentation structure and content are correct; only the stale reference needs correction
2. POST /ack compatibility alias has been deleted (confirmed via grep)

## Design decisions

- Remove the POST /ack entry from the routing table entirely since it no longer exists
- If the context around the reference is still relevant, add a note explaining the actual ack mechanism

## Alternatives considered

- Adding inline notes within existing sections instead of removing references
- Creating a separate appendix for deprecated endpoints

## Implementation

### Target file

- `docs/06_eventbus_00_document-guide.md`

### Procedure

#### Step 1: Locate the stale reference

1. Open `docs/06_eventbus_00_document-guide.md`
2. Find line 79 (the routing table entry)

#### Step 2: Remove the POST /ack entry

Find the row containing "POST /ack" in the routing table and remove it entirely.

Change from:

```markdown
| POST /ack | ... |
```

To:

```markdown
(removed)
```

#### Step 3: Verify cross-references

If there are any cross-references to this section elsewhere in the document, ensure they still work correctly.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The corrected routing table helps prevent misunderstanding about available endpoints

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the removal if the original meaning was intentional

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/06_eventbus_00_document-guide.md` | Stale reference removal | grep for POST /ack | No POST /ack references remain |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-125038_require.md
- Source plan: plans/20260722-170550_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-181529
- Related target files: docs/06_eventbus_00_document-guide.md
