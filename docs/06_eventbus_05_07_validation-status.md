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
| テスト | `uv run pytest tests/test_eventbus*.py` | すべて成功 |

最終確認日: 2026-06-24

## Related Documents

- `06_eventbus_05_02_bind-address-and-start.md`

## Keywords

event-bus
ci
lint
type-check
tests
verification
