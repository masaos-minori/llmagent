# ToolLoopGuard unavailable-repeat and empty-result guards share one config knob

## Priority
Medium

## Summary
`ToolLoopGuard` gates two semantically distinct per-turn guards — empty-result repeat detection and server-unavailability repeat detection — on the same configuration value, `tool_empty_result_max_repeats`. There is no independent control: enabling empty-result detection automatically enables the unavailable-repeat guard, and vice versa. Give each guard its own threshold so operators can enable exactly one.

## Background
`scripts/agent/tool_loop_guard.py` implements several per-turn guards. Two of them count repeats and fire a guard hint when a threshold is reached:

- Empty-result repeat guard: `record_tool_result` / `scan_empty_result_repeat` / `check_empty_result_repeat` (lines ~214-252). Reads `ctx.cfg.tool.tool_empty_result_max_repeats`.
- Unavailable-repeat guard: `observe_availability` / `scan_unavailable_repeat` / `check_unavailable_repeat` (lines ~256-304). Also reads `ctx.cfg.tool.tool_empty_result_max_repeats`.

Both thresholds default to `0` (disabled) per `config_dataclasses.py`:
```python
# Max consecutive empty tool results within a turn; > 0 enables
# empty-result repeat detection, <= 0 disables it. Default 0 (disabled).
tool_empty_result_max_repeats: int = 0
```

`scan_unavailable_repeat` explicitly reuses the empty-result bound:
```python
def scan_unavailable_repeat(self) -> tuple[str, int] | None:
    limit = self._ctx.cfg.tool.tool_empty_result_max_repeats
    if limit <= 0:
        return None
    return next(((k, c) for k, c in self._unavailable_counts.items() if c >= limit), None)
```

`check_unavailable_repeat` documents this reuse:
```python
"""Reuses the empty-result repeat bound (``tool_empty_result_max_repeats``);
limit <= 0 disables the check entirely (default-off)."""
```

A prior item, `issues/done/20261017-123510_retrysup01_make-retry-suppression-and-empty-result-defaults-observable.md`, made retry-suppression and empty-result defaults observable (startup log/warn) but did not address this coupling.

## Problem
The two guards detect different failure modes:
- Empty-result: a tool repeatedly returns an empty value (`None`, `""`, empty dict/list).
- Unavailable: an MCP server repeatedly reports unavailability via the `availability_hint` channel.

Yet both read the single knob `tool_empty_result_max_repeats`. Consequences:
- **No independent toggling.** An operator who wants empty-result detection ON cannot leave unavailable-repeat detection OFF; setting the knob above 0 flips both on together.
- **Shared default-off.** Both are off by default, so neither fires until the knob is set — but setting it activates a guard the operator may never have intended to touch.
- **Threshold conflation.** The two guards have different natural cadences (a tool returning empty vs. a server flapping). Forcing them to share one threshold means the value that is safe for one may be wrong for the other, with no way to diverge.
- **Silent activation.** Unlike retry/empty-result guards, the unavailable-repeat guard surfaces no enabled/disabled signal, so the operator is unaware that turning on empty-result detection also armed unavailable-repeat detection.

## Reason for Change
The coupling makes the effective behavior of a single config value ambiguous and prevents operators from scoping the unavailable-repeat guard independently. Decoupling restores one-threshold-per-guard semantics.

## Implementation Intent
Introduce a dedicated threshold for the unavailable-repeat guard (e.g. `tool_unavailable_repeat_max_repeats`) in `config_dataclasses.py`, wire it through the config section builder, and point `scan_unavailable_repeat` / `check_unavailable_repeat` at it. Keep `tool_empty_result_max_repeats` as the sole input for the empty-result guard. Preserve backward compatibility: default the new knob to `0` (disabled) so existing deployments see no behavior change, and keep the `<= 0` disables-check semantics.

## Target Files or Areas
- `scripts/agent/config_dataclasses.py` (add the new field)
- `scripts/agent/config_section_builders.py` (wire the new field)
- `scripts/agent/tool_loop_guard.py` (`scan_unavailable_repeat`, `check_unavailable_repeat`)
- Config schema / validation if knobs are registered there
- Tests covering independent on/off for each guard

## Required Changes
- Add a new integer config field for the unavailable-repeat threshold, defaulting to `0` (disabled).
- Wire the new field through the config section builder alongside `tool_empty_result_max_repeats`.
- Point `scan_unavailable_repeat` and `check_unavailable_repeat` at the new field instead of `tool_empty_result_max_repeats`.
- Add tests proving the two guards toggle independently (empty-result ON while unavailable-repeat OFF, and vice versa).
- Update any config documentation describing these knobs.

## Constraints
- Must preserve backward compatibility: the new knob defaults to `0` (disabled) so existing deployments are unaffected.
- Must not change the empty-result guard's existing knob name or semantics.
- Must keep the `<= 0` disables-check contract for the new guard.
- Must not alter the public config dataclass surface in a way that breaks existing serialized configs (additive-only).

## Acceptance Criteria
- `tool_empty_result_max_repeats` still controls only the empty-result guard.
- A new knob controls only the unavailable-repeat guard.
- Setting the empty-result knob above 0 leaves the unavailable-repeat guard off unless its own knob is also > 0.
- Setting the unavailable-repeat knob above 0 leaves the empty-result guard off unless its own knob is also > 0.
- Existing deployments with only `tool_empty_result_max_repeats` configured show no behavior change.

## Testing Expectations
Unit tests for independent toggling of both guards, the default-off behavior of the new knob, and a regression sweep confirming the empty-result guard still honors `tool_empty_result_max_repeats`. Confirm any pinned pattern/config-count assertions are updated.

## Documentation Impact
Document the two independent knobs and their separate semantics in the operator-facing config reference, noting the additive default-off behavior of the new unavailable-repeat knob.

## Out of Scope
- Changing the empty-result guard's threshold name, default, or disable semantics.
- Redesigning the availability-hint channel or how `_unavailable_counts` accumulates.
- Changing retry-suppression or dedup guards.

## Dependencies
N/A: none

## Unresolved Questions
- Should the new knob reuse the empty-result guard's startup-observability treatment once decoupled? Needs confirmation whether to surface its enabled/disabled state too.
- Is there an existing serialized-config version bump required for the additive field? Needs confirmation.

## AI Implementation Instruction
Additive-only change. Add a new default-0 integer knob for the unavailable-repeat guard, wire it through the config builder, repoint `scan_unavailable_repeat`/`check_unavailable_repeat` to it, and add independent-toggle tests. Do not touch the empty-result guard's knob or semantics.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-191833
- **Related target files**: scripts/agent/tool_loop_guard.py, scripts/agent/config_dataclasses.py