# Implementation: Document unified GitHub mutation set and dry-run failure semantics

Source plan: `plans/20260715-141245_plan.md` (Implementation step 5)

## Goal

Document, in the agent tool-execution/approval doc set:
1. the single shared GitHub mutation set (`GITHUB_WRITE_TOOLS |
   GITHUB_DANGEROUS_TOOLS`) now used by both `tool_policy.py` and
   `tool_approval.py` (replacing two independently-maintained local
   frozensets).
2. the `gitops_push_blocked` scope — it blocks a narrower
   `_GITOPS_BLOCKABLE_TOOLS` set that excludes
   `github_create_issue`/`github_add_issue_comment` — and why.
3. the new dry-run-error-blocks-HIGH-risk-tools behavior vs. the
   unchanged dry-run-unsupported/connection-failure fallback.

## Scope

**In scope**
- Add a short subsection to the target file named in the plan,
  `docs/05_agent_06_01_tool-execution-and-approval-execution.md`.

**Out of scope**
- Rewriting existing sections of the doc set.
- Any source-code change (documentation only).

**IMPORTANT — target-file discrepancy found; flagged, not silently
resolved:**

The plan names `docs/05_agent_06_01_tool-execution-and-approval-execution.md`
as the file to update. Reading that file shows its actual content is
`ToolExecutor`, parallel/serial execution, and the DAG scheduler — it
does not currently discuss `gitops_push_blocked`, GitHub tool
classification, or dry-run previews at all. The content the plan
describes (gitops flags, the 7-tool GitHub write list, dry-run preview
behavior) already lives in the **sibling file**
`docs/05_agent_06_02_tool-execution-and-approval-approval.md`, in its
"gitops系フラグと承認フローの関係" (line 103) and "ドライラン プレビュー"
(line 125) sections — confirmed by direct read of both files. Both
files share the same `related:` front-matter cross-links (06_01 lists
06_02 and vice versa is assumed), so they are treated as one document
set per `routing.md`'s "Agent REPL flow / tool execution" mapping
(`docs/05_agent_03_01_...` + `docs/05_agent_06_01_...`).

This document therefore describes the change as a **two-file update**:
- **Primary edit**: `docs/05_agent_06_02_tool-execution-and-approval-approval.md`
  — update the existing "GitHub書き込みツール" table (lines 109-122) and
  "gitops系フラグと承認フローの関係" section (lines 103-108) to reflect the
  shared-constant-derived `_GITOPS_BLOCKABLE_TOOLS`, and add a new
  subsection after "ドライラン プレビュー" (after line 128) describing the
  dry-run-error-blocks-HIGH-risk behavior.
