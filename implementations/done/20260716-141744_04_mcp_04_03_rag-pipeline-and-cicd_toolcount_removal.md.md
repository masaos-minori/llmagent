# Implementation: docs/04_mcp_04_03_rag-pipeline-and-cicd.md (drop `（N個）` from tool headings)

Source plan: `plans/20260716-135355_plan.md`

## Goal

Remove the `（4個）` parenthetical from both `**ツール（4個）:**` headings in
this catalog doc (rag-pipeline-mcp and cicd-mcp sections).

## Scope

**In:**
- Line 25: `**ツール（4個）:**` (rag-pipeline-mcp section)
- Line 75: `**ツール（4個）:**` (cicd-mcp section)

**Out:**
- Any other content on these lines or elsewhere in the file. Note both
  headings currently have no inline tool listing on the same line per the
  earlier grep (`**ツール（4個）:**` with nothing trailing) — confirm during
  implementation whether the tool names appear on the following line(s);
  if so, leave that continuation untouched.

## Assumptions

1. Both occurrences use the identical `**ツール（4個）:**` heading text
   (verified by direct read: both rag-pipeline-mcp and cicd-mcp happen to
   have exactly 4 tools each) — the edit is the same mechanical
   replacement in both places, applied independently at each line number.

## Implementation

### Target file

`docs/04_mcp_04_03_rag-pipeline-and-cicd.md`

### Procedure

1. Open `docs/04_mcp_04_03_rag-pipeline-and-cicd.md`.
2. Line 25: change `**ツール（4個）:**` to `**ツール:**`.
3. Line 75: change `**ツール（4個）:**` to `**ツール:**`.
4. Confirm both edits target the correct distinct sections
   (rag-pipeline-mcp at line 25, cicd-mcp at line 75) — do not
   accidentally apply a blanket find/replace that could match an
   unintended third occurrence if one exists; re-`grep` after editing to
   confirm exactly the expected two lines changed.

### Method

Two mechanical parenthetical removals, identical shape, at two distinct
section headings that happen to share the same tool count.

### Details

- Do not alter any content following the heading on subsequent lines
  (the tool-name listing, wherever it appears).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Parentheticals removed | `grep -n "ツール（[0-9]*個）" docs/04_mcp_04_03_rag-pipeline-and-cicd.md` | 0 matches |
| Both sections still present | `grep -n "^## " docs/04_mcp_04_03_rag-pipeline-and-cicd.md` | rag-pipeline-mcp and cicd-mcp section headers both still present, unchanged |
