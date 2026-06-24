# Implementation Procedure: docs/03_rag_01_system_overview.md + docs/03_rag_03_query_pipeline.md

## Goal

`scripts/mcp/rag_pipeline/server.py` と `service.py` の責務分割を明文化する。

## Scope

**In:**
- `docs/03_rag_01_system_overview.md` — MCP エントリポイントの説明
- `docs/03_rag_03_query_pipeline.md` — 呼び出しパスの記述

**Out:** MCP サーバー実装のリファクタリング

## Canonical 責務分割

| ファイル | 責務 |
|---|---|
| `server.py` | HTTP エントリポイント + ルート定義 |
| `service.py` | パイプラインアダプタ (ライフサイクル + レスポンスフォーマット) |
| `pipeline.py` | コア RAG ロジック |

## Implementation

### Phase 1: 矛盾する doc セクションを読む

```bash
grep -n "server.py\|service.py\|mcp.*rag\|entrypoint" docs/03_rag_{01,03}*.md
```

### Phase 2: 呼び出しパスを追記

```markdown
## MCP サーバー呼び出しパス

MCP クライアント
  → `scripts/mcp/rag_pipeline/server.py` (HTTP ルート)
    → `RagPipelineMCPService.run_pipeline()` (service.py)
      → `RagPipeline.run()` (scripts/rag/pipeline.py)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| 矛盾なし | Manual review | server.py / service.py の役割が一致 |
| コード変更なし | `git diff scripts/` | no changes |
