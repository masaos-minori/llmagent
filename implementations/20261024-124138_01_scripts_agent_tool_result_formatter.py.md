## Goal

Make `mask_args` mask configured argument keys at any depth inside nested dicts and lists without
mutating the input, and state the logging-only boundary in its docstring (`REQ-002`, `REQ-003`,
`REQ-005`).

## Scope

- `scripts/agent/tool_result_formatter.py`: add the private recursive helper `_mask_value` (new),
  rewire `mask_args` (`:42-49`) to delegate to it, and rewrite the `mask_args` docstring.
- No other function in the file changes. No call site changes: the four sinks
  (`tool_runner.py:254`, `tool_audit.py:46`, `tool_audit.py:157`, `tool_approval.py:222`) already
  import and call `mask_args`.

## Assumptions

- Tool arguments are JSON-derived containers (`dict` / `list` / scalars), acyclic and bounded by tool
  argument parsing, so recursive traversal terminates and is cheap (Plan `Assumptions`, `:172-173`).
- The measured file size is 4095 B / 104 lines, not the 3458 B recorded in the Plan body; the module
  size gate is `DEFAULT_LIMIT = 20480` in `tools/check_module_size.py`, and this file has no entry in
  `tools/check_module_size_baseline.txt`. See `#### Corrections from re-measurement and owner answers`
  in `plans/20261023-072425_plan.md`.
- `_mask_value` (new) is `_`-prefixed, so `tools/generate_reference_table.py` skips it and it never
  appears in `docs/23_agent/agent_13_reference-api-generated.md`. Only the `mask_args` docstring first
  line affects the generated table.

### Procedure-local findings

- The Plan's recorded anchors for this row are stale (`mask_args` at `:27-32`, file 3458 B, call sites
  `tool_runner.py:204` and `tool_approval.py:213`); the measured anchors are used throughout this
  document. The correction is recorded in `plans/20261023-072425_plan.md`.
- `BLK-001` is resolved: the generated-document ceiling lives in `tools/check_docs_structure.py:114`,
  a file no row of this Plan targets. That edit is traceable through the Plan's Blocker Log and the
  `20261024-061024_05` procedure record.

## Design decisions

- One recursive copy-on-write helper owned by `mask_args` inside this file (Plan Design,
  `Recursive helper, copy-on-write`): all four sinks already call `mask_args`, so this single function
  is the only place that propagates nesting coverage without touching the runner, approval, or audit
  modules. No new imports and no new module, so the import-layer contract in `skills/DESIGN.md`
  Shared Vocabulary is untouched.
- Containers are rebuilt unconditionally rather than reusing the current comprehension, so the input
  argument tree is never mutated and the same `args` object continues to flow to approval, planning,
  and execution (`AC-5`).
- The `mask_args` docstring first line is fixed to the wording measured against the generated-table
  size gate: `Return a copy of args with masked_fields keys replaced by '***' at any depth.` (77
  characters). The accepted ceiling for `docs/23_agent/agent_13_reference-api-generated.md` is
  24972 B (`tools/check_docs_structure.py:114`, Plan `BLK-001`), which the regenerated file meets with
  0 B to spare; a longer first line invalidates that accepted value.

## Alternatives considered

- Masking at the four call sites or inside the audit writers: rejected. It duplicates the traversal in
  every sink and leaves `mask_args` as a top-level-only trap for the next caller.
- Mutating the argument dict in place: rejected. The same object is handed to approval, planning, and
  execution (`tool_runner.py:254`), so in-place redaction would corrupt the values the tool runs with
  and break `AC-5`.
- Keeping the existing comprehension and recursing only into dict values: rejected. It misses
  list-of-dicts argument shapes such as `edits` (`scripts/mcp_servers/file/write_tools.py:50`), which is
  the verified defect in `REQ-002`.
- A longer docstring first line that explains the boundary in the summary line: rejected. It changes
  the generated `mask_args` row length and requires re-measuring and re-accepting the `agent_13`
  ceiling recorded in `tools/check_docs_structure.py:114`.

## Implementation

### Target file

`scripts/agent/tool_result_formatter.py` — `mask_args` at `:42-49`, inside the `Tool argument masking
and previews` section.

### Procedure

1. Add `_mask_value` (new) immediately above `mask_args`.
2. Replace the body of `mask_args` with a delegation to `_mask_value(args, masked_fields)`.
3. Rewrite the `mask_args` docstring: the measured 77-character first line, a blank line, then the
   logging-only boundary sentence.
4. Leave `build_github_preview`, `_preview_file_write`, `_preview_file_path`, `_preview_shell_cmd`, and
   `build_preview` untouched.

### Method

- `_mask_value(value: object, masked_fields: list[str]) -> object`: for a `dict`, build a new dict
  whose keys in `masked_fields` map to `"***"` and whose other values are the recursive result; for a
  `list`, build a new list with each item recursed; every other value is returned as-is.
- `mask_args(args: dict[str, object], masked_fields: list[str]) -> dict[str, object]` keeps its
  signature, return type, and the `key in masked_fields` comparison unchanged.
- Masking replaces values; it never removes keys, so `_extract_resource_scope`
  (`scripts/agent/tool_audit.py:26`, called at `:47` and `:158`) keeps seeing the same key set at the
  top level.

### Details

- Helper budget: at most 12 lines and complexity rank A (target ≤ A(6)); the file's worst block must
  remain the pre-existing `build_github_preview` B(9) (`AC-7`, `AC-8`).
- Docstring convention: one summary line, a blank line, then the boundary sentence — the shape
  `uv run python tools/check_docstrings.py` enforces.
