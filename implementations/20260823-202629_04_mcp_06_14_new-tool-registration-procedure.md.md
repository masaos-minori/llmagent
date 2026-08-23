# Implementation Procedure: docs/04_mcp_06_14_new-tool-registration-procedure.md

## Goal

Apply the same `resource_scope` legacy-alias wording fix as
`docs/04_mcp_02_01_endpoints-and-transport.md`, once the six dependency strict-contract
requirements have landed in code.

## Scope

**In-Scope**
- The "Optional fields" bullet reading "`resource_scope`: legacy singular scope field;
  type-checked only if present, not required".

**Out-of-Scope**
- Every other "Optional fields" bullet (`status`, `enabled`, `capabilities`,
  `server_key`, `config_dependent`, `disabled_reason`) — unaffected.
- The preceding "never silently defaulted" text about `RuntimeToolRegistry` — unrelated
  to `resource_scope`.

## Assumptions

- **Same blocking precondition as the sibling `04_mcp_02_01_endpoints-and-transport.md`
  procedure, not yet satisfied**: do not edit until the six dependency requirements'
  code changes are merged. Verified during this review: the underlying code
  (`scripts/agent/services/mcp_tool_discovery.py`) still type-checks `resource_scope`
  only when present — this doc's current wording still accurately describes live
  behavior.
- Found by this plan's own `rg -n "backward compat|legacy|input_schema|resource_scope|
  _update_null_fill|fallback|migration" docs` validation search rather than being named
  in the source requirement's original Target files list (per the source plan's
  Assumption A5) — verified by direct read that this file contains the identical stale
  "legacy singular scope field" language as `04_mcp_02_01_endpoints-and-transport.md`.

## Design decisions

- Delete the `resource_scope` bullet entirely (same decision as the sibling
  `04_mcp_02_01_endpoints-and-transport.md` procedure, for the same reason: once the
  legacy singular field is rejected outright by the merged code, there is no supported
  field left to document under "Optional fields" for this concept — `resource_scope_kind`/
  `resource_scope_keys` would need to be documented as required fields instead, if this
  registration procedure doc doesn't already cover them elsewhere in the file).
- Before deleting, check whether this file documents `resource_scope_kind`/
  `resource_scope_keys` anywhere else (a required-fields section) — if not, this plan's
  scope (per its own Scope/Design sections) is limited to removing the stale legacy
  wording, not adding new required-field documentation; a gap here would need a
  follow-up requirement, not a silent addition beyond this plan's stated scope.

## Alternatives considered

- Reword the bullet to "Removed; use `resource_scope_kind`/`resource_scope_keys`"
  instead of deleting — rejected for the same reason as the sibling procedure: this is
  a live-fields reference section, and removal history belongs in
  `docs/00_governance_05_deprecated-items.md` (covered by this plan's Phase 2, separate
  target file).

## Implementation

### Target file
`docs/04_mcp_06_14_new-tool-registration-procedure.md`

### Procedure
1. Re-verify the Assumptions precondition (dependency code merged) before editing.
2. Check whether `resource_scope_kind`/`resource_scope_keys` are documented elsewhere in
   this file as required fields; if not, note this as a possible follow-up gap in the
   Execution Status notes rather than expanding this procedure's scope.
3. Delete the `resource_scope` legacy bullet.
4. Spelling/grammar pass on the edited section.

### Method
Direct text edit of one bullet point in a Markdown list.

### Details
- Confirmed via `rg -n "resource_scope" docs/04_mcp_06_14_new-tool-registration-procedure.md`
  during this review that this is the only `resource_scope`-related line in the file.

## Compatibility considerations

N/A: documentation-only change, gated on the same code-merge precondition as the
sibling doc.

## Security considerations

N/A: documentation wording change only.

## Rollback considerations

- Trivially revertable, independent of the other three doc edits in this plan (each
  targets a different file with no cross-file dependency at the text level).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/04_mcp_06_14_new-tool-registration-procedure.md | Documentation consistency | `uv run check-mcp-docs` | No new drift introduced |
| docs/04_mcp_06_14_new-tool-registration-procedure.md | Structural/formatting | `uv run python tools/check_doc_quality.py` | No new formatting violations |
| Repo-wide | Regression search | `rg -n "resource_scope\"" docs scripts tests` (singular legacy field, not `resource_scope_kind`/`_keys`) | No remaining reference implying singular `resource_scope` is accepted |

## Out of scope

- Documenting `resource_scope_kind`/`resource_scope_keys` as required fields in this
  file if they are not already covered elsewhere — flagged as a possible follow-up, not
  performed here (see Design decisions).

## Execution Status

##### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

##### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-101341_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-202629
- Related target files: docs/04_mcp_06_14_new-tool-registration-procedure.md
