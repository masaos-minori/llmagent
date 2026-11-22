## Goal

Add the reader and model contract tests for the typed prompt source, including the error-boundary cases (REQ-001, reader contract tests).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Companion judgement: condition 2 fails — this file is named in the `Related Tests` cell of two rows (02 and 03), not exactly one — so it keeps its own document.
- The names used here must match the symbols row 03 creates; both documents are written against the same API, so the test imports the model, the error type, and the reader from `agent.prompt_source`.
- Test names follow the repository convention `tests/<package>/test_<affected_module>.py`, so this file mirrors `scripts/agent/prompt_source.py`.
- The tests read a fixture file, not `registry/manifests/prompt_source.toml` directly, so the path contract is exercised through the resolved registry directory rather than a repository-relative path.

## Design decisions
- Unit level only, no marker: these tests do not start subprocesses, so they run in the default and full-suite selections.
- The fixture values are copied from the current prompt content so the contract asserts that no prompt text is lost when the values move (AC-1).

## Alternatives considered
- Marking this file `integration` because it reads a file: rejected, the `integration` marker is defined for tests that start real subprocesses.

## Implementation
### Target file
`tests/agent/test_prompt_source.py` (new)
### Procedure
Create the test module for the typed model and the reader.
### Method
- Reader returns the frozen typed model; the returned mapping is read-only and no mutable copy escapes it.
- Name lookup resolves `default`; a lookup for `strict` and `creative` returns the carried-over content.
- Missing source file raises the reader's error at the read boundary.
- Missing `default` entry raises at the read boundary, with no silent default.
- Path resolution is exercised through `shared.runtime_paths.resolve_registry_dir`, so an explicit `LLMAGENT_REGISTRY_DIR` is honoured.
### Details
- Keep each case independent of the real `registry/manifests/prompt_source.toml`; use a temporary fixture directory so the inventory of the committed file is not asserted here (that belongs to row 13).

## Compatibility considerations
- This file is the coverage source for the changed lines of row 03, since `diff-cover` runs with `integration` deselected.

## Security considerations
- N/A: no trust boundary beyond the read contract the tests assert.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_prompt_source.py`
- `uv run ruff check tests/agent/test_prompt_source.py`, `uv run mypy scripts/`
- Full suite with `-n logical` and the `diff-cover` ≥ 90% gate against the recorded baseline (95.49% at 2026-11-22).

## Completion criteria
- The five contract cases pass, and each failure mode named by AC-1 and AC-5 has a case that fails without the implementation.

## Out of Scope
- Asserting the contents of the committed prompt source file (row 13).
- Startup and reload behaviour (rows 18, 15).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-180859 | 20261122-180859 | depends on row 03 landing first 6 passed; names match row 03 (PromptSource/PromptSourceError/load_prompt_source); ruff clean after import sort |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-180859 | 20261122-183359 | targeted run passes; full suite + diff-cover at batch end end-of-batch full-suite run: 13333 passed, 2 failed — b04 concurrent-writes flaky (3 reruns pass, unrelated to this batch), and an unlisted positional _build_tool_config call site in test_tool_result_formatter.py:77 fixed (finding recorded on row 14); diff-cover 100% (>=90) |

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
- **Requirement ID**: `REQ-001` (typed read-only prompt model and its reader contract)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `tests/agent/test_prompt_source.py`