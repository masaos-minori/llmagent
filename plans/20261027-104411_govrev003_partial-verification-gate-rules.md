## Goal
- Define the Verification Status vocabulary of the ADR Invariant Verification Matrix and the Gate effect of each value in `adr_01_index.md`, so that the merge or deployment effect of a partially or manually verified Blocking invariant is stated once and can be judged the same way by every reviewer.

## Priority
Medium

## Scope
- **In-Scope**:
  - Define the status values (Confirmed, Partial, Manual, Not verified) and their Gate effects in the matrix introduction.
  - Define the mandatory content of a Partial row and of a manually verified Blocking row (unverified scope or manual procedure, and an Owner).
  - Update the ADR-004 INV-07, INV-10, INV-01 and INV-02 rows to the defined form without changing their Gate or invariant statement.
  - Map the other non-standard rows (ADR-004 INV-15 and INV-16, ADR-014 INV-01 and INV-03) to defined values and align the Pipeline Mapping Summary wording.
- **Out-of-Scope**:
  - Writing new tests for the ADR-004 invariants.
  - Changing any Gate value or any ADR invariant.
  - Extending `check_adr_invariant_matrix.py` and reconciling ADR body versus index evidence (separate issues of the same batch).
  - Editing `governance_01_documentation-policy.md` (it states that the matrix is maintained in `adr_01_index.md`).
- **Dependencies**: N/A: none. No open issue or in-flight plan touches this document. The ADR verification-evidence and checker-extension plans of the same batch depend on the vocabulary defined here, so this Plan is implemented first.

## Background
- The matrix introduction states that a row whose Verification Status is "Not verified" is Non-Blocking. No other status value has a stated Gate effect.
- A survey of the matrix found that most rows start with "Confirmed" and none uses the literal "Not verified". Other forms are: ADR-004 INV-01 and INV-02 ("Manual review", Gate `Deployment Blocking`), ADR-004 INV-07 and INV-10 ("By phase", Gate `Deployment Blocking`), ADR-004 INV-15 and INV-16 (a manual-release-review decision, Gate `Non-Blocking`), and ADR-014 INV-01 and INV-03 (a code reference, Gate `Non-Blocking`). The Gate values in use are `Blocking`, `Deployment Blocking` and `Non-Blocking`.
- No tool depends on the status vocabulary: `check_adr_invariant_matrix.py` extracts only backtick-quoted test node IDs from the status column.
- `adr_01_index.md` is close to the documentation size gate (about 2.5 KB of headroom).

## Problem
For a partially or manually verified invariant with a Blocking Gate, it is undefined whether the Gate is met, whether only the unverified part falls back to a manual gate, and whether merge or deployment is blocked. Reviewers can judge the same row differently, and a Blocking invariant can silently behave as a warning.

## Reason for Change
The Gate column is the mechanism that makes an Accepted ADR enforceable. An undefined case weakens that mechanism for the ADR-004 fail-fast invariants, which are Deployment Blocking.

## Implementation Intent
Keep the existing Gate values and the existing "Not verified is Non-Blocking" rule. Add a compact definition of the status vocabulary next to the matrix, in the maintained source `adr_01_index.md`, and state the Gate effect of each value. Recommended rule for Partial and Manual rows with a Blocking Gate: the Gate is unchanged, and the row MUST state the unverified scope or manual procedure and the Owner. Do not lower any Gate and do not change any invariant statement.

## Requirements
- `REQ-001`: Define the Verification Status values (Confirmed, Partial, Manual, Not verified) and the Gate effect of each in the matrix introduction of `adr_01_index.md`, keeping the existing "Not verified is Non-Blocking" rule.
- `REQ-002`: Define the mandatory content of a Partial row and of a manually verified Blocking row: the unverified scope or manual procedure, and an Owner.
- `REQ-003`: Update the ADR-004 INV-07, INV-10, INV-01 and INV-02 rows to the defined form, keeping their Gate and invariant statement.
- `REQ-004`: Map the ADR-004 INV-15 and INV-16 and the ADR-014 INV-01 and INV-03 rows to defined values and align the Pipeline Mapping Summary wording with the vocabulary.
- `REQ-005`: Keep every existing Gate value and invariant statement, keep the file within the documentation size gate, and leave the checkers without findings.

