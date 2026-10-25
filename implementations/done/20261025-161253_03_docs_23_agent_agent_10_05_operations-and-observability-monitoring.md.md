# Implementation Procedure — docs/23_agent/agent_10_05_operations-and-observability-monitoring.md

## Goal

State the diagnostics config snapshot semantics in
`docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`: config
changes take effect at the start of each `DiagnosticStore` operation, one snapshot
per operation (REQ-006, AC-005).

## Scope

- One bullet added under `### Session Summary` in
  `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`.
- No other docs file changes (plan Documentation Impact; `rules/coding.md` unchanged).

## Assumptions

- Verified 2026-10-25 against master @ d41092a81: the `Session Summary` subsection
  (78-83) ends with two bullets — workflow-field fallback and "A failure to persist
  diagnostics is logged at DEBUG level ..." (83). The new bullet anchors after them.
- The `[diagnostics]` section of `config/agent.toml` currently lists
  `encryption_key` and `retention_days`; `sensitive_fields` is supported by the
  loader (`_load_diagnostics_config` reads it) though not present in the shipped
  file — the docs sentence describes supported keys generically, no claim about the
  shipped file.

## Design decisions

- Single policy sentence as a bullet, no code detail (plan target-table contract):
  per-operation snapshot semantics are the operator-visible contract the tests from
  procedure 02 pin.
- Placed under `Session Summary` next to the existing persistence-behavior bullets
  rather than `Querying Session Diagnostics` (read-path only today).

## Alternatives considered

- Separate subsection: rejected — Path A scope, one sentence suffices.
- Needs-Confirmation marker: not needed; the design (per-operation load, no cache)
  is verified by procedure 02 tests 1-3 (plan Documentation Impact).

## Implementation

### Target file

`docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` (modify).

### Procedure

1. After the bullet "A failure to persist diagnostics is logged at DEBUG level and
   never blocks conversation continuation or session shutdown." (83) append:

   ```markdown
   - The `[diagnostics]` settings (`encryption_key`, `retention_days`,
     `sensitive_fields`) are read fresh once per `DiagnosticStore` operation: edits
     to `config/agent.toml` take effect from the next diagnostic write or query
     without restarting the agent, and all decisions inside one operation use that
     single snapshot.
   ```

2. Run the docs checker (routing.md Tools: "When to run which tool" — docs entry).

### Method

Text-only edit.

### Details

- Wording must not promise mid-operation reload: "next diagnostic write or query"
  matches the REQ-004 contract exactly.

## Compatibility considerations

- No keyword/anchor collisions: `Keywords` section (85+) untouched; stale checker
  must see the quoted bullet text as live after the edit.

## Security considerations

- None: no secrets, no paths beyond the config filename.

## Rollback considerations

- Single-bullet append; revert by deleting it.

## Validation plan

- `uv run tools/check_workitem_structure.py --file implementations/20261025-161253_03_docs_23_agent_agent_10_05_operations-and-observability-monitoring.md.md` (this document)
- Repo docs checker per routing.md after the edit; `uv run pytest tests/agent/test_diagnostic_store.py -q` unaffected (docs-only change).

## Completion criteria

- Bullet present under `Session Summary`; docs checker clean.

## Out of Scope

- Any other section of `agent_10_05`, the linked `agent_10_06` file, config file
  content changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the snapshot-semantics bullet | Completed | — | — | After procedure 01 lands (contract must exist in code before docs claim it) bullet appended under Session Summary |
| 2 | Run docs checker | Completed | — | — | quality/structure/content-policy/consistency clean; pre-existing /stats stale_detector source_missing unrelated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006
- **Source issue**: `issues/20261025-115935_sess006_diagnostic-store-config-reload.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124341_sess006_diagnostic-store-config-reload.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure