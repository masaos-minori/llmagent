# Implementation Procedure: docs/04_mcp_02_01_endpoints-and-transport.md

## Goal

Replace the stale "`inputSchema` (or `input_schema`)" and "legacy singular
`resource_scope`" wording with language naming `inputSchema`, `resource_scope_kind`, and
`resource_scope_keys` as the only supported fields, once the six dependency
strict-contract requirements have landed in code.

## Scope

**In-Scope**
- The bullet reading "`inputSchema` — per-tool schema (or `input_schema`)".
- The bullet reading "`resource_scope` — legacy singular scope field; type-checked only
  if present, not required".

**Out-of-Scope**
- Every other field bullet in this section (`name`, `description`, `status`,
  `server_key`, `enabled`, `disabled_reason`, `is_write`, `requires_serial`,
  `resource_scope_kind`/`resource_scope_keys`, `capabilities`, `config_dependent`) —
  already accurate, no change needed.
- The "Deferred fields" section below (`include_disabled`) — unrelated.

## Assumptions

- **Blocking precondition, not yet satisfied**: this edit must not land until the six
  dependency requirements' code changes are implemented and merged (per the source
  plan's Phase 1 gate). Verified during this implementation-procedure review:
  `scripts/agent/services/mcp_tool_discovery.py` still reads
  `entry.get("inputSchema", entry.get("input_schema"))` and `resource_scope` is still
  only type-checked when present, not rejected — i.e., the doc's current wording still
  accurately describes the live code. Editing this doc now would make it describe
  behavior that does not yet exist. Re-verify this precondition immediately before
  editing.
- The two target bullets, verified by direct read, currently exist essentially as
  quoted in the source plan (the plan's line numbers were off by a few lines from a
  full-file line count, but the bullet text itself matches exactly) — confirmed via
  direct file read during this review, not the plan's line-number claim alone.

## Design decisions

- Replace "`inputSchema` — per-tool schema (or `input_schema`)" with "`inputSchema` —
  per-tool schema (required; `input_schema` is not accepted)" — states the sole
  supported field name explicitly and names the rejected alias, rather than silently
  dropping the parenthetical.
- Replace "`resource_scope` — legacy singular scope field; type-checked only if
  present, not required" by deleting the bullet entirely, since `resource_scope_kind`/
  `resource_scope_keys` (already documented two bullets above as **required**,
  schema-2.0) are the sole supported replacement once the legacy singular field is
  rejected outright — keeping a bullet for a field that no longer exists in any form
  would misdescribe the schema.

## Alternatives considered

- Keep the `resource_scope` bullet but reword it to "Removed; use
  `resource_scope_kind`/`resource_scope_keys`" — rejected in favor of outright deletion,
  because this section documents the *live, accepted* per-tool response fields, not a
  changelog; a "removed field" note belongs in
  `docs/00_governance_05_deprecated-items.md` (this plan's own Phase 2 covers adding
  that entry there), not duplicated inline in the field reference.

## Implementation

### Target file
`docs/04_mcp_02_01_endpoints-and-transport.md`

### Procedure
1. Re-verify the Assumptions precondition (dependency code merged) before editing.
2. Edit the `inputSchema` bullet per Design decisions.
3. Delete the `resource_scope` legacy bullet per Design decisions.
4. Spelling/grammar pass on the edited section (per the source plan's Phase 2 last
   step).

### Method
Direct text edit of two bullet points in a Markdown list; no structural document
changes (headings, tables, front matter unaffected).

### Details
- No other section of this file references `inputSchema`/`input_schema`/
  `resource_scope` — confirmed via `rg -n "inputSchema|input_schema|resource_scope"
  docs/04_mcp_02_01_endpoints-and-transport.md` during this review; the two identified
  bullets are the complete set of edits needed in this file.

## Compatibility considerations

N/A: documentation-only change; no code or schema compatibility is affected by editing
prose. The prose change itself must be *preceded by* the code change it describes (see
Assumptions) — that is a sequencing dependency, not a compatibility risk.

## Security considerations

N/A: documentation wording change only.

## Rollback considerations

- Trivially revertable: reverting this doc edit has no effect on code or other files.
  If the underlying code change is reverted after this doc edit lands, revert this doc
  edit in the same pass to avoid the doc describing behavior the code no longer has.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/04_mcp_02_01_endpoints-and-transport.md | Documentation consistency | `uv run check-mcp-docs` | No new port/tool-name drift introduced |
| docs/04_mcp_02_01_endpoints-and-transport.md | Structural/formatting | `uv run python tools/check_doc_quality.py` | No new formatting violations |
| Repo-wide | Regression search | `rg -n "input_schema" docs scripts tests` | No remaining reference implying `input_schema` is accepted |

## Out of scope

- Any change to `docs/04_mcp_06_14_new-tool-registration-procedure.md` or the other two
  target docs — each has its own implementation procedure document in this same batch.

## Execution Status

##### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Precondition not met |
| 2 | Add or update tests per Validation plan | Skipped | — | — | Gated on code merge |
| 3 | Run the validation sequence (rules/toolchain.md) | Skipped | — | — | Gated on code merge |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | Documentation-only; gated |

##### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Assumption | Code still accepts input_schema alias and resource_scope optional field (scripts/agent/services/mcp_tool_discovery.py:275, 357). Procedure assumption conflicts with actual code behavior. | No | 2026-08-25 |

##### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-101341_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-202629
- Related target files: docs/04_mcp_02_01_endpoints-and-transport.md
