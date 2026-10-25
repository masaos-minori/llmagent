# Remove runtime mutation of the TRUSTED_SOURCES registry

## Priority
Medium

## Summary
Make `scripts/agent/message_schema.py`'s `TRUSTED_SOURCES` registry the single declarative source of truth for message-source trust, and remove the runtime registration performed by `scripts/agent/llm_turn_runner.py`'s `_finalize_after_guard`. Review finding F-002.

## Background
Explicit in code: `TRUSTED_SOURCES` is a module-level `dict[str, set[str]]` defined in `scripts/agent/message_schema.py`, and `_ALL_EPHEMERAL_KEYS` is computed once at import time from its values. `agent/llm_turn_runner.py`'s `_finalize_after_guard` mutates the registry at runtime: when the tool-loop guard fires, it adds the `loop_guard` source with `{"_ephemeral"}` if absent. `scripts/agent/context.py` reads `TRUSTED_SOURCES` when authorizing ephemeral keys on messages. Confirmed by review (python-code-review finding F-002, High confidence).

## Problem
A trust-boundary allowlist is mutated from a per-turn runtime code path. Because `_ALL_EPHEMERAL_KEYS` and any other import-time derivations of the registry are computed once, a later-added entry (or a future entry granting keys beyond `_ephemeral`) silently diverges from those derived constants, weakening the guarantee that validation consults one fixed registry.

## Reason for Change
The mechanism guards which message sources may carry ephemeral keys — a validation boundary. Fragile registration makes future changes to the registry error-prone and hard to audit.

## Implementation Intent
Declare every trusted source, including the loop-guard source, in the `TRUSTED_SOURCES` definition itself. Runtime code paths (including the tool-loop-guard finalization in `llm_turn_runner`) read the registry only and never write it. Validation semantics for existing sources stay identical.

## Target Files or Areas
- `scripts/agent/message_schema.py` (`TRUSTED_SOURCES`, `_ALL_EPHEMERAL_KEYS`)
- `scripts/agent/llm_turn_runner.py` (`_finalize_after_guard`)

## Required Changes
- Add the `loop_guard` source entry to the `TRUSTED_SOURCES` definition with the same ephemeral-key grant it receives today.
- Delete the mutation (`if loop_guard_source not in TRUSTED_SOURCES: ...`) from `_finalize_after_guard`.
- Verify import-time derivations such as `_ALL_EPHEMERAL_KEYS` cover every declared entry.

## Constraints
- `validate_message` outcomes for every existing source must be unchanged.
- Keep the registry a module-level definition in `message_schema.py`; do not introduce a new registry abstraction.
- No changes to the loop-guard trigger logic itself.

## Acceptance Criteria
- No write to `TRUSTED_SOURCES` exists outside its definition (verifiable by source inspection / grep).
- `validate_message` accepts the loop-guard ephemeral message in the guard path exactly as before (regression test).
- mypy, ruff, and the full test suite pass.

## Testing Expectations
- Regression test asserting `validate_message` behavior for the `loop_guard` source (accept with `_ephemeral`, reject unlisted ephemeral keys) before and after the change.
- Existing `message_schema` and turn-runner tests pass unchanged.

## Documentation Impact
Update only if a document describes the trusted-source registry as runtime-extensible; none found in the reviewed docs. Otherwise none.

## Out of Scope
- Redesigning message validation or the ephemeral-key model.
- Other consumers of `TRUSTED_SOURCES` (`agent/context.py`) beyond keeping their behavior identical.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Move the entry into the declarative registry and delete the runtime mutation; keep the diff minimal and behavior identical. If a test depends on the registry being empty before the guard fires, report it instead of changing test semantics silently.

## Traceability
- **Workflow phase**: python-code-review (finding F-002)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261025-210105
- **Related target files**: `scripts/agent/message_schema.py`, `scripts/agent/llm_turn_runner.py`
