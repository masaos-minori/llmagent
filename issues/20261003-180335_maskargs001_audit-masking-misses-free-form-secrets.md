# Audit masking misses free-form secrets

## Priority
Medium

## Summary
Audit-log argument masking relies solely on key matching against a configured `masked_fields` list, with no content-pattern scan over the values. A secret embedded inside a free-form string-valued argument (for example a `shell_run` `command` containing `Authorization: Bearer ...`) is written verbatim into the persisted audit log (`args_preview`). The interactive approval preview is built from the raw arguments and is not masked at all; whether to scrub it is a separate decision.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's tool-execution/audit subsystem (`scripts/agent/tool_result_formatter.py`, `scripts/agent/tool_audit.py`, `scripts/agent/tool_approval.py`) and re-verified against the current code. `mask_args()` is used for the plan-blocked emit, the audit events (`audit_tool_exec`, `audit_approval`) and tool-runner logging. Its docstring states that masking is not applied to the interactive approval preview; `tool_approval.check_approval` shows `build_preview(tool_name, args)` (defined in `tool_result_formatter.py`) built from the raw arguments, on the operator's own terminal. `origin/master` changes `audit_tool_exec` (adds `dedup_state` and `execution_snapshot_json`), so expect a small merge when editing it.

## Problem
`scripts/agent/tool_result_formatter.py::mask_args()` delegates to `_mask_value()`, which replaces values whose key is in `ctx.cfg.tool.masked_fields` at any depth (including inside lists). There is no content scan. A secret embedded in a string-valued argument under a key not listed in `masked_fields` (an LLM-generated `shell_run` `command` such as `curl -u user:pass`, or a secret concatenated into a path or query value) is written verbatim into `args_preview` by `audit_tool_exec` and `audit_approval`.

## Reason for Change
Secret exposure in the durable audit trail whenever a sensitive value does not live under an explicitly configured field name, which by construction cannot cover free-form fields such as shell commands.

## Implementation Intent
Run a content-pattern scrub (reusing `secrets_masker`'s redaction) over string values inside `mask_args()` (or in the audit's bounded-preview step), in addition to the existing key-based masking, so the audit log and the tool-runner logging are covered. Decide separately whether the approval preview should be scrubbed: the operator needs to see the real command, so that is an explicit decision, not an assumption.

## Target Files or Areas
- `scripts/agent/tool_result_formatter.py` (`mask_args()`, `_mask_value()`; `build_preview()` is read-only reference)
- `scripts/agent/tool_audit.py` (`_bounded_preview` or wherever `args_preview` is built)
- `scripts/agent/secrets_masker.py` (the redaction function to reuse)

## Required Changes
- After key-based masking, run each remaining string value through a content-pattern secret scrub (`secrets_masker._mask_secrets()` or an equivalent shared utility).
- Record the decision on the approval preview (leave raw, or scrub); implement only what is decided.
- Add a test asserting a secret embedded in a free-form argument value (not under a `masked_fields` key) is redacted in the audit `args_preview` and the tool-runner logging path.

## Constraints
- Do not remove or weaken the existing key-based masking.
- Keep this change scoped to adding a content-pattern pass — do not restructure `mask_args()`'s key-based logic.

## Acceptance Criteria
- A secret pattern embedded in a free-form argument value is redacted in the persisted audit log's `args_preview`.
- Arguments under a configured `masked_fields` key continue to be masked exactly as before.
- The approval preview behavior matches the recorded decision.

## Testing Expectations
Unit tests covering a secret under a `masked_fields` key (existing behavior) and a secret embedded in a non-listed free-form string value (new). Run `tests/agent/test_tool_result_formatter.py` and `tests/agent/test_tool_audit.py` after the change.

## Documentation Impact
N/A: no operator-facing documentation describes `mask_args()`'s exact coverage today; this is an internal security hardening fix.

## Out of Scope
- `secrets_masker.py`'s own pattern coverage (see `issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md`).
- `diagnostic_store.py`'s separate secret-detection guard (tracked separately).

## Dependencies
Depends on `issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md` (now the colon-form coverage gap): the scrub reuses the masker, so its pattern coverage sets this issue's coverage. Shares `audit_tool_exec` with `assertaudit001` and `toolaudit001`.

## Unresolved Questions
- Whether the approval preview should be scrubbed or stay raw so the operator can read the actual command: a decision for the owner.

## AI Implementation Instruction
Reuse the `secrets_masker` redaction rather than writing a second pattern set. Do not change the existing key-based masking behavior. Do not change the approval preview unless the owner has decided to. Add the regression tests described above before considering this done.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180335
- **Related target files**: scripts/agent/tool_result_formatter.py, scripts/agent/tool_audit.py, scripts/agent/tool_approval.py, scripts/agent/secrets_masker.py
