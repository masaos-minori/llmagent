# Web 検索 MCP サーバ (web-search-mcp)

## 1. Web 検索機能 (web-search-mcp)

### 1.1 機能概要

RAG の検索結果に加えて Web 検索結果をコンテキストに追加して回答を生成する。ローカル DB に存在しない最新情報や未収録ドキュメントへの補完に利用する。

Web 検索は `mcp/web_search/server.py` として独立した MCP (Model Context Protocol: Anthropic が策定した LLM とツールを接続するプロトコル) 互換サーバ (ポート 8004) で動作する。`agent.py` は `/v1/call_tool` 統合エンドポイントを呼び出すだけで、検索バックエンドへの依存は `mcp/web_search/server.py` に閉じている。

```
agent.py REPL で質問を入力すると、LLM がツール呼び出しを判断して mcp/web_search/server.py の search_web ツールを実行する:
  agent[chat]> (質問を入力)
    ├─ RAG パイプライン (KNN + BM25 → RRF → Rerank)
    └─ LLM が search_web ツールを選択 → POST :8004/v1/call_tool → 検索プロバイダ (上位 5 件)
```

#### 1.1.1 マルチプロバイダ対応 (Brave / Bing / DuckDuckGo)

`mcp/web_search/server.py` は複数の検索プロバイダに対応し、フォールバック機能を備える。プロバイダの優先順位は `config/web_search_mcp_server.toml` の `search_providers` で設定する。

| プロバイダ | API キー | 無料枠 | フォールバック順位 |
|---|---|---|---|
| Brave Search | `BRAVE_API_KEY` (必須) | 2000 req/月 | 1 番目 |
| Bing Web Search | `BING_API_KEY` (任意) | Azure の料金体系に従う | 2 番目 |
| DuckDuckGo | 不要 | 制限なし (非公式) | 3 番目 |

先頭プロバイダが失敗またはゼロ件のとき、自動的に次のプロバイダに切り替わる。API キーが未設定のプロバイダは自動スキップ。全プロバイダが失敗した場合は HTTP 502 を返す。Bing は `mkt=ja-JP` で日本語ロケールを指定。DuckDuckGo は同期ライブラリのため `asyncio.to_thread` でスレッドプール実行。

### 1.2 サービス構成ファイル

| ファイル | 配置先 | 説明 |
|---|---|---|
| `scripts/mcp/web_search/server.py` | `/opt/llm/scripts/mcp/web_search/server.py` | FastAPI + マルチプロバイダ検索サーバ本体 |
| `config/web_search_mcp_server.toml` | `/opt/llm/config/web_search_mcp_server.toml` | プロバイダ優先順位・URL・タイムアウト設定 |
| `init.d/web-search-mcp` | `/etc/init.d/web-search-mcp` | OpenRC 起動スクリプト |
| `conf.d/web-search-mcp` | `/etc/conf.d/web-search-mcp` | API キー設定ファイル |

### 1.3 インストール

```bash
# 1. ライブラリをインストールする (DuckDuckGo プロバイダに必要)
source /opt/llm/venv/bin/activate
pip install "duckduckgo-search>=6.0.0"

# 2. API キーを取得して設定ファイルに記入する
#    [Brave] https://brave.com/search/api/ → 無料枠 2000 req/月
#    [Bing]  https://www.microsoft.com/en-us/bing/apis/bing-web-search-api → Azure Cognitive Services
#    ※ DuckDuckGo は API キー不要 (フォールバック用として自動で使用される)
cp conf.d/web-search-mcp /etc/conf.d/web-search-mcp
vi /etc/conf.d/web-search-mcp
# 取得した API キーを設定する:
#   BRAVE_API_KEY="<Brave API キー>"
#   BING_API_KEY="<Bing API キー>"  # 任意

# 3. スクリプトと設定ファイルを配置する
cp scripts/mcp/web_search/server.py /opt/llm/scripts/
cp config/web_search_mcp_server.toml /opt/llm/config/

# 4. OpenRC スクリプトを配置して有効化する
cp init.d/web-search-mcp /etc/init.d/web-search-mcp
chmod +x /etc/init.d/web-search-mcp
rc-update add web-search-mcp default

# 5. サービスを起動する
rc-service web-search-mcp start

# 6. 動作確認
curl -s http://127.0.0.1:8004/health
# → {"status":"ok","providers":["brave","bing","duckduckgo"],"brave_key":"set","bing_key":"not_set"}
#    brave_key / bing_key が "not_set" の場合は /etc/conf.d/web-search-mcp を確認する

curl -s -X POST http://127.0.0.1:8004/search \
  -H "Content-Type: application/json" \
  -d '{"query": "llama.cpp latest release", "max_results": 3}' \
  | python3 -m json.tool
# → {"query":"...","results":[...],"provider":"brave"}  ← provider フィールドで使用されたプロバイダを確認できる
```

### 1.4 使用方法

