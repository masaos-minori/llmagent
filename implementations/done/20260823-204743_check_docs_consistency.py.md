# Implementation Procedure: tools/check_docs_consistency.py

## Goal

Add `main_mcp()` and `main_agent()` wrapper functions that invoke the consolidated
`main()` with the appropriate `--domain` argument, correctly passing through real CLI
arguments (`--skip`, `--docs-dir`) when invoked as a console-script entry point.

## Scope

**In-Scope**
- Add `main_mcp(argv: list[str] | None = None) -> int` and
  `main_agent(argv: list[str] | None = None) -> int` functions.

**Out-of-Scope**
- Any change to `main()` itself, `DOMAIN_PREFIXES`, or any check-logic function in this
  module — the wrappers only add a `--domain` default on top of the existing, unchanged
  `main()`.
- `main_deployment`/`main_overview`/`main_rag` wrapper functions — not requested by the
  source requirement; this plan restores only `check-mcp-docs`/`check-agent-docs`.

## Assumptions

- `main(argv: list[str] | None = None) -> int` is the existing, unchanged signature —
  confirmed by direct read: it builds an `argparse.ArgumentParser` with a required
  `--domain` argument (`choices=list(DOMAIN_PREFIXES.keys())`), an optional
  `--docs-dir`, and an optional `--skip` (`nargs="+"`), then calls
  `parser.parse_args(argv)`.
- `sys` is already imported at module level in this file — confirmed by direct read
  (`import sys` near the top of the file) — so the corrected wrapper implementation
  needs no new import.
- **Bug in the source requirement's own proposed wrapper code, NOT yet corrected**:
  the requirement suggested `return main((argv or []) + ["--domain", "mcp"])`. When
  installed as a `[project.scripts]` console-script entry point, setuptools' generated
  wrapper script calls the target function with no arguments (`main_mcp()`), so `argv`
  is always `None` in that call path — `(None or []) + [...]` becomes `[...]`, silently
  discarding whatever the user actually typed after `check-mcp-docs` on the command
  line (e.g. `check-mcp-docs --skip portdrift` would run with `--skip` dropped). The
  actual CLI arguments live in `sys.argv[1:]`, which the requirement's proposed code
  never reads. Verified during this review: the current file still contains the buggy
  `(argv or [])` pattern at lines 759 and 764; this procedure implements the correction.

## Design decisions

- Corrected wrapper implementation:
  ```python
  def main_mcp(argv: list[str] | None = None) -> int:
      return main((argv if argv is not None else sys.argv[1:]) + ["--domain", "mcp"])

  def main_agent(argv: list[str] | None = None) -> int:
      return main((argv if argv is not None else sys.argv[1:]) + ["--domain", "agent"])
  ```
  This preserves the requirement's intent (a thin default-domain wrapper) while
  actually forwarding real CLI arguments when invoked as a console-script, and still
  supports explicit `argv` passing for direct/test invocation
  (`main_mcp(["--skip", "portdrift"])`).
- Append `["--domain", "<domain>"]` after the forwarded args (not before), so that if a
  future caller mistakenly also passes `--domain` explicitly, `argparse` reports the
  duplicate rather than silently taking the wrong one first — no different behavior
  today (single `--domain` occurrence expected), but a safer append order than
  prepending.

## Alternatives considered

- Have the wrappers call `sys.exit(main(...))` directly rather than `return main(...)`
  — rejected: `main()` already returns an `int` exit code, and the console-script entry
  point mechanism (`[project.scripts]`) handles converting a non-`None` int return into
  the process exit code automatically; adding `sys.exit()` here would be redundant with
  what setuptools' generated wrapper already does.

## Implementation

### Target file
`tools/check_docs_consistency.py`

### Procedure
1. Add `main_mcp()` and `main_agent()` immediately after the existing `main()`
   function, using the corrected implementation in Design decisions above.
2. Confirm `sys` is imported (it already is; no action needed).
3. Manually invoke both new functions with a representative `--skip` argument
   (e.g. `python -c "from tools.check_docs_consistency import main_mcp; import sys;
   sys.argv = ['check-mcp-docs', '--skip', 'portdrift']; main_mcp()"`) to confirm the
   `--skip` flag reaches `main()`'s `--domain mcp` invocation.

### Method
Two small function additions; no existing code modified.

### Details
- No test file currently exists for `tools/check_docs_consistency.py`'s `main()` per a
  scan of `tests/tools/` — if one exists elsewhere, it is not part of this plan's
  Related target files and this procedure does not modify it. New wrapper functions
  should be smoke-tested via the CLI invocation in Procedure step 3, per this plan's
  Validation plan.

## Compatibility considerations

- No behavior change to `main()` or existing callers — this is a pure addition of two
  new functions with no interaction with existing code paths.

## Security considerations

N/A: no security-relevant logic; these are thin CLI-argument wrappers.

## Rollback considerations

- Trivially revertable: removing the two new functions has no effect on `main()` or any
  other caller, provided the companion `pyproject.toml` entries (which reference these
  functions) are reverted in the same change — otherwise the console-script entries
  would point at now-missing functions.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/check_docs_consistency.py (main_mcp) | Smoke test | `uv run check-mcp-docs` (after pyproject.toml companion procedure lands) | Executes without import error; runs MCP domain checks |
| tools/check_docs_consistency.py (main_agent) | Smoke test | `uv run check-agent-docs` (after pyproject.toml companion procedure lands) | Executes without import error; runs agent domain checks |
| tools/check_docs_consistency.py (main_mcp with --skip) | Argument-forwarding regression | Invoke `main_mcp(["--skip", "portdrift"])` directly, and separately via `sys.argv` simulation (Procedure step 3) | `--skip portdrift` reaches `main()`'s parsed args in both invocation styles |
| tools/check_docs_consistency.py | Lint/type | `uv run ruff check tools/check_docs_consistency.py && uv run mypy tools/check_docs_consistency.py` | Clean |

## Out of scope

- `pyproject.toml` — covered by its own implementation procedure document.
- `rules/toolchain.md` — covered by its own implementation procedure document.

## Execution Status

##### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

##### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-115047_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-204743
- Related target files: tools/check_docs_consistency.py
