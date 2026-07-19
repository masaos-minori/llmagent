## Goal

Implementation step 2 of `plans/20260717-180307_plan.md` (requirement 19): a sequencing check
that must be re-run immediately before editing the four MCP server-catalog docs
(`docs/04_mcp_04_01_web-search-file-read-github.md`, `docs/04_mcp_04_02_file-write-file-delete-shell.md`,
`docs/04_mcp_04_03_rag-pipeline-and-cicd.md`, `docs/04_mcp_04_05_git.md`), because a **sibling**
plan (`plans/20260717-173602_plan.md`, requirement 14) independently commits to renaming
`requires_config` → `config_dependent` in these same 4 files. This plan (requirement 19) only
adds new `enabled`/`disabled_reason` computation notes next to the existing field mentions — it
must never perform the rename itself, to avoid a duplicate/clobbering edit against requirement
14's commit.

## Scope

**In scope**: re-grep the 4 files for `requires_config` immediately before editing (Implementation
step 5, covered by its own procedure doc), and record the branch logic: if requirement 14 has
already landed (zero matches), this plan's edits reference `config_dependent` directly with no
adjacent `requires_config` text; if requirement 14 has not landed (matches found — the current
state as of this investigation), this plan's new notes are added **next to**, not replacing, the
`requires_config` text, and this plan does **not** perform the rename.

**Out of scope**: performing the `requires_config` → `config_dependent` rename itself (that
remains requirement 14's / `plans/20260717-173602_plan.md`'s own commit, tracked by whatever
implementation-procedure doc(s) exist for that plan under `implementations/`).

## Assumptions

- As of this investigation (2026-07-18), requirement 14 has **not yet landed**: the rename has
  not been applied to the real doc files. Confirmed by direct grep (see Details) — all 4 files
  still contain `requires_config` mentions, and no `config_dependent` string appears in any of
  the 4 files.
- Because requirement 14 has not landed yet, the procedure doc for Implementation step 5 (this
  plan's actual edit to the 4 files) must add the new `enabled`/`disabled_reason` note
  immediately adjacent to the existing `requires_config` line/table cell, not replace it — so
  that whichever plan (14 or 19) lands its own commit first, the other's later commit is a clean
  textual adjacency, not a semantic clash on the same line.
- If, by the time Implementation step 5 is actually executed, requirement 14 HAS landed (i.e. the
  re-grep at that time returns zero matches and `config_dependent` is present instead), the
  procedure doc for step 5 should be treated as needing this one adjustment: reference
  `config_dependent` in the new note instead of `requires_config`, with no other change to the
  plan.

## Implementation

### Target file

- `docs/04_mcp_04_01_web-search-file-read-github.md` (read only, this step)
- `docs/04_mcp_04_02_file-write-file-delete-shell.md` (read only, this step)
- `docs/04_mcp_04_03_rag-pipeline-and-cicd.md` (read only, this step)
- `docs/04_mcp_04_05_git.md` (read only, this step)

### Procedure

1. Run `grep -rn "requires_config" docs/04_mcp_04_01_web-search-file-read-github.md
   docs/04_mcp_04_02_file-write-file-delete-shell.md docs/04_mcp_04_03_rag-pipeline-and-cicd.md
   docs/04_mcp_04_05_git.md` immediately before executing Implementation step 5.
2. Also run `grep -rln "config_dependent" docs/04_mcp_04_01_web-search-file-read-github.md
   docs/04_mcp_04_02_file-write-file-delete-shell.md docs/04_mcp_04_03_rag-pipeline-and-cicd.md
   docs/04_mcp_04_05_git.md` to detect whether requirement 14's rename has already landed.
3. Branch: if `requires_config` matches are found (rename not landed) — add this plan's new
   `enabled`/`disabled_reason` note adjacent to the existing `requires_config` mention, do not
   touch the `requires_config` text itself. If no `requires_config` matches are found and
   `config_dependent` is present instead (rename landed) — add the new note referencing
   `config_dependent`.
4. No file is modified in this step; the actual edit happens in Implementation step 5.

### Method

Read-only grep-based check; no code/doc changes performed here.

### Details

Investigation performed 2026-07-18 confirms the current (pre-landing) state:

- `docs/04_mcp_04_01_web-search-file-read-github.md` (158 lines total) —
  L67: `全ツールとも config を必要としない（`requires_config: false`）。` (after the file-read
  tool list `read_media_file, read_multiple_files, search_files, grep_files, get_file_info`);
  L111: `全ツールとも config が必須（`requires_config: true`）。` (after the github tool list).
- `docs/04_mcp_04_02_file-write-file-delete-shell.md` (141 lines total) —
  L28: `全ツールとも config を必要としない（`requires_config: false`）。` (after
  `write_file, edit_file, create_directory, move_file`); L60: same sentence (after
  `delete_file, delete_directory`).
- `docs/04_mcp_04_03_rag-pipeline-and-cicd.md` (111 lines total) — `requires_config` appears only
  as a **table column** (not prose): L77 header row `| ツール | ティア | 入力 |
  `requires_config` |`, L79 first data row `| `trigger_workflow` | WRITE_DANGEROUS |
  `{repo, workflow, ref?, inputs?}` | yes |`.
- `docs/04_mcp_04_05_git.md` (77 lines total) — L27 prose: `全ツールとも config が必須
  （`requires_config: true`）。`; L29 table header `| ツール | ティア | `read_only` ガード |
  `dry_run` | `requires_config` |`; L31 first data row `| `git_status` | READ_ONLY | — | — |
  yes |`.

None of the 4 files currently contain `config_dependent` — requirement 14 has not landed as of
this check. This confirms Implementation step 5's procedure doc (separate file) must add
adjacent notes only, per the branch above.

Baseline reconciliation note: the plan's Assumption 2 cites "10 files, 47 occurrences" of
`requires_config` under `scripts/`. A fresh `grep -rn "requires_config" scripts/ | wc -l` at
investigation time returns **51** (10 files unchanged), a drift of +4 from the plan's stated
baseline — likely a difference in exact grep invocation/counting method between the plan
author's check and a plain `grep -rn | wc -l`. This does not affect the doc-only scope of this
plan (Assumption 2's substantive point — `requires_config` still active in `scripts/`,
`config_dependent`/`enabled`/`disabled_reason`/`RuntimeToolRegistry` not yet present — is
unaffected by the exact count), but is worth flagging as a minor discrepancy rather than
silently treating the plan's number as re-verified.

## Validation plan

- No file changed in this step.
- Downstream: before Implementation step 5's edit is applied, re-run the two greps in Procedure
  step 1-2 above one more time (state may have changed between plan-writing time and execution
  time), and apply the correct branch.
- Downstream: Implementation step 8 (final leakage check, covered by its own procedure doc) must
  confirm the new `04_mcp_03_06` file and the 4 catalog-doc additions never claim
  `requires_config` is still active/current.
