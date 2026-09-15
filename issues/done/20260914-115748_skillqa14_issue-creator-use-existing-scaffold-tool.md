# Have issue-creator workflow Phase 10 use the existing generate_workitem.py --kind issue scaffold tool

## Priority
Medium

## Summary
`tools/generate_workitem.py --kind issue --id <id> --title <title>` already generates a correctly-named, correctly-structured issue skeleton (confirmed via `--help`: it produces the `{timestamp}_{id}_{slug}.md` filename and refuses to overwrite an existing file) — but `skills/issue-creator/workflow.md` Phase 10 does not reference this tool and instead describes a fully manual 6-step filename-generation procedure, unlike its sibling skills `issue-to-plan` and `plan-to-implementation-procedure`, which both already use `generate_workitem.py` for their own scaffolding.

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session. The review's initial finding was that issue-creator lacked any scaffolding tool entirely — re-verified during this issue's drafting and found inaccurate: the tool exists and already supports issue mode (`--kind issue`); the actual gap is narrower — `issue-creator/workflow.md` simply doesn't call it.

## Problem
Confirmed by direct reading of `skills/issue-creator/workflow.md` Phase 10 (Generate Issue Filename): it describes 6 manual sub-steps (extract/assign `{id}`, generate `{timestamp}`, derive `{slug}`, assemble the filename, verify uniqueness, retry on collision) with no reference to `tools/generate_workitem.py`, even though that tool already performs steps 1-4 and refuses to overwrite an existing file (covering step 5's uniqueness concern for the exact-match case). This is inconsistent with `skills/issue-to-plan/workflow.md` and `skills/plan-to-implementation-procedure/workflow.md`, both of which already delegate their own scaffolding to this same tool (`--kind plan` / `--kind implementation-procedure`).

## Reason for Change
A fully manual filename-assembly procedure risks the exact class of error the tool already prevents — a transcription mistake in the timestamp, id, or slug — and duplicates logic (uniqueness checking, refusal to overwrite) that already exists in one place, now needing to stay in sync by hand across three near-identical Phase-10-equivalent procedures.

## Implementation Intent
Update `issue-creator/workflow.md` Phase 10 to prefer `tools/generate_workitem.py --kind issue --id <id> --title <title>` for the initial scaffold, following the same pattern `issue-to-plan`/`plan-to-implementation-procedure` already use, then fill in the scaffold's content per Phases 3-9's drafted fields — keep the manual procedure only as an explicit fallback for when the tool is unavailable, matching those sibling skills' own fallback framing.

## Target Files or Areas
- `skills/issue-creator/workflow.md`

## Required Changes
- Add, as the primary path in Phase 10: "Prefer `uv run python tools/generate_workitem.py --kind issue --id {id} --title {title}` to scaffold the file — it generates the `{timestamp}_{id}_{slug}.md` filename and refuses (non-zero exit, no write) on a path collision rather than auto-incrementing; treat that refusal as the trigger for the retry-with-disambiguator step already described, not as a workflow failure."
- After a `0` exit, add the same independent-verification requirement `issue-to-plan`/`plan-to-implementation-procedure` already state for this tool: confirm the reported output path exists and contains the expected section headings before filling in content — a `0` exit alone is not proof of correct output.
- Retain the existing 6-step manual procedure, explicitly framed as the fallback used only if the tool is unavailable.

## Constraints
Do not change `generate_workitem.py` itself — this issue only changes which skill references it; if `--kind issue` needs a behavior change to fit `issue-creator`'s exact needs, that would be a separate issue with its own justification.

## Acceptance Criteria
- `issue-creator/workflow.md` Phase 10 names `tools/generate_workitem.py --kind issue` as the preferred scaffolding method.
- The same independent-verification step (confirm output path/section headings after a `0` exit) used by sibling skills is present here too.
- The existing manual procedure remains as an explicit fallback, not removed.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only workflow file. Run `tools/check_skills_references.py` per `routing.md`'s relevant row. As a manual smoke check, run `tools/generate_workitem.py --kind issue --id test99 --title "Test Issue"` once against a scratch path to confirm the tool's current behavior still matches what this issue describes, before finalizing the wording.

## Documentation Impact
This issue's entire scope is `skills/issue-creator/workflow.md`.

## Out of Scope
- Any change to `tools/generate_workitem.py` itself.
- Any other evaluation criterion from the same review — tracked in separate issues (`skillqa03` already covers this same file's missing Phase 3-8 completion criteria).

## Dependencies
Related to `skillqa03` (same file, different Phase) — no ordering dependency, both can be implemented independently.

## Unresolved Questions
N/A: none — the tool's issue-mode behavior was directly confirmed via `--help` during this issue's drafting.

## AI Implementation Instruction
Verify `tools/generate_workitem.py --kind issue`'s actual current behavior (run its `--help`, and ideally a scratch invocation) before finalizing the wording, in case the tool has changed since this issue was drafted. Model the added text on how `issue-to-plan/workflow.md`/`plan-to-implementation-procedure/workflow.md` already reference this same tool for their own scaffolding, for consistency. Do not remove the existing manual fallback procedure.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-115748
- **Related target files**: skills/issue-creator/workflow.md
