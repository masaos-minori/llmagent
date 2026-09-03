## Goal
Remove `docs/05_agent_13_reference-api.md`'s incorrect claim that
`ToolRouteResolver`'s constructor "accepts `server_configs` for backward
compatibility," replace it with the constructor's actual parameters, and reconcile
the resulting text with the file's own existing correction note three lines later
so the section no longer contradicts itself.

## Scope
- **In-Scope**: `docs/05_agent_13_reference-api.md`'s `## ToolRouteResolver` section
  (the "Configuration" line and its relationship to the existing correction note).
- **Out-of-Scope**: `docs/04_mcp_03_01_dispatch-and-routing.md` (seq 02 of this
  Plan), `docs/04_mcp_90_inconsistencies_and_known_issues.md` (REQ-006, now
  Obsolete — see the Plan's own 2026-09-03 correction; that file no longer exists,
  consolidated into `docs/00_governance_03_issue-and-uncertainty-management.md`).
  `ToolRouteResolver`, `RuntimeToolRegistry`, `ToolExecutor` source code — this row
  is documentation-only.

## Assumptions
- `scripts/shared/route_resolver.py`'s `ToolRouteResolver.__init__()` accepts only
  `warn_on_missing: bool = False`, `strict_mode: bool = False`,
  `runtime_registry: RuntimeToolRegistry | None = None` (all keyword-only, per the
  `*` in the signature) — re-verified 2026-09-03 by direct `Read` of
  `scripts/shared/route_resolver.py:72-91`, matching the Plan's own evidence with
  no drift. It has never accepted a `server_configs` parameter.
- `resolve()` raises `ValueError` immediately when no match is found in
  `RuntimeToolRegistry`, with no fallback to any other source — re-verified at
  `scripts/shared/route_resolver.py:93-106`.
- Lines 114 and 117 of `docs/05_agent_13_reference-api.md` are unchanged from the
  Plan's own citation — re-verified 2026-09-03 by direct `grep`, no drift.

## Design decisions
- **Rewrite the "Configuration" line to list the constructor's actual three
  parameters**, rather than simply deleting the false claim and leaving no
  Configuration line at all — every other component's reference entry in this file
  (see `## ToolExecutor` above it) has a populated "Configuration" line, so leaving
  it empty would break the file's own established per-component field structure.
- **Trim the existing line-117 correction note's constructor-configuration detail
  down to a single cross-reference to the (now-corrected) Configuration line**,
  rather than duplicating the parameter list in both places — REQ-002 requires the
  section to "state one consistent, current description," which duplicating the
  same fact in two places (an inline field and a lengthy prose note) would not
  achieve as cleanly as stating it once, with the note explaining the earlier
  design's *history* (why it changed) rather than restating *what* it is now.
