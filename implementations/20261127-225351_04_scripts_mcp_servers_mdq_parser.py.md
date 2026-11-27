# Implementation Procedure — scripts/mcp_servers/mdq/parser.py

## Goal

Make invalid frontmatter observable without making it blocking: a structured warning record with a
stable code and a count, and a decoded-character count that keeps the byte gate and the character
limit distinct.

## Scope
**Release unit**: N/A: not part of a release unit (Phase 6 is not grouped in one; the
decoded-character reporting belongs to the `byte-limit-key-rename` unit through REQ-004)

Requirements implemented: REQ-004 (the byte gate and the character limit are distinct), REQ-007
(structured `invalid_frontmatter` (new) warning codes and counts).
Acceptance criteria: AC-3, AC-6.

## Assumptions
- The permissive fallback stays: invalid frontmatter still parses to empty tags and does not
  interrupt the rest of the file. `tests/mcp_servers/mdq/test_parser.py::test_invalid_yaml_syntax_falls_back_to_empty_tags`
  (Line 39) is the characterization that pins it.
- The warning record is the DTO defined by procedure seq 01; this document fills its
  `warning_codes` (new), `warning_count` (new), and `char_count` (new) fields and does not define a
  new model.
- The record carries the root-relative POSIX path, never an absolute path, per the audit rule owned
  by the server-boundary plan.

## Design decisions
- The warning is a reason code, not a message, so a count can be reported without a path.
- `parse_markdown()` gains a third return value for the warning record; the 13 unpacking test call
  sites (2 in `tests/mcp_servers/mdq/test_parser.py`, 11 in `tests/mcp_servers/mdq/test_mdq_service.py`)
  are rewritten in Phase 1 before the contract change lands.

## Alternatives considered
- Logging the YAML failure only: rejected, because a log line is not a count and cannot be reported
  in the tool response without a path.
- Raising on invalid YAML: rejected, because the fallback is pinned behavior and the requirement is
  explicitly non-blocking.

## Implementation
### Target file
`scripts/mcp_servers/mdq/parser.py`

### Procedure
Keep the fallback, record the failure as a structured warning, and report the decoded-character
count.

### Method
The existing `except` branch becomes a warning-producing branch; the return tuple gains one element.
No new module-level name is introduced in this file.

### Details
- `_try_parse_frontmatter()` Lines 173-212: at Line 199 keep `fm_data = None` and record reason code
  `invalid_frontmatter` (new) with a count of 1 for the failed parse.
- `parse_markdown()` Lines 50-170: return the warning record as the third value of the tuple, and
  report `len(content)` from Line 67 as `char_count` (new) so the caller can state the decoded
  character count separately from the byte gate measured in `scripts/mcp_servers/mdq/indexer.py`.
- Module docstring: state that the warning record carries no absolute path.

### Companion test files
- `tests/mcp_servers/mdq/test_parser.py`
  - Procedure: keep `test_invalid_yaml_syntax_falls_back_to_empty_tags` (Line 39) unchanged as the
    fallback characterization, and add the structured warning and its count case.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_parser.py` — invalid frontmatter still
    returns empty tags and now produces a warning code and a count with no absolute path.

## Compatibility considerations
- The return contract changes from a two-value tuple to a three-value tuple at 17 call sites
  (13 unpacking test call sites plus the production call site in `scripts/mcp_servers/mdq/indexer.py`
  Line 89); the call sites are rewritten in Phase 1.
- No existing assertion is weakened: the fallback test stays as written.

## Security considerations
- The warning record carries no absolute path, which is the audit rule the server-boundary plan
  defines; no redaction is re-implemented here.

## Rollback considerations
- N/A: revert the commit — the change is confined to one function and one return contract.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_parser.py`
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports` and
  `uv run python tools/check_module_size.py` (9551 B of 24576 B used).

## Completion criteria
- Invalid frontmatter remains non-blocking and produces a structured warning code and a count.
- The decoded-character count is reported, so the byte gate and the character limit are distinct
  numbers in the outcome record.
- The warning record contains no absolute path.

## Out of Scope
- The DTO definition and the closed reason-code set (procedure seq 01).
- The byte gate itself, which is enforced in `scripts/mcp_servers/mdq/indexer.py` (seq 02).
- Adding a decoded-character configuration key (UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the structured warning and count test (companion) | Pending | — | — | REQ-007, AC-6 |
| 2 | Record `invalid_frontmatter` (new) in the existing fallback branch | Pending | — | — | REQ-007, Phase 6 |
| 3 | Report the decoded-character count and extend the return tuple | Pending | — | — | REQ-004, AC-3 |
| 4 | Rewrite the 13 unpacking test call sites | Pending | — | — | Phase 1 |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (byte gate and character limit are distinct), REQ-007 (structured
  `invalid_frontmatter` (new) warnings and counts)
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-225351
- **Related target files**: `scripts/mcp_servers/mdq/parser.py`, `tests/mcp_servers/mdq/test_parser.py`
