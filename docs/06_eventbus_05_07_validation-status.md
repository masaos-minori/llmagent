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

## Validation Status

The following quality gates are executed in the CI pipeline:

- Lint checks
- Type checks
- Test regressions

Since defects related to the DLQ loop have occurred in the past, regression coverage for health and DLQ-related tests is particularly critical.

## Related Documents

- `06_eventbus_05_02_bind-address-and-start.md`
