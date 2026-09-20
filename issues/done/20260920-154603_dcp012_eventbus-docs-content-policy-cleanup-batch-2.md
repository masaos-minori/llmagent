# EventBus docs content policy cleanup (batch 2)

## Priority
Medium

## Summary
Remove the mechanically-derivable content flagged by `tools/check_docs_content_policy.py`
(`GV-021`) across five EventBus documents — two literal port numbers, a seven-line
config-file inventory correspondence list, and five full JSON payload examples — per
`skills/DESIGN.md` Docs content policy — remove/retain.

## Background
`docscope1`/`docscope2` (see `issues/done/`) established the Docs content policy and the
`check_docs_content_policy.py` detection tool. A prior EventBus cleanup issue
(`issues/done/20260905-153715_dcp006_eventbus_docs_content_policy_cleanup.md`) already
removed one literal port number from
`06_eventbus_05_configuration-and-operations.md`, but subsequent feature commits (e.g.
`d743e6639` centralizing operational thresholds into `EventBusConfig`) reintroduced new
findings in the same and adjacent files — see Problem. `docs/00_governance_04_documentation-checks.md`'s `GV-021` entry itself already notes this domain has unresolved literal-port-number findings as of 2026-09-05 ("content-migration work removing port numbers from those files has not started").

## Problem
`uv run python tools/check_docs_content_policy.py` (run 2026-09-20) reports the
following unresolved findings in EventBus documents:
- `06_eventbus_03_persistence_schema_and_replay.md:156`, `:185` — literal port number
  (`8080`, inside `uvicorn ... --port 8080` operational runbook commands)
- `06_eventbus_05_configuration-and-operations.md:55`-`:62` — config-file inventory
  correspondence entries (a bullet-per-field "Configuration Fields" list restating
  `EventBusConfig` field names/purposes/defaults)
- `eventbus/01_dlq_operations.md:27` — full JSON payload example (paginated list
  response body)
- `eventbus/03_replay_operations.md:48` — full JSON payload example (paginated replay
  response body)
- `eventbus/health-endpoint.md:34`, `:103`, `:131` — full JSON payload examples (healthy
  and degraded `/health` response bodies)

## Reason for Change
The port numbers and config-field list duplicate `EventBusConfig`
(`scripts/eventbus/config.py`) — per `docs/00_governance_01_documentation-policy.md`
Claim Type Taxonomy, `production-effective-value`/`configuration-schema` claims whose
canonical source is the config file/dataclass, not the runbook prose. The JSON payload
examples duplicate the actual response schema the corresponding endpoint handler
produces (`api-contract` claim type) — a field added or removed from the response would
require three separate doc edits to stay in sync, which is exactly the drift mode this
policy targets.

## Implementation Intent
Apply `skills/DESIGN.md` Avoid implementation-reference duplication and Docs content
policy — remove: for the runbook commands, keep the command shape but replace the
literal port with a placeholder or a pointer to the configured `port` value (per "No
concrete configuration values" — a config value belongs to the config file, not
hardcoded prose); for the Configuration Fields list, replace the per-field bullets with
a pointer to `EventBusConfig` and retain any constraint/rationale bullets that already
follow it (per Docs content policy — retain and the "Recency Is Not Authority"
precedent already applied to this same file's per-role-token section); for each JSON
example, keep only the fields that carry non-obvious health/degradation semantics
already explained in surrounding prose and point to the endpoint handler for the exact
schema, rather than reproducing every key.

## Target Files or Areas
- `docs/06_eventbus_03_persistence_schema_and_replay.md`
- `docs/06_eventbus_05_configuration-and-operations.md`
- `docs/eventbus/01_dlq_operations.md`
- `docs/eventbus/03_replay_operations.md`
- `docs/eventbus/health-endpoint.md`

## Required Changes
1. `06_eventbus_03`: replace the two literal `8080` occurrences in the WAL-checkpoint
   runbook commands (lines ~156, ~185) with a placeholder (e.g. `<port>`) or a note that
   the port is read from the deployed `EventBusConfig`.
2. `06_eventbus_05`: replace the "Configuration Fields" bullet list (lines ~55-62) with
   a pointer to `EventBusConfig`; keep the per-role-token bullets and the cross-field
   constraint prose immediately below it untouched (already compliant, not flagged).
3. `eventbus/01_dlq_operations.md`, `eventbus/03_replay_operations.md`: replace each full
   JSON response example with a one-line description of the shape (pagination envelope
   plus item list) and a pointer to the route handler for the exact schema; keep the
   `limit`/`offset` parameter table above it in `01_dlq_operations.md` untouched — it is
   a request-parameter contract already covered by a different finding class, not this
   one.
4. `eventbus/health-endpoint.md`: replace the healthy and degraded response examples
   with a short description of the fields that carry degradation semantics
   (`status`, `degraded_reasons`) and a pointer to the health-check handler for the full
   schema.
5. Re-run `uv run python tools/check_docs_content_policy.py` and confirm zero findings
   for these five files.

## Constraints
- Do not alter any other content in these five files beyond the flagged
  lines/lists/examples and their immediately surrounding prose.
- Do not remove the per-role-token bullets or cross-field constraint prose in
  `06_eventbus_05_configuration-and-operations.md` — those were confirmed compliant
  during this issue's investigation (not flagged by the tool).
- This issue covers only the EventBus findings from the 2026-09-20 tool run; the
  remaining literal-port-number findings across other domains noted in `GV-021`'s
  history are out of scope (see Out of Scope).

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero findings for the five
  files in Target Files or Areas.
- Each edited runbook command still executes the same operation (only the port literal
  is replaced/parameterized); each edited JSON example section still tells the reader
  what to look for without reproducing the full schema.
- `uv run python tools/check_docs_structure.py` passes for the five files.

## Testing Expectations
Documentation-only change. Run `uv run python tools/check_docs_content_policy.py`,
`uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`
(scoped to the five files). `check_docs_consistency.py` has no dedicated `eventbus`
`--domain` flag (confirmed during investigation of a prior EventBus issue,
`issues/done/20260905-153715_dcp006...`) — this is a pre-existing gap, not something to
fix here. No `pytest`/`mypy`/`ruff` run required.

## Documentation Impact
Yes — this issue is itself a documentation cleanup. No `docs/*.md` outside the five
listed files should need changes.

## Out of Scope
- Any EventBus document not listed in Target Files or Areas.
- Literal-port-number findings in other domains referenced by `GV-021`'s historical note
  in `docs/00_governance_04_documentation-checks.md` — file separate per-domain issues
  if a fresh tool run confirms they still exist.
- Adding a dedicated `--domain eventbus` flag to `check_docs_consistency.py`.
- Extending `check_docs_content_policy.py`'s detection rules.

## Dependencies
N/A: none — independent of the RAG/MCP/Agent/Shared batches filed alongside this issue
(different files, no shared edit surface).

## Unresolved Questions
N/A: none — each finding above was confirmed by a direct tool run and file read on
2026-09-20.

## AI Implementation Instruction
Process the five files independently, one at a time. For each: read the flagged
line(s) and enough surrounding context to preserve meaning, replace the
mechanically-derivable content with a canonical-source pointer or placeholder per
Required Changes, then re-run `tools/check_docs_content_policy.py` scoped mentally to
that file before moving to the next. Do not touch files outside Target Files or Areas,
and do not remove the per-role-token / constraint content in `06_eventbus_05` that was
confirmed compliant during investigation.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-154603
- **Related target files**: see Target Files or Areas above
