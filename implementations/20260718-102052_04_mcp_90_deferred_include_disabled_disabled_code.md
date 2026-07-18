## Goal

Implementation steps 3-4 of `plans/20260717-181151_plan.md` (requirement 20): add a new
"known gap / deferred decision" entry to `docs/04_mcp_90_inconsistencies_and_known_issues.md`
stating that the `include_disabled` query-parameter filter and the `disabled_code` structured
enum were evaluated per requirement 20 and intentionally deferred (not implemented), with
cross-references back to `plans/20260717-181151_plan.md` and to the "Future / deferred design
options" subsection of `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` (once that file
exists — see the companion doc
`implementations/20260718-102011_04_mcp_03_06_future_options_appendix.md`). This is
documentation only; no source or test file is touched.

Note on a prior filename match: `implementations/20260718-101707_04_mcp_90_inconsistencies_and_known_issues.md`
also targets `docs/04_mcp_90_inconsistencies_and_known_issues.md`, but its Goal is Implementation
step 7 of `plans/20260717-180307_plan.md` (requirement 19) — a *different* known-gap entry,
stating that `config_dependent`/`enabled`/`disabled_reason`/`RuntimeToolRegistry` are documented
as target design but not yet implemented. That entry does not mention `include_disabled` or
`disabled_code` at all (confirmed: `grep -rl "include_disabled\|disabled_code"
implementations/` returns no matches anywhere in the repo prior to this doc). This is a
**false-positive filename match** for this plan's item — flagged here, not silently skipped —
and this new doc is deliberately named with an `include_disabled_disabled_code` slug to keep the
two entries distinguishable in any future filename search over the reused `04_mcp_90` target.

## Scope

**In scope**:
- Read `docs/04_mcp_90_inconsistencies_and_known_issues.md` in full (already done during this
  investigation) to match its existing entry format exactly.
- Add one new entry, in that file's existing format, describing `include_disabled` and
  `disabled_code` as evaluated-but-deferred.
- Re-verify via grep that the new entry does not misstate `config_dependent`/`disabled_reason` as
  already live (they are not — see Assumptions).

**Out of scope**:
- Any change to `scripts/mcp_servers/**`, `scripts/shared/**`, `scripts/agent/**`, or test files.
- Editing or duplicating requirement 19's own known-gap entry (`implementations/20260718-101707_...md`'s
  deliverable) — this is an additional, separate entry, not a replacement.
- Registering anything in `docs/04_mcp_00_document-guide.md` — `04_mcp_90` already exists and is
  already registered; adding a body entry to it needs no File Index change.

## Assumptions

1. `docs/04_mcp_90_inconsistencies_and_known_issues.md` exists today (confirmed via
   `find docs -iname "04_mcp_90*"` → `docs/04_mcp_90_inconsistencies_and_known_issues.md`), unlike
   `04_mcp_03_06` which does not exist yet — this step is actionable now, independent of
   requirement 19's status.
2. The file's current entry format (read in full) is:
   - A `---` frontmatter block (title/category/tags/related).
   - A short Japanese intro paragraph describing the file's purpose.
   - A bullet list defining each entry's expected fields: `**Type:**`, `**Impact scope:**`,
     `**Statement A / B:**` (when applicable), `**Current safe interpretation:**`,
     `**Recommended action:**`, `**Notes for AI reference:**`.
   - One `## <Japanese title>` section per issue, each followed by a `---` separator, containing
     the fields above (using whichever subset applies — the sole existing entry, "MDQ ハイブリッ
     ド検索はstub（未実装）", uses `Type`, `Impact scope`, `Current behavior`, `Affected config`,
     `Recommended action`, `Notes for AI reference` — a slight field-name variant of the header's
     own `Current safe interpretation` label, i.e. `Current behavior`/`Affected config` are used
     in practice for `Unimplemented`-type entries instead of `Statement A/B`).
   - A closing `## Related Documents` and `## Keywords` section at file end.
3. `config_dependent`/`disabled_reason` are still unimplemented in `scripts/` (verified in the
   source plan's Assumption 2, zero occurrences via
   `grep -rl "config_dependent\|disabled_reason\|RuntimeToolRegistry\|mcp_tool_discovery" scripts/`);
   the new entry must describe `include_disabled`/`disabled_code` as deferred without implying
   `config_dependent`/`disabled_reason` are already live.
