# WALバックアップ時のファイルパス検証が不十分

## Summary

DBパスの拡張子が変わってしまうため、WALファイルの存在確認が正しくできない可能性がある。また、allowed_root チェックは WALファイルそのものではなく DBパスに対して行われるため、DBパスが allowed_root 内にあっても WALファイルが別のディレクトリにコピーされる可能性がある。

## Severity

Medium

## Confidence

Medium

## Evidence

- `agent/repl.py:366-367` — `wal_file = f"{db_path}-wal"`、`backup_dir = os.path.dirname(db_path) or "/tmp"`
- WALファイルのパスは DBパスに `-wal` を付加したもの
- DBパスが `/opt/llm/data/session.db` の場合、WALファイルは `/opt/llm/data/session-wal` になる（`.db` の拡張子が消える）
- `shutil.copy2(wal_file, wal_backup_path)` でコピーされるが、`_is_db_path_allowed()` で allowed_root チェックが行われる

## Current behavior

DBパスの拡張子が変わってしまうため、WALファイルの存在確認が正しくできない可能性がある。また、allowed_root チェックは WALファイルそのものではなく DBパスに対して行われるため、DBパスが allowed_root 内にあっても WALファイルが別のディレクトリにコピーされる可能性がある。

## Impact

- WALファイルの存在確認が正しくできない
- allowed_root チェックが WALファイル自体には適用されない
- セキュリティポリシー違反の可能性

## Recommended action

- WALファイルのパスを `f"{db_path}.wal"` に修正する
- WALファイルのバックアップ先ディレクトリにも allowed_root チェックを追加する

## Suggested Tests

- **Test target:** `agent/repl.py::AgentREPL._save_session_diagnostic()`
- **Behavior to verify:** WALファイルのパスが正しい形式で生成され、allowed_root チェックが適用されること
- **Failure mode:** WALファイルのパスが不正な形式になり、バックアップ先に誤ったファイルがコピーされる
