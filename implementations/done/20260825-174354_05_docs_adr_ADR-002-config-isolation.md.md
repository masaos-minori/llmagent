## Goal

`REQ-003`: correct the CI-001 Known Deviation entry's file attribution (it currently
names a file with no config-loading code at all) and update its Recommended Action and
Status to match the local-implementation fix delivered by REQ-001/REQ-002.

## Scope

- **In-Scope**: edit the `### CI-001: EventBus does NOT use ConfigLoader at all` entry
  (`docs/adr/ADR-002-config-isolation.md:358-369`) — `Conflicting Source`, `Observed
  Implementation`, `Recommended Action`, and add a `Status: Resolved` line (or
  equivalent) once REQ-001/REQ-002 land; add one line to `## Change History`
  (`docs/adr/ADR-002-config-isolation.md:438-446`).
- **Out-of-Scope**: any change to `## Decision` body text or the ADR's `Status` field
  (`Accepted`, line 16) — per ADR-002's own rule ("Accepted後に判断内容を変更する場合は
  本文を直接変更せず、新しいADRを作成して本ADRをSupersededへ変更する", line 26), Known
  Deviations entries are corrections to a record of drift, not Decision changes, so they
  may be edited in place without a new ADR.

## Assumptions

- Confirmed via Read that the current CI-001 entry reads:
  - `Conflicting Source`: `docs/adr/ADR-002-config-isolation.md:Decision #9,
    scripts/eventbus/broker.py`
  - `Observed Implementation`: "EventBus broker.py loads its own config via tomllib
    without calling restrict_to(), allowing it to access configs outside its declared
    scope"
  - `Recommended Action`: "Add ConfigLoader.restrict_to() call in EventBus startup path"
  - `Resolution Target`: "Before ADR-002 moves from Proposed to Accepted status"
- Confirmed via `rg` that `scripts/eventbus/broker.py` contains no `tomllib`,
  `ConfigLoader`, `restrict_to`, or config-loading code of any kind (zero matches) — the
  actual config-loading code is `scripts/eventbus/config.py:load_config()`, called from
  `scripts/eventbus/app.py:58,198`.
- Confirmed the ADR's own `## Status` (line 16) is already `Accepted`, so the existing
  `Resolution Target` ("Before ADR-002 moves from Proposed to Accepted status") is
  already past its own deadline — this entry has been sitting unresolved since
  acceptance and should be closed out by this Requirement, not merely re-dated.
- This document depends on REQ-001 (`scripts/eventbus/config.py`, implementation
  procedure `20260825-174354_02_scripts_eventbus_config.py.md`) and REQ-002
  (`scripts/agent/context.py`, implementation procedure
  `20260825-174354_01_scripts_agent_context.py.md`) landing first, since the
  `Recommended Action` and Status update describe those changes as already made — apply
  this document's edit after REQ-001/REQ-002 are implemented and validated, not before.

## Design decisions

- Correct `Conflicting Source` to `docs/adr/ADR-002-config-isolation.md:Decision #9,
  scripts/eventbus/config.py (load_config()), scripts/eventbus/app.py` — keep the
  `Decision #9` reference (still the relevant Decision), replace only the wrong file.
- Correct `Observed Implementation` to name `scripts/eventbus/config.py`'s
  `load_config()` (called from `app.py`) instead of `broker.py`.
- Update `Recommended Action` to describe the local-implementation fix actually taken:
  "EventBus cannot import `ConfigLoader` (`.importlinter` `eventbus-is-isolated`
  contract). Resolved via a local invariant instead: `load_config()`'s docstring states
  callers must pass `get_config_path()`'s return value, and a regression test in
  `tests/eventbus/test_eventbus_config.py` locks both call sites in `app.py` to that
  invariant. Agent-side, `ConfigLoader.restrict_to(\"agent.toml\")` was added to
  `AgentContext.__init__` (`scripts/agent/context.py`)."
- Add a `Status: Resolved (2026-08-25)` line to the CI-001 entry itself, since the entry
  format (per Assumptions) has no separate status field beyond `Resolution Target` —
  append it as a new bullet immediately after `Resolution Target` rather than replacing
  that field, preserving the historical target for audit purposes.
- Add one `## Change History` line: `- 2026-08-25: CI-001 file attribution corrected
  (broker.py -> config.py/app.py) and marked Resolved after local-implementation fix.`

