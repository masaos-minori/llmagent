# Close remaining ConfigLoader/MCPServer fail-closed gaps (REQ-003 through REQ-006 of H-02)

## Priority
High

## Summary
`issues/done/20260902-101452_h02_config_loader_fail_closed_gap.md` requested six fixes
(REQ-001 through REQ-006) for `ConfigLoader`'s fail-closed guarantee. Its resulting plan
(`plans/done/20260902-191443_plan.md`) generated 13 implementation procedure documents
(`implementations/done/20260902-220059_01` through `_13`), and every one of them is scoped to
REQ-001 and/or REQ-002 only (confirmed by direct read of each document's Traceability >
Requirement ID field) — none target REQ-003, REQ-004, REQ-005, or REQ-006. Direct reads of the
current code and docs confirm REQ-001/REQ-002 are correctly implemented, but REQ-003 through
REQ-006 were never implemented at all; no implementation procedure was ever generated for them.

## Background
`Explicit in code`: `scripts/shared/config_loader.py`'s `load_all()` already defaults to
`strict=True` (REQ-001), and `scripts/agent/config_builders.py`'s `security_profile` resolution
no longer has the `None`-fallback ambiguity (REQ-002) — both confirmed present in the current
source. `plans/done/20260902-191443_plan.md`'s own `## Execution Status` table (checked
directly) still reads a single placeholder row, `Status: Pending`, never updated to reflect
even the REQ-001/002 work that did land — this Plan's own bookkeeping does not distinguish
"done" from "not done" per requirement, which is why REQ-003–006's absence was not visible from
the Plan or its archived implementation procedures alone; it required reading each procedure's
Traceability block individually.

## Problem
- `scripts/mcp_servers/server.py::MCPServer.run_http()` still guards `restrict_to()` with a bare
  `if self.own_config_file:` (no `else`/fail-closed branch) — a falsy `own_config_file` silently
  skips Config Isolation restriction (REQ-003 unmet).
- `scripts/shared/production_config_validator.py` has no general unknown-top-level-key rejection
  — only the narrower `tool_safety_tiers`-specific bidirectional check
  (`_check_missing_tool_safety_tiers`/`_check_unknown_tool_safety_tiers`) exists (REQ-004 unmet).
- `docs/adr/ADR-002-config-isolation.md` has no per-process required-file/required-key/
  empty-allowed-key table (REQ-005 unmet; confirmed absent by direct read).
- `docs/adr/ADR-004-environment-failure-handling-policy.md`'s INV-07 row still reads "Needs
  confirmation" (REQ-006 unmet; confirmed by direct read at the row citing INV-06/INV-07).

## Reason for Change
These are the same security-relevant fail-closed gaps the original H-02 issue identified:
Config Isolation can still be silently bypassed by a falsy `own_config_file`, no config loader
rejects unknown/mistyped top-level keys, and two ADRs' own Verification sections still record
"Needs confirmation"/missing documentation for exactly this scenario class. REQ-001/002 landing
does not close these remaining gaps — they require independent implementation work that the
original Plan never generated procedures for.

## Implementation Intent
Carry forward REQ-003 through REQ-006 exactly as specified in
`issues/done/20260902-101452_h02_config_loader_fail_closed_gap.md`'s Implementation Intent and
Required Changes sections — this issue does not redesign that scope, it re-files the portion of
it that was never actioned. Treat REQ-001/REQ-002 as already satisfied and out of scope here.

