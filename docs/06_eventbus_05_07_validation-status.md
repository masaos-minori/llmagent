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

CIパイプラインで以下の品質ゲートが実行されている：

- リントチェック
- 型チェック
- テストレグレッション

DLQループ関連の欠陥が過去に発生しているため、ヘルス/DLQ関連テストの回帰カバレッジは特に重要である。

## Related Documents

- `06_eventbus_05_02_bind-address-and-start.md`
