## Goal

Apply the display policy to `/config`: redact the LLM endpoint URL and replace configured absolute
paths with logical identifiers (REQ-005 — normal CLI output is safe for terminal capture).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `llm_url` is printed raw at `scripts/agent/commands/cmd_config_display.py` line 43 and
  `approval_protected_paths` at lines 88-89; these are the only credential- or path-bearing values in
  this module's output.
- Step 3b correction: the assumption is incomplete. `memory_jsonl_dir` (line 148), `rag_db_path` and
  `session_db_path` (lines 214-215) also print absolute paths. Per the confirmed decision these three
  are rendered through `redact_path` as well, so the module's whole output satisfies AC-1.
- No overlap with a sibling Plan on this file.

## Design decisions

- Redaction happens at the display boundary (Plan D5): the config model itself is not modified, so
  runtime consumers keep the real values.
- Path values are replaced by the logical identifier from `redact_path` (document 01), not masked
  with `***MASKED***`, so the operator can still identify which entry is configured.

## Alternatives considered

- Masking paths as `***MASKED***` — rejected: it removes the operator's ability to tell entries
  apart, which the Plan's logical-identifier policy preserves.

## Implementation
### Target file
`scripts/agent/commands/cmd_config_display.py`
### Procedure
- Wrap the `llm_url` pair value with `redact_url` (document 01).
- Map each `approval_protected_paths` entry through `redact_path` (document 01) before joining.
- Map `memory_jsonl_dir`, `rag_db_path`, and `session_db_path` through `redact_path` (document 01),
  keeping the `"(not set)"` placeholder for an empty value.

### Method
- `pairs` construction at line 43 uses `redact_url(str(ctx.cfg.llm.llm_url))`; the join at lines
  88-89 uses `", ".join(redact_path(p) for p in ctx.cfg.approval.approval_protected_paths)`.
- Lines 148 and 214-215 use `redact_path(...)` on the value before it enters the `pairs` list.

### Details
- Other displayed settings are unchanged; only URL and path forms are transformed.

### Companion test files
- `tests/agent/commands/test_agent_cmd_config.py`
  - Procedure: add display-policy assertions for the URL and path forms.
  - Validation: `uv run pytest tests/agent/commands/test_agent_cmd_config.py`.

## Compatibility considerations

- Display text changes only; the config model and its consumers are untouched.

## Security considerations

- AC-1 boundary for `/config`, which is the surface most often screen-shared.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/commands/test_agent_cmd_config.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- A configured URL with credentials renders without userinfo, query, or fragment, and each protected
  path renders as a logical identifier rather than an absolute path.

## Out of Scope

- The common redaction helpers themselves (document 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-022000 | llm_url via redact_url, protected_paths via redact_path; Step 3b: memory_jsonl_dir/rag_db_path/session_db_path also print absolute paths and are redacted per confirmed decision |
| 2 | Add or update tests per Validation plan | Completed | — | 20261127-022000 | companion `tests/agent/commands/test_agent_cmd_config.py` 3 tests added (URL, protected paths, memory/DB paths); 51 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-095216 | 20261127-095216 | gates pass; mypy clean on both files; bandit clean; changed files: scripts/agent/commands/cmd_config_display.py, tests/agent/commands/test_agent_cmd_config.py; awaiting end-of-batch full suite gates pass; mypy clean on both files; bandit clean; changed files: scripts/agent/commands/cmd_config_display.py, tests/agent/commands/test_agent_cmd_config.py; awaiting end-of-batch full suite |

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
- **Requirement ID**: `REQ-005` (normal CLI output carries no credential or absolute path)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `scripts/agent/commands/cmd_config_display.py`, `tests/agent/commands/test_agent_cmd_config.py`