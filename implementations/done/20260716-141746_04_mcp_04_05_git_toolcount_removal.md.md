# Implementation: docs/04_mcp_04_05_git.md (drop `（10個）` from the tool heading)

Source plan: `plans/20260716-135355_plan.md`

## Goal

Remove the `（10個）` parenthetical from the `**ツール（10個）:**` heading.

## Scope

**In:**
- Line 25: `**ツール（10個）:**` (git-mcp section)

**Out:**
- Any other content on this line or elsewhere in the file. Confirm during
  implementation whether the 10 tool names appear on the same line or a
  following line (per the earlier grep, nothing trailed on line 25 itself
  in the sampled output) — if the listing is on a subsequent line, leave
  it untouched.

## Assumptions

1. git-mcp has exactly 10 tools per `tools/check_mcp_docs_consistency.py`'s
   `_SERVER_TOOLS_MAP["git-mcp"]` (10 entries: `git_status`, `git_log`,
   `git_diff`, `git_branch`, `git_show`, `git_add`, `git_commit`,
   `git_checkout`, `git_pull`, `git_push`) — confirms the current "10個" is
   accurate before removal (not a stale-number fix, purely a
   maintenance-burden removal).

## Implementation

### Target file

`docs/04_mcp_04_05_git.md`

### Procedure

1. Open `docs/04_mcp_04_05_git.md`.
2. Locate line 25: `**ツール（10個）:**`
3. Replace with: `**ツール:**`
4. Confirm the tool-name listing (wherever it appears — same line or
   following lines) remains unchanged.

### Method

Single mechanical parenthetical removal.

### Details

- Do not alter any tool name in the listing.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Parenthetical removed | `grep -n "ツール（[0-9]*個）" docs/04_mcp_04_05_git.md` | 0 matches |
| Tool listing intact | `grep -n "git_status\|git_push" docs/04_mcp_04_05_git.md` | present, unchanged |
| Final sweep (run once all 6 doc files in this plan are edited) | `rg "ツール（\d+個）\|個のMCPサーバ\|個のtool" docs/` | 0 matches across all of `docs/` |
