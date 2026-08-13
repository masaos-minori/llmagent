# `ToolTransportInvoker` does not disable the call timeout when `call_timeout_sec=0`, contradicting its own documented intent

## Priority
Medium

## Summary
`scripts/shared/tool_transport_invoker.py`'s `__init__` reads `cfg.call_timeout_sec` with a
`hasattr` defensive check and a truthy fallback; because `McpServerConfig.call_timeout_sec` is
always present (dataclass field, default `60.0`), the `hasattr` check is dead code. Separately,
an inline comment indicates `call_timeout_sec == 0` is intended to mean "no timeout," but a
falsy check causes it to silently fall back to the default `60.0` instead.

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/tool_transport_invoker.py`
(2026-08-13). Not fixed in that cycle because it is a behavior change, out of scope for a
zero-behavior-change refactor (Evidence label: Explicit in code — the dead `hasattr` check and
the truthy-vs-falsy mismatch are both directly visible in the source).

## Implementation Intent
Decide and implement the intended contract for `call_timeout_sec=0`:
- If "0 means no timeout" is the intended contract (per the existing comment), fix the check to
  distinguish "field absent" from "field is 0" (e.g. use `is None` semantics or an explicit
  sentinel) rather than a bare truthy check.
- If "0 means no timeout" is not actually a supported use case, remove the misleading comment
  and the dead `hasattr` check, documenting that `call_timeout_sec` always uses the configured
  value with `60.0` as the default only when unset.

## Target Files or Areas
- `scripts/shared/tool_transport_invoker.py` (`ToolTransportInvoker.__init__`)
- `config/agent.toml` (if `call_timeout_sec: 0` is or should be a documented supported value)

## Required Changes
- Remove or fix the dead `hasattr(cfg, "call_timeout_sec")` check.
- Fix the 0-means-no-timeout handling if that is the intended contract, or update the comment
  and remove the dead branch if it is not.
- Add a characterization test asserting the chosen `call_timeout_sec=0` behavior explicitly.

## Acceptance Criteria
- `call_timeout_sec=0` behaves according to one explicit, tested, documented contract (either
  "means no timeout" or "0 is rejected/treated as default" — not silently ignored).
- No dead `hasattr` branch remains.

## Testing Expectations
Unit test(s) in `tests/shared/test_tool_transport_invoker.py` asserting the resolved timeout
value for `call_timeout_sec=0`, a positive value, and the default-when-unset case.

## Documentation Impact
If `call_timeout_sec: 0` becomes a supported "disable timeout" value, document it in
`docs/` wherever `config/agent.toml`'s per-server config keys are documented.

## Out of Scope
- Do not change any other timeout/retry/health-check logic in this class.
- Do not touch `HttpTransport`'s own timeout handling (`scripts/shared/http_transport.py`).

## AI Implementation Instruction
Read `scripts/shared/tool_transport_invoker.py::ToolTransportInvoker.__init__` and
`McpServerConfig.call_timeout_sec`'s definition/default in `scripts/shared/mcp_config.py`
before changing anything. Confirm via `rg "call_timeout_sec"` across `scripts/` and `config/`
whether any existing config file or caller sets it to `0` before choosing the "no timeout"
interpretation. Add a test locking the current (buggy or fixed) behavior before touching the
code, per this project's refactor discipline.
