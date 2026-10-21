# Obtain owner offset-file state to set the EventBus offset import end condition

## Priority
High

## Summary
Obtain from the owner the deployed state of the EventBus legacy offset directory and decide the end condition and retention policy for the legacy file-based offset import, so that `compat002` can record its decisions. This issue tracks the owner input; it is not code work. Once the answers are recorded here, close this issue and proceed with `compat002`.

## Background
- `compat002` decides when the EventBus startup step that imports legacy file-based consumer offsets into the database may be retired, what happens to the old offset files, and which side is authoritative. Those decisions are recorded in the operations and database documents.
- An investigation dated 2026-10-20 re-checked the import code against the current source: `migrate_legacy_offsets()` in `scripts/eventbus/offset_migrator.py` reads each offset file under `offsets_dir`, recovers the consumer id from the `.map` companion (or the sanitized file name), and inserts into `consumer_offsets` with `INSERT OR IGNORE` without modifying or deleting the files; the lifespan in `scripts/eventbus/app.py` calls it on every start inside a `try` that only logs and continues. The runtime no longer writes offset files: `write_offset()` / `read_offset()` in `scripts/eventbus/offsets.py` have no caller outside tests, and `scripts/eventbus/ack_route.py` routes through `ack_event_for_consumer()`. (Confirmed by repository evidence)
- No document states why the files are kept, who owns them, which side wins after the import, or when the import ends. (Confirmed by repository evidence: absence verified by search of `docs/`)
- Whether any deployment still holds legacy offset or `.map` files lives outside the repository and must not be guessed.

## Problem
The import runs on every start with no completion marker and no stated end. The legacy files stay in place indefinitely, so an operator cannot tell whether they are still authoritative, a rollback aid, or garbage. A consumer-id collision aborts the whole import silently relative to startup, leaving some consumers unmigrated with only a log line. Nothing records when the import may be removed.

## Reason for Change
Consumer offsets decide where each consumer resumes; losing or mis-restoring one repeats or skips events. The import is a data-integrity path that cannot be deleted on a guess, and it should not stay on the startup path forever without an owner and an exit condition. Writing the decisions down now lets the removal be reviewed against a fixed criterion.

## Implementation Intent
This is an inquiry-and-record task, not a code change. Ask the owner the questions below, record the answers verbatim in the Owner Input Record section of this issue, and hand the recorded answers to `compat002`. Do not infer deployments from the repository.

## Target Files or Areas
- `issues/20261021-092415_owner002_...` (this issue; the answer record lives here)
- `issues/20261020-122817_compat002_...` (the parent issue this unblocks)
- `owner-question-packet.md` (working questionnaire; being retired once these issues exist)

## Required Changes
- Obtain from the owner the state of `offsets_dir` in every deployment: whether any offset or `.map` file exists, and whether any consumer still depends on it.
- Decide and record the end condition for the import (for example, no deployment holds a legacy file, and the minimum supported schema from `compat001` is past the file-based era).
- Decide and record the retention policy for the files: keep for rollback or audit, archive, or delete, with the permissions and backup treatment that follows.
- Record the authority rule after import (database is authoritative; files are not a resume source).
- Decide whether a consumer-id collision should stop startup or only be reported, whether the import should leave a completion marker, and whether `write_offset()` / `read_offset()` should be removed with the import.

## Constraints
- Do not guess whether a deployment still holds legacy files. Record only owner-supplied answers.
- Do not change `scripts/`, `config/`, or `tests/`, and do not delete or move any offset file. That work belongs to `compat002`.
- Answers may be supplied in English or Japanese; record them verbatim.

## Acceptance Criteria
- **AC-1**: The Owner Input Record section states whether any deployment still holds legacy offset or `.map` files and whether any consumer relies on them.
- **AC-2**: The Owner Input Record section states the end condition, the file retention policy, and the authority rule after import.
- **AC-3**: The decisions on collision handling, a completion marker, and helper removal are recorded, each either decided or listed as an open question with an owner.
- **AC-4**: Every answer carries an answerer and a date.

## Testing Expectations
Not required: this issue produces recorded owner input, not code. Verify AC-1..AC-4 by inspection.

## Documentation Impact
None beyond this issue's own Owner Input Record. The recorded answers feed `compat002`, which writes the operations, semantics, and database documents.

## Out of Scope
- Changing `migrate_legacy_offsets()`, its startup call, or the file-based helpers.
- Deleting any offset file or changing `offsets_dir`.
- Writing the decisions into the operations/semantics/database documents. That is `compat002`.

## Dependencies
- **Unblocks**: `compat002` (`issues/20261020-122817_compat002_...`); `compat002` cannot record its end condition without this input.
- **Depends on**: `compat001` for the minimum supported schema baseline (this issue should be answered together with or after the `compat001` owner input).
- Sibling-issue check: no other open issue under `issues/` tracks the legacy offset import; the schema migrations of `eventbus.sqlite` are covered by `compat001`, and the post-start verification failure is handled by `ebstart003`, neither overlapping this issue.

## Unresolved Questions
- Does any deployment still hold legacy offset or `.map` files, and does any consumer rely on them?
- Does `migrate_legacy_offsets()` make its inserts durable? It issues `INSERT OR IGNORE` and never calls `commit()`; whether a later commit on the same connection always follows before shutdown was not verified.
- Should a consumer-id collision stop startup, or is a logged, partial import acceptable?
- Are the file-based `write_offset()` and `read_offset()` kept for a reason other than tests?
- Who owns the offset files and the decision to delete them?

## AI Implementation Instruction
- This issue is an inquiry-and-record task. Do not touch `scripts/`, `config/`, or `tests/`, and do not delete or move any offset file.
- Ask the owner the questions above and record the answers verbatim in the Owner Input Record section with an answerer and date.
- Do not infer or guess the deployed offset-file state from the repository. If an answer is unavailable, leave it open with an owner rather than filling a gap.
- When all owner inputs are recorded and AC-1..AC-4 hold, close this issue and hand the recorded answers to `compat002`.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-092415
- **Related target files**: `issues/20261021-092415_owner002_...`, `issues/20261020-122817_compat002_...`

## Owner Input Record
| Item | Answer | Answerer / Date |
|---|---|---|
| Any deployment still holding legacy offset / `.map` files | _pending_ | — |
| Any consumer still depending on the files | _pending_ | — |
| Import end condition | _pending_ | — |
| File retention policy (keep / archive / delete + backup treatment) | _pending_ | — |
| Authority rule after import | _pending_ | — |
| Collision handling / completion marker / helper removal | _pending_ | — |
