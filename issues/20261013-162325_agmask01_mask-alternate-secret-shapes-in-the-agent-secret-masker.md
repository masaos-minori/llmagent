# Mask alternate secret shapes in the agent secret masker

## Priority
Medium

## Summary
`agent.secrets_masker._mask_secrets()` only recognizes secrets written as `key=value`
(`password=...`, `api_key=...`, `secret/token=...`). Any secret in another shape — for
example an `Authorization: Bearer <token>` header, a JSON `"key": "value"`, or a bare
hex/base64 token — is not matched at all and reaches logs or error reports unmasked. This is
the known issue tracked as `AGENT-006`. Fix the still-open shape-recognition gap left by
`secmask001` (which only closed the value-leak bug) and cover it with tests.

## Background
`_mask_secrets()` is applied to MCP subprocess output that the Agent reports on startup
failure (`scripts/agent/http_lifecycle.py`, `scripts/agent/startup_mcp_starter.py`). The
ledger entry `AGENT-006` records it as `open` / `Medium` / `design-gap`;
source `scripts/agent/secrets_masker.py`, target
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`.

`issues/done/20261004-160514_secmask001_secrets-masker-leaves-short-secret-values-unmasked.md`
(`secmask001`) addressed a different defect in the same module: the replacement leaked the
leading characters of short values. That fix is implemented and tested
(`tests/agent/test_secrets_masker.py`). `secmask001` raised, as an unresolved question,
whether non-`key=value` shapes such as `Authorization: Bearer ...` should be masked, and did
not change the matcher. `AGENT-006` tracks exactly that deferred shape-recognition gap, which
remains open.

## Problem
The three `SECRET_PATTERNS` in `scripts/agent/secrets_masker.py` each require a
`<key>\s*=\s<value>` structure. Real subprocess output frequently carries credentials in
other shapes — an `Authorization: Bearer <token>` header line, a JSON field
`"api_key": "..."`, or a bare token on its own line. None of these match, so they are logged
in clear text. Masking is best-effort here, but the current matcher gives a false sense of
protection: it masks `key=value` secrets and silently passes everything else through.

## Reason for Change
The masking path is security-sensitive (it exists precisely to keep credentials out of logs
and startup-error reports). A shape it does not recognize leaks directly. The value-leak half
of the problem is now fixed by `secmask001`; the recognition half is still open and should not
be left as an unanswered question.

## Implementation Intent
Extend `_mask_secrets()` so it recognizes additional common secret shapes while keeping its
public contract (replace secrets in a string, never raise, stay cheap). Choose one of the
two resolution paths recorded in `AGENT-006`:
- extend the regex patterns in `SECRET_PATTERNS` to also match bearer/authorization headers
  and other common shapes, or
- route the recognized values through the shared log-redaction registry
  (`shared/logger.py::register_secret` / `attach_redaction_filter`) where appropriate.

Decide explicitly which shapes are in scope and document the final set. Preserve the existing
`key=value` behavior and all call sites.

## Target Files or Areas
- `scripts/agent/secrets_masker.py` (`SECRET_PATTERNS`, `_mask_secrets()`)
- `scripts/shared/logger.py` (if reusing the shared redaction registry)
- `tests/agent/test_secrets_masker.py`
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

## Required Changes
- Add patterns (or registry wiring) so a non-`key=value` secret such as an
  `Authorization: Bearer <token>` header is masked.
- Decide and document the exact set of masked shapes.
- Keep the existing `key=value` patterns working unchanged.
- Add unit tests for the new shapes and for regression of the existing ones.
- Update the secret-masking description in `agent_10_01` to state the final set of masked
  forms.

## Constraints
- The masker must not raise on arbitrary text, including empty strings.
- It is applied to log output; it must stay cheap.
- Do not change which call sites apply the masker.
- If reusing the shared registry, do not alter its public API or other callers.

## Acceptance Criteria
- An `Authorization: Bearer <token>` header (or whichever shapes are in scope) is masked in
  `_mask_secrets()` output.
- Existing `key=value` masking still produces the previously asserted results.
- Text without secrets is returned unchanged; empty string returns empty string.
- The chosen masked shapes are documented in `agent_10_01`.

## Testing Expectations
Unit tests under `tests/agent/test_secrets_masker.py` covering the new shapes plus the
existing `key=value` cases. Run `ruff`, `mypy`, and the agent test suite.

## Documentation Impact
Update the secret-masking section in `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`:
state the final set of masked forms and remove/adjust the limitation note. Re-check whether
`AGENT-006`'s ledger entry should be marked resolved once fixed.

## Out of Scope
- The value-leak bug fixed by `secmask001` (already resolved; do not re-address here).
- Introducing a general log-redaction framework beyond the two options above.
- Changing call sites or the shared registry's public API.

## Dependencies
- `issues/done/20261004-160514_secmask001_secrets-masker-leaves-short-secret-values-unmasked.md`
  (`secmask001`): fixed the value-leak half of the same module and left this shape-recognition
  gap open as an unresolved question. Re-verify against `secmask001`'s resolution; the two
  changes touch the same file, tests, and doc, so coordinate them.

## Unresolved Questions
- Which shapes are in scope (e.g. `Authorization: Bearer`, JSON fields, bare tokens)?
- Extend `SECRET_PATTERNS` vs. reuse `shared/logger.py`'s redaction registry — which fits the
  call sites better?
- Are there other places that log subprocess output without passing it through the masker?

## AI Implementation Instruction
Keep the change minimal and limited to `scripts/agent/secrets_masker.py` (and optionally
`scripts/shared/logger.py`) plus its tests. Do not change call sites or the existing
`key=value` behavior. Pick one resolution path (pattern extension or shared registry) and
document the decision; do not add shapes beyond what you can justify. Stop and report if the
intended masked shapes are unclear.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261013-162325
- **Related target files**: scripts/agent/secrets_masker.py, scripts/shared/logger.py, tests/agent/test_secrets_masker.py, docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md
