---
title: "Event Bus: Validation Status"
area: eventbus
tags:
  - event-bus
  - ci
  - lint
  - type-check
  - tests
  - verification
related:
  - eventbus_00_document-guide.md
  - eventbus_01_system-overview.md
  - eventbus_09_configuration-and-operations.md
source:
  - eventbus_09_configuration-and-operations.md
---

# Event Bus: Validation Status

## Validation Status

The following quality gates are executed in the CI pipeline:

- Lint checks
- Type checks
- Test regressions

Since defects related to the DLQ loop have occurred in the past, regression coverage for health and DLQ-related tests is particularly critical.

## Related Documents

- `eventbus_09_configuration-and-operations.md`
