## Goal
Replace `docs/05_agent_05_llm-and-streaming.md`'s "Partial Completion Persistence
Rules" table (lines 52-56) and "Error Type Design" table (lines 62-70) with pointers to
their canonical source, per `REQ-001`/`REQ-002` (Plan
`plans/20260920-160327_plan.md`), so `tools/check_docs_content_policy.py` reports no
finding at either location.

## Scope
In scope: the two flagged tables (lines 48-70, i.e. both `### Partial Completion
Persistence Rules` and `### Error Type Design` subsections, headings included) only.
Out of scope: every other section of this file — `## Purpose`, the `### LLMClient
Objectives`/`Hot-Reloadable Settings`/`Request Payload`/`Streaming Design Intent`
subsections above the flagged tables, `### Runtime Parameter Generation` below them,
`## Responsibility Boundary`, `## Key Constraints`, `## Operational Notes`, and `##
Known Limitations` — none of these were flagged by `check_docs_content_policy.py`
(re-confirmed 2026-09-20). Also out of scope, per the Plan: the three false-positive
findings in `05_agent_06_02`/`05_agent_06_03`/`05_agent_10_05` (do not touch those
files) and the pre-existing missing `## Related Documents` section in this file.

## Assumptions
The two findings (lines 52, 62) and the file's exact current content (re-verified via
Read during this document's creation) have not shifted since the Plan was frozen — no
commit has touched this file, `scripts/agent/llm_turn_runner.py`, or
`scripts/shared/llm_exceptions.py` since.

## Design decisions
Replace each table with a one-sentence pointer to its Plan-confirmed canonical source:
`scripts/agent/llm_turn_runner.py`'s `partial_text` handling (lines 149-163) for the
persistence-rules table, and `scripts/shared/llm_exceptions.py`'s `LLMErrorKind`
(line 14)/`LLMTransportError` (line 27) for the error-type table. The persistence-rules
table's lead-in sentence ("Handled by the orchestrator's transport error handler:")
is updated to name the actual file (`scripts/agent/llm_turn_runner.py`) rather than the
generic "orchestrator," since Step 3's investigation (recorded in the Plan) found the
primary handling site is that module, not `orchestrator.py` itself (which only
consumes `partial_text` downstream).

## Alternatives considered
- Leave the "Handled by the orchestrator's..." lead-in sentence unchanged and only
  remove the table: rejected — "the orchestrator" is a generic, slightly inaccurate
  reference once the exact file is known; naming
  `scripts/agent/llm_turn_runner.py` directly gives the reader a precise place to look,
  consistent with the Plan's own corrected understanding.
- Remove both subsection headings along with their tables: rejected — the Plan's
  Requirements target the tables, not the headings; keeping `### Partial Completion
  Persistence Rules` and `### Error Type Design` preserves the document's navigable
  structure (e.g. for the `## Related Docs`/TOC-style cross-references elsewhere in
  this file series).

## Implementation
### Target file
`docs/05_agent_05_llm-and-streaming.md`

### Procedure
1. Read lines 46-71 to confirm current content matches the Plan's recorded evidence.
2. Replace lines 50-56 (the "Handled by the orchestrator's transport error handler:"
   sentence through the last table row) with one sentence: the exact case/action
   mapping for partial-completion persistence is implemented in
   `scripts/agent/llm_turn_runner.py`'s transport error handling.
3. Replace lines 60-70 (the "The `kind` of `LLMTransportError` is categorized as
   follows:" sentence through the last table row) with one sentence: the full set of
   `LLMTransportError.kind` categories is defined by `LLMErrorKind` in
   `scripts/shared/llm_exceptions.py`.
4. Leave the `### Partial Completion Persistence Rules` and `### Error Type Design`
   headings, and every other line in this file, unchanged.

### Method
Two independently revertable `Edit` calls against the same file: one for the
persistence-rules subsection (step 2), one for the error-type subsection (step 3). Do
not touch any other line.

### Details
Do not restate any of the three persistence-rules cases (non-empty `partial_text`,
empty `partial_text`, tool execution failure) or their actions — all are directly
readable from `scripts/agent/llm_turn_runner.py`. Do not restate any of the seven
`LLMTransportError.kind` category names or descriptions
(`HTTP_STATUS_RETRYABLE`/`HTTP_STATUS_FATAL`/`CONNECT_ERROR`/`READ_TIMEOUT`/
`HEARTBEAT_TIMEOUT`/`MALFORMED_SSE_FRAME`/`PREMATURE_EOF`) — all are directly readable
from `scripts/shared/llm_exceptions.py`'s `LLMErrorKind` definition. Note for
awareness only (no action required by this row): lines 115-117 (`### Retryable vs
Fatal Semantics`, in `## Key Constraints`, out of scope) and lines 111-113 (`###
Partial Completion Isolation`, also out of scope) already carry a design-intent
summary of part of what these two tables listed — this is why removing the tables
loses less design context than it might first appear, but neither of those existing
sections is part of this row's edit.

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
`N/A: no security-relevant content is touched`.

## Rollback considerations
Revert via `git checkout` on this one file. The two edits are independently
revertable from each other.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/05_agent_05_llm-and-streaming.md` (Plan `AC-1`, `AC-2`, `AC-3`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/05_agent_05_llm-and-streaming.md`
  — confirm the finding count does not exceed the one pre-existing missing `##
  Related Documents` finding already recorded in the Plan.
- `uv run python tools/check_docs_consistency.py --domain agent` — confirm no new
  drift finding.

## Completion criteria
Neither the "Partial Completion Persistence Rules" nor the "Error Type Design"
subsection contains a table; each states its canonical source instead; the
persistence-rules lead-in sentence names `scripts/agent/llm_turn_runner.py`
specifically; `check_docs_content_policy.py` reports zero findings for this file.

## Out of scope
- Every other section of this file (see Scope) — not flagged, not part of
  `REQ-001`/`REQ-002`.
- `docs/05_agent_06_02_tool-execution-and-approval-approval.md`,
  `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`,
  `docs/05_agent_10_05_operations-and-observability-monitoring.md` — confirmed false
  positives per the Plan; do not edit.
- The pre-existing missing `## Related Documents` section in this file.
- Extending `check_docs_content_policy.py`'s detection rules (tracked separately in
  `issues/20260920-154905_docschk02_recognize-fail-safe-fail-closed-rationale-in-content-policy-checker.md`,
  now moved to `issues/done/` per the Plan's own Dependencies note).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-170916 | 20260920-170916 | Adversarial verification: after removing the two flagged tables, the retained heading '### Error Type Design' fell within check_error_handling_table()'s 10-line heading window of the unrelated 'Runtime Parameter Generation' table (a distance-shrinkage side effect of the deletions), causing a new false-positive finding. Fixed by renaming the heading to '### LLMTransportError Kind Categories' (first word no longer matches _ERROR_HEADING_RE), preserving meaning while avoiding the pattern - not a scope change to the Runtime Parameter Generation table itself |
| 2 | Add or update tests per Validation plan | Completed | 20260920-170916 | 20260920-170916 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-170916 | 20260920-170916 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-170916 | 20260920-170916 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-001`, `REQ-002` — replace both flagged tables with canonical-source pointers
- **Source issue**: issues/20260920-154509_dcp011_agent-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-160327_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-163055
- **Related target files**: docs/05_agent_05_llm-and-streaming.md