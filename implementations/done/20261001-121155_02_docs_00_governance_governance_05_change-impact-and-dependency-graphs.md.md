## Goal
- Create the new governance document holding the 8 relocated sections verbatim (REQ-002) without new checker findings (REQ-007).

## Scope
- In: the changes listed under Implementation > Details in `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`.
- Out: every other file and every unlisted part of `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`.

## Assumptions
- New file; containing directory `docs/00_governance/` exists and holds governance_00 to governance_04 (re-verified 2026-10-01).
- `schemas/doc_front_matter.json` requires `title`, `area`, `tags`, `related`; `tools/check_docs_structure.py` also requires one H1, `## Related Documents`, and `## Keywords`.
- The moved text contains no 'needs confirmation' string, so `check_needs_confirmation_inventory.py` (which exempts only governance_00 to governance_04) gains no finding.
- Execution order across this Plan's procedures follows Plan Implementation steps: Step 1 baseline -> Step 2 (seq 01 Part A) -> Step 3 (seq 02) -> Step 4 (seq 06, 07, 08) -> Step 5 (seq 01 Part B) -> Step 6 (seq 03) -> Step 7 (seq 04, 05) -> Step 8 verification.

## Design decisions
- Copy section bodies verbatim from the current Policy, in this order: Update Rule, Change Impact Rule, Change-Impact Matrix, RACI Model, Software Runtime Dependency Graph, Deployment Management Graph, Documentation Reference Graph, Governance Applicability Matrix — keeps the existing 'below'/'above' references valid.
- Only relocation edit: in `## Change Impact Rule`, the text 'continue to use the existing Canonical Source Precedence matrix (Decision Target Canonical Source Matrix)' links that matrix to `governance_01_documentation-policy.md#decision-target-canonical-source-matrix`.
- The stale path `docs/00_governance_04_documentation-checks.md` inside `## Software Runtime Dependency Graph` is copied unchanged (owned by `govpath001`).

## Alternatives considered
- Fix the stale path while moving: rejected — not relocation-required (Plan Out-of-Scope; `govpath001`'s repository-wide grep will catch it in the new file).

## Implementation
### Target file
- `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`

### Procedure
1. Confirm the prerequisite procedures named in Assumptions are Completed.
2. Apply the changes in Details, in the listed order.
3. Run the Validation plan and compare with the Plan Design baseline.
4. Record results in Execution Status Notes.

### Method
- Targeted edits only; confirm with `git diff docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` that nothing outside Details changed.

### Details
- Front matter: `title: "Change Impact and Dependency Graphs"`, `area: governance`, `tags: [governance]` (list form as in governance_04), `related:` `governance_01_documentation-policy.md`, `governance_04_documentation-checks.md`.
- `# Change Impact and Dependency Graphs`, then `## Purpose`: one sentence stating that this document defines how a change maps to affected documents, the approval model, and the dependency-graph taxonomy, split out of the Documentation Policy.
- Then the 8 sections verbatim (order and relocation edit per Design decisions).
- `## Related Documents`: Documentation Policy (`governance_01_documentation-policy.md`), Documentation Checks (`governance_04_documentation-checks.md`).
- `## Keywords`: change impact, RACI, dependency graph, governance.

## Compatibility considerations
- `tools/check_dependency_graph_cycles.py` will read `## Software Runtime Dependency Graph` from this file after seq 06.

## Security considerations
- N/A: documentation/tool path change only; no secrets, network access, or runtime behavior beyond which file the checker reads.

## Rollback considerations
- Revert with `git checkout -- docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` (or delete the file if newly created). Revert seq 01 Part B before seq 02/06 to keep the graph checker passing.

## Validation plan
- `uv run python tools/check_docs_structure.py docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` — no findings.
- Byte comparison script: each moved section body equals the saved Policy body, except the one listed relocation edit (diff printed in the report).
- `uv run python tools/check_needs_confirmation_inventory.py` — no finding for this file.
- `uv run python tools/check_docs_quality.py` — no within-file pair for this file (the moved sections produced none in the Policy).
- `uv run python tools/check_docs_japanese.py` — file not listed.

## Completion criteria
- File exists with valid front matter, one H1, Purpose, the 8 sections in the specified order, Related Documents, Keywords.
- Moved bodies byte-identical except the listed relocation edit.

## Out of scope
- Rule wording changes; stale-path cleanup (`govpath001`); `## Area Canonical Maps` (`canon001`); ADR quotes (`langdoc001`); the external-behavior matrix discrepancy (`issues/20261001-112149_unknowns.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create front matter, H1, Purpose | Completed | 20261001-151934 | 20261001-130000 |  |
| 2 | Copy the 8 sections verbatim; apply the one relocation edit | Completed | 20261001-151934 | 20261001-152101 |  |
| 3 | Add Related Documents and Keywords | Completed | 20261001-151934 | 20261001-152101 |  |
| 4 | Run Validation plan including byte comparison | Completed | — | 20261001-152200 | Changed governance_05 new doc. Byte comparison identical except the listed link edit. Transient similarity warnings remain until seq 01 Part B. |

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
- **Requirement ID**: REQ-002, REQ-007 (new document holding the moved cluster; no regression) — Plan Implementation steps Step 3
- **Source issue**: issues/20261001-104656_docsize001_reduce-documentation-policy-below-structure-size-limit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-112149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-121155
- **Related target files**: docs/00_governance/governance_05_change-impact-and-dependency-graphs.md