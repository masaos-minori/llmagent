# Implementation Procedure: docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md

## Goal
Replace the runbook's migration-era instructions (schema-version query and
"re-run the deployment scripts to apply migrations") with the archive-and-recreate procedure.

## Scope
- Target file:
  `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
  (MODIFY).
- Release unit: `policy-finalization`.
- Related requirement / acceptance criteria: REQ-005, REQ-006 / AC-004, AC-005 (frozen target
  row 10).

## Assumptions
- Anchors grep-verified: line 54 (`SELECT * FROM workflow_schema_version` in a diagnostic block,
  context lines 52-54) and line 93 ("Re-run the deployment scripts to apply migrations", context
  lines 91-93).
- `workflow_schema_version` is a retired mechanism (compatrm001); the EventBus `user_version`
  stamp is live and may remain if referenced.

## Design decisions
- Diagnostic replacement: schema mismatch is detected by startup failure; the runbook instructs
  comparing deployed code version against the database by archiving and recreating, not by
  querying a version table.
- The old command lines are removed, not commented out — runbooks must not invite operators to
  run commands against tables that no longer exist; the only historical mention left is one
  supersession note carrying `removed` in the same line.

## Verification findings (adversarial re-verification 2026-11-07, HEAD `be4d74463`)

- Already satisfied by the compatrm001-era rewrite; no edit needed. Lines 52-53 now read "Check
  workflow DB schema tables (the legacy marker tables schema_migrations and
  workflow_schema_version must be absent)" — an absence assertion carrying the `legacy` marker on
  the same line (historical-context exempt), not a version-table query. Lines 91-93 are the
  legacy-marker refusal symptom and the archive-and-recreate response ("No migration is
  attempted"); "Re-run the deployment scripts to apply migrations" no longer exists in the file.
- Whole-file sweep confirmed: the only `migration` mentions are the refusal/error texts and their
  negations; the consolidated checker reports zero findings for this file (verified by the full
  `--check-removed-names --check-doc-symbols` run). This row executes as VERIFY.

## Alternatives considered
- Keeping the SQL query marked as historical inside the runbook: rejected — runbook sections are
  action text; historical context belongs in the db docs (docs 12-13), not an operator procedure.

## Implementation

### Target file
- `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
  (MODIFY).

### Procedure
1. Lines 52-54: remove the `workflow_schema_version` diagnostic query block; replace with the
   current-only mismatch handling: startup error text → archive DB file → recreate via the
   canonical creation path → restore workload.
2. Lines 91-93: replace "Re-run the deployment scripts to apply migrations" with the
   archive-and-recreate instruction sentence.
3. Whole-file sweep: any remaining present-tense migration claim gets removed; any necessary
   historical mention carries a marker word.

### Method
- Text edits; checker doc-claim + doc-symbol pass afterwards (the removed query names are
  doc-symbol risks if left in backticks).

### Details
- Keep runbook numbering/heading structure intact so cross-references from other agent docs stay
  valid.

## Compatibility considerations
- Agent-docs consistency CI must stay green.

## Security considerations
- None.

## Rollback considerations
- Single-file revert.

## Validation plan
- Checker blocking run exit 0; agent docs consistency CI.

## Completion criteria
- Zero live migration instructions in the runbook; archive-and-recreate procedure present;
  checker green.

## Out of Scope
- db docs policy text (docs 12-13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Lines 52-54 block | Completed | 20261107-184026 | 20261107-184026 |  |
| 2 | Lines 91-93 sentence | Completed | 20261107-184026 | 20261107-184026 |  |
| 3 | Sweep | Completed | 20261107-184026 | 20261107-184026 |  |
### Blocker Log
- None.

### Work Items Created
- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005, REQ-006 / AC-004, AC-005
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-064415_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-103000
- **Related target files**: `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`