# scripts/**/*.py 改善案

調査日: 2026-06-07  
調査対象: `scripts/` 配下の Python ファイル全163ファイル  
ベースライン: ruff クリーン、mypy 0 エラー、lint-imports 0 違反、テスト 990 合格

---
## 1. 廃止スタブの削除（最優先）

プロダクションコードから一切参照されていないファイル。`spec_agent.md` 13章にも削除対象として記載済み。

| ファイル | 問題 | 対処 |
|---|---|---|
| `scripts/agent/repl_debug.py` | 参照元ゼロ。カバレッジ 0%。 | 削除 |
| `scripts/agent/rag_debug.py` | 参照元ゼロ。カバレッジ 0%。 | 削除 |
| `scripts/agent/context_detection.py` | 参照元ゼロ。カバレッジ 0%。日本語文字列リテラルあり。 | 削除または使用箇所に再統合 |
| `scripts/agent/memory/scoring.py` | 参照元ゼロ。カバレッジ 0%。`ScoringPolicy` が `MemoryRetriever` から未参照。 | 削除または `MemoryRetriever` に統合 |

削除時は `deploy/deploy.sh` の `cp` 行も同時に削除すること（`File Split Rule` 参照）。

---
## 2. テストカバレッジの向上（Phase 2 gate 解除に必要）

以下のファイルはカバレッジが 80% 未満のため、リファクタリングの Phase 2 gate（coverage ≥ 80%）を満たせない。characterization tests を追加することで gate を解除し、次のリファクタリングを可能にする。

### 2-A. コマンドミックスイン（最高優先度）

`cmd_session.py` の `_cmd_session` は複雑度 C=16 でプロジェクト最高値だが、カバレッジが 11% で手が出せない状態。

| ファイル | カバレッジ | 未カバー行 | 対処 |
|---|---|---|---|
| `agent/commands/cmd_session.py` | 11% | 83-110, 122-132 | characterization tests 追加 → `_cmd_session` リファクタリング |
| `agent/commands/cmd_memory.py` | 41% | 61-138, 140-211 | characterization tests 追加 → `_memory_list` リファクタリング |
| `agent/commands/cmd_config.py` | 77% | 90-97, 154-215 | 残り 3% 補完 → `_print_config_values` 整理 |
| `agent/commands/cmd_notes.py` | 15% | 17-66 (ほぼ全体) | characterization tests 追加 |
| `agent/commands/cmd_db.py` | 16% | 40-203 (ほぼ全体) | characterization tests 追加 |
| `agent/commands/cmd_context.py` | 53% | 39-173 | characterization tests 追加 |

テスト作成方法: `tests/conftest.py` の `_make_ctx()` ヘルパーを使い、モック `AgentContext` で各スラッシュコマンドを呼び出す。

### 2-B. RAG ステージ（新規実装のテスト不足）

`rag/stages/` は今ブランチで追加された新実装だが、ユニットテストが薄い。

| ファイル | カバレッジ | 未カバー主要ロジック |
|---|---|---|
| `rag/stages/search.py` | 30% | `run()` の全ロジック（embedding → KNN 検索） |
| `rag/stages/rerank.py` | 35% | `run()` の全ロジック（クロスエンコーダー再ランク） |
| `rag/stages/mqe.py` | 38% | `run()` の全ロジック（マルチクエリ拡張） |
| `rag/stages/fusion.py` | 62% | RRF マージのエッジケース |
| `rag/stages/augment.py` | 57% | `run()` の一部 |

`rag/stages/` 全体をカバーする `tests/test_rag_stages.py` を新規作成する。各ステージの `run()` を `PipelineContext` モックで単体テストする。

### 2-C. その他の低カバレッジファイル

| ファイル | カバレッジ | 優先度 | 備考 |
|---|---|---|---|
| `agent/tool_scheduler.py` | 15% | 中 | `build_execution_groups()` が未テスト |
| `shared/formatters.py` | 26% | 中 | テキスト整形関数が未テスト |
| `shared/git_helper.py` | 33% | 中 | `get_repo_info()` が未テスト |
| `mcp/dispatch.py` | 68% | 低 | エラーパスが未テスト |
| `agent/memory/jsonl_store.py` | 79% | 低 | 並行書き込みテストが通過済みのため残りは軽微 |

---
## 3. Grade C 以上の複雑関数リファクタリング（カバレッジ確保後）

カバレッジが確保された後に実施する。

| 関数 | 複雑度 | カバレッジ | リファクタリング案 |
|---|---|---|---|
| `cmd_session._cmd_session` | C=16 | 11% ❌ | サブコマンドを `_session_list/load/rename/delete` に分割し、`_cmd_session` をディスパッチャのみにする |
| `config.DbConfig` | C=13 | 82% ✅ | `__post_init__` のパスチェック (`Path.exists()`) を `_validate_paths()` として抽出する |
| `config.DbConfig.__post_init__` | C=12 | 82% ✅ | 上記と同様 |
| `config.LLMConfig.__post_init__` | C=11 | 82% ✅ | バリデーションブランチを `_validate_llm_config()` にグループ化する |
| `history._select_turns_to_compress` | C=11 | 94% ✅ | D=22 から改善済み。これ以上の分割は benefit が薄い |
| `cmd_memory._memory_list` | C=11 | 41% ❌ | カバレッジ確保後にサブロジックを抽出 |
| `llm_client._stream_once` | C=11 | 85% ✅ | SSE 例外ハンドラ 4 本は本質的な複雑度。変更リスクが高いためスキップ推奨 |

