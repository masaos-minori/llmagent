# Procedure: correct the get_resume_position docstring

## Goal

Make the `get_resume_position` docstring describe exactly what the function returns (Plan REQ-001..003).

## Scope

- Modify only `scripts/eventbus/delivery_repo.py`.
- In scope: the docstring body and `Returns` section of `get_resume_position`.
- Out of scope: any code, signature or first-line change, other functions, docs.

## Assumptions

- Path A change (one file, docstring only).
- The first docstring line stays byte-identical so the generated API reference row (which quotes only the first line) needs no regeneration.
- The existing tests in `tests/eventbus/test_eventbus_restart_resume.py` cover no offset, an unacked event below the offset (including one with no delivery record) and the all-acked case.

## Design decisions

- Use the offsets document's terms (lowest_unacked_seq and stored_offset + 1) and the code's own definition of unacked.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/eventbus/delivery_repo.py`

### Procedure

- Replace the body after the first line with: `Return the first seq to deliver on reconnect. Return 0 when the consumer has no stored offset. Otherwise return the lowest seq at or below the stored offset that this consumer has not acknowledged (a consumer_delivery row with acked = 0, or no row at all), or stored_offset + 1 when every such event is acknowledged.`, wrapped to 88 columns.
- Remove the "Returns the maximum of" list and the sentence that follows it; keep a one-sentence note that this lets a reconnecting consumer skip already-acknowledged events without skipping an unacknowledged one.
- Keep the `Args` section; change `Returns` to `Resume position (int): 0 without an offset row, the lowest unacked seq, or stored_offset + 1.`

### Method

Edit the docstring text only; do not touch the body, signature or comments.

### Details

- `seq` starts at 1, so the existing `if row and row[0]:` truthiness test is unaffected (not changed here).

## Compatibility considerations

- No behavior change.

## Security considerations

- No security impact.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/delivery_repo.py`; `uv run ruff check scripts/eventbus/delivery_repo.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/delivery_repo.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |
| 4 | `uv run python tools/check_docstrings.py`; `uv run python tools/generate_reference_table.py --check`; `uv run python tools/check_docs_consistency.py --domain eventbus` | No finding; no drift |

## Completion criteria

- The docstring matches all three outcomes, defines unacked as the code does and contains no mention of a maximum.
- `git diff` for the file touches only docstring lines; the first docstring line is unchanged.

## Out of Scope

- Behavior or signature changes, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 2026-10-28 | docstring rewritten per procedure; note: procedure Details mentions 'if row and row[0]' but actual code uses 'if row is None' (body untouched) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 2026-10-28 | pytest 411 passed; ruff/mypy/lint-imports/bandit/size/docstring/reference-table/docs-consistency clean |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (three outcomes; definition of unacked; no behavior change)
- **Source issue**: issues/20261027-155852_ebresume009_fix-resume-position-docstring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094951_ebresume009_fix-resume-position-docstring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120349
- **Related target files**: scripts/eventbus/delivery_repo.py