# Implementation Procedure — scripts/mcp_servers/mdq/mdq_models.py

## Goal

Define the shared outcome vocabulary the other procedures consume: the per-file result DTO, its
closed status and reason-code sets, the warning-count field, the grep context fields, and the
byte-unit configuration field.

## Scope
**Release unit**: per-file-outcome-and-counters (the size-limit rename in this file is the part
that belongs to release unit `byte-limit-key-rename`)

Requirements implemented: REQ-001 (per-file result DTO with the closed status vocabulary),
REQ-003 (counter keys that name their unit), REQ-004 (byte-unit configuration field),
REQ-006 (grep context fields), REQ-007 (structured warning codes and counts).
Acceptance criteria: AC-1, AC-2, AC-3, AC-5, AC-6.

## Assumptions
- Definitions only: this file declares the contract; the behaviour that fills it is in
  `scripts/mcp_servers/mdq/indexer.py`, `scripts/mcp_servers/mdq/db_grep.py`,
  `scripts/mcp_servers/mdq/parser.py`, and `scripts/mcp_servers/mdq/mdq_service.py`.
- `line_number` keeps its name and its new definition — the first stored content line
  (`start_line + 1 + k`), per the owner decision recorded on 20261127 (UNK-03).
- Existing counter keys keep their path-level meaning; the file-level counters are added as new
  keys (UNK-06), so `tests/mcp_servers/test_mdq_audit.py` is unaffected.
- No decoded-character key is added (UNK-02): the byte gate is the enforced limit, and the
  character limit stays a documented decision.
- The DTO carries a root-relative POSIX path, never an absolute path.

## Design decisions
- `FileOutcome` (new) is a Pydantic model, matching the other response models in this file, so the
  DTO is validated at construction instead of assembled by callers.
- Statuses and reason codes are module-level closed sets, `FILE_OUTCOME_STATUSES` (new) and
  `FILE_OUTCOME_REASON_CODES` (new); a value outside a set is a construction error, not a runtime
  string.
- `GrepDocMatch` gains `context_before_lines` (new) and `context_after_lines` (new) as lists, so
  the requested context becomes part of the result instead of a local variable.
- `RefreshSummary` is defined in `scripts/mcp_servers/mdq/indexer.py` line 42, so its new keys are
  added by that procedure, not here; this file adds the matching keys to `IndexPathsMetadata`.

## Alternatives considered
- TypedDict for the DTO, the style `IndexPathsMetadata` uses: rejected because the status and the
  reason code must be validated against a closed set, which a TypedDict cannot enforce.
