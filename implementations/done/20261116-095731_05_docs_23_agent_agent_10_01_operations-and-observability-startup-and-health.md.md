## Goal

Correct the interruption description in the startup and health document so it states which startup stages observe a shutdown request, that the stage in progress is cancelled, and that started servers are rolled back before a quiet exit (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the sentence about signals during the startup sequence (near the start of the orchestrator description) and the section "SIGINT/SIGTERM Interruption During Startup" in `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`.
- Out of scope: the `readiness` bullet (Plan `startrev005`), the startup validation description (Plan `startrev006`), other documents, and any concrete value.

## Assumptions

- Execute after documents `01` and `02` of this Plan so the text describes landed behavior.
- Verified Step 3a (after documents `01` and `02` landed): `run()` races the event against `_check_services` and `_setup_prompt` via `_run_stage`, checks event boundaries before every stage in the `try` and after the last stage, and the MCP starter raises `StartupInterrupted` at its per-server boundaries while racing the event in stagger, retry and health-poll delays; cancelling the services stage now also sets the RAG stop event (document `02`'s handler). The document text to replace (line 39 and the section at lines 91-93) still describes only the delayed-timer race.
- Plan overlap judgment: this document is also a target of Plans `startrev005` and `startrev006`; each edits a different passage and no sentence is shared, so the edits are compatible; this Plan goes last.

## Design decisions

- Describe behavior as policy: the startup stages that wait on external services or on the RAG check and prompt setup observe a shutdown request and are cancelled; the synchronous local stages are covered by boundary checks between stages; on a request, the servers started so far are rolled back and the process exits with status 0 without a traceback. Keep the existing description of the MCP subprocess delay and health polling race. No timeouts, counts, ports or file names (`skills/DESIGN.md` Docs content policy).

## Alternatives considered

N/A: documentation-only row.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
1. Rewrite the sentence that says signals can fire during startup and are raced only against delayed timers, so it states the broader behavior in one or two sentences.
2. Rewrite the body of the "SIGINT/SIGTERM Interruption During Startup" section to name which stages observe a request, that the in-progress stage is cancelled, that started servers are rolled back, and that the exit is quiet with status 0.
3. Run the documentation checkers named in the Validation plan and fix findings in the changed text only.

### Method
- Keep the section heading and the existing statement about the quiet exit and the absent traceback; change only what the code no longer matches.

### Details
- Leave front matter, the Keywords section and unrelated sections untouched; do not add links.

## Compatibility considerations

N/A: documentation-only; no document is renamed or moved.

## Security considerations

N/A: no secrets or values are added.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- The document names the startup stages that observe a shutdown request and what is rolled back, matching the code (`REQ-006`, AC-6); all checkers above report no finding.

## Out of Scope

- Code, tests, other passages of the document, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the startup interruption passages to match the code | Completed | 20261116-214500 | 20261116-214800 | line 39 sentence and SIGINT/SIGTERM section rewritten to describe landed behavior from docs 01/02 |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261116-214800 | 20261116-215000 | check_docs_quality/structure/content_policy/consistency --domain agent/japanese all exit 0 |

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
- **Requirement ID**: `REQ-006` (startup document matches the code on interruption)
- **Source issue**: issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-221200_startrev004_startup-ignores-shutdown-signal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095731
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`