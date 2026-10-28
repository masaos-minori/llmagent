# Procedure: align the safe-defaults sentence in the shared types doc

## Goal

Replace the sentence that says the builder applies safe defaults to unspecified annotation fields (Plan REQ-006).

## Scope

- Modify only `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- Ordering note: the fixture builder row (seq 02) is applied first, then the call-site rows (seq 03 to 08), and the strict production builder row (seq 01) last, so no test breaks between steps.
- All text stays English (`skills/DESIGN.md` Output language).
- Overlap (compatible): `plans/done/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md` (archived, procedures pending) also targets `tests/shared/test_runtime_tool_registry.py`; it adds exclusion-reason tests, while this procedure only changes which builder the existing calls use. The mcpcompat003 work (`implementations/20261028-065435_*`, already executed) edited `tests/shared/test_resource_scope.py`; re-read it before editing.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md`

### Procedure

- In section `7c. RuntimeTool`, replace "`build_runtime_tool()` applies safe defaults to unspecified annotation fields." with: `build_runtime_tool()` requires `is_write`, `requires_serial`, `resource_scope_kind` and `resource_scope_keys` and rejects a missing or `None` value; the remaining fields default conservatively (the most restrictive safety tier, not visible to the LLM, no capabilities, extra fields rejected).
- Keep the `allow_extra_fields` sentence unchanged.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- The sentence is the only statement of builder defaults in `docs/`; `rg "safe defaults" docs` confirms it.

## Compatibility considerations

N/A: documentation-only.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py --strict`; `uv run python tools/check_docs_japanese.py`; `uv run python tools/check_docs_consistency.py --domain shared` | No finding |

## Completion criteria

- The section states the required fields and the conservative defaults.
- `uv run python tools/check_docs_consistency.py --domain shared` and the other doc checkers report no finding.

## Out of Scope

- Every other document.
- Code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (shared types doc)
- **Source issue**: issues/20261027-155851_rtool008_fail-closed-runtimetool-builder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120306
- **Related target files**: docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md
