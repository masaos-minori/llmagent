## Goal

Harden the manual recovery procedure for `workflow.sqlite` and `eventbus.sqlite` in `agent_10_01` so it mirrors the automated path's safety bar: stop the standalone EventBus service and the Agent, move each database's `-wal`/`-shm` sidecars aside before the restore `cp`, verify the backup, restore, then start — per `REQ-001` (harden the manual recovery procedure).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The automated restore path is the safety baseline the manual procedure mirrors: `recovery.py::_restore_from_backup()` stages the candidate, verifies it (`_verify_candidate()`), and only then activates (`_activate_candidate()`); `recovery_restore.py::_quarantine_sidecar_files()` moves stale `-wal`/`-shm` sidecars aside (fail-closed); `recovery.py::_backup_is_usable()` runs `_run_integrity_check(backup, target)` before any copy.
- The EventBus is a separate, persistent uvicorn HTTP process (`scripts/eventbus/app.py::_main()`), independent of the Agent process, that holds `eventbus.sqlite` open. It runs only when the EventBus is enabled, but `adr_02_05_008` lists it as a distinct target process, so name it explicitly regardless of whether it is currently enabled.
- The `adrrev005` post-restore schema-fingerprint verification is a real check whose exact form is defined by `adrrev005`; this procedure names it as a post-restore gate but does not redefine it.
- The current 7-step Manual Recovery structure is preserved; edits insert service stops into Step 1 and sidecar handling before Step 5's `cp`, rather than restructuring into a command catalog.

## Design decisions

- Keep the change documentation-only and localized to the "Manual Recovery: workflow.sqlite / eventbus.sqlite" section; do not introduce runtime behavior, an interface, or a new script the operator cannot invoke.
- Mirror the automated ordering (stop → preserve → locate → validate → move sidecars → restore → re-verify → start) with minimal operator steps, matching the plan's Out-of-Scope prohibition on a command-by-command catalog.

## Alternatives considered

- N/A: documentation-only change; no runtime behavior, persistence, or public-interface impact.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

1. Edit **Step 1** (current line 102, "Stop the agent process completely (ensure no remaining subprocesses)") to stop two distinct processes: the Agent process, then the standalone EventBus service. State that the EventBus service is the persistent uvicorn HTTP server in `scripts/eventbus/app.py` that binds `cfg.host:cfg.port` and holds `eventbus.sqlite` open, and that the Agent's own shutdown does not stop it. Give the operator a concrete stop mechanism (the service manager or the process that launched the EventBus) and a verification that no `eventbus` uvicorn process remains. Note the step is conditional on the EventBus being enabled, but name it regardless (per `adr_02_05_008`).
2. Insert a new step between **Step 4** (validate candidate) and **Step 5** (apply backup): move each database's `-wal`/`-shm` sidecars aside to a timestamped quarantine directory before the restore `cp`. Provide a one-block bash snippet and explain that leaving stale sidecars in place lets SQLite replay those frames onto the restored file on next open, which can produce a corrupted or mixed database — the same hazard the automated path closes by quarantining sidecars (`recovery_restore.py::_quarantine_sidecar_files()`).
3. In **Step 5** (current lines 127-134), after the post-copy `PRAGMA integrity_check` must print `ok` again, add a reference to run the `adrrev005` post-restore schema-fingerprint verification against the restored databases and treat a fingerprint mismatch as a failed restore (revert to the archived original). Name the check; defer its exact assertions to `adrrev005`.

### Method

- **Step 1 edit.** Replace the parenthetical with an explicit two-part stop. Suggested wording: "Stop the Agent process completely, then stop the standalone EventBus service. The EventBus is a persistent uvicorn HTTP process (`scripts/eventbus/app.py`) that binds `cfg.host:cfg.port` and holds `eventbus.sqlite` open; it is separate from the Agent process, so the Agent's shutdown does not stop it. Stop it via its service manager (or the process that launched it) and confirm no `eventbus` uvicorn process remains. This step applies when the EventBus is enabled; name it regardless, because `adr_02_05_008` lists the EventBus as a target process that holds `eventbus.sqlite`."
- **Sidecar step (new, before Step 5).**
  ```bash
  # Move -wal/-shm sidecars aside before restoring, so SQLite cannot replay
  # stale frames onto the restored file on next open. Mirrors
  # scripts/db/recovery_restore.py::_quarantine_sidecar_files().
  QUARANTINE_DIR="./recovery_quarantine_$(date -u +%Y%m%d_%H%M%S)"
  mkdir -p "$QUARANTINE_DIR"
  for db in workflow eventbus; do
    for ext in -wal -shm; do
      [ -f "${db}.sqlite${ext}" ] && mv "${db}.sqlite${ext}" "$QUARANTINE_DIR/"
    done
  done
  ```
