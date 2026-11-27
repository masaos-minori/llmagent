## Goal

Add the MDQ write branch to the approval preview builder, so the prompt for `index_paths` and
`refresh_index` shows the common root and representative paths from the masked arguments instead of
the raw JSON dump.

## Scope
**Release unit**: preview path

- `build_preview()` (lines 109-131) in `scripts/agent/tool_result_formatter.py`: one new branch plus a
  small helper for the common root.

### Companion test files
- `tests/agent/test_tool_result_formatter.py`
  - Procedure: add the mdq cases for the common root, representative paths, masked values, and a large
    path list; the existing cases (199-226) are unchanged.
  - Validation: `uv run pytest tests/agent/test_tool_result_formatter.py tests/agent/test_tool_audit.py`

## Assumptions

- The formatter receives the masked arguments, not the server-side decision, so it can describe the
  requested paths only; the planned counts come from the tool result metadata, not from this function.
- The agent layer does not import the mdq models (the plan records this as a hierarchy-convention
  choice, not a contract-enforced one), so the branch works from the argument values alone.
- A path argument can be a list, so the helper iterates every element of a list-valued argument.

## Design decisions

- The branch is keyed on the two tool names, matching how the other tool families are keyed in the same
  function, rather than on a path-kind key lookup, so the display stays independent of the registry.
- The helper `_preview_mdq_paths` (new) is a separate function, matching `_preview_file_write()` and
  `_preview_shell_cmd()`, so the branch itself stays one line and the common-root logic is testable on
  its own.
- Representative paths are a bounded sample of the requested paths, so a large path list does not expand
  the approval prompt past the existing 300-character ceiling of the fallthrough.

## Alternatives considered

- Reading the planned metadata in the formatter: rejected, the formatter is the display layer and the
  audit redaction path is separate; making it depend on mdq models would cross that boundary.
- Keeping the JSON fallthrough for these tools: rejected, the requirement is precisely that the argument
  dump is replaced for the two write tools.

## Implementation
### Target file
`scripts/agent/tool_result_formatter.py`

### Procedure
1. Add `_preview_mdq_paths` (new) that returns the common root of the `paths` argument and a bounded
   number of representative paths.
2. In `build_preview()`, add a branch for `index_paths` and `refresh_index` before the JSON fallthrough
   that returns the helper's output.

### Method

- The helper takes the same `args: dict[str, Any]` shape as the existing preview helpers and returns
  `?` when the argument is missing or not a string, matching `_preview_file_path()`'s handling.
- The common root is computed with `os.path.commonpath` over the string values; a non-string element is
  skipped, and an unusable argument falls back to the existing `?` behavior.

### Details

- Output shape: `common_root=<root> paths=<n> sample=<first representative paths>`, with the sample count
  bounded so the whole string stays within the display ceiling.
- The other branches in `build_preview()` are unchanged.

## Compatibility considerations

- The persistent audit path is not modified: `_extract_resource_scope()` keeps the path-kind list values
  joined with `;`, which is the canonical audit contract (UNK-03). `tests/agent/test_tool_audit.py` is
  the unchanged guard for that shape.
- Tools without a branch still fall through to `_json_dumps(args)[:300]`, so the change affects only the
  two mdq write tools.

## Security considerations

- Masked values are displayed as they arrive, so the display does not reveal content the masking already
  removed; the preview is display-only and does not authorize anything.

## Rollback considerations

- Revert the commit; no persisted state depends on the display branch.

## Validation plan

- `uv run pytest tests/agent/test_tool_result_formatter.py tests/agent/test_tool_audit.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The approval preview for the two write tools shows the common root and representative paths, and the
  audit payload shape is unchanged (AC-4).

## Out of Scope

- The planned-count metadata model: row 2.
- The canonical display statement in the docs: row 16.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion row 13 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs row 16 records the display rule |

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
- **Requirement ID**: REQ-006
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `scripts/agent/tool_result_formatter.py`, `tests/agent/test_tool_result_formatter.py`
