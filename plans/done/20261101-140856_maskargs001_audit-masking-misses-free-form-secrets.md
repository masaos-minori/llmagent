## Goal
- Make `mask_args()` additionally redact content-pattern secrets inside string values (reusing the shared `secrets_masker` redaction) so the persisted audit `args_preview`, the tool-runner logging and the plan-blocked notice no longer carry a secret embedded in a free-form argument such as a `shell_run` `command`, while the key-based `masked_fields` masking and the interactive approval preview stay exactly as they are.

## Priority
Medium

## Scope
- **In-Scope**:
  - After the existing key-based check, run each remaining string value (any depth, including list items) through `secrets_masker._mask_secrets()` inside `tool_result_formatter._mask_value()`, so every `mask_args()` consumer is covered by one change.
  - Tests: unit tests for `mask_args()`, one for each audit writer's `args_preview`, one for the tool-runner "Tool call" log and emit path.
  - Update the documentation sentence that defines `masked_fields` masking.
  - Record the approval-preview decision (default: leave raw, matching the documented "unmasked by design" statement) without changing `check_approval` or `build_preview`.
- **Out-of-Scope**:
  - `scripts/agent/secrets_masker.py` pattern coverage (secmask001, diagmask001); this Plan adds no patterns and does not edit that module.
  - `scripts/agent/diagnostic_store.py` secret detection.
  - Scrubbing the approval preview built by `build_preview()` (owner decision, UNK-02; no change unless decided).
  - Scrubbing dict keys, non-string values, or treating a sensitive key name as a reason to mask its value (key-name-aware masking beyond `masked_fields`).
  - Tool result text logged by `_emit_tool_result` (`Tool result ... (full)`) and the persisted tool-result message content, which are not argument masking.
  - Any change to `tool_audit.py` (`_bounded_preview`, `audit_tool_exec`, `audit_approval`) or `tool_approval.py`.
  - Restructuring the key-based logic of `mask_args()` / `_mask_value()` (Issue Constraint).
- **Dependencies**:
  - `issues/done/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md` (Plan `plans/20261101-140116_secmask001_secrets-masker-leaks-unmasked-value.md`, Frozen, all Phases `Pending`): this Plan reuses the masker, so its coverage is whatever `_mask_secrets` covers when this lands; secmask001 adds the colon forms and re-pins the pattern count in `tests/agent/test_secrets_masker.py`. It is an ordering preference, not a technical prerequisite: this Plan's tests use shapes the current masker already masks (`key=value`, `Authorization: Bearer`), so it can land before or after secmask001 (non-blocking, UNK-01). Landing secmask001 first makes the audit scrub cover colon-form secrets.
  - `plans/20261101-140448_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md` (Issue `issues/done/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md`, Frozen, Phases `Pending`): extends `SECRET_PATTERNS` (bare JWT, `scheme://user:pass@host`, more key names) and adds a shared detection function. This Plan calls only `_mask_secrets`, so it neither needs nor conflicts with the detection function and gains the new shapes automatically once that Plan lands; no file overlap.
  - Fix order against siblings that also touch `audit_tool_exec` in `scripts/agent/tool_audit.py` (`issues/20261003-180336_assertaudit001_audit-assert-risks-post-execution-crash.md`, `issues/20261003-180330_toolaudit001_audit-drops-denied-gateway-tool-calls.md`, `issues/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md`; none planned yet): this Plan does not modify `tool_audit.py`, only `tests/agent/test_tool_audit.py` (shared test file, merge-conflict risk only). No ordering requirement; whichever lands later rebases its additions to `tests/agent/test_tool_audit.py`. `args_preview` is built from `mask_args()`, so a sibling that reorders masking and `_bounded_preview` inside `audit_tool_exec` must keep calling `mask_args()` first.

## Background
`mask_args()` is used for the plan-blocked emit (`run_approval_checks`), both audit events (`audit_approval`, `audit_tool_exec`, whose `args_preview` goes through `_bounded_preview` after masking) and the tool-runner "Tool call" log line and REPL emit (`_collect_tool_result_msgs`). It delegates to `_mask_value()`, which replaces values whose key is in `ctx.cfg.tool.masked_fields` (shipped default `content`, `old_text`, `new_text`) at any depth, including inside lists. The interactive approval preview (`build_preview()`, defined in `tool_result_formatter.py`) is built from the raw arguments and is deliberately not masked; `docs/23_agent/agent_08_03_configuration-tools-memory.md` documents this exception ("unmasked by design", the reader is the person who supplied the arguments).

