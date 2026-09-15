## Goal
State a concrete guideline for "bloat" in `prompts/08_document-sync.md` line 212
(REQ-004).

## Scope
In scope: the "Use concise, professional Markdown. Do not bloat the documents." bullet
under the "Style" heading. Out of scope: the other 2 bullets under the same "Style"
heading and "Separate document content from synchronization history" bullets above
it; any other section of this file.

## Assumptions
- Adding one short guideline clause will not push this file over the 400-line File
  Split Rule trigger in `skills/DESIGN.md`.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), the guideline reuses the immediately-preceding "Separate document
content from synchronization history" distinction already stated in this same file
(target documents vs. `docs/99_documentation_sync_report.md`) as the operational test
for "bloat," rather than inventing an unrelated line-count number, per the Plan's own
Implementation Intent (a rough line-count ceiling per section, OR "no content already
fully covered by a source reference" — the latter fits this file's own adjacent
distinction more naturally than an arbitrary line count would).

## Alternatives considered
- A rough numeric line-count ceiling per section (the Plan's own alternative
  suggestion) — considered, but rejected in favor of the content-based test below,
  since this file already draws a content-based line (target-document content vs.
  sync-report content) two bullets above the target line, making a content-based
  "bloat" test the more consistent, already-modeled choice for this specific file.

## Implementation
### Target file
prompts/08_document-sync.md

### Procedure
1. Open the "Style" heading, locate "Use concise, professional Markdown. Do not
   bloat the documents." (line 212).
2. Append a concrete guideline for what counts as bloat.
3. Leave the other 2 "Style" bullets and all surrounding content unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full bullet line
(unique in the file), appending the guideline at its end.

### Details
Change:
`- Use concise, professional Markdown. Do not bloat the documents.`
to:
`- Use concise, professional Markdown. Do not bloat the documents — content already
covered by a source-code/config reference, or by the synchronization history in
\`docs/99_documentation_sync_report.md\`, does not belong in the target document; keep
the target document to design intent, boundaries, constraints, and operational notes
only (see "Separate document content from synchronization history" above).`

Do not alter the "Output language" bullet or the "Separate document content from
synchronization history" bullets above the target line.

## Compatibility considerations
This file is referenced by 4+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected — this is a prompt/workflow
entry-point file, and the change only clarifies an existing style rule.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to one bullet; revertable independently of
the other 7 documents in this pass via `git checkout -- prompts/08_document-sync.md`
(pre-commit) or a follow-up commit reverting this file only.

## Validation plan
- `git diff prompts/08_document-sync.md` — confirm only the named bullet's appended
  clause changed, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/`/`docs/` reference was introduced (the new clause
  references `docs/99_documentation_sync_report.md` by name).

## Completion criteria
The "Do not bloat the documents" bullet states a concrete, content-based guideline;
the bullet's original wording and the other "Style" bullets are unchanged;
`tools/check_skills_references.py` passes (Plan AC-4).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document); the other 2 "Style" bullets; any other section of
`prompts/08_document-sync.md`; any other evaluation criterion from the source review
batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-102308 | 20260915-102308 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-102308 | 20260915-102308 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-102308 | 20260915-102308 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-102308 | 20260915-102308 | N/A: no `docs/*.md` update required (this edit targets `prompts/`, not `docs/`) |

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
- **Requirement ID**: REQ-004 (state a concrete "bloat" guideline)
- **Source issue**: issues/20260914-114854_skillqa02_replace-vague-qualifiers-with-concrete-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-094354
- **Related target files**: prompts/08_document-sync.md