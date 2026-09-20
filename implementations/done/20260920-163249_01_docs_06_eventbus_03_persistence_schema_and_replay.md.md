## Goal
Replace the two literal `8080` port occurrences (lines 156, 185) in
`docs/06_eventbus_03_persistence_schema_and_replay.md`'s WAL-checkpoint runbook
commands with a placeholder or a pointer to the deployed `EventBusConfig`, per
`REQ-001` (Plan `plans/20260920-160505_plan.md`), so
`tools/check_docs_content_policy.py` reports no finding at either location.

## Scope
In scope: the two `uvicorn ... --port 8080` lines (156, 185) only. Out of scope: every
other line in this file, including the two `curl http://127.0.0.1:8080/health` lines
(161, 190) — neither was flagged by `check_docs_content_policy.py` (re-confirmed
2026-09-20) and neither is part of `REQ-001` (see Design decisions for the
consistency implication this leaves); the three pre-existing `check_docs_structure.py`
structural findings for this file recorded in the Plan (missing `## Related
Documents`/`## Keywords` sections, a front-matter `source` field referencing a missing
`index.md`).

## Assumptions
The two findings (lines 156, 185) and the file's exact current content (re-verified
via Read during this document's creation) have not shifted since the Plan was frozen —
no commit has touched this file since.

## Design decisions
Replace `--port 8080` with `--port <port>` (a placeholder) in both commands, per the
Plan's Implementation intent ("replace the literal port with a placeholder ... per
`skills/DESIGN.md` 'No concrete configuration values'"). Step 3a's re-verification
found the two `curl http://127.0.0.1:8080/health` lines (161, 190) in the same runbook
still contain the literal `8080` and are not flagged — this is a **Plan Gap**, not a
blocking discrepancy: leaving them unedited creates a minor internal inconsistency
(one line in the procedure is parameterized, the next literal), but `REQ-001`'s scope
is explicitly the two flagged lines only, and editing unflagged lines would exceed this
row's frozen scope. Recorded here for the record, not acted on in this document — see
Out of scope.

## Alternatives considered
- Replace `8080` with the actual current deployed value re-read from
  `config/eventbus.toml`: rejected — this would itself violate `skills/DESIGN.md` "No
  concrete configuration values" (restating a live operational value in a runbook that
  should point to config, not hardcode it).
- Also parameterize the two `curl .../health` lines' port for internal consistency:
  rejected as exceeding this row's frozen `Implementation Target Files` scope (see
  Design decisions) — if this inconsistency is worth fixing, it belongs in a follow-up
  issue/Plan revision, not a scope expansion here.

## Implementation
### Target file
`docs/06_eventbus_03_persistence_schema_and_replay.md`

### Procedure
1. Read lines 148-192 to confirm current content matches the Plan's recorded evidence.
2. Edit line 156: `uvicorn eventbus.app:app --host 127.0.0.1 --port 8080 &` → `uvicorn
   eventbus.app:app --host 127.0.0.1 --port <port> &` (`<port>` denoting the value
   configured in the deployed `EventBusConfig`).
3. Edit line 185: `uvicorn scripts.eventbus.app:app --host 127.0.0.1 --port 8080 &` →
   `uvicorn scripts.eventbus.app:app --host 127.0.0.1 --port <port> &`.
4. Leave lines 161, 190 (the `curl` health-check commands) and every other line
   unchanged.

### Method
Two independent single-line `Edit` calls (steps 2 and 3) — each command block is
distinct (one uses `eventbus.app:app`, the other `scripts.eventbus.app:app`), so a
single `replace_all` on the string `--port 8080` would be unsafe if either module path
string were to also match a different, unintended location; verify each edit targets
only its own line.

### Details
Do not touch lines 161/190's `curl http://127.0.0.1:8080/health` — not flagged, out of
this row's scope (see Design decisions' Plan Gap note). Do not introduce a real
`config/eventbus.toml` value in place of `8080` — the placeholder `<port>` is the
correct replacement per the Plan's own "No concrete configuration values" rationale.

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
`N/A: no security-relevant content is touched`.

## Rollback considerations
Revert via `git checkout` on this one file. The two edits are independently
revertable from each other and from the other four Plan rows' files.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/06_eventbus_03_persistence_schema_and_replay.md` (Plan `AC-1`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/06_eventbus_03_persistence_schema_and_replay.md`
  — confirm the finding count does not exceed the three pre-existing findings already
  recorded in the Plan.

## Completion criteria
Both `uvicorn` startup commands use `--port <port>` instead of a literal `8080`; the two
`curl .../health` lines are unchanged; `check_docs_content_policy.py` reports zero
findings for this file.

## Out of scope
- Lines 161, 190 (`curl http://127.0.0.1:8080/health`) — not flagged, and a Plan Gap
  (internal consistency) is noted but not acted on here (see Design decisions).
- The three pre-existing `check_docs_structure.py` findings for this file — tracked in
  the Plan as pre-existing, out-of-scope structural findings.
- Any other `docs/*.md` file — see the Plan's other four target-file rows, each with
  its own implementation procedure document.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-171036 | 20260920-171036 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-171036 | 20260920-171036 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-171036 | 20260920-171036 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-171036 | 20260920-171036 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-001` — replace the two literal port numbers with a placeholder/pointer
- **Source issue**: issues/20260920-154603_dcp012_eventbus-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-160505_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-163249
- **Related target files**: docs/06_eventbus_03_persistence_schema_and_replay.md