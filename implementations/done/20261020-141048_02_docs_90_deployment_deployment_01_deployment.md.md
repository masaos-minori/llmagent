## Goal

Document the gate severity that `deploy/setup_services.sh` applies to the remote LLM services,
the `LLM_GATE_STRICT=1` switch, and the failure mode for an unreachable LLM service, and remove
the wording that says the script blocks until both services are healthy (REQ-005).

## Scope

Documentation only. Update `docs/90_deployment/deployment_01_deployment.md`:

- Section 2.3 "Starting Services": the sentence that says the script "blocks until both are
  healthy before proceeding".
- Section 3.3 "Failure Modes": one row for the LLM gate failure.

No source, test, or config change. The behavior described is implemented by seq 01.

## Assumptions

- After seq 01: an `agent-llm` failure aborts the script, an unreachable `embed-llm` only
  warns and the Event Bus still starts, and `LLM_GATE_STRICT=1` makes either failure abort with
  the unchanged `[FATAL] LLM services did not become ready within <N> attempts` message.
- The file is 24219 B against a 24576 B limit enforced by `tools/check_docs_structure.py`
  (no per-file exception), so the net growth budget is about 350 B.

## Design decisions

- **Replace, do not append.** Rewrite the existing clause so the net growth stays inside the
  size budget, and add a single combined Failure Modes row instead of one row per message.
- **Operator-facing wording only.** Describe the severity and the switch; do not copy the
  retry count, interval defaults, or script line numbers (`skills/DESIGN.md` Docs content
  policy).

## Alternatives considered

N/A: two table rows (one for `[FATAL]`, one for `[WARN]`) read better but exceed the size
limit; the combined row keeps the document valid.

## Implementation

### Target file

`docs/90_deployment/deployment_01_deployment.md`

### Procedure

1. In section 2.3, replace the "blocks until both are healthy" clause with the severity
   classification and the strict switch.
2. Add one row to the section 3.3 Failure Modes table.
3. Measure the file size; if it exceeds the budget, shorten only the new wording.

### Method

Current clause in section 2.3:

> ... it validates their remote `/health` endpoints (read from `config/agent.toml`) and blocks until both are healthy before proceeding, rather than spawning them — or MCP servers.

Replace with:

> ... it validates their remote `/health` endpoints (read from `config/agent.toml`), waiting for them rather than spawning them — or MCP servers. An unhealthy `agent-llm` aborts the script; an unreachable `embed-llm` only warns and the Event Bus still starts, unless `LLM_GATE_STRICT=1` requires both.

New Failure Modes row (after the existing rows):

> | `[FATAL] LLM services did not become ready within <N> attempts` | setup_services.sh | Start `agent-llm` (or `embed-llm` under `LLM_GATE_STRICT=1`); an unreachable `embed-llm` alone only warns |

### Details

- Keep the rest of section 2.3 (the Event Bus credential sentence, the manual `curl` checks)
  unchanged.
- The `[WARN]` line for an unreachable `embed-llm` is covered by the clause in section 2.3
  and the last phrase of the new row; do not add a second row.
- Measured on the current file: the wording above grows it by 317 B to 24536 B, 40 B under
  the limit. Run the size check last; do not trim unrelated text to make room.

## Compatibility considerations

N/A: documentation-only update. The prose describes the behavior introduced by seq 01 and must
be applied with or after it.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Read sections 2.3 and 3.3 and confirm no wording still says the script blocks until both
  services are healthy, and the strict switch and failure row are present.
- Documentation checkers from `routing.md`: `check_docs_quality.py`,
  `check_docs_structure.py docs/90_deployment/deployment_01_deployment.md`,
  `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain deployment`,
  `check_needs_confirmation_inventory.py`, `check_docs_japanese.py`.

## Completion criteria

- Section 2.3 states the `agent-llm` / `embed-llm` severity and `LLM_GATE_STRICT=1`.
- Section 3.3 has the LLM gate failure row.
- The file stays under 24576 B and all checkers pass.

## Out of Scope

- Any source, test, or config change.
- Other sections of this document and other documents (seq 03 covers the Event Bus doc).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update section 2.3 and add the section 3.3 failure row in `docs/90_deployment/deployment_01_deployment.md` | Completed | 20261020-185323 | 20261020-185323 | REQ-005 changed: docs/90_deployment/deployment_01_deployment.md (24536 B, limit 24576) |
| 2 | Run the documentation checkers from `routing.md` | Completed | 20261020-185323 | 20261020-185323 | AC-05 docs checkers pass (quality, structure, content-policy --strict, consistency deployment, needs-confirmation, japanese) |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261019-210938_ebops002_setup_services_llm_gate_blocks_eventbus.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261020-130914_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-141048
- **Related target files**: docs/90_deployment/deployment_01_deployment.md