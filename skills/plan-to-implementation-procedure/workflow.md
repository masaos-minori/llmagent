# Plan To Implementation Procedure — Detailed Workflow

## Workflow position

See `routing.md`, section 'Document workflow directories' for this pipeline; this
skill produces the `implementations/` step.

- Input: `plans/{filename}.md`
- Output: `implementations/{timestamp}_{seq}_{target_file_slug}.md`, where
  `target_file_slug` is `target_file_path` with `/` and any non-alphanumeric/`_`/`-`/
  `.` character replaced by `_`, `timestamp` is shared across every document
  generated in one Step 3 pass, and `seq` is the row's 1-indexed, zero-padded
  position within the plan's `Implementation Target Files` table
  (`templates/plan.md`) — sorting filenames reproduces the implementation order.
- Archive destination: `plans/done/`
- Workflow phase: `plan-to-implementation-procedure`

This phase produces the **implementation procedure**, not an architecture design
document — there is no separate design phase in this pipeline.

## Allowed file operations

This is a document-only phase. Allowed operations:
- Create implementation procedure documents in `implementations/`.
- Move the processed plan file to `plans/done/` once Step 3's validation passes —
  no human approval is required, per `rules/workflow-lifecycle.md` Validation
  Reporting.
- Correct the Plan file itself (`plans/{filename}.md`, via Edit) when Step 3's
  adversarial verification finds an unconfirmed item or an inconsistency — the
  document-only constraint applies to source code and `docs/*.md`, not to the Plan
  document under active revision.
- If `tools/generate_workitem.py --kind implementation-procedure` is used (see Step 3),
  it appends a timestamp-marker HTML comment to the Plan file being processed (never
  rewriting existing content) so repeated invocations against the same Plan share one
  timestamp — an expected side effect, not a violation of the document-only constraint.
- See `skills/plan-to-implementation-procedure/SKILL.md` Purpose and `skills/DESIGN.md`,
  section "Analysis-only phase constraint".
- MUST NOT modify files outside `implementations/` and the plan file being moved — the
  general prohibition is `AGENTS.md` Global Rule 5.

## Out of Scope

See `rules/workflow-lifecycle.md` Global Safety Restrictions for the full list.

## Toolchain

Repository tools for this workflow (see `tools/TOOL_DESCRIPTIONS.md` for usage):
- `tools/generate_workitem.py --kind implementation-procedure` (Step 3, skeleton
  generation; see Allowed file operations for its Plan-file timestamp-marker side
  effect).
- `tools/manage_workitem_stage.py set-step-status` (Step 4, the Plan's `### Execution
  Status` row updates without hand-editing the table).
- `tools/check_plan_target_overlaps.py` (Step 2, candidate overlaps between Frozen Plans).
- `tools/manage_workitem_stage.py close-plan` (Step 4, `git mv`-based archival move).

Per `rules/ai-execution.md` Repository Tool Usage, prefer these over the equivalent
manual command when they cover the need; Step 3 and Step 4 state the fallback if a tool
is unavailable or refuses.

Step 3's narrow delegation to `skills/python-design/SKILL.md` (Design-decisions-family
fields only) inspects `skills/python-design/workflow.md` Step 3 and Step 4 for its own tool needs
(`lint-imports`, `ast-grep`) — this workflow's own Repository Tool Usage inspection
obligation (Step 0) does not extend to that skill's tools beyond the delegation itself.

## Multi-file processing

Apply `rules/ai-execution.md` Sequential Target Processing (Base): each cycle covers
Steps 1-4, ending with the move to `plans/done/` in Step 4, before starting Step 1 for
the next file.

Idempotency for a resumed pass comes from two existing mechanisms, not from this
section: Step 3's `Already implemented` classification (skips a row already covered by
an existing document) and the Plan-file timestamp-marker mechanism (see `Allowed file
operations` and Step 3), which keeps the generated-document timestamp consistent.

Apply `rules/ai-execution.md` Context Reading and Progress Reporting (Base) for the per-step report
cadence, using this line format:
`Step {N} | {state} | Plan: {path} | Generated: {files or None} | Blockers: {items or None}`

---

## Step 0: Load Required Instructions

Read, if not already loaded this session: `routing.md`, `rules/coding.md`,
`rules/toolchain.md`, `skills/python-design/SKILL.md`,
`skills/python-design/workflow.md`, `rules/ai-execution.md`,
`rules/workflow-lifecycle.md`, `skills/DESIGN.md` (Output language, Out-of-scope
paths), `templates/traceability.md`, `templates/plan.md`,
`templates/implementation-procedure.md`, `templates/execution-status.md`,
`SKILL.md` (this skill), and this file.

Apply `rules/ai-execution.md` Context Reading for reuse-vs-reload of shared files
across cycles.

Apply `rules/ai-execution.md`, section 'Required File Validation'.

---

## Step 1: Identify the Target Plan File(s)

Apply `rules/workflow-lifecycle.md` Target Validation (Step 1) and Current-Target
Loading in full. This workflow's target files: `plans/{filename}.md`; archive
directory: `plans/done/`.

---

## Step 2: Read the Target Plan File

Only the current file MUST be read; multiple target files MUST NOT be read
simultaneously.

- Before reading, run `uv run python tools/check_workitem_structure.py --file
  {plan_path}` to confirm the Plan contains every `## ` section `templates/plan.md`
  requires. If it reports any `missing-section` finding, see "Non-conforming Plan
  structure" below before proceeding — a Plan missing entire sections (e.g.
  `Implementation Target Files`, `Traceability`) cannot be read as if it followed
  `templates/plan.md`, and the checks below (Freeze status, Source issue extraction)
  assume those sections exist.