## Implementation Target Files
**Freeze status**: Frozen (validated by `issue-to-plan` Step 8's
Implementation Target Files Validation — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_01_index.md` | ADR index: matrix introduction, matrix rows, Pipeline Mapping Summary | Add the status vocabulary and Gate effects; update the ADR-004 rows and the non-standard rows | REQ-001 to REQ-005; AC-1 to AC-5 | `## ADR Invariant Verification Matrix` introduction defines only "Not verified" as Non-Blocking; the ADR-004 INV-07 and INV-10 row starts with "By phase"; `### Pipeline Mapping Summary` lists them as partial (checked in Step 3) | `tests/tools/test_check_adr_invariant_matrix.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | States that the matrix is maintained in the index and defines the Merge Conditions the Gate feeds | REQ-001 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | ADR-004 invariants and its own Verification section behind the rows | REQ-003, REQ-004 |
| `tools/check_adr_invariant_matrix.py` | Confirms the checker reads only test node IDs from the status column | REQ-005 |
| `tools/check_docs_structure.py` | Defines the size gate that bounds the added text | REQ-005 |

## Acceptance Criteria
- AC-1 (REQ-001): The vocabulary and the Gate effect of every status value are stated once, in `adr_01_index.md`, and the "Not verified is Non-Blocking" rule is preserved.
- AC-2 (REQ-002): Each Partial row and each manually verified Blocking row names its unverified scope or manual procedure and an Owner.
- AC-3 (REQ-003): ADR-004 INV-07, INV-10, INV-01 and INV-02 keep their Gate and satisfy the row rule of their status value.
- AC-4 (REQ-004): Every matrix row uses a defined status value, and the Pipeline Mapping Summary uses the same words.
- AC-5 (REQ-005): No Gate value or invariant statement changed, `adr_01_index.md` stays within the size gate, and the checkers under Tests pass.

## Tests
- `uv run python tools/check_adr_invariant_matrix.py` and `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -q` (REQ-005).
- `uv run python tools/check_adr_preservation.py` and `uv run python tools/check_adr_structure.py` (REQ-005).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py docs/10_adr/adr_01_index.md`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` (REQ-001 to REQ-005).

## Documentation Impact
Yes. `docs/10_adr/adr_01_index.md` changes (status vocabulary, Gate effects, row requirements: verification boundary and gate failure behavior); REQ-001 to REQ-005 drive it. `governance_01` is not changed. All text is written in English.

## Assumptions
- A distinct Manual value is the recommended design (UNK-01); if the owner prefers to treat manual rows as a form of Partial, the same required content applies.
- The Owner of a row is `Repository owner` unless the ADR names another.
- The definitions can fit in the size headroom, possibly after shortening the verbose ADR-004 INV-07 and INV-10 status prose without removing its evidence (UNK-02).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Should a manually verified Blocking row be a distinct status value (Manual) or a form of Partial? | No stated owner decision | Record the repository owner's decision on this plan before the edit, per the sign-off channel of `rules/coding.md` Explicit sign-off gates | False |
| UNK-02 | Do the added definitions fit within the size gate of `check_docs_structure.py`? | The final text does not exist yet | Measure with `wc -c` and `check_docs_structure.py`; if over, shorten existing status prose without dropping evidence | False |
| UNK-03 | Should a Partial row carry an expiry date or review deadline in addition to the Owner? | No stated preference | The recommendation omits it; the repository owner decides while reviewing the edit | False |
| UNK-04 | Should `governance_01` Merge Conditions state the effect of a partially verified Blocking row directly? | No stated preference | Keep the matrix as the single definition; add a pointer only if the owner asks (a separate change) | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_01_index.md` | Modify | Medium | 18 | N/A | not applicable (rsynced) |

## Design
- Path A: one documentation file, no public interface, no schema. Validation baseline is `N/A: no Python target`.
- Decision: define the vocabulary in the index (the maintained source of the matrix), not in `governance_01`. Alternative rejected: defining it in `governance_01`, which delegates the matrix to the index and would split the definition from the data.
- Decision: keep Gate values unchanged; a Partial or Manual row with a Blocking Gate stays Blocking, and the row records what is not automatically verified, the manual procedure and the Owner.
- The index is referenced by 16 files and had 18 commits in 30 days; the headroom under the size gate is about 2.5 KB, so the definitions are written compactly.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Define the vocabulary**
   - [ ] Add the status values and Gate effects, and the required row content, to the matrix introduction (REQ-001, REQ-002; `docs/10_adr/adr_01_index.md`)
2. **Phase 2: Align the rows**
   - [ ] Update the ADR-004 INV-07, INV-10, INV-01 and INV-02 rows (REQ-003; `docs/10_adr/adr_01_index.md`)
   - [ ] Map ADR-004 INV-15, INV-16 and ADR-014 INV-01, INV-03 and align the Pipeline Mapping Summary (REQ-004; `docs/10_adr/adr_01_index.md`)
3. **Phase 3: Verification (no deployment)**
   - [ ] Measure the file size, run the checkers under Tests and review any `check_adr_preservation.py` report (REQ-005; `docs/10_adr/adr_01_index.md`). No `scripts/` or `config/` file changes, so no deploy step applies.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/adr_01_index.md` | Matrix checker and its tests | `check_adr_invariant_matrix.py`; `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -q` | No finding; tests pass |
| `docs/10_adr/adr_01_index.md` | Preservation and structure | `check_adr_preservation.py`; `check_adr_structure.py` | No ERROR; Gates and invariants unchanged |
| `docs/10_adr/adr_01_index.md` | Documentation checks and size gate | `check_docs_quality.py`; `check_docs_structure.py` (changed file); `check_docs_content_policy.py --strict`; `check_docs_japanese.py` | No finding; size within the ceiling |

## Risks
- **Risk**: The added text exceeds the size gate of `check_docs_structure.py` → **Mitigation**: Write compact definitions, measure early, and shorten verbose status prose without dropping evidence; do not raise the ceiling.
- **Risk**: A Gate or invariant statement changes by accident → **Mitigation**: Edit only the introduction and status cells, and run `check_adr_preservation.py`.
- **Risk**: The vocabulary conflicts with the ADR verification-evidence plan of the same batch → **Mitigation**: This Plan is implemented first, and that Plan uses the values defined here.
- **Risk**: The index is edited by other work (18 commits in 30 days) → **Mitigation**: Make one small commit and re-run the checkers after any sync.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define the status vocabulary and Gate effects | Pending | — | — | |
| 2 | Align the ADR-004 rows and the other non-standard rows | Pending | — | — | |
| 3 | Measure size and run the documentation checkers (no deployment) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-101850_govrev003_partial-verification-gate-rules.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-104411
- **Related target files**: `docs/10_adr/adr_01_index.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (define each status and Gate effect); Implementation Intent | `docs/10_adr/adr_01_index.md` | Phase 1 | AC-1 | `check_adr_invariant_matrix.py`; `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes (mandatory Partial and Manual row content) | `docs/10_adr/adr_01_index.md` | Phase 1 | AC-2 | `check_docs_quality.py` | Derived from confirmed evidence |
| REQ-003 | Required Changes (update ADR-004 rows); Constraints | `docs/10_adr/adr_01_index.md` | Phase 2 | AC-3 | `check_adr_preservation.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes (map rows; align Pipeline Mapping Summary) | `docs/10_adr/adr_01_index.md` | Phase 2 | AC-4 | `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-005 | Constraints; Acceptance Criteria; Testing Expectations | `docs/10_adr/adr_01_index.md` | Phase 3 | AC-5 | `check_docs_structure.py` (size gate); checkers under Tests | Confirmed by repository evidence |
