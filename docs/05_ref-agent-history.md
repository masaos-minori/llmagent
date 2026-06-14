# agent/history.py

## 1. 機能概要

`AgentREPL` から抽出した会話履歴管理レイヤー。文字数カウントとトークン数推定、LLM ベースのコンテキスト圧縮を担当。`AgentREPL._init_history_manager()` で生成され `ctx.services.hist_mgr` に保持。

圧縮候補の選択ロジックは独立した `agent.history_selection_policy.HistorySelectionPolicy` クラスに委譲されている (重要度スコアリング + カテゴリ別分類)。

クラス: `HistoryManager`

## 2. コンストラクタ引数

```python
from agent.history import HistoryManager

mgr = HistoryManager(
    http=httpx.AsyncClient(...),        # httpx.AsyncClient — LLM 呼び出しに使用する HTTP クライアント
    llm_url="http://127.0.0.1:8002/v1/chat/completions",  # str — 要約 LLM のエンドポイント URL
    char_limit=8000,                    # int — 圧縮を発動する文字数閾値 (0 = 無効)
    compress_turns=4,                   # int — 1 回の圧縮で対象にする最古のターンペア数
    compress_temperature=0.3,           # float — 要約 LLM に渡す temperature
    compress_max_tokens=300,            # int — 要約 LLM に渡す max_tokens
    on_compress=None,                   # Callable[[int], None] | None — 圧縮成功時に呼ばれるコールバック。引数は圧縮したメッセージ数
    protect_turns=2,                    # int — 最新 N ペア (user+assistant) を圧縮対象外に保護 (デフォルト: 2)
    token_limit=0,                      # int — 圧縮を発動するトークン数閾値 (0 = 無効、char_limit のみ使用)
    tokenize_url="",                    # str — llamacpp /tokenize エンドポイント URL; "" = 無効 (chars // 4 フォールバック)
)
```

## 3. API

### プロパティ

| プロパティ | 型 | 説明 |
|---|---|---|
| `compress_turns` | `int` | 圧縮対象の最古ターンペア数 (`_compress_turns` の公開プロパティ)。外部 (`_cmd_compact` 等) からの読み取り用 |

### 統計属性

| 属性 | 型 | 説明 |
|---|---|---|
| `stat_compress_count` | `int` | セッション通算圧縮実行回数。インスタンス生成時に 0 で初期化 |

### パブリックメソッド

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `count_chars` | `(history: list[LLMMessage]) -> int` | 会話履歴の総文字数を推定する。content 文字列長と tool_calls の JSON シリアライズ長の合計を返す |
| `count_tokens` | `(history: list[LLMMessage], last_input_tokens: int \| None = None) -> int` | トークン数を推定する (同期版)。`last_input_tokens` が非 None のときはその値をそのまま返す (LLM usage の精確値)。None のときは `count_chars(history) // 4` でフォールバック推定。`/context` コマンドなど非同期コンテキスト外からの参照用 |
| `count_tokens_async` | `async (history: list[LLMMessage], last_input_tokens: int \| None = None) -> tuple[int, bool]` | トークン数を非同期で取得し `(count, is_exact)` を返す。優先順位: (1) `last_input_tokens` (LLM usage 精確値、is_exact=True), (2) `tokenize_url` が設定済みのとき `POST /tokenize` 呼び出し (is_exact=True), (3) `chars // 4` フォールバック (is_exact=False)。`compress()` および `Orchestrator._warn_budget()` から呼ばれる |
| `compress` | `async (history: list[LLMMessage]) -> tuple[list[LLMMessage], CompressResult]` | 文字数が `char_limit` を超える (`char_limit > 0` の場合のみ評価)、またはトークン数が `token_limit` を超える (`token_limit > 0` の場合のみ評価) とき、最古のターンを LLM 要約に置換する。選択は委譲先の `HistorySelectionPolicy.select_turns_to_compress()` で行う (重要度スコアリング + カテゴリ別分類)。いずれの閾値も超えていない場合、選択結果が `None` の場合、または LLM が要約を返せなかった場合は `(history, CompressResult(0, 0, False))` を返す。圧縮成功時に `stat_compress_count` をインクリメントし `on_compress(n)` を呼び出す |
| `compress_turns` (property) | — | 圧縮対象の最古ターンペア数 (`_compress_turns` の公開プロパティ)。外部 (`_cmd_compact` 等) からの読み取り用 |
| `apply_config` | `(char_limit?, compress_turns?, token_limit?, tokenize_url?) -> None` | ヒートリロード可能な設定フィールドを更新する。`compress_turns` を更新すると内部の `HistorySelectionPolicy` も再生成される |
| `force_compress` | `async (history: list[LLMMessage]) -> tuple[list[LLMMessage], CompressResult]` | 現在の制限を一時無効化して即時圧縮を実行する。`char_limit=1`, `token_limit=0` に設定してから `compress()` を呼び出し、finally で元に戻す |

### プライベートメソッド

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `_selection_policy.select_turns_to_compress` | `(history: list[LLMMessage]) -> SelectionResult \| None` | 選択ロジックは `agent.history_selection_policy.HistorySelectionPolicy` クラスに委譲。重要度スコアリング (pinned → explicit importance → keyword-based) + カテゴリ別分類 (`temporary`, `temporary_reasoning`, `factual`, `history`) で圧縮対象を決定する |
| `_build_history_text` | `(messages: list[LLMMessage]) -> str` | 圧縮 LLM への入力テキストを `ROLE: content[:300]` 形式の改行区切りで生成する |
| `_call_compress_llm` | `async (history_text: str) -> str \| None` | LLM に 1 段落の要約を要求し文字列を返す。空応答または例外発生時は `None` を返す |
| `_classify` | `@staticmethod (msg: LLMMessage) -> str` | メッセージを圧縮優先度カテゴリに分類する。委譲先の `HistorySelectionPolicy.classify()` へのエイリアス。戻り値は `'temporary'` (tool ロール) / `'temporary_reasoning'` (tool_calls 付き assistant) / `'factual'` (system) / `'history'` (その他) のいずれか |

### CompressResult データクラス

| フィールド | 型 | 説明 |
|---|---|---|
| `compressed_count` | `int` | 要約されたメッセージ数 |
| `protected_count` | `int` | 保護されたメッセージ数 (圧縮対象から除外) |
| `summary_added` | `bool` | 要約メッセージが追加されたかどうか |

## 4. 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent/repl.py` | `_init_history_manager()` で生成し `ctx.services.hist_mgr` に格納。`tokenize_url=ctx.cfg.tokenize_url` を渡す |
| `agent/orchestrator.py` | `_handle_history_compression()` が `compress()` を呼び出す。`_warn_budget()` が `count_tokens_async()` を呼び出す |
| `agent/commands/cmd_context.py` | `count_chars()` / `count_tokens()` でコンテキスト使用量を算出。`/tokenize` 設定状況に応じて表示ラベルを切り替え |
| `agent/commands/cmd_config.py` | `/reload` 時に `_apply_config_params()` が `apply_config()` でホットリロード |
| `agent/commands/cmd_ingest.py` | `_cmd_compact` が `force_compress()` を呼び出して即時圧縮を実行。`compress_turns` はプロパティ経由で読み取り |
| `shared/token_counter.py` | `count_tokens_async()` から呼び出す `get_token_count()` の実装。`/tokenize` HTTP 呼び出しと `chars // 4` フォールバックを提供 |
| `agent/history_selection_policy.py` | `HistorySelectionPolicy` クラス。重要度スコアリング (pinned → explicit importance → policy keyword) + カテゴリ別分類ロジックをカプセル化。`HistoryManager` に委譲される |
