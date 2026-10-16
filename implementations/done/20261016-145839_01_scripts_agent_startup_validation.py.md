## Goal

Implement `REQ-001` (classify non-timeout RAG consistency exceptions by root cause), `REQ-002` (carry the category in the `SKIPPED` outcome message), and `REQ-003` (keep the check soft / never `FATAL`) by rewriting only the broad `except Exception` branch of the RAG consistency block in `StartupValidationPipeline.check_services()`.

## Scope

Modify `scripts/agent/startup_validation.py` only. Add an inline exception-type classification inside the RAG `except Exception` branch and carry the category + exception type name in the `add_skipped("rag_consistency", ...)` message. Leave the `except TimeoutError` branch byte-for-byte unchanged. No other file is modified.

## Assumptions

- Category labels and the exception type name are not sensitive; carrying them in the `SKIPPED` message adds no new secret exposure beyond the pre-existing `{exc}` interpolation already present in this branch.
- `TimeoutError` is still handled by the outer `wait_for` branch, so the inner classification only needs to resolve `NETWORK_TRANSIENT`, `DATABASE_OR_IO`, `PROGRAMMING_ERROR`, and `UNKNOWN`.
- Reusing the memory-failure vocabulary keeps the RAG check consistent with `PromptSetup._classify_memory_failure()`.

## Design decisions

- Re-declare the exception-type list inline in `startup_validation.py` rather than importing `startup_prompt_setup.py`'s private `_PROGRAMMING_ERROR_TYPES`. Importing would couple `startup_validation.py` to another module's internals and invite an import-layer concern outside this scope; the inline list mirrors `_classify_memory_failure()` exactly.
- Convey the category through the `message` field of the `SKIPPED` `StartupCheckOutcome`, which carries only `source`, `status`, `message`, `remediation`. No data-model/interface change to `health_models.py`.

## Alternatives considered

`N/A: single-function change confined to one soft-check failure branch; no public contract, persistence, or security impact.`

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
1. Add `import sqlite3` to the stdlib import block (after `import asyncio`, before `from typing import TYPE_CHECKING`).
2. Inside the RAG consistency `except Exception as exc:` branch (currently lines 166-170), classify `exc` by root cause before recording the outcome.
3. Rewrite the `add_skipped("rag_consistency", ...)` call so its message carries the category and the exception type name.
4. Leave the `except TimeoutError` branch (lines 161-165) unchanged; confirm no branch calls `add_fatal`.

### Method

Mirror `PromptSetup._classify_memory_failure()` in `scripts/agent/startup_prompt_setup.py` (`startup_prompt_setup.py:36-48`, with `_PROGRAMMING_ERROR_TYPES` at `startup_prompt_setup.py:20-26`):

- `ConnectionError` (and defensively `TimeoutError`) -> `NETWORK_TRANSIENT`.
- `sqlite3.Error`, `OSError` -> `DATABASE_OR_IO`.
- `AttributeError`, `NameError`, `TypeError`, `LookupError`, `AssertionError` -> `PROGRAMMING_ERROR`.
- otherwise -> `UNKNOWN`.

### Details

Replace lines 166-170:

```python
        except Exception as exc:  # noqa: BLE001 — non-critical maintenance check must not abort startup
            logger.warning("RAG consistency check failed: %s", exc)
            pipeline.add_skipped(
                "rag_consistency", f"RAG consistency check skipped: {exc}"
            )
```

with:

```python
        except Exception as exc:  # noqa: BLE001 — non-critical maintenance check must not abort startup
            # Classify by root cause, mirroring PromptSetup._classify_memory_failure()
            # in startup_prompt_setup.py. Re-declared inline here to avoid coupling
            # startup_validation.py to another module's private tuple.
            if isinstance(exc, (ConnectionError, TimeoutError)):
                category = "NETWORK_TRANSIENT"
            elif isinstance(exc, (sqlite3.Error, OSError)):
                category = "DATABASE_OR_IO"
            elif isinstance(
                exc,
                (AttributeError, NameError, TypeError, LookupError, AssertionError),
            ):
                category = "PROGRAMMING_ERROR"
            else:
                category = "UNKNOWN"
            logger.warning("RAG consistency check failed: %s", exc)
            pipeline.add_skipped(
                "rag_consistency",
                f"RAG consistency check skipped: {category} ({type(exc).__name__}): {exc}",
            )
```

Notes:
- `ConnectionError` is a subclass of `OSError`; the `NETWORK_TRANSIENT` check precedes the `DATABASE_OR_IO` check so a connection error is never misclassified.
- `sqlite3` is stdlib and already imported at module top level in `startup_prompt_setup.py`, so the new `import sqlite3` introduces no import-layer risk.
- `ruff format` normalizes the exploded tuple and the multi-line `add_skipped` call; the retained `# noqa: BLE001` stays on the `except Exception` line.

