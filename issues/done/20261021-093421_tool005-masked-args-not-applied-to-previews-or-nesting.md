# `masked_fields` is applied only at the top level, and approval previews render unmasked arguments

## Priority
Medium

## Summary
Make argument masking apply to nested values and to every string a user can see, so a configured masked
field never reaches the terminal or the audit log.

## Background
`mask_args()` is the single masking implementation:
`{k: ("***" if k in masked_fields else v) for k, v in args.items()}`
(`scripts/agent/tool_result_formatter.py:27-31`). It is applied by the audit paths
(`scripts/agent/tool_audit.py:46`, `:157`) and by `run_approval_checks()` for the plan-mode block message
(`scripts/agent/tool_approval.py:211-212`) and by the tool-result emitter (`scripts/agent/tool_runner.py:204`).

## Problem
- Masking is top-level only. A secret under a nested key survives: `{"headers": {"authorization": "…"}}`
  is unchanged when `masked_fields` contains `authorization` (`tool_result_formatter.py:31` iterates
  `args.items()` with no recursion). The masked value then reaches
  `ToolApprovalEvent.args_preview` and `ToolExecEvent.args_preview` (`tool_audit.py:58`, `:169`).
- The interactive preview bypasses the masked copy. `run_approval_checks()` computes `masked_preview` but
  passes the raw dict onward: `await check_approval(ctx, tc_name, args_preview)` (`tool_approval.py:214`),
  and `check_approval()` renders `preview = build_preview(tool_name, args)` (`:179`, `:182`) and audits
  raw `args` (`:148-149`, `:159-160`). The preview builders print argument content directly:
  `_preview_file_write` returns a 200-character `content!r` snippet and `build_github_preview` returns a
  200-character JSON dump of the remaining args (`tool_result_formatter.py:34-41`, `:44-49`). So the
  approval prompt the operator sees can contain the exact value `masked_fields` is configured to hide.
- `tool.masked_fields` semantics are not stated anywhere: exact key match, no case folding, no nesting
  rule, no wildcard.

## Reason for Change
`masked_fields` exists to keep secrets out of logs and prompts. Today it holds for the flat case and
silently fails for nested arguments and for the approval preview, which is the most visible surface.

## Implementation Intent
Define masking as a property of "any value shown or recorded about a tool call", implement it once,
recursively, and pass the masked copy to every renderer instead of the raw dict.

## Target Files or Areas
- `scripts/agent/tool_result_formatter.py` (`mask_args`, `build_preview`, `_preview_file_write`,
  `build_github_preview`)
- `scripts/agent/tool_approval.py` (`run_approval_checks`, `check_approval`)
- `scripts/agent/config_dataclasses.py` (`tool.masked_fields` documentation)

## Required Changes
- Make `mask_args` recurse into nested dicts and lists of dicts.
- Pass masked arguments into `check_approval()` and the preview builders, or make the preview builders
  take the masked copy internally.
- State the matching rule (exact key, case sensitivity, nesting, list handling) in the function docstring
  and in configuration documentation.
- Keep preview length limits unchanged.

## Constraints
- Masking must not alter the arguments actually passed to the tool — only what is rendered or recorded.
- Preview truncation behavior (`[:200]`) must stay.
- Audit event field names and shapes must not change.
- `masked_fields` must stay a plain list of key names in configuration.

## Acceptance Criteria
- For `masked_fields = ["token"]` and args `{"query": {"token": "secret"}}`, the approval preview and both
  audit events contain `***` and not `secret`.
- No call site passes unmasked args to `build_preview()` or `audit_approval()`.
- The documented matching rule matches the implementation, and a test asserts each documented case.

## Testing Expectations
- Unit tests for nested masking (dict-in-dict, dict-in-list, non-string values).
- A test asserting the approval preview text for a tool whose args contain a masked key does not contain
  the secret.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document `tool.masked_fields` semantics (matching rule, nesting, what surfaces are masked) in the
configuration reference and in the tool-approval docs, including that masking applies to previews and
audit rows, not to the values sent to the tool.

## Out of Scope
- Tool result content masking (result output is a separate concern from arguments).
- Adding new masked fields to shipped configuration.
- Redaction of LLM request payloads.

## Dependencies
- Independent. Related to `tool002`/`tool003` only in that all three touch `tool_runner.py`.

## Unresolved Questions
- Should masking apply to values or to keys only (current: keys)? Should matching be case-insensitive?
  Needs confirmation.
- Should the dry-run preview (`tool_approval.py:143-145`) also receive masked args? Needs confirmation.

## AI Implementation Instruction
Keep one masking function and make it recursive; fix the call sites that pass raw args. Do not add a
second, preview-specific masking helper.

## Traceability
- **Workflow phase**: `python-code-review` (tool subsystem review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/tool_result_formatter.py`, `scripts/agent/tool_approval.py`,
  `scripts/agent/tool_audit.py`, `scripts/agent/config_dataclasses.py`