- Read the target plan file in full. It follows `templates/plan.md`'s structure.
- Identify the target feature. The files to modify are exactly the Plan's
  `Implementation Target Files` rows — MUST NOT re-derive the file list independently
  from `Implementation steps` or prose.
- Confirm the `Implementation Target Files` section's `Freeze status` is `Frozen`. If
  it is not, stop and report `Blocked` — freezing is `issue-to-plan` Step 8's
  responsibility; MUST NOT freeze it here.
- **Plan-level start conditions** (read-only checks; a hit ends the cycle `Blocked` and
  the Plan stays in `plans/`):
  - A row of the Plan's `Unknowns` table has `Blocking? = True`. That is unresolved by
    definition (`issue-to-plan` Step 6 ends `Blocked` while one remains). Report it and
    ask the user to resolve it in the Plan first.
  - The Plan's `Scope` lists a Dependency on another open Plan or Issue (including a fix
    order against sibling plans). Report it and ask whether to proceed; do not decide the
    order here.
  - Run `uv run python tools/check_plan_target_overlaps.py`. It lists candidates only, never
    a verdict. For each overlap that names this Plan, read both Plans and record in the
    generated documents' `Assumptions` whether it is a conflict, a sequencing dependency,
    or compatible; a conflict is `Blocked`.
- **All-rows-already-implemented short-circuit**: check whether every
  `Implementation Target Files` row's `target_file_slug` already matches a document
  under `implementations/` or `implementations/done/` whose `Source plan` and
  `Related target files` confirm full coverage of that row — the identical criteria
  Step 3's `Already implemented` classification uses per-row, not a separate, looser
  check. If every row meets them, skip Revalidation and Step 3's per-row loop entirely
  and proceed directly to Step 4's move, reporting explicitly:
  `All rows already implemented — proceeding to Step 4`.
- Revalidate the frozen inventory per `rules/workflow-lifecycle.md` Implementation
  Target Files Validation (Plan Freeze) — Revalidation, before proceeding to Step 3.
  If revalidation finds a discrepancy, correct the Plan per that section's rules, then
  re-run the Plan Freeze validation for the corrected row(s) specifically (not the whole
  table, and not skipped) before proceeding to Step 3.
- Extract the Plan's Traceability section's `Source issue` value for reuse in this
  cycle's generated documents (Step 3) — MUST NOT re-derive it from scratch.
- If the plan is ambiguous or the scope is unclear, stop and ask for clarification
  before proceeding.
- **After finishing all Steps 1-4 for this file, load the NEXT target file.** MUST NOT
  preload or batch-read other files.

### Non-conforming Plan structure

Applies when `tools/check_workitem_structure.py --file {plan_path}` (above) reports
one or more `missing-section` findings — the Plan does not follow `templates/plan.md`'s
required structure (e.g. it uses a non-standard section in place of `Implementation
Target Files`, or has no `Traceability` section).

MUST NOT silently proceed on an incomplete Plan, and MUST NOT silently report `Blocked`
without offering the user a choice — ask the user which path to take for this specific
Plan:

