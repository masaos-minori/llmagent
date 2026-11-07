# Implementation Procedure: tests/tools/test_no_compatibility_policy_gate.py

## Goal
Create the repository-wide no-compatibility-policy gate test: production-category-zero, zero live
references to the consolidated removed names, mandatory-consumer NACK signature, `AuthzGeneration`
-
only state, and checker blocking of reintroduction (rotation/recovery).

## Scope
- Target file: `tests/tools/test_no_compatibility_policy_gate.py` (new).
- Release unit: `policy-finalization` (lands after compatrm001/002/003 and this plan's docs 01-03).
- Related requirement / acceptance criteria: REQ-007 / AC-002, AC-004, AC-005, AC-007 (frozen
  target row 4); proves REQ-004 / AC-003 option-pair identity.

## Assumptions
- Prerequisites landed: facades and migration modules deleted (compatrm001/003), auth state is
  `AuthzGeneration`-only (compatrm002), checker consolidated (doc 01), manifest holds 18 `fixture`
  entries only (doc 02, including the new `deploy-init-db-schema-gate-test` entry recorded in that
  document's Verification findings). Verified 2026-11-07 (HEAD `be4d74463`): the pre-commit hook
  (`.pre-commit-config.yaml` id `check-compat-shims`) and the CI run step
  (`.github/workflows/backward-compat-check.yml`) both carry exactly
  `--check-removed-names --check-doc-symbols`; `pyproject.toml` and `tox.ini` contain no checker
  invocation — the step 7 assertions match the current tree before implementation.
- `tests/conftest.py` adds `scripts/` and `tools/` to `sys.path`; imports resolve as
  `eventbus.delivery_repo` and `check_compat_shims`.
- UNK-03 (Blocking? = False): early-session grep output referenced `TestGateguardCoverage`,
  `tests/test_precommit_gate_failure_recovery.py`, `tests/tools/test_gateguard_rotation.py`, and
  `docs/40_testing/test_document.md`; none of these exist in the current tree or git history. The
  cause is unknown. This gate test is designed self-contained: it parses config files directly and
  implements its own rotation scenario, so it does not depend on those artifacts.

## Design decisions
- Retired-name literals never appear in this gate file: names are derived programmatically from
  `check_compat_shims.COMPAT_PATTERNS` and the doc-claim phrase patterns. Writing literals here
  would require adding this file to the fixture manifest and weaken the gate.
- Config-pair pinning parses YAML files (`yaml.safe_load` available in the test environment; fall
  back to line regex if not) instead of trusting external gate tests.
- Rotation runs the checker in a sandbox: copy `tools/check_compat_shims.py`, the manifest, and a
  fixture doc into `tmp_path` (the checker resolves its manifest and `ROOT_DIR` relative to its
  own file), delete one manifest entry plus its fixture file, run the subprocess, expect exit 1;
  restore and expect exit 0. This keeps rotation proof hermetic (no mutation of the real repo).
- One dedicated test asserts the gate file itself contains no retired-name literal (self-audit).

## Alternatives considered
- Reusing a repo-wide grep script inside the test: rejected — pattern drift between checker and
  gate would silently desynchronize the two; deriving from the checker keeps one source of truth.
- Running `pre-commit run --id check-compat-shims` in a sandbox git repo: rejected — heavier,
  requires git plumbing; the checker subprocess is the blocking surface the hook invokes verbatim.

## Implementation

### Target file
- `tests/tools/test_no_compatibility_policy_gate.py` (new).

### Procedure
1. Module scaffolding: `sys.path` via conftest; import `check_compat_shims` as `checker`; derive
   `RETIRED = checker.COMPAT_PATTERNS` names and the doc-claim phrases from the checker module
   (attribute access only — no literal retired names in this file).
2. `TestProductionExceptionZero`: parse `tools/compat_exceptions.toml` with `tomllib`; assert every
   `[[compatibility_exceptions]]` entry has `category == "fixture"`, no entry id starts with
   `migration-`, and no `[symbol_stage_allowance]`-style production exemption reappears as a
   `compatibility` entry.
3. `TestNoLiveReferences`: scan `scripts/**.py`, active `docs/**.md` (skipping paths listed in the
   fixture manifest and any `done/` component), and `tools/**.py` (excluding checker and manifest)
   for the derived retired names and doc-claim phrases; assert zero live hits outside fixture
   paths.
4. `TestMandatoryConsumerNack`: `from eventbus.delivery_repo import nack_event`;
   `inspect.signature(nack_event).parameters["consumer_id"].default is inspect.Parameter.empty`
   (post-compatrm003 tightening).
5. `TestAuthzGenerationOnly`: assert the eventbus auth surface exposes `AuthzGeneration` and the
   module contains no legacy auth-compat state names derived from the checker pattern set.
6. `TestCheckerBlocking`: subprocess `sys.executable -m tools.check_compat_shims
   --check-removed-names --check-doc-symbols` at the repo root → exit 0; a tmp sandbox with one
   manifest entry deleted and its fixture doc dirtied by appending a synthetic, marker-free
   migration-claim sentence (e.g. "the schema migrates forward on open") → exit 1
   (rejection); restoring the file and entry → exit 0 (recovery) — AC-006 rotation proof. The
   contaminant must not quote live doc text: the historical-context exemption already covers the
   live corpus, so quoting it would not flip the checker's verdict.
7. `TestOptionPairIdentity`: parse `.pre-commit-config.yaml` hook `check-compat-shims` entry and
   `.github/workflows/backward-compat-check.yml` run step; assert both carry exactly
   `--check-removed-names --check-doc-symbols` and no allowlist or allow-entry override flags;
   assert
   `pyproject.toml` and `tox.ini` contain no checker invocation (drift tripwire).
8. `TestGateFileSelfAudit`: assert none of the derived retired names appears as a literal in this
   test file's own text.

### Method
- `subprocess.run([sys.executable, "-m", "tools.check_compat_shims", ...], cwd=REPO_ROOT)`.
- Sandbox copies via `shutil.copy`; manifest edits via text replacement before the failing run.

### Details
- Retired names for step 3 include the consolidated import forms (`db.store` import, `eventbus.db`
  import, `shared.db_migrations`, `migrate_db.py`, `schema_migrations`,
  `workflow_schema_version`/`WORKFLOW_SCHEMA_VERSION`, two-arg `nack_event(` call shape) — all via
  checker attributes.
- Fixture-manifest paths are excluded from step 3 scanning because they legitimately quote the
  removed names as fixture data.

## Compatibility considerations
- Strictly ordered after docs 01-02 and the compatrm001/002/003 procedures; running earlier
  produces expected red until prerequisites land (same release unit).

## Security considerations
- No secrets; sandbox writes under `tmp_path` only; no network or DB access.

## Rollback considerations
- New test file only: delete the file to roll back; safe only as a unit with the checker/manifest
  finalization it proves.

## Validation plan
- Targeted: `uv run pytest tests/tools/test_no_compatibility_policy_gate.py -v`.
- Full: `uv run pytest`.

## Completion criteria
- All classes green on the finalized tree; rotation sandbox demonstrates reject-then-recover;
  option-pair pin matches pre-commit and CI verbatim; zero retired-name literals in the file.

## Out of Scope
- Checker internals (doc 01), manifest content (doc 02), checker unit tests (doc 03).
- Editing `.pre-commit-config.yaml`, `.github/workflows/backward-compat-check.yml`, or
  `pyproject.toml` — those are VERIFY rows (docs 05-07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Module scaffolding + derived pattern set | Completed | 20261107-184026 | 20261107-184026 | no literals |
| 2 | TestProductionExceptionZero | Completed | 20261107-184026 | 20261107-184026 | tomllib parse |
| 3 | TestNoLiveReferences | Completed | 20261107-184026 | 20261107-184026 | fixture paths excluded |
| 4 | TestMandatoryConsumerNack | Completed | 20261107-184026 | 20261107-184026 | inspect.signature |
| 5 | TestAuthzGenerationOnly | Completed | 20261107-184026 | 20261107-184026 | compatrm002 state |
| 6 | TestCheckerBlocking (rotation/recovery) | Completed | 20261107-184026 | 20261107-184026 | sandbox subprocess |
| 7 | TestOptionPairIdentity | Completed | 20261107-184026 | 20261107-184026 | YAML pair pin |
| 8 | TestGateFileSelfAudit | Completed | 20261107-184026 | 20261107-184026 | self-audit |
### Blocker Log
- UNK-03: `TestGateguardCoverage` / `tests/test_precommit_gate_failure_recovery.py` /
  `tests/tools/test_gateguard_rotation.py` / `docs/40_testing/test_document.md` were referenced by
  session-early searches but do not exist in the tree or git history at generation time; cause
  unknown (`不明`). Mitigation: gate test is self-contained (steps 6-7). Non-blocking for this
  document; flagged for the user in the cycle report.

### Work Items Created
- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007 / AC-002, AC-004, AC-005, AC-007
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-064415_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-103000
- **Related target files**: `tests/tools/test_no_compatibility_policy_gate.py`