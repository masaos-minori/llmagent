# Use orjson for JSON serialization in session_persister

## Priority
Medium

## Summary
`scripts/agent/session_persister.py` uses the stdlib `json` module for both
serialization and parsing, contradicting the repository rule "Use `orjson` (not
stdlib `json`) for all JSON serialization" (`rules/coding.md`). Replace the stdlib
usage with `orjson` while keeping the persisted JSON content byte-compatible for
existing readers.

## Background
`rules/coding.md` (Key library choices) mandates `orjson` for all JSON
serialization; the only stdlib-`json` carve-out noted there is
`config_loader.py`. `session_persister.py` was not caught by any static gate:
`ruff check` passes on it today (Evidence: confirmed — gate run during the
python-code-review pass), so the violation is enforcement-invisible. The sibling
component `scripts/agent/diagnostic_store.py` already uses `orjson`
(`orjson.loads`), so the inconsistency is inside one persistence domain.

## Problem
Confirmed by code reading (Evidence: confirmed, Confidence: High):
- `scripts/agent/session_persister.py` line 17: `import json`
- line 117: `json.loads(e["content"])` on stored diagnostic payloads
- line 161: `content=json.dumps(summary)` when persisting the session summary

Consequences: a rule violation that reviewers and linters do not flag, a second
JSON implementation to keep behaviorally aligned in the same subsystem, and
needless divergence from the `orjson.dumps()`-returns-`bytes` convention that
every other writer in this domain follows.

## Reason for Change
Small, low-risk convention fix in a file the review just touched; fixing it now
keeps the session-diagnostic payload writers (`session_persister.py` and
`diagnostic_store.py`) on one serializer so future payload-format changes happen
in one place.

## Implementation Intent
Swap the module's JSON calls to `orjson` equivalents at the same call sites. No
design change: the persisted payload format (JSON object written to
`session_diagnostics.content`) must remain exactly what current readers parse.

## Target Files or Areas
- scripts/agent/session_persister.py
- tests/agent/test_session_persister.py

## Required Changes
- Replace `import json` with `orjson` usage.
- `json.loads(e["content"])` → `orjson.loads(...)`; adjust the caught exception to
  `orjson.JSONDecodeError`.
- `json.dumps(summary)` → `orjson.dumps(summary).decode()` (per the
  `orjson.dumps()`-returns-`bytes` constraint in `docs/40_shared/shared_01_overview.md`).
- If canonical key ordering matters for the summary payload, use
  `orjson.OPT_SORT_KEYS` — decide against the readers (see Unresolved Questions).

## Constraints
- The content column is read back by `session_persister.py` itself and by session
  export/restore paths; the serialized document must remain semantically identical
  (same keys, same values).
- Do not touch `config_loader.py` (its stdlib carve-out stands).
- No behavior change beyond serialization.

## Acceptance Criteria
- `rg -n 'import json|json\.' scripts/agent/session_persister.py` returns nothing.
- Existing `tests/agent/test_session_persister.py` passes unchanged (or with only
  serialization-library-specific adjustments).
- A round-trip check shows a persisted summary parses back to the same dict.

## Testing Expectations
- Run `tests/agent/test_session_persister.py`.
- Run the session test set (`test_session_restore.py`, `test_agent_session.py`) to
  confirm readers of `session_diagnostics.content` still parse the payload.
- `uv run ruff check` and `uv run mypy --no-namespace-packages` on the changed file.

## Documentation Impact
No documentation update required (behavior-preserving library swap; the rule already
exists in `rules/coding.md`).

## Out of Scope
- Enforcing the orjson rule repo-wide (e.g. a new ruff rule or ast-grep gate) —
  out of scope; this issue covers `session_persister.py` only.
- Changing the diagnostic/summary payload schema.

## Dependencies
- N/A: none

## Unresolved Questions
- Do any consumers compare the serialized summary byte-for-byte or rely on key
  insertion order? 不明 — verify the readers during planning; it decides whether
  `OPT_SORT_KEYS` is required.

## AI Implementation Instruction
Single-file swap plus test adjustments only. Preserve exception semantics of the
parse site (`JSONDecodeError` plus `KeyError` handling at line 119 must stay
equivalent). Do not rename functions or restructure the persister.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261025-115739
- **Related target files**: scripts/agent/session_persister.py, tests/agent/test_session_persister.py
