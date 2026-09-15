## Goal
Register a new Known Issue, `CI-016`, in
`docs/00_governance_03_issue-and-uncertainty-management.md` for the Decision
#12/INV-14 test-coverage gap in ADR-004, per `REQ-006` — the one item the source
issue's own text recommends registering but never does.

## Scope
- In scope: insert one new `#### CI-016` entry (16-field template) after the
  existing `#### CI-015` entry; update the closing "No other active Known Issues
  beyond ... CI-001, CI-003 through CI-015" line to include `CI-016`.
- Out of scope: any other existing `CI-*`/`RAG-*`/`EVENTBUS-*`/`DESIGN-*` entry;
  `docs/adr/ADR-004-environment-failure-handling-policy.md` (covered by the sibling
  procedure document for that row); resolving `UNK-01` (the `docs/adr-index.md`
  INV-021 vs. ADR-004 Completion Checklist discrepancy) — not this Plan's scope.

## Assumptions
- The new `CI-016` entry is written entirely in English, matching this file's own
  existing convention (all `CI-*` entries here are already English) — no Japanese
  content, unlike the sibling ADR-004 procedure's mixed-language content (Plan
  Assumptions).
- `Area: Agent` and `Type: operational-gap` follow the `CI-008`/`CI-014`/`CI-015`
  "verified [by code inspection] but needs test coverage" precedent exactly (Plan
  Design).

## Design decisions
- Model `CI-016` directly on `CI-008` (`docs/00_governance_03_issue-and-uncertainty-management.md`
  lines 344-361): same `Status: open`, `Severity: Medium`, `Type: operational-gap`
  shape, since both describe a design requirement that is verified by code
  inspection but lacks an automated test — not a design-gap or a document-code
  mismatch, since the code inspection itself found no contradiction, only missing
  coverage.
- State `Current Description` precisely: `McpServerConfig.required` defaults to
  `True` (a safe default — undefined criticality is never silently treated as
  non-required), but no automated test verifies this default, and no distinct code
  path flags "criticality was never explicitly configured" as its own design/config
  error per Decision #12's literal wording. Do not overstate this as "INV-14 is not
  enforced at all" (contradicted by the safe-default evidence) or understate it as
  "fully resolved" (contradicted by ADR-004's own Completion Checklist and Manual
  Review notes) — both would misrepresent the evidence gathered in
  `plans/20260915-145322_plan.md` Unknowns `UNK-01`.

## Alternatives considered
- Classify as `Type: design-gap` instead of `operational-gap` — rejected; the design
  itself (the `required: bool = True` default) already satisfies the safety
  requirement, so this is a missing-verification gap, not a missing-design one,
  matching the `CI-008`/`CI-014`/`CI-015` precedent's own reasoning.
- Fully resolve `UNK-01` (reconcile `docs/adr-index.md` INV-021's "Resolved" claim
  against this) before filing `CI-016` — rejected as out of scope; `UNK-01` is
  explicitly Non-blocking in the Plan and targets a different file
  (`docs/adr-index.md`), not this row's target file.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Re-confirm (idempotent recheck) that no `CI-016` entry exists yet
   (`grep -c "CI-016" docs/00_governance_03_issue-and-uncertainty-management.md`
   should return `0`) and that `#### CI-015` is still the last entry before the
   closing "No other active Known Issues..." line.
2. Insert a new `#### CI-016` entry immediately after the existing `#### CI-015`
   entry (and its trailing blank line) and before the "No other active Known Issues
   beyond RAG-005, DESIGN-1, DESIGN-2, EVENTBUS-001 through EVENTBUS-008, and CI-001,
   CI-003 through CI-015 above." line, using this exact 16-field content:

   ```markdown
   #### CI-016

   - **ID**: CI-016
   - **Title**: ADR-004 Decision #12/INV-14 — undefined component criticality treatment relies on a safe default, verified but needs test coverage
   - **Status**: open
   - **Severity**: Medium
   - **Area**: Agent
   - **Type**: operational-gap
   - **Source**: `scripts/shared/mcp_config.py` (`required: bool = True` default), `scripts/agent/services/mcp_tool_discovery.py`
   - **Owner**: Unassigned
   - **First Found**: Unconfirmed
   - **Target**: `docs/adr/ADR-004-environment-failure-handling-policy.md`
   - **Related**: ADR-004
   - **Summary**: ADR-004 Decision #12/INV-14 requires that undefined or undeterminable component criticality never be assumed non-required and be treated as an unresolved design/config error.
   - **Current Description**: `McpServerConfig.required` defaults to `True` (`scripts/shared/mcp_config.py:95`), so an unspecified criticality is never silently treated as non-required. However, no automated test verifies this default-required safety net, and no distinct code path flags "criticality was never explicitly configured" as its own design/config error per Decision #12's literal wording — ADR-004's own Completion Checklist and Manual Review notes still list INV-14 as unverified/Manual-Review-only.
   - **Observed Implementation**: Verified by code inspection only (default value inspection); no automated test.
   - **Impact**: Without test coverage, a future change to the default value (e.g. `required: bool = False`) would silently violate INV-14 with no automated check to catch the regression.
   - **Recommended Action**: Add a unit test asserting `McpServerConfig.required` defaults to `True` when unspecified, and/or a test asserting undefined-criticality components are never routed as non-required.

   ```
