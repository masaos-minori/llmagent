## Goal

Update the `/stats` hint description in
`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md` to match
the corrected hint string landed in
`implementations/20260719-103030_cmd_config_stats.py.md` — per `rules/coding.md`'s "Documentation fix
required" classification, since the doc was accurate before and must track the corrected code.

## Scope

**In scope**
- Update the hint-text quotation inside the bullet at line 96 from
  `` `Hint: Run /db rag consistency for index integrity status` `` to
  `` `Hint: Run /session rag-consistency for index integrity status` ``.

**Out of scope**
- Any other content in this bullet (the conditions under which `Memory inconsist.` / `Memory embed:
  CIRCUIT OPEN [DEGRADED]` / `Memory embed: fts_only x<N> [degraded]` are shown) or in the
  surrounding `実装補足` section (lines 93-97).

## Assumptions

1. The plan cites line 96 for this hint text; direct read confirms **no line-number drift**. However,
   the plan's Scope text describes the current string as `"Run /db rag consistency for index
   integrity status"` (matching what's actually in `cmd_config_stats.py` before this plan's fix), and
   direct read of the doc confirms it quotes the **exact same string**, embedded inside a longer
   Japanese sentence at line 96:
   ```
   96:- 条件付き行として、`stat_memory_consistency_failures` が真の場合のみ `Memory inconsist.`、メモリ埋め込みのサーキットブレーカーが開いている場合は `Memory embed: CIRCUIT OPEN [DEGRADED]`、そうでなくFTSフォールバック回数が1以上の場合は `Memory embed: fts_only x<N> [degraded]`、`rag_db_configured`(`db.config.build_db_config()` が例外なく成功するか)が真の場合は `Hint: Run /db rag consistency for index integrity status` が追加表示される。これらはドキュメントのサンプルには含まれていない(根拠: Explicit in code)。
   ```
   The exact substring to change is `` `Hint: Run /db rag consistency for index integrity status` ``
   (backtick-quoted, embedded mid-sentence) → `` `Hint: Run /session rag-consistency for index
   integrity status` ``.
2. This documentation note falls under `rules/coding.md`'s "Accepted current specification" /
   "Documentation fix required" classification scheme: prior to this plan, the doc accurately
   described the code (the hint really did say `/db rag consistency`), so it was correctly
   unlabeled prose (not a flagged discrepancy). Once `cmd_config_stats.py`'s hint string changes
   (per `implementations/20260719-103030_cmd_config_stats.py.md`), this doc becomes stale unless
   updated in lockstep — this is a same-day, same-plan "Documentation fix required" edit, not a new
   issue to file, since both the code change and the doc correction are part of this same plan's
   scope.
3. No other line in this file (`05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md`)
   references `/db rag consistency` — confirmed by the investigation's targeted read of lines 88-97;
   the surrounding bullets (88-91, 97) describe unrelated stats fields (`Partial completions`, `HB
   timeouts`, `Cache hits`, `Approval pending`, `Latency (mean/max)`) and do not mention the RAG hint.

## Implementation

### Target file

`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md`.

### Procedure

1. Edit line 96, replacing the substring `` `Hint: Run /db rag consistency for index integrity
   status` `` with `` `Hint: Run /session rag-consistency for index integrity status` ``, leaving the
   rest of the sentence (Japanese prose before and after) unchanged.

### Method

Single substring edit inside one existing bullet line. No structural change to the document.

### Details

No code changes. This is a documentation-only edit tracking the corrected hint string in
`cmd_config_stats.py`.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Old string fully removed | `rg -n "db rag consistency" docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md` | 0 matches |
| New string present | `rg -n "session rag-consistency" docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md` | 1 match, at (or near) line 96 |
| Rest of bullet unchanged | `sed -n '93,97p' docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md` | only the hint substring differs from the pre-edit text quoted in Assumption 1; surrounding Japanese prose, other conditional-line descriptions, and line 97 unchanged |
| Docs consistency checker | `uv run python tools/check_agent_docs_consistency.py` | no new ERROR/WARNING introduced |
| Cross-reference with code | `rg -n "session rag-consistency" scripts/agent/commands/cmd_config_stats.py docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md` | both files reference the identical corrected hint string |
