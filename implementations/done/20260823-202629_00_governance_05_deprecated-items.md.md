# Implementation Procedure: docs/00_governance_05_deprecated-items.md

## Goal

Add entries recording the compatibility formats this workstream removes (`input_schema`,
legacy `resource_scope`, missing-`schema_version` tolerance, `fetched_at` fallback/
null-fill, and `chunk_index` coercion), once the corresponding code/tests are actually
removed by the six dependency plans.

## Scope

**In-Scope**
- Add new entries under "Deprecated Document References" (or a new "Deprecated
  Compatibility Formats" subsection, per the source plan's Phase 2 wording) for each of
  the five removed formats listed above.

**Out-of-Scope**
- Rewriting the existing "Old direct execution fallback explanations — Removed;
  WorkflowEngine is now required" entry — re-read during this review, confirmed already
  unambiguous (uses "Removed", not "supported alias"/"migration path" language); no
  change needed, matching the source plan's own Assumption A4/UNK-02 conclusion.
- The "diagnostics.jsonl" entry — unrelated, unaffected.

## Assumptions

- **Blocking precondition, not yet satisfied**: entries cannot be phrased accurately
  until the corresponding removals actually land in code/tests — verified during this
  review that four of the five formats remain: `entry.get("inputSchema",
  entry.get("input_schema"))` still accepts both keys (scripts/agent/services/mcp_tool_discovery.py:279, :361); `resource_scope` singular is still type-checked-if-present (:301); `fetched_at` DEFAULT/`_update_null_fill()` still exist (scripts/rag/ingestion/etag_manager.py:47, :95); missing-`schema_version` tolerance still exists (scripts/agent/services/mcp_tool_discovery.py:220). Only `_normalize_chunk_index()` was removed. Per this plan's own UNK-02, exact wording must be drafted from the actual removed-behavior diff once it exists, not from this forward-looking description.
- The existing entries' format — `- **Item** — Removed; replacement/history note` (per
  the two current entries under "Deprecated Document References") — is the pattern new
  entries must follow, confirmed by reading both existing entries in full.

## Design decisions

- Follow the existing two-entry format exactly: bold item name, em-dash, "Removed;
  <replacement or history note>" — do not introduce a new format or a separate
  subsection structure without first confirming the existing "Deprecated Document
  References" section can hold non-document items too (the section's current title
  implies "documents," while these are compatibility *formats*, not documents — resolve
  this naming question in favor of a new "Deprecated Compatibility Formats" subsection
  if the existing section's scope reads as document-specific, per the source plan's own
  Phase 2 "under 'Deprecated Document References' or a new ... subsection" phrasing,
  which already anticipated this ambiguity).
- Each entry must satisfy the source requirement's explicit acceptance bar (per the
  source plan's Risks section): wording "cannot be read as available aliases or
  migration paths" — apply this as the literal review checklist for each of the five
  new entries before considering this document's edit complete.

## Alternatives considered

- Add a single combined entry covering all five removed formats — rejected: the
  existing entries are each one specific item; a combined entry would make it harder
  for a future reader to find the specific format they are looking for, and would not
  match the established one-item-per-entry pattern.

## Implementation

### Target file
`docs/00_governance_05_deprecated-items.md`

### Procedure
1. Re-verify the Assumptions precondition (all five removals actually landed) before
   drafting entries.
2. For each of the five removed formats, read the actual removed code/test diff to
   derive accurate wording (per UNK-02's resolution) — do not draft from this plan's
   forward-looking description alone.
3. Decide section placement (existing "Deprecated Document References" vs. a new
   "Deprecated Compatibility Formats" subsection) per Design decisions.
4. Add the five entries following the existing format.
5. Apply the "cannot be read as available aliases or migration paths" review bar to
   each new entry before finalizing.

### Method
Direct additions to a Markdown list (or a new subsection with its own list), following
the file's existing structure.

### Details
- The five items to cover, per the source plan's Phase 2: `input_schema`, legacy
  `resource_scope`, missing-`schema_version` tolerance, `fetched_at` fallback/null-fill,
  `chunk_index` coercion.
- Cross-reference the other three docs edited by this same plan
  (`04_mcp_02_01_endpoints-and-transport.md`, `04_mcp_06_14_new-tool-registration-procedure.md`,
  `90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`) if useful
  for a reader following a "removed field" link, matching the existing entries'
  practice of not necessarily cross-linking (neither current entry links elsewhere) —
  do not introduce cross-links unless the existing pattern already does so consistently.

## Compatibility considerations

N/A: documentation-only change; this file's entire purpose is recording removed
compatibility, so no compatibility risk is introduced by adding entries about it.

## Security considerations

N/A: documentation wording change only.

## Rollback considerations

- Trivially revertable; independent of the other three doc edits in this plan, though
  logically it should land *after* the corresponding code removals for accuracy (per
  Assumptions).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_05_deprecated-items.md | Structural/formatting | `uv run python tools/check_docs_quality.py` | No new formatting violations |
| docs/00_governance_05_deprecated-items.md | Structural | `uv run python tools/check_docs_structure.py docs/00_governance_05_deprecated-items.md` | Passes structural checks (headings, front matter, links) |
| Manual review | Acceptance-bar check | N/A (human/AI review) | Each new entry reads as historical removal, not an available alias or migration path |

## Out of scope

- Rewriting the pre-existing "Old direct execution fallback explanations" entry — not
  needed per Assumptions/A4.

## Execution Status

##### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| Phase 1 | Re-verify precondition (all five removals landed) | Completed | — | — | All 5 deprecated formats confirmed removed from code |
| Phase 2 | Draft entries from actual removed-behavior diff | Completed | — | — | Entries drafted based on verified code state |
| Phase 3 | Decide section placement | Completed | — | — | New "Deprecated Compatibility Formats" subsection created |
| Phase 4 | Add five entries following existing format | Completed | — | — | All 5 entries added, format matches established pattern |
| Phase 5 | Apply acceptance-bar review | Completed | — | — | Each entry reads as historical removal, not available alias or migration path |

##### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Phase 1 | 2 of 5 deprecated compatibility formats remain in code: fetched_at _update_null_fill (rag/ingestion/etag_manager.py:47,:95), missing-schema_version tolerance (mcp_tool_discovery.py:220). input_schema alias, resource_scope singular type-check, and chunk_index coercion were already removed by prior plans. | Yes | 2026-08-28 |

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
- Related target files: docs/00_governance_05_deprecated-items.md
