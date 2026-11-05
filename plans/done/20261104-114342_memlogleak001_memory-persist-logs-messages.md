## Goal
- Stop the session-end memory persistence from logging full message content at WARNING on ordinary messages: base the "unexpected keys" check on the message schema's per-role allowed keys, and make any remaining warning name only the role and the key names, never message content.

## Priority
High

## Scope
- **In-Scope**:
  - Add one public helper to `scripts/agent/message_schema.py` that returns the keys of a message that are neither in the role's `ROLE_KEY_WHITELIST` entry nor an authorized ephemeral key, so the schema stays the single source of allowed keys.
  - `SessionPersister.persist_session_memories` uses that helper and logs only the role and the unexpected key names.
  - Tests for the persister (ordinary tool messages log nothing; a truly unexpected key logs the key name but no content) and for the helper.
  - Regenerate the generated agent reference document, which lists the module's public functions.
- **Out-of-Scope**:
  - Masking policy for other log call sites and the other places that may log whole history messages (not searched here).
  - What is passed to `MemoryServices.on_session_stop`, the memory extraction rules, and the exceptions handled around the memory call.
  - `validate_message` behavior and the history sanitization in `context.py`.
- **Dependencies**: N/A: none. The diagnostic-store secret-guard issue concerns a different component and is independent.

## Background
`persist_session_memories` computes `set(m.keys()) - {"role", "content"}` for every history message and, when non-empty, logs a WARNING that includes the whole message. Assistant messages with `tool_calls` and every tool result with `tool_call_id` (and `name`) carry other keys, and `ROLE_KEY_WHITELIST` already allows those per role. The conversion to `HistoryMessage(role, content)` uses only role and content (checked in Step 2).

## Problem
Each session that used a tool writes the full text of its tool results and tool-call arguments to the log at session end, unmasked, and the warning is noise on the normal path. The Issue's throwaway reproduction captured a made-up secret-like line from a tool result in the log output; the code path was re-read in Step 2 (the warning call passes `m`, the whole message).

Verification corrections and findings:
1. `ROLE_KEY_WHITELIST` is the single per-role source, but it does not cover the ephemeral keys. History messages can still carry `_ephemeral` (command hints, mode-classification hints, the loop-guard hint) and `_memory_injected` (memory injection) at session end, because only the previous turn's ephemeral messages are cleared at the next turn start (checked in Step 2). A whitelist-only check would still log a WARNING with full content for those system messages. The Issue's open question "allow the ephemeral keys here?" is therefore decided: allow them, using the keys authorized in `TRUSTED_SOURCES`.
2. `source` is validation-only metadata and is never stored on a history message (`ConversationState.append_message` documents it), so it needs no allowance.
3. `message_schema.py` keeps its ephemeral key set private (`_ALL_EPHEMERAL_KEYS`). To avoid importing a private name or duplicating the derivation, the schema gets one small public helper; this makes `message_schema.py` a target, not a read-only file, and adds a public function to the generated reference document.
4. `validate_message` itself is not reused: it requires a `source` for ephemeral keys, which history messages lack, so it would reject legitimate stored ephemeral messages.
5. The persister's module logger is `agent.session_persister`; which production handlers receive it is not verified (the Issue's open question stays an Unknown).

## Reason for Change
Logging complete message content is a data-exposure risk on the normal path of every tool-using session, and the check flags messages the schema allows.

## Implementation Intent
Add `unexpected_message_keys(msg)` to the schema module (whitelist for the role, falling back to `{"role", "content"}` for an unknown role, plus the authorized ephemeral keys) and call it from the persister. The warning, when it fires, reports the role and the sorted key names only, with no content, not even truncated.