- **Secondary edit** (to satisfy the plan's literal file path): add a
  one-line cross-reference in `docs/05_agent_06_01_tool-execution-and-approval-execution.md`
  pointing to the new 06_02 subsection, so a reader who lands on 06_01
  first (as the plan's author apparently did) is not left without a
  pointer.

This is flagged for reviewer/implementer confirmation: this document
does not skip the plan's literal instruction, but implements it in a way
consistent with the doc set's actual content ownership, and calls out
the discrepancy explicitly rather than silently placing unrelated
content into 06_01 or silently editing only 06_02 without a trace back
to the plan's stated target.

## Assumptions

1. Both `docs/05_agent_06_01_...` and `docs/05_agent_06_02_...` are part
   of the same numbered document family (`05_agent_06_0N`) and are
   cross-linked via `related:` front matter — placing detailed content
   in whichever of the two already owns that topic, with a short
   pointer in the other, matches the existing convention seen elsewhere
   in `docs/` (e.g. topic ownership split across `_part1`/`_part2` or
   numbered subsections with cross-links).
2. The doc set is written in Japanese throughout (confirmed: both files'
   body text, headings, and existing tables are Japanese). New content
   added to these files should match — this diverges from
   `rules/coding.md`'s "Comments and log output: English only" rule,
   but that rule governs source-code comments/log messages, not
   Markdown documentation prose; the existing doc files are the
   controlling precedent for doc-file language.
3. No change to front matter `tags`/`related` is required — the new
   subsection fits under existing topics already tagged
   (`tool-execution`, and 06_02's own approval-related tags, not
   directly inspected here since it is the secondary file, but assumed
   unaffected since only a subsection is added, not a new topic).

## Implementation

### Target file

- `docs/05_agent_06_01_tool-execution-and-approval-execution.md` (as
  literally named by the plan — cross-reference only, see below)
- `docs/05_agent_06_02_tool-execution-and-approval-approval.md` (primary
  content location — see discrepancy note above)

### Procedure

1. In `docs/05_agent_06_02_tool-execution-and-approval-approval.md`:
   - Update the "gitops系フラグと承認フローの関係" section (starting line
     103) to replace the description "`_GITHUB_WRITE_TOOLS`に対して即時拒否"
     with a description of the shared-derived
     `_GITHUB_MUTATION_TOOLS`/`_GITOPS_BLOCKABLE_TOOLS` constants and
     their source (`shared.tool_constants.GITHUB_WRITE_TOOLS |
     GITHUB_DANGEROUS_TOOLS`, minus the two issue-tracker tools).
   - Update the "GitHub書き込みツール" table (lines 109-122) — the table
     content (7 tools) is unchanged, but add a short note directly below
     it stating that `github_create_issue`/`github_add_issue_comment`
     are members of the shared GitHub mutation set (used elsewhere for
     `OperationType.API_WRITE` classification and repo-allowlist checks)
     but are **excluded** from `gitops_push_blocked` blocking — this is
     the resolved UNK-03 scope decision, flagged for reviewer sign-off
     per the plan's Risks section.
   - Add a new subsection after "ドライラン プレビュー" (after line 128),
     e.g. titled "ドライラン失敗時のHIGHリスクツール拒否", describing:
     - a dry-run result with `is_error=True` on a `RiskLevel.HIGH` tool
       → `check_approval()` denies immediately
       (`denied_dry_run_error`), no prompt.
     - a dry-run raising `RuntimeError`/`OSError` (unsupported /
       connection failure) → unchanged: falls back to text-only preview,
       still prompts.
     - note that as of this writing no GitHub tool is in
       `approval_dry_run_tools` by default, so this path is currently
       dormant for GitHub tools and only activates if an operator opts
       one in.
2. In `docs/05_agent_06_01_tool-execution-and-approval-execution.md`: add
   one line near the top (in the existing bullet list at lines 19-20)
   cross-referencing the approval-flow doc:
   ```
   - GitHub変更操作の承認/gitops制御 → [05_agent_06_02_tool-execution-and-approval-approval.md](05_agent_06_02_tool-execution-and-approval-approval.md)
   ```

### Method

Documentation-only edit; Markdown prose and one table annotation, no
code blocks beyond illustrative constant names. Keep additions
consistent with the existing Japanese technical-writing style and
heading level conventions (`###`/`####`) already used in both files.

### Details

- Do not delete or renumber any existing section — only insert new
  subsections/notes.
- Cross-check the final `gitops_push_blocked`-excluded-tools note
  against the actual shipped constant name
  (`_GITOPS_BLOCKABLE_TOOLS`) once `tool_approval.py` is implemented
  (see `20260715-154002_tool_approval.py.md`) — the doc must name the
  real constant, not a placeholder.
- If reviewers determine during PR review that 06_01 should also carry
  full content (not just a cross-reference) because the plan explicitly
  named it, that is a low-cost follow-up — the cross-reference line can
  be expanded into a full duplicate subsection without any source-code
  impact.

## Validation plan

```bash
uv run check-mcp-docs   # confirms no unrelated MCP doc-consistency regressions
```

Since this is a documentation-only change, standard code-quality gates
(ruff/mypy/pytest) do not apply. Manual review checklist:
- [ ] New content accurately names `_GITHUB_MUTATION_TOOLS` /
      `_GITOPS_BLOCKABLE_TOOLS` as implemented (not `_GITHUB_WRITE_TOOLS`,
      which will no longer exist after the `tool_approval.py` change).
- [ ] The 7-tool table and the 2-tool exclusion list match the actual
      shipped constants exactly.
- [ ] Dry-run failure semantics description matches the actual
      `ApprovalPreviewBlockingError` behavior implemented per
      `20260715-154002_tool_approval.py.md` and
      `20260715-154002_tool_exceptions.py.md`.
- [ ] Cross-reference link in 06_01 resolves to a real heading in 06_02.

## Note on prior implementation documents

No existing document under `implementations/` or `implementations/done/`
targets `05_agent_06_01_tool-execution-and-approval-execution.md` or
`05_agent_06_02_tool-execution-and-approval-approval.md` (confirmed via
`find implementations -iname "*05_agent_06_0*"` — no results). This is a
new implementation item with no prior overlap to reconcile.