- **(a) Blocked, refer back to `issue-to-plan`**: stop this cycle and report `Blocked:
  Plan missing required section(s): {list}` — structural completeness is
  `issue-to-plan`'s responsibility; the Plan should be regenerated or corrected there.
- **(b) Correct in place, with the user's explicit approval**: only when the user
  explicitly approves for this specific Plan, rewrite `plans/{filename}.md` (via
  Write/Edit) to add the missing section(s), grounding every added claim (Requirements,
  Implementation Target Files rows, Traceability values) in repository evidence per
  Step 3a's Adversarial Verification procedure below — MUST NOT fabricate a Requirement,
  a Source issue path, or a Target File row that cannot be traced to the Plan's own
  prose or its source issue. Re-run `tools/check_workitem_structure.py --file
  {plan_path}` after the rewrite and confirm zero findings before proceeding to Freeze
  validation (this Step's next bullet).

MUST NOT default to (b) without asking — a structurally incomplete Plan may reflect an
upstream `issue-to-plan` defect that repeated silent correction here would mask rather
than surface.

---

## Step 3: Create Implementation Procedure Documents

Write the entire document in English (see `SKILL.md` Core Execution Rules) — every
section's body text, not only headings, regardless of the chat language.

Generate each document using the exact structure defined in
`templates/implementation-procedure.md` (loaded in Step 0). See that template's Notes
on filling sections for how to apply `skills/python-design/SKILL.md` +
`skills/python-design/workflow.md` to the Design-decisions-family fields — draw only
the few relevant bullets from that skill's broader multi-section template (its Design
Decisions and Alternatives, Interface Design, Security and Trust Boundaries, and
Implementation Plan sections); MUST NOT produce
its full architecture output here.

