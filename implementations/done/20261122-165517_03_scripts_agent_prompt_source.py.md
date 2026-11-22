## Goal

Create the typed prompt-source model and the single reader both the startup path and the reload path use, so prompt content has exactly one stored source (REQ-001, typed single-source model).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The module lives under `scripts/agent/` because only agent consumers use it; `scripts/shared/` stays a leaf module per the import-linter `shared-is-leaf` contract (Plan Design, `rules/coding.md` import layer contract).
- Path resolution goes through `shared.runtime_paths.resolve_registry_dir` (`scripts/shared/runtime_paths.py` lines 80-89), so a compiled binary reads the deployed `registry/`; the module must not resolve the path through `__file__`.
- The reader is a read boundary: a missing file or a missing `default` entry is an error, never a silent default (REQ-001, Plan UNK-03 default decision).
- `registry/manifests/prompt_source.toml` (row 02) is parsed with the standard library `tomllib`; no PyYAML is needed.

## Design decisions
- One frozen model plus one reader, shared by both consumers, so no caller can hold its own mutable copy of prompt content (AC-1). The reader returns a read-only mapping, matching the precedent shape of `scripts/shared/component_mandatoriness.py` (`load_component_mandatoriness`, lines 147-160).
- Error type raised at the read boundary, following the precedent's fail-fast style, so a missing source is reported where it is read rather than at the first prompt use.
- The module exposes no default prompt content: the single source is the only source.

## Alternatives considered
- Putting the reader under `scripts/shared/` like the mandatoriness precedent: rejected, `shared` must not be imported by nothing that only agent code consumes it, and no non-agent consumer exists.
- Keeping a code-level default prompt as a fallback: rejected, a silent default is the failure mode this plan removes.

## Implementation
### Target file
`scripts/agent/prompt_source.py` (new)
### Procedure
Add the frozen prompt-source model and the reader, and nothing else.
### Method
- Model: one frozen dataclass (or frozen mapping) holding prompt name to content; no mutable view escapes it (REQ-001).
- Reader: resolve the path through `resolve_registry_dir`, parse `registry/manifests/prompt_source.toml`, validate the top-level shape and each entry, return the read-only mapping.
- Lookup: name lookup for the caller's prompt name with `default` as the required entry; callers pass the name, the module does not select it.
- Errors: missing file, unparseable file, non-mapping top level, missing `default`, empty content — one error type at the read boundary.
### Details
- Module header follows the repository docstring convention (path line plus a one-paragraph purpose naming the single-source contract), checked by `tools/check_docstrings.py`.
- Consumers are row 11 (startup) and row 10 (reload); neither may keep a local copy of prompt content.
- New names in this module are the model, the error type, and the reader function; row 12 tests them by name, so both documents must use the same names.

## Compatibility considerations
- Nothing imports this module today, so the change is additive; the two consumers switch to it in rows 10 and 11, and no other call path reads prompt content.
- `tools/check_module_size.py` gates a new `scripts/` module at 24576 B; this module stays well under it.

## Security considerations
- The read-only contract is the boundary: prompt content is data from a repository file, not user input, and no write path exists.
- Fail-fast on a missing source keeps a deployed instance from starting with an unintended prompt.

## Rollback considerations
- Remove the module together with rows 02, 10 and 11; a partial rollback leaves the consumers without a prompt source.

## Validation plan
- `uv run pytest tests/agent/test_prompt_source.py` (row 12): frozen model, `default` lookup, missing file, missing entry, no mutable copy escapes.
- `uv run ruff check .`, `uv run mypy scripts/`, `uv run lint-imports` (the `shared-is-leaf` contract stays intact).
- `uv run python tools/check_docstrings.py` after adding the module.

## Completion criteria
- Both consumers obtain prompt content only through this reader, the returned model is immutable, and the missing-file and missing-entry cases raise at the read boundary (AC-1, AC-4).

## Out of Scope
- Prompt-name selection features and any command that changes the name (Plan Out-of-Scope, UNK-04).
- Registering `registry/manifests/prompt_source.toml` as a generator manifest type (UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-180330 | 20261122-180330 | names must match row 12 names: PromptSource (frozen model), PromptSourceError, load_prompt_source; ruff/mypy/check_docstrings/lint-imports pass on this module |
| 2 | Add or update tests per Validation plan | Completed | 20261122-180330 | 20261122-180330 | covered by row 12 no test change here; covered by row 12 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-180330 | 20261122-183359 | includes `lint-imports` per-module checks pass; row 12 tests and full suite at batch end end-of-batch full-suite run: 13333 passed, 2 failed — b04 concurrent-writes flaky (3 reruns pass, unrelated to this batch), and an unlisted positional _build_tool_config call site in test_tool_result_formatter.py:77 fixed (finding recorded on row 14); diff-cover 100% (>=90) |

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
- **Requirement ID**: `REQ-001` (typed read-only prompt model), `REQ-006` (startup reads through it), `REQ-007` (reload reads through it)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `scripts/agent/prompt_source.py`