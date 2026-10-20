## Goal

State in the Event Bus operations document that the Event Bus process has no dependency on the
remote LLM services, and when `deploy/setup_services.sh` withholds its launch (REQ-006).

## Scope

Documentation only. Update `docs/24_eventbus/eventbus_07_configuration-and-operations.md`,
section "Start Command". No source, test, or config change.

## Assumptions

- After seq 01 of the same Plan: the script launches the Event Bus when `agent-llm` is healthy
  and `embed-llm` is only warned about; it aborts before the launch when `agent-llm` fails, or
  when either service fails under `LLM_GATE_STRICT=1`.
- The plan's wording "Event Bus startup does not depend on the remote LLM services" was
  corrected during verification: a literal reading contradicts the `agent-llm` abort, so the
  text separates the process from the deployment script.

## Design decisions

- **Process versus script.** Say that the Event Bus process itself needs no LLM service, and
  that only the deployment script's health gate can withhold the launch.
- **One short paragraph** after the existing "Do not start the server with `uvicorn`"
  paragraph, with no new heading.

## Alternatives considered

N/A: a new subsection would be larger than the statement needs.

## Implementation

### Target file

`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure

1. In "Start Command", add one paragraph after the `uvicorn` warning paragraph and before
   the credential paragraph.

### Method

Add:

> The Event Bus process has no dependency on the remote LLM services (`embed-llm`, `agent-llm`). `deploy/setup_services.sh` withholds its launch only when `agent-llm` fails the health gate, or when either service fails under `LLM_GATE_STRICT=1`; an unreachable `embed-llm` alone does not prevent it.

### Details

- Do not restate retry counts or defaults; point readers to the deployment document only if a
  link is needed, using the existing link style of this document.
- Leave the start command block and the credential paragraph unchanged.

## Compatibility considerations

N/A: documentation-only update. Apply with or after seq 01.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Read "Start Command" and confirm the new paragraph is present and that nothing else changed.
- Documentation checkers from `routing.md`: `check_docs_quality.py`,
  `check_docs_structure.py docs/24_eventbus/eventbus_07_configuration-and-operations.md`,
  `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain deployment`,
  `check_needs_confirmation_inventory.py`, `check_docs_japanese.py`.

## Completion criteria

- The document states the process has no LLM dependency and names when the script withholds
  the launch.
- All checkers pass.

## Out of Scope

- Any source, test, or config change.
- Other sections and other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Event Bus independence paragraph to "Start Command" in `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Completed | 20261020-190020 | 20261020-190020 | REQ-006 changed: docs/24_eventbus/eventbus_07_configuration-and-operations.md |
| 2 | Run the documentation checkers from `routing.md` | Completed | 20261020-190020 | 20261020-190020 | AC-06 docs checkers pass; full suite re-run after all docs edits |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261019-210938_ebops002_setup_services_llm_gate_blocks_eventbus.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261020-130914_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-141048
- **Related target files**: docs/24_eventbus/eventbus_07_configuration-and-operations.md