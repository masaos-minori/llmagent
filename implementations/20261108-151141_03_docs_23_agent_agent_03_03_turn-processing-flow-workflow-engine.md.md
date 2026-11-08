# Implementation procedure: docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md

## Goal
State the strict loader contract in the existing "### Workflow Loader Validation Rules" section: stage elements and
`retry_policy` must be JSON objects, and `retryable` must be a strict JSON bool.

## Scope
**Release unit**: wfaudit004-full
**Phases:** 2 (entry-point consistency + docs, `REQ-005` docs row)
**Covers Plan target file row**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` (`Modify`,
`REQ-005`; added to the plan 2026-11-08 via `tools/amend_plan.py`, class `scope`)
- Only the "### Workflow Loader Validation Rules" section (L148-158) of this file changes.
- Documentation-only change; no code in this procedure.

## Assumptions
- The section "### Workflow Loader Validation Rules" exists at L148-158 of the target file, with its current bullets
  quoted verbatim in Method below (quoted at HEAD `ad48bfa28`). Plan Implementation Target Files row (`Verified`).
- The loader contract described by the new bullets is implemented by `implementations/20261108-151141_01_scripts_agent_workflow_workflow_loader.py.md`
  (earlier-seq sibling in this pass, `REQ-001`-`REQ-004`); this document describes post-change state and depends on
  that procedure landing first (Plan Execution Status: same Phase 1/2 batch).
- The docs `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` file is not edited by any other
  procedure of this timestamp batch (only 151141_03 names it). Plan Implementation Target Files.

## Design decisions
- Extend the existing bullet list rather than adding a new subsection: the section already owns the loader's field
  contract (numeric fields, `retry_on`), and `skills/DESIGN.md` Output language keeps docs in English. Plan row
  (amendment record).
- Wording states the contract as behavior (what the loader refuses), not implementation helper names — consistent
  with the section's current style ("The loader refuses invalid values before construction"). Quoted section text at HEAD.

## Alternatives considered
- No docs change (plan's original conditional) — rejected: the plan's condition "if a loader contract section exists"
  resolved to true (section at L148-158), so the amendment added this row; leaving the contract undocumented would
  contradict the plan.
- Documenting in `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` — rejected: that doc covers
  state persistence, not workflow definition loading; the workflow engine doc is the canonical loader contract location.

## Security considerations
N/A: documentation-only change.

## Compatibility considerations
- Adding strictness statements to a "Validation Rules" section: the statements become the documented contract only
  after the seq-01 loader change lands; sequencing within the wfaudit004 batch (Phase 1 loader + tests, Phase 2 this
  docs row) keeps docs and behavior consistent.
- No code, API, schema, migration, or config compatibility impact.

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

**Fix notes (20261108-151141): target path verified as `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` by the Plan target row (amended 2026-11-08) and the section quoted below at L148-158.**

### Change responsibility
Edit only the bullet list under "### Workflow Loader Validation Rules" (L148-158): extend existing bullets and add
two new ones.

### Method

**Step 1 — amend the stage-fields bullet (first bullet, L152).** Current text, quoted verbatim from HEAD `ad48bfa28`:
> - A definition must have a non-empty list of uniquely identified stages, which must include `plan`, `execute`, and
>   `verify`; each stage declares `timeout_sec` and `retryable`, with `timeout_sec` an integer of at least 1

Replace with (single bullet, rest of wording intact):
> - A definition must have a non-empty list of uniquely identified stages, which must include `plan`, `execute`, and
>   `verify`; each stage must be a JSON object and declares `timeout_sec` and `retryable`, with `timeout_sec` an
>   integer of at least 1 and `retryable` a boolean (not a string, number, or null)

**Step 2 — insert one new bullet immediately after the numeric `retry_policy` bullet (second bullet, L153).** Current
second bullet for location reference (not reworded):
> - `retry_policy.max_attempts` and `retry_policy.backoff_sec` must both be integers, not booleans, floats, or
>   strings, with `max_attempts` at least 1 and `backoff_sec` at least 0

New bullet:
> - Each stage must be an object and `retry_policy`, when present, must itself be an object; a stage or
>   `retry_policy` of any other JSON type stops loading with a workflow load error that names the field

**Step 3 — append one sentence to the error-type bullet (third bullet, L154).** Current text, quoted verbatim:
> - A value that fails this validation stops loading with a workflow load error that names the field and the
>   offending value, so every caller observes the same error type

Replace the trailing clause with: "so every caller observes the same error type, including the startup preflight
`check_workflow_definition`, which reports the refusal as a `RuntimeError` whose `__cause__` is the workflow load
error."

**Step 4 — verify surrounding text.** The section intro line ("When loading workflow definitions from
`config/workflows/*.json`:"), the `retry_policy.retry_on` bullet, the `require_approval` bullet, and the "See also"
line are not reworded and stay byte-identical.

### Details
- Match the file's existing bullet indentation and backtick style; the section is Markdown with inline-code field names.
- No heading-level changes; the section keeps its `###` level so `check_docs_claims.py` heading extraction is unaffected.

## Rollback considerations
- Single-file docs change: `git checkout -- docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
  restores HEAD `ad48bfa28`. No code, config, or service impact.

## Validation plan
- Read-back: quote the final bullets and diff against the Method quote blocks.
- Docs checkers per `routing.md` Tools ("When to run which tool") for any `docs/*.md` edit:
  `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py
  'docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md'`,
  `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`, and
  `uv run python tools/check_docs_consistency.py --domain agent` (the touched doc is in the `agent` domain); all exit 0.
- `uv run python tools/stale_detector.py implementations/20261108-151141_03_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`
  after the edit (the quoted section text resolves against HEAD; the sibling loader procedure marks its planned-new symbols).

## Completion criteria
1. The section states: stage elements must be JSON objects; `retry_policy` must be a JSON object; `retryable` must be
   a JSON bool with non-bool values refused.
2. The startup-preflight error-wrapping statement matches the implemented behavior (seq-01 + seq-02 tests).
3. All other bullets (numeric `retry_policy` bullet, `retry_policy.retry_on` bullet, `require_approval` bullet), the
   section intro, and the "See also" line are byte-identical to HEAD except the Step 1 amendment, the Step 2 added
   bullet, and the Step 3 appended sentence.
4. Docs checkers exit 0.

## Out of Scope
- Any other section of this file; any other docs file.
- Loader code and tests (own procedure documents 151141_01/02).

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the Validation Rules bullets (Steps 1-3) | Pending | — | — | |
| 2 | Run docs checkers (`check_docs_claims.py`, `check_docs_diagrams.py`) and stale_detector | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (docs row added 2026-11-08 by `tools/amend_plan.py`, class `scope`)
- **Source issue**: `issues/20261107-203217_wfaudit004_loader-validation-gaps.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084007_wfaudit004_loader-validation-gaps.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-151141
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

<!-- tools/generate_workitem.py implementation-procedure 20261108-151141_03 from plans/20261108-084007_wfaudit004_loader-validation-gaps.md -->
