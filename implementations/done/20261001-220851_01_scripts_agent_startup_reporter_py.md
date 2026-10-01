## Goal

Replace the substring-based `"unreachable" in o.message.lower()` computation of
`unreachable_count` in `ReadinessReporter.report_readiness()` with the structured
`runtime_tools.unavailable_servers` set, eliminating display logic coupling to exact
message wording (REQ-001; AC-01).

## Scope

Move `unavailable_servers` computation earlier in `report_readiness()` (before line 94)
and replace the substring match with `len(unavailable_servers)`; keep the emitted
"Unreachable servers: N" line stable in format.

## Assumptions

- `self._ctx.services_required.runtime_tools` is populated before
  `report_readiness()` is called (confirmed by `discover_all()` being called prior to
  reporting).
- `runtime_tools.unavailable_servers` contains the same set of server keys as what the
  substring match would have identified.
- The `unavailable_servers` frozenset is always defined (even if empty) so it can be
  safely referenced.

## Design decisions

- Prefer the structured `discovery.unreachable` / `runtime_tools.unavailable_servers`
  data (already used elsewhere in the same method) over substring scanning.
- Move the `unavailable_servers` assignment earlier in the method body so it is
  available when computing `unreachable_count`.
- Keep the "Unreachable servers: N" output line format unchanged.

## Alternatives considered

- Keep the substring match and add a comment noting its fragility: rejected — defeats
  the purpose of REQ-001 (eliminate message-text coupling).
- Replace only the count but leave `unavailable_servers` where it is (after the
  unreachable_count block): rejected — requires duplicating the assignment or passing
  it via a local variable, which is less clear than moving it up.

## Implementation

### Target file

`scripts/agent/startup_reporter.py`

### Procedure

1. Verify `report_readiness()` is called after `discover_all()` completes.
2. Read the surrounding code to confirm the exact insertion point for
   `unavailable_servers` computation.
3. Move `unavailable_servers` computation to before the `unreachable_count` block.
4. Replace the substring match with `len(unavailable_servers)`.
5. Confirm the "Unreachable servers: N" line format is preserved.

### Method

Edit `scripts/agent/startup_reporter.py` in-place.

### Details

**Phase 1: Preparation / Verification**

1. Verify `report_readiness()` is called after `discover_all()` completes:
   ```bash
   rg -n "discover_all\(\)|report_readiness\(" scripts/agent/startup.py
   ```
   Expected: `discover_all()` is called before `report_readiness()` in the caller.

2. Read the current `report_readiness()` method body to confirm the exact insertion
   point for `unavailable_servers` computation.

**Phase 2: Core Logic Implementation**

Replace the `unreachable_count` computation (lines 94-97) and move
`unavailable_servers` earlier:

```python
# Before (lines 94-97):
unreachable_count = sum(
    1
    for o in pipeline.outcomes
    if o.source == "mcp_tool_discovery" and "unreachable" in o.message.lower()
)

# After:
unavailable_servers: frozenset[str] = frozenset()
runtime_tools = (
    self._ctx.services_required.runtime_tools
    if self._ctx.services_required
    else None
)
if runtime_tools is not None:
    unavailable_servers = runtime_tools.unavailable_servers
unreachable_count = len(unavailable_servers)
```

Then remove the later `unavailable_servers` assignment (currently lines 115-125) since
it will now be done above.

**Phase 3: Deployment & Verification**

1. Run `ruff` on `scripts/agent/startup_reporter.py`:
   ```bash
   uv run ruff format scripts/agent/startup_reporter.py && uv run ruff check scripts/agent/startup_reporter.py
   ```
2. Run `mypy` on `scripts/agent/startup_reporter.py`:
   ```bash
   uv run mypy scripts/agent/startup_reporter.py
   ```
3. Run existing tests to confirm no regression:
   ```bash
   uv run pytest tests/agent/test_startup.py -v --tb=short
   ```

## Compatibility considerations

- The "Unreachable servers: N" line format must remain identical to avoid downstream
  parsing breakage.
- If `runtime_tools` is `None`, `unavailable_servers` defaults to `frozenset()`,
  yielding `unreachable_count = 0` — equivalent to the previous behavior when no
  outcomes contained "unreachable".

## Security considerations

N/A: display-only change; no security-sensitive surface.

## Rollback considerations

Restore the original substring-match `unreachable_count` computation and revert the
`unavailable_servers` placement to its original position.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_reporter.py` | Lint check | `uv run ruff format scripts/agent/startup_reporter.py` then `uv run ruff check scripts/agent/startup_reporter.py` | Clean (no errors) |
| `scripts/agent/startup_reporter.py` | Type check | `uv run mypy scripts/agent/startup_reporter.py` | Clean (no type errors) |
| `tests/agent/test_startup.py` | Regression test | `uv run pytest tests/agent/test_startup.py -v --tb=short` | All tests pass |

## Completion criteria

- `unreachable_count` is derived from `len(unavailable_servers)` instead of substring
  matching on `o.message.lower()`.
- The "Unreachable servers: N" line format is preserved.
- No other reported lines or readiness semantics changed.
- `ruff` and `mypy` clean on the modified file.

## Out of scope

Any change to the tool-discovery service or its messages; changes to other reported
lines or readiness semantics.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-001, REQ-002, REQ-003 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no new tests required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | REQ-004 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no doc change required |

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
- **Requirement ID**: REQ-001 — replace the substring match with the structured
  `unavailable_servers` set for computing the unreachable count
- **Source issue**: issues/20260930-161945_rep001_readiness_summary_unreachable_count_message_string_coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-103920_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-220851
- **Related target files**: scripts/agent/startup_reporter.py