## Compatibility considerations

`N/A: no caller, signature, or interface change; `check_services()` still returns `StartupValidationResult` unchanged.`

## Security considerations

`N/A: no new secret exposure — the category label and exception type name are added; the pre-existing `{exc}` interpolation is retained unchanged for parity with the memory-failure path.`

## Rollback considerations

`N/A: revert the single commit that applies this change.`

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_validation.py` | Static: format, lint, architecture, security | `uv run ruff format scripts/` then `uv run ruff check scripts/`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit scripts/agent/startup_validation.py -c pyproject.toml` | All clean; no new findings; `# noqa: BLE001` retained |
| Complexity | Radon on `check_services()` | `uv run radon cc scripts/agent/startup_validation.py -s` | Grade C or better; if worse, extract the classifier into a module-level helper (see Risks) |
| `tests/agent/test_startup_validation.py` | Unit: new programming-error case plus existing cases | `uv run pytest tests/agent/test_startup_validation.py -v` | New and existing tests pass |

## Completion criteria

- The RAG `except Exception` branch records a `SKIPPED` outcome whose message contains both the category label (e.g. `PROGRAMMING_ERROR`) and the exception type name (e.g. `KeyError`).
- The `except TimeoutError` branch is byte-for-byte unchanged and still produces a `SKIPPED` outcome with `"timeout"` in its message.
- No branch calls `add_fatal`; `check_services()` still returns without raising for any RAG exception.
- `ruff format`, `ruff check`, `mypy`, `lint-imports`, and `bandit` are clean on the changed file; the regression test for the programming-error path passes.

## Out of scope

Any change to `scripts/agent/shared/health_models.py` (no new category field), `scripts/agent/startup_prompt_setup.py` (no shared-tuple refactor), the reporter (`scripts/agent/startup_reporter.py`), or any other pipeline check. Surfacing the per-category indicator in the human-readable readiness summary is a deferred follow-up (see the Plan's Unknowns).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261016-171028 | 20261016-171028 | changed: scripts/agent/startup_validation.py (import sqlite3; classification of the RAG failure carried in the SKIPPED message). Deviation from the procedure: the classification is a module-level helper _classify_rag_failure (new), not inline, so check_services stays at its baseline complexity D(26) instead of rising to D(29); startup_prompt_setup.py's private tuple is still not imported. docs: N/A; ruff/mypy/lint-imports/bandit(0)/vulture clean; full suite 8460 passed; diff-cover 100% |
| 2 | Add or update tests per Validation plan | Completed | 20261016-171028 | 20261016-171028 | changed: scripts/agent/startup_validation.py (import sqlite3; classification of the RAG failure carried in the SKIPPED message). Deviation from the procedure: the classification is a module-level helper _classify_rag_failure (new), not inline, so check_services stays at its baseline complexity D(26) instead of rising to D(29); startup_prompt_setup.py's private tuple is still not imported. docs: N/A; ruff/mypy/lint-imports/bandit(0)/vulture clean; full suite 8460 passed; diff-cover 100% |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-171028 | 20261016-171028 | changed: scripts/agent/startup_validation.py (import sqlite3; classification of the RAG failure carried in the SKIPPED message). Deviation from the procedure: the classification is a module-level helper _classify_rag_failure (new), not inline, so check_services stays at its baseline complexity D(26) instead of rising to D(29); startup_prompt_setup.py's private tuple is still not imported. docs: N/A; ruff/mypy/lint-imports/bandit(0)/vulture clean; full suite 8460 passed; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261016-171028 | 20261016-171028 | changed: scripts/agent/startup_validation.py (import sqlite3; classification of the RAG failure carried in the SKIPPED message). Deviation from the procedure: the classification is a module-level helper _classify_rag_failure (new), not inline, so check_services stays at its baseline complexity D(26) instead of rising to D(29); startup_prompt_setup.py's private tuple is still not imported. docs: N/A; ruff/mypy/lint-imports/bandit(0)/vulture clean; full suite 8460 passed; diff-cover 100% |

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
- **Requirement ID**: `REQ-001` (classify non-timeout RAG exceptions by root cause), `REQ-002` (carry the category in the `SKIPPED` message), `REQ-003` (never promote to `FATAL`)
- **Source issue**: issues/20261016-133921_startup001_classify-rag-consistency-startup-exceptions-instead-of-skipping-all.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-135325_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145839
- **Related target files**: scripts/agent/startup_validation.py