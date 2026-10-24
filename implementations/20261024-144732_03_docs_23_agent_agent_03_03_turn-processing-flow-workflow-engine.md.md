## Goal

Document the `tasks.status` state machine in the chapter that is already the canonical home of
turn-persistence semantics: add a `### Task Status Transitions` subsection, and amend `### Startup
Recovery`, `## Operational Notes` and `## Known Limitations` so the chapter states who writes each
status, that a cancellation is recorded `halted`, that adapter status writes are best-effort, and
that startup recovery repairs attempts only (`REQ-010`; `AC-9`).

## Scope

- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` only, four passages:
  - new `### Task Status Transitions` inserted inside `## Responsibility Boundary`, directly after
    `### Workflow Status` (heading `:65`, body `:67-72`) and before `### Workflow Stages` (`:74`);
  - `### Startup Recovery` (`:102-104`): one added sentence;
  - `## Operational Notes` (`:106-108`): added bullets;
  - `## Known Limitations` (`:110-112`): one added bullet.
- Front matter (`:1-16`) is not edited: no new tag, no new `related` entry, no `Status` or Metadata
  field (`GV-016`).
- `## Design Intent` subsections, `### Partial Completion Model`, `### Workflow Stages`,
  `### Retry Mechanism`, `### Workflow Loader Validation Rules`, `## Key Constraints` heading, and
  the whole `## Turn-by-turn State Changes` region are untouched.
- No other chapter is edited. `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`
  is handled by `implementations/20261024-144732_04_docs_23_agent_agent_06_04_tool-execution-and-approval-canonical.md.md`.

## Assumptions

- This chapter is the canonical home for the state machine: `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md:31`
  points readers here for "the formal partial completion model", this chapter is one of only two documents
  in the corpus that mention task status at all, and `docs/00_index.md:148` reaches it through its hub
  `agent_03_01` (Plan `Documentation Impact`). Neither `agent_03_01` nor `agent_10_05` is edited by this
  row.
- The wording must describe the state machine that
  `implementations/20261024-144732_01_scripts_agent_workflow_engine_adapter.py.md` implements, so the
  six-row table in `Method` is written against the post-change behavior, not today's behavior.
- `halted` keeps its current meaning in this chapter (`:40` resume guard, `:108` operational note); the
  new content extends it to cancellation instead of redefining it, which is what `DR-001` decided.
- Status names are a code convention, not a schema constraint, so the chapter is the place where the
  vocabulary is documented (`schema_sql.py` `tasks` DDL, `task_ops.create_task()` writes `pending`).

### Procedure-local findings

- Frozen row status: **Not implemented** (no code or doc change for this row has been made) and
  **file-level overlap with active sibling procedures** on this same chapter:
  `implementations/20261024-083059_04_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`
  (turn002: `### Workflow Stages` stage table, `### Retry Mechanism`) and
  `implementations/20261024-092307_09_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`
  (turn004: the `verify` stage role, `execute_turn`'s `finally` teardown, `_handle_workflow_halt` state
  clearing). Sections are disjoint by design — `092307_09`'s Scope names
  "the task-status state machine (turn003's `### Task Status Transitions`)" as out of scope for it —
  so land this row **after** both and re-take the four anchors before editing.
- Anchor check against the current file at HEAD `6fcbb7e0c`: the Plan's `### Workflow Status`
  `:65-73`, `### Startup Recovery` `:102-104`, `## Operational Notes` `:106-108` and
  `## Known Limitations` `:110-114` are accurate. `## Known Limitations` `:110-114` includes the
  horizontal rule at `:114`, which separates the `## Responsibility Boundary` region from
  `## Turn-by-turn State Changes` (`:116`); insert the new subsection before `### Workflow Stages`
  (`:74`), never after `:114`, and never inside the `## Turn-by-turn State Changes` region.
- `092307_09` names no section for its teardown and halt-clearing passages. If it lands in
  `## Operational Notes`, this row's added bullets must be re-worded against the resulting text rather
  than applied blindly; that is the only plausible textual collision between the three procedures.
- The chapter's `### Turn State Mutation Reference` table (`:120-128`) lists per-turn state fields and
  does not include `tasks.status`. Adding a row there is outside the frozen row's four passages and is
  recorded as a follow-up candidate, not performed.
- The body already links this chapter's sibling at `:46` without a matching front-matter `related`
  entry; `check_docs_structure.py`'s `check_related_links` only validates entries that exist, and does
  not require reciprocity for non-ADR documents. No front-matter change is made.
- File size gate: `MAX_SIZE = 24576` in `tools/check_docs_structure.py` (raised from 16384). The chapter
  measures 7060 B / 137 lines today, so the added 40-55 lines stay far under the gate.
