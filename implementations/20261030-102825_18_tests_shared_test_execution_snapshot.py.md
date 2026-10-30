# Implementation Procedure: tests/shared/test_execution_snapshot.py

## Goal

Regression coverage for the new snapshot module (row 03): build, per-component
equality/mismatch, and the missing-DEPLOYED_REV boundary (REQ-004 snapshot
semantics), test-first for row 03.

## Scope

**In scope:**
- `tests/shared/test_execution_snapshot.py`: new file.

**Out of scope:**
- Snapshot module (row 03); snapshot persistence (rows 06-07); audit serialization
  (row 05).

## Assumptions

- New file: does not exist at HEAD (verified `ls tests/shared/`); plan row 18 "New"
  confirmed. Red until row 03 lands.
- `/opt/llm/DEPLOYED_REV` must never be read from or written to in tests: the module
  (row 03) takes an injectable path/env override; tests point it at tmp files. If
  row 03 exposes no override seam, the tests monkeypatch the path constant — Needs
  Confirmation at implementation, and the seam is then a row-03 requirement note.
- The four components are `deployed_rev` (new), `git_sha` (new), `config_hash` (new),
  `schema_versions` (new) (row 03 design).

## Design decisions

- Build: with fixtures present, all four components populated;
  `deployed_rev` (new) fixture JSON mirrors the real producer shape (`{commit,
  deployed_at, dirty}` written by `deploy/deploy.sh:144` /
  `tools/manage_binaries.py:53,354` — verified HEAD).
- Equality/mismatch per component: identical inputs → equal snapshot hash; each of
  the four components perturbed alone (git sha changed, one TOML byte changed,
  PRAGMA user_version changed, DEPLOYED_REV regenerated) → inequality, and the
  mismatch report names the differing component (row 03 comparator contract).
- Missing DEPLOYED_REV: absent file → component `"unknown"`, module does not raise;
  snapshot still comparable (two unknown-deployed_rev snapshots with equal other
  components are equal).
- Determinism: config_hash stable under TOML dict insertion-order variation (canonical
  serialization), unstable under content change.

## Alternatives considered

- Reading the real `/opt/llm/DEPLOYED_REV` in tests — rejected: host-dependent,
  violates test hermeticity.
- Full structural fingerprint comparison (eventbus_schema_fingerprint-style) —
  rejected here: row 03 pins version numbers; fingerprint depth is out of this
  plan's scope.

## Implementation
### Target file
`tests/shared/test_execution_snapshot.py` (new)

### Procedure
1. Fixtures: tmp DEPLOYED_REV writer, tmp config-dir builder, in-memory sqlite with
   `PRAGMA user_version`.
2. Test classes: `TestBuild` (new), `TestEquality` (new), `TestPerComponentMismatch` (new),
   `TestMissingDeployedRev` (new), `TestDeterminism` (new).

### Method
Test-first: red until row 03 lands.

### Details
- Shared-layer test: imports only `shared.*` (import-contract safe).

## Compatibility considerations

- None (new file).

## Security considerations

- Snapshot values are synthetic; no real config content copied into fixtures.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_execution_snapshot.py` (red before row 03, green
  after); `uv run mypy --no-namespace-packages tests/shared`; `uv run lint-imports`.

## Completion criteria

- Build/equality/mismatch/missing/unknown semantics all proven; suite green with
  row 03 landed.

## Out of Scope

- Replay decision policy in the dispatcher (row 19); snapshot columns in workflow
  tables (rows 06-07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create test file + five test classes | Pending | — | — | Red until row 03 lands |
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
- **Requirement ID**: `REQ-004` (snapshot at execution, replay comparison inputs)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: tests/shared/test_execution_snapshot.py (new)
