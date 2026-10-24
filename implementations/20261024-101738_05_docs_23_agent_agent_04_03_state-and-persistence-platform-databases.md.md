# Implementation Procedure: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` — align the StateStore idempotency statement

## Goal

Make the agent-side document say what the task key now means, and record how a retained
`workflow.sqlite` behaves for a new session (`REQ-008` — documented meaning, scope, and
retained-DB behavior).

## Scope

- The `StateStore` sentence under `### StateStore Responsibility Scope` (`:71`, section heading at
  `:70`).
- One added bullet in `## Operational Notes` (heading at `:83`), after the existing
  `begin_stage_if_new` bullet at `:86`.
- `## Key Constraints` (`:73`), the DB table row at `:40` that routes `workflow.sqlite` to
  [db_02](db_02_architecture_and_schema-schema-reference.md) section 7, `## Keywords` (`:88`), and the
  front matter are untouched.

## Assumptions

- `:85` already states that no slash command exposes `workflow.sqlite` for maintenance, so the new
  bullet must agree that nothing has to be deleted from a retained file.
- `:71` is the only sentence in this document that mentions task idempotency; stage-level idempotency
  is described separately at `:86` and must stay distinct.

## Design decisions

- Keep stage-level idempotency (`begin_stage_if_new`, `processed_events`) and task-key uniqueness in
  separate statements, because the Plan's `Reference Files` row for `agent/workflow/idempotency_ops.py`
  exists precisely to prevent conflating them.
- Record the environment condition (the production `workflow.sqlite` was not inspected during
  verification) as a known condition rather than as evidence the defect is absent (`UNK-01`).

## Alternatives considered

N/A: the Plan's `Documentation Impact` fixes this file as the agent-side home.

## Implementation

### Target file

`docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

### Procedure

1. Extend the `:71` sentence with the task-key scope clause; keep its existing structure and its link
   to `agent_09_01_data-layer-session-db.md`.
2. Append one bullet to `## Operational Notes` after `:86`.
3. Leave all other lines byte-identical.

### Method

`:71` becomes:

`StateStore` manages tasks, attempts, artifact references, and idempotency (duplicate detection and
atomic attempt initiation) in `workflow.sqlite`, through the operation modules under
`agent/workflow/`. A task's idempotency key is globally unique per row and is not derived from the
session or turn values the caller passes; `session_id` and `turn_number` stay recorded metadata. See
[agent_09_01_data-layer-session-db.md](agent_09_01_data-layer-session-db.md).

The new bullet after `:86`:

- A retained `workflow.sqlite` needs no cleanup when a new session starts: task keys are new for every
  insert, pre-existing task rows remain readable, and resume uses `task_id`. Whether the production
  database currently holds task rows was not inspected during verification, so this is stated as a
  contract, not as an observed state.

### Details

- Both statements stay at contract level: no code snippet beyond naming `task_id`, `session_id`, and
  `turn_number` as columns (`check_docs_content_policy.py --strict`).
- The `:71` clause order keeps the original sentence intact and appends, so the section's existing
  cross-links are not re-flowed.

## Compatibility considerations

N/A: documentation-only; `:40` already routes schema detail to db_02 §7, which row 4 of the same Plan
edits in the same cycle.

## Security considerations

N/A: no runtime path, credential, or configuration value is stated.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py` → no issue.
- `uv run python tools/check_docs_structure.py "docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md"`
  → no finding.
- `uv run python tools/check_docs_content_policy.py --strict` → no finding.
- `uv run python tools/check_docs_consistency.py --domain agent` → no finding.
- The whole-glob structure run remains blocked by the pre-existing
  `agent_13_reference-api-generated.md` size finding recorded as `BLK-001` in
  `plans/done/20261023-183637_plan.md`; scoping the command to this file is the usable form until that
  ceiling decision is recorded.

## Completion criteria

- The document states the key is globally unique per task row and not derived from caller-supplied
  session/turn values (`AC-7`).
- The retained-database behavior and the un-inspected production state are both stated (`REQ-008`).
- Task-level and stage-level idempotency remain described as different mechanisms.
- The docs checkers report nothing for this file.

## Out of Scope

- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` §7 — owned by
  `implementations/20261024-101738_04_docs_41_db_db_02_architecture_and_schema-schema-reference.md.md`.
- `scripts/agent/workflow/task_ops.py` and the two workflow test files — rows 1 to 3.
- `docs/00_index.md`: no index row change is in this Plan's target table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the `:71` StateStore sentence | Pending | — | — | Keeps existing link |
| 2 | Append the retained-database bullet to `## Operational Notes` | Pending | — | — | Records `UNK-01` |
| 3 | Run the documentation checkers named in `routing.md` | Pending | — | — | Structure scoped to this file |

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
- **Requirement ID**: `REQ-008` (document the key's meaning, scope, and retained-DB behavior)
- **Source issue**: `issues/20261021-093421_turn001_task-idempotency-key-collides-across-restarts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-084918_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-101738
- **Related target files**: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`
