## Goal

Record the ebcompat002 retain decision in `scripts/eventbus/README.md` by appending one decision
sentence to the Stub Module Pattern section. This is the only edit of the task: no source-code,
test, or docs change (plan AC-02 pins `git diff -- scripts/agent/ scripts/eventbus/db.py` to empty).

## Scope

- Edit `scripts/eventbus/README.md`: append the decision sentence after the existing rule line at
  the end of the Stub Module Pattern section (line 19), inside the same section (lines 15-19).
- Verification (plan Phase 2, no file edits): run the three Phase 2 commands and the AC-02 diff
  pin. Commands are listed in the Validation plan below and in the source plan's Test Strategy.

Out of scope per the source plan: renaming, splitting, or deleting `scripts/eventbus/db.py`;
touching any other file; changing `tools/check_compat_shims.py` or the canonical registry entry;
ADR-006 or any `docs/` file; adding a new check (no manifest entry is needed — the checker
already passes against the facade with zero findings).

## Assumptions

- (confirmed by plan verification 2026-10-27) `tools/check_compat_shims.py` exits 0 with zero
  findings against the current facade: the facade's 13 re-exported names are not in the legacy
  namespace, and the canonical registry entry covers `scripts/eventbus/` for the
  forbidden-module-imports check.
- (confirmed by plan verification 2026-10-27) the deferred facade imports in
  `tests/agent/services/test_eventbus_consumer.py` and `tests/metrics/test_eventbus_dlq_metrics.py`
  are monkeypatch convenience, not compat requirements.
- (confirmed at procedure generation 2026-10-28) the README is 19 lines and the Stub Module
  Pattern section ends with the "Do not add new functions here" rule line, matching the plan's
  location claim (lines 15-19).
- (assumption, benign) the appended sentence may adjust wording slightly at implementation time;
  AC-01/AC-03 check the section and the decision record, not an exact string.

## Design decisions

- (confirmed, frozen plan Decision 1 + user retain decision 2026-10-27) the facade stays: layering
  rule for `scripts/agent/services/*`, test seam for deferred eventbus imports, single canonical
  checker entry point.
- (confirmed, frozen plan Decision 2) the decision is recorded in the README only, not in
  `docs/` or an ADR: the README already owns the module's usage rules.
- (design) single sentence appended after the existing rule line: the README's pattern for
  section-local rules is a bold-labelled line (the existing **Rule** line); the decision line
  mirrors that shape so the decision sits at the point of use.

## Alternatives considered

- (rejected, plan Decision 2) `docs/` or ADR-006 entry: out of scope, already ruled out.
- (rejected, plan Step 3 verification) new `tools/compat_exceptions.toml` entry: unnecessary; the
  checker passes with zero findings.
- (rejected, frozen plan) removal variants: the owner decision is retain; the alternative path's
  test-retargeting work was never needed.

## Implementation
### Target file
`scripts/eventbus/README.md` (edit, 1 section)
### Procedure
1. Append one new line after line 19 (the existing **Rule** line), inside the Stub Module Pattern
   section. New content (1 line):

   ```text
   **Decision (2026-10-27)**: Retain this facade as the single entry point for the eventbus module; all consumer imports, including `scripts/agent/services/*`, go through it.
   ```
2. Run the Validation plan below (Phase 2 of the source plan). No other file changes.
### Method
Text append only. The exact sentence may be reworded (see Assumptions); it must record the retain
decision and the facade rule (consumers import through the facade).
### Details
- Reference file (not modified): `scripts/eventbus/db.py` — the facade itself; 13 re-exported
  names pinned by `tests/eventbus/` (AC-02 pins its diff to empty).
- The append lands at line 20 of the resulting file; the section keeps its existing heading and
  both existing lines unchanged.

## Compatibility considerations

- README is documentation consumed by humans and stale_detector; no runtime consumer.
- `tools/stale_detector.py scripts/eventbus/README.md` currently reports no findings; the new
  line references only existing paths (`scripts/agent/services/` exists as a directory; the
  sentence's backticked path is a directory, not a symbol).

## Security considerations

No security surface: documentation-only change.

## Rollback considerations

Single-line append; revert the file (`git checkout -- scripts/eventbus/README.md`).

## Validation plan

| Check | Command / Criterion | Status |
|-------|---------------------|--------|
| Phase 2 agent tests | `uv run pytest tests/agent -q` (AC-01) | Expected pass |
| Facade shape gate | `uv run python tools/check_compat_shims.py` (AC-02, AC-03) | Expected exit 0, zero findings; already confirmed passing at procedure generation 2026-10-28 |
| README freshness | `uv run python tools/stale_detector.py scripts/eventbus/README.md` (AC-02) | Expected no findings |
| No-code-edit pin | `git diff -- scripts/agent/ scripts/eventbus/db.py` is empty (AC-02) | Expected empty |

No new or modified test files: the plan's test-files column lists the README and the facade as
verification targets only.

## Completion criteria

- AC-01: `tests/agent` green (unchanged code).
- AC-02: the three commands above pass and the diff pin is empty.
- AC-03: the README Stub Module Pattern section records the retain decision.

## Out of Scope

All plan Out-of-scope items apply without change: facade removal/rename, any file other than the
README, checker or manifest changes, docs/ADR edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-153121 | 20261028-153121 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261028-153121 | 20261028-153121 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-153121 | 20261028-153121 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-153121 | 20261028-153121 |  |

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
- **Requirement ID**: `AC-01`, `AC-02`, `AC-03` (acceptance-criteria ids of the source plan's single target row; the plan defines no REQ ids)
- **Source issue**: N/A: no standalone issue; the plan's Source issue is N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-120858_ebcompat002_decide-eventbus-db-facade.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-10-28T07:04:53
- **Related target files**: `scripts/eventbus/README.md`, `scripts/eventbus/db.py` (reference only)