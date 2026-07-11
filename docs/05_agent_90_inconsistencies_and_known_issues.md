---
title: "Agent Inconsistencies and Known Issues"
category: agent
tags:
  - agent
  - inconsistencies
  - known-issues
  - bugs
related:
  - 05_agent_00_document-guide.md
---

# Agent Inconsistencies and Known Issues

このファイルは、agent 層（`agent/`、`shared/`）における既知の不具合、仕様の矛盾、
文書間の不整合、未実装領域、および未解決の疑問点を記録する。

各エントリの形式:
- **Type:** `Document inconsistency` / `Implementation bug` / `Undocumented` / `Needs confirmation` / `Open Question`
- **Impact scope:** 影響を受けるモジュール／動作
- **Statement A / B:** 矛盾する事実（該当する場合）
- **Current safe interpretation:** 不明な場合に前提とすべき内容
- **Recommended action:** 必要な修正または調査
- **Notes for AI reference:** この問題に関する AI 推論のためのガイダンス

---

## 未解決の疑問点

### セッション SQLite 破損復旧のギャップ

- `/db rag recover [backup-path]` は `rag.sqlite` のみを対象とする（`RagMaintenanceService` 経由）
- `/db session recover [backup-path]` が存在する。`DbMaintenanceService.recover_session()` → `recover_corruption(backup_path, target="session")` を呼び出す
- オペレーターの操作: `/db session recover /path/to/backup.sqlite`

---

## 未文書化領域

*（現在追跡中の未文書化領域はない。UNDOC-02「プラグインツールの戻り値の
規約が登録時に強制されていない」は 2026-07-09 に削除された。
`05_agent_11_01_extension-points-plugin-command.md` の §`@register_tool` は現在、
`ToolExecutor.execute()` における実行時の値検証に加えて、登録時の fail-fast な
戻り値アノテーション検証（欠落または誤りの場合に `ValueError`、
`shared/plugin_registry.py::register_tool()` で確認済み）を文書化している。
両方の層が強制されかつ文書化されており、このエントリが追跡していたギャップはもはや
存在しない。）*

---

## Related Documents

- `05_agent_00_document-guide.md`

## Keywords

agent
inconsistencies
known-issues
bugs