This step has four sub-steps. Step 3b runs once, before the row loop starts. Then, for
each target-file row in order, apply 3a (verify the Plan's claims), 3c (process the row),
and 3d (record progress), in that order.

### Step 3a: Verify the Plan's claims (adversarial verification)

Treat the Plan's descriptions of current source-code behavior as claims, not
confirmed present-tense fact — it may have gone stale since approval. Apply
`rules/ai-execution.md` Adversarial Verification (Base) before writing
Procedure/Method/Details for a row: look for reasons the Plan's claims about the
target file, symbol, call path, or test might be wrong — shifted line numbers, an
already renamed/removed symbol, a dependency the Plan did not account for, a
Requirement duplicating/contradicting another Plan, or a code path the Plan's
Background never checked — verifying each via `rg`/Read. Apply `rules/ai-execution.md`
Tool Usage's idempotent-command rule: MUST NOT re-run a `rg`/Read check already performed
against this same file at its current content within this cycle.

If adversarial verification finds an unconfirmed item or an inconsistency (a stale
claim, a missing Requirement, a newly discovered dead-code reference, a duplicate or
superseded Plan, etc.), correct the Plan document itself (`plans/{filename}.md`,
via Edit) in the same cycle — update whichever sections apply (Background,
Requirements, Acceptance criteria, Assumptions, Risks, Requirement Traceability,
Execution Status) rather than silently working around the discrepancy — and reflect
the corrected understanding in the generated document(s). Record what was found and
corrected in the progress report; MUST NOT report a row `Completed` while a
Plan-level inconsistency it surfaced remains unresolved. After correcting, re-run this
Step 3a's verification against the corrected Plan text for this row before proceeding
to Step 3c — MUST NOT assume one correction resolved everything.

Apply `rules/workflow-lifecycle.md` Correction-and-Recheck Cycle Bound (re-running
Step 3a against the corrected Plan); the `{artifact}` in that bound's `Blocked`
message is "Plan ... for {row}".

If this correction requires reverting a prior edit to `plans/{filename}.md`, see
`rules/workflow-lifecycle.md` Plan-Document Correction Handling for whether `AGENTS.md`
Rollback Directive applies (it does not) — and, if a revert is nonetheless performed,
see the timestamp-marker preservation requirement in Step 3b.

If this correction is made while processing row K (K > 1), check whether any
already-generated document for rows 1..K-1 relied on the now-corrected claim. If one
does: amend that earlier document in the same cycle when the fix is bounded and does
not require re-investigating that row's dependencies or tests; otherwise, flag it in
the progress report and the Plan's Execution Status as needing re-verification before
Step 4's move — MUST NOT silently leave a stale earlier document unflagged. Scope this
check to the corrected claim only, not a full re-verification of every prior row.

**Completed when**: for the current row, the target file, its direct dependencies, and its
related tests have each been checked once against the Plan's claim about them, and any
disconfirming finding has been corrected in the Plan document.

### Step 3b: Prepare the shared pass timestamp

Apply `rules/workflow-lifecycle.md` Evidence-Only vs. Target Files: a file belongs under
`Target file` only if it is a row in the Plan's `Implementation Target Files` table
(revalidated in Step 2) — see `templates/implementation-procedure.md` Notes on filling
sections for how a `Reference Files` entry is mentioned in the generated document.

Before iterating, set one shared timestamp for this Step 3 pass: run
`date +%Y%m%d-%H%M%S` once and reuse that exact value for every document created in
this pass. MUST NOT re-run `date` per row — creation order MUST be recoverable from
`seq`, not from timestamp drift between rows. If using
`tools/generate_workitem.py --kind implementation-procedure` (see the `Not
implemented` case below), this manual step is unnecessary — the tool derives and shares
the pass timestamp itself via a marker in the Plan file (see Allowed file operations),
so every invocation against the same `--source-plan` reuses the same value regardless
of invocation order or a resumed session.

If `plans/{filename}.md` is reverted (in whole or in part) during an active Step 3
pass for any reason, the existing timestamp marker line (format:
`<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: {timestamp}
-->`) MUST be preserved — re-add it if a full-file revert removed it. MUST NOT let it
silently regenerate with a new value: a still-pending row's later
`generate_workitem.py` call would then mint a different timestamp than earlier rows in
the same pass, breaking the "one shared timestamp per pass" guarantee.

**Completed when**: one timestamp value is set (manually or via the tool's marker
mechanism) and will be reused for every document this pass creates.

### Step 3c: Process each target file row

For each row in `Implementation Target Files`, in the order they appear in that table
— **one target file = one implementation procedure document** (see `SKILL.md` Core
Execution Rules):

- `target_file_path` is the row's `File Path` (e.g. `scripts/agent/foo.py`);
  `target_file_name` is its base name only. Use `target_file_path` for traceability
  matching and output naming — `target_file_name` alone is ambiguous when the same
  base name exists under multiple directories.
- `seq` is this row's 1-indexed position within the Plan's `Implementation Target
  Files` table, zero-padded to 2 digits (`01`, `02`, ...) — fixed by the row's
  position in the table, not by generation order or how many rows were skipped as
  already implemented, so re-running an interrupted cycle assigns the same `seq` to
  the same row every time.
- `Implementation Target Files` disallows duplicate `File Path` rows once `Frozen`
  (see `rules/workflow-lifecycle.md`), so each row maps to exactly one document — no
  merging is needed. If a duplicate `File Path` is found across rows, the Plan was not
  correctly frozen; stop and report `Blocked`.
- Classify the row's implementation state:
  - `Already implemented`: an existing document under `implementations/` or
    `implementations/done/` has both `Source plan` equal to the current
    repository-relative plan path (`plans/<file>` and `plans/done/<file>` count as the
    same path, since a Plan moves after its documents are written) and
    `Related target files` equal to the current
    repository-relative target path (matched via `target_file_path`, not only
    `target_file_name`), AND — confirmed against current source, not just the matched
    document's text — its stated scope covers the current row's full scope. The
    target source file merely existing is not sufficient evidence; read the matched
    document's content and confirm.
  - `Partially implemented`: a matching document exists, but its scope is outdated,
    narrower than, or only overlaps the current row.
  - `Not implemented`: no matching document exists, or none of the above applies.
- If `Already implemented`, skip this row.
- If `Partially implemented`, create a document scoped to only the not-yet-implemented
  remainder — reference the matched existing document for the already-covered portion
  instead of repeating it, and note the discrepancy in the progress report. The row is
  then covered by two documents by design (the existing one plus this cycle's remainder
  document); Step 4's one-document-per-row checks count only documents generated this
  cycle.
- If traceability is missing or ambiguous, MUST NOT skip the row. Report
  `Needs confirmation`.
- If `Not implemented`, create the document only (MUST NOT implement anything):
  - Create a file-level implementation and test procedure document containing
    modification instructions for exactly this row's `File Path` — no other file.
  - Optionally scaffold the empty file first with `uv run python
    tools/generate_workitem.py --kind implementation-procedure --source-plan
    {plan_path} --target-file-path {target_file_path} --seq {seq}` — it reproduces
    `templates/implementation-procedure.md`'s current field order exactly, computes
    `target_file_slug` per the naming rule above, and shares this pass's timestamp
    automatically across every row's invocation (see Allowed file operations).
    After a `0` exit, independently verify the expected file exists at
    `implementations/{timestamp}_{seq}_{target_file_slug}.md` before proceeding — a `0`
    exit alone is not sufficient evidence per `rules/ai-execution.md` Repository Tool
    Usage #8.
  - Save the document as `implementations/{timestamp}_{seq}_{target_file_slug}.md`
    (naming per Workflow position above), using this pass's shared `timestamp` and
    this row's `seq`.
  - After writing it, run `uv run python tools/stale_detector.py {document_path}` (the
    same check `code-implementation` runs before executing a procedure, so a stale
    reference surfaces here instead of aborting that later cycle). For each mismatch:
    (1) a name, import, or target file this document creates — add `(new)` after it
    (see `templates/implementation-procedure.md` Notes); (2) a name that only an
    earlier-`seq` row's procedure in this Plan creates — acceptable, because it will
    exist when `code-implementation` executes the rows in order; note it in the
    document's Assumptions; (3) anything else is a stale reference — correct the
    document and re-run.
  - If the resulting path already exists, this can only mean an interrupted cycle is
    being resumed and the classification above did not treat it as covering this row
    (e.g. stale or partial-scope content) — it MUST NOT be overwritten. Stop and
    report `Needs confirmation` for this row instead. The tool's own collision
    refusal is the same signal, not a separate failure mode.
    This `Needs confirmation` report is terminal for this cycle, not retriable: MUST NOT
    re-attempt the same row within the same pass. Report it once and continue with the
    remaining rows; this row has no document, so Step 4's move gate does not hold. A
    human must resolve the underlying interrupted-cycle state (confirm whether the
    existing file is stale, partial, or already covers the row — for a stale file, by
    removing that single file) and then re-invoke this skill, before any future run
    revisits this row.
- Classify each evidence gap encountered while investigating a row as Blocking or
  Non-blocking:
  - Blocking: a safe, concrete procedure cannot be written without this evidence. Stop
    and report `Blocked: {specific row}`.
  - Non-blocking: a procedure can still be written with a noted caveat. Report
    `Needs confirmation` and proceed — MUST NOT skip the row.
- If investigation reveals that implementing this row requires modifying a file not
  listed in `Implementation Target Files`, this is an **additional target file
  discovery** — stop immediately and report `Blocked: additional target file
  discovered — {path}`. MUST NOT generate a procedure document for this or any further
  row until the Plan has been amended (the new file added as its own `Implementation
  Target Files` row appended after the last existing row — never inserted earlier,
  so no existing row's `seq` changes — with evidence and a Requirement link) and
  revalidated/re-frozen
  per `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
  Freeze). Once re-frozen, resume this same session's cycle from Step 3c at the row
  that discovered the gap — MUST NOT restart from Step 2's Revalidation (already
  satisfied by the re-freeze) or from row 1.
- If investigation instead reveals that this row's approach needs to change but no
  additional file is involved, MUST NOT add the change to the generated document.
  Report it as `Plan Gap: {description}` and ask the user for the scope decision, which
  belongs to a Plan revision, not this workflow. Once decided, correct the Plan (see
  Allowed file operations); if a file row changed, re-validate and re-freeze it per
  `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze). Then
  re-invoke this skill: Step 3c's classification resumes only the unfinished rows.
- Apply `rules/workflow-lifecycle.md` Requirement Reference Format in the generated
  document (see `templates/implementation-procedure.md`).
- Judge each row against the template's "Lightweight fill for small rows" criteria
  (`templates/implementation-procedure.md` Notes) and shrink the optional-detail sections
  accordingly. This changes only the section bodies — it never merges rows, drops
  headings, or skips the Blocked/Plan Gap checks above.

**Completed when**: every row has been classified and assigned exactly one outcome —
skipped (`Already implemented`), a scoped document created (`Partially implemented` or
`Not implemented`, including a non-blocking `Needs confirmation` written with a caveat),
or reported without a document (`Blocked`, `Plan Gap`, or the terminal `Needs
confirmation` for an existing path). A row reported without a document leaves the
cycle unmoved: Step 4's move gate requires every row to be covered by a document.

### Step 3d: Progress recording

**Chat-facing reporting** (frequency-gated): report an interim update only when a
row's outcome is Blocked, Partially implemented, fails verification, produces a Plan
Gap, or is an additional target file discovery — MUST NOT report for a row that
completes as Already implemented or Not implemented→newly created without incident.
When reporting, note which target file you are working on, record the current status
(In Progress / Blocked / Completed), and if blocked, describe the blocker and whether
it requires user intervention.

**Persisted record** (unconditional, per row): a generated document's own `### Execution
Status` table starts with every step `Pending` and stays that way — nothing in it has been
executed, and only `code-implementation` advances it, so this skill does not change it.
Record what this cycle learned in the document itself instead: a caveat from a
non-blocking `Needs confirmation` goes in `Assumptions` and in the affected step's `Notes`.
A row that ends without a document (`Blocked`, `Plan Gap`, terminal `Needs confirmation`)
has no document to hold a record: it appears in the progress line and the final report
(Step 4). This is the recovery record if the session is interrupted mid-pass, because a
resumed run reclassifies every row by Step 3c.

---

## Step 4: Move the Completed Plan File

This step MUST NOT be skipped.

This workflow's move to `plans/done/` does not require human approval, per
`rules/workflow-lifecycle.md` Validation Reporting — proceed once Step 3
completes and the checks below pass, without stopping to ask the user for
approval.

Read these values back from each row's Step 3c/3d outcome as already recorded — MUST NOT
recount by rescanning `implementations/`; the in-memory listing `Procedure-Specific
Guidance` describes maintaining through Step 3 already reflects every document this
cycle created. Verify that:
- every `Implementation Target Files` row in the Plan is covered by a document
  (`Already implemented` by an existing document, `Partially implemented` by an existing
  document plus this cycle's remainder document, or newly created this cycle). A row
  that ended `Blocked`, `Plan Gap`, or the terminal `Needs confirmation` has no document
  and fails this check;
- the number of `Implementation Target Files` rows equals the number of rows covered
  (each counted once, including `Already implemented` matches), and the documents
  generated this cycle number at most one per row;
- every document generated this cycle maps back to exactly one row, and no row has more
  than one document generated this cycle;
- no procedure document modifies more than one file (its `Implementation > Target
  file` names exactly one path);
- no file outside `Implementation Target Files` was added as a modification target
  during this cycle (an additional target file discovery MUST already have been
  reported `Blocked` and resolved per Step 3, not silently included here);
- each document created this cycle has every step in its Execution Status `Pending`
  (nothing in it has been executed), and each caveat from a non-blocking `Needs
  confirmation` is recorded in its `Assumptions`.

If any of the above does not hold, MUST NOT proceed to the move — report `Blocked`, list
every uncovered row with its outcome (`Blocked` / `Plan Gap` / `Needs confirmation`),
and leave the Plan in `plans/`; a later run resumes through Step 3's `Already
implemented` classification once the cause is resolved.

This workflow MUST update the Plan's own `### Execution Status` table (in
`plans/{filename}.md`) before the move — MUST NOT leave any row `Pending` once
its outcome is known. That table has one row per Plan `Implementation steps` entry
(same numbering — see `issue-to-plan` Step 5), not one row per `Implementation Target
Files` row. A procedure document carries out the modification of one file, so only a
step that modifies a cited `File Path` is mapped to procedures. A step that only runs
checks or gates, records a baseline, deploys, or waits for a user decision modifies no
file: leave its row as it is — `code-implementation` or a person carries it out — and it
does not count against the `Pending` rule below. If you cannot tell whether a step
modifies a file, treat it as unmapped and say so in the final report. For each mapped
step N, once every `Implementation Target Files` row it cites has an outcome, mark row N
`In Progress` if any of those rows' procedure document was newly generated this cycle,
or `Completed` if every one was matched as `Already implemented`. If a `File Path` is
modified by no step, report `Plan Gap: no Implementation step modifies {path}`. Use `uv run python tools/manage_workitem_stage.py set-step-status
plan {plan_path} --step {N} {status}` — not `--description`, which updates only the
first row whose Description merely contains the given text — rather than editing the
table directly. This is
separate from each generated document's own Execution Status table, and separate
from `code-implementation`'s later responsibility (see that skill's own workflow)
to mark the same row `Completed` once the corresponding implementation procedure
document is actually executed — this Step's update reflects only what this cycle
observed (procedure generated vs. already implemented), not the eventual outcome of a
future `code-implementation` cycle.
MUST NOT proceed to the move below while any mapped row remains `Pending` — if a row's
outcome genuinely cannot be determined this cycle, report `Blocked` instead of
leaving it `Pending` silently.

