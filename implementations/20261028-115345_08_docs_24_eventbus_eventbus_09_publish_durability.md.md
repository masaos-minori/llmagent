# Procedure: state the publish guarantee once with the authority model and fix the duplicate-publish sentence

## Goal

Restate the publish guarantee together with the authority model and correct the "idempotent by nature" sentence (Plan REQ-001, REQ-007).

## Scope

- Modify only `docs/24_eventbus/eventbus_09_publish_durability.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- The code procedures of this Plan (`seq` 01 and 02) have landed before the test procedures run.
- All text stays English (`skills/DESIGN.md` Output language).
- Overlap (compatible): `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived, procedures pending) also targets `scripts/eventbus/ack_route.py` (authorization at the start of the routes) and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (Authentication section and error table); this procedure edits only the promotion block of `_nack_and_promote` and one transition-table row.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/24_eventbus/eventbus_09_publish_durability.md`

### Procedure

- In `## Canonical Store`, add one sentence tying the guarantee to the authority model: SQLite is canonical for events and DLQ state, the JSONL archive and DLQ files are derived, broker notification is best-effort and recoverable through SQLite replay; the publish guarantee is the database commit.
- In `### Permission Failure Scenario`, replace "No retry attempt (idempotent by nature — JSONL append is append-only)." with: a retry of the same event is idempotent in SQLite and does not append to JSONL, because JSONL is appended only for newly inserted events, so a failed append is not repaired by a retry.
- Keep the failure-scenario and recovery sections otherwise unchanged.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- The doc already names SQLite as canonical; this edit adds the single guarantee statement and removes the misleading sentence.

## Compatibility considerations

N/A: documentation-only.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py --strict`; `uv run python tools/check_docs_japanese.py`; `uv run python tools/check_docs_consistency.py --domain eventbus` | No finding |

## Completion criteria

- The document states the behavior described in Details.
- All listed documentation checkers report no finding.

## Out of Scope

- Every other document.
- Code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-007 (publish guarantee; no JSONL backfill on duplicate publish)
- **Source issue**: issues/20261027-155846_ebdurable003_define-publish-dlq-durability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115345
- **Related target files**: docs/24_eventbus/eventbus_09_publish_durability.md
