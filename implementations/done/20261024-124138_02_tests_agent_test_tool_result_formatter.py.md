## Goal

Add the unit coverage for recursive masking and the input-not-mutated contract (`T-1`) to
`tests/agent/test_tool_result_formatter.py`, while keeping every existing test byte-identical
(`REQ-002`, `REQ-003`, `REQ-004`).

## Scope

- `tests/agent/test_tool_result_formatter.py`: new tests inside the existing `TestMaskArgs` class
  (`:54-76`).
- No change to `TestBuildPreview` (`:80+`) or any other class in this file, and no change to the
  import block at the top of the file.

## Assumptions

- `mask_args` keeps its signature `mask_args(args: dict[str, object], masked_fields: list[str]) ->
  dict[str, object]`, so the new tests import nothing new; the existing import block already imports
  `mask_args` and `build_preview` from `scripts/agent/tool_result_formatter.py`.
- This row is executed against the implementation in
  `implementations/20261024-124138_01_scripts_agent_tool_result_formatter.py.md`; the nesting tests
  cannot pass before that row lands.

### Procedure-local findings

- The Plan records `TestMaskArgs` at `:53-76`; the measured range is `:54-76` (6 tests). Recorded in
  the Plan's corrections subsection.
- The Plan's `T-1` example masks `file_content`. That key name matches no real tool argument
  (`issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`); the
  tests here keep one `file_content` case for continuity with `AC-1` and add a `content` case for the
  real shape.

## Design decisions

- New cases go inside `TestMaskArgs` rather than a new class, so the top-level suite
  (`AC-3`: "all 6 tests, zero edits") and the nesting suite are read together as one behavior
  contract.
- `repr()`/deep-equality snapshots are used for the no-mutation assertion instead of identity checks,
  because the contract is about the caller's data, not about object identity.
- Key names in the new cases use both a neutral name (`secret`) and a real argument key (`content`),
  so the suite documents what masking is actually for.

## Alternatives considered

- A parametrized single test over several container shapes: rejected. Each shape fails for a different
  reason, and separate named tests make a regression point to the shape that broke.
- Testing through `audit_approval()` only: rejected. That path is `T-2` in
  `implementations/20261024-124138_03_tests_agent_test_tool_approval_preflight.py.md`; the unit path
  must fail independently of the audit writer.
- Asserting the returned object is a different object (`is not args`): rejected as the primary check.
  A copy is an implementation choice; deep-equality of the untouched input is the contract (`AC-5`).

## Implementation

### Target file

`tests/agent/test_tool_result_formatter.py` — append to `TestMaskArgs` after
`test_non_string_values_preserved` (`:75-76`).

### Procedure

1. Keep the 6 existing tests byte-identical.
2. Append the nesting cases listed under Details.
3. Append the snapshot/no-mutation case last, so it reads as the contract the others rely on.

### Method

- Build the argument trees with literals, call `mask_args`, and compare the whole result with `==`.
- For the no-mutation case, take a `repr()` snapshot of `args` before the call and compare it after the
  call, then also assert the masked result is not the same values.

### Details

- `test_masks_nested_dict` (new): `{"a": {"file_content": "s"}}` with `["file_content"]` →
  `{"a": {"file_content": "***"}}`.
- `test_masks_key_in_list_of_dicts` (new): the `edits` shape
  `{"path": "/f", "edits": [{"find": "a", "content": "secret"}]}` with `["content"]` → the nested
  `content` becomes `"***"` and `find` is untouched.
- `test_masks_same_key_at_multiple_depths` (new): one tree where the configured key appears at depth 1, 2,
  and inside a nested list; every occurrence is `"***"`.
- `test_masks_non_string_value_at_depth` (new): `{"a": {"secret": 42}}` with `["secret"]` → `"***"`, matching
  the top-level rule that a masked value is replaced regardless of type.
- `test_empty_containers_pass_through_as_new_containers` (new): `{"a": {}, "b": []}` → `{"a": {}, "b": []}`.
- `test_input_args_unchanged_after_masking` (new) (`AC-5`): a nested tree is deep-equal to its pre-call
  snapshot after `mask_args` returns, including the nested containers.
- `AC-1` shape check: `mask_args({"path": "/f", "edits": [{"find": "a", "file_content": "secret"}]},
  ["file_content"])` returns the nested value as `"***"`.

## Compatibility considerations

- The 6 existing `TestMaskArgs` tests must pass with zero edits (`AC-3`); any edit to them is a signal
  that the implementation changed top-level behavior.
- No new import and no new fixture: the file's existing import block is the only dependency.
- Tests must not touch `/opt/llm` (`tests/conftest.py` isolation guard).

## Security considerations

- These tests are the guard that sensitive argument values cannot reach a log formatter unredacted at
  depth. They assert the redaction, not the transport.
- Test payloads use obviously synthetic values (`"secret"`, `"s3cr3t"`), so the suite itself contains
  no real secret material.

## Rollback considerations

- Deleting the appended cases reverts this row completely; nothing else in the file is touched.
- A rollback of the implementation row (`_01`) must keep these tests out of the tree, or the agent
  suite fails on nesting expectations.

## Validation plan

- `uv run pytest tests/agent/test_tool_result_formatter.py -v` — all tests pass, including the 6
  pre-existing `TestMaskArgs` cases.
- `uv run pytest tests/agent -q` — no new failure (`AC-8`).
- Mutation intent (manual, per repo practice; no mutation tool is installed): restricting recursion to
  the top level, skipping list traversal, or mutating the input in place must each make at least one of
  these cases fail.
- `uv run ruff format tests/agent/test_tool_result_formatter.py` and `uv run ruff check
  tests/agent/test_tool_result_formatter.py`.

## Completion criteria

- `AC-1` and `AC-5` are asserted by named tests in `TestMaskArgs`.
- `AC-3`: the 6 pre-existing tests are byte-identical and pass.
- `AC-8`: `uv run pytest tests/agent -q` reports no new failure.

## Out of Scope

- Audit-path coverage with a serialized payload (`T-2`), owned by
  `implementations/20261024-124138_03_tests_agent_test_tool_approval_preflight.py.md`.
- The preview-boundary characterization test (`T-3`), owned by
  `implementations/20261024-124138_04_tests_agent_test_tool_approval_risk.py.md`.
- Any assertion about the default `masked_fields` value; `tests/agent/test_config_builders.py:155`
  already pins the default and must keep passing unmodified.


## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the nesting and no-mutation cases to `TestMaskArgs` | Completed | 20261024-175841 | 20261024-175841 | Existing 6 tests untouched verified: suite+gates green |
| 2 | Run the targeted file and the agent suite | Completed | 20261024-175841 | 20261024-175841 | Requires `_01` to be implemented verified: suite+gates green |
| 3 | Verify the mutation-intent statements by hand | Completed | 20261024-175841 | 20261024-175841 | Each mutation must break at least one case verified: suite+gates green |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | N/A: no work item was created by this row |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261021-093421_tool005-masked-args-not-applied-to-previews-or-nesting.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-072425_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-124138
- **Related target files**: `tests/agent/test_tool_result_formatter.py`