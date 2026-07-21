# Issue: mcp_tool_discovery.py - Duplicate tool exclusion only produces WARNING in LOCAL mode

## 概要

複数のMCPサーバーから同じツール名が報告された場合、ツールはレジストリから除外される。LOCALモードではこの事象はWARNINGとして記録されるが、REPL上で警告が表示されない可能性があり、運用者がツールが利用不可になる原因に気づかない。

## 該当コード

`scripts/agent/services/mcp_tool_discovery.py:298-309`

```python
server_keys = sorted({server_key for server_key, _, _ in group})
if len(server_keys) > 1:
    status = (
        StartupCheckStatus.FATAL if is_fatal else StartupCheckStatus.WARNING
    )
    msg = (
        f"duplicate tool name {name!r} reported by multiple servers: "
        f"{', '.join(server_keys)} — excluded from registry"
    )
    findings.append(
        StartupCheckOutcome(source=_SOURCE, status=status, message=msg)
    )
    continue
```

`startup.py:291-297` の表示ロジック:

```python
for outcome in pipeline.outcomes:
    if outcome.status == StartupCheckStatus.WARNING:
        self._view.write_warning(f"{OutputTag.NON_FATAL} {outcome.message}")
    elif outcome.status == StartupCheckStatus.FATAL:
        self._view.write_warning(f"{OutputTag.FATAL} {outcome.message}")
```

## 問題点

- LOCALモードでは `is_fatal = False` なので、重複ツールはWARNINGとして記録される
- WARNINGは `write_warning()` で表示されるが、起動バナーの一部として大量の警告が表示される場合、見逃される可能性
- ツールの除外は「静かな」操作であり、REPL上でツールが見つからないとエラーが出ても、その原因が重複ツールであることは明白ではない
- FATALモードでも `write_warning()` で表示される（FATALなのにWARNING表示）

## 改善案

- 重複ツールの除外は重要な事象なので、LOCALモードでもFATALとして扱う
- または、FATAL/WARNINGに関わらず、REPL上に明確な通知を表示
- FATALの場合は `write_fatal()` を使用して視覚的に区別

## 優先度

中 - ツールの欠落原因が不明瞭になり、トラブルシューティングが困難になる
