## Goal

Add the characterization test (`T-3`) that the interactive approval preview produced by `build_preview`
contains raw argument values and is never masked, making the Option-2 boundary executable
(`REQ-001`, `REQ-004`, `AC-6`).

## Scope

- `tests/agent/test_tool_approval_risk.py`: one new test inside the existing `TestBuildPreview` class
  (`:219-265`).
- No change to the `build_preview as _build_preview` import (`:16`) or to the 7 existing
  `TestBuildPreview` cases.

## Assumptions

- `build_preview` (`scripts/agent/tool_result_formatter.py:82`) takes no `masked_fields` argument and
  never calls `mask_args`; the preview path in `scripts/agent/tool_approval.py` reaches it without
  masking.
- `TestBuildPreview` in this file already calls `_build_preview` directly, so the new test needs no
  fixture, config object, or audit sink.

### Procedure-local findings

- The Plan cites the `build_preview` test area as `:216-221`. Measured: `TestBuildPreview` spans
  `:219-265` with 7 cases, and `TestClassifyOperationType` starts at `:268`. The procedures use the
  measured anchors; the correction is recorded in `plans/20261023-072425_plan.md`.
- The same file's `TestBuildPreview` already pins the `[:200]` truncation (`:256`), so this row adds no
  truncation coverage.

## Design decisions

- Pin the boundary with a key name that masking *would* target if it were applied here (`content`, the
  real `write_file` argument key), so the test fails if masking is ever introduced into the preview
  path.
- Keep the content short (well under the `[:200]` truncation at `scripts/agent/tool_result_formatter.py:66`)
  so a failure means masking, not truncation.
- Assert the raw substring is present rather than asserting the absence of `***`: the contract is "the
  approving user sees what they are approving".

## Alternatives considered

- Asserting that the preview equals the pre-change rendering byte-for-byte: rejected. It encodes
  formatting details the Plan does not promise; only the masking boundary is the contract.
- Adding the case to `tests/agent/test_tool_result_formatter.py`'s own `TestBuildPreview` (`:80`):
  rejected. The Plan row assigns this coverage to the approval-risk file, which is where the approval
  boundary is documented by the surrounding tests.
- Testing through `check_approval()`: rejected. It would require approval plumbing and would not
  isolate the preview function the docs describe.

## Implementation

### Target file

`tests/agent/test_tool_approval_risk.py` — append inside `TestBuildPreview` after
`test_content_truncated_at_200_chars` (`:256-265`).

### Procedure

1. Add `test_preview_is_never_masked` (new).
2. Call `_build_preview("write_file", {"path": "/f", "content": "sensitive-body-value"})`.
3. Assert the rendered preview contains `sensitive-body-value` and does not contain `***`.

### Method

- One call, two assertions. The `***` absence assertion documents intent for the reader even though
  the raw-substring assertion already fails when masking is introduced.

### Details

- Test name: `test_preview_is_never_masked` (new).
- The argument shape mirrors the real `write_file` schema (`scripts/mcp_servers/file/write_tools.py:31`:
  `required: ["path", "content"]`).
- Existing `TestBuildPreview` cases stay byte-identical (`AC-6`).

## Compatibility considerations

- This test locks an intentional non-behavior: any future change that masks previews must delete or
  rewrite this test, which forces the decision to be re-made explicitly.
- The plan-mode blocked notice (`scripts/agent/tool_approval.py:222`, which does mask) is a different
  path and is not covered here; the docs row states that distinction.
- No new import; `_build_preview` is already imported at `:16`.

## Security considerations

- The test asserts an accepted exposure, so its docstring must state why: the preview's reader is the
  same person who supplied the arguments, and masking it would remove the approval signal while
  protecting nothing (`REQ-001` rationale).
- Persistent/transcript outputs (audit events, logger writes, the REPL tool-call line) remain masked;
  this test does not weaken them.

## Rollback considerations

- Deleting the appended test reverts this row; nothing else in the file is touched.

## Validation plan

- `uv run pytest tests/agent/test_tool_approval_risk.py -v` — the new test plus all 7 pre-existing
  `TestBuildPreview` cases and the rest of the file pass.
- Targeted single test: `uv run pytest tests/agent/test_tool_approval_risk.py -k
  test_preview_is_never_masked -v`.
- Mutation intent (manual): adding a `mask_args` call anywhere inside `build_preview` must make this
  test fail.
- `uv run pytest tests/agent -q` — no new failure (`AC-8`).

## Completion criteria

- `AC-6`: a new test shows `build_preview` output contains the raw value for a key name that masking
  would otherwise target, and the existing `TestBuildPreview` cases pass unmodified.
- `AC-8`: the agent suite reports no new failure.

## Out of Scope

- Changing any preview behavior or adding masking to a preview: explicitly out of scope per `REQ-001`.
- Dry-run preview behavior (`scripts/agent/tool_approval.py:174`), which is not produced by
  `build_preview`.
- The `masked_fields` documentation text, owned by
  `implementations/20261024-124138_05_docs_23_agent_agent_08_03_configuration-tools-memory.md.md`.


## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append `test_preview_is_never_masked` (new) to `TestBuildPreview` | Pending | — | — | No new import |
| 2 | Run the targeted file and the agent suite | Pending | — | — | `AC-6`, `AC-8` |
| 3 | Confirm the 7 existing `TestBuildPreview` cases are byte-identical | Pending | — | — | `AC-6` |

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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: `issues/20261021-093421_tool005-masked-args-not-applied-to-previews-or-nesting.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-072425_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-124138
- **Related target files**: `tests/agent/test_tool_approval_risk.py`