- Baseline measured 2026-10-24 at HEAD `6fcbb7e0c`, this file clean in every docs checker:
  `check_docs_structure.py "docs/23_agent/agent_03_03*.md"` — "All checks passed";
  `check_docs_quality.py` and `check_docs_content_policy.py` — no finding naming this file;
  `check_docs_consistency.py --domain agent` — "No issues found."; `check_docs_japanese.py` —
  "No Japanese files found."
- Plan-evidence correction: the Plan's `Documentation Impact` rationale says
  `docs/23_agent/agent_04_01_state-and-persistence-state-model.md:44` "defers this topic to
  `agent_03_03`". Re-measured: `agent_04_01:44` is `### DiagnosticStore Separation Design` body text about
  `session_diagnostics`, and `agent_04_01` references this chapter only in front matter (`:17`). There is
  no deferral sentence, so canonicality is grounded on `agent_10_05:31`, the `docs/00_index.md:148` hub path
  and the fact that no other chapter documents task status. The Plan's conclusion and its frozen row are
  unchanged.
- Heading map measured at HEAD `6fcbb7e0c` (`grep -n "^#{1,4} " <this chapter>`): Responsibility
  Boundary `:52`, Partial Completion Model `:54`, Workflow Status `:65`, Workflow Stages `:74`, Retry
  Mechanism `:82`, Workflow Loader Validation Rules `:90`, Key Constraints `:100`, Startup Recovery
  `:102`, Operational Notes `:106`, Known Limitations `:110`, Turn-by-turn State Changes `:116`, Turn
  State Mutation Reference `:120`, Keywords `:130`. No "Task Status Transitions" heading exists, and
  the docs structure checker has no duplicate-heading rule (its checks are size, H1 count, front
  matter, schema compliance, status value, tail sections, links, ADR IDs, related links, ADR related
  coverage), so the insertion cannot collide with an existing heading.

## Design decisions

- Component names, not file paths: the text says "the workflow engine" and "the turn adapter", which is
  the retain-category "component responsibility / state each component owns" content in
  `skills/DESIGN.md` Docs content policy, and avoids the remove-category "implementation-location
  mapping" pattern that `check_docs_content_policy.py`'s `check_location_mapping` flags.
- The private status-decision helper is not named in the chapter. `check_docs_consistency.py --domain
  agent` resolves backtick-quoted `name()` references against `scripts/`, so naming a symbol that does
  not exist yet would create a finding; only `update_task_status()` and `recover_stale_attempts()` are
  cited, and both exist.
- A table is used for the six exit paths because a table row is exempt from the default-value
  restatement rule and because the reader must compare writer and reason per exit at a glance; the
  header avoids `Case`/`Scenario` + `Action` and `Function`/`Signature` shapes so
  `check_error_handling_table` and `check_index_table` stay silent.
- `halted` for cancellation is stated as a deliberate design rule with its reason, in `### Task Status
  Transitions` and again as an operational note, because `:40` and `:108` already promise `halted` is
  terminal and non-resumable; without the new sentence the two passages would read as contradicting
  the cancellation rule.
- No numeric configuration value is written (the stale grace period is named, not quantified), per
  `skills/DESIGN.md` "No concrete configuration values".

## Alternatives considered

- Document the state machine in `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`: that
  chapter covers session, message and diagnostic persistence and its row is not in the Plan's frozen target
  list; adding the workflow task state machine there would create a second canonical source for a durable
  record that chapter does not otherwise describe.
- Extend the existing `### Workflow Status` subsection instead of adding one: that subsection documents
  what `Orchestrator.workflow_status()` reports to the operator (`running` / `enabled` / `unknown`), a
  different concept from the persisted `tasks.status` value, and merging them would conflate a
  reporting API with the durable record.
- Add the state machine to `## Turn-by-turn State Changes`: that region describes in-memory turn state
  (`ctx.*`) and its table is the per-turn mutation reference, not the durable task record.
- Put the cancellation rule only in `## Operational Notes`: the Plan requires both chapters to state the
  same state machine (`AC-9`), and `### Task Status Transitions` is the row the other chapter points at.
- Duplicate the full six-row table in `agent_06_04`: rejected — `check_docs_quality.py`'s
  `check_content_similarity` compares sections across documents, and the Plan names `agent_03_03` as
  the canonical source precisely so the other chapter points instead of repeats.

## Implementation
### Target file