- **Step 5 edit.** After both `PRAGMA integrity_check` calls print `ok`, append: "Run the `adrrev005` post-restore schema-fingerprint verification against `workflow.sqlite` and `eventbus.sqlite`. A fingerprint mismatch means the restore did not produce the expected schema: do not start the agent; revert to the archived original and escalate."

### Details

- Evidence for the claims above (verified against current source, HEAD `e700efa5f`):
  - **Step 1** (line 102) currently states only "ensure no remaining subprocesses"; it does not name the standalone EventBus service.
  - **Step 5** (lines 127-134) copies the backup over the live file with `cp` and runs `PRAGMA integrity_check`; it does NOT move `-wal`/`-shm` sidecars beforehand.
  - **Step 6** (lines 137-143) removes sidecars via `rm -f ... -wal ... -shm`, but only inside the no-backup fallback path, not before a restore.
  - `recovery.py::_backup_is_usable()` (line 180) runs `_run_integrity_check(backup, target)` before any copy; `recovery.py::_restore_from_backup()` (line 336) stages via `recovery_restore.py::_stage_restore()` (line 76), verifies via `_verify_candidate()`, then activates — the staging-before-activation pattern the manual path should mirror.
  - `recovery_restore.py::_quarantine_sidecar_files()` (line 22) copies each `-wal`/`-shm` sidecar to a quarantine directory and unlinks it (fail-closed); `recovery_restore.py::_stage_restore()` (line 76) quarantines, archives the corrupt DB, then stages the candidate.
  - `scripts/eventbus/app.py::_main()` (lines 227-272) starts a persistent uvicorn server (`uvicorn.Config`, `server.run()`) binding `cfg.host:cfg.port`; it is separate from the agent process and holds `eventbus.sqlite` open.
  - `scripts/db/create_schema.py::create_workflow_schema()` (line 103) produces the empty `workflow.sqlite` used by Step 6's fallback.
- Do not fabricate: the exact `adrrev005` fingerprint assertion is `adrrev005`'s — name it, do not redefine it.
- Keep every other byte of the file identical (Plan Risks: scope each edit to the clause under change; re-run `check_docs_consistency.py --domain agent` against `HEAD` before committing).

## Compatibility considerations

- N/A: documentation-only; no source, config, schema, migration, deployment, or public-interface change. The EventBus service-stop step is conditional on the EventBus being enabled; state that explicitly.

## Security considerations

- N/A: no security-relevant behavior change. Moving sidecars aside prevents data corruption (integrity), not a security boundary.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

| Action | Tool / Command | Expected Outcome |
|---|---|---|
| Cross-domain claim consistency (manual recovery vs automated path) | `uv run python tools/check_docs_consistency.py --domain agent` | Pass |
| Japanese-text policy | `uv run python tools/check_docs_japanese.py` | Pass (English only) |

## Completion criteria

- Step 1 names the standalone EventBus service stop explicitly, separate from the Agent.
- An explicit "move `-wal`/`-shm` sidecars aside" step appears before Step 5's restore `cp`, with the replay-hazard rationale.
- Step 5 references the `adrrev005` post-restore schema-fingerprint verification as a gate.
- `check_docs_consistency.py --domain agent` and `check_docs_japanese.py` pass.

## Out of Scope

- Implementing the schema fingerprint (`adrrev005`).
- Automating the manual restore (`adr_02_05_008` INV-18 stays prohibited).
- Rewriting the procedure into a command-by-command catalog beyond the minimal operator steps.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (harden the manual recovery procedure to stop the EventBus service and Agent, move `-wal`/`-shm` sidecars aside, verify the backup)
- **Source issue**: `issues/20261109-112922_adrrev009_adr008-recovery-align.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-233648_adrrev009_adr008-recovery-align.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-181318
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