## Problem
Verified in Step 2: `_mask_value()` has no string-content handling, so a secret inside a string value under a key not listed in `masked_fields` reaches `args_preview` and the log unchanged. Probing `_mask_secrets` on shell-command shapes: `export API_KEY=abcd && run`, `curl https://h/?token=abc&x=1` and `curl -H "Authorization: Bearer abc123" https://h` are masked; `curl -u user:pass https://h/x` (the Issue's own example) and `psql postgres://u:pw@h/db` are NOT masked by the current masker, and neither is `password: hunter2`. So reusing the masker fixes the `key=value` / header / Bearer shapes immediately, the colon form once secmask001 lands, the URL-credential form once diagmask001 lands, and `curl -u user:pass` by neither (UNK-03).

## Reason for Change
The audit trail is durable. A free-form value such as an LLM-generated shell command cannot be covered by a configured field-name list, so a secret in it is persisted verbatim in `args_preview` and logged on every tool call.

## Implementation Intent
Add a content-pattern pass at the single choke point, the string branch of `_mask_value()`, by calling the shared `_mask_secrets()`; key-based masking runs first and keeps precedence. Leave the approval preview raw and record that as the decision.

## Requirements
- `REQ-001`: `mask_args()` redacts content-pattern secrets inside string values at any depth (nested dicts and list items) using `secrets_masker._mask_secrets()`, with no second pattern set; a string with no secret is returned unchanged, non-string values and dict keys are untouched, and the input `args` is not mutated.
- `REQ-002`: Values under a `masked_fields` key are still replaced by `"***"` exactly as before (key-based masking runs first, takes precedence, and is not restructured).
- `REQ-003`: The persisted audit `args_preview` of both `audit_approval` and `audit_tool_exec` carries the scrubbed values (a secret embedded in a free-form value under an unlisted key does not appear), including when the preview is replaced by the oversized `truncated` envelope.
- `REQ-004`: The tool-runner "Tool call" log line and the REPL tool-call emit carry the scrubbed arguments.
- `REQ-005`: The approval preview behavior is unchanged (decision: stays raw, per the existing documented rationale, pending the owner's confirmation in UNK-02): `check_approval` and `build_preview` are not modified.
- `REQ-006`: The documentation of `masked_fields` masking states that string values are additionally content-scrubbed, names the coverage as that of the shared masker, and keeps the approval-preview exception.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/tool_result_formatter.py | In `_mask_value()` add a string branch that returns `_mask_secrets(value)` after the key-based dict check; import `_mask_secrets` from `agent.secrets_masker`; update the `mask_args()` / `_mask_value()` docstrings | `_mask_value()` returns every non-dict, non-list value as-is, so no string content is scanned | REQ-001, REQ-002, REQ-005 / AC-1, AC-2, AC-5 | `_mask_value` handles only `dict` and `list`; `mask_args` is its only entry and delegates with `cast`; file has no `agent.*` import today and `secrets_masker` imports only `re`, so no cycle; module is 4810 B (checked in Step 2 and Step 3) | tests/agent/test_tool_result_formatter.py | Verified |
| tests/agent/test_tool_result_formatter.py | Add `mask_args` content-scrub tests: shell `command` with `key=value` and `Authorization: Bearer`, nested dict, list item, no-secret string unchanged, non-string untouched, key precedence, input not mutated, idempotence | The `mask_args` test class pins only key-based behavior (`test_masks_specified_fields`, nested, list, no-mutation) | REQ-001, REQ-002 / AC-1, AC-2, AC-6 | Tests for `mask_args` exist and call it with explicit `masked_fields` lists, e.g. `["password"]`, `["secret"]`; none passes a secret-bearing string under an unlisted key (checked in Step 2) | tests/agent/test_tool_result_formatter.py itself | Verified |
| tests/agent/test_tool_audit.py | Add parametrized tests (both writers) that a secret embedded in a free-form value under an unlisted key is absent from the logged `args_preview`, plain and oversized-envelope cases | `_args_preview_after_write` and `TestArgsPreviewBound` cover only key-based masking and the cap; no content-scrub assertion | REQ-003 / AC-3 | Helper `_args_preview_after_write(writer, args)` runs `audit_approval` / `audit_tool_exec` with `masked_fields = ["secret"]` and returns the logged `args_preview`; it is reusable (checked in Step 2) | tests/agent/test_tool_audit.py itself | Verified |
| tests/agent/test_tool_runner.py | Add a test that `_collect_tool_result_msgs` logs (caplog, logger `agent.tool_runner`) and emits (patched `emit_tool_call`) the scrubbed arguments | No test asserts what the "Tool call (turn ...)" log and `emit_tool_call` receive; `_collect_tool_result_msgs` is already imported and exercised in this file | REQ-004 / AC-4 | `_collect_tool_result_msgs` calls `mask_args` then `_log_and_emit_tool_call`, which logs `"Tool call (turn %s): %s(%s)"` and calls `emit_tool_call(name, _json_dumps(masked))`; the file's caplog pattern at the long-result tests is reusable (checked in Step 2) | tests/agent/test_tool_runner.py itself | Verified |
| docs/23_agent/agent_08_03_configuration-tools-memory.md | Extend the `masked_fields` bullet: string values are also scrubbed for secret patterns by the shared masker before reaching the same sinks; approval preview exception unchanged | The bullet says masking replaces configured keys only and describes the sinks; it becomes incomplete after this change (the Issue's "N/A: no document describes mask_args()" claim is wrong) | REQ-006 / AC-7 | The `masked_fields` bullet and its two sub-bullets exist, including "The interactive approval preview is the one deliberate exception and stays unmasked" (checked in Step 2) | N/A: documentation (docs checkers in the Validation plan) | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/secrets_masker.py | Defines `_mask_secrets` and `SECRET_PATTERNS` (pure regex, no imports beyond `re`); read-only here, extended by the secmask001 and diagmask001 Plans | REQ-001 |
| scripts/agent/tool_audit.py | `audit_approval` and `audit_tool_exec` build `args_preview` as `_bounded_preview(mask_args(...))`; `_extract_resource_scope` reads path/branch values from the masked tree; must stay unchanged | REQ-003 |
| scripts/agent/tool_runner.py | `_collect_tool_result_msgs` and `_log_and_emit_tool_call` consume `mask_args`; must stay unchanged | REQ-004 |
| scripts/agent/tool_approval.py | `run_approval_checks` masks for the plan-blocked emit; `check_approval` shows the raw `build_preview` (the unchanged approval preview) | REQ-005 |
| scripts/agent/config_dataclasses.py | `ToolConfig.masked_fields` default (`content`, `old_text`, `new_text`) | REQ-002 |
| config/agent.toml | Shipped `masked_fields` value | REQ-002 |
| tests/agent/test_secrets_masker.py | Pins the masker's pattern behavior and count that secmask001 and diagmask001 change; this Plan must not depend on a pinned count | REQ-001 |
| plans/20261101-140116_secmask001_secrets-masker-leaks-unmasked-value.md | Prerequisite-ordering Plan: colon-form patterns, apply-order and idempotence constraints | REQ-001 |
| plans/20261101-140448_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md | Sibling Plan extending `SECRET_PATTERNS` and adding the detection function | REQ-001 |
| docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md | Describes `args_preview` bounding "after masking"; read to confirm no statement of masking coverage needs changing | REQ-006 |
| docs/00_index.md | "Document References by Task" routing for the docs row and the docs checkers | REQ-006 |

## Acceptance Criteria
- AC-1 (REQ-001): `mask_args({"command": "export API_KEY=abcd && run"}, [])` and `{"command": "curl -H \"Authorization: Bearer abc123\" https://h"}` return values in which `abcd` / `abc123` do not appear; the same holds for a string nested in a dict and for a string inside a list.
- AC-2 (REQ-001, REQ-002): a value under a `masked_fields` key is still `"***"`; a string with no secret (for example a plain path) is returned unchanged; ints, bools and dict keys are untouched; the original `args` object is unchanged after the call; applying `mask_args` to its own output equals applying it once.
- AC-3 (REQ-003): for both `audit_approval` and `audit_tool_exec`, the logged `args_preview` for `{"command": "<secret-bearing string>"}` (key not in `masked_fields`) does not contain the secret value, and with an oversized payload the secret is also absent from the `truncated` envelope's `preview` string.
- AC-4 (REQ-004): after `_collect_tool_result_msgs` with such arguments, the captured "Tool call" log record and the `emit_tool_call` argument do not contain the secret.
- AC-5 (REQ-005): `git diff` shows `build_preview`, `check_approval` and `tool_approval.py` unchanged; the owner decision is recorded in UNK-02.
- AC-6 (REQ-001, REQ-002): all pre-existing tests in `tests/agent/test_tool_result_formatter.py`, `tests/agent/test_tool_audit.py` and `tests/agent/test_tool_runner.py` pass unchanged apart from the added tests.
- AC-7 (REQ-006): the `masked_fields` bullet in the target doc states the additional content scrub and the preserved preview exception, and the docs checkers pass.

## Tests
- Unit (REQ-001, REQ-002): `tests/agent/test_tool_result_formatter.py` parametrized over secret shapes the current masker covers (`key=value`, `Authorization: Bearer`, standalone `Bearer`), nesting (dict in list in dict), key precedence, no-secret passthrough, non-string passthrough, no mutation, idempotence. A colon-form case is added only if secmask001 has landed.
- Audit (REQ-003): `tests/agent/test_tool_audit.py` parametrized over both writers using `_args_preview_after_write`, plain and oversized cases.
- Runner (REQ-004): `tests/agent/test_tool_runner.py` with `caplog` on `agent.tool_runner` and `patch("agent.tool_runner.emit_tool_call")`.
- Performance guard (REQ-001): a unit test that a large (several hundred kB) non-secret string completes quickly and is returned unchanged.
- Regression (AC-6): the three test modules above plus `tests/agent/test_audit_log_format.py`, `tests/agent/test_tool_approval_paths.py` and `tests/agent/test_tool_output.py` run unchanged.

## Documentation Impact
Required (REQ-006): `docs/*.md` describes `masked_fields` masking and the unmasked approval preview today (the Issue's "N/A" claim is incorrect). Update the `masked_fields` bullet in the target doc listed in `Implementation Target Files` (reached via `docs/00_index.md` "Document References by Task", Agent row; configuration and tools). State the content scrub in terms of "the shared secrets masker" without listing its patterns, because secmask001 and diagmask001 change them. Run the docs checkers from `routing.md` Tools after the edit.

## Assumptions
- Per-value scrubbing (not serialized-JSON scrubbing) is the chosen mechanism; consequence: the masker's quoted-JSON-key pattern, which needs `"key": "value"` text, does not fire on a dict argument such as `{"api_key": "abc"}` whose value `abc` has no secret shape. That case remains covered only by `masked_fields`. Falsifiable by the AC-1/AC-2 tests; follow-up in UNK-04 if the owner wants it.
- The scrub lives in `mask_args()`/`_mask_value()` rather than `_bounded_preview` because `mask_args()` is the shared choke point for audit, plan-blocked and tool-runner logging (the Issue allows either); `_bounded_preview` would cover only the audit events.
- `_extract_resource_scope` reads path/branch values from the masked tree, so a path value that itself matches a secret pattern is scrubbed in `resource_scope` too; accepted as a security-over-fidelity trade-off, falsifiable by the AC-2 plain-path test.
- Path B: 5 target files (more than 3), no interface change; classification recorded in Step 3.
- Step 8b: `tools/check_plan_target_overlaps.py` names this Plan for two test files, both judged compatible (add-only, disjoint test additions, no source-file overlap): `tests/agent/test_tool_audit.py` is also targeted by `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (adds an `attempt_number` test for the `stage_completed` event; this Plan adds `args_preview` scrub tests), and `tests/agent/test_tool_runner.py` is also targeted by `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` (adds a non-READ side-effect-flag test; this Plan adds a tool-call log test). Neither Plan touches `mask_args` or `tool_result_formatter.py`; any order works, the later one rebases its additions.
- The key-based mask replaces the whole value with `"***"` before the string branch can run, so the content scrub never sees masked values; the content scrub's own output is idempotent on `***MASKED***` per secmask001 AC-5.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether this Plan must wait for secmask001 (and diagmask001) so the audit scrub covers colon-form and URL-credential secrets | Owner sequencing preference | Implement secmask001 first if colon-form coverage in the audit log is wanted at the same release; otherwise land independently with the covered shapes; see `plans/20261101-140116_secmask001_secrets-masker-leaks-unmasked-value.md` | False |
| UNK-02 | Whether the approval preview should be scrubbed or stay raw so the operator can read the actual command (Issue Unresolved Questions; owner decision) | No owner decision; the existing doc states "unmasked by design" | Default if no decision: stay raw (REQ-005, matches the documented rationale); if the owner decides to scrub, amend this Plan to add `scripts/agent/tool_approval.py` and its tests as target files | False |
| UNK-03 | `curl -u user:pass` (the Issue's own example) and `scheme://user:pass@host` forms: the current masker matches neither, so the audit log still carries them after this change; diagmask001 adds the URL form, nothing adds `-u user:pass` | Whether `-u user:pass` coverage is wanted, and in which plan | Out of this Plan's scope (Issue Out of Scope: `secrets_masker.py` coverage); owner may file a masker-coverage issue | False |
| UNK-04 | Whether a sensitive key name (for example `api_key`) in an unlisted dict argument should force-mask its value even when the value has no secret shape | Not requested by the Issue | Out of scope here; owner may extend `masked_fields` config or file an issue | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/tool_result_formatter.py | Modify | Medium (`mask_args` feeds the plan-blocked emit, both audit events and tool-runner logging; every string argument now passes through the regex set) | 2 commits (30d) | N/A | Deployed runtime file under `scripts/agent/`: takes effect only after a deploy (hand-off to `skills/deploy/SKILL.md`) |
| tests/agent/test_tool_result_formatter.py | Modify | Low | 4 commits (30d) | N/A | None: tests are not deployed |
| tests/agent/test_tool_audit.py | Modify | Low (shared with the later audit_tool_exec sibling issues) | 4 commits (30d) | N/A | None: tests are not deployed |
| tests/agent/test_tool_runner.py | Modify | Low | 12 commits (30d) | N/A | None: tests are not deployed |
| docs/23_agent/agent_08_03_configuration-tools-memory.md | Modify | Low | 18 commits (30d) | N/A | None: docs are not deployed |

## Design
- Path B (Step 3): 5 target files. Architecture: `agent.tool_result_formatter` gains an import of `agent.secrets_masker` (both in package `agent`; `secrets_masker` imports only `re`, so no import cycle and no layer-contract change; `tool_audit` already imports `agent.*` modules the same way). Callers of `mask_args` (rg over `scripts/`): `tool_runner`, `tool_approval`, `tool_audit` (two sites); none changes. Baseline: `radon cc` on the target gives `_mask_value` B (6) and `mask_args` A (1) before the change; `bandit` reports no issues on the target; `vulture` reports nothing on it; the diff-cover number needs a full-suite run and is deferred to the implementation phase, which must reach the threshold in `rules/toolchain.md`.
- Decision 1, where to scrub. Alternatives: (a) string branch of `_mask_value` (chosen: one choke point covering audit, plan-blocked and runner logging, preserves the dict-in/dict-out shape that `_extract_resource_scope` and `_bounded_preview` rely on); (b) scrub the serialized JSON inside `_bounded_preview` (covers audit only, would turn the dict into text and break the `args_preview` structure when below the cap); (c) a new wrapper over `mask_args` (extra layer, no benefit). Compatibility impact of (a): `args_preview` values that match a secret pattern change from raw to masked; the dict structure and `truncated` envelope are unchanged.
- Decision 2, which function. `secrets_masker._mask_secrets` is the only masking entry point today and is already imported across modules despite its underscore (`startup_mcp_starter`, `http_lifecycle_*`); reuse it as is. diagmask001's detection function is not needed. If the owner wants a public name, renaming is a separate change.
- Order: dict-key check first (`"***"` for listed keys, never scrubbed), then recursion, then the string scrub on leaves. Because the scrub is a pure function of one string, order against secmask001's internal pattern ordering is that module's concern (its `token: Bearer abc` ordering constraint); this Plan adds no ordering of its own.
- Approval preview (REQ-005): left raw, consistent with the documented rationale; not implemented as scrubbing. This is a recorded default, with the owner decision in UNK-02.
- Failure path: `_mask_secrets` is pure regex and cannot raise on `str`; no new error handling. Performance: six bounded regexes per string leaf per call; large strings under unlisted keys (for example GitHub file-write bodies if not listed) cost linear time; guarded by the large-input test.

## Implementation steps
1. **Phase 1: Tests first (revertable alone)**
   - [ ] Add failing `mask_args` content-scrub tests (REQ-001, REQ-002; tests/agent/test_tool_result_formatter.py)
   - [ ] Add failing audit `args_preview` tests for both writers, plain and oversized (REQ-003; tests/agent/test_tool_audit.py)
   - [ ] Add the tool-runner log/emit test (REQ-004; tests/agent/test_tool_runner.py)
2. **Phase 2: Core logic**
   - [ ] Add the string branch calling `_mask_secrets` in `_mask_value`, the import, and docstring updates, leaving the key-based logic and `build_preview` untouched (REQ-001, REQ-002, REQ-005; scripts/agent/tool_result_formatter.py)
3. **Phase 3: Documentation**
   - [ ] Extend the `masked_fields` bullet for the content scrub and the preserved preview exception (REQ-006; docs/23_agent/agent_08_03_configuration-tools-memory.md)
4. **Phase 4: Deployment & Verification**
   - [ ] Run the validation sequence in the Validation plan, including the regression modules; hand off to `skills/deploy/SKILL.md` for the `scripts/` change (prerequisite: the change is committed and pushed first; deploying is the user's decision) (REQ-001..REQ-006; scripts/agent/tool_result_formatter.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/tool_result_formatter.py, tests/agent/test_tool_result_formatter.py | Unit | `uv run pytest tests/agent/test_tool_result_formatter.py` | New and existing tests pass |
| tests/agent/test_tool_audit.py | Unit | `uv run pytest tests/agent/test_tool_audit.py` | New and existing tests pass |
| tests/agent/test_tool_runner.py | Unit | `uv run pytest tests/agent/test_tool_runner.py` | New and existing tests pass |
| Mask_args consumers | Integration (regression) | `uv run pytest tests/agent/test_audit_log_format.py tests/agent/test_tool_approval_paths.py tests/agent/test_tool_output.py` | Pass unchanged (AC-6) |
| scripts/agent/tool_result_formatter.py | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml` per `rules/toolchain.md` | Clean |
| scripts/agent/tool_result_formatter.py | Size gate | `uv run python tools/check_module_size.py` | Pass |
| scripts/agent/tool_result_formatter.py | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` per `rules/toolchain.md` | At or above threshold |
| scripts/agent/ | Generated reference drift | `uv run python tools/generate_reference_table.py --check` | Pass |
| docs/23_agent/agent_08_03_configuration-tools-memory.md | Docs checks | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent` | Pass |

## Risks
- **Risk**: Coverage is bounded by the masker: `curl -u user:pass` and `scheme://user:pass@host` stay unmasked until other Plans land (likelihood High for the first) → **Mitigation**: recorded in UNK-03; documentation states coverage is that of the shared masker; secmask001 and diagmask001 extend it with no change here.
- **Risk**: Over-masking (the `key=value` patterns use `(\S+)`, so `token=abc&x=1` loses `&x=1`, and `Authorization:` masks the next word) makes audit previews less readable (likelihood Medium) → **Mitigation**: accepted for a security control; tests pin only the absence of the secret value, not the exact masked text.
- **Risk**: Large string arguments under unlisted keys add regex cost on every tool call (likelihood Low) → **Mitigation**: the patterns are linear and non-nested; the large-input test guards a regression; large known-bulky keys can be added to `masked_fields` config.
- **Risk**: A path or branch value in `resource_scope` matching a secret pattern is altered (likelihood Low) → **Mitigation**: accepted; falsifiable by the plain-path test.
- **Risk**: The operator may expect the approval preview to be scrubbed (likelihood Low) → **Mitigation**: UNK-02 default keeps it raw as documented; amend the Plan if the owner decides otherwise.
- **Risk**: Sibling Plans for `audit_tool_exec` (assertaudit001, toolaudit001, idemaudit001) edit `tests/agent/test_tool_audit.py` concurrently (likelihood Medium) → **Mitigation**: no source-file overlap (this Plan does not edit `tool_audit.py`); append-only test additions; the later one rebases.
- **Risk**: The `scripts/` change takes effect only after deploy → **Mitigation**: Phase 4 hand-off to `skills/deploy/SKILL.md` after commit and push.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first: mask_args, audit args_preview, tool-runner log tests (tests/agent/test_tool_result_formatter.py, tests/agent/test_tool_audit.py, tests/agent/test_tool_runner.py) | Completed | — | 2026-11-02 | Procedures 02, 03, 04; red evidence: 3+4+2 failed across the three files |
| 2 | Core logic: string branch in `_mask_value` calling `_mask_secrets` (scripts/agent/tool_result_formatter.py) | Completed | — | 2026-11-02 | Procedure 01; _mask_value string branch calls _mask_secrets |
| 3 | Documentation: extend the `masked_fields` bullet (docs/23_agent/agent_08_03_configuration-tools-memory.md) | Completed | — | 2026-11-02 | Procedure 05; masked_fields bullet extended; docs checkers exit 0 |
| 4 | Deployment and verification: validation sequence, regression modules, deploy hand-off (scripts/agent/tool_result_formatter.py) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-132615_02_tests_agent_test_tool_result_formatter.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-132615_03_tests_agent_test_tool_audit.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-132615_04_tests_agent_test_tool_runner.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-132615_01_scripts_agent_tool_result_formatter.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-132615_05_docs_23_agent_agent_08_03_configuration-tools-memory.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180335_maskargs001_audit-masking-misses-free-form-secrets.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-140856
- **Related target files**: scripts/agent/tool_result_formatter.py, tests/agent/test_tool_result_formatter.py, tests/agent/test_tool_audit.py, tests/agent/test_tool_runner.py, docs/23_agent/agent_08_03_configuration-tools-memory.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (content-pattern scrub); `_mask_value` has no string branch | scripts/agent/tool_result_formatter.py | 2 | AC-1, AC-2 | Tests: mask_args unit | Confirmed by repository evidence |
| REQ-001 | Issue Testing Expectations (free-form value case) | tests/agent/test_tool_result_formatter.py | 1 | AC-1, AC-2 | Tests: mask_args unit, performance guard | Explicit in issue |
| REQ-002 | Issue Constraints and Acceptance Criteria (key-based masking unchanged) | scripts/agent/tool_result_formatter.py | 2 | AC-2, AC-6 | Tests: key precedence; regression modules | Explicit in issue |
| REQ-002 | Issue Testing Expectations (secret under `masked_fields` key) | tests/agent/test_tool_result_formatter.py | 1 | AC-2 | Tests: key precedence | Explicit in issue |
| REQ-003 | Issue Acceptance Criteria (`args_preview` redacted); `audit_*` build `args_preview` from `mask_args` | tests/agent/test_tool_audit.py | 1 | AC-3 | Tests: audit args_preview | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes (tool-runner logging path test); `_collect_tool_result_msgs` logs masked args | tests/agent/test_tool_runner.py | 1 | AC-4 | Tests: runner log/emit | Confirmed by repository evidence |
| REQ-005 | Issue Required Changes and AI Implementation Instruction (approval preview decision); Unresolved Questions | scripts/agent/tool_result_formatter.py | 2 | AC-5 | Validation plan: `git diff` check | Needs confirmation |
| REQ-006 | `agent_08_03` `masked_fields` bullet documents the sinks and the preview exception (Issue Documentation Impact says N/A) | docs/23_agent/agent_08_03_configuration-tools-memory.md | 3 | AC-7 | Validation plan: docs checkers | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-132615 -->