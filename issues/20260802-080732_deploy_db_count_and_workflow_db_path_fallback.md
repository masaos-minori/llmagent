# Fix DB-count "3→4" error and document workflow_db_path fallback behavior in docs/02_deployment-part2.md

## Priority
High

## Summary
`docs/02_deployment-part2.md` §3.0 states "The agent uses three SQLite databases. All paths are configured in `agent.toml`," but confirmed source inspection shows 2 inaccuracies: (1) there are actually 4 databases — `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite` (confirmed via `agent.toml`'s `eventbus_db_path`, `scripts/db/create_schema.py`'s `create_eventbus_schema()`, and `deploy/init_db.sh` line ~58's eventbus table check); (2) `workflow_db_path` has no entry in `agent.toml` at all — it silently falls back to `scripts/db/config.py`'s dataclass default (`/opt/llm/db/workflow.sqlite`), unlike the other 3 paths which are explicitly configured.

## Reason for Change
This is a confirmed factual error with real operational risk — an operator relying on "3 databases, all in agent.toml" for backup/recovery planning would omit `eventbus.sqlite` entirely, and would not realize that changing the deployment's DB directory layout could silently leave `workflow.sqlite` pointing at a stale path (since it has no explicit config entry to update).

## Implementation Intent
Correct the database count to 4, explicitly listing all 4 by name, and explicitly flag `workflow_db_path`'s code-side-default-only status as an important operational caveat.

## Target Files or Areas
`docs/02_deployment-part2.md` (§3.0)

## Required Changes
- Replace "The agent uses three SQLite databases. All paths are configured in `agent.toml`." with: "The agent uses four SQLite databases: rag.sqlite, session.sqlite, workflow.sqlite, eventbus.sqlite. Paths for rag/session/eventbus are configured in `agent.toml`; `workflow_db_path` has no explicit entry in `agent.toml` and instead falls back to the code-side default (`scripts/db/config.py`, `/opt/llm/db/workflow.sqlite`) — a mismatch here is silent."
- Confirm whether `eventbus.sqlite`'s omission from the original "three databases" framing was intentional (Event Bus treated as a separate subsystem elsewhere) or an oversight — if a design rationale for treating it separately exists elsewhere, cross-reference it; otherwise treat as a straightforward correction.
- Confirm whether `workflow_db_path`'s missing `agent.toml` entry is an intentional design choice (code-default is canonical) or a configuration gap that should be filled — document whichever is confirmed, or mark as an explicit Needs Confirmation note if the author's intent can't be determined.

## Acceptance Criteria
The section states 4 databases by name; `workflow_db_path`'s fallback-to-code-default behavior and its silent-mismatch risk are explicitly documented.

## Testing Expectations
Not required (documentation-only). Manually re-verify all 4 DB paths/keys against `config/agent.toml` and `scripts/db/config.py`'s defaults before finalizing.

## Documentation Impact
`docs/02_deployment-part2.md` corrected — resolves 2 confirmed factual errors.

## Out of Scope
Do not add a `workflow_db_path` entry to `config/agent.toml` in this issue unless confirmed that this is the intended fix (that would be a config/implementation change, not documentation) — if confirmed, file it as a separate implementation issue instead.

## AI Implementation Instruction
This is a confirmed factual error (DB count, workflow_db_path fallback) — apply directly. If the intent behind either gap (eventbus exclusion, workflow_db_path omission) can't be confirmed from context, state that explicitly as an open question rather than asserting an unconfirmed rationale.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §4 強化候補 (§3.0 DB一覧), §5 例3, §6 (DB台数「3つ」記述とeventbus.sqliteの欠落, workflow_db_pathのagent.toml不記載)
- Generated at: 2026-08-02