4. Requirement 19's own known-gap entry (`config_dependent`/`disabled_reason` not yet implemented)
   may or may not exist in the live file yet at the time this entry is added — this entry is
   independent of that one and does not need it to exist first (no ordering dependency, unlike
   the `04_mcp_03_06` appendix step).

## Implementation

### Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md` (exists; current tail, before the closing
`## Related Documents` section, ends with the single "MDQ ハイブリッド検索はstub（未実装）" entry
followed by `---`).

### Procedure

1. Read `docs/04_mcp_90_inconsistencies_and_known_issues.md` in full (confirmed format per
   Assumptions above).
2. Insert a new `## <title>` entry immediately before the `## Related Documents` section (i.e.
   after the existing "MDQ ハイブリッド検索はstub（未実装）" entry and its trailing `---`),
   following the same field structure (`Type`, `Impact scope`, `Current behavior`/`Current safe
   interpretation`, `Recommended action`, `Notes for AI reference`), using `Type: Unimplemented`
   to match the deferred-but-designed nature of both proposals.
3. Terminate the new entry with a trailing `---` separator, matching the existing entry's
   convention, before `## Related Documents`.
4. Run `grep -rn "requires_config\|config_dependent\|disabled_reason" docs/04_mcp_90_inconsistencies_and_known_issues.md`
   after the edit and manually confirm the new entry's wording describes `include_disabled`/
   `disabled_code` as deferred/unimplemented, and does not assert `config_dependent`/
   `disabled_reason` as already live (it should only reference them as the still-target-design
   contract these codes/params would attach to, per Assumption 3).

### Method

Manual Markdown edit (no scripted generation, no code).

### Details

New entry content (Japanese, matching the file's existing language and field convention):

```
## `include_disabled` フィルタと `disabled_code` 構造化コードは評価済みだが未実装（意図的に延期）

- **Type:** `Unimplemented`
- **Impact scope:** `/v1/tools` エンドポイント全般（`scripts/mcp_servers/*/server.py` の
  10実装すべて）、将来の `disabled_reason` フィールド（requirement 15、未実装）
- **Current behavior:** `/v1/tools` は現在クエリパラメータを一切受け付けず、常に全ツールを
  無条件に返す（無効化されたツールも除外しない）。`include_disabled` クエリパラメータおよび
  `disabled_code` 列挙型はどちらも要求20で評価されたが、実装は行われていない。
- **Recommended action:** 実装が必要になった場合は `plans/20260717-181151_plan.md` の
  "Future / deferred design options" 提案（`docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
  作成後に追記予定）を参照すること。初期の RuntimeToolRegistry 移行（requirements 14-19）は
  これらのオプションに依存しない。
- **Notes for AI reference:** `include_disabled=false` や `disabled_code` への言及がコード上に
  見つからない場合、それは正常（未実装が既定の状態）。`config_dependent`/`disabled_reason`
  自体も別途未実装（requirements 14-18 未着手）であり、本エントリはそれらの実装状況を変更する
  ものではない。
```

Insert this block as a new `## ...` section, followed by `---`, directly before the file's
existing `## Related Documents` section.

## Validation plan

- `grep -c "include_disabled\|disabled_code" docs/04_mcp_90_inconsistencies_and_known_issues.md`
  → expect result `>0` after the edit (currently `0`, confirmed via
  `grep -rl "include_disabled\|disabled_code" implementations/` returning no matches, and the file
  containing no such terms before this edit).
- `grep -rn "requires_config\|config_dependent\|disabled_reason" docs/04_mcp_90_inconsistencies_and_known_issues.md`
  → manual read-through to confirm the new entry does not misstate current implementation status
  (Implementation step 4 above).
- Manual read-through confirming the new entry follows the file's existing field format
  (Type / Impact scope / Current behavior / Recommended action / Notes for AI reference).
- `uv run pytest tests/test_check_mcp_docs_consistency.py -v` — optional re-run; this test's
  fixtures are synthetic (`_mk_issues_file()` in
  `tests/test_check_mcp_docs_consistency.py:33-41`) and do not read the real `docs/` tree, so it
  is not expected to be affected by this content-only addition, but running it costs nothing and
  catches any unforeseen consistency-checker regression.
- No ruff/mypy/lint-imports/bandit/full-pytest/diff-cover run — Markdown-only change.
- `git diff --stat docs/04_mcp_90_inconsistencies_and_known_issues.md` reviewed before commit to
  confirm only the intended entry was added.
