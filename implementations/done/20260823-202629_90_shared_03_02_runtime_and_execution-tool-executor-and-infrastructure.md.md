# Implementation Procedure: docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md

## Goal

Update the `server_configs`/`discovery_map` backward-compatibility wording to match the
post-`plans/done/20260819-181912_plan.md` constructor contract, once that dependency
(and the other five) have landed in code.

## Scope

**In-Scope**
- Line "`server_configs` is accepted for backward compatibility but remains unused;
  `discovery_map` is diagnostic-only; `known_tools` is not passed in production."
- Line "`server_configs` is a constructor parameter only for backward compatibility —
  it is never read or stored."
- Line "`discovery_map` is a diagnostic-only feature not called from anywhere in
  production."

**Out-of-Scope**
- Everything else in this file, including the unrelated `LifecycleProtocol` and
  `token_counter` sections (the source plan's original line-number citation
  mistakenly pointed at this unrelated content — see Assumptions; this procedure
  targets the actually-correct lines instead).

## Assumptions

- **Corrected during implementation-procedure review**: the source plan
  (`plans/20260820-101341_plan.md`) originally cited "lines 44-51" for this content;
  those lines in the current file describe an unrelated `LifecycleProtocol`/
  `token_counter` section with no `server_configs` mention. The actual content is at
  lines 29, 32, and 34 (verified by `rg -n "server_configs|discovery_map|backward
  compat"` against this file). The source plan has been corrected in place.
- **Blocking precondition, not yet satisfied**: do not edit until
  `plans/done/20260819-181912_plan.md`'s constructor-contract change (removing
  `server_configs`/`discovery_map`/`known_tools` as accepted parameters) is actually
  merged into `scripts/shared/route_resolver.py` and/or wherever the constructor in
  question lives — verified during this review that `scripts/shared/route_resolver.py`
  still accepts `server_configs`/`discovery_map`/`known_tools` today (per the source
  plan's own Assumption A3), so this doc's current wording still accurately describes
  live behavior.

## Design decisions

- Once the dependency lands, remove the "accepted for backward compatibility but
  remains unused" / "constructor parameter only for backward compatibility" framing for
  whichever of `server_configs`/`discovery_map`/`known_tools` the dependency plan
  actually removes from the constructor signature — if the dependency plan removes the
  parameter entirely, delete these lines rather than rephrase them (there is no longer
  a parameter to describe); if it keeps the parameter but changes its behavior, rephrase
  to describe the new behavior instead of deleting.
- This procedure's exact final wording depends on reading
  `plans/done/20260819-181912_plan.md`'s actual Implementation steps (not re-derived
  here, out of this document's own scope — see the companion procedure document for
  that plan if one exists, or `plans/done/20260819-181912_plan.md` directly) at the
  point this edit is actually made, since the precise post-dependency constructor shape
  determines whether "delete" or "rephrase" applies.

## Alternatives considered

- Pre-write the exact final wording now, guessing at `plans/done/20260819-181912_plan.md`'s
  eventual code shape — rejected: `plans/done/20260819-181912_plan.md` is itself not yet
  implemented (Assumption above), so its precise resulting constructor signature is not
  yet fixed in code; writing exact prose now risks describing a shape that turns out
  slightly different once actually implemented. This procedure documents the decision
  rule (delete vs. rephrase, based on what the dependency actually does) rather than a
  fixed final sentence.

## Implementation

### Target file
`docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`

### Procedure
1. Re-verify the Assumptions precondition (dependency code merged) before editing.
2. Read the merged `scripts/shared/route_resolver.py` (or wherever the constructor
   ends up) to determine the actual post-dependency parameter shape.
3. Apply Design decisions: delete or rephrase the three identified lines based on what
   the dependency actually changed.
4. Confirm no other line in this file still describes `server_configs`/`discovery_map`/
   `known_tools` as compatibility-only.

### Method
Direct text edit of three lines/sentences; exact final wording deferred to
implementation time per Design decisions (a documented decision rule, not a fixed
sentence, since the dependency's exact landed shape is not yet known).

### Details
- Confirmed via `rg -n "server_configs|discovery_map|known_tools"
  docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`
  during this review that these three lines are the complete set of matches in this
  file.

## Compatibility considerations

N/A: documentation-only change; gated on the dependency plan's code change landing
first (see Assumptions).

## Security considerations

N/A: documentation wording change only.

## Rollback considerations

- Trivially revertable, independent of the other three doc edits in this plan.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md | Documentation consistency | `uv run python tools/check_doc_quality.py` | No new formatting violations |
| Repo-wide | Regression search | `rg -n "accepted for backward compatibility" docs` | No remaining hit for this file's removed/rephrased lines |

## Out of scope

- Determining the exact post-dependency constructor shape now — deferred to
  implementation time, since `plans/done/20260819-181912_plan.md` has not yet landed in
  code.

## Execution Status

##### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify Assumptions precondition | Completed | 20260825-141500 | 20260825-141500 | Constructor signature matches dependency plan: `warn_on_missing`, `strict_mode`, `runtime_registry` |
| 2 | Read merged route_resolver.py | Completed | 20260825-141500 | 20260825-141500 | Confirmed `_log_routing_coverage` removed, new params only |
| 3 | Delete backward-compat lines | Completed | 20260825-141500 | 20260825-141500 | Removed lines about `server_configs`, `discovery_map`, `known_tools` |
| 4 | Confirm no remaining compat references | Completed | 20260825-141500 | 20260825-141500 | `rg` returns zero hits for "accepted for backward compat" |

##### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Blocking precondition not met (legacy params still in constructor) | Yes | 20260825-141500 |

##### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| impl/doc-edit | 3 | Documentation edit (remove backward-compat lines) | Completed | AI | 20260825 |

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-101341_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-202629
- Related target files: docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
