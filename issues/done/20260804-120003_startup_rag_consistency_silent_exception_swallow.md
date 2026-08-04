# 起動処理: RAG整合性チェックの例外が握りつぶされログにも残らない

## 優先度
Medium

## 概要
`StartupOrchestrator._check_services()`（`scripts/agent/startup.py`）内のRAG整合性チェックが `except Exception:` で例外を捕捉しているが、他のチェック項目とは異なり例外内容を一切ログ出力せず、`pipeline.add_skipped("rag_consistency", "RAG consistency check skipped")` という固定文言だけを記録する。実際に何が失敗したのか（DB破損、権限エラー、想定外のバグなど）が起動ログから完全に失われる。

## 変更理由
`scripts/agent/startup.py` の `_check_services()` 内、RAG整合性チェック部分は次の通り（358-359行目付近）。

```python
try:
    rag_check = RagMaintenanceService().consistency()
    if rag_check.is_consistent:
        pipeline.add_ok("rag_consistency")
    else:
        for issue in rag_check.issues:
            pipeline.add_warning(
                "rag_consistency", f"[RAG] Consistency issue: {issue}"
            )
except Exception:  # noqa: BLE001
    pipeline.add_skipped("rag_consistency", "RAG consistency check skipped")
```

同じ `_check_services()` メソッド内の他のすべての `except` ブロック（security_audit, readiness, mcp_tool_discovery, routing_drift, routing_safety_tiers）は、例外を捕捉した際に必ず `logger.error(...)` または `logger.warning(...)` で実際の例外内容を記録している。例えば readiness チェックは次のようになっている。

```python
except Exception as exc:  # noqa: BLE001
    pipeline.add_fatal("readiness", f"Readiness check failed: {exc}")
```

（このケースも `pipeline.add_fatal` の呼び出し自体はメッセージに `exc` を含めており、後段の `_display_pipeline_results()` や `logger.error("FATAL pipeline outcomes: %s", ...)` を通じて記録される。）

一方 RAG整合性チェックの `except Exception:` は例外オブジェクトを変数にすら束縛しておらず（`except Exception:`）、`logger` を一切呼び出していない。`rules/coding.md` §Suppression governance および本レビューで使用した `python-code-review` スキルの Phase 5 が明示的に禁止する「握りつぶされたエラー（swallowed errors）」に該当する。DB破損やスキーマ不整合など、本来オペレーターに通知されるべき重大な問題が発生していても、起動ログには "RAG consistency check skipped" としか残らず、原因調査が事実上不可能になる。

## 実装方針
`except Exception as exc:` に変更し、`logger.warning("RAG consistency check failed: %s", exc)`（あるいは深刻度に応じて `logger.error`）を追加した上で、`pipeline.add_skipped()` のメッセージにも `exc` の内容を含める。

## 対象ファイル
- `scripts/agent/startup.py`（`StartupOrchestrator._check_services()` のRAG整合性チェック部分）

## 必要な変更
- 例外を変数に束縛し、ログへ実際のエラー内容を出力するよう修正する。
- 可能であれば `pipeline.add_skipped()` のメッセージ文字列にも簡潔な原因を含める。

## 受け入れ基準
- `RagMaintenanceService().consistency()` が例外を送出するケースを模擬し、起動ログ（`/opt/llm/logs/agent.log`）に例外の詳細（例外クラス名・メッセージ）が記録されることを確認する。

## テスト方針
- `RagMaintenanceService.consistency` をモックして例外を送出させ、`logger.warning`（もしくは同等のロガー呼び出し）が実際に呼ばれることを検証する単体テストを追加する。

## ドキュメントへの影響
特になし。

## 対象外
`RagMaintenanceService.consistency()` 自体の実装（例外を送出する条件など）は本Issueの対象外。あくまで起動シーケンス側での例外の扱いが対象。

## AI実装時の制約
- 例外の種類を絞り込みすぎず（`Exception` の広い捕捉自体は起動フローを止めないための意図的な設計と考えられるため維持してよい）、ログ出力の追加のみに変更範囲を限定すること。
- `# noqa: BLE001` の抑制コメントを残す場合は、`rules/coding.md` の抑制ガバナンス規約に従い、なぜ広い `except Exception` が必要かを示す説明コメントを付すこと。