## Alternatives considered

- Deleting the CI-001 entry outright instead of marking it Resolved: rejected — the
  Known Deviations section's own guidance (line 356, "ADRと現行実装...に差異がある場合に
  記載する") implies entries document history; marking Resolved preserves the audit trail
  that the deviation existed and was fixed, consistent with how `Change History` is used
  elsewhere in this ADR.

## Implementation

### Target file
`docs/adr/ADR-002-config-isolation.md`

### Procedure
1. Locate the `### CI-001: EventBus does NOT use ConfigLoader at all` section
   (currently lines 358-369).
2. Replace the `Conflicting Source` line's file reference from
   `scripts/eventbus/broker.py` to `scripts/eventbus/config.py (load_config()),
   scripts/eventbus/app.py`.
3. Replace the `Observed Implementation` line's file reference from `broker.py` to
   `scripts/eventbus/config.py`'s `load_config()` (called from `app.py`).
4. Replace the `Recommended Action` line with the local-implementation description (see
   Design decisions above), naming both the EventBus-side test-locked invariant and the
   Agent-side `restrict_to()` addition.
5. Add a `Status: Resolved (2026-08-25)` bullet after `Resolution Target`.
6. Add one line under `## Change History` (currently lines 438-446) following the
   existing format (`- YYYY-MM-DD: ...`).
7. Run `grep -c "eventbus/broker.py" docs/adr/ADR-002-config-isolation.md` and confirm 0.

### Method
Targeted text replacement within one existing subsection plus one new
`Change History` line; no other section of the document is touched.

### Details
- Do not alter `## Status` (line 16, `Accepted`) or any `## Decision` subsection — this
  edit is scoped to the Known Deviations record only, per Scope/Out-of-Scope above.

## Compatibility considerations

N/A: documentation-only change, no code or config file is affected.

## Security considerations

N/A: no security-relevant behavior is described or changed by this edit; it corrects a
documentation record of a now-fixed isolation gap.

## Rollback considerations

- Revert the CI-001 entry's four edited fields and remove the added `Change History`
  line; no other state depends on this document.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/adr/ADR-002-config-isolation.md` | Documentation verification | `grep -c "eventbus/broker.py" docs/adr/ADR-002-config-isolation.md` | `0` |
| `docs/adr/ADR-002-config-isolation.md` | Documentation verification | `uv run python tools/check_doc_quality.py` | Passes (structural/formatting rules) |
| `docs/adr/ADR-002-config-isolation.md` | Documentation verification | `uv run python tools/validate_docs_structure.py docs/adr/ADR-002-config-isolation.md` | Passes |

## Completion criteria

- CI-001's `Conflicting Source` and `Observed Implementation` no longer reference
  `scripts/eventbus/broker.py`.
- CI-001's `Recommended Action` describes the actual local-implementation fix taken by
  REQ-001/REQ-002.
- CI-001 carries a `Status: Resolved (2026-08-25)` marker.
- `## Change History` has one new line documenting this correction.
- `grep -c "eventbus/broker.py" docs/adr/ADR-002-config-isolation.md` returns `0`.

## Out of scope

- `## Decision`, `## Status` (ADR-level), and any section other than the CI-001 entry
  and `## Change History`.
- Filing a new ADR — not needed per ADR-002's own rule for non-Decision corrections.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct CI-001's `Conflicting Source` / `Observed Implementation` / `Recommended Action`, add `Status: Resolved` | Completed | — | — | |
| 2 | Add one `Change History` line | Completed | — | — | |
| 3 | Run documentation validation (`check_doc_quality.py`, `validate_docs_structure.py`) | Completed | — | — | Pre-existing errors only; no new issues introduced |
| 4 | Documentation update | Completed by Step 1-2 | — | — | This document's entire purpose is the documentation update itself |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Assumption | REQ-001/REQ-002 の完了に依存（AgentContext.__init__ に AGENT_RESTRICT_CONFIG guard + ConfigLoader.restrict_to() 追加、EventBus load_config() ドキュメント更新）。両方とも完了済み。 | Yes | 2026-08-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` — correct CI-001's file attribution and close it out as Resolved
- **Source issue**: `issues/20260822_ci_eventbus_bypasses_restrict_to.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-131854_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-174354
- **Related target files**: `docs/adr/ADR-002-config-isolation.md`