```bash
# agent.py REPL 経由での利用 (LLM が自律的に search_web ツールを選択する)
source /opt/llm/venv/bin/activate
python /opt/llm/scripts/agent.py
# agent[chat]> llama.cpp の最新バージョンを調べてください
# → LLM が search_web ツールを選択して実行する

# HTTP API 直接呼び出し
curl -s -X POST http://127.0.0.1:8004/search \
  -H "Content-Type: application/json" \
  -d '{"query": "gemma 4 の最新リリース情報", "max_results": 3}' \
  | python3 -m json.tool
```

### 1.5 設定項目

| パラメータ | 設定ファイル | デフォルト | 説明 |
|---|---|---|---|
| `web_search_url` | `config/agent.toml` | `http://127.0.0.1:8004` | web-search-mcp サーバのベース URL |
| `web_search_max_results` | `config/agent.toml` | 5 | Web 検索で取得する上位件数 |
| `search_providers` | `config/web_search_mcp_server.toml` | `["brave","bing","duckduckgo"]` | プロバイダの優先順位リスト |
| `default_max_results` | `config/web_search_mcp_server.toml` | 5 | リクエストで `max_results` 省略時のデフォルト件数 |
| `max_results_limit` | `config/web_search_mcp_server.toml` | 20 | サーバ側の件数上限 (負荷抑制) |

### 1.6 実装方式

| 機能 | 実装 |
|---|---|
| フレームワーク | FastAPI + Uvicorn (ポート 8004) |
| 起動モード | HTTP モード (ポート 8004、OpenRC サービス `web-search-mcp`) |
| Brave/Bing 検索 | `httpx.AsyncClient` で非同期 HTTP リクエスト |
| DuckDuckGo 検索 | `DDGS` (同期ライブラリ) を `asyncio.to_thread` でスレッドプール実行 |
| 設定読み込み | `config/web_search_mcp_server.toml` から起動時に一括読み込み |
| API キー取得 | `/etc/conf.d/web-search-mcp` で設定した環境変数 (`BRAVE_API_KEY`, `BING_API_KEY`) から取得 |

### 1.7 入出力インタフェース

**HTTP API**

| エンドポイント | リクエスト | レスポンス |
|---|---|---|
| `POST /search` | `{query: str, max_results?: int}` | `{query, results: [{title, url, body, provider}], provider}` |
| `POST /v1/call_tool` | `{name: str, args: dict}` | `{result: str, is_error: bool}` |
| `GET /v1/tools` | なし | `{tools: [{name, description}]}` |
| `GET /health` | なし | `{status, providers, brave_key, bing_key}` |

**MCP ツール (tools/call)**

| ツール名 | 引数 | 戻り値 |
|---|---|---|
| `search_web` | `{query: str, max_results?: int}` | ヘッダ行 `[Search: N results via <provider>]` + 各件 `[n] タイトル\nURL: url\nProvider: provider\nスニペット(最大400文字)` 形式のテキスト |

### 1.8 エラーハンドリング

| ケース | 対処 |
|---|---|
| プロバイダ失敗またはゼロ件 | 次プロバイダへ自動フォールバック |
| API キー未設定 | モジュールロード時に `WARNING` ログを出力し、該当プロバイダを自動スキップ |
| 全プロバイダ失敗 | HTTP 502 + 最後のエラー詳細を返す |
| 未知プロバイダ設定 | `WARNING` ログでスキップ |

### 1.9 ログ出力

- **ファイル:** `/opt/llm/logs/web-search-mcp.log` + 標準エラー出力
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | 検索件数・使用プロバイダ |
| `WARNING` | プロバイダ失敗、ゼロ件フォールバック、API キー未設定 |

### 1.10 クラス API

`WebSearchMCPServer` は `MCPServer` を継承し、HTTP モード起動ロジックを提供する。`MCPServer` 共通 API は `docs/06_ref-mcp.md` §2 を参照。

```python
from mcp.web_search.server import WebSearchMCPServer

WebSearchMCPServer().run_http()
```

| クラス属性 | 値 | 説明 |
|---|---|---|
| `server_name` | `"web-search-mcp"` | MCP `initialize` レスポンスのサーバ識別名 |
| `server_version` | `"3.0.0"` | バージョン文字列 |
| `http_port` | `8004` | HTTP モード待受ポート |
| `app_module` | `"web_search_mcp_server:app"` | uvicorn 起動ターゲット |
| `mcp_tools` | `_MCP_TOOLS` | `tools/list` に返すツール定義 (`search_web` 1 種) |

| メソッド | 説明 |
|---|---|
| `dispatch(name, args) -> tuple[str, bool]` | `_dispatch_web_tool(name, args)` に委譲する。`search_web` を処理し、`(result_text, is_error)` を返す |
| `run() -> None` | HTTP サーバを起動する (継承) |

**HTTP エンドポイント `POST /v1/call_tool`**

```json
// リクエスト
{"name": "search_web", "args": {"query": "llama.cpp latest release", "max_results": 3}}

// レスポンス
{"result": "[Search: 3 results via brave]\n\n[1] llama.cpp b5210 released\nURL: https://github.com/.../releases/tag/b5210\nProvider: brave\nllama.cpp b5210 adds Metal GPU support...\n\n[2] ...", "is_error": false}
```

