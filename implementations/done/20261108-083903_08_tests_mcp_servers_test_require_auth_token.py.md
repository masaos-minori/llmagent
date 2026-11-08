## Goal

Add a structural enforcement test to `tests/mcp_servers/test_require_auth_token.py` that fails when any `*_server.py` module attaches the Bearer middleware without routing its token through the shared enforcement point `require_auth_token()`, and that fails a synthetic module which calls `attach_auth_middleware` with an unvalidated token (`REQ-001`/`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The plan resolves to approach (a): all ten servers call `require_auth_token()` before `attach_auth_middleware()` (`UNK-01`); the six consolidated servers are covered by their own procedures.
- The existing test file already lists all ten servers in `_SERVERS` and imports `require_auth_token` from `mcp_servers.server`.
- `require_auth_token(label, env_var, token)` is the single shared enforcement point (`scripts/mcp_servers/server.py` `L137-151`).

## Design decisions
- **AST-based scanner.** Add a module-level helper `_routes_through_enforcement_point(source: str) -> bool` that parses the module source with `ast` and returns `True` iff it finds a module-scope call to `require_auth_token(...)`. This is robust to message-wording drift and directly detects a module that attaches middleware without the shared point.
- **Positive coverage.** A parametrized test over the ten `*_server.py` source files asserts each routes through the enforcement point (`REQ-001`).
- **Negative coverage (`REQ-002`).** A test builds a synthetic module source that calls `attach_auth_middleware(...)` without `require_auth_token(...)` and asserts the scanner flags it (`False`).

## Alternatives considered
- **Textual substring scan (`"require_auth_token" in source`).** Weaker — matches comments/strings. Rejected in favor of the AST scan.
- **Runtime import check only.** The existing `test_empty_token_prevents_every_server_from_importing` already covers import-time refusal; it cannot detect a module that attaches middleware without the shared point. The structural scanner adds that gap (`REQ-002`).

## Implementation
### Target file
`tests/mcp_servers/test_require_auth_token.py`

### Procedure
1. Add an `import ast` at the top of the file.
2. Add the `_routes_through_enforcement_point(source: str) -> bool` helper: parse `source` with `ast`, walk the tree, and return `True` on the first `ast.Call` whose `func` is an `ast.Name` equal to `"require_auth_token"`.
3. Add a module-level list of the ten server source paths under `scripts/mcp_servers/**/*_server.py` (or derive them by globbing that directory).
4. Add a parametrized test `test_every_server_routes_through_shared_enforcement_point` asserting `_routes_through_enforcement_point(source) is True` for each of the ten files.
5. Add `test_attach_middleware_without_enforcement_point_is_flagged`: build a synthetic source string that imports `attach_auth_middleware` and calls it once without any `require_auth_token` call, and assert `_routes_through_enforcement_point(synthetic) is False`.
6. Keep the existing helper tests and the import-refusal parametrization unchanged.

### Method
Append the helper and two tests to the existing file; do not alter existing tests. The glob/helper live at module scope.

### Details
Recommended scanner (append near the other module-level helpers):
```python
import ast


def _routes_through_enforcement_point(source: str) -> bool:
    """True iff the module calls require_auth_token() at module scope."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "require_auth_token"
        ):
            return True
    return False


_SERVER_SOURCE_GLOB = str(_SCRIPTS / "mcp_servers" / "*" / "*_server.py")
```
Positive coverage:
```python
@pytest.mark.parametrize("path", sorted(glob.glob(_SERVER_SOURCE_GLOB)))
def test_every_server_routes_through_shared_enforcement_point(path: str) -> None:
    with open(path, encoding="utf-8") as handle:
        assert _routes_through_enforcement_point(handle.read()) is True
```
Negative coverage (`REQ-002`):
```python
def test_attach_middleware_without_enforcement_point_is_flagged() -> None:
    synthetic = (
        "from mcp_servers.server import attach_auth_middleware\n"
        "attach_auth_middleware(app, '')\n"
    )
    assert _routes_through_enforcement_point(synthetic) is False
```
The implementer may tighten the scanner (for example also asserting no literal-empty `attach_auth_middleware(app, "")` call remains) but must keep the negative test green.

## Compatibility considerations
- Purely additive test code; no production change. Existing tests are untouched.

## Security considerations
- The scanner strengthens the auth guarantee: a future eleventh server that forgets `require_auth_token()` fails CI rather than silently accepting unauthenticated requests.

## Rollback considerations
- Revert the commit; only test code changes.

## Validation plan
- `uv run pytest tests/mcp_servers/test_require_auth_token.py` — new and existing tests pass.
- `uv run pytest tests/mcp_servers` — new and existing tests pass.
- `uv run ruff check tests/` — clean.

## Completion criteria
- `REQ-001`: the parametrized test asserts all ten `*_server.py` modules route through `require_auth_token()`.
- `REQ-002`: the negative test asserts a module attaching middleware without `require_auth_token()` is flagged.

## Out of Scope
- Consolidating the six inline guards — handled in the per-server procedures.
- Changing the middleware accept-all default — handled in the `server.py` procedure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261108-170747 | 20261108-170747 | — |
| 2 | Add or update tests per Validation plan | Completed | 20261108-170747 | 20261108-170747 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261108-170747 | 20261108-170747 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261108-170747 | 20261108-170747 | — |

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
- **Requirement ID**: `REQ-001` (shared enforcement point scanned), `REQ-002` (unvalidated attach fails the checker)
- **Source issue**: `issues/20261107-132052_mcpstartup003_auth-guard-single-point.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-214719_mcpstartup003_auth-guard-single-point.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-083903
- **Related target files**: `tests/mcp_servers/test_require_auth_token.py`
- **Related target files**: {target_file_path}
