# Event Bus: Document Guide

## Purpose

These documents describe the `scripts/eventbus/` implementation. Use them when implementing, debugging, or extending Event Bus features.

## Reading order

| File | When to read |
|---|---|
| `06_eventbus_01_system-overview.md` | Starting point: architecture, capabilities, security model |
| `06_eventbus_02_http_api_and_runtime.md` | Endpoint spec, request/response formats, failure behavior |
| `06_eventbus_03_persistence_schema_and_replay.md` | SQLite schema, WAL, JSONL archive, replay semantics |
| `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` | DLQ promotion, consumer offsets, at-least-once guarantees |
| `06_eventbus_05_configuration_deploy_and_operations.md` | Config fields, env vars, deployment, validation status |
| `06_eventbus_06_reference_api.md` | Module-level API reference (functions, types) |
| `06_eventbus_90_inconsistencies_and_known_issues.md` | Known schema/implementation gaps, unconfirmed items |

## AI routing

Load these docs for Event Bus tasks:

- Implementing or debugging `scripts/eventbus/*.py`: `01`, `02`, `03`, `04`
- Config/env/deployment: `05`
- Known issues: `90`
- Module API: `06`

## Canonical source rule

The canonical source of truth for behavior is the **source code** (`scripts/eventbus/`), not these documents. When a document conflicts with the code, trust the code and update the document.
