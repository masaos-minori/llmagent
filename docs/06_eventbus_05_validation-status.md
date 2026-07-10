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
  - 06_eventbus_05_bind-address-and-start.md
source:
  - 06_eventbus_05_config-env-and-fields.md
---

# Event Bus: Validation Status

## Validation status

Event Bus module CI verification:

| Check | Command | Status |
|---|---|---|
| Lint | `uv run ruff check scripts/eventbus/` | 0 errors |
| Type check | `uv run mypy scripts/eventbus/` | no errors |
| Tests | `uv run pytest tests/test_eventbus*.py` | all pass |

Last verified: 2026-06-24

## Related Documents

- `06_eventbus_05_bind-address-and-start.md`

## Keywords

event-bus
ci
lint
type-check
tests
verification
