# `docs/99_documentation_sync_report.md` has a stray, unresolved merge-conflict marker committed at line 1

## Problem

`docs/99_documentation_sync_report.md` begins with a literal Git conflict
marker that was committed as real file content:

```
1: <<<<<<< HEAD
2: ---
3: title: "Documentation Sync Report"
...
```

This is not an actual unresolved 3-way conflict — there is no matching
`=======`/`>>>>>>>` pair anywhere else in the file (confirmed: `grep -n
"^<<<<<<<\|^=======$\|^>>>>>>>" docs/99_documentation_sync_report.md` returns
only this single line-1 match). It is a stray leftover marker line that was
never cleaned up before committing, not a genuine merge artifact needing
3-way resolution.

## Origin

Introduced in commit `4c47d645` ("doc: remove private method references
from agent docs (3 refs); add documentation sync report", 2026-07-13
18:47:23 +0900) — confirmed via `git log --all -S"<<<<<<< HEAD" --
docs/99_documentation_sync_report.md`. That commit is a regular
single-parent commit, not a merge commit (`git show 4c47d645 --format="%P"
-s` shows one parent), so the marker was manually typed/pasted rather than
produced by an actual `git merge` conflict at commit time. It has survived
two subsequent full doc-sync passes untouched (`62e275a5` on 2026-07-13,
`621344b5` on 2026-07-18), both of which edited other lines in this same
file without removing the stray marker.

## Downstream impact

The marker sits *before* the YAML frontmatter's opening `---` delimiter
(now line 2, was line 1 before the marker was inserted). Any tooling that
detects frontmatter by checking whether line 0 is exactly `---` will see
`<<<<<<< HEAD` instead and skip frontmatter parsing entirely for this file.
Concretely: `scripts/mcp_servers/mdq/parser.py`'s `parse_markdown()` checks
`if i == 0 and stripped == "---":` — for this file that condition is now
false, so the frontmatter block (`tags: [documentation-sync, run-report,
known-issues]`) is never stripped or extracted, and if this file is ever
indexed via mdq, `<<<<<<< HEAD` plus the full frontmatter block would be
absorbed into a `<root>` section as plain content instead of being parsed
as metadata.

No other `docs/*.md` file links to `99_documentation_sync_report.md`
(confirmed: no hits in `docs/index.md` or other doc files), so this is
currently an orphaned report file with no cross-reference breakage — the
impact is limited to the file's own frontmatter/content integrity, not
broken links elsewhere.

## Reproduction

```bash
grep -n "^<<<<<<<\|^=======$\|^>>>>>>>" docs/99_documentation_sync_report.md
# => 1:<<<<<<< HEAD  (single stray marker, no matching pair)
head -2 docs/99_documentation_sync_report.md
# => <<<<<<< HEAD
#    ---
```

## Why this wasn't fixed inline

Filed per explicit user request to record the finding rather than
auto-fix it; per `rules/coding.md`'s "Current behavior" classification
table this is squarely a "Documentation fix required" case (the doc
itself is wrong — a stray leftover marker, not a code/spec mismatch), so
no design decision is needed before fixing. The fix is a one-line
deletion once someone chooses to apply it.

## Recommended action

Delete line 1 (`<<<<<<< HEAD`) from `docs/99_documentation_sync_report.md`
so the file's first line is the frontmatter's opening `---` again. No
other content changes needed. Consider adding a repo-wide pre-commit or
`tools/check_docs_consistency.py` check that greps for `^<<<<<<<
\|^=======$\|^>>>>>>>` across `docs/*.md` to catch this class of leftover
marker before it reaches `master` again.
