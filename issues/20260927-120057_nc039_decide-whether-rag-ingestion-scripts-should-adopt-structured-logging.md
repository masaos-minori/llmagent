# Decide whether RAG ingestion scripts should adopt structured logging

## Priority
Low

## Summary
Obtain an owner decision on whether `crawler.py`, `chunk_splitter.py`, and `ingester.py` should adopt `structured_log=True` (JSON-lines output), closing Needs Confirmation item NC-039.

## Background
`docs/rag_05_3-logging.md`'s Implementation Notes cross-reference NC-039, which asks whether these three RAG ingestion scripts intentionally stay on text-format logging, or whether JSON-lines output was intended and never enabled.

## Problem
Confirmed still current via direct read: none of `scripts/rag/crawler.py`, `scripts/rag/ingestion/chunk_splitter.py`, or `scripts/rag/ingestion/ingester.py` pass `structured_log=True` to `shared/logger.py`'s `Logger` (`structured_log: bool = False` default, confirmed at `scripts/shared/logger.py` line 126). Context fields such as `turn_id`, `session_id`, `rag_query_id`, `workflow_id`, and `task_id` passed via `extra={...}` are consequently dropped from these three scripts' text-format output — `shared/logger.py`'s own docstring confirms `structured_log=True` is what "switches to JSON-lines" output that would preserve such fields.

## Reason for Change
If JSON-lines output was intended for these scripts, this is a silent observability gap (context fields are being dropped, not merely formatted differently) rather than a documented decision — worth resolving before it causes an unexplained gap during an incident investigation.

## Implementation Intent
Present the owner with the confirmed current behavior and ask for a ruling: enable `structured_log=True` on these three scripts (a small, low-risk config-flag change), or confirm text-format logging is intentional for them (e.g. because they are typically run interactively rather than as long-running services whose logs are machine-parsed).

## Target Files or Areas
- `scripts/rag/crawler.py`
- `scripts/rag/ingestion/chunk_splitter.py`
- `scripts/rag/ingestion/ingester.py`
- `scripts/shared/logger.py` (reference only)
- `docs/rag_05_3-logging.md` (Implementation Notes)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (NC-039 entry)

## Required Changes
- Present the owner with the confirmed current behavior (three scripts drop the listed context fields in their output).
- If the owner rules JSON-lines was intended: add `structured_log=True` to each of the three scripts' logger configuration.
- If the owner rules text-format is intentional: document that decision and its rationale in `docs/rag_05_3-logging.md`.
- Remove NC-039 from Active Items once resolved.

## Constraints
- If enabling `structured_log=True`, confirm no downstream tooling (dashboards, log parsers, `tools/`) depends on these three scripts' current text-format output before changing it.

## Acceptance Criteria
- The owner's ruling (enable structured logging, or confirm text-format is intentional) is recorded in `docs/rag_05_3-logging.md`.
- If enabled: the three scripts' log output is confirmed to be valid JSON-lines and to include the previously-dropped context fields.
- NC-039 is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items.

## Testing Expectations
If `structured_log=True` is enabled: a manual or automated check that log output from each of the three scripts parses as valid JSON-lines and includes the expected context fields. If the ruling is "no change," no test change is needed.

## Documentation Impact
Update `docs/rag_05_3-logging.md`'s Implementation Notes to record the owner's ruling and rationale. Remove the NC-039 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` once resolved.

## Out of Scope
- Changing `shared/logger.py`'s `structured_log` mechanism itself.
- Any other RAG script's logging configuration beyond these three.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none — the decision itself is this issue's entire content; the evidence needed to present it is already confirmed.

## AI Implementation Instruction
Do not enable `structured_log=True` on any of the three scripts without the owner's explicit ruling recorded first. Before enabling it, check for any existing consumer of these scripts' current text-format log output (dashboards, parsers, other tools) that a format change could break, and report that check's result alongside the change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-120057
- **Related target files**: scripts/rag/crawler.py, scripts/rag/ingestion/chunk_splitter.py, scripts/rag/ingestion/ingester.py, docs/rag_05_3-logging.md