## Requirements
- `REQ-001`: `scripts/agent/message_schema.py` MUST provide a public helper returning the keys of a message outside the role's allowed keys and the authorized ephemeral keys, derived from `ROLE_KEY_WHITELIST` and `TRUSTED_SOURCES` with no duplicated key lists.
- `REQ-002`: `persist_session_memories` MUST use the helper, MUST emit no "unexpected keys" warning for assistant messages with `tool_calls`, tool results, or messages carrying only authorized ephemeral keys, and MUST NOT change what is passed to `MemoryServices.on_session_stop` or the exceptions handled around it.
- `REQ-003`: For a message with a key outside the allowed set, the warning MUST name the role and the key names and MUST NOT contain any message content, tool output, or argument value (not even truncated).
- `REQ-004`: Tests MUST cover the ordinary-message case, the ephemeral-key case, the unexpected-key case (key name present, content absent), and the helper; the persister tests MUST fail on the pre-change code and pass after it.
- `REQ-005`: The generated agent reference document MUST be regenerated so it lists the new public helper.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed: every row `Verified` — exists, requires modification, supporting evidence, linked to a Plan requirement; no path appears in both tables; no directory, glob, or vague row).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/message_schema.py` | Schema helper | Add the public `unexpected_message_keys` helper built from `ROLE_KEY_WHITELIST` and the ephemeral keys derived from `TRUSTED_SOURCES` (checked in Step 2) | REQ-001; AC-1 | `ROLE_KEY_WHITELIST` and `TRUSTED_SOURCES` are module-level; `_ALL_EPHEMERAL_KEYS` is private and derived from `TRUSTED_SOURCES`; `validate_message` embeds the same comparison inline (checked in Step 2) | `tests/agent/test_message_schema.py` | Verified |
| `scripts/agent/session_persister.py` | Key check and warning text | Replace the fixed `{role, content}` comparison in `persist_session_memories` with the helper and log only role and key names (checked in Step 2) | REQ-002, REQ-003; AC-2, AC-3 | The loop logs `"Unexpected keys in history message: %s — full message: %s"` with the whole message `m` (checked in Step 2) | `tests/agent/test_session_persister.py` | Verified |
| `tests/agent/test_session_persister.py` | Persister tests | Add `caplog` tests with a stub memory service next to `TestPersistSessionMemoriesGate`: tool-call and tool-result history logs no warning and no content; ephemeral keys log nothing; an unexpected key logs the key name and role but not the content (checked in Step 2) | REQ-004; AC-2, AC-3, AC-4 | The file has `TestPersistSessionMemoriesGate` with `_ctx` and an `AsyncMock` `on_session_stop` (checked in Step 2) | `tests/agent/test_session_persister.py` | Verified |
| `tests/agent/test_message_schema.py` | Helper tests | Add unit tests for `unexpected_message_keys` (allowed keys per role, ephemeral keys, unknown role, truly extra key) (checked in Step 2) | REQ-001, REQ-004; AC-1, AC-4 | The file already tests `ROLE_KEY_WHITELIST` and `validate_message` (checked in Step 2) | `tests/agent/test_message_schema.py` | Verified |
| `docs/23_agent/agent_13_reference-api-generated.md` | Generated reference | Regenerate with `tools/generate_reference_table.py --type agent` so the new public function is listed (checked in Step 2) | REQ-005; AC-5 | The document lists `ValidationResult` and `validate_message` for `message_schema.py`, and `generate_reference_table.py --check` reports no drift before the change (checked in Step 2) | N/A: generated documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/context.py` | `append_message` keeps `source` out of the stored message and `_sanitize_message` applies whitelist plus authorized ephemeral keys; the helper must agree with it | REQ-001 |
| `scripts/shared/types.py` | `LLMMessage` declares `_ephemeral`, `_memory_injected`, and `source` | REQ-001 |
| `scripts/agent/conversation_state_manager.py` | Produces `_memory_injected` messages and clears the previous turn's ephemeral messages | REQ-002 |
| `scripts/agent/mode_classification.py` | Produces `_ephemeral` system hints that can remain in history at session end | REQ-002 |
| `tests/agent/test_repl.py` | Calls the persister through the REPL shutdown path; must keep passing | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): the helper returns an empty set for every message shape the schema allows (user, assistant with `tool_calls`, tool with `tool_call_id` and `name`, system, ephemeral keys) and the offending key names otherwise; the allowed sets come from the schema constants.
- AC-2 (REQ-002): persisting memories for a history with tool calls, tool results, and ephemeral messages emits no "unexpected keys" warning, and `on_session_stop` receives the same arguments as before.
- AC-3 (REQ-003): for a message with a key outside the allowed set, the warning names the role and the key and contains none of the message content.
- AC-4 (REQ-004): the new persister tests fail on the pre-change code and pass after the change.
- AC-5 (REQ-005): `uv run python tools/generate_reference_table.py --check` exits 0 after regeneration and the docs checkers report no findings.

