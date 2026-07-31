# MCPサーバー起動処理 — stderrログの無制限肥大

**重大度:** HIGH
**関連ファイル:** `scripts/agent/http_lifecycle.py:81-89`

## 概要

stderrログファイルはアペンドモードで開かれるが、ローテーションやサイズ制限がない。不審なMCPサーバーがディスク容量を埋める可能性がある。

## 詳細

```python
def _open_stderr_log(self, server_key: str) -> IO[bytes]:
    safe_key = re.sub(r"[^A-Za-z0-9_-]", "_", server_key)
    log_dir = Path("/opt/llm/logs/mcp_servers")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{safe_key}.stderr.log"
    fh = log_path.open("ab")
```

ファイルは常にアペンドされ、ローテーションや圧縮の仕組みがない。

## 影響

- ディスク容量の枯渇
- システム全体の障害

## 修正案

1. ファイルサイズの上限を設定し、超過時にローテーション
2. ログローテーションライブラリ（logrotateなど）の使用を検討
3. 起動時のみログを開き、終了時に閉じる（既存の実装と異なるアプローチ）

## 関連ファイル

- `scripts/agent/http_lifecycle.py:81-89`
