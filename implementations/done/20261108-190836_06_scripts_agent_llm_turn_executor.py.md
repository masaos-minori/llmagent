## Goal
Reword the section header comment in the LLM turn executor so it describes what the helper methods are, removing the "Backward-compatible" wording the strict COMPAT scan flags — the methods themselves stay (`REQ-002`).

## Scope
**Release unit**: wfaudit012-full

- Covers Plan `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md` row 6 only: `scripts/agent/llm_turn_executor.py`.

## Assumptions
- Procedure 01 (`implementations/20261108-190836_01_tools_check_compat_shims.py.md`) lands in the same change unit; the header at L54 only appears in the strict run.
- The helpers are live internal call sites, not compatibility aliases: `call_on_llm_wait_start` (L61-66) is awaited at L98 and `call_on_llm_wait_end` (L56-59) is called at L110, both from inside this class. The 2026-11-08 grep over `scripts/`, `tests/`, `docs/`, `tools/` finds no other reference to either name.
- No documentation references these method names, so rewording the comment creates no docs mismatch.

## Design decisions
- Reword only the comment: the flagged text is an inaccurate label, and the code it labels is current design (callback invocation wrappers around the optional `on_llm_wait_start` / `on_llm_wait_end` / `on_error` hooks). Deleting the helpers would change turn behavior, which this plan does not authorize.
- New header wording: `# ── Callback invocation helpers ─...─` — the same `# ── <label> ─...─` separator style used at L54, padded to the same width so the comment block stays visually aligned. It contains no COMPAT pattern phrase.

## Alternatives considered
- Delete the helper methods and inline the callback calls: rejected — behavior change beyond the plan's scope, and `call_on_error` (L68-71) shares the same section.
- Delete only the section header comment: rejected — the separators in this file mark structural sections; removing the label leaves the methods unsectioned, and the plan calls for accurate prose.
- Add a `fixture`-category manifest entry for this file: rejected — production source, not negative-test data.

## Implementation
### Target file
`scripts/agent/llm_turn_executor.py`

### Procedure
Replace the single comment line at L54.

### Method
Change `    # ── Backward-compatible helper methods ────────────────────────────────────` (L54) to `    # ── Callback invocation helpers ───────────────────────────────────────────`, keeping the leading four-space indent, the `# ── ` prefix, and the same total line width. L53 and L55-59 stay as they are; the method bodies (L56-59, L61-66, L68-71) and the call sites (L98, L110) are untouched.

### Details
- The file's other comments and the class docstring carry no COMPAT pattern phrase, so L54 is the only edit needed to clear this file.
- No signature, docstring text, or import changes.

## Compatibility considerations
- No public or internal behavior changes: the class API, callback ordering, and async-awaitable handling in `call_on_llm_wait_start` stay identical.
- After this edit the file produces no COMPAT finding in the strict run.

## Security considerations
- No security-relevant code touched; the wait-state callback path (which drives the UI "Thinking" indicator and error reporting) is unchanged.

## Rollback considerations
- Revert the commit restores the original header. Rolling this back while procedure 01 stays landed re-opens the `llm_turn_executor.py:54` finding, so a rollback here must be followed by the census gate re-run.

## Validation plan
- Grep gate: `grep -rn "Backward-compatible" scripts/agent/llm_turn_executor.py` returns nothing; `grep -rn "call_on_llm_wait_" scripts/ tests/` still shows the definitions (L56, L61) and the two call sites (L98, L110).
- Targeted tests: `uv run pytest tests/agent/test_llm_turn_executor.py tests/agent/test_llm_turn_runner.py -q` (async-callback ordering and guard-deferral wiring), then `uv run pytest tests/agent/ -q`.
- Checker gate: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` reports no finding for this file; the full run exits 0 only after procedures 03-09 and `wfaudit008` have all landed.
- `uv run ruff check scripts/agent/llm_turn_executor.py` and `uv run ty check scripts/agent/llm_turn_executor.py` per `rules/toolchain.md`.

## Completion criteria
- L54 states the section's real purpose, the helper methods and their call sites are unchanged, and the strict checker reports nothing for this file.

## Out of Scope
- The helper methods themselves and their call sites (L98, L110).
- Any change to callback behavior or the `on_llm_wait_*` hook contract.
- The checker semantics flip and the other census files (procedures 01-05, 07-09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-091755 | 20261109-091755 | one comment line (L54) STEP 1: L54 header reworded to 'Callback invocation helpers'; ruff/mypy clean |
| 2 | Add or update tests per Validation plan | Completed | 20261109-091755 | 20261109-091755 | no new test: behavior unchanged STEP 2: no new test; behavior unchanged; 50 targeted tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-101121 | 20261109-101121 | repo-clean gate depends on procedures 03-09 and `wfaudit008` STEP 3: per-member validators + targeted tests pass; diff-cover 100%; census 0 findings. End-of-unit full suite has 28 pre-existing eventbus failures (verified on clean HEAD, unrelated to unit); user approved proceeding. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-091755 | 20261109-091755 | no doc references these method names STEP 4: N/A - no docs/00_index.md task-scope mapping for scripts/agent/llm_turn_executor.py |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-190836
- **Related target files**: `scripts/agent/llm_turn_executor.py`; tests `tests/agent/test_llm_turn_executor.py`, `tests/agent/test_llm_turn_runner.py`