- Reinterpreting `skipped_count` and `failed_count` as file-level counters: rejected per UNK-06,
  because `tests/mcp_servers/test_mdq_audit.py` pins their path-level meaning.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_models.py`

### Procedure
Add the DTO and the two closed sets, add the grep context fields, add four file-level counter keys,
rename the size-limit field and its rule key. No default is changed.

### Method
Model definitions only — no behaviour. Each addition is a field or a module-level constant; the
rename is a field name change that keeps the same constraint.

### Details
- `MdqConfig` Line 142: rename `max_file_chars` to `max_file_bytes` (new), keeping `Field(gt=0)`.
  The field declares no default: `MdqConfig` requires every key (REQ-007), and
  `tests/mcp_servers/mdq/test_mdq_config.py` Line 68 asserts the value from an explicit payload, not
  a model default.
- `MdqConfig` Line 122 (`_CONFIG_FIELD_RULES`): rename the rule key `"max_file_chars"` to
  `"max_file_bytes"` in the same step, because `_apply_declared_rule` (Line 165) looks the rule up by
  field name, so renaming only the field raises `KeyError` at validation.
- `MdqConfig` Lines 150-151: `context_before` and `context_after` carry no default here. The value `2`
  is the `GrepDocsRequest` default (Lines 241-242), and honoring an explicit zero is the service's
  `is None` check (REQ-006, `scripts/mcp_servers/mdq/mdq_service.py`), not a default change, so this
  document changes no default.
- `GrepDocMatch` Lines 325-331: add `context_before_lines` (new) and `context_after_lines` (new).
  `line_number` keeps its name and takes the first-stored-content-line definition
  (`start_line + 1 + k`).
- `IndexPathsMetadata` Lines 389-396: add `discovered_file_count` (new), `committed_file_count` (new),
  `skipped_file_count` (new), `failed_file_count` (new).
- New `FileOutcome` (new) model with fields `path`, `status`, `reason_code`, `warning_codes` (new),
  `warning_count` (new), and `char_count` (new) — the decoded-character count that keeps the byte
  gate and the character limit distinct (REQ-004).
- New closed sets: `FILE_OUTCOME_STATUSES` (new) — `indexed` (new), `skipped_unchanged` (new),
  `skipped_size_limit` (new), `skipped_no_content` (new), `failed` (new);
  `FILE_OUTCOME_REASON_CODES` (new) — `unchanged` (new), `size_limit` (new), `no_content` (new),
  `file_disappeared` (new), `write_failure` (new), `invalid_frontmatter` (new), enumerated from the
  codes the sibling procedures name (seq 02 size gate, the `FileNotFoundError` and `sqlite3.Error`
  branches, seq 04 frontmatter warning). Closed-set membership is enforced at construction by a
  field validator on `FileOutcome`, so the sets stay a runtime vocabulary and the model cannot accept
  a value outside them.

## Compatibility considerations
- The field rename breaks `tests/mcp_servers/mdq/test_mdq_config.py` Lines 40, 68, and 103,
  `scripts/mcp_servers/mdq/mdq_security_validation.py` Line 48, `config/mdq_mcp_server.toml`
  Line 29, `scripts/mcp_servers/mdq/mdq_service.py` Line 75, `scripts/mcp_servers/mdq/indexer.py`
  Lines 80, 82, and 85, and `tests/mcp_servers/mdq/test_mdq_service.py` Lines 130, 137, and 151; all
  are rows of this Plan and must change in the same commit (release unit `byte-limit-key-rename`).
- The rename also breaks `tests/mcp_servers/mdq/_startup.py` Line 29. `MdqConfig` has no field
  default, so `make_startup()` raises `ValidationError` once the key is renamed, and the shared
  fixture is consumed by 28 test files. `_startup.py` is not a row of this Plan, and
  `tools/amend_plan.py` refuses to add a target file to an archived Plan, so the key rename there is
  carried as an explicit user-approved exception recorded in procedure seq 13, which edits the
  fixture in the same release-unit commit.
- New keys are additive: `scripts/mcp_servers/mdq/mdq_server.py` reads the counters with
  `.get(..., 0)`, so the audit detail builder is unaffected.
- `GrepDocMatch` gains fields, which is a visible output change for `grep_docs`; the pinned
  assertion in `tests/mcp_servers/mdq/test_db_grep.py` Line 108 is rewritten by that row.

## Security considerations
- No authentication, path authorization, or limit semantics change here. `max_file_bytes` (new)
  remains a hard bound (`gt=0`) enforced by the indexer.
- The DTO carries a root-relative POSIX path, which keeps warning records inside the audit rule
  that persistent output carries no absolute path.

## Rollback considerations
- Revert this file as part of the release-unit commit. Consumers that already write the new keys
  (`indexer.py`, `db_grep.py`, `parser.py`) must be reverted first, otherwise they construct models
  that no longer declare the fields.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py tests/mcp_servers/mdq/test_db_grep.py`
  — the DTO, the reason codes, the byte field, and the match model.
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`,
  `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll`,
  `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`
  (14087 B of 24576 B used at the time of the 20261128 adversarial verification).

## Completion criteria
- The status and reason-code sets are closed and enumerable, and no caller can construct a DTO with
  a value outside them.
- The match model carries the context it was asked for, and the counter keys name distinct units.
- The configuration field names its unit, and the declared rule key matches the renamed field.

## Out of Scope
- The runtime behaviour that produces the DTO statuses, the counters, and the warning records.
- The `RefreshSummary` keys, which are added in `scripts/mcp_servers/mdq/indexer.py`.
- Adding a decoded-character configuration key (UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `FileOutcome` (new) and the two closed sets | Completed | — | 20261128-131946 | REQ-001, REQ-007 |
| 2 | Add the `GrepDocMatch` context fields (`line_number` keeps its name) | Completed | — | 20261128-131946 | REQ-006, AC-5 |
| 3 | Add the four file-level counter keys to `IndexPathsMetadata` | Completed | 2026-11-28 | 2026-11-28 | Completed. 3b: line numbers re-verified (MdqConfig 142, rule key 122, GrepDocMatch 325-331, IndexPathsMetadata 389-396); removed the false context-default and Field(default=100000) claims; the rule key must be renamed with the field or _apply_declared_rule raises KeyError; match_line_number row removed because the Plan keeps the field name (UNK-03). |
| 4 | Rename `max_file_chars` to `max_file_bytes` (new) in the field and in `_CONFIG_FIELD_RULES` | Completed | 2026-11-28 | 2026-11-28 | Completed. 3b correction recorded. Recorded the user-approved tests/mcp_servers/mdq/_startup.py companion exception in seq 13; the rename lands in the same release-unit commit as seq 06/07/08/13. |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-28 | 2026-11-28 | Gates on the changed file pass: ruff format/check, mypy, lint-imports (6 kept), bandit (0 findings on mdq_models.py), check_module_size OK (not a baselined module). Targeted tests: test_db_grep.py 13 passed; test_mdq_config.py 5 failures, the release-unit allowed red state attributable to the shared fixture rename (seq 13) and config key (seq 08). Full suite + diff-cover run once at batch end. |

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
- **Requirement ID**: REQ-001 (per-file result DTO), REQ-003 (counters that name their unit),
  REQ-004 (byte-unit configuration field), REQ-006 (grep context fields), REQ-007 (warning codes
  and counts)
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-225351
- **Related target files**: `scripts/mcp_servers/mdq/mdq_models.py`
