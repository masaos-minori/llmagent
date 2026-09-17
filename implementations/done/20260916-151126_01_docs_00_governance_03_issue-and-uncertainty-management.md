## Goal

Register the previously-deferred ADR-010 Decision #9 vs. `call_rag_service()` parse-error discrepancy as a single Needs Confirmation entry (`NC-036`) in `docs/00_governance_03_issue-and-uncertainty-management.md` Part 2, since this Plan's own investigation found the classification (intentional refinement vs. unintended deviation) genuinely requires owner/architect judgment rather than a determination this document-only phase can make unilaterally.

## Scope

- Add a new Part 2 entry, `NC-036`, to `docs/00_governance_03_issue-and-uncertainty-management.md`'s Active Items, using the 15-field template.
- Cite ADR-010 Decision #9, `scripts/rag/pipeline_service.py::call_rag_service()`, and `test_json_parse_error_calls_set_fallback_reason` by name.
- Set `Assigned To: @data-eng` (RAG area lead per RACI Model) and `Blocking: No`.
- Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` after the edit and confirm it passes.

## Assumptions

- The classification question was independently re-investigated during this Plan's Step 2 verification and found genuinely mixed:
  - Evidence toward "intentional": the `except ValueError` branch is deliberately structured (explicit logging, descriptive fallback-reason string, symmetric with HTTPStatusError branch), and the function's docstring conceptually separates "valid empty result" from "failure/fallback," placing parse errors in the latter category.
  - Evidence toward "unintended": ADR-010 Decision #6 uses exhaustive enumeration of exactly three fallback-triggering conditions, explicitly excluding parse errors; Decision #9 then states the parse-error case explicitly and separately.
- No existing Part 1 or Part 2 entry already tracks this discrepancy (confirmed via grep).
- `@data-eng` maps to the RAG area lead per the RACI Model in `docs/00_governance_01_documentation-policy.md`.

## Design decisions

- Use the Needs Confirmation entry type — not a Known Issue or ADR amendment — because the mixed evidence makes a unilateral classification inappropriate.
- Follow the established 15-field template for Part 2 entries.
- Do not amend ADR-010 — that requires RACI approval this document-only phase cannot grant.

## Alternatives considered

- Registering a Part 1 Known Issue (`document-code-mismatch`) — rejected because the evidence is genuinely mixed; a Known Issue would assert the deviation is confirmed unintended, which this Plan's evidence does not establish with confidence.
- Amending ADR-010 directly — rejected because it requires RACI approval from `@data-eng` this document-only phase cannot itself obtain.

## Implementation
### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Locate Part 2's Active Items section and find the last existing entry (NC-035, approximately line 772).
2. Append the NC-036 entry after NC-035, following the 15-field template pattern used by other Part 2 entries.
3. Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` and confirm it passes.

### Method

Current state: Part 2's last entry is NC-035 (approximately line 772).

Required addition after NC-035:
```markdown
#### NC-036: ADR-010 Decision #9 vs. `call_rag_service()` parse-error discrepancy

- **Source File**: `scripts/rag/pipeline_service.py::call_rag_service()` / `ADR-010-rag-fallback.md`
- **Section/Line Number**: `call_rag_service()` (lines ~163-170) / Decision #9 (line 69)
- **Question**: Is `call_rag_service()`'s parse-error-triggers-fallback behavior an intentional, undocumented refinement of Decision #9, or an unintended deviation?
- **Evidence**: 
  - ADR-010 Decision #9 (line 69): "解析エラーはログに記録し、空結果として扱う" — parse errors should be logged and treated as an empty result, not a fallback trigger.
  - `scripts/rag/pipeline_service.py::call_rag_service()` (lines 163-170): `except ValueError` branch returns `None` (triggering fallback), with explicit logging and a descriptive `http_parse_error` fallback-reason string.
  - `scripts/shared/json_utils.py::parse_http_json()` (line 82): raises `ValueError` for invalid JSON body, per its own docstring's `Raises` section.
  - `tests/rag/test_rag_pipeline_service.py::test_json_parse_error_calls_set_fallback_reason` (line 241): exists, passes, asserts `result is None` with exactly one fallback reason recorded.
- **Impact**: An undocumented ADR deviation actively defended by a passing test — bypasses governance mechanism entirely if left unrecorded.
- **Required Action**: 
  1. If intentional: amend ADR-010 via ADR Change Protocol + RACI approval from `@data-eng`.
  2. If unintended: file a Part 1 `document-code-mismatch` Known Issue.
- **Status**: open
- **Assigned To**: @data-eng
- **Last Reviewed**: [today's date]
- **Priority**: High
- **Related NC**: None
- **Resolution Target**: Next RAG architecture review
- **Blocking**: No
```

### Details

The entry must use the same 15-field template as other Part 2 entries. The `Last Reviewed` field should contain today's date. The `Required Action` field must name both remaining resolution paths so no re-investigation is needed once assigned.

## Compatibility considerations

- This is a documentation-only change — no code compatibility impact.
- The entry cross-references ADR-010, which is governed by a different team — the Needs Confirmation routing ensures proper ownership.

## Security considerations

- No security impact — documentation-only change.

## Rollback considerations

- If the entry is found to duplicate an existing tracking artifact, simply remove it. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Documentation structural check | `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` | Passes with no new findings |
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Needs Confirmation registry check | `uv run python tools/check_needs_confirmation_inventory.py` | Passes; `NC-036` correctly registered |
| `tests/rag/test_rag_pipeline_service.py` | Existing unit test (evidentiary basis for NC-036's Evidence field) | `uv run pytest tests/rag/test_rag_pipeline_service.py -k test_json_parse_error_calls_set_fallback_reason` | Passes |

## Completion criteria

- Exactly one tracking entry exists (`NC-036`), and ADR-010 was not amended.
- The entry cites ADR-010 Decision #9, `scripts/rag/pipeline_service.py::call_rag_service()`, and `test_json_parse_error_calls_set_fallback_reason` by name.
- The entry has a named owner (`@data-eng`, not `Unassigned`).
- No behavior change was made to the RAG fallback path.
- `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` passes clean.
- `uv run python tools/check_needs_confirmation_inventory.py` passes; `NC-036` correctly registered.

## Out of scope

- Amending `docs/adr/ADR-010-rag-fallback.md` — this Plan's own investigation found the "intentional vs. unintended" classification genuinely ambiguous, requiring owner/architect input.
- Registering a Part 1 Known Issue (`document-code-mismatch`) — not taken for the same reason.
- Changing `scripts/rag/pipeline_service.py::call_rag_service()` or its tests.
- Revisiting CI-004's closure.
- Reviewing other ADR-010 decisions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260915-200218_rag02_register-the-adr-010-decision-9-parse-error-discrepancy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-151126_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-151126
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
