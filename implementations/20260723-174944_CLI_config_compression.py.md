## Goal

Compress exhaustive CLI argument tables and configuration key tables in seven design and operations documents into concise Japanese summaries and source references, separating design-relevant configuration behavior from mechanically recoverable implementation details.

## Scope

**In**:
- Compress exhaustive CLI and configuration reference details in 7 documents
- Replace with Japanese summaries under suggested section headings (`## 設定の責務境界`, `## 変更時の運用影響`, `## 再起動が必要な設定`, `## ホットリロード可能な範囲`, `## 起動失敗につながる設定`, `## セキュリティに関わる設定`, `## 実装詳細の参照先`)
- Preserve specific configuration behaviors (`startup_mode` operational impact, `security_profile` fail-fast/fail-open behavior, process-local configuration rules, etc.)

**Out**:
- Modifying source code
- Creating ADR documents
- Modifying `00_index.md`
- Resolving any individual NC items
- Removing design intent, responsibility boundaries, invariants, failure behavior, or operational constraints

## Assumptions

1. All seven target documents exist at their expected paths.
2. The existing CLI/configuration listings can be safely compressed without losing design-relevant information.

## Design decisions

- Group configuration by purpose rather than listing each key individually.
- Use exact Japanese section headings as specified in the requirement where they improve clarity.
- Preserve all design-relevant content including: startup_mode operational impact, security_profile fail-fast/fail-open behavior, process-local configuration rules, and other specific configuration behaviors listed in scope.
- Keep implementation notes that describe design rationale; only compress field-level detail.

## Alternatives considered

- Delete CLI/configuration details entirely: loses operator-facing contract information.
- Create separate CLI reference documents: fragments documentation unnecessarily.
- Keep full listings but add navigation links: doesn't reduce cognitive load.

## Implementation

### Target file

7 documents: `docs/03_rag_05_1-configuration-reference.md`, `docs/04_mcp_06_02_configuration-file-inventory.md`, `docs/05_agent_08_01_configuration-loading-agent-config-part1.md`, `docs/05_agent_08_02_configuration-loading-agent-config-part2.md`, `docs/06_eventbus_05_01_config-env-and-fields.md`, `docs/02_deployment-part1.md`, `docs/02_deployment-part2.md`

### Procedure

1. Verify all seven target documents exist at expected paths; record any not found
2. For each document:
   a. Read the document and identify the CLI/configuration detail sections
   b. Classify each candidate before editing: design-relevant vs implementation-derived
   c. Compress implementation-derived details into Japanese summaries
   d. Apply suggested section headings where appropriate
   e. Add source references where appropriate
3. Verify preservation of specific configuration behaviors listed in scope

### Method

Replace detailed field-by-field tables with responsibility-oriented groupings.

### Details

For `05_agent_08_01_configuration-loading-agent-config-part1.md`, replace the detailed configuration tables with:

```markdown
# エージェント設定

## 設定の責務境界

### 設定ファイルの所有関係

| ファイル | 責務 | ホットリロード |
|---|---|---|
| `config/agent.toml` | エージェントプロセス設定（LLM/RAG/DB/ツール/メモリ/観測/承認/MCPライフサイクル） | ほとんど可能; `use_memory_layer`/`memory_embed_enabled`は起動時のみ |
| `config/*_mcp_server.toml` | MCPサーバー固有設定（allowlist/denylist/リソース制限/監査パス等） | 再起動必須（追加/削除/リネーム時） |

### 再起動が必要な設定

- MCPサーバーのURL、認証トークン、起動モード、コマンド、環境変数の変更
- `use_memory_layer` — メモリサブシステムの有効/無効（起動時のみ）
- `memory_embed_enabled` — 埋め込み生成・KNN検索の有効/無効（起動時のみ）
- `memory_jsonl_dir` — メモリエントリのJSONLバックアップ先ディレクトリ（起動時のみ）
- `routing_drift_strict` — ルーティングドリフトのfatal扱い（起動時のみ）

### ホットリロード可能な範囲

- LLMClient: temperature, max_tokens, max_retries, retry_base_delay, SSEパラメータ
- HistoryManager: context_char_limit, context_compress_turns, context_token_limit, tokenize_url
- ToolExecutor: tool_cache_ttl
- システムプロンプト: system_prompt_tool → `ctx.conv.system_prompt_content`

### 変更時の運用影響

`ConfigReloadOutcome`の出力で以下のカテゴリを確認:
- `[APPLIED]` — ホットリロード適用済み
- `[RESTART]` — サブシステム再起動が必要
- `[STARTUP-ONLY]` — `/reload`では変更できないフィールド

## 実装詳細の参照先

フィールド単位の完全なマッピングについては `agent/services/config_reload.py` を参照。
```

Apply similar compression to remaining six documents following the same pattern, adapting section headings based on which are relevant for each document.

## Compatibility considerations

None — documentation-only change; no behavioral impact.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

Restore original CLI/configuration details from git history; no data migration or config changes required.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Markdown rendering | Manual review | Correct rendering |
| Content preservation | Manual review | No design-relevant content loss |
| Listing reduction | Manual review | Significant reduction achieved |
| Configuration behavior verification | Manual review | All specific configuration behaviors preserved |

## Out of scope

- Modifying source code
- Creating ADR documents
- Modifying `00_index.md`
- Resolving any individual NC items
- Removing design intent, responsibility boundaries, invariants, failure behavior, or operational constraints

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-165912_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-174944
- Related target files: Implementation-dependent — design and operations documents