`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

- 137 lines / 7060 B at HEAD `6fcbb7e0c`; docs size gate 24576 B.
- Insertion point: after the blank line at `:73` (end of `### Workflow Status`), before `### Workflow
  Stages` at `:74`.

### Procedure

1. Land `implementations/20261024-083059_04_*` and `implementations/20261024-092307_09_*` first, then
   re-read the file and re-take the four anchors; every line number below is the HEAD `6fcbb7e0c`
   position.
2. Land `implementations/20261024-144732_01_scripts_agent_workflow_engine_adapter.py.md` before this
   row commits, so the documented state machine matches the shipped behavior.
3. Insert `### Task Status Transitions` per `Method` step 1.
4. Amend `### Startup Recovery`, `## Operational Notes` and `## Known Limitations` per `Method`
   steps 2-4.
5. Run the docs checker set in `Validation plan` and confirm no finding names this file (`AC-9`).

### Method

1. Insert after `:73`:

   ```markdown
   ### Task Status Transitions

   The persisted turn outcome lives in the workflow `tasks` table. Each outcome has exactly one writer.

   | Turn exit | `tasks.status` | Written by | Reason |
   |---|---|---|---|
   | All stages complete | `completed` | workflow engine | so that the record is written at the moment the transition happens and no second owner has to re-derive it |
   | A stage raises and the engine re-raises it | `failed` | workflow engine | the engine observes the failing stage directly |
   | A retryable stage exhausts `max_attempts`, or a stage times out | `halted` | workflow engine | the engine stops the run itself |
   | The turn is cancelled while a stage is running | `halted` | turn adapter | the engine cannot observe cancellation, so the adapter records the stop in the existing terminal vocabulary instead of introducing a new status |
   | The engine completes but the turn reported a soft error | `failed` | turn adapter | a downgrade the engine cannot see, because the soft error never became a stage exception |
   | The turn fails before the engine starts | `pending` | neither | the row keeps the value it was created with, because no stage ever ran |

   - A successful turn produces exactly one `completed` write.
   - Cancellation is recorded `halted` on purpose: no `cancelled` status exists, and `halted` is already
     the terminal, non-resumable state described in [Resuming Existing Tasks](#resuming-existing-tasks)
     and in `## Operational Notes`.
   - Status writes made by the adapter are best-effort: a persistence failure is logged at error level
     with the task id and the intended status, and is never reported to the user as an LLM error.
   - A cancelled turn is distinguishable from a retry-exhausted halt by the attempt records: the
     abandoned attempt carries no error classification.
   ```

2. In `### Startup Recovery`, after the sentence at `:104`, add:

   ```markdown
   It repairs attempt records only: it never changes the persisted task status, so a task left `running`
   or `halted` by an earlier process stays as it was.
   ```

3. In `## Operational Notes`, after the existing bullet at `:108`, add:

   ```markdown
   - `halted` is also the recorded outcome of a cancelled turn. The adapter records it because the engine
     does not observe cancellation, and it uses the same terminal state so the resume guard needs no new
     case.
   - A persisted task status is written by one owner per outcome; see [Task Status
     Transitions](#task-status-transitions).
   ```

4. In `## Known Limitations`, after the bullet at `:112`, add:

   ```markdown
   - A cancelled turn leaves its in-flight attempt open until the next process start, when startup
     recovery closes it after the stale grace period. The task record itself is not repaired by that
     pass.
   ```

### Details

- Heading levels: `## Responsibility Boundary` (`:52`) > `### Task Status Transitions`. No `####` is
  introduced, so `check_broken_headings` and `check_duplicate_heading_numbers` stay silent.
- Table shape: four columns, every row four cells, separator row `|---|---|---|---|` —
  `check_malformed_tables` compares column counts.
- The two new inline anchors (`#resuming-existing-tasks`, `#task-status-transitions`) point at headings
  inside the same file. `check_docs_structure.py`'s `LINK_RE` only treats links ending in `.md` as file
  references, and `check_docs_consistency.py`'s broken-internal-link check behaves the same, so a bare
  same-file anchor is not resolved as a file path. If the checker reports either anchor, replace the
  anchor link with a plain cross-reference to the section name.
- The row header `| Turn exit | ... | Written by | Reason |` deliberately avoids `Case`/`Scenario` +
  `Action` (`_ERROR_ACTION_TABLE_HEADER_RE`) and `Field`/`Type`/`Default`
  (`_FIELD_TYPE_TABLE_HEADER_RE`), and no new line matches `_DEFAULT_VALUE_RE` outside the table.
- `## Known Limitations` keeps its existing bullet; the added bullet is the `DR-006` limitation the Plan
  requires the docs to carry.
- Do not cite source-code line numbers or `scripts/**.py` paths in the new prose: those go stale and are
  outside this chapter's current style.

## Compatibility considerations

- The chapter has 9 inbound document links (verified by `grep -rn "agent_03_03" docs/`); headings are
  added, not renamed, so inbound links and `related` front matter stay valid.
