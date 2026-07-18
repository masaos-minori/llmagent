## Goal

Implementation step 7 of `plans/20260717-180307_plan.md` (requirement 19): add a new "known gap"
entry to `docs/04_mcp_90_inconsistencies_and_known_issues.md` stating that
`config_dependent`/`enabled`/`disabled_reason`/`RuntimeToolRegistry` are documented as target
design (in the new `04_mcp_03_06` file) but not yet implemented in `scripts/`, with pointers to
the implementing plans (requirements 14-18), in the format confirmed by the format-precheck
procedure doc for Implementation step 1
(`20260718-101327_mcp90_and_consistency_test_format_precheck.md`).

## Scope

**In scope**: append one new entry to `docs/04_mcp_90_inconsistencies_and_known_issues.md`,
between the existing MDQ entry and the `## Related Documents` footer, following the file's real
current entry format (H2 heading + bullet fields + `---` rules), not the `MCP-NN` numbering
scheme the test file expects (that scheme is not present in the real file and retrofitting it is
out of scope for this plan).

**Out of scope**: adding `MCP-NN` numbering or a `## Active Issues` section wrapper (would be a
structural change to the whole file, not an additive entry, and is not requested by this plan);
editing any other section of this file.

## Assumptions

- Per the format-precheck investigation, the real current file (49 lines) has exactly one entry
  (`## MDQ ハイブリッド検索はstub（未実装）`, L28-36) using bullet fields
  `**Type:**`, `**Impact scope:**`, `**Current behavior:**`, `**Affected config:**`,
  `**Recommended action:**`, `**Notes for AI reference:**` (a slight variation on the declared
  template at L18-24, which additionally lists `**Statement A / B:**` and
  `**Current safe interpretation:**` — these are optional/guideline fields, not mandatory).
- The new entry's `**Type:**` value should be `Unimplemented` (matching the existing entry's
  usage for "designed but code doesn't do it yet"), since `config_dependent`/`enabled`/
  `disabled_reason`/`RuntimeToolRegistry` are confirmed absent from `scripts/` (zero grep matches
  for `config_dependent|disabled_reason|RuntimeToolRegistry`; `requires_config` still the active
  field, 51 occurrences across 10 files as of this investigation).
- Append point: after L37 (closing `---` of the MDQ entry), before L39 (`## Related Documents`)
  — i.e. insert at line 38.

## Implementation

### Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md` (49 lines total, edit in place — append)

### Procedure

1. Insert a new H2 entry after L37, before L39, following the real file's bullet-field format
   (not the `MCP-NN` scheme).
2. Entry title (H2 heading): something like "ツール可用性メタデータ
   （config_dependent/enabled/disabled_reason/RuntimeToolRegistry）は文書化済みだが未実装".
3. Bullet fields, modeled on the existing MDQ entry's field set:
   - `**Type:**` `Unimplemented`
   - `**Impact scope:**` `scripts/mcp_servers/**`（`requires_config`のまま）、
     `scripts/agent/**`（RuntimeToolRegistry未実装）
   - `**Current behavior:**` `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`に
     `config_dependent`/`enabled`/`disabled_reason`/`RuntimeToolRegistry`の対象設計が記述され
     ているが、実装コードは`requires_config`のままであり、`enabled`/`disabled_reason`は
     `/v1/tools`レスポンスに存在しない。RuntimeToolRegistryクラス自体も未実装。
   - `**Affected config:**` N/A（コード側フィールド名の問題であり、config側の値ではない）
   - `**Recommended action:**` requirement 14-18のプラン
     （`plans/20260717-173602_plan.md`, `plans/20260717-174024_plan.md`,
     `plans/20260717-174848_plan.md`, `plans/20260717-175327_plan.md`,
     `plans/20260717-175630_plan.md`）の実装完了後、本エントリを削除すること。
   - `**Notes for AI reference:**` `config_dependent`/`enabled`/`disabled_reason`/
     `RuntimeToolRegistry`という語がコード中またはテスト中に見つからない場合、これは
     ドキュメント先行（target design documented ahead of implementation）であり、バグでは
     ない。実装が完了したらこのエントリと`04_mcp_03_06`の「Implementation status」コールアウト
     の両方を更新/削除すること。
4. Wrap the entry with `---` before and after, matching the existing entry's convention.

### Method

Direct Markdown insertion of one new H2 entry (heading + 6 bullet fields + `---` wrapper). No
restructuring of the rest of the file.

### Details

Verbatim existing entry to model against (L28-36, for exact formatting fidelity):
```
## MDQ ハイブリッド検索はstub（未実装）

- **Type:** `Unimplemented`
- **Impact scope:** `scripts/mcp_servers/mdq/search.py`, `scripts/mcp_servers/mdq/tools.py`
- **Current behavior:** `use_embedding = true` でハイブリッド検索が有効になるが、`_search_vector()` は常に空リストを返す。セマンティック検索の結果は得られない。
- **Affected config:** `config/mdq_mcp_server.toml` の `use_embedding = true`
- **Recommended action:** ハイブリッド検索を本番投入するには、`_search_vector()` の実装が必要
- **Notes for AI reference:** MDQ のハイブリッド検索（`use_embedding = true`）は未実装（stub）。セマンティック検索が必要な場合は RAG パイプラインを使用すること。
```

This plan's new entry should mirror this exact shape (H2 title, then the 5-6 bullet fields in
the same order, then a trailing `---`).

Note: the format-precheck doc already flagged a real discrepancy between the test file's
`MCP-NN`/`## Active Issues` expectations and the real file's plain-heading format. This new
entry deliberately follows the **real file's actual format**, consistent with the existing MDQ
entry, and does not attempt to retrofit `MCP-NN` numbering (out of scope for this
documentation-only plan; that would be a separate structural-consistency fix, not requested by
requirement 19).

## Validation plan

- Manual read-through: confirm the new entry sits between the MDQ entry and
  `## Related Documents`, uses the same bullet-field shape, and is wrapped in `---` before/after.
- `grep -n "config_dependent\|disabled_reason\|RuntimeToolRegistry"
  docs/04_mcp_90_inconsistencies_and_known_issues.md` → expect new matches from this entry.
- `uv run check-mcp-docs` — run to confirm the real-file consistency checks (e.g.
  `check_active_inconsistencies`, which looks for `### MCP-NN:` headings under `## Active
  Issues`) do not choke on the new plain-heading entry — since the real file has no
  `## Active Issues` section at all, this checker function's `## Active Issues`-scoped logic
  should simply find no such section and behave as it already does for the existing MDQ entry
  (no regression expected, but confirm by running the CLI, not by assuming).
- `uv run pytest tests/test_check_mcp_docs_consistency.py -v` — expected to pass regardless
  (synthetic fixtures only, does not exercise this real file — see the format-precheck doc); not
  proof this edit is correct.
- `git diff docs/04_mcp_90_inconsistencies_and_known_issues.md` — confirm only one new entry
  appended, no existing content altered.
