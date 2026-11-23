# Plan To Implementation Procedure — Edge Cases

Sections of `workflow.md` that apply only to a minority of cycles, moved here verbatim. Load
this file only when the trigger written in the matching place of `workflow.md` holds, and
follow the section it names. The main workflow keeps every heading, so a citation by section
name still resolves there.

### Non-conforming Plan structure

Applies when `tools/check_workitem_structure.py --file {plan_path}` reports
`missing-section` findings (the Plan lacks a section `templates/plan.md` requires, e.g. `Implementation
Target Files` or `Traceability`).

MUST NOT silently proceed on an incomplete Plan, and MUST NOT silently report `Blocked`
without offering the choice — ask the user which path to take for this Plan:

- **(a) Blocked, refer back to `issue-to-plan`**: stop this cycle and report `Blocked:
  Plan missing required section(s): {list}` (structural completeness is
  `issue-to-plan`'s responsibility).
- **(b) Correct in place, with the user's explicit approval**: only when the user
  explicitly approves for this specific Plan, rewrite `plans/{filename}.md` (via
  Write/Edit) to add the missing section(s), grounding every added claim (Requirements,
  Implementation Target Files rows, Traceability values) in repository evidence per
  Step 3a's Adversarial Verification procedure below — MUST NOT fabricate a Requirement,
  a Source issue path, or a Target File row that cannot be traced to the Plan's own
  prose or its source issue. Re-run `tools/check_workitem_structure.py --file
  {plan_path}` after the rewrite and confirm zero findings before proceeding to Freeze
  validation (this Step's next bullet).

MUST NOT default to (b) without asking (silent correction here would mask an upstream `issue-to-plan` defect).

### Step 3b: reverted Plan timestamp marker

If `plans/{filename}.md` is reverted (in whole or in part) during an active Step 3
pass for any reason, the existing timestamp marker line (format:
`<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: {timestamp}
-->`) MUST be preserved — re-add it if a full-file revert removed it. MUST NOT let it
silently regenerate with a new value: a still-pending row's later
`generate_workitem.py` call would then mint a different timestamp than earlier rows in
the same pass, breaking the "one shared timestamp per pass" guarantee.

### Step 3c: existing output path

- If the resulting path already exists, this can only mean an interrupted cycle is
  being resumed and the classification above did not treat it as covering this row
  (e.g. stale or partial-scope content) — it MUST NOT be overwritten. Stop and
  report `Needs confirmation` for this row instead. The tool's own collision
  refusal is the same signal, not a separate failure mode.
  This `Needs confirmation` is terminal for this cycle: MUST NOT
  re-attempt the row within the same pass. Report it once and continue with the
  remaining rows; the row has no document, so Step 4's move gate does not hold. A
  human must resolve the interrupted-cycle state (confirm whether the
  existing file is stale, partial, or covers the row — a stale file is removed as that single file) and then re-invoke this skill.

### Step 3c: additional target file discovery

- If investigation reveals that implementing this row requires modifying a file not
  listed in `Implementation Target Files`, this is an **additional target file
  discovery** — stop immediately and report `Blocked: additional target file
  discovered — {path}`. MUST NOT generate a procedure document for this or any further
  row until the Plan has been amended and revalidated/re-frozen per
  `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
  Freeze). Amend through `uv run python tools/amend_plan.py {plan_path} --file {path}
  --responsibility ... --reason ... --requirement {REQ-ID} --evidence ... --tests ...
  --step {N} --class fallout|scope` (add `--dry-run` first to preview every edit): it
  appends the new `Implementation Target Files` row after the last existing row —
  never inserted earlier, so no existing row's `seq` changes — with evidence and a
  Requirement link, edits the other Plan sections consistently, re-checks the four
  Freeze criteria for the row (`Draft` on a failure), and prints the structure,
  path-audit, and overlap checks. State the class per `rules/workflow-lifecycle.md` Plan
  Amendment Approval Classes: for a fallout amendment, amend without asking
  and report it afterward (file, class, reason); for a scope or behavior change, a new requirement,
  or a removed row, stop `Blocked: additional target file discovered — {path}` and
  ask before amending. Once re-frozen, resume this same session's cycle from Step 3c at the row
  that discovered the gap — MUST NOT restart from Step 2's Revalidation (already
  satisfied by the re-freeze) or from row 1.

### Step 3c: Plan Gap

- If investigation instead reveals that this row's approach needs to change but no
  additional file is involved, MUST NOT add the change to the generated document.
  Report it as `Plan Gap: {description}` and ask the user for the scope decision, which
  belongs to a Plan revision, not this workflow. Once decided, correct the Plan (see
  Allowed file operations); if a file row changed, re-validate and re-freeze it per
  `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze). Then
  re-invoke this skill: Step 3c's classification resumes only the unfinished rows.

### Step 3c: gated Plan marker

- When the user chose to proceed with a gated Plan in Step 2, start the Notes cell of each
  pending row of every generated document with `Gated: {blocking path} phase {N or all}
  - {reason}`, as `templates/execution-status.md` defines it: write it while authoring
  the document, or with `set-step-status implementation-procedure {path} --step {N}
  Pending --notes "Gated: ..."` only while that row's Notes is empty (the call appends).
  The owner decides the order and clears the marker, not this workflow.
