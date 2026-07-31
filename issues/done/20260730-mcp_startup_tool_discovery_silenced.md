# MCPサーバー起動処理 — ツール発見失敗の沈黙化（開発モード）

**重大度:** MEDIUM
**関連ファイル:** `scripts/agent/startup.py:293-319`

## 概要

非生産モードでツール発見に失敗した場合、「スキップ」として扱われ、エージェントがゼロのツールで起動する。下流のエラーが混乱を招く。

## 詳細

```python
except Exception as exc:
    msg = f"MCP tool discovery failed - ALL tool calls will fail this session: {exc}"
    if production_mode:
        pipeline.add_fatal(...)
    else:
        pipeline.add_skipped(...)
```

開発モードでは例外がキャッチされ「スキップ」として扱われる。エージェントはツールなしで起動し、LLMがツールを使用しようとしたときに不明なエラーが発生する。

## 影響

- 開発中のトラブルシューティングが困難
- 「ALL tool calls will fail」メッセージは誤解を招く（実際にはツールが存在しない）

## 修正案

1. 開発モードでも致命的なエラーとして扱う
2. メッセージを修正し、ツールが存在しないことを明確にする
3. デバッグログに詳細情報を追加

## 関連ファイル

- `scripts/agent/startup.py:293-319`