### Record the generated documents in the Plan

Add one row to the Plan's `### Work Items Created` table for each procedure document
generated this cycle (replacing the placeholder row on the first one): Item ID = the
document's repository-relative path, Related Step = the mapped step number(s), Type =
`Procedure`, Status = `Pending`, Owner and Due Date = `—`. There is no tool for this
table; edit it directly. `tools/manage_workitem_stage.py close-batch` finds the owning
Plan first by the `implementations/<prefix>_` text in the Plan, and only otherwise by a
shared `Source issue`, which is ambiguous when several Plans share one Issue.

Apply `rules/workflow-lifecycle.md` Archival Move (`plan-to-impl-procedure` row) and
Completion Criteria in full. This workflow's move: `plans/{filename}.md` to
`plans/done/{filename}.md`, using `git mv` only.

**This cycle is complete when, and only when**: the move above has succeeded and been
verified (both locations checked, per Archival Move), or this Plan's cycle ended in a
`Blocked` state per Step 3's own stop conditions — in either case, emit this cycle's
progress report once, then (per Multi-file processing) begin Step 1 for the next
target Plan, or end the batch if none remain.

Prefer `uv run python tools/manage_workitem_stage.py close-plan
plans/{filename}.md` over a direct `git mv` — it auto-commits the Plan file
first if it has uncommitted changes (commonly this Step's own Execution Status
update above, or an earlier Step 3a correction), then performs the move; it refuses
(non-zero exit, no move) only if the source is missing or the destination already
exists. The auto-commit stages only the Plan file itself — unrelated uncommitted
changes elsewhere in the repository are left untouched and do not block the move. Pass
`--stage-only` to stage the dirty Plan instead of committing it, so the rename lands in
the next real commit with the work it belongs to and no `chore: auto-commit ...` commit is
created (`skills/git-commit-and-sync/workflow.md` Phase 2 includes such staged renames in
the cycle's commit). Fall back to the direct `git mv` command only if the tool is
unavailable.

After a `0` exit, independently verify the same checklist `rules/workflow-lifecycle.md`
Archival Move requires for the manual `git mv` fallback: destination file exists,
source file no longer exists, and the move is recorded as a Git rename — a `0` exit
alone is not sufficient evidence per `rules/ai-execution.md` Repository Tool Usage #8,
regardless of which path (tool call or manual fallback) performed the move.

### Final report

Emit once per Plan, whether the cycle ended moved or `Blocked`. The one-line progress
format above stays for step-by-step updates; the final report adds:

- the Plan path and its outcome (`moved to plans/done/` or `Blocked` with the cause);
- the generated documents in `seq` (execution) order, as paths;
- rows skipped as `Already implemented` (with the matched document) and rows
  `Partially implemented` (with the existing document the new one references);
- each non-blocking `Needs confirmation` caveat, each `Plan Gap`, and each uncovered row
  with its next action for the user;
- every edit made to the Plan in Step 3a (which sections, and why), the Plan steps treated
  as unmapped in Step 4, and any Plan-level overlap found in Step 2;
- the next step: run `code-implementation` over the documents in `seq` order.

---

## Procedure-Specific Guidance

- In Step 3, check "already implemented" status by first matching `target_file_slug`
  against file names under `implementations/` and `implementations/done/` as a cheap
  filter; only when a name matches, read that matched file's content (not the full
  target source file) to confirm its stated scope actually covers the current row
  before deciding to skip.
  Capture the `implementations/` and `implementations/done/` directory listing once at
  the start of Step 3's row-processing loop, and reuse it for every row's filter check
  rather than re-scanning the filesystem per row. If this same pass writes a new file for
  an earlier row, update the in-memory listing to include it (MUST NOT re-scan the
  filesystem) before checking any later row against it. After a context compaction or a
  resumed session the in-memory listing is gone: capture it again once, then continue.
- In Step 3, perform the per-row investigation (reading the related source file to
  write Method/Details) sequentially; read only the relevant sections of the target
  source file (locate them with grep first, then read a limited range) rather than the
  full file. Retain only what is needed for the procedure document, not full file
  contents.

## Output format

See `SKILL.md` Output format for the exact Markdown structure to generate.
