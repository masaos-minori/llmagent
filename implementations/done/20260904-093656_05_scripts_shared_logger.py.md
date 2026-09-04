## Goal
Add `auth_token`/Bearer-token-value redaction to log output, so a token
value never appears in plaintext in logs, diagnostics, exceptions, or
configuration previews.

## Scope
- **In-Scope**: adding a redaction mechanism to this file's logging
  pipeline — a new filter applied via `_configure_logger()` (verified
  2026-09-04, lines 118-140), plus a small registration API for callers
  that resolve secret values (rows 1, 3) to register them for redaction.
- **Out-of-Scope**: `_ContextFilter` (lines 37-61), `_JsonFormatter` (lines
  64-84)'s existing field structure, `Logger.set_context()`/`clear_context()`
  (lines 106-112) — confirmed by direct read to be unrelated trace-context
  concerns; this row adds a new, separate filter, not a modification to
  these.

## Assumptions
- Per the Plan's own Risk: "REQ-004's redaction targets the specific
  `auth_token` value and `Authorization: Bearer <token>` header pattern, not
  a generic keyword-based filter" — this row implements two complementary
  mechanisms: (a) a pattern-based scrub of `Bearer <token>`-shaped header
  values (catches the header case without needing to know the actual token
  value), and (b) a value-registry scrub of specific known secret values
  (catches a bare token value logged outside the header context, e.g. in an
  exception message or config-preview dump).
- Coupled to row 1 (`scripts/shared/mcp_config.py`) — once row 1 resolves an
  `auth_token` value (from environment or TOML literal), that value must be
  registered with this row's redaction mechanism so it is scrubbed wherever
  logged thereafter.

## Design decisions
- Add a module-level `_SECRET_VALUES: set[str]` registry and a
  `register_secret(value: str) -> None` function that callers add resolved
  token values to (a no-op for an empty string, since an empty token is
  never itself sensitive and rows 1/3 reject it anyway).
- Add a `_RedactionFilter(logging.Filter)` class, applied to every `Logger`
  instance's underlying stdlib logger alongside the existing `_ContextFilter`
  (in `_configure_logger()`), that:
  1. Replaces any `Bearer\s+\S+` occurrence in `record.getMessage()`'s
     rendered text with `Bearer ***REDACTED***` (pattern-based, header
     case).
  2. Replaces any exact-match occurrence of a registered secret value in the
     rendered text with `***REDACTED***` (registry-based, bare-value case).
  Since `logging.Filter.filter()` cannot rewrite `record.msg` after
  formatting has already captured positional `%`-args into the message text
  in all cases, apply the substitution by overwriting `record.msg` with the
  already-`%`-formatted, redacted string and clearing `record.args` to
  `()`, so downstream formatters (`_JsonFormatter`, the plain
  `logging.Formatter`) both see the redacted text — re-confirm this
  approach against Python's `logging` internals at execution time (the
  `record.getMessage()` call inside the filter must happen before `record.args`
  is cleared).

## Alternatives considered
- Redacting only at the `_JsonFormatter`/plain-formatter level (post-filter):
  rejected — a filter applied once, shared by all `Logger` instances via
  `_configure_logger()`, is simpler than duplicating the redaction logic in
  both formatter classes, and correctly applies before either formatter
  renders the final text.
- A purely keyword-based filter matching generic terms like "token",
  "secret", "password": rejected per the Plan's own Risk section — too
  broad, risks masking legitimate non-secret fields whose names merely
  contain those substrings.

## Implementation
### Target file
`scripts/shared/logger.py`

### Procedure
1. Add `import re` and a module-level `_BEARER_RE = re.compile(r"Bearer\s+\S+")`.
2. Add `_SECRET_VALUES: set[str] = set()` and
   `def register_secret(value: str) -> None: ...` (guarding against
   registering an empty string).
3. Add `class _RedactionFilter(logging.Filter):` with a `filter()` method
   implementing the two-step substitution described in Design decisions.
4. In `_configure_logger()` (lines 118-140), add
   `self._logger.addFilter(_RedactionFilter())` alongside the existing
   `self._logger.addFilter(self._filter)` (line 120).

### Method
Direct `Edit`/new-code addition at the sites above.

### Details
Illustrative implementation:
```python
import re

_BEARER_RE = re.compile(r"Bearer\s+\S+")
_SECRET_VALUES: set[str] = set()


def register_secret(value: str) -> None:
    """Register a secret value (e.g. an auth_token) for log redaction."""
    if value:
        _SECRET_VALUES.add(value)


class _RedactionFilter(logging.Filter):
    """Redacts Bearer-token headers and registered secret values from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        text = record.getMessage()
        text = _BEARER_RE.sub("Bearer ***REDACTED***", text)
        for secret in _SECRET_VALUES:
            text = text.replace(secret, "***REDACTED***")
        record.msg = text
        record.args = ()
        return True
```
In `_configure_logger()`:
```python
self._logger.addFilter(self._filter)
self._logger.addFilter(_RedactionFilter())
```

## Compatibility considerations
Coupled to row 1 — token values must be registered via `register_secret()`
at the point they are resolved (row 1's `resolve_env_ref()` call site, or
`McpServerConfig.__post_init__`) for the value-registry half of this row's
redaction to take effect; the pattern-based `Bearer` redaction works
independently of registration.

## Security considerations
This row is the core enforcement of REQ-004/AC-4 (token values absent from
logs, diagnostics, exceptions, configuration previews).

## Rollback considerations
Additive filter/registry under version control; revert via `git revert` if
needed, together with row 1's registration call site.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/logger.py` | Unit | New log-capture test (REQ-007; `caplog`-based, added to a test file at the implementer's discretion since no dedicated test file is confirmed for this module) | A log message containing `Bearer <token>` or a registered secret value never appears in plaintext in captured output; unrelated log fields are unaffected |

## Completion criteria
Logging a message containing a `Bearer <token>` header or a registered
secret value produces redacted output; no unrelated field is masked.

## Out of scope
`_ContextFilter`, `_JsonFormatter`'s field structure, `set_context()`/
`clear_context()`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Added `register_secret()`/`_RedactionFilter`; wired into `_configure_logger()` alongside `_ContextFilter`. Row 1's `_build_single_server()` calls `register_secret()` on every resolved `auth_token` |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | `tests/integration/test_production_security_regression.py::test_mcp_auth_token_redacted_in_logs` — removed its `xfail` marker and rewrote to call `register_secret()` directly, asserting both the `Bearer <token>` pattern match and the exact-value registry match are redacted |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff/mypy clean; also functionally verified via a standalone script |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260904 | 20260904 | `docs/00_index.md`'s "Config / logger / formatters / rag_utils" row maps to `90_shared_03_01_runtime_and_execution-config-and-logging.md` — added a "Secret redaction" bullet under `Logger` |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260902-143335_mcpauth_preserve_mandatory_mcp_authentication_under_loopback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-092407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-093656
- **Related target files**: scripts/shared/logger.py
