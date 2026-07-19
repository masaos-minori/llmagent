# Implementation procedure: `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` (stale `db_allowlist` reference removal, line 111)

Source plan: `plans/20260719-101501_plan.md`, Implementation step 7 (Design step 4, Required
Change 2 from the source requirement).

`grep -rl "05_03_fail-open-fail-closed-and-risk-tiers\|fail-open-fail-closed"` across
`implementations/` and `implementations/done/` found exactly one prior hit:
`implementations/done/20260712-164711_docs_front_matter_dead_reference_cleanup.md`. Checked by
content: that doc's only reference to this filename is as one entry in a *frontmatter-splitting
lineage mapping table* (documenting which old, pre-split file this page descended from) — it
does not touch line 111 or the `db_allowlist` content at all. Not a genuine overlap; this is a
distinct, not-yet-implemented edit.

## Goal

Remove the stale `db_allowlist`/SQLite-access-denial numbered note (line 111, item 4 of the "AI
システムのための注記" section) from `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`,
since it describes access control for a server (SQLite MCP) that no longer exists.

## Scope

**In scope**
- Delete list item 4 (line 111) from the "## AI システムのための注記" numbered list
  (section starts at line 101, verified).
- Renumber the remaining list items (5→4, 6→5, 7→6) if the list uses explicit numeric prefixes
  that Markdown does not auto-renumber on render (Markdown ordered lists typically auto-render
  sequential numbers regardless of the source numerals used, but the *source* numerals should
  still be kept sequential for readability when the file is read as raw text, matching this
  project's apparent convention of matching source numerals to rendered numerals in this file).

**Out of scope**
- No change to any other numbered item (1, 2, 3, and the current 5/6/7) or any other section of
  this file (the Fail-Open/Fail-Closed summary table, Risk Tiers, Dry-Run sections, etc. are
  untouched).
- Per `rules/coding.md`'s "Current behavior" classification table: this note is classified
  **Obsolete and removable** ("The discrepancy no longer exists (verify against current code
  first). Delete the note.") — verified per Assumption 2 below that no current server's
  fail-closed policy depends on this item, so outright deletion (not a rewrite describing a
  replacement mechanism) is the correct action, matching the plan's own Design step 4 guidance:
  "if the surrounding list is otherwise still accurate, remove just this one item rather than
  the whole section."

## Assumptions

1. Verified directly (`docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md:111`, re-read
   fresh in this cycle):
   ```
   4. **`db_allowlist` が空 = SQLite アクセス拒否。** `rag` と `session` のエントリを設定すること。
   ```
   This matches the plan's Design step 4 quote exactly — no drift between the plan's citation
   and the file's current state.
2. Verified: no current MCP server's config (`grep -rn "db_allowlist" config/ scripts/` —
   confirm at implementation time; this investigation's broader survey of `config/agent.toml`
   and every sampled per-server TOML found no `db_allowlist` key anywhere) references
   `db_allowlist`. The SQLite MCP server itself does not exist in `scripts/mcp_servers/`
   (verified: `ls scripts/mcp_servers/` lists 10 current server subpackages, no `sqlite/`
   directory — same finding used to justify the paired `AGENTS.md` doc's edit). Deleting this
   item removes a reference to a config key and server that both no longer exist; no other
   current item in this list (items 1, 2, 3, 5, 6, 7) depends on or cross-references item 4.
3. The surrounding list items (1-3, 5-7, verified by direct read of lines 103-119) are all still
   accurate and describe currently-real config keys (`allowed_repos`, `command_allowlist`,
   `allowed_repo_paths`, `workflow_allowlist`, mdq-mcp production-readiness, `dry_run`) — per the
   plan's Design step 4 guidance, only item 4 is removed; the section itself is kept.
4. Per the plan's own Non-Goals: "No SQLite MCP re-add — its removal ... was deliberate; not
   reversed here." This edit is a pure deletion of a stale doc reference, not a functional
   change and not a re-add of SQLite MCP.

## Implementation

### Target file

`docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`.

### Procedure

1. Delete line 111 in full:
   ```
   4. **`db_allowlist` が空 = SQLite アクセス拒否。** `rag` と `session` のエントリを設定すること。
   ```
   (and the blank line immediately following it, if one exists solely as this item's paragraph
   separator — verify exact surrounding whitespace at implementation time so the remaining list
   items' spacing stays consistent with the rest of the section).
2. Re-verify the current line 109's item (`3. **allowed_repo_paths が空 = git アクセス拒否。**
   ...`) and line 113's item (currently numbered `5.`, the `workflow_allowlist` note) — renumber
   line 113 from `5.` to `4.`, and correspondingly renumber the subsequent items (`6.`→`5.`,
   `7.`→`6.`) so the source numerals remain sequential, per Scope.

### Method

Single-item deletion plus sequential renumbering of the remaining list items in the same
section; no other textual change.

### Details

Not applicable (documentation file, no code).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Stale reference removed | `grep -n "db_allowlist" docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | 0 matches |
| List renumbered correctly | manual read of the "AI システムのための注記" section (lines ~101-119 pre-edit) | items read `1.`-`6.` sequentially with no gap or duplicate number |
| Surrounding items intact | `grep -n "allowed_repo_paths が空\|workflow_allowlist は fail-closed\|mdq-mcp は本番運用可能\|dry_run" docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | all still present, unchanged in wording |
| No other stale sqlite reference in this file | `grep -in "sqlite" docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | 0 matches after this edit (confirm none existed elsewhere in the file before concluding the fix is complete) |
| Docs consistency | `uv run python tools/check_agent_docs_consistency.py` | no new ERROR/WARNING |
| MCP docs consistency | `uv run check-mcp-docs` | passes (no fail-open wording regression introduced by the renumbering) |