- **Keep the correction note's `> **Evidence Classification: Explicit in code
  (Correction).**` framing and its narrative about the removed 4-layer cascade and
  `KeyError` behavior** — that content is about `resolve()`'s failure behavior and
  routing history (REQ-003/REQ-004's territory: `RuntimeToolRegistry` sole
  authority, `ValueError` not `KeyError`), which remains accurate and is not the
  contradiction this row fixes; only the note's redundant restatement of the
  constructor's `server_configs` framing is removed.

## Alternatives considered
- **Delete the correction note (line 117) entirely and fold its content into the
  rewritten Configuration line** — rejected: the note documents *why* the
  behavior changed (previous versions' 4-layer cascade and `KeyError` claims),
  which is exactly the kind of "Evidence Classification: ... (Correction)" history
  this file's own established pattern (see the second `Evidence Classification`
  block at line 171 for the LLM-callee correction) preserves elsewhere — removing
  it would lose that precedent-setting context, not just fix the contradiction.
- **Leave line 114 as "No direct configuration" with no further detail** —
  considered, rejected: REQ-001 explicitly requires replacing the false claim
  "with the constructor's actual parameters," not merely deleting it; stating the
  actual parameters is more informative for a reader who wants to know how to
  construct a `ToolRouteResolver`.

## Implementation
### Target file
`docs/05_agent_13_reference-api.md`

### Procedure
1. Re-read lines 105-120 in full immediately before editing to reconfirm no drift
   (done above; confirmed identical to the Plan's citation).
2. Replace line 114's "Configuration" bullet with the corrected text in Details
   below.
3. Replace the line-117 correction note's constructor-related sentence with a
   cross-reference to the corrected Configuration line, per Details below.

### Method
Direct text edit (e.g. via the `Edit` tool) using the exact before/after blocks in
Details, as two edits within the same section.

### Details

**Edit 1 — Configuration line (REQ-001, REQ-002, REQ-003, REQ-004)**:

Before:
```
- **Configuration:** No direct configuration. The constructor accepts `server_configs` for backward compatibility but does not read them.
```

After:
```
- **Configuration:** Constructor parameters only — `warn_on_missing` (bool, default `False`), `strict_mode` (bool, default `False`), and `runtime_registry` (`RuntimeToolRegistry | None`, default `None`, the sole routing source `resolve()` consults). No `server_configs` parameter exists.
```

**Edit 2 — correction note (REQ-002)**:

Before:
```
> **Evidence Classification: Explicit in code (Correction).** Previous versions described a "4-layer cascade (live discovery > ToolRegistry > config `tool_names` > static constants)" and stated that a `KeyError` would occur on failure. However, after `shared/route_resolver.py::ToolRouteResolver.resolve()` was updated to only reference `ToolRegistry` and raise `ValueError` if no match is found, and subsequently migrated to `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`), the logic changed. `ToolRegistry` has been downgraded to seed data for drift detection and is no longer used for routing decisions. Config `tool_names` is merely drift verification metadata and not an input for routing. This change follows the implementation in `04_mcp_03_01_dispatch-and-routing.md` Reliable source of routing information.
```

After:
```
> **Evidence Classification: Explicit in code (Correction).** Previous versions described a "4-layer cascade (live discovery > ToolRegistry > config `tool_names` > static constants)", stated that a `KeyError` would occur on failure, and incorrectly claimed the constructor retained a `server_configs` parameter for backward compatibility (corrected above). After `shared/route_resolver.py::ToolRouteResolver.resolve()` was updated to only reference `ToolRegistry` and raise `ValueError` if no match is found, and subsequently migrated to `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`), the logic changed. `ToolRegistry` has been downgraded to seed data for drift detection and is no longer used for routing decisions. Config `tool_names` is merely drift verification metadata and not an input for routing. This change follows the implementation in `04_mcp_03_01_dispatch-and-routing.md` Reliable source of routing information.
```

Note: Edit 2 adds one clause ("and incorrectly claimed the constructor retained a
`server_configs` parameter for backward compatibility (corrected above)") rather
than restating the parameter list — this satisfies REQ-002's "state one
consistent, current description" by making the note point at the corrected
Configuration line as the single source of the parameter list, instead of
repeating it.

## Compatibility considerations
No other document links to this section by anchor with content that assumes the
old "server_configs for backward compatibility" wording (verified: this file's own
`## ToolRouteResolver` heading is referenced from
`docs/04_mcp_03_01_dispatch-and-routing.md`'s "Full details" link by heading name
only, unaffected by this row's body-text edits). Independent of seq 02 — this row
can be applied in any order relative to it.

## Security considerations
None — documentation-only correction of a component reference description; no
code, credentials, or access-control content is affected.

## Rollback considerations
Single-file, two-edit change to a Markdown document under version control; revert
via `git revert`. No other file's content depends on the exact old wording (see
Compatibility considerations).

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/05_agent_13_reference-api.md | Automated doc quality check | `uv run python tools/check_docs_quality.py` | No new errors |
| docs/05_agent_13_reference-api.md | Domain consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | No new port/tool/link drift findings |
| docs/05_agent_13_reference-api.md | Manual self-consistency check | Re-read the section around lines 108-117 | Exactly one, correct description of `ToolRouteResolver`'s constructor remains; no `server_configs` claim anywhere in the file |

## Completion criteria
- No statement in `docs/05_agent_13_reference-api.md` claims `ToolRouteResolver`
  accepts `server_configs` (AC-1).
- The Configuration line and the correction note state one consistent, current
  description of the constructor with no contradiction (AC-2, AC-4).
- No statement in this file describes a static routing fallback for unknown tool
  names (AC-3).
- `uv run python tools/check_docs_quality.py` and `uv run python
  tools/check_docs_consistency.py --domain mcp` report no new errors.

## Out of scope
`docs/04_mcp_03_01_dispatch-and-routing.md` (seq 02 of this Plan) — has its own
implementation-procedure document per this Plan's Implementation Target Files
table. `docs/04_mcp_90_inconsistencies_and_known_issues.md` / REQ-006 — Obsolete
per this Plan's 2026-09-03 correction (file no longer exists).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/done/20260902-143330_toolroutedoc_correct_tool_routing_docs_remove_obsolete_compat_claims.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-090104_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-151738
- **Related target files**: docs/05_agent_13_reference-api.md