- The boundary sentence states that masking is applied before logging and audit writes and is not
  applied to the interactive approval preview built by `build_preview` (`:82`).

## Compatibility considerations

- Top-level behavior is byte-compatible for flat arguments, so `TestMaskArgs` (6 tests,
  `tests/agent/test_tool_result_formatter.py:54-76`) and
  `tests/agent/test_tool_approval_preflight.py::test_masked_fields_applied_to_args` (`:417-430`) pass
  with zero edits (`AC-3`).
- Non-matching keys, scalars, and non-string values are preserved unchanged
  (`test_non_string_values_preserved`, `:75`).
- For a deployment that already configures a key name which appears at depth, audit rows change from
  raw values to `***`. That is the intended fix (`REQ-002`); the repo default `["file_content"]`
  matches no current argument key, so no shipped configuration changes behavior
  (`config/agent.toml:98`, `scripts/agent/config_dataclasses.py:182`,
  `scripts/agent/config_section_builders.py:204-205`).
- No public API, import, or signature changes; `scripts/agent/tool_approval.py`,
  `scripts/agent/tool_audit.py`, and `scripts/agent/tool_runner.py` are read-only references for this
  row.

## Security considerations

- This is the redaction fix: after this change a configured key is redacted wherever it appears in the
  argument tree, which is what the audit sinks write (`tool_audit.py:58` and `:169` pass the masked
  dict as `args_preview`).
- Redaction is not redaction of the preview: the interactive approval preview stays unmasked by
  decision (`REQ-001`), and `tests/agent/test_tool_approval_risk.py` `T-3` pins that boundary.
- Recursive traversal has no depth limit. It is safe for the assumption above (JSON-derived, acyclic
  tool arguments); a cyclic or pathologically deep container would raise `RecursionError` rather than
  loop. Recorded as a known bound, not a defect, because no tool argument path produces such a value.

## Rollback considerations

- Revert the two hunks in this file (`_mask_value` (new) and the `mask_args` body/docstring). No call
  site needs reverting.
- A revert also desyncs `docs/23_agent/agent_13_reference-api-generated.md`, so it must be followed by
  `uv run python tools/generate_reference_table.py --type agent` and a re-check of
  `tools/check_docs_structure.py`; the accepted 24972 B ceiling recorded at `:114` describes the
  post-change document and must be re-accepted if the docstring is reverted.

## Validation plan

- `uv run pytest tests/agent/test_tool_result_formatter.py -v` — existing `TestMaskArgs` unchanged, new
  nesting tests from `implementations/20261024-124138_02_tests_agent_test_tool_result_formatter.py.md`
  pass.
- `uv run pytest tests/agent/test_tool_approval_preflight.py tests/agent/test_tool_approval_risk.py -v`
  — the audit-path and preview-boundary rows from `_03` and `_04`.
- `uv run radon cc scripts/agent/tool_result_formatter.py -s -n C` — no block at rank C or worse; worst
  remains `build_github_preview` B(9).
- `uv run python tools/check_module_size.py` — "ALL OK"; file stays far below `DEFAULT_LIMIT`.
- `uv run python tools/check_docstrings.py` — passes after the docstring edit.
- `uv run ruff format scripts/`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml
  -ll`, `uv run vulture scripts/ --min-confidence 80`, `uv run semgrep --config=p/python scripts/`.
- `uv run python tools/generate_reference_table.py --type agent` then `--check` — exits 0 only after
  `implementations/20261024-124138_06_docs_23_agent_agent_13_reference-api-generated.md.md` is done.

## Completion criteria

- `AC-1`: nested masking returns `"***"` at any depth and leaves non-matching keys and scalars
  untouched.
- `AC-2`: the `tool_approval` audit payload contains no nested sensitive value (verified by the `_03`
  test).
- `AC-3`: `TestMaskArgs` and the existing audit masking test pass with zero edits;
  `tests/agent/test_tool_audit.py` and `tests/agent/test_config_builders.py` pass unmodified.
- `AC-5`: `args` is deep-equal to its pre-call snapshot after `mask_args`.
- `AC-7`, `AC-8`: generated reference `--check` exits 0 and the full `rules/toolchain.md` sequence
  passes with no new finding.

## Out of Scope

- Changing the default `masked_fields` value: filed as
  `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`.
- Bounding the size of `args_preview` in audit events: filed as
  `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`.
- Masking the interactive approval preview, and any change to `build_preview` or the preview helpers.
- The `masked_fields` documentation text: owned by
  `implementations/20261024-124138_05_docs_23_agent_agent_08_03_configuration-tools-memory.md.md`.


## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_mask_value` (new), rewire `mask_args`, rewrite its docstring within the measured first-line length | Pending | — | — | Docstring first line fixed to the 77-character measured wording |
| 2 | Confirm the `_02`, `_03`, `_04` test rows pass against the change | Pending | — | — | `AC-1`, `AC-2`, `AC-3`, `AC-5` |
| 3 | Run the lint / type / security / architecture / complexity / docstring gates | Pending | — | — | `rules/toolchain.md` |
| 4 | Confirm `generate_reference_table.py --check` exits 0 after the `_06` regeneration | Pending | — | — | `AC-7`; depends on the accepted 24972 B ceiling |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | N/A: the three issues for this Plan were created by the Plan pass, not by this row |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-005`
- **Source issue**: `issues/20261021-093421_tool005-masked-args-not-applied-to-previews-or-nesting.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-072425_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-124138
- **Related target files**: `scripts/agent/tool_result_formatter.py`
