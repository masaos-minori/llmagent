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
- The record carries the root-relative POSIX path when it lands in the DTO, never an absolute
  path, per the audit rule owned by the server-boundary plan. Re-verified 20261128: the parse-stage
  record itself carries no path at all; the path appears only in the indexer's `FileOutcome`, where
  `_outcome_path()` produces the root-relative form.

## Design decisions
- The warning is a reason code, not a message, so a count can be reported without a path.
- `parse_markdown()` gains a third return value for the warning record; the 16 unpacking test call
  sites (2 in `tests/mcp_servers/mdq/test_parser.py`, 14 in `tests/mcp_servers/mdq/test_mdq_service.py`
  — re-counted 20261128; the recorded 13 was stale) are rewritten in the same cycle as the contract
  change, together with the production call site in `scripts/mcp_servers/mdq/indexer.py`.
- The warning record is a plain `dict[str, Any]` whose keys are exactly the three FileOutcome field
  names (`warning_codes`, `warning_count`, `char_count`), so the indexer spreads it into the outcome
  with `**frontmatter_warning` and no new model or parser-level type is introduced. The record carries
  no path at all; the path the DTO eventually holds is the indexer's root-relative `_outcome_path`.

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
- `_try_parse_frontmatter()` Lines 173-212: at the `except yaml.YAMLError:` branch (Line 199 in the
  pre-change file) keep `fm_data = None` and record reason code `invalid_frontmatter` (new) with a
  count of 1 for the failed parse. The helper's return tuple gains a third element carrying the codes.
- `parse_markdown()` Lines 50-170: return the warning record as the third value of the tuple, and
  report `len(content)` from Line 67 as `char_count` (new) so the caller can state the decoded
  character count separately from the byte gate measured in `scripts/mcp_servers/mdq/indexer.py`.
  `parse_markdown()` also logs a `logger.warning` line naming the offending file when a code is
  recorded; the audit rule applies to persistent output, not to logs.
- Module docstring: state that the warning record carries no absolute path.
- Production call site: `scripts/mcp_servers/mdq/indexer.py` Line 195 (the procedure recorded Line 89;
  the seq 02 implementation moved it) unpacks the three-value tuple and spreads the record into the
  `indexed` and `skipped_no_content` FileOutcome records.

### Companion test files
- `tests/mcp_servers/mdq/test_parser.py`
  - Procedure: keep `test_invalid_yaml_syntax_falls_back_to_empty_tags` (Line 39) unchanged as the
    fallback characterization, and add the structured warning and its count case.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_parser.py` — invalid frontmatter still
    returns empty tags and now produces a warning code and a count with no absolute path.

## Compatibility considerations
- The return contract changes from a two-value tuple to a three-value tuple at 16 unpacking test
  call sites (2 + 14) plus the production call site in `scripts/mcp_servers/mdq/indexer.py` Line 195;
  one further test call site does not unpack (`test_mdq_service.py` Line 280, inside
  `pytest.raises`) and is unaffected. All sites are rewritten in the same cycle as the change.
- No existing assertion is weakened: the fallback test stays as written.

## Security considerations
- The warning record carries no absolute path, which is the audit rule the server-boundary plan
  defines; no redaction is re-implemented here.

## Rollback considerations
- N/A: revert the commit — the change is confined to one function and one return contract.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_parser.py`
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports` and
  `uv run python tools/check_module_size.py` (11189 B of 24576 B used as of 20261128).

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
| 1 | Add the structured warning and count test (companion) | Completed | 2026-11-28 | 2026-11-28 | Three new cases in TestFrontmatterInvalidYamlSyntax: structured warning code+count with no path in the record, empty record for a valid file, char_count == decoded characters (< byte count for Japanese+emoji). Written red first: 5 failed before the parser change. |
| 2 | Record `invalid_frontmatter` (new) in the existing fallback branch | Completed | 2026-11-28 | 2026-11-28 | except yaml.YAMLError branch appends invalid_frontmatter to a new warning_codes list; helper returns (tags, next_index, warning_codes). parse_markdown logs a logger.warning naming the file when a code is recorded. |
| 3 | Report the decoded-character count and extend the return tuple | Completed | 2026-11-28 | 2026-11-28 | Third tuple element is a dict[str, Any] keyed warning_codes/warning_count/char_count (char_count = len(content)); indexer.py:195 spreads it via **frontmatter_warning into the indexed and skipped_no_content FileOutcome records. Refresh reuses _index_single_file, so there is one parse site only. |
| 4 | Rewrite the 16 unpacking test call sites (2 + 14, re-counted 20261128) | Completed | 2026-11-28 | 2026-11-28 | test_parser.py 2 sites + test_mdq_service.py 14 sites (recorded 11 was stale; test_mdq_service.py grew since the plan). The pytest.raises site at test_mdq_service.py:280 does not unpack and stays. This completes step 4 of procedure seq 12 early; recorded there. |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-28 | 2026-11-28 | Gates: ruff format/check, mypy (20 files), lint-imports 6 kept 0 broken, bandit clean, check_module_size OK (parser.py 11189 B, indexer.py 24292 B). Targeted: parser+service+incremental_refresh+internal_failures+scan_semantics = 138 passed; whole tests/mcp_servers/mdq/ + test_mdq_audit.py = 525 passed (was 522). |

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
