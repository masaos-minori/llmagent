# Match _invoke_callback's exception scope to its never-re-raise contract

## Priority
Low

## Summary
`DocumentManager._invoke_callback` documents "Invoke the callback, logging any exception
without re-raising" but catches only `(TypeError, ValueError)`. An `on_ingest_complete`
callback that raises anything else (e.g. `sqlite3.Error` from a DB-reporting callback)
propagates through `check_consistency` out of `ingest_all`, turning a fully successful
ingestion into a crashed run.

### Verification (issue-to-plan cycle 20261106-104826)
- Confirmed at HEAD `bdb9bed66`: `except (TypeError, ValueError)` at `document_manager.py:159`
  vs docstring "logging any exception without re-raising" at `:155`; `_invoke_callback` is
  called at `:140`, outside `check_consistency`'s own try/except (`:134-138`), and
  `check_consistency` is called unguarded inside `ingest_all` (`ingester.py:171-175`) — a
  propagating callback error escapes `ingest_all`.
- New finding: the escape point sits **before** `bump_index_generation` (`ingester.py:181-182`)
  — a run that legitimately wrote content also loses its generation bump when the callback
  raises. The fix restores that side effect as a consequence.
- New finding (latency): the only production call site `ingester.py:409` (`ingest_all(args.force)`)
  passes no callback, and no other production caller passes `on_ingest_complete` — the defect
  is latent today and bites programmatic callers (e.g. future MCP/service integrations).
- Lint feasibility: ruff selects `BLE001` (`pyproject.toml:106`); empirically
  `except Exception:` (bound or unbound) passes BLE001 under this repo's config
  (`/tmp/opencode/raging012/probe.py` all-checks-passed; precedent `orchestrator.py:86`).
  No suppression needed.
- Test status confirmed: `tests/rag/ingestion/test_rag_ingester_callback.py` has exactly one
  test (`test_ingest_all_calls_on_ingest_complete`, `:81`), happy path only; its harness
  (patched `_process_url_groups` → `[]`, mocked `check_rag_consistency` → MagicMock report) is
  reusable for the failure-class regression test.

## Problem
- `scripts/rag/ingestion/document_manager.py` `_invoke_callback`:
  `except (TypeError, ValueError)` — narrower than its own docstring.
- `check_consistency` calls `_invoke_callback` after its own try/except around
  `check_rag_consistency`, so a propagating callback error is not caught there either;
  it escapes `check_consistency` and `RagIngester.ingest_all`.
- The failure appears after all ingestion work succeeded, so the run's exit status and
  traceback misreport a successful ingestion.
- `tests/rag/ingestion/test_rag_ingester_callback.py` covers the happy path (callback
  called once) but not failure classes.

## Background
The callback exists so callers receive a post-ingestion completion notification without
a caller-side try/except; the same never-raises principle governs `check_consistency`'s
own DB-error handling and `bump_index_generation` (REQ-007). The callback's catch tuple
was written narrower than the surrounding pattern.

## Reason for Change
Consistency with the established "ingestion completion must not be broken by reporting
failures" contract, and with the method's own docstring.

## Implementation Intent
Broaden the caught set in `_invoke_callback` to `Exception` (matching the documented
"any exception" behavior), logging with `logger.exception` as today.

## Target Files or Areas
- `scripts/rag/ingestion/document_manager.py`
- `tests/rag/ingestion/test_rag_ingester_callback.py`

## Required Changes
- Change `except (TypeError, ValueError)` to `except Exception` in `_invoke_callback`.
- Add a regression test: a callback raising `sqlite3.Error` (or a generic error) is
  logged and `ingest_all` returns its consistency report normally.

## Constraints
- The broadened catch wraps only the callback invocation, never the consistency check or
  ingestion path.
- Keep the `logger.exception` call and its message.

## Acceptance Criteria
- A raising `on_ingest_complete` callback does not propagate out of `ingest_all`
  (covered by test).
- Existing callback tests pass.

## Testing Expectations
- New failure-class regression test in `test_rag_ingester_callback.py`.
- `uv run pytest tests/rag/ingestion`.

## Documentation Impact
N/A: behavior already documented as "logging any exception without re-raising".

## Out of Scope
- Redesigning the consistency report contents.

## Dependencies
- N/A: none

## Unresolved Questions
- None.

## AI Implementation Instruction
Single handler-scope change plus one test; do not alter ingestion flow.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/document_manager.py`, `tests/rag/ingestion/test_rag_ingester_callback.py`
