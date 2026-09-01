# No automated test verifies required-component Fail-Fast, non-required-component partial availability, or undefined-criticality handling

## Priority
Medium

## Summary
`docs/adr/ADR-004-environment-failure-handling-policy.md` defines INV-08/INV-09 (required-component
unavailability aborts startup; non-required-component availability failure permits continuation
with partial availability) and INV-14 (undefined criticality must not permit continuation) — listed
as INV-019/INV-020/INV-021 in `docs/adr-index.md`'s cross-ADR matrix. None of these currently has a
dedicated automated test, confirmed by searching the test suite during the 2026-08-31 ADR-004
rewrite.

## Background
ADR-004's own Verification section and `docs/adr-index.md`'s Invariant Verification Matrix both
mark these three invariants "Not verified" / "Not implemented" as of the 2026-08-31 rewrite. This
issue tracks closing that gap, separately from the config-model implementation work tracked in
`issues/20260831-192510_adr004_05_mcp_config_alignment_superseded_by_policy_reversal.md` and the
Specification-classification work tracked in
`issues/20260831-192510_adr004_06_missing_component_criticality_specification.md`.

## Problem
(Evidence: Explicit in code — confirmed by search, not by exhaustive test-suite enumeration)
`grep`-ing the test suite for `is_required`, `required_in_local`, `required_in_production` found
no test in `tests/agent/` that exercises the classification branch in
`scripts/agent/services/mcp_tool_discovery.py::discover_all()`. The only related evidence found is
`tests/agent/shared/test_startup_validation_pipeline.py`'s generic FATAL/WARNING aggregation tests
(`test_single_fatal_readiness_raises`, `test_warnings_only_no_raise`), which verify the pipeline's
general mechanism (one FATAL aborts; warnings-only does not) but not the MCP-discovery-specific
required/non-required scenario. Undefined-criticality handling (INV-021) has no implementation to
test against at all today, since `required_in_production`/`required_in_local` are booleans
defaulting to `True` with no distinct "undefined" state.

## Reason for Change
Without dedicated tests, a future change to `mcp_tool_discovery.py`'s classification branch (or to
`McpServerConfig`) could silently violate ADR-004's required-component Fail-Fast guarantee or its
non-required-component partial-availability guarantee, and no CI signal would catch it.

## Implementation Intent
Add tests exercising `McpToolDiscoveryService.discover_all()`'s classification branch directly:
one scenario where an unreachable component is classified required (expect FATAL/startup abort),
one where it is classified non-required due to an availability failure (expect WARNING, component
disabled, continuation permitted), and confirm that only a genuine availability failure — not a
safety/integrity failure — can reach the non-required/continuation path. Sequence this after
`issues/20260831-192510_adr004_05_mcp_config_alignment_superseded_by_policy_reversal.md` lands,
since that issue changes the classification field shape these tests would target; writing tests
against the current `required_in_production`/`required_in_local`/`security_profile` model would
need rewriting once that issue's environment-independent classification lands.

## Target Files or Areas
- `tests/agent/services/` (or wherever `McpToolDiscoveryService` tests currently live — exact
  location needs confirmation) — new tests for the classification branch
- `scripts/agent/services/mcp_tool_discovery.py` — read-only reference; not expected to change as
  part of this issue alone (see dependency on `adr004_05`)

## Required Changes
- Add a test: an unreachable, required-classified component causes `discover_all()` to surface a
  FATAL finding (startup abort).
- Add a test: an unreachable, non-required-classified component causes a WARNING finding, is
  excluded from the resulting `RuntimeToolRegistry` (tools not LLM-visible/executable), and does
  not abort startup.
- Add a test (once the environment-independent classification from `adr004_05` lands) confirming
  classification does not depend on `security_profile`.
- If an "undefined criticality" state is introduced as part of `adr004_05`, add a test confirming
  it does not permit startup continuation (INV-021 / INV-014 in the ADR body).

## Constraints
- Do not write these tests against the current `security_profile`-conditional classification
  model if `adr004_05` is expected to land first — coordinate sequencing to avoid throwaway work.
- Do not claim these tests exist or pass in any ADR or index document until they are actually
  written and run.

## Acceptance Criteria
- Dedicated tests exist and pass for: required-component Fail-Fast, non-required-component
  partial-availability continuation, and (once implemented) undefined-criticality rejection.
- `docs/adr/ADR-004-environment-failure-handling-policy.md`'s Verification section and
  `docs/adr-index.md`'s INV-019/INV-020/INV-021 rows are updated to cite the new tests once they
  exist, replacing the current "Not verified"/"Not implemented" status.

## Testing Expectations
Run the new tests plus the full `tests/agent/` suite once added; apply the standard validation
sequence in `rules/toolchain.md`.

## Documentation Impact
Update ADR-004's Verification section and the corresponding `docs/adr-index.md` rows once these
tests exist, per each document's own instruction to cite real evidence.

## Out of Scope
- Changing `McpServerConfig`'s field shape (tracked in `adr004_05`).
- Defining which components are required/non-required (tracked in `adr004_06`).

## Dependencies
Depends on `issues/20260831-192510_adr004_05_mcp_config_alignment_superseded_by_policy_reversal.md`
for the classification model these tests should target. Follows the 2026-08-31 ADR-004 rewrite.

## Unresolved Questions
Exact current location of `McpToolDiscoveryService`'s test file, if one already exists partially
covering adjacent behavior — needs confirmation before adding new test files to avoid duplication.

## AI Implementation Instruction
Confirm whether `adr004_05` has landed before writing tests against a specific field shape; if not
landed, either wait or write tests against the current model and flag them for rework. Do not
mark any ADR-004 invariant as verified without an actually passing test.
