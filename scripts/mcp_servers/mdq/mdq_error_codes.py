#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/mdq_error_codes.py — Closed MDQ domain error-code vocabulary and exception mapping.

Closed MDQ domain error-code vocabulary plus the mapping from the MDQ exception
classes to codes (REQ-004).

Policy only: no I/O, no logging, and no transport status mapping. The transport
rendering is owned by `mdq_server.py`; the documented transport policy is that a
tool-domain failure returns HTTP 200 with `is_error=true` and the code. Retry
guidance lives in `docs/22_mcp/mcp_03_03_transport-and-health.md`.

`CONTROL_ERROR_CODES` in `scripts/shared/mcp_call_state_contract.py` is closed to
the control API and cannot carry domain codes, so this vocabulary stays here.

Dependency direction: mdq_error_codes → models
Import from here:  from mcp_servers.mdq.mdq_error_codes import MDQ_DOMAIN_ERROR_CODES, code_for_exception
"""

from __future__ import annotations

from mcp_servers.mdq.mdq_models import (
    MdqAuthorizationError,
    MdqConsistencyError,
    MdqDatabaseError,
    MdqIndexNotReadyError,
    MdqNotFoundError,
    MdqServiceError,
    MdqValidationError,
)

# Closed lowercase-snake vocabulary (REQ-004). `timeout` is defined here and its
# behavior lands in plan mdqmcp002; `tool_disabled` is the code the dispatch
# boundary uses for a refusal before the handler.
MDQ_DOMAIN_ERROR_CODES = frozenset(
    {
        "validation_error",
        "authorization_error",
        "tool_disabled",
        "not_found",
        "database_unavailable",
        "consistency_error",
        "timeout",
        "unexpected_error",
    }
)

UNEXPECTED_ERROR = "unexpected_error"
TOOL_DISABLED = "tool_disabled"

# Keyed by the MDQ exception classes, most specific first and `MdqServiceError`
# last so the mapping resolves a subclass before its base. `tool_disabled` and
# `timeout` have no exception class: they are produced by the dispatch boundary
# and by the search path respectively.
EXCEPTION_ERROR_CODES: dict[type[Exception], str] = {
    MdqValidationError: "validation_error",
    MdqAuthorizationError: "authorization_error",
    MdqNotFoundError: "not_found",
    MdqIndexNotReadyError: "database_unavailable",
    MdqDatabaseError: "database_unavailable",
    MdqConsistencyError: "consistency_error",
    MdqServiceError: UNEXPECTED_ERROR,
}


def code_for_exception(exc: BaseException) -> str:
    """Return the closed-vocabulary code for an MDQ exception.

    The returned code never carries exception text, SQLite detail, or a path
    (AC-5); an exception outside the MDQ classes resolves to `unexpected_error`.
    """
    for error_class, code in EXCEPTION_ERROR_CODES.items():
        if isinstance(exc, error_class):
            return code
    return UNEXPECTED_ERROR
