## Goal
Bring `check_docs_structure.py` back to exit 0 with no size findings by reconciling the two
currently-drifting documents (`adr_02_04_006`, `adr_02_03_012`) with their recorded
ceilings. The three documents this Issue originally named (`adr_02_01_004`, `adr_02_05_008`,
`deployment_01`) were already re-recorded by adrrev014/adrrev015 (2026-11-12/13) and sit at or
below their ceilings; the drift the Issue described has since moved to two other files.

## Priority
Medium

## Scope
- **In-Scope**:
  - Re-record the `adr_02_04_006` `SIZE_EXCEPTIONS` ceiling from 30064 to 30069 in
    `tools/check_docs_structure.py`, with a dated comment naming the commit and grown content.
  - Condense `adr_02_03_012` back under the 24576 default limit by trimming prose that
    duplicates other sections, preserving every protected section verbatim.
  - Bump the `check_docs_structure.py` row in `tools/check_module_size_tools_baseline.txt` to
    the checker's new byte size if the dated comment grows it past its current baseline.
  - Re-run `check_docs_structure.py` and confirm zero findings.
- **Out-of-Scope**:
  - The three originally-named files (`adr_02_01_004`, `adr_02_05_008`, `deployment_01`):
    already re-recorded by adrrev014/adrrev015 and stable; not modified here.
  - No change to `MAX_SIZE`; no new `SIZE_EXCEPTIONS` entries; no splitting of
    `tools/check_docs_structure.py`.
  - No edits to invariant, normative-keyword, Implementation Reference, Known Deviation, or
    Approval text in either ADR.
  - No change to `scripts/`, tests, or `config/`.
  - The paused Plans `plans/20261111-104605_adrrev016_adr-authority-format.md` and
    `plans/20261111-110144_adrrev017_docs-history-wording.md`.
  - ADR-013 (`adr_02_04_013`): its ceiling was re-accepted at 28647 on 2026-11-11 (since
    re-accepted at 31478 by 2026-11-15) and must not be changed here.
- **Dependencies**:
  - Sequencing note only (not a blocking dependency): `issues/20261111-163903_deploydoc001_lifecycle-deployment-docs.md`
    (active) also touches `docs/90_deployment/`. This Plan does not modify
    `deployment_01_deployment.md` (already stable at 27339 == its ceiling), so no ordering
    constraint applies. Recorded here because the Issue listed it.

## Background
Each `SIZE_EXCEPTIONS` entry in `tools/check_docs_structure.py` carries a dated comment stating
that "the ceiling equals the accepted size, so further growth fails". When a document grows
past its recorded ceiling without the ceiling being re-accepted, the drift lands silently and
the "further growth fails" contract stops being enforced at the intended size.
`20261001-104656_docsize001` and `20261001-125058_adrsize001` (both in `issues/done/`) are the
earlier lineage of the same gate; this Issue was filed 2026-11-11 to close three such drifts.
adrrev014/adrrev015 re-recorded those three on 2026-11-12/13, after this Issue was opened.

