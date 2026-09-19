## Goal
Classify `docs/04_mcp_01_system_overview.md`'s 2 real `## Implementation Notes` bullets
against `docs/00_governance_02_documentation-metadata.md`'s Decision Categories and apply
the corresponding action (REQ-002, REQ-003).

## Scope
In scope: the 2 confirmed real bullets in this file's `## Implementation Notes` section.
Out of scope: this file's other sections; any other file.

## Assumptions
Confirmed 20260919 (`plan-to-implementation-procedure` Step 3a, re-confirming the
finding already surfaced during the source Issue's own drafting): this file's
`## Implementation Notes` section (line 159) contains exactly 2 real bullets:
1. `McpServerHealthRegistry` state transitions are 5-valued (`HEALTHY`/`DEGRADED`/
   `UNAVAILABLE`/`HALF_OPEN`/`UNKNOWN`), not a simple ternary; `UNAVAILABLE` auto-
   transitions to `HALF_OPEN` after 30s (`half_open_cooldown_sec`) on `is_unavailable()`,
   implementing a simple circuit breaker.
2. `record_degraded()` does not overwrite `UNAVAILABLE`/`HALF_OPEN` state, "to avoid
   breaking the circuit breaker and trial window" (line 162 — contains the "to avoid"
   rationale marker per `tools/check_docs_content_policy.py`'s `_RATIONALE_MARKERS`).

## Design decisions
Per the Decision Categories table and this Plan's own Background (this exact bullet 2
was the confirmed promotion candidate that motivated this whole audit): bullet 2 is
`Retain` — it states *why* a design constraint exists ("to avoid breaking the circuit
breaker and trial window") and what breaks if violated, which is squarely "Correlated
constraints and their rationale" per the Decision Categories' retain criteria. Bullet 1
is more mixed: the 5-state enumeration itself is `Delete`/`Compress`-able (verifiable
directly from `shared/mcp_health.py`'s enum definition), but the *behavioral* fact that
`UNAVAILABLE` auto-transitions to `HALF_OPEN` after a specific cooldown, acting as a
circuit breaker, is design-relevant context that bullet 2 depends on for the reader to
understand what "the circuit breaker and trial window" even refers to — classify bullet
1's behavioral half as `Retain` alongside bullet 2, and only the bare enum-value list as
`Delete`/`Compress`.

## Alternatives considered
Treating bullet 1 as entirely `Delete` (since enum values are code-verifiable) was
considered and rejected: doing so would strand bullet 2's promoted "to avoid breaking the
circuit breaker and trial window" rationale without the context of what the circuit
breaker/trial window actually are, making the promoted text confusing on its own.

## Implementation
### Target file
docs/04_mcp_01_system_overview.md

### Procedure
1. Read this file's main body (the `## Major Components`/`## Relationship between
   server, protocol, and shared` sections, lines 114-148) to find the best existing
   location to promote the circuit-breaker behavior and rationale into, rather than
   inventing a new subsection.
2. Split bullet 1: delete/compress the bare 5-value enum list (or leave a one-line
   pointer to `shared/mcp_health.py` if the main body doesn't already name the states);
   promote the `UNAVAILABLE`→`HALF_OPEN` auto-transition + cooldown + circuit-breaker
   framing into the main body location found in step 1.
3. Promote bullet 2's full content (the "to avoid breaking..." rationale) into the same
   main body location, immediately following the promoted content from step 2 — do not
   split the constraint from its rationale.
4. Remove both bullets from `## Implementation Notes` once promoted (a short
   cross-reference is acceptable if useful, not a full duplicate).
5. Re-run the Validation plan's checkers.

### Method
`Edit` tool — direct text edit within `## Implementation Notes` and the main-body
location identified in step 1.

### Details
Keep the promoted text's wording close to the original (accurate, evidence-grounded)
rather than paraphrasing loosely — this content was already verified accurate during
this Plan's own Background investigation.

## Compatibility considerations
Only `## Implementation Notes` and the identified main-body section within this file are
affected. No other file is modified.

## Security considerations
N/A: documentation-only, no credentials or runtime behavior change.

## Rollback considerations
`git checkout -- docs/04_mcp_01_system_overview.md` reverts this row independently.

## Validation plan
- `uv run python tools/check_docs_quality.py` — confirm no new finding for this file.
- `uv run python tools/check_docs_structure.py` — confirm no new finding for this file.

## Completion criteria
Both bullets are classified and their content correctly split between `Delete`/
`Compress` (bare enum list) and `Retain` (circuit-breaker behavior + rationale, promoted
together into the main body); no content is lost or duplicated; the checkers above
report no new finding.

## Out of scope
This file's other sections beyond `## Implementation Notes` and the identified main-body
promotion destination; any other design doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Split bullet 1; promote circuit-breaker behavior + bullet 2's rationale together |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, no test to add |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | check_docs_quality.py, check_docs_structure.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own Target file IS the documentation being updated |

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
- **Requirement ID**: REQ-002, REQ-003 (classify 2 real bullets; promote circuit-breaker rationale)
- **Source issue**: issues/20260919-193722_impln01_audit-and-reclassify-docs-implementation-notes-items-per-existing-decision-categories.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-194628_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-195506
- **Related target files**: docs/04_mcp_01_system_overview.md