---
## 4. 型注釈の改善

### 4-A. logging で f-string を使用している箇所（175 件）

`logging` の f-string 使用はログレベルチェック前に文字列構築が発生し、パフォーマンスロスになる（ただし本プロジェクトでは実害は軽微）。

```python
# 現在（175 件）
logger.info(f"Tool call (turn {turn}): {name}({masked})")

# 推奨
logger.info("Tool call (turn %d): %s(%s)", turn, name, masked)
```

対象ファイル: `scripts/` 配下の全ファイル。`rg 'logger\.(info|debug|warning|error)\(f"' scripts/` で一覧取得可能。
一括変換は `libcst` または正規表現置換で実施できるが、変換後に `mypy`・`ruff` の確認が必要。優先度は**低**。

### 4-B. `rag/stages/` の型注釈不足

```python
# 現在 (search.py 例)
class SearchStage:
    def __init__(self, cfg, http) -> None:

# 推奨
class SearchStage:
    def __init__(self, cfg: RagConfig, http: httpx.AsyncClient) -> None:
```

`rag/stages/search.py`, `mqe.py`, `rerank.py`, `fusion.py`, `augment.py` の `__init__` シグネチャに型注釈がない。`mypy` が `Any` として扱っており、型チェックの恩恵を受けられない。

### 4-C. `assert isinstance()` の使用

`rag/stages/search.py:30` に `assert isinstance(result, list)` がある。`coding.md` の「Do not use `Any`, unnecessary casts, or unsafe assertions.」に抵触。以下に修正:

```python
# 現在
assert isinstance(result, list)

# 推奨
if not isinstance(result, list):
    logger.warning("Unexpected embedding result type: %s", type(result).__name__)
    continue
```

---
## 5. rag/stages/ の設計改善

`rag/stages/` の各 `run()` メソッドのシグネチャが統一されていない。

```python
# search.py
async def run(self, ctx: PipelineContext, db=None, **kwargs) -> None:

# mqe.py — シグネチャを確認
```

`PipelineStage` プロトコル (`rag/stage.py`) で定義された `run(ctx: PipelineContext) -> PipelineContext` に準拠するよう統一する必要がある。現在の `db=None, **kwargs` は `PipelineContext` にフィールドとして含めるべき。

---
## 6. 内部実装の整合性

### 6-A. `agent/commands/cmd_session.py` の内部インポート残存

`cmd_session.py` にはコマンドハンドラ層から `agent.config` への `from agent.config import _CONFIG_DIR` の遅延インポートがある（282行目の `_cmd_config` 内）。これはプライベートシンボルへの依存であり、設計上望ましくない。
推奨: `AgentConfig` に `config_dir: Path` を公開プロパティとして追加し、プライベートシンボルへの直接参照をなくす。

### 6-B. `mcp/dispatch.py` のエラーハンドリング

`mcp/dispatch.py:23-26` がカバーされておらず、HTTP エラー処理パスのテストがない。FastAPI の `HTTPException` を想定したエラーパスを単体テストで確認する。

---
## 7. 改善点

### 7-A. テストの安定性
- `TestSearchStage::test_run_success` テストが失敗し、全体のテスト実行がタイムアウトしている
- 非同期処理に関連するモック設定不備により、期待される結果が返らない
- 原因: テストで使用されている `get_embedding` のモックが正しく設定されていない

### 7-B. 非同期処理の管理
- 373の非同期関数が存在し、await式も363個使用されている
- テストコードで非同期処理が適切に扱われていない部分がある

### 7-C. コード品質と保守性
- 大量の非同期コードが存在するが、テストコードでの管理方法が一貫していない

### 7-D. テスト環境の最適化
- 全テスト実行がタイムアウトしている
- タイムアウト設定の見直しが必要

### 7-E. ドキュメントと設計
- 計画書が多数存在するが、実装と対応が完全に一致していない可能性がある

---
## 8. 実施順序の推奨

```
Phase 1（1-2時間）: 廃止スタブの削除（Section 1）
Phase 2（2-3時間）: rag/stages/ の characterization tests 追加（Section 2-B）
Phase 3（3-4時間）: コマンドミックスインの characterization tests 追加（Section 2-A）
Phase 4（1-2時間）: Grade C 以上のリファクタリング（Section 3、カバレッジ確保後）
Phase 5（1時間）:   型注釈の追加（Section 4-B, 4-C）
Phase 6（任意）:    logging f-string の一括変換（Section 4-A）
```

各 Phase は独立してコミット可能。Phase 2-3 は `python-test-and-fix` スキルを使用。