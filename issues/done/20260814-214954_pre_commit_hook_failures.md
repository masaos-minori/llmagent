# Pre-commit hooks fail: check-suppression-justification and git-exc-import-guard

## Priority
Medium

## Summary

Two pre-commit hooks fail when committing changes, preventing clean commits:

1. `check-suppression-justification` reports unjustified `# type: ignore` suppressions in existing test files
2. `git-exc-import-guard` detects files using `git.exc.` without also importing `git.exc`

Both issues are pre-existing and unrelated to any specific feature change.

## Reason for Change

Pre-commit hooks must pass before every commit per `rules/coding.md` §Constraint checks. These failures block all future commits until resolved.

## Implementation Intent

Address each hook failure separately:
- For `check-suppression-justification`: add em-dash justified comments to existing `# type: ignore` suppressions or remove unnecessary ones
- For `git-exc-import-guard`: add `import git.exc` alongside existing `import git` statements in affected files

Do not modify pre-commit configuration to bypass these checks.

## Target Files or Areas

### check-suppression-justification failures:
- `tests/shared/test_route_resolver.py:267`
- `tests/shared/test_tool_spec.py:49`
- `tests/shared/test_tool_transport_invoker_merge.py:46,47,63,72`

### git-exc-import-guard failures:
- Files under `scripts/` that reference `git.exc.` without `import git.exc`

## Required Changes

- [ ] Add em-dash justification comments to `# type: ignore` suppressions in the 6 locations above, or remove suppressions where no longer needed
- [ ] Identify all files using `git.exc.` without `import git.exc` and add the required import statement

## Acceptance Criteria

- [ ] `uv run pre-commit run --all-files` passes without errors
- [ ] No unjustified `# type: ignore` suppressions remain in the repository
- [ ] All files referencing `git.exc.` also have `import git.exc`

## Testing Expectations

- Run `uv run pre-commit run --all-files` to verify all hooks pass
- Verify `# noqa`, `# type: ignore`, and `# nosec` suppression justifications with:
  ```bash
  rg '# noqa' scripts/ | grep -v '# noqa:.*—'
  rg '# type: ignore' scripts/ | grep -v '\[.*—'
  rg '# nosec' scripts/ | grep -v ' — '
  ```
- Verify `git.exc` import guard:
  ```bash
  rg -l "git\.exc\." scripts/ | while read f; do ! grep -q "import git\.exc" "$f" && echo "$f"; done
  ```

## Documentation Impact

Update `rules/coding.md` §Constraint checks if the `git.exc` import guard pattern needs documentation as a project-wide convention.

## Out of Scope

- Do not modify pre-commit configuration to skip these hooks
- Do not add broad suppressions to pyproject.toml
- Do not change production code behavior unrelated to these fixes

## AI Implementation Instruction

Concise constraints for an AI coding agent implementing this issue:
- Fix only the pre-commit hook failures listed above
- Add justification comments using em-dash separator (e.g., `# type: ignore[misc] — reason`)
- Add `import git.exc` where `git.exc.` is referenced without the explicit import
- Do not rewrite unrelated sections of files
- Verify with `uv run pre-commit run --all-files` after changes
