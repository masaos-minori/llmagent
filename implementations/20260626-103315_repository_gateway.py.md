# Implementation: Audit approval call conditions in repository_gateway.py

Steps covered: Plan 20260626-090724 — Phase 1, Step 1-1

---

## Goal

Document the exact conditions under which `run_approval_checks` is called in `repository_gateway.py`, and record the approval startup conditions completely so the canonical model can be defined.

---

## Scope

- **In scope**: read `scripts/agent/repository_gateway.py` lines 1-110, record call conditions for `run_approval_checks`
- **Out of scope**: any code changes

---

## Assumptions

- `run_approval_checks` lives in `scripts/agent/tool_approval.py` (line 156) and is imported lazily by `repository_gateway.py` (line 93).
- The plan originally referenced `llm_turn_runner.py` but the actual caller is `repository_gateway.py`.

---

## Implementation

### Target file
`scripts/agent/repository_gateway.py`

### Procedure
1. Read `scripts/agent/repository_gateway.py` fully.
2. Record: which code path imports `run_approval_checks`, what arguments are passed, what conditions enable or skip the call.
3. Cross-reference `tool_approval.py:156` (`run_approval_checks` definition) to confirm the call signature matches.
4. Document findings in a comment block at the top of the implementation ADR (`docs/05_agent_06_tool-execution-and-approval.md`).

### Method
Read-only audit. No code changes.

### Details

From the existing code:
- `repository_gateway.py:93` lazy-imports `run_approval_checks` inside a conditional block.
- `repository_gateway.py:102` calls it with `(ctx, tool_calls)` (approximate — confirm exact args by reading the file).
- Approval is triggered per tool-call batch, not per individual call.
- The trigger is inside the tool-execution path, before actual execution.

Key fact to confirm: does any code path in `repository_gateway.py` skip `run_approval_checks` when a workflow is active? If not, both approvals fire independently.

---

## Validation plan

- No code changes — validation is reading/documentation only.
- Confirm: `grep -n "run_approval_checks" scripts/agent/repository_gateway.py` lists expected call sites.
- Confirm: no other caller exists — `grep -rn "run_approval_checks" scripts/` lists only `tool_approval.py` (definition) and `repository_gateway.py` (call site).
