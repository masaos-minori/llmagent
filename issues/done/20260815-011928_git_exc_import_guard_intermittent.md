# pre-commit hook git-exc-import-guard fails intermittently despite passing locally

## Priority
Medium

## Summary
The `git-exc-import-guard` pre-commit hook fails via pre-commit but passes when run manually
from the same repository root. Both files that reference `git.exc.*` currently include
`import git.exc`:
- `scripts/shared/git_helper.py:40` — local `import git.exc` inside function scope
- `scripts/mcp_servers/git/git_service.py:20` — top-level `import git.exc`

This prevents clean commits until the intermittent failure is resolved.

## Reason for Change
The hook's logic is correct — it finds files with `git.exc.` usage and flags any missing
`import git.exc`. However, the hook fails via pre-commit while passing when executed identically
in the terminal. This inconsistency blocks commit workflows.

## Target Files
- `.pre-commit-config.yaml` (hook definition)
- `scripts/shared/git_helper.py` (has `import git.exc` on line 40)
- `scripts/mcp_servers/git/git_service.py` (has `import git.exc` on line 20)

## Current Error
```
git.exc import guard.....................................................Failed
- hook id: git-exc-import-guard
- exit code: 1
```

## Investigation Notes
Manual verification commands (both pass):
```bash
# Find files with git.exc usage
rg -l "git\.exc\." scripts/
# Output: scripts/mcp_servers/git/git_service.py  scripts/shared/git_helper.py

# Check each file for import git.exc
for f in $(rg -l "git\.exc\." scripts/); do
    grep -n "import git\.exc" "$f" || echo "NO MATCH: $f"
done
# Output:
# scripts/mcp_servers/git/git_service.py:20:import git.exc
# scripts/shared/git_helper.py:40:        import git.exc
```

Pre-commit execution (fails):
```bash
uv run pre-commit run git-exc-import-guard --all-files
# Returns exit code 1 with no additional output
```

Possible causes:
1. Pre-commit may use a different working directory than expected
2. Pre-commit may check a different git index state (staged vs working tree)
3. Different shell/environment variables during pre-commit execution
4. Race condition or timing issue with file writes

## Acceptance Criteria
- `uv run pre-commit run git-exc-import-guard --all-files` passes without errors
- Hook reliably detects missing `import git.exc` when present
- Hook does not produce false positives when `import git.exc` exists

## Notes
This is a pre-existing issue unrelated to any recent feature changes. The hook was added
as part of the constraint-check mechanism in `plans/20260814-153545_plan.md` (now moved
to `implementations/done/`).