- `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` (front matter `:17`),
  `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md:31` and
  `docs/23_agent/agent_03_01_turn-processing-flow-overview.md` (front matter `:10`) must keep pointing here
  consistently; they are read, not edited (`REQ-010`).
- `agent_06_04`'s `### Persistence of Partial Completion` is aligned by the sibling procedure so the two
  chapters do not disagree (`AC-9`).
- `## Workflow Status` keeps its meaning (the operator-facing `Orchestrator.workflow_status()` value);
  the new subsection names the durable record, so the two must not be merged.
- No `docs/00_index.md` change: neither this chapter nor `agent_06_04` has its own task-scope row; that
  gap is `UNK-04` and is unresolved owner question, not this row's work.
- No code, test, config or generated-document interaction: this is prose only.

## Security considerations

- The documented error-level log line names only the task id and the intended status; the chapter must
  not describe it as carrying turn text or tool arguments, so the docs do not imply a wider log payload
  than the code writes.
- No secrets, no concrete configuration values, no port numbers (`check_docs_content_policy.py`'s
  `check_literal_port_number`).

## Rollback considerations

- Revert with `git checkout HEAD~1 -- docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`.
- If the adapter row (`_01`) is reverted while this chapter stays, the chapter describes behavior the
  code no longer has; revert both together, or reword the table back to the pre-change ownership.
- The added passages are self-contained (one new subsection plus three appended items), so partial
  rollback is possible without orphaning a heading; the `## Operational Notes` anchor link must be
  removed together with the new subsection if only one part is rolled back.

## Validation plan

- `uv run python tools/check_docs_structure.py "docs/23_agent/agent_03_03*.md"` — must print
  "All checks passed" (baseline: it does today).
- `uv run python tools/check_docs_quality.py` — no finding naming this file (baseline: none today).
- `uv run python tools/check_docs_content_policy.py` — no warning naming this file; re-run with
  `--strict` to confirm the new content does not exit 1 through this file.
- `uv run python tools/check_docs_consistency.py --domain agent` — "No issues found."
- `uv run python tools/check_docs_japanese.py` — no Japanese text.
- `uv run python tools/check_metadata_field_policy.py` — no new Metadata or Status field (`GV-016`).
- Manual cross-read: `## Operational Notes` and `### Task Status Transitions` must agree with
  `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`'s `### Persistence of Partial
  Completion` and with `### Resuming Existing Tasks` (`:40`) on the `halted` rule.
- `uv run python tools/stale_detector.py implementations/20261024-144732_03_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`
  — no `source_missing` finding.

## Completion criteria

- `### Task Status Transitions` exists under `## Responsibility Boundary` after `### Workflow Status`
  and states all six exit paths with their single writer (`REQ-010`, `AC-9`).
- The chapter states the `cancelled`-to-`halted` rule, the best-effort status write with error-level
  logging, and that startup recovery repairs attempts only and never a task row (`REQ-010`, `AC-9`).
- `## Known Limitations` carries the abandoned in-flight attempt limitation (`DR-006`).
- All docs checkers report no finding naming this file, and no other file was modified (`AC-9`).
- Front matter is unchanged.

## Out of Scope

- Registering this chapter in `docs/00_index.md`'s task-scope table (`UNK-04`).
- Editing `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`,
  `docs/23_agent/agent_03_01_turn-processing-flow-overview.md` or
  `docs/41_db/db_02_architecture_and_schema-schema-reference.md` (§7 belongs to
  `plans/20261023-084918_plan.md`).
- The `### Workflow Stages` stage table and `### Retry Mechanism` passages — owned by
  `implementations/20261024-083059_04_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`.
- The `verify` stage role, `execute_turn` teardown and halt state-clearing passages — owned by
  `implementations/20261024-092307_09_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`.
- Adding a `tasks.status` row to `### Turn State Mutation Reference` (`:120-128`).
- Any statement about resumability of a cancellation-halted task (`UNK-01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Not implemented; land after `083059_04`, `092307_09` and `_01`, then re-take anchors |
| 2 | Add or update tests per Validation plan | N/A: documentation row | — | — | Docs checkers are the validation |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Baselines recorded 2026-10-24 in Procedure-local findings |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This row is a docs row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Two active sibling procedures edit this same chapter (`083059_04`, `092307_09`); anchors must be re-taken after they land | False | — |
| 1 | The chapter must describe post-change behavior, so `_01` has to land first | False | — |
| 1 | Plan `UNK-04` (index registration) has no owner decision | False | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-010`
- **Source issue**: `issues/20261021-093421_turn003_task-status-overwritten-after-failure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-125756_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-144732
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