Adversarial-verification update (2026-11-15): both findings quoted in Problem are closed at
HEAD by maintainer commit `bca9ec63f` ("chore(tools): re-record docs size ceilings for db_07
fix and pre-existing ADR drift", 2026-11-15): the `adr_02_04_006` ceiling is re-recorded at
30069 with a dated comment naming `23ca93846` (rmcompat005, INV-08 verification row + events
column), and `adr_02_03_012` now carries a `SIZE_EXCEPTIONS` entry of 25253 with a dated
comment closing the `a66077b4f` gate drift. `check_docs_structure.py` exits 0 with no size
findings, and the `check_docs_structure.py` baseline row is 32352, matching the checker's
current size. The condensation path chosen for `adr_02_03_012` is superseded by the maintainer's
re-record decision (commit notes "closing gate drift only; no ADR content changed"); this Plan's
remaining cycle is verification-only and edits no file.

## Problem
`tools/check_docs_structure.py` exits 1 at HEAD with two size findings on files this Issue never
named:

```
adr_02_03_012_mcp-git-server-side-write-enforcement.md: size 25253 bytes exceeds 24576 byte limit
adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md: size 30069 bytes exceeds 30064 byte limit
```

Because the gate exits 1 for reasons unrelated to the change under review, every procedure that
runs `check_docs_structure.py` in its Validation plan gets a red signal it cannot fix within its
own scope and cannot tell whether its own edits are what broke the gate. The recorded ceiling for
`adr_02_04_006` (30064) no longer describes reality (the file is 30069 B), so the contract is not
enforced at the intended size.

## Reason for Change
The Issue hit the same shape of failure before: adrrev010's ADR-013 sat exactly at its ceiling
and its mandated wording grew it past, resolved by re-recording the ceiling with a dated comment.
Resolving only one file leaves the other finding in place, so the checker still fails for the
next procedure. Both current findings are the same drift class the Issue was created to close.

## Implementation Intent
Resolve each file once, one resolution per file, choosing the accepted resolution the file's
state calls for:

- `adr_02_04_006` has an existing `SIZE_EXCEPTIONS` entry and grew 5 B (30064 -> 30069) by real,
  owner-intended content (rmcompat005's INV-08 verification-row update + events column list).
  Re-record the existing ceiling to 30069 with a dated comment. The document itself is not edited.
- `adr_02_03_012` has no `SIZE_EXCEPTIONS` entry and sits at 25253 B, over the 24576 default. The
  Issue's "no new exceptions" constraint forbids adding one, so condense the document back under
  24576 by trimming prose that duplicates other sections. Invariants, normative keywords,
  Implementation References, Known Deviations, and Approval records stay intact.

Do not raise `MAX_SIZE` and do not remove an entry. Each re-recorded ceiling equals the accepted
size exactly, so later growth fails again.

## Requirements
- `REQ-001`: After the change, `uv run python tools/check_docs_structure.py` exits 0 and prints no
  size findings.
- `REQ-002`: `adr_02_04_006`'s `SIZE_EXCEPTIONS` ceiling equals its accepted size (30069) with a
  dated comment naming the commit and the content that grew.
- `REQ-003`: `adr_02_03_012` sits at or below 24576 B; its Invariants, normative keywords,
  Implementation References, Known Deviations, and Approval records are unchanged in meaning.
- `REQ-004`: `tools/check_docs_structure.py` stays within its `tools/` baseline; if the dated
  comment grows it past 30619 B, the `check_docs_structure.py` row in
  `tools/check_module_size_tools_baseline.txt` is bumped to the new size exactly.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Modify | Condense 677+ B of duplicate prose (Consequences/Rationale restating Invariants) back under the 24576 default limit; no `SIZE_EXCEPTIONS` entry exists, so condensation is the only compliant resolution. | REQ-003, AC-3 | 25253 B at HEAD; 17842 -> 25253 B in `a66077b4f` (authority-model batch); Consequences (L104-126) duplicates Invariants (L128-139) and Rationale (L76-88). (checked in Step 3) | none — documentation-only | Verified |
| `tools/check_docs_structure.py` | Modify | Re-record the `adr_02_04_006` `SIZE_EXCEPTIONS` ceiling 30064 -> 30069 with a dated comment. Document is not edited; only the checker's recorded ceiling changes. | REQ-002, AC-2 | 30069 B at HEAD vs recorded 30064; +5 B from `23ca93846` (rmcompat005, INV-08 verification-row + events column). (checked in Step 3) | none — documentation-only | Verified |
| `tools/check_module_size_tools_baseline.txt` | Modify | Bump the `check_docs_structure.py` row to the checker's new byte size if the dated comment grows it past the current 30619 B baseline. | REQ-004, AC-6 | `check_docs_structure.py` is exactly at baseline (30619 B); the dated comment will grow it. (checked in Step 3) | none — documentation-only | Verified |

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
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Confirm current size (30069 B) and identify the +5 B grown content (rmcompat005 INV-08 verification-row + events column) before re-recording the ceiling. | `tools/check_docs_structure.py` (REQ-002) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Confirm it remains at/below its ceiling (34555 == 34555) so the gate stays green after this Plan. | `tools/check_docs_structure.py` (REQ-001) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Confirm it remains at/below its ceiling (37291 == 37291 as of 2026-11-15; re-recorded from 36189 < 36570 by later approved growth). | `tools/check_docs_structure.py` (REQ-001) |
| `docs/90_deployment/deployment_01_deployment.md` | Confirm it remains at/below its ceiling (27339 == 27339). | `tools/check_docs_structure.py` (REQ-001) |
| `skills/DESIGN.md` | Docs content policy ("Avoid implementation-reference duplication", "Docs content policy — remove") that bounds which `adr_02_03_012` prose may be trimmed. | `docs/10_adr/adr_02_03_012...` (REQ-003) |

## Acceptance Criteria
- `AC-01` (REQ-001): `uv run python tools/check_docs_structure.py` exits 0 and prints no size findings.
- `AC-02` (REQ-002): `adr_02_04_006`'s `SIZE_EXCEPTIONS` ceiling is 30069 with a dated comment naming commit `23ca93846` (rmcompat005) and the INV-08 verification-row / events-column growth.
- `AC-03` (REQ-003): `adr_02_03_012` is at or below 24576 B; Invariants, normative keywords, Implementation References, Known Deviations, and Approval records are unchanged in meaning.
- `AC-04` (REQ-003): `uv run python tools/check_adr_preservation.py` reports no ERROR against `HEAD` for both ADRs; any reduction is accompanied by a sentence-level mapping for the sections it flags.
- `AC-05` (REQ-003): `uv run python tools/check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`, `check_docs_consistency.py --domain eventbus`, and `check_docs_consistency.py --domain workflow` pass.
- `AC-06` (REQ-004): `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` exits 0.

## Tests
Documentation-only change: no unit or integration test changes. Verification is the
documentation checkers in `AC-01`–`AC-06` plus `check_module_size.py` for the `tools/` side.
Manual check: diff each document against `HEAD` and confirm no normative or approval text
changed.

## Documentation Impact
The change is inside the two documents themselves plus the ceiling comments in
`tools/check_docs_structure.py`. No new document is created. If condensation is chosen for
`adr_02_03_012`, its `Known Deviations` and `Review Triggers` sections must stay consistent with
what was removed. The affected document lives in the ADR area (`docs/10_adr/`), mapped to the
architecture/ADR task in `docs/00_index.md` "Document References by Task".

## Assumptions
- The +5 B growth in `adr_02_04_006` (rmcompat005, `23ca93846`) is owner-intended, real
  content (an INV-08 verification-row update + events column list), so re-recording the ceiling
  is correct rather than condensing 5 bytes of genuine detail.
- At least 677 B of duplicate prose exists in `adr_02_03_012`'s Consequences/Rationale to clear
  24576 without touching protected sections: the Security Consequences bullets restate INV-01/
  INV-07 and Decision Details, and the Ongoing Risks bullets restate INV-01/07/08/09.
- The three originally-named files remain at/below their ceilings (34555 / 36189 < 36570 /
  27339) and are not modified by other in-flight work.
- No active Plan modifies `adr_02_03_012` or `adr_02_04_006` before this Plan runs.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which specific duplicate-prose slices in `adr_02_03_012` to trim first to land just under 24576 B without over-condensing legitimate authority-model detail added by `a66077b4f`. | None blocking: the duplicate slices are identifiable (Consequences restating Invariants). | Trim the Security Consequences and Ongoing Risks bullets first (they duplicate Invariants verbatim in meaning), then re-measure; stop as soon as the file is at or below 24576 B. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Modify | Low | N/A | N/A | none (docs-only) |
| `tools/check_docs_structure.py` | Modify | Medium | N/A | N/A | none (docs-only; gate other procedures depend on) |
| `tools/check_module_size_tools_baseline.txt` | Modify | Low | N/A | N/A | none (docs-only) |

## Design
Path A (≤ 3 modification-target files, no public/runtime interface change, no DB schema): skip
architecture/dependency/historical analysis. The design choice is per-file resolution selection,
grounded in the Issue's own constraints:

- `adr_02_04_006` → re-record. It has an existing `SIZE_EXCEPTIONS` entry and grew by real
  content; re-recording the existing ceiling (not adding a new one) is the Issue's primary
  accepted resolution and keeps the "no new exceptions" constraint.
- `adr_02_03_012` → condense. It has no `SIZE_EXCEPTIONS` entry and sits over the default limit;
  the Issue's "no new exceptions" constraint forbids adding one, so condensation is the only
  compliant path. The authority-model expansion (`a66077b4f`, +7411 B) added legitimate
  verification detail that lives in the Automated Tests table, which stays intact; condensation
  trims only the duplicate prose in Consequences/Rationale.

Both resolutions preserve every protected section verbatim and set each ceiling to the accepted
size exactly, so the "further growth fails" contract is restored.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Re-record the `adr_02_04_006` ceiling** (`tools/check_docs_structure.py`, REQ-002 / AC-02)
   - [ ] Open the `SIZE_EXCEPTIONS` dict and locate the `adr_02_04_006` entry (currently 30064).
   - [ ] Replace the value with 30069 and append a dated comment naming commit `23ca93846`
     (rmcompat005) and the INV-08 verification-row / events-column growth that pushed the file
     30064 -> 30069, matching the existing comment convention ("the ceiling equals the accepted
     size, so further growth fails").
   - [ ] Do not touch any other entry, `MAX_SIZE`, or the document itself.
2. **Phase 2: Condense `adr_02_03_012` under 24576 B** (`docs/10_adr/adr_02_03_012...`, REQ-003 / AC-03, AC-04)
   - [ ] Confirm the current size (25253 B) and that no other Plan is editing it.
   - [ ] Trim prose in the Consequences section (Security Consequences and Ongoing Risks bullets
     that restate Invariants/Rationale) and any other duplicated prose, per `skills/DESIGN.md`
     Docs content policy, stopping as soon as the file is at or below 24576 B.
   - [ ] Preserve Invariants, normative keywords, the Automated Tests table, Implementation
     References, Known Deviations, and Approval Record verbatim in meaning.
   - [ ] Confirm `check_adr_preservation.py` reports no ERROR against `HEAD`; map any flagged
         reduction sentence-level.
3. **Phase 3: Baseline bookkeeping and verification** (`tools/check_module_size_tools_baseline.txt`, `tools/check_docs_structure.py`, REQ-004 / AC-01, AC-06)
   - [ ] Re-measure `tools/check_docs_structure.py`; if the dated comment grew it past 30619 B,
     bump the `check_docs_structure.py` row in `tools/check_module_size_tools_baseline.txt` to
     the new byte size exactly.
   - [ ] Re-run `uv run python tools/check_docs_structure.py` and confirm zero findings.
   - [ ] Run `check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`,
     `check_docs_consistency.py --domain eventbus`, `check_docs_consistency.py --domain workflow`,
     and `check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.
   - [ ] Diff both documents against `HEAD` and confirm no normative or approval text changed.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_docs_structure.py` | Gate re-run | `uv run python tools/check_docs_structure.py` | Exit 0, no size findings (AC-01) |
| `tools/check_module_size_tools_baseline.txt` | Size baseline | `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Exit 0 (AC-06) |
| `adr_02_03_012` | ADR preservation | `uv run python tools/check_adr_preservation.py` | No ERROR against `HEAD` (AC-04) |
| `adr_02_03_012`, `adr_02_04_006` | Docs quality/content/language | `uv run python tools/check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_japanese.py` | Pass (AC-05) |
| affected docs | Domain consistency | `uv run python tools/check_docs_consistency.py --domain eventbus` and `--domain workflow` | Pass (AC-05) |

## Risks
- **Risk**: Condensing `adr_02_03_012` removes prose that, while duplicative in meaning, carries
  audit/traceability wording that `check_adr_preservation.py` or a future checker may expect. →
  **Mitigation**: Only trim text whose meaning is fully restated elsewhere (Invariants/Rationale);
  keep every invariant bullet, the Automated Tests table, Implementation References, Known
  Deviations, and Approval Record intact; re-run `check_adr_preservation.py` and the docs checkers
  after each edit.
- **Risk**: The dated comment for `adr_02_04_006` grows `tools/check_docs_structure.py` past its
  `tools/` baseline and `check_module_size.py` fails. → **Mitigation**: Phase 3 re-measures the
  checker and bumps the baseline row to the exact new size.
- **Risk**: Another in-flight Plan edits `adr_02_03_012` or `adr_02_04_006` concurrently, making
  the recorded sizes stale. → **Mitigation**: Step 2 confirms no active Plan owns these files
  before editing; if one appears, sequence after it.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-record the `adr_02_04_006` ceiling in `tools/check_docs_structure.py` (30064 -> 30069) with a dated comment. | Completed | — | 20261115 | Already done at HEAD by maintainer commit `bca9ec63f` (2026-11-15), whose dated comment names `23ca93846` (rmcompat005) and the INV-08 verification-row / events-column growth. Verified 20261115. |
| 2 | Condense `adr_02_03_012` under 24576 B by trimming duplicate prose, preserving protected sections. | Completed | — | 20261115 | Superseded at HEAD: `bca9ec63f` instead re-recorded the ceiling to 25253 (dated comment closing the a66077b4f gate drift); the maintainer chose re-record over condensation, so no document edit is due. Verified: size 25253 == ceiling. |
| 3 | Bump the tools baseline if the checker grew, re-run the gate, and run all docs checkers. | Completed | — | 20261115 | Gate verified at HEAD: `check_docs_structure.py` exits 0 with no size findings; checker 32352 B == baseline row 32352. Stale-at-plan-time figures (`adr_02_05_008` 36189, `adr_02_04_013` 28647, baseline 30619) were since re-recorded (37291 / 31478 / 32352); gate stays green. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261115-201501_02_tools_check_docs_structure.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261115-201501_01_docs_10_adr_adr_02_03_012_mcp-git-server-side-write-enforcement.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261115-201501_03_tools_check_module_size_tools_baseline.txt.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261111-224650_docsize002_re-record-drifted-docs-size-ceilings.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-073403
- **Related target files**: `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `tools/check_docs_structure.py`, `tools/check_module_size_tools_baseline.txt`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Summary, Background | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | 3 | AC-01 | `check_docs_structure.py` | Confirmed by repository evidence |
| REQ-001 | Summary, Background | `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | 2 | AC-01 | `check_docs_structure.py` | Confirmed by repository evidence |
| REQ-001 | Summary, Background | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | 1 | AC-01 | `check_docs_structure.py` | Confirmed by repository evidence |
| REQ-001 | Summary, Background | `docs/90_deployment/deployment_01_deployment.md` | 3 | AC-01 | `check_docs_structure.py` | Confirmed by repository evidence |
| REQ-002 | Background (adr_02_04_006 drift) | `tools/check_docs_structure.py` | 1 | AC-02 | `check_docs_structure.py` | Confirmed by repository evidence |
| REQ-003 | Summary, AI Implementation Instruction | `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | 2 | AC-03, AC-04 | `check_adr_preservation.py`, `check_docs_quality.py`, `check_docs_consistency.py` | Confirmed by repository evidence |
| REQ-004 | Background (baseline contract) | `tools/check_module_size_tools_baseline.txt` | 3 | AC-06 | `check_module_size.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261115-201501 -->
