# Implementation Procedure Output Template (Canonical)

Use this exact Markdown structure when generating
`implementations/{timestamp}_{seq}_{target_file_slug}.md` in the
`plan-to-implementation-procedure` workflow (see
`skills/plan-to-implementation-procedure/workflow.md` Step 3). `seq` is the row's
1-indexed, zero-padded position within the plan's `Implementation Target Files` table
(`templates/plan.md`), so that sorting the generated filenames lexicographically
reproduces the plan's implementation order. One document per
`Implementation Target Files` row; a test file that qualifies as a companion is covered
by its code row's document (see the Companion test files note below) — see Notes on
filling sections below. Do not omit
any section. Write every section's body text in English, regardless of the chat
language (see `skills/plan-to-implementation-procedure/SKILL.md` Core Execution
Rules).

Keep each section concise and file-level (a few bullets each) — this is not a broad
architecture document. Use `N/A: {short reason}` for any section that does not apply
to the item.

```markdown
## Goal

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

## Design decisions

## Alternatives considered

## Implementation
### Target file
### Procedure
### Method
### Details

## Compatibility considerations

## Security considerations

## Rollback considerations

## Validation plan

## Completion criteria

## Out of Scope

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: {the Requirement ID(s) from the Plan's Implementation Target Files row this document implements, e.g. `REQ-003`}
- **Source issue**: {inherited from the target plan file's own Traceability section}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: {exact repository-relative path of the target plan file}
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {timestamp}
- **Related target files**: {target_file_path}
```

## Notes on filling sections

- **Lightweight fill for small rows** — applies when the row is a documentation-only
  change, or a code change confined to one function/section with no public-contract,
  persistence, or security impact. The section headings stay (the structure is checked
  by `tools/check_workitem_structure.py`; a qualifying test row may be a companion
  instead of its own document, otherwise the one-document-per-row invariant is
  unchanged); only the bodies shrink:
  - "Alternatives considered", "Compatibility considerations", "Security
    considerations", and "Rollback considerations" may each be one line:
    `N/A: {short reason}` (rollback for a docs-only or single-commit change may be
    `N/A: revert the commit`). Do not invoke `python-design` for them.
  - "Design decisions" holds at most 2 bullets; "Procedure"/"Method"/"Details" state
    only what a reader cannot infer from the Plan's Requirement text.
  - "Execution Status" lists only the steps that apply: a docs-only row drops the
    "Add or update tests" step and keeps the validation step as the documentation
    checkers named in `routing.md` Tools "When to run which tool".
  - Target length is about 40 lines. A row that does not fit the lightweight criteria
    above uses the full form.

- **Release unit** — the `## Scope` line carries the unit name when the Plan's `### Release units`
  entry lists the Plan step that cites this document's `File Path` in its `Phases`; the generation
  workflow copies the name from that entry. Otherwise keep the default
  `N/A: not part of a release unit`. `skills/code-implementation/workflow.md` Batch mode reads it.

- "Target file" (singular) names exactly the one `File Path` this document modifies —
  the one `Implementation Target Files` row (`templates/plan.md`) this document was
  generated from. Any other file mentioned in Procedure/Method/Details is a reference
  or verification dependency only — this document MUST NOT contain modification
  instructions for more than one file in this section; its test companions are listed in
  `### Companion test files`, not here. If implementing this item turns out to require
  modifying a second file, that is an additional-target-file discovery, not something
  to add here — see `skills/plan-to-implementation-procedure/workflow.md` Step 3.
- **Companion test files** — a code row's document may carry the test files of that row
  as companions (the eligibility conditions are in the "One target file = one procedure
  document" rule of `skills/plan-to-implementation-procedure/SKILL.md`). Add a
  `### Companion test files` heading under `## Implementation`, after `### Details`
  (outside the fenced block above, so single-target documents and the generator's
  skeleton are unchanged). Each companion is a top-level bullet whose first backticked
  token is its path, with `(new)` right after the path when the document creates it, and
  two indented bullets `Procedure:` and `Validation:` of one line each:

  ```markdown
  ### Companion test files
  - `tests/tools/test_example.py` (new)
    - Procedure: {what to add or change}
    - Validation: {how to verify}
  ```

  A document without companions omits the heading. `tools/stale_detector.py` and
  `tools/check_workitem_traceability.py` read this section.
- **Target file that this document creates** — write the word (new) in parentheses after
  the backticked path in "Target file". `tools/stale_detector.py` then skips the
  existence check for that file, requires its containing directory to exist, reports a
  file that already exists, and skips line citations that resolve to it. A target that
  does not exist and is not marked is reported as stale.
- For "Design decisions" / "Alternatives considered" / "Compatibility considerations" /
  "Security considerations" / "Rollback considerations", apply
  `skills/python-design/SKILL.md` + `skills/python-design/workflow.md` for how to
  reason about them — draw only the few relevant bullets from that skill's broader
  12-section template; do not produce its full architecture output here.
- "Execution Status" / "Blocker Log" / "Work Items Created" table structure and
  status/type vocabulary: see `templates/execution-status.md`. The rows above are this
  document's default starting set — pre-populate with the actual steps the item
  requires when the document is first created; split further if Method/Details call
  for multiple distinct sub-steps. Do not leave a single placeholder row.
- "Source issue" must carry forward the value from the target plan's own Traceability
  section — set to N/A only if the Plan's own Traceability section genuinely records
  N/A itself; never default to N/A when the Plan carries a concrete value.
- "Requirement ID" and any reference to the Plan elsewhere in this document (Goal,
  Scope) must cite the Requirement by ID plus a short (one-clause) purpose — do not
  paste the Plan's full Requirement description text.
- "Completion criteria" states the specific, checkable conditions under which this
  file-level change is done — distinct from "Validation plan" (how to verify), this is
  what verifying confirms.
- "Related target files" uses `target_file_path` (the repository-relative path), not
  `target_file_name` (its base name) — this is also what the "already implemented"
  check matches against. A document with companions lists the target first, then each
  companion, comma-separated and each backticked.
- **Marking what the procedure creates** — when a procedure names a symbol or an import
  statement that it will create (it does not exist yet), write the name in backticks and
  follow it with the word (new) in parentheses. `tools/stale_detector.py` skips the
  existence check for such a name, while a name that is absent and not marked is reported
  as stale and aborts the cycle. Only an import statement at the start of a line is
  checked as an import, so a sentence that merely mentions an import is not.
  The marker is needed only for names this document itself creates: a name that an
  earlier-`seq` procedure of the same Plan marks (new) is resolved by the detector, which
  prints a `resolved from sibling` line, so no Assumptions note is needed (only an earlier
  sibling counts by default; `--sibling-order any` and `--no-siblings` change this).