## Tests
- `REQ-004`: in `tests/agent/test_session_persister.py`, `caplog` at WARNING on `agent.session_persister`, a stub memory service, and a history of user text, an assistant message with `tool_calls`, a tool result whose content is a made-up secret-like line, and an ephemeral system message; assert no warning and no content in the log. A second test adds a message with a truly unexpected key and asserts the log contains the role and the key name but not the content or any argument value.
- `REQ-001`: helper unit tests in `tests/agent/test_message_schema.py`.
- Regression: `tests/agent/test_session_persister.py`, `tests/agent/test_message_schema.py`, `tests/agent/test_ephemeral_filtering_security.py`, `tests/agent/test_repl.py`.

## Documentation Impact
Yes, generated only: the generated agent reference document is regenerated (REQ-005). No prose document describes the internal warning (a search of `docs/` for the warning text and "unexpected keys" finds only the schema module's own validation messages, in tests).

## Assumptions
- A history message never carries `source` (documented on `append_message`), so the helper needs no `source` allowance (checked in Step 2).
- The authorized ephemeral keys for the helper are the union over `TRUSTED_SOURCES`, matching `_ALL_EPHEMERAL_KEYS`; per-source authorization is a validation-time concern, not a session-end one.
- Overlap with other Frozen Plans is judged by `tools/check_plan_target_overlaps.py` in Step 8b.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which handlers and files receive the `agent.session_persister` logger in production and who can read them. | The logging configuration was not traced; the priority assumes the agent log. | Not needed for the fix (the content is removed from the log); an operator may confirm during deploy verification. | False |
| UNK-02 | Whether other call sites log whole history messages. | Not searched by this Plan; the Issue lists it as out of scope. | Separate issue if a search finds any. | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/message_schema.py` | Modify | Low: additive public helper; `validate_message` untouched | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/session_persister.py` | Modify | Low: one method, called at session shutdown | 4 | N/A | not applicable (rsynced) |
| `tests/agent/test_session_persister.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_message_schema.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_13_reference-api-generated.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Decision 1, how to define "allowed". Alternatives: (a) whitelist only, as the Issue suggests; (b) whitelist plus ephemeral keys; (c) reuse `validate_message`. Chosen: (b) through a new public helper. (a) would keep logging full content for stored ephemeral hints; (c) rejects them for lack of a `source`. Compatibility: purely additive in the schema module; `validate_message` and its tests are unchanged.

Decision 2, the warning text. Role and sorted key names only, so no content or value can reach the log, which satisfies the constraint that nothing from the message appears in the new text.

Consumer scan: a new public function is added and no existing symbol, constant, or schema changes, so no consumer scan is required beyond the reference document, which is a target.

## Implementation steps
1. **Phase 1: Failing tests first**
   - [ ] Add the persister `caplog` tests and record that they fail on the current code (REQ-004; `tests/agent/test_session_persister.py`).
2. **Phase 2: Schema helper**
   - [ ] Add `unexpected_message_keys` and its unit tests (REQ-001, REQ-004; `scripts/agent/message_schema.py`, `tests/agent/test_message_schema.py`).
3. **Phase 3: Persister**
   - [ ] Use the helper and log only the role and key names (REQ-002, REQ-003; `scripts/agent/session_persister.py`).
4. **Phase 4: Generated reference**
   - [ ] Run `uv run python tools/generate_reference_table.py --type agent` and verify with `--check` (REQ-005; `docs/23_agent/agent_13_reference-api-generated.md`).
5. **Phase 5: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` for the `scripts/` change; prerequisite: the change is committed and pushed first, and deploying is the user's decision (approval gate). Run `uv run python tools/check_docs_consistency.py --domain agent` (REQ-002; `scripts/agent/session_persister.py`).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/session_persister.py` | Unit with `caplog` and a stub memory service | `uv run pytest tests/agent/test_session_persister.py -v` | New tests fail before Phase 3, pass after |
| `scripts/agent/message_schema.py` | Unit | `uv run pytest tests/agent/test_message_schema.py tests/agent/test_ephemeral_filtering_security.py -v` | All pass |
| REPL shutdown path | Unit | `uv run pytest tests/agent/test_repl.py -v` | All pass |
| Touched Python files | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean, no new errors |
| `scripts/agent/` | Security / architecture | `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | No new findings |
| Changed lines | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent |
| Generated reference | Generated-doc drift | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Reference document | Docs checkers | `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent` | No findings |

Baseline (Step 5): `radon cc` reports `SessionPersister.persist_session_memories` at B (8) and `persist_session_diagnostics` at C (19, untouched), and `validate_message` at B (8); the change MUST NOT raise `persist_session_memories` above its current grade. `vulture` shows no finding in the two Python targets; diff-cover is recorded at implementation time.

## Risks
- **Risk**: The helper and `validate_message` drift apart on allowed keys → **Mitigation**: both read `ROLE_KEY_WHITELIST` and `TRUSTED_SOURCES`; a helper unit test pins agreement for every role.
- **Risk**: A new key added to `LLMMessage` is missing from the schema and triggers the warning again → **Mitigation**: the warning then names the key without content, which is the intended signal.
- **Risk**: A future log line re-introduces content → **Mitigation**: the persister test asserts the content string is absent from all captured records.
- **Risk**: The generated reference document drifts and fails CI → **Mitigation**: Phase 4 regenerates and checks it; a manual edit of the generated block is not allowed.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: failing persister caplog tests | Completed | — | 20261105-104710 |  |
| 2 | Phase 2: schema helper and its tests | Completed | — | 20261105-104710 |  |
| 3 | Phase 3: persister uses the helper | Completed | — | 20261105-104710 |  |
| 4 | Phase 4: regenerate the generated reference | Completed | — | 20261105-104710 |  |
| 5 | Phase 5: deployment hand-off and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-070039_01_scripts_agent_message_schema.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-070039_02_scripts_agent_session_persister.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261105-070039_03_tests_agent_test_session_persister.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261105-070039_04_tests_agent_test_message_schema.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-070039_05_docs_23_agent_agent_13_reference-api-generated.md.md | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/done/20261031-180407_memlogleak001_memory-persist-logs-messages.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-114342
- **Related target files**: scripts/agent/message_schema.py, scripts/agent/session_persister.py, tests/agent/test_session_persister.py, tests/agent/test_message_schema.py, docs/23_agent/agent_13_reference-api-generated.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; Implementation Intent | scripts/agent/message_schema.py | 2 | AC-1 | Helper unit tests | Derived from confirmed evidence |
| REQ-001 | Required Changes bullet 1 | tests/agent/test_message_schema.py | 2 | AC-1 | Helper unit tests | Derived from confirmed evidence |
| REQ-002 | Required Changes bullet 1; Constraints bullets 1-2 | scripts/agent/session_persister.py | 3 | AC-2 | Ordinary-message persister test | Explicit in issue |
| REQ-003 | Required Changes bullet 2; Constraints bullet 3 | scripts/agent/session_persister.py | 3 | AC-3 | Unexpected-key persister test | Explicit in issue |
| REQ-004 | Required Changes bullet 3; Acceptance Criteria bullet 3 | tests/agent/test_session_persister.py | 1 | AC-2, AC-3, AC-4 | New `caplog` tests | Explicit in issue |
| REQ-005 | Derived: new public function listed in generated reference | docs/23_agent/agent_13_reference-api-generated.md | 4 | AC-5 | `tools/generate_reference_table.py --check` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261105-070039 -->
