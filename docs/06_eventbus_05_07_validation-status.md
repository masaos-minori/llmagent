---
title: "Event Bus: Validation Status"
category: eventbus
tags:
  - event-bus
  - ci
  - lint
  - type-check
  - tests
  - verification
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_05_02_bind-address-and-start.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: Validation Status

## 検証状況

Event Bus モジュールの CI 検証結果:

| チェック | コマンド | 状態 |
|---|---|---|
| Lint | `uv run ruff check scripts/eventbus/` | エラー0件 |
| 型チェック | `uv run mypy scripts/eventbus/` | エラーなし |
| テスト | `uv run pytest tests/test_eventbus*.py` | 148 passed |

最終確認日: 2026-07-13

**修正履歴:** 2026-07-13、`_dlq_loop()`(`scripts/eventbus/app.py`)が `route_helpers` の app 引数版ヘルパー(`get_config`/`get_db`)をダミーの `Req` ラッパー越しに呼び出しており毎ティッククラッシュしていた不具合を修正(`get_config(app)`/`get_db(app)` に変更)。修正前は `test_health_ok` 系5件が FAIL、97件が ERROR になっていた。詳細は [06_eventbus_90_inconsistencies_and_known_issues.md](06_eventbus_90_inconsistencies_and_known_issues.md) を参照。

## Related Documents

- `06_eventbus_05_02_bind-address-and-start.md`

## Keywords

event-bus
ci
lint
type-check
tests
verification
