# Procedure: repair the matrix parser and replace the substring match with a structured marker

## Goal

Make `check_adr_reference.py` parse the current matrix and require a deliberate `# ADR-NNN` comment marker instead of a substring (Plan REQ-005).

## Scope

- Modify only `tools/check_adr_reference.py`.
- In scope: `parse_matrix_source_refs`, `check_adr_reference`, `collect_issues` and the docstring.
- Out of scope: tests (row 4), marker comments (rows 10-13), docs.

## Assumptions

- Ordering note: apply the marker rows (seq 10-13) before this row so the repaired checker's live run is clean.
- The live matrix has six columns (`Invariant | Statement | Type | Timing | Gate | Verification Status`) and the ID cell reads like `ADR-001 INV-01`, so the current parser returns no references.
- Overlap (compatible): `plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` edits only the ADR-006 Implementation Notes, while this Plan edits ADR-006's Verification table. Any citation added by that Plan must resolve to an existing test node once the node validation of this Plan is in force.

## Design decisions

- Find columns by header name rather than by fixed position so a future column change cannot silently disable the check again.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`tools/check_adr_reference.py`

### Procedure

- In `parse_matrix_source_refs`, locate the header row after the matrix heading, find the indexes of the `Invariant` and `Verification Status` columns, and for each data row take every `ADR-\d+` token from the invariant cell as an ADR id; extract `scripts/*.py` backticked paths from the status cell as today.
- Replace `if ref.adr_id not in content:` with a `tokenize` pass (`_has_adr_marker(source, adr_id)` (new)) that accepts a comment token (as produced by `tokenize`) matching `#\s*<adr_id>\b`; report the existing ERROR message adjusted to say the file has no `# ADR-NNN` comment marker.
- In `collect_issues`, when `parse_matrix_source_refs` returns no references, return an ERROR Issue (`matrix yielded no source references; the matrix shape may have changed`) so the check cannot pass vacuously.
- Update the module docstring: marker form, parse by header, zero-row failure.

### Method

Rewrite the parser body and one check function; add `import io` and `import tokenize` (standard library).

### Details

- Matrix-named files today: `scripts/agent/orchestrator.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/mcp_servers/tool_validators.py`, `scripts/mcp_servers/shell/shell_service.py`, all for ADR-014.
- A file that cannot be tokenized (syntax error) must produce an ERROR, not an exception.

## Compatibility considerations

- Behavior change: files that passed vacuously now need the marker; rows 10-13 add it.

## Security considerations

- Read-only tokenization; no code executed.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/tools/test_check_adr_reference.py -q` | Pass |
| 2 | `uv run ruff format tools/check_adr_reference.py`; `uv run ruff check tools/check_adr_reference.py`; `uv run mypy tools/check_adr_reference.py`; `uv run bandit tools/check_adr_reference.py` | No finding (`mypy` receives the path explicitly because `pyproject.toml` does not cover `tools/`) |
| 3 | `uv run python tools/check_tool_descriptions_sync.py` | No finding |

## Completion criteria

- The checker parses four references on the live matrix, passes with the markers present, and fails for prose-only mentions and for an unparseable matrix.

## Out of Scope

- Marker comments, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-162007 | 20261028-162007 | Live matrix yields the 4 expected ADR-014 refs; applied after marker rows |
| 2 | Add or update tests per Validation plan | Completed | 20261028-162007 | 20261028-162007 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-162007 | 20261028-162007 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-162007 | 20261028-162007 |  |

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
- **Requirement ID**: REQ-005 (parser for the six-column matrix; tokenize marker; fail on zero rows)
- **Source issue**: issues/20261027-155848_adrgate005_enforce-adr-evidence-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093931_adrgate005_enforce-adr-evidence-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115901
- **Related target files**: tools/check_adr_reference.py