3. Update the closing line "No other active Known Issues beyond RAG-005, DESIGN-1,
   DESIGN-2, EVENTBUS-001 through EVENTBUS-008, and CI-001, CI-003 through CI-015
   above." to read "...and CI-001, CI-003 through CI-016 above." (extend the range
   to include the new entry).

### Method
Use `Edit` (exact-string replacement) against
`docs/00_governance_03_issue-and-uncertainty-management.md` — one `Edit` call to
insert the `#### CI-016` block after `#### CI-015`'s content, and a second `Edit`
call to update the closing "No other active Known Issues..." line.

### Details
- Match the exact Markdown field-bullet format of `#### CI-007`/`#### CI-008`/
  `#### CI-014`/`#### CI-015` (blank line after the `#### CI-016` heading, then one
  `- **Field**: value` bullet per line, in the same 16-field order as those entries)
  — do not introduce a different bullet order or omit a field; use `N/A` only where
  those existing entries themselves use it (none of `CI-007`/`CI-008`/`CI-014`/
  `CI-015` use `N/A` for any field, so `CI-016` should not either, per Design above).
- The sibling ADR-004 procedure document
  (`implementations/20260915-150541_01_docs_adr_ADR-004-environment-failure-handling-policy.md.md`)
  adds a matching `### {ID}` block inside ADR-004's own `## Known Deviations`
  section that cross-references this `CI-016` ID — process this row's edit
  independently (it does not depend on that document's edit having been applied
  first), but both must agree on the ID `CI-016` and its `Target`/`Related` fields
  once both are applied.

## Compatibility considerations
N/A: documentation-only change; no code, config, or test reads this file's Known
Issue entries programmatically (confirmed: `tools/check_docs_structure.py` and
`tools/check_docs_quality.py` apply only generic structural/link checks to this
file, not per-entry schema validation).

## Security considerations
N/A: documentation-only change; no credentials, secrets, or executable content is
introduced.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via `git checkout -- docs/00_governance_03_issue-and-uncertainty-management.md`
(or the specific commit, once committed) if validation fails and cannot be fixed
forward within `AGENTS.md` Loop Prevention's attempt bound. If the sibling ADR-004
document's edit was already applied and references `CI-016`, do not roll back this
file in isolation without also flagging that cross-reference as stale in the
sibling document's own Execution Status / Blocker Log.

## Validation plan
- `grep -c "^#### CI-016" docs/00_governance_03_issue-and-uncertainty-management.md` — expect `1`.
- `grep -n "CI-001, CI-003 through CI-016" docs/00_governance_03_issue-and-uncertainty-management.md` — expect one match (closing line updated).
- `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` — expect zero findings.
- `uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md` — expect exactly the pre-existing 1-finding baseline recorded in the Plan (size limit) and no new finding.

## Completion criteria
- `#### CI-016` exists exactly once, positioned after `#### CI-015` and before the
  closing "No other active Known Issues..." line, with all 16 required fields
  populated (no blank field).
- The closing summary line includes `CI-016` in its range.
- All Validation plan checks above pass (or, for `check_docs_structure.py`, produce
  no finding beyond the recorded pre-existing baseline).

## Out of scope
- `docs/adr/ADR-004-environment-failure-handling-policy.md` itself — covered by the
  sibling procedure document,
  `implementations/20260915-150541_01_docs_adr_ADR-004-environment-failure-handling-policy.md.md`.
- Resolving `UNK-01` (`docs/adr-index.md` INV-021 vs. ADR-004 Completion Checklist
  reconciliation) — a separate, narrowly-scoped issue per the Plan, not this row.
- Fixing this file's pre-existing byte-size-limit finding — pre-existing, unrelated
  to this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-150541 | 20260915-151517 | Registered CI-016 after CI-015 and updated the closing summary line via Edit |
| 2 | Add or update tests per Validation plan | Completed | 20260915-151517 | 20260915-151517 | N/A: documentation-only, no automated test suite targets this file's content — Validation plan is grep/tool checks, not pytest N/A: documentation-only, no automated test suite targets this file's content |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-151517 | 20260915-151517 | Use this document's own Validation plan (doc checkers), not the Python `rules/toolchain.md` sequence — not applicable to a documentation-only change check_docs_quality: 0 findings; check_docs_structure: exactly the pre-existing 1-finding baseline (size limit), no new finding; both grep acceptance checks passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-151517 | 20260915-151517 | N/A: this document's own target file IS the documentation being updated N/A: this document's own target file IS the documentation being updated; no docs/00_index.md row requires a further cascading update |

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
- **Requirement ID**: REQ-006 — register CI-016 for the Decision #12/INV-14 test-coverage gap
- **Source issue**: issues/20260914-124357_docqa01_adr-004-known-deviations-section-missing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-145322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-150541
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md