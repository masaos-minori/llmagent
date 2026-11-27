# Git Commit and Sync - Edge Cases

Loaded only when the Phase 9 report needs the full form; the default is the compact form in `workflow.md`.

### Phase 9: full report

Use this report when the run had any deviation.

Report:
- branch and commit SHA; staged files; commit message
- pre-push recheck result (proceeded, already on upstream, or remote advanced, with the SHAs)
- sync result (already up to date, fast-forwarded, rebased, aborted due to a rebase conflict with the conflicted paths, or skipped because no upstream exists); pre-rebase SHA only when a rebase ran
- validation result (Phase 4 gates, and status/diff review or tests after a successful sync)
- unrelated gate failures ignored under Phase 4's rule (gate, command, exit code), if any
- push result (or reason push was skipped)
- other commits published (in the pre-push `@{u}..HEAD` list, not created by this run), if any
- remaining uncommitted changes (and whether Phase 6's check found any unstaged file temporarily missing)
- stop conditions triggered, with explanation; warnings
