# Procedure: refresh the generated API reference rows for the authorization symbols

## Goal

Refresh the `Principal`, `require_consumer_identity` and new function rows through the generator, not by hand (Plan REQ-008).

## Scope

- Modify only `docs/24_eventbus/eventbus_08_reference_api.md`.
- Documentation-only change; state current behavior only (no history of the old model).

## Assumptions

- The implementation rows of this Plan have landed, so the text describes shipped behavior.
- All text stays English (`skills/DESIGN.md` Output language).
- Overlap (compatible): `plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md` also targets `scripts/eventbus/ack_route.py` and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`; it edits the promotion block of `_nack_and_promote` and one transition-table row, which this procedure does not touch. `plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` also targets `scripts/eventbus/app.py` (`_shutdown_lifespan` only).

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow the surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure

- Run `uv run python tools/generate_reference_table.py --type eventbus --dry-run` first if that type exists, otherwise `uv run python tools/generate_reference_table.py --check` to see the drift; then regenerate with the matching `--type` so the `<!-- AUTO-GENERATED -->` block updates in place.
- If the generator does not cover these rows, edit only the rows for `Principal`, `require_consumer_identity`, `authorize_consumer_access` and `effective_topics` to match the new signatures.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- The generated block is guarded by `tools/generate_reference_table.py --check` (ADR-015 INV-01); a manual edit that drifts fails CI.

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

- The document states the pairwise grant model and the behavior described in Details.
- All listed documentation checkers report no finding.

## Out of Scope

- Every other document.
- Code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-130500 | 20261028-130500 |  |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261028-130500 | 20261028-130500 |  |

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
- **Requirement ID**: REQ-008 (generated reference stays in sync)
- **Source issue**: issues/20261027-155843_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-114911
- **Related target files**: docs/24_eventbus/eventbus_08_reference_api.md