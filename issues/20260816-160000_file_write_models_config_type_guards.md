# Decide on config-value type-strictness consistency across `*_models.py` config loaders

## Priority
Low

## Summary
`scripts/mcp_servers/file/write_models.py`'s `FileWriteConfig.from_dict` coerces raw TOML values
via bare `int(...)`/`list(...)` calls with no `isinstance` pre-check (e.g. a TOML float like
`1048576.0` for `max_write_bytes` currently coerces successfully via `int()`). This is looser
than `scripts/mcp_servers/git/git_models.py`'s `GitConfig.from_dict`, which was refactored
(2026-08-14) to use an explicit `_get_typed(d, key, expected_type, type_label)` helper that
raises `ValueError` on a type mismatch.

## Reason for Change
Found during a `prompts/04_refactor.md` cycle on `write_models.py` (2026-08-15). Not implemented
there because adding an `isinstance` guard to `write_models.py` would change what values are
accepted and what exception/message is raised for malformed config — a real behavior change on
the config-loading boundary, not a pure refactor. This is really a cross-cutting consistency
question: should `write_models.py`/`read_models.py`/`delete_models.py`/`web_search_models.py`'s
config loaders match `git_models.py`'s stricter validation, or should `git_models.py`'s validation
be relaxed to match the others' looser coercion? That decision should be made once, not per file.

## Implementation Intent
Decide the target strictness level for config-value coercion across all `*_models.py` config
loaders in `scripts/mcp_servers/`. Once decided, apply consistently: either backport
`git_models.py`'s `_get_typed`-style validation to the looser loaders, or relax `git_models.py`
to match them. Either direction requires characterization tests for the newly-accepted/rejected
value shapes (e.g. float-for-int fields) before implementation.

## Target Files or Areas
- `scripts/mcp_servers/git/git_models.py` (`GitConfig.from_dict`, current strict behavior)
- `scripts/mcp_servers/file/write_models.py` (`FileWriteConfig.from_dict`)
- `scripts/mcp_servers/file/read_models.py`, `delete_models.py` (confirm current strictness
  level — not yet audited for this specific concern)
- `scripts/mcp_servers/web_search/web_search_models.py` (confirm current strictness level)

## Required Changes
- Audit every `*_models.py` config loader's current type-coercion strictness (via `rg` for
  `int(`/`float(`/`list(` calls inside `from_dict` methods).
- Decide and document the target strictness policy for the codebase.
- Apply the decision consistently across all affected loaders, one file at a time, with
  characterization tests for both accepted and newly-rejected value shapes per file.

## Acceptance Criteria
- All `*_models.py` config loaders apply the same, documented strictness policy.
- Each affected file has characterization tests covering both the valid-value and
  malformed-value paths.
- No existing valid TOML config file in `config/` fails to load after the change (verify by
  loading each real config file, not just synthetic test values).

## Testing Expectations
Full `tests/mcp_servers/` regression suite; new characterization tests per affected loader;
manual verification that every existing `config/*.toml` file still loads successfully.

## Documentation Impact
Document the decided strictness policy in `rules/coding.md` or `rules/env.md` (whichever governs
config-loading conventions) so future config loaders follow it consistently.

## Out of Scope
- Do not change any config loader's accepted *field set* (only value-type strictness).
- Do not implement per-file ad hoc without first deciding and documenting the repo-wide policy.

## AI Implementation Instruction
This is a policy decision affecting multiple files — do not implement a fix for
`write_models.py` alone without first surfacing the cross-cutting question (match `git_models.py`
or relax it) for explicit sign-off, per `rules/coding.md`'s explicit sign-off gates.