## Target Files or Areas
- `scripts/mcp_servers/server.py` (`MCPServer.run_http()`'s falsy `own_config_file` skip)
- `scripts/shared/production_config_validator.py` (unknown-top-level-key rejection, derived from
  `scripts/agent/config_dataclasses.py` via introspection)
- `docs/adr/ADR-002-config-isolation.md` (per-process required-file/required-key table;
  Verification section INV-01/INV-02 update)
- `docs/adr/ADR-004-environment-failure-handling-policy.md` (Verification section INV-07 status
  update)
- `tests/shared/test_config_loader.py`, `tests/agent/test_startup.py`,
  `tests/agent/shared/test_startup_validation_pipeline.py`,
  `tests/agent/test_config_permission_cross_server.py` (new startup-scenario tests for the above)

## Required Changes
- Fix `MCPServer.run_http()` to fail closed (raise, not silently skip) when `own_config_file` is
  falsy.
- Add unknown-top-level-key rejection for production config loading, with valid keys derived
  from `scripts/agent/config_dataclasses.py` via introspection (`dataclasses.fields()`).
- Add a per-process required-file/required-key/empty-allowed-key table as a new section in
  `docs/adr/ADR-002-config-isolation.md`.
- Add startup tests for the falsy-`own_config_file` case and for unknown-key rejection, mapped
  to `ADR-004`'s INV-07 and `ADR-002`'s INV-01/INV-02.
- Update both ADRs' Verification sections' `Status` fields from "Needs confirmation" to
  "Confirmed", citing the new tests by name.

## Constraints
- Do not modify anything already satisfied by REQ-001/REQ-002 — `load_all()`'s strict default
  and `config_builders.py`'s `security_profile` resolution are out of scope here.
- Per `ADR-004` INV-01/INV-02, any fix must apply identically across all environments (no
  environment-based branching).
- Do not weaken `ProductionConfigValidator`'s existing checks; only add the new unknown-key
  check alongside them.

## Acceptance Criteria
- [ ] `MCPServer.run_http()` with a falsy `own_config_file` fails at startup instead of running
      unrestricted.
- [ ] At least one new test asserts an unknown/mistyped top-level config key (not among
      `agent/config_dataclasses.py`'s introspected fields) is rejected in production.
- [ ] A per-process required-file/required-key/empty-allowed-key table exists as a new section
      in `docs/adr/ADR-002-config-isolation.md`.
- [ ] `docs/adr/ADR-004-environment-failure-handling-policy.md`'s INV-07 row and
      `docs/adr/ADR-002-config-isolation.md`'s INV-01/INV-02 rows cite the new tests and no
      longer read "Needs confirmation" for the scenarios this issue's tests cover.
- [ ] `uv run pytest tests/shared/test_config_loader.py tests/agent/test_startup.py
      tests/agent/shared/test_startup_validation_pipeline.py
      tests/agent/test_config_permission_cross_server.py -q` passes.

## Testing Expectations
New unit/integration tests for the falsy-`own_config_file` fail-closed path and unknown-key
rejection, plus a regression run of the existing suites listed in Target Files or Areas.

## Documentation Impact
Yes: `docs/adr/ADR-002-config-isolation.md` gains a new required-file/required-key table section
and its Verification section updates; `docs/adr/ADR-004-environment-failure-handling-policy.md`'s
Verification section's INV-07 row updates once the new tests land.

## Out of Scope
- REQ-001 (`load_all()` strict default) and REQ-002 (`security_profile` resolution order) —
  already implemented; do not re-touch.
- `scripts/eventbus/config.py` — does not use `ConfigLoader`, already tracked separately
  (`ADR-002` Known Deviation `CI-001`).
- Any change to `ProductionConfigValidator`'s existing `tool_safety_tiers`/`approval_risk_rules`
  check logic — only the new unknown-key check is in scope.

## Dependencies
Supersedes the REQ-003–REQ-006 portion of
`issues/done/20260902-101452_h02_config_loader_fail_closed_gap.md` (that issue's REQ-001/REQ-002
portion is already implemented and not reopened by this issue).

## Unresolved Questions
N/A: none — REQ-003 through REQ-006's scope, source-of-truth decisions (introspection-based key
validation, ADR-002 as the documentation target), and acceptance criteria are already fully
specified in the original H-02 issue; this issue only re-files the unactioned portion.

## AI Implementation Instruction
Before editing `scripts/mcp_servers/server.py` or `scripts/shared/production_config_validator.py`,
re-read both files in full and re-confirm current behavior via `grep -n "own_config_file"
scripts/mcp_servers/server.py`, since this issue's evidence may go stale if either file changes
before implementation. Do not re-implement or re-verify REQ-001/REQ-002 — treat them as already
done. If the TOML-key-to-dataclass-field mapping proves ambiguous for a given key, stop and
report it rather than guessing.
