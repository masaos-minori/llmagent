## Goal
Create `scripts/eventbus/README.md` to document the layer architecture referenced by `db.py`'s stub header comment. Implements REQ-004 (document layer boundaries).

## Scope
- Create a new `scripts/eventbus/README.md` file documenting:
  - Layer architecture (connection layer, event repo, delivery repo, DLQ repo)
  - Stub module pattern (`db.py` re-exports)
  - Rule: "Do not add new functions here. Add them to the appropriate layer module and re-export from this stub."

## Assumptions
- The layer architecture documented here matches the actual structure of the eventbus module
- The rule about adding new functions to the appropriate layer module is still valid

## Design decisions
- Document the layered architecture that exists in the codebase
- Include the stub module pattern as it's explicitly referenced by `db.py`'s docstring
- Keep the README concise — focused on architecture, not implementation details

## Alternatives considered
- No README: rejected because `db.py`'s stub header references one and developers need guidance on which module owns which responsibility
- Separate architecture document in `docs/`: rejected because the README should live alongside the code it describes

## Implementation
### Target file
`scripts/eventbus/README.md`

### Procedure
Create a new README documenting the eventbus layer architecture.

### Method
1. Read current `db.py` stub header to confirm the referenced content
2. Review each layer module to understand its responsibilities
3. Write the README with:
   - Overview of the eventbus module purpose
   - Layer architecture description
   - Stub module pattern explanation
   - Rule about adding new functions

### Details
Create `scripts/eventbus/README.md` with the following content:

```markdown
# EventBus Module

Layered SQLite-based event bus for managing event persistence, delivery, and dead-letter queue operations.

## Architecture

The module follows a layered architecture:

1. **Connection layer** (`db_conn.py`): SQLite connection lifecycle, locking, pragma application
2. **Schema layer** (`schema.py`): Schema definition, migration logic
3. **Event repository** (`event_repo.py`): All event read/write operations
4. **Delivery repository** (`delivery_repo.py`): Ack/nack semantics and per-consumer delivery state
5. **DLQ repository** (`dlq_repo.py`): Dead-letter queue operations

## Stub Module Pattern

`db.py` is a stub module that re-exports functions from the layer modules above. It provides a single entry point for consumers of the eventbus module.

**Rule**: Do not add new functions here. Add them to the appropriate layer module and re-export from this stub.
```

## Compatibility considerations
- This is a documentation-only change; no behavioral impact
- Existing code that imports from `db.py` will continue to work unchanged

## Security considerations
- None — documentation only

## Rollback considerations
- Revert: delete the README file
- Risk: none — removing documentation has no runtime impact

## Validation plan
- Manual: verify content completeness
  - Read file and confirm it documents: layer architecture, stub module pattern, and the rule about adding new functions to the appropriate layer module
- Verify `db.py` stub header reference is accurate:
  ```bash
  rg "See scripts/eventbus/README.md" scripts/eventbus/db.py
  ```

## Completion criteria
- [ ] `scripts/eventbus/README.md` exists
- [ ] Documents layer architecture (connection, event repo, delivery repo, DLQ repo)
- [ ] Documents stub module pattern (`db.py` re-exports)
- [ ] Includes rule: "Do not add new functions here. Add them to the appropriate layer module and re-export from this stub."

## Out of scope
- Removing duplicate constants from Python modules (handled in separate procedure documents)
- Renaming any column names
- Changing SQL query logic
- Adding new functionality
- Modifying schema.sql

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260920-162933 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260920-162939 | N/A: documentation-only change, no tests needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260920-162944 | N/A: documentation-only change, no validation sequence needed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260920-162949 | This step IS the documentation update — README.md created |

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
- **Requirement ID**: REQ-004 (document layer boundaries)
- **Source issue**: issues/20260920-151726_eb001_refactor-eventbus-column-constants-and-add-layer-documentation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-153828_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-154418
- **Related target files**: scripts/eventbus/README.md