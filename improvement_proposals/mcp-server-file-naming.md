# 改善要望書: MCPサーバー固有の名前によるファイル名重複の解消

## 1. 背景・課題

`scripts/mcp_servers/`以下の各サブディレクトリに、以下のファイル名が重複している。

| ファイル名 | 重複数 | 含まれるディレクトリ |
|-----------|--------|---------------------|
| `__init__.py` | 9 | browser, cicd, file, git, github, mdq, rag_pipeline, shell, web_search |
| `models.py` | 9 | browser, cicd, file, git, github, mdq, rag_pipeline, shell, web_search |
| `server.py` | 9 | browser, cicd, file, git, github, mdq, rag_pipeline, shell, web_search |
| `service.py` | 8 | browser, cicd, file, git, github, mdq, rag_pipeline, shell |
| `tools.py` | 9 | browser, cicd, file, git, github, mdq, rag_pipeline, shell, web_search |

**問題点:**
- 同一モジュールパスでのインポートが曖昧になる（例: `import mcp_servers.github.models`）
- IDEのコードナビゲーションが混乱する（ジャンプ先が複数存在）
- リファクタリング時に誤ったファイルを変更するリスクがある
- モジュール探索時の競合が発生する可能性

## 2. 目標

各MCPサーバーのファイル名を一意にし、IDEや開発者の混乱を防ぐ。

## 3. 改善案: サーバー固有の名前付け

### 3.1 変更対象ファイル一覧

#### browser/
| 変更前 | 変更後 |
|-------|--------|
| `browser/models.py` | `browser/browser_models.py` |
| `browser/server.py` | `browser/browser_server.py` |
| `browser/service.py` | `browser/browser_service.py` |
| `browser/tools.py` | `browser/browser_tools.py` |

#### cicd/
| 変更前 | 変更後 |
|-------|--------|
| `cicd/models.py` | `cicd/cicd_models.py` |
| `cicd/server.py` | `cicd/cicd_server.py` |
| `cicd/service.py` | `cicd/cicd_service.py` |
| `cicd/tools.py` | `cicd/cicd_tools.py` |

#### file/
| 変更前 | 変更後 |
|-------|--------|
| `file/models.py` | `file/file_models.py` |
| `file/server.py` | `file/file_server.py` |
| `file/service.py` | `file/file_service.py` |
| `file/tools.py` | `file/file_tools.py` |

#### git/
| 変更前 | 変更後 |
|-------|--------|
| `git/models.py` | `git/git_models.py` |
| `git/server.py` | `git/git_server.py` |
| `git/service.py` | `git/git_service.py` |
| `git/tools.py` | `git/git_tools.py` |

#### github/
| 変更前 | 変更後 |
|-------|--------|
| `github/models.py` | `github/github_models.py` |
| `github/server.py` | `github/github_server.py` |
| `github/service.py` | `github/github_service.py` |
| `github/tools.py` | `github/github_tools.py` |

#### mdq/
| 変更前 | 変更後 |
|-------|--------|
| `mdq/models.py` | `mdq/mdq_models.py` |
| `mdq/server.py` | `mdq/mdq_server.py` |
| `mdq/service.py` | `mdq/mdq_service.py` |
| `mdq/tools.py` | `mdq/mdq_tools.py` |

#### rag_pipeline/
| 変更前 | 変更後 |
|-------|--------|
| `rag_pipeline/models.py` | `rag_pipeline/rag_pipeline_models.py` |
| `rag_pipeline/server.py` | `rag_pipeline/rag_pipeline_server.py` |
| `rag_pipeline/service.py` | `rag_pipeline/rag_pipeline_service.py` |
| `rag_pipeline/tools.py` | `rag_pipeline/rag_pipeline_tools.py` |

#### shell/
| 変更前 | 変更後 |
|-------|--------|
| `shell/models.py` | `shell/shell_models.py` |
| `shell/server.py` | `shell/shell_server.py` |
| `shell/service.py` | `shell/shell_service.py` |
| `shell/tools.py` | `shell/shell_tools.py` |

