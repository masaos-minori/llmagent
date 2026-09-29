## Goal
Update the leftover misleading log message in `call_rag_service()`'s `except
ValueError` branch to accurately describe returning an empty result, with no
mention of "falling back" (REQ-002).

## Scope
- **In-Scope**: The single `logger.warning(...)` call in the `except
  ValueError` branch (confirmed at lines 175-181).
- **Out-of-Scope**: The branch's return value (`return "", None, 0.0`) or
  control flow; any other branch in `call_rag_service()` (the sibling
  HTTP-client-error branches at lines 152-169 are correct as-is and use
  `_set_fallback_reason` deliberately, unlike this branch); removing the
  NC-036 entry from the governance inventory (covered by the sibling
  implementation procedure document for that file, seq 01 of this Plan);
  re-verifying ADR-010 Decision #9 compliance itself.

## Assumptions
- Commits `ba82419b` and `4ee51b8d` already fixed this branch's actual
  behavior (return an empty result, no `_set_fallback_reason` call) — only the
  log message text is stale, not the logic (Plan Background).
- test_json_parse_error_does_not_call_set_fallback_reason (this file's test
  counterpart, `tests/rag/test_rag_pipeline_service.py:240`) already asserts
  the current, correct behavior and requires no change — only the log string
  is being corrected, which that test does not assert on.

## Design decisions
- Change only the log message string; do not touch the `return "", None, 0.0`
  statement, the `except ValueError as e:` clause, or any other line — per
  `skills/python-design`, the smallest change that fixes the confirmed stale
  wording without risking the branch's already-correct control flow.

## Alternatives considered
- Remove the log statement entirely instead of correcting its wording —
  rejected: out of scope; the Issue's own instruction is to fix the message
  text, not remove the log line (a parse error is still worth logging).
- Reword to match the sibling HTTP-client-error branches' "falling back to
  in-process" phrasing family — rejected: that phrasing is accurate for those
  branches (they do call `_set_fallback_reason` and return `None`, triggering
  an actual fallback) but is exactly the inaccurate framing this branch must
  stop using, since it returns an empty result instead.

## Implementation
### Target file
`scripts/rag/pipeline_service.py`

### Procedure
1. Open `scripts/rag/pipeline_service.py` and locate the `except ValueError as
   e:` branch (confirmed at lines 175-181 by direct read during this
   document's generation).
2. Replace the `logger.warning(...)` call's message string only, leaving the
   `rag_url`/`e` arguments and the subsequent `return "", None, 0.0` statement
   unchanged.

### Method
Direct text replacement (single string literal in one existing log call) — no
new imports, no change to the branch's control flow or return value.

### Details
Current lines 175-181 (confirmed via direct read):
```
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            return "", None, 0.0
```

New lines 175-181 — only the message string on the line following
`logger.warning(` changes:
```
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), returning empty result: %s",
                rag_url,
                e,
            )
            return "", None, 0.0
```

Do not modify the sibling `except httpx.HTTPStatusError` or `except
httpx.TransportError` branches (lines 151-173), or any other line in this
function or file.

## Compatibility considerations
N/A: log-message-text-only change; `call_rag_service()`'s return value and
control flow are unchanged, so callers (`http_augment.py`, `pipeline.py`) are
unaffected.

## Security considerations
N/A: no credentials, data-handling, or security-relevant logic change.

## Rollback considerations
Single-line string revert via `git revert`/`git checkout` of this file if
needed; no data migration or schema state to unwind.

## Validation plan
- `uv run ruff format scripts/rag/pipeline_service.py` and
  `uv run ruff check scripts/rag/pipeline_service.py` — formatting/lint.
- `uv run mypy scripts/rag/pipeline_service.py` — type check (no type change
  expected; a string literal edit only).
- `PYTHONPATH=scripts uv run lint-imports` — architecture/import-boundary
  check (no import change expected).
- `uv run bandit scripts/rag/pipeline_service.py` — security scan (no new
  finding expected).
- `uv run pytest tests/rag/test_rag_pipeline_service.py -v` — targeted;
  confirm test_json_parse_error_does_not_call_set_fallback_reason and all
  other tests in the file still pass unchanged.
- `uv run pytest -q` — full suite, once, per `rules/toolchain.md` (REQ-002).

## Completion criteria
- The `except ValueError` branch's log message no longer mentions "falling
  back" and accurately describes returning an empty result.
- The branch's return value and control flow are unchanged.
- No other line in this file is changed.
- All validation steps above pass.

## Out of scope
- Removing the NC-036 entry from
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md` —
  handled by the sibling implementation procedure document for that file (seq
  01 of this Plan).
- Any other branch or line in `call_rag_service()` or elsewhere in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the log message string per Implementation > Procedure/Method/Details | Completed | 20260929-160500 | 20260929-160500 | Log message updated ('falling back to in-process' -> 'returning empty result'); diff scoped to 1 line |
| 2 | Run non-test validation, then targeted test and full suite once | Completed | 20260929-160500 | 20260929-160500 | ruff/mypy/lint-imports/bandit run — mypy clean, pre-existing unrelated lint-imports violation confirmed. Targeted: 16 passed (incl. test_json_parse_error_does_not_call_set_fallback_reason). Full suite (non-randomized): 8004 passed, 24 skipped, 0 failed. |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260927-211419_nc036_remove-stale-nc-036-adr-010-contradiction-entry.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-164318_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-154555
- **Related target files**: scripts/rag/pipeline_service.py