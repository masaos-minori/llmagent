# Evaluate hoisting `shell_server.py`'s local `shutil` import in `health()` to module level

## Priority
Low

## Summary
`scripts/mcp_servers/shell/shell_server.py`'s `health()` endpoint does a local
`import shutil as _shutil` wrapped in `try/except (ImportError, OSError)`, letting the endpoint
degrade gracefully (return a degraded health status) if the import were ever to fail. Sibling
file `scripts/mcp_servers/git/git_server.py` imports `shutil` at module (top) level instead.

## Reason for Change
Found during a `prompts/04_refactor.md` cycle on `shell_server.py` (2026-08-16). Not implemented
there because hoisting the import would change the failure mode: currently an (unrealistic)
`ImportError` on `shutil` would produce a degraded health response; after hoisting, the same
failure would instead crash the whole app at startup. This is a behavior change in an edge case,
however unlikely `shutil` failing to import actually is in practice.

## Implementation Intent
Confirm whether the graceful-degradation behavior for a `shutil` import failure is actually
meaningful (i.e., has this ever been observed, or is it purely defensive boilerplate copied from
elsewhere?). If it's purely defensive and inconsistent with the sibling `git_server.py`'s
top-level-import convention, hoist it for consistency and document the (accepted) change in
startup-failure behavior. If the graceful-degradation behavior is intentional, leave it and close
this issue as "no action, confirmed intentional."

## Target Files or Areas
- `scripts/mcp_servers/shell/shell_server.py` (`health()`)
- `scripts/mcp_servers/git/git_server.py` (sibling convention for comparison)

## Required Changes
- Determine whether any other `*_server.py` health-check import pattern is inconsistent in the
  same way (local vs. top-level `shutil`/similar stdlib import), to decide if this should be a
  repo-wide convention fix or a one-off.
- If hoisting: move `import shutil` to module level, remove the `try/except`, and add a
  characterization test for `health()` when `shutil.which` returns `None` (the realistic
  degradation case, distinct from the unrealistic `ImportError` case).

## Acceptance Criteria
- Either: the import is hoisted, the `try/except (ImportError, OSError)` around the import
  itself is removed, and a characterization test for the realistic `shutil.which() is None` case
  is added and passes; or
- The current behavior is confirmed intentional and documented, with no code change.

## Testing Expectations
`tests/mcp_servers/shell/test_shell_server_endpoints.py` (new 2026-08-16 characterization
tests) plus a new test for `shutil.which() is None` if the import is hoisted.

## Documentation Impact
None expected.

## Out of Scope
- Do not change `health()`'s actual degraded-status response shape or logic — only the import
  location and the `ImportError`-handling branch.

## AI Implementation Instruction
Check whether this same local-vs-top-level-import inconsistency exists in other `*_server.py`
health checks before deciding whether to fix it here alone or as a repo-wide convention pass.