#### web_search/
| 変更前 | 変更後 |
|-------|--------|
| `web_search/models.py` | `web_search/web_search_models.py` |
| `web_search/server.py` | `web_search/web_search_server.py` |
| `web_search/service.py` | `web_search/web_search_service.py` |
| `web_search/tools.py` | `web_search/web_search_tools.py` |

### 3.2 インポート側の修正例

**変更前:**
```python
from mcp_servers.github.models import GitHubConfig, CreateOrUpdateFileRequest
from mcp_servers.github.server import app
from mcp_servers.github.service import build_service
from mcp_servers.github.tools import TOOL_LIST
```

**変更後:**
```python
from mcp_servers.github.github_models import GitHubConfig, CreateOrUpdateFileRequest
from mcp_servers.github.github_server import app
from mcp_servers.github.github_service import build_service
from mcp_servers.github.github_tools import TOOL_LIST
```

### 3.3 影響範囲

インポート文の修正が必要なファイル数: **172行**

**scripts/側:**
- `scripts/mcp_servers/*/server.py` — 各サーバーのエントリーポイント
- `scripts/mcp_servers/*/service*.py` — サービス層
- `scripts/mcp_servers/*/format_output.py`, `mapper.py` など — サブモジュール
- `scripts/agent/security_audit_config.py` — セキュリティ監査設定

**tests/側:**
- `tests/test_github_mcp_service.py`
- `tests/test_cicd_mcp_service.py`
- `tests/test_shell_mcp_service.py`
- `tests/test_browser_mcp_service.py`
- `tests/test_mdq_*.py` (10ファイル以上)
- `tests/test_rag_pipeline_mcp_service.py`
- `tests/test_tool_server_layer_consistency.py`
- `tests/test_mcp_server_health_status.py`
- `tests/test_call_tool_validation.py`
- `tests/test_github_config_consistency.py`
- `tests/test_github_tool_registry.py`
- `tests/test_tools_endpoint.py`
- その他多数

## 4. 実施手順

### フェーズ1: ファイルのリネーム
```bash
# browser/
mv scripts/mcp_servers/browser/models.py scripts/mcp_servers/browser/browser_models.py
mv scripts/mcp_servers/browser/server.py scripts/mcp_servers/browser/browser_server.py
mv scripts/mcp_servers/browser/service.py scripts/mcp_servers/browser/browser_service.py
mv scripts/mcp_servers/browser/tools.py scripts/mcp_servers/browser/browser_tools.py

# 同様に全ディレクトリで実行
```

### フェーズ2: インポート文の一括置換
```bash
# Pythonのsed相当ツールを使用（例: ripgrep + sed）
rg -l "from mcp_servers\.(github|git|shell|browser|cicd|mdq|rag_pipeline|web_search)\.(models|server|service|tools) import" \
   --files-with-matches scripts/ tests/ | xargs sed -i 's/from mcp_servers\.\(github\)\.models import/from mcp_servers.\1.github_models import/g'
```

### フェーズ3: テストの実行と修正
```bash
uv run pytest tests/ -x -v
```

### フェーズ4: mypyの型チェック
```bash
uv run mypy scripts/ tests/
```

## 5. リスクと対策

| リスク | 対策 |
|-------|------|
| インポート文の漏れ | rgで全インポートを検索し、手動で確認 |
| __init__.pyの再エクスポート | `__init__.py`内の`from .models import ...`も修正が必要か確認 |
| mypyの型エラー追加発生 | mypyを実行し、型エラーがあれば対応 |
| pre-commitフックの失敗 | mypy以外のフック（ruff等）も確認 |
| ドキュメントの更新漏れ | 関連ドキュメントを確認し、必要に応じて更新 |

## 6. 期待される効果

- 各MCPサーバーのファイル名が一意になり、IDEのコードナビゲーションが明確化
- モジュール探索時の競合が解消
- リファクタリング時の誤変更リスクが低減
- コードベースの可読性が向上
