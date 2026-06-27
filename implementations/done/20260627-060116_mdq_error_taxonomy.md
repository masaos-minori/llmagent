## Goal

Define MDQ tool error taxonomy and error handling by creating explicit MDQ domain exceptions and mapping them to appropriate MCP tool responses.

## Scope

**In-Scope**:
- Create MdqValidationError, MdqAuthorizationError, MdqNotFoundError, MdqIndexNotReadyError, MdqDatabaseError, MdqConsistencyError
- Map validation errors to tool error
- Map not found to tool error
- Map unauthorized path to tool error
- Map DB unavailable to health impact
- Handle unexpected exceptions consistently

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' error handling

## Assumptions

1. Tool-level errors return is_error=true in MCP response
2. Transport-level failures remain distinguishable from tool errors
3. Logs include error kind for operational debugging

## Implementation

### Target file: scripts/mcp/mdq/models.py

**Procedure**: Add error class hierarchy (MdqServiceError base, subclasses for each error type).

**Method**: Add new exception classes after existing MdqServiceError class in models.py.

**Details**:
1. Keep existing `MdqServiceError(RuntimeError)` as base class (line 52)
2. Add subclass exceptions:
   - `MdqValidationError(MdqServiceError)` — for validation errors (invalid input, bad regex, etc.)
   - `MdqAuthorizationError(MdqServiceError)` — for authorization errors (unauthorized path access)
   - `MdqNotFoundError(MdqServiceError)` — for not found errors (file not found, chunk not found)
   - `MdqIndexNotReadyError(MdqServiceError)` — for index not ready errors (index missing, stale)
   - `MdqDatabaseError(MdqServiceError)` — for database errors (DB unavailable, migration failed)
   - `MdqConsistencyError(MdqServiceError)` — for consistency errors (FTS mismatch, data corruption)

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Raise appropriate exceptions per error condition.

**Method**: Replace generic MdqServiceError raises with specific exception types in service methods.

**Details**:
1. Validation errors: raise MdqValidationError (e.g., invalid regex pattern, bad query)
2. Not found: raise MdqNotFoundError (e.g., file not found, chunk not found)
3. Unauthorized path: raise MdqAuthorizationError (e.g., path outside allowed_dirs)
4. DB unavailable: raise MdqDatabaseError (e.g., migration failed, connection error)
5. Index not ready: raise MdqIndexNotReadyError (e.g., index missing, stale)

### Target file: scripts/mcp/mdq/server.py

**Procedure**: Update FastAPI exception handlers for each error type.

**Method**: Add per-error-type exception handlers in server.py.

**Details**:
1. Replace single handler with per-error-type handlers:
   - MdqValidationError → HTTP 400 (tool error)
   - MdqAuthorizationError → HTTP 403 (authorization failure)
   - MdqNotFoundError → HTTP 404 (not found)
   - MdqIndexNotReadyError → HTTP 503 (service unavailable)
   - MdqDatabaseError → HTTP 503 (health impact)
   - MdqConsistencyError → HTTP 500 (internal error)
2. Map tool errors to appropriate HTTP status codes
3. Add error kind logging in each handler

### Target file: scripts/mcp/mdq/server.py

**Procedure**: Add error kind logging and audit log detail.

**Method**: Modify _audit_log call to include error_kind field.

**Details**:
1. In exception handlers, extract error_kind = type(e).__name__
2. Pass error_kind to _audit_log in detail parameter
3. Log error_kind for operational debugging

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| models.py | Verify error class hierarchy | Check inheritance chain | All errors inherit from MdqServiceError |
| service.py | Verify validation error raises MdqValidationError | Trigger validation error | MdqValidationError raised |
| server.py | Verify tool error returns is_error=true | Call tool with invalid input | HTTP 400 returned, not 500 |
| server.py | Verify DB error returns appropriate status | Simulate DB failure | HTTP 503 returned |

## Risks

- **Risk**: Breaking changes to consumers expecting HTTP 500 for all errors | **Likelihood**: Medium | **Mitigation**: Document breaking changes; consider backward-compatible status codes | False
- **Risk**: Error kind classification misses edge cases | **Likelihood**: Low | **Mitigation**: Use broad error categories; document limitations | False
