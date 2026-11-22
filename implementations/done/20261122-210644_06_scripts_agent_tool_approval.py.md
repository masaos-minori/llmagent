## Goal

Bind each approval to a controller request and operation id, fail closed on any HIGH-risk preview failure, build previews from masked data, and pass provenance to the audit (REQ-005, REQ-006, REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `scripts/agent/tool_approval.py`; tests are the separate `test_tool_approval_request_binding.py` row. Another open Issue and the mcpdl003 procedures edit other parts of this file (see Assumptions).

## Assumptions

- Verified: `build_preview` receives raw `args` (line 101) and dry-run text is truncated unmasked (lines 119 and 121); a dry-run execution failure falls back to the static preview even for HIGH (lines 124-127 and 221-223).
- Overlap (Plan Assumptions): the mcpdl003 procedure edits `_issue_grant` only; rebase line references if it lands first.
- The MEDIUM fallback setting is read as `ctx.cfg.approval` plus the new field declared by the config procedure (seq 13); until then the code path is guarded by the field's default of allowed.

## Design decisions

- A frozen `PreviewResult`(new) holds `text`, `source` (static or dry_run), `required` (HIGH), and `fallback_reason`.
- HIGH: any `ApprovalPreviewError` (blocking or not) denies with a reason code and no raw exception text; MEDIUM: falls back to the static preview only when the config field allows it, otherwise denies.
- Static previews call `build_preview` with `mask_args(args, ctx.cfg.tool.masked_fields)`; dry-run output and error text pass the shared masker before the 300 and 200 character cuts.

## Alternatives considered

Rejected: masking inside `build_preview` (its truncation would still precede redaction for callers that do not mask); rejected: a second masker (the Issue requires one).

## Implementation
### Target file
`scripts/agent/tool_approval.py`

### Procedure
1. Replace `_approval_read` and `_prompt_user_approval` with a controller request of kind tool_approval whose operation id is the logical call id; approve only on a completed outcome with `yes` (HIGH) or `y` (MEDIUM); every other outcome, and `InputBusyError`, denies.
2. Rework `_build_preview_with_dry_run` to return `PreviewResult`(new); import the masker used by `tool_result_formatter` and apply it before truncation.
3. Rework the `check_approval` preview handling to the HIGH and MEDIUM rules above; new denial reason codes `denied_preview_failed`(new) and `denied_input_busy`(new) (the existing `denied_dry_run_error` stays for a dry-run error result).
4. Pass `request_id`, `preview_source`(new), and `fallback_reason`(new) to `audit_approval` for every audited path that reaches a prompt; never pass the answer text.
5. Mask the exception text in the `logger.warning` calls for preview failures.

### Method
Edit the four functions named above; keep `run_approval_checks` and `_issue_grant` untouched except to pass the call id already available in `check_approval`.

### Details
- A tool that declares no dry-run capability gets the static preview as its normal source, not as a failure.
- Denial messages use fixed reason text plus the tool name; detail goes to the masked log only.

## Compatibility considerations

Callers of `check_approval` and `run_approval_checks` keep their signatures; behavior changes: HIGH now denies on dry-run execution failure.

## Security considerations

Closes stale-answer approval, unmasked previews, and raw exception display (AC-1, AC-4); a HIGH operation never runs on a failed required preview.

## Rollback considerations

N/A: revert the commit; the audit and config rows are default-valued and independent.

## Validation plan

- `uv run pytest tests/agent -k tool_approval -q`
- `uv run ruff check scripts/agent/tool_approval.py && uv run mypy scripts/agent/tool_approval.py && uv run bandit scripts/agent/tool_approval.py`

## Completion criteria

- No path approves from a late or cancelled answer; HIGH previews cannot silently fall back; prompts carry only masked text; audit gets provenance and no answer.

## Out of Scope

Grant lifetime (mcpdl003), mdq dry-run policy (mdqmcp007), preview content formatting beyond masking.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213733 | 20261122-213733 | Changed: scripts/agent/tool_approval.py (and companions) |
| 2 | Add or update tests per Validation plan (companion test files included) | Completed | 20261122-213733 | 20261122-213733 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-213733 | 20261122-213733 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-005` (request binding, required/optional preview, fail-closed HIGH), `REQ-006` (masked previews), `REQ-007` (audit provenance inputs)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/tool_approval.py`
