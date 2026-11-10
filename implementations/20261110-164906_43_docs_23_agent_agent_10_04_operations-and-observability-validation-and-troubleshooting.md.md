## Goal

Describe the single fingerprint validation mechanism in the troubleshooting steps of `agent_10_04`
(`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The "Legacy Migration Marker Refusal" troubleshooting entry (lines 89-93) currently describes a
  marker-table check plus a `user_version` stamping message; both are replaced by the fingerprint
  gate.
- The archive-and-recreate response (line 93) stays.

## Design decisions
- Rewrite the symptom (line 91) to report a fingerprint mismatch and the archive-and-recreate error;
  drop the "version stamping are not supported" wording.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`

### Procedure
1. Legacy Migration Marker Refusal (line 89-91): replace the symptom text
   "`Legacy migration marker table(s) present: <tables>` followed by 'The database does not match
   the current schema. Automatic migration and version stamping are not supported.' `init_db.sh`
   reports `[FATAL] workflow.sqlite carries legacy migration marker table(s) and does not match the
   current schema.`" with a fingerprint-mismatch symptom: "the startup gate reports that the workflow
   database shape does not match the current canonical schema ... `[FATAL] workflow.sqlite does not
   match the current schema`".
2. Keep line 93 (Response: stop the service, archive, remove or rename, recreate with the current
   schema) unchanged.

### Method
- Locate the clause with
  `rg -n 'Legacy migration marker table|version stamping are not supported' docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
  before editing.

### Details
- The surrounding troubleshooting entries are unaffected.

## Compatibility considerations
Cross-references to the severity-mapping document remain valid.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run python tools/check_docs_consistency.py --domain agent` passes; no document claims a
validation mechanism other than fingerprint matching.

## Completion criteria
Lines 89-93 describe the fingerprint gate and archive-and-recreate failure; the marker-table and
version-stamp wording is removed.

## Out of Scope
Changing other troubleshooting entries or the severity mapping.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Describe the validation mechanism in the troubleshooting steps | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` — describe the validation mechanism in the troubleshooting steps
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
