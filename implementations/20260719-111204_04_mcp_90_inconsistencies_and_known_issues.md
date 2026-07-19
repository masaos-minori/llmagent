# Implementation: `docs/04_mcp_90_inconsistencies_and_known_issues.md` (delete stale MDQ hybrid-search entry)

Source plan: `plans/20260719-100727_plan.md` ("Implement `tags_json`/`token_count` in mdq-mcp;
reconcile stale MDQ known-issue docs"), Implementation step 5 (first half — deleting the stale
entry; the closure-note half of step 5 targets `docs/04_mcp_04_04_mdq.md` and
`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`, covered by separate docs).

Two existing implementations docs also target this same file:
`implementations/20260718-101707_04_mcp_90_inconsistencies_and_known_issues.md` and
`implementations/20260718-102052_04_mcp_90_deferred_include_disabled_disabled_code.md`. Both
read in full and confirmed **not a genuine overlap**: they each *add* a new, unrelated known-gap
entry (`config_dependent`/`enabled`/`disabled_reason`/`RuntimeToolRegistry` unimplemented, and
`include_disabled`/`disabled_code` deferred, respectively) — neither mentions or touches the
"MDQ ハイブリッド検索はstub" entry this item deletes. Flagged as checked, not a genuine overlap,
matching the convention in `implementations/20260717-224725_repl_health.py.md`. (Neither of those
two docs has been implemented in code yet either, per their own status, but that is independent
of this item — this item's target text and line range remain accurate regardless.)

## Goal

Delete the stale "MDQ ハイブリッド検索はstub（未実装）" entry
(`docs/04_mcp_90_inconsistencies_and_known_issues.md:28-36`), since the discrepancy it describes
(`use_embedding = true` as live config causing `_search_vector()` to always return `[]`) no
longer exists in any form — `config/mdq_mcp_server.toml` no longer has `use_embedding` (or the
other hybrid-search keys) at all, only a removal NOTE. Per `rules/coding.md`'s "Current
behavior" classification table, this is **"Obsolete and removable"**: delete the note, don't
reword it.

## Scope

**In scope**
- Delete the entry at `docs/04_mcp_90_inconsistencies_and_known_issues.md:28-36` and its
  surrounding separator line, per the exact boundary in Assumption 2 below.

**Out of scope**
- Any other section of this file (intro, template description, `## Related Documents`,
  `## Keywords`).
- Adding a *new* entry to this file — that is the job of the two other, already-pending
  implementation docs noted above (unrelated topics, different requirements).
- `docs/04_mcp_04_04_mdq.md` / `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` closure notes
  — covered by separate docs.

## Assumptions

1. Verified by direct read of the full file (49 lines total,
   `docs/04_mcp_90_inconsistencies_and_known_issues.md`): the entry to delete is exactly
   ```
   26: ---
   27: (blank)
   28: ## MDQ ハイブリッド検索はstub（未実装）
   29: (blank)
   30: - **Type:** `Unimplemented`
   31: - **Impact scope:** `scripts/mcp_servers/mdq/search.py`, `scripts/mcp_servers/mdq/tools.py`
   32: - **Current behavior:** `use_embedding = true` でハイブリッド検索が有効になるが、`_search_vector()` は常に空リストを返す。セマンティック検索の結果は得られない。
   33: - **Affected config:** `config/mdq_mcp_server.toml` の `use_embedding = true`
   34: - **Recommended action:** ハイブリッド検索を本番投入するには、`_search_vector()` の実装が必要
   35: - **Notes for AI reference:** MDQ のハイブリッド検索（`use_embedding = true`）は未実装（stub）。セマンティック検索が必要な場合は RAG パイプラインを使用すること。
   36: (blank)
   37: ---
   38: (blank)
   39: ## Related Documents
   ```
   Line 26 is a `---` separator between the file's intro/template-description block (ending at
   line 24) and this entry — it is this file's *only* entry today, so line 26's `---` also
   functions as "the separator before the first (only) entry." Line 37 is the closing `---`
   after this entry, before the blank line 38 and `## Related Documents` at line 39. This exactly
   matches the plan's own citation of "lines ~28-35" (off by one from the true 28-36 span, per
   this investigation's direct read) and the plan's Assumption 3's stated boundary.
2. To remove the entry cleanly while leaving exactly one `---` separator between the intro block
   and `## Related Documents` (matching this file's structural convention, and leaving the file
   ready for the two other pending, unrelated entries to be appended above `## Related Documents`
   in their own separate commits): **delete lines 27-37 inclusive** (blank line, heading, blank
   line, the 6 field bullets, blank line, and the closing `---`), and **keep line 26's `---`**
   as-is. After deletion, the file reads: `...` (line 25, blank) → `---` (former line 26) →
   (blank, former line 38) → `## Related Documents` (former line 39) — one separator, no
   dangling content.
3. Verified by direct read of `config/mdq_mcp_server.toml:67-73`: the file carries a removal
   NOTE, not live config:
   ```
   67: # NOTE: use_embedding, embedding_dims, vector_table, and embedding_model were
   68: # removed (2026-07-16). Hybrid/semantic search was never functionally implemented
   69: # -- _search_vector() in search.py always returned an empty list. FTS5 (BM25) is
   70: # the only supported search mode; use the RAG pipeline (rag-pipeline-mcp) for
   71: # semantic search. See docs/04_mcp_04_04_mdq.md and
   72: # docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md. Re-add only alongside a real
   73: # embedding-search implementation.
   ```
   No `use_embedding`/`embedding_dims`/`vector_table`/`embedding_model` keys exist anywhere else
   in this config file (confirmed per the source plan's own Assumption 3 investigation). This
   confirms the entry being deleted describes a discrepancy that "no longer exists in any form"
   per `rules/coding.md`'s "Obsolete and removable" classification, not a case needing a reword.
4. `tools/check_agent_docs_consistency.py`'s broken-internal-link check (run via `check-mcp-docs`
   or the standalone script) is the source plan's own stated mitigation for the risk that some
   other doc might cross-reference this entry — this item's Validation plan re-runs that check
   rather than manually grepping every doc in the repo for a reference to this entry's exact
   heading text.

## Implementation

### Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md`

### Procedure

1. Open `docs/04_mcp_90_inconsistencies_and_known_issues.md`.
2. Delete lines 27-37 inclusive (per Assumption 2's exact boundary): the blank line after the
   `---` at line 26, the `## MDQ ハイブリッド検索はstub（未実装）` heading, its blank line, its
   6 field bullets (`Type`/`Impact scope`/`Current behavior`/`Affected config`/
   `Recommended action`/`Notes for AI reference`), the trailing blank line, and the closing
   `---`.
3. Leave line 26's `---` in place, followed directly by the blank line and `## Related
   Documents` heading that previously sat at lines 38-39 (now immediately following, since the
   entry between them is gone).
4. Confirm the file's front matter (`title`/`category`/`tags`/`related`, lines 1-11), intro
   paragraph (lines 13-16), and field-format template description (lines 18-24) are all
   untouched.

### Method

Direct Markdown deletion — no restructuring, no renumbering (the file uses plain `## <title>`
headings, not an `MCP-NN` numbering scheme, so no adjacent-entry renumbering is needed).

### Details

No code, no test file, no schema involved — this is a pure documentation deletion. The file's
remaining structure after this edit: front matter → intro → field-format template → `---` →
`## Related Documents` → `## Keywords`, i.e. structurally identical to "zero known issues
currently on file," ready to receive the two other pending, unrelated entries
(`implementations/20260718-101707_...md` and
`implementations/20260718-102052_...md`) whenever those are implemented, independent of this
deletion.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Entry removed | `grep -n "MDQ ハイブリッド検索はstub\|use_embedding" docs/04_mcp_90_inconsistencies_and_known_issues.md` | 0 matches |
| Structure intact | `grep -n "^## " docs/04_mcp_90_inconsistencies_and_known_issues.md` | only `Related Documents` and `Keywords` remain (no orphaned entry heading) |
| No dangling separator | Manual read-through of the file | exactly one `---` between the intro/template block and `## Related Documents`; no double blank lines or duplicate `---` |
| Docs consistency | `uv run check-mcp-docs` (or `uv run python tools/check_agent_docs_consistency.py`) | no new ERROR/WARNING; confirms no other doc's cross-reference to this entry breaks |
| Cross-reference scan | `rg -rn "MDQ ハイブリッド検索はstub" docs/ scripts/ tests/` | 0 matches anywhere in the repo (confirms nothing else pointed at this specific heading text) |
| Docs test suite | `uv run pytest tests/test_check_mcp_docs_consistency.py -v` | passes unchanged (synthetic fixtures, not exercising this real file, per the precedent noted in `implementations/20260718-101707_...md`'s own Validation plan) |
| Diff review | `git diff docs/04_mcp_90_inconsistencies_and_known_issues.md` | only the one entry (lines 27-37) removed; no other line changed |
