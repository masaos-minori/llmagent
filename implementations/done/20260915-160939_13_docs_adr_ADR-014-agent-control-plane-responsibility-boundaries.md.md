## Goal
Remove ADR-014's redundant file/class/config/test list from `## Implementation
Notes` once reconciled into `### Implementation References`, per `REQ-013` —
including correcting a stale test-path glob the ADR's own text already flagged
as unconfirmed.

## Scope
- In scope: add `scripts/mcp_servers/shell/shell_service.py` to References
  (confirmed to exist, confirmed absent); verify and add the corrected test
  path(s) (Notes' own `tests/agent/test_llm_turn_executor*.py` glob does not
  resolve — confirmed via `find` that the actual file is
  `tests/agent/test_llm_turn_runner.py`); delete the Notes list; insert the
  one-line pointer.
- Out of scope: this ADR's own pre-existing `## Known Deviations` section
  (lines 201-203, a dead-code issue) — untouched.

## Assumptions
- The one-line pointer is used verbatim.
- `tests/agent/workflow/test_workflow_engine.py` and the `test_orchestrator*.py`
  glob (matching `tests/agent/test_orchestrator.py`,
  `tests/agent/test_orchestrator_bg_failure_threshold.py`) were confirmed to
  resolve to real files during Plan creation — only the `test_llm_turn_executor*.py`
  glob needs correction.

## Design decisions
- Notes' own text already hedges its test citation with "正確なファイル名は
  実装時に確認" (exact filenames to confirm at implementation time) — this is
  exactly that implementation-time confirmation. Do not propagate the
  unconfirmed/stale glob into References merely because it was written in Notes;
  add only the verified, corrected path.
- `shell_service.py` has no specific symbol named in either copy — add it at the
  same file-level specificity Notes itself uses.

## Alternatives considered
- Add the literal glob `tests/agent/test_llm_turn_executor*.py` to References
  as-is, preserving Notes' own uncertainty — rejected; a glob that resolves to
  zero files is not a valid citation, and References is meant to be this ADR's
  reliable, canonical source, not a place to canonize an already-flagged
  uncertainty.

## Implementation
### Target file
`docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md`

### Procedure
1. Re-verify current line numbers: confirm the Notes list is still at lines
   192-195 and References at 249-255 (this ADR's own `## Known Deviations` at
   201-203 is unaffected).
2. Re-confirm via `ls scripts/mcp_servers/shell/shell_service.py` that it still
   exists and is still absent from References.
3. Re-confirm via `find tests -iname "*llm_turn_executor*"` (expect no match)
   and `ls tests/agent/test_llm_turn_runner.py` (expect success) that the
   corrected test path is still accurate.
4. Add `scripts/mcp_servers/shell/shell_service.py` to References.
5. Add `tests/agent/test_llm_turn_runner.py` to References' test citation
   (replacing/supplementing the stale glob reference — Notes' own text is not
   modified by this step, only References; Notes' hedge remains until step 6
   deletes it).
6. Delete the Notes list (lines 192-195: 実装ファイル / 主要ClassまたはFunction
   / 設定ファイル、設定Key / 対応するテスト — including its "正確なファイル名は
   実装時に確認" hedge, now resolved).
7. Insert: "See Related Documents > Implementation References for the current
   file/symbol list."

### Method
Use `Edit` (exact-string replacement) — one call per step 4-7.

### Details
- Do not touch this ADR's `## Known Deviations` section (201-203).
- Verify `tests/agent/workflow/test_workflow_engine.py` and
  `tests/agent/test_orchestrator*.py` are still accurate (re-run `ls`) before
  finalizing References' test bullet, per the Plan's own blanket mandatory
  re-verification requirement — do not rely solely on this document's
  Assumptions section.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md`
if validation fails.

## Validation plan
- `ls scripts/mcp_servers/shell/shell_service.py` — must resolve.
- `find tests -iname "*llm_turn_executor*"` — expect no match; `ls tests/agent/test_llm_turn_runner.py` — must resolve.
- `ls tests/agent/workflow/test_workflow_engine.py tests/agent/test_orchestrator*.py` — must resolve.
- Manual diff: confirm References includes `shell_service.py` and the corrected test path; confirm Notes list (including the hedge) removed.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md` — zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md` — record baseline, confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — zero findings.

## Completion criteria
- References includes `shell_service.py` and the corrected, verified test path(s)
  (`tests/agent/test_llm_turn_runner.py`, `tests/agent/workflow/test_workflow_engine.py`,
  `tests/agent/test_orchestrator*.py`) — no unresolved glob remains.
- `## Implementation Notes` contains only the one-line pointer plus boilerplate.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- This ADR's `## Known Deviations` section.
- Any other section of ADR-014.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-163431 | Confirmed test_llm_turn_executor* glob does not resolve (find returned nothing), used corrected test_llm_turn_runner.py instead; added shell_service.py; deleted Notes list; inserted pointer |
| 2 | Add or update tests per Validation plan | Completed | 20260915-163431 | 20260915-163431 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-163431 | 20260915-163431 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 1 pre-existing unrelated finding, confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-163431 | 20260915-163431 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-013 — reconcile shell_service.py + verified tests, delete Notes list
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md