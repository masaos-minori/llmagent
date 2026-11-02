## Goal
- Make `DiagnosticStore.save()`'s plaintext-path guard use the shared `secrets_masker` detection (one implementation for log masking and diagnostic persistence) and widen it to unlisted key names, other separators, a bare JWT and `scheme://user:pass@host` credentials, without changing the guard's `RuntimeError` contract or the encrypted path.

## Priority
Medium

## Scope
- **In-Scope**:
  - Add a shared detection entry point to `scripts/agent/secrets_masker.py` and make `DiagnosticStore.save()` call it instead of its private `_SENSITIVE_PATTERNS`.
  - Extend the shared pattern set: key names the current guard covers but the masker does not (`bearer`, `auth_token` / `access_token` / `client_secret` in quoted-JSON-key form), the Issue's unlisted key names (`authorization`, `credential`, `private_key`), other separators, a bare JWT, and `scheme://user:pass@host`.
  - Tests for the new coverage and for every shape the current guard already blocks; update the one masker test that pins the pattern count.
  - Update the documentation that names `_SENSITIVE_PATTERNS` and the one that lists the masker's shapes (both go stale).
- **Out-of-Scope**:
  - `diagnostics.encryption_key` encryption itself and any behavior when the key is set (Issue Constraint).
  - The `RuntimeError`-on-detection behavior and message (only what triggers it widens).
  - `scripts/agent/tool_result_formatter.py::mask_args()` key-based audit masking (tracked by `issues/20261003-180335_maskargs001_audit-masking-misses-free-form-secrets.md`).
  - The `_filter_sensitive_fields()` redaction and the `_filter_failed` carve-out.
  - Making the not-yet-contained `DiagnosticStore.save()` callers catch the refusal (see Risks and UNK-03).
- **Dependencies**: Implement after `plans/20261101-140116_secmask001_secrets-masker-leaks-unmasked-value.md` (Issue `issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md`, archived in `issues/done/`), whose Phases are all still `Pending`. That Plan adds the colon-form patterns to `SECRET_PATTERNS`, updates `test_pattern_count_grew_by_exactly_one` (currently 6) and the masker section of the operations doc; this Plan builds on that final pattern set and re-updates the same count assertion and the same doc section, so landing it first avoids both a merge conflict and inheriting the colon gap. It is an ordering preference, not a technical impossibility, hence UNK-04 is non-blocking. Sibling ordering within the series: `issues/20261003-180335_maskargs001_audit-masking-misses-free-form-secrets.md` also depends on secmask001 and is independent of this Plan. No other active Plan targets the five source/test/doc files below beyond secmask001 (Step 8b: see Assumptions).

## Background
`DiagnosticStore.save()` persists diagnostics to `session_diagnostics`. Redaction of configured payload fields (`_filter_sensitive_fields`) runs first; then, when `diagnostics.encryption_key` is empty (the shipped default; no production caller passes `encrypt=True`) and the filter did not fail, a private regex list `_SENSITIVE_PATTERNS` is searched and a match raises `RuntimeError("Sensitive information detected ...")`. The accepted storage posture ("plaintext-with-redaction", decided 2026-10-25) names this guard as the fail-closed layer. `scripts/agent/secrets_masker.py` keeps a separate `SECRET_PATTERNS` list used to mask log text; the two lists share no code and cover different shapes. Related earlier work: the diagstore001 fix contained the `RuntimeError` in the two turn-path callers (commit `9a6f41e13`).

## Problem
Verified by running both implementations on probe strings (Step 2). The guard's value group `[a-zA-Z0-9_\-\.]{16,}` matches any 16-character prefix, so a JWT under a listed key (`token: eyJ...`) is detected. Real gaps of the guard: (1) key names not in its list (`passwd=...`, `private_key=...`, `credential: ...`, `authorization: Basic ...` are not detected; `Authorization: Bearer ...` is, via the `bearer` word); (2) separators other than whitespace, `:` and `=` (`api_key => ...` is not detected); (3) bare values with no key (a raw JWT, `postgres://user:pass@host/db`, `https://admin:pw@host/`) are not detected; (4) not stated in the Issue: values shorter than 16 characters are never detected (`password=hunter2` is persisted), whereas the masker has no minimum. In the other direction the masker does not cover shapes the guard blocks today: `{"client_secret": "..."}`, `{"bearer": "..."}` and `{"auth_token": "..."}` in quoted-JSON form are not changed by `_mask_secrets`, so the guard cannot simply delegate to the masker's current patterns.

## Reason for Change
A secret shape the guard does not recognise is written to `session_diagnostics` in plaintext by default. Two divergent implementations also mean a fix to one does not benefit the other (secmask001 is fixing colon forms in the masker only).

## Implementation Intent
Put detection in `secrets_masker.py` as a public function built on the same `SECRET_PATTERNS`, so there is one pattern set, and have the guard call it. Detection is defined as "masking the text would change it", which reuses every pattern, is automatically idempotent on already-masked values, and needs no per-pattern duplication. Extend `SECRET_PATTERNS` (not a second list) with the missing key names, separators, bare-JWT and URL-credential shapes, so log masking gains the same coverage.

## Requirements
- `REQ-001`: `secrets_masker.py` exposes one shared detection function over `SECRET_PATTERNS`; `diagnostic_store.py` no longer defines `_SENSITIVE_PATTERNS` or imports `re` for it and calls the shared function (single implementation, Issue Acceptance Criterion 1).
- `REQ-002`: Every shape the current guard blocks keeps being blocked: the six parametrized cases in `TestSensitiveDataRefusal`, the `sk-...` api_key JSON case in `test_save_rejects_sensitive_data_without_encryption`, and `access_token` / `auth_token` / `client_secret` / `bearer` keys in both `key=value` and quoted-JSON forms.
- `REQ-003`: New coverage is detected and blocked when no encryption key is set: a secret under an unlisted key name (at least `authorization`, `credential`, `private_key`, per the Issue's examples, plus `passwd` / `pwd`), a separator the guard misses (at least `=>`), a bare JWT-shaped value with no key, and a `scheme://user:pass@host` credential. Extra key names or separators beyond these are `Needs confirmation` (UNK-02).
- `REQ-004`: The guard's contract is otherwise unchanged: same `RuntimeError` and message, raised only when `encryption_key` is empty and `_filter_failed` is false; the encrypted path and `_filter_sensitive_fields()` are untouched; non-secret diagnostic payloads (for example `{"message": "hello world"}`, `[INCOMPLETE: timeout]`), already-masked values (`token=***MASKED***`) and the short-value decision of UNK-01 do not cause false refusals.
- `REQ-005`: Log masking keeps working with the extended `SECRET_PATTERNS`: `_mask_secrets` keeps its signature and call sites, masks the new JWT and URL-credential shapes in log text, stays idempotent, and the pattern-count assertion is updated to the final count.
- `REQ-006`: The two documents that go stale are updated: the data-layer doc that names `_SENSITIVE_PATTERNS` (the Issue's "no documentation describes the guard" claim is wrong) and the operations doc that lists the masker's masked shapes.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/secrets_masker.py | Add the shared detection function; extend `SECRET_PATTERNS` with the missing key names, separators, bare-JWT and URL-credential shapes | The module has no detection API, no `bearer` / `auth_token` / `client_secret` JSON-key coverage and no JWT or URL-credential pattern | REQ-001, REQ-002, REQ-003, REQ-005 / AC-1, AC-2, AC-3, AC-5 | `SECRET_PATTERNS` and `_mask_secrets` are the only public symbols; probe run showed `{"client_secret": "..."}`, a bare JWT and `postgres://user:pw@host` unchanged by `_mask_secrets` (checked in Step 2) | tests/agent/test_secrets_masker.py, tests/agent/test_diagnostic_store_security.py | Verified |
| scripts/agent/diagnostic_store.py | Replace `_SENSITIVE_PATTERNS` and its loop in `DiagnosticStore.save()` with the shared detection call | The private regex list is the divergent second implementation; `save()` is its only user | REQ-001, REQ-004 / AC-1, AC-4 | `_SENSITIVE_PATTERNS` defined at module level and used only inside `DiagnosticStore.save()` (rg over `scripts/` and `tests/`, checked in Step 2) | tests/agent/test_diagnostic_store_security.py, tests/agent/test_diagnostic_store.py | Verified |
| tests/agent/test_secrets_masker.py | Add tests for the new masked shapes and idempotence; update the pattern-count assertion | `test_pattern_count_grew_by_exactly_one` asserts `len(SECRET_PATTERNS) == 6`; adding patterns fails it (secmask001 changes it first) | REQ-005 / AC-5 | Class `TestMaskSecrets` and the count test exist (checked in Step 2) | tests/agent/test_secrets_masker.py itself | Verified |
| tests/agent/test_diagnostic_store_security.py | Add guard tests: new key names, separator, bare JWT, URL credential, short value (UNK-01), no-false-positive and already-masked cases; extend the existing refusal parametrization | `TestSensitiveDataRefusal` pins only the six shapes the old regex covers; Issue Required Changes asks for new-coverage tests | REQ-002, REQ-003, REQ-004 / AC-2, AC-3, AC-4 | `TestSensitiveDataRefusal.test_refuse_when_sensitive_data_present_without_key` is parametrized over six JSON payloads (checked in Step 2) | tests/agent/test_diagnostic_store_security.py itself | Verified |
| docs/23_agent/agent_09_01_data-layer-session-db.md | Reword the "Accepted storage posture" fail-closed bullet so it describes the shared-detector guard instead of naming `_SENSITIVE_PATTERNS`; state the widened coverage and that detection stays best-effort | The bullet names the removed `_SENSITIVE_PATTERNS` symbol and would be stale | REQ-006 / AC-6 | The bullet "Fail-closed detection: ... `_SENSITIVE_PATTERNS` matching raises `RuntimeError`" exists (checked in Step 2) | N/A: documentation (docs checkers in the Validation plan) | Verified |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Update the "Secret Masking in MCP Subprocess Failure Reports" section for the shapes this Plan adds (bare JWT, URL credentials, added key names) on top of secmask001's update | The section lists the masker's masked shapes and is stale after the extension | REQ-006 / AC-6 | The section states the masker "masks three shapes" (checked in Step 2); secmask001 also targets this file, so edit after it (see Scope Dependencies) | N/A: documentation (docs checkers in the Validation plan) | Verified |

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
| plans/20261101-140116_secmask001_secrets-masker-leaks-unmasked-value.md | Prerequisite Plan: final colon-form patterns, apply-order and idempotence constraints (`token: Bearer abc`), pattern-count update; read-only | REQ-003, REQ-005 |
| tests/agent/test_diagnostic_store.py | Holds the existing refusal and non-sensitive-save tests (`test_save_rejects_sensitive_data_without_encryption`, `test_save_saves_non_sensitive_data_normally`) that must keep passing; its fake DB fixtures are reused | REQ-002, REQ-004 |
| tests/agent/test_regression_diagnostic_persist.py | Regression tests around diagnostic persistence that must keep passing | REQ-004 |
| scripts/agent/session.py | Caller `AgentSession.save_diagnostic` of `DiagnosticStore.save()` with no `RuntimeError` handling | REQ-004 (Risks, UNK-03) |
| scripts/agent/llm_transport_errors.py | Callers `handle_partial_completion` / `handle_non_partial_error`, which pass raw partial LLM text to `save()` with no handling | REQ-004 (Risks, UNK-03) |
| scripts/agent/error_injection_service.py | Caller that saves `mid_turn_error` with no handling | REQ-004 (Risks, UNK-03) |
| scripts/agent/session_persister.py | Caller that already catches `RuntimeError` around `save(kind="session_summary")` | REQ-004 |
| docs/00_index.md | "Document References by Task" routing for the docs rows and the docs checkers | REQ-006 |

## Acceptance Criteria
- AC-1 (REQ-001): `scripts/agent/diagnostic_store.py` contains no `_SENSITIVE_PATTERNS` and the guard calls the shared function from `secrets_masker.py`; a test asserts `DiagnosticStore.save()` refuses content for which the shared function is true.
- AC-2 (REQ-002): all pre-existing guard tests pass unchanged, and `access_token` / `auth_token` / `client_secret` / `bearer` keys in `key=value` and quoted-JSON forms are refused.
- AC-3 (REQ-003): a bare JWT, `scheme://user:pass@host`, `authorization` / `credential` / `private_key` / `passwd` secrets, and `api_key => value` are each refused by `save()` with no encryption key; the same strings are masked by `_mask_secrets` with no part of the secret left.
- AC-4 (REQ-004): with an encryption key set, the same content is saved encrypted without raising; with `_filter_failed` set the guard is skipped as today; `{"message": "hello world"}`, `[INCOMPLETE: timeout]`, `token=***MASKED***`, `{"token": ""}` (per UNK-01) and a JSON payload with no secret are saved without raising; the `RuntimeError` message is byte-identical.
- AC-5 (REQ-005): `_mask_secrets` signature and all four call-site modules are unchanged (`git diff`); applying it twice equals once for the new shapes; the pattern-count assertion equals the final `len(SECRET_PATTERNS)` and the non-secret log sample is returned unchanged.
- AC-6 (REQ-006): neither doc names `_SENSITIVE_PATTERNS`, both state the final behavior accurately, and the docs checkers pass.

## Tests
- Guard tests in `tests/agent/test_diagnostic_store_security.py` (REQ-002, REQ-003): parametrized refusal over old and new shapes, including the `sensitive_fields` redaction running first (a payload whose `artifacts` field is redacted and whose other text carries a secret is still refused).
- Guard tests (REQ-004): no-false-positive payloads, already-masked value, encrypted path and `_filter_failed` carve-out unchanged, error message unchanged.
- Masker tests in `tests/agent/test_secrets_masker.py` (REQ-005): new masked shapes, idempotence, updated count.
- Regression (REQ-002, REQ-004): `tests/agent/test_diagnostic_store.py`, `tests/agent/test_regression_diagnostic_persist.py`, `tests/agent/test_session_persister.py`, `tests/agent/test_http_lifecycle_command_validator.py` run unchanged.

## Documentation Impact
Required (REQ-006). The Issue's "N/A" is incorrect: the data-layer doc names `_SENSITIVE_PATTERNS` in its accepted-storage-posture section, and the operations doc lists the masker's shapes. Target docs are listed in `Implementation Target Files` (reached via `docs/00_index.md` "Document References by Task", Agent row). Describe intent and boundaries only, not the pattern list (`skills/DESIGN.md` Docs content policy). Run the docs checkers from `routing.md` Tools after the edits.

## Assumptions
- Detection is defined as `_mask_secrets(text) != text` or an equivalent over the same `SECRET_PATTERNS`; falsifiable by the AC-4 already-masked test (a substitution of a value by the same `***MASKED***` marker yields equal text).
- Consolidating onto the masker removes the guard's 16-character minimum: `password=hunter2` becomes refused. This follows from the Issue's "consolidate on one implementation" and is the stricter, fail-closed direction; whether empty or very short values should be exempt is UNK-01, default no exemption except empty and already-masked values.
- Path B (Step 3): 6 target files and a new public function in `secrets_masker.py` (a runtime-facing interface), so the broader analysis applies. No schema, configuration, dependency or MCP change, so `pip-audit` and `ss` are N/A.
- The key list is the guard's current names plus the Issue's examples; the masker's existing names stay. No other names are invented (UNK-02).
- Step 8b: `tools/check_plan_target_overlaps.py` reports three overlaps naming this Plan, all with `plans/20261101-140116_secmask001_secrets-masker-leaks-unmasked-value.md`: `scripts/agent/secrets_masker.py`, `tests/agent/test_secrets_masker.py` and `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`. Judgment: sequencing dependency, designs compatible. secmask001 only adds colon-form patterns for the existing key names and states that no new key names and no change to `diagnostic_store.py` are in its scope; this Plan appends further patterns, a detection function and new key names on top, after secmask001 has set the count assertion and the doc section. Ordering is recorded in Scope Dependencies and UNK-04. The other overlaps in the tool output concern only the four workflow-engine Plans and do not involve this Plan.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Behavior for short values: the old guard ignored values under 16 characters, the masker has no minimum, so consolidation refuses `password=hunter2` and could refuse empty-value JSON such as `{"token": ""}` (masker rewrites the empty value) | No owner decision; no data on how often diagnostic payloads carry empty or short secret-keyed values | Default: no minimum length (fail-closed), exempt empty and already-masked values via tests AC-4; owner may confirm at `plan-to-implementation-procedure` time | False |
| UNK-02 | Full set of additional key names and separators; the Issue says "for example" `authorization`, `passwd`, `credential`, `private_key` and "other separators" without a list | No enumerated list in the Issue | Default: implement the REQ-003 minimum (Issue examples, `passwd`/`pwd`, `=>`, secmask001's colon forms); anything more is a separate owner request | False |
| UNK-03 | The `save()` callers `AgentSession.save_diagnostic`, `handle_partial_completion` / `handle_non_partial_error` (raw partial LLM text) and the `mid_turn_error` saver in `error_injection_service` do not catch the refusal; a wider guard (more false-positive surface than the old 16-character rule) makes an uncaught `RuntimeError` more likely there | No evidence of how those callers behave end to end when `save()` raises; the Issue forbids changing the raise contract | Owner decides whether to file a follow-up issue to contain them (as commit `9a6f41e13` did for two other callers); not changed here | False |
| UNK-04 | Whether this Plan may be implemented before secmask001's Plan (the Issue says implement it first); both edit `SECRET_PATTERNS`, its count test and one doc section | Both Plans are Frozen but all their steps are `Pending` | Implement secmask001 first as recorded in Scope Dependencies; if the order is reversed, re-run `check_plan_target_overlaps.py` and rebase the count assertion | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/secrets_masker.py | Modify | Medium (four log-masking call sites plus the diagnostic guard; behavior of masked text changes) | 3 commits (30d) | N/A | Deployed runtime file under `scripts/agent/`: takes effect only after a deploy (hand-off to `skills/deploy/SKILL.md`) |
| scripts/agent/diagnostic_store.py | Modify | High (every `save()` caller; refusal surface widens) | 2 commits (30d) | N/A | Deployed runtime file under `scripts/agent/`: takes effect only after a deploy |
| tests/agent/test_secrets_masker.py | Modify | Low | 3 commits (30d) | N/A | None: tests are not deployed |
| tests/agent/test_diagnostic_store_security.py | Modify | Low | 0 commits (30d) | N/A | None: tests are not deployed |
| docs/23_agent/agent_09_01_data-layer-session-db.md | Modify | Low | 17 commits (30d) | N/A | None: docs are not deployed |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Modify | Low | N/A | N/A | None: docs are not deployed |

## Design
- Path B (Step 3): more than 3 files plus a new public function. Architecture : `diagnostic_store.py` already lives in `agent` and importing `agent.secrets_masker` (a stdlib-only leaf module with no imports besides `re`) adds no layering edge; `lint-imports` reports 6 contracts kept. Dependency graph: `secrets_masker` has four importers (`startup_mcp_starter`, `http_lifecycle_errors`, `http_lifecycle_health_checker`, `shared/retry_helper`); `DiagnosticStore` is imported by `session`, `session_persister`, `orchestrator`, `llm_transport_errors`, `repl` and tests. Baseline: `radon cc` shows `DiagnosticStore.save` rank B (8) and `_mask_secrets` rank A (2); `vulture` and `bandit` report nothing on the two sources; the diff-cover baseline needs a full-suite run and is deferred to the implementation phase, which must reach the threshold in `rules/toolchain.md`. Operational inspection: N/A (no DB schema, MCP or dependency change).
- Decision 1, ownership: the shared detector lives in `secrets_masker.py` (alternatives: a new common module both import, or detection in `diagnostic_store.py`). A new module adds a file and a second place for patterns without benefit, since `secrets_masker.py` is already the pattern owner and only 804 bytes; the Issue allows either. Compatibility: `_mask_secrets` and `SECRET_PATTERNS` names stay.
- Decision 2, detection predicate: `masked != text` over the same patterns (alternative: per-pattern `search`). `search` would flag already-masked `password=***MASKED***` because `(\S+)` matches the marker, and would need a separate no-op check; the difference form treats a same-marker substitution as no change, which is why previously masked diagnostic text is not refused.
- Decision 3, patterns extend the one list: the guard's current key names missing from the masker (`bearer`, and `auth_token` / `access_token` / `client_secret` in quoted-JSON-key form, where the existing JSON pattern requires the key to be exactly one of its short names) are added to `SECRET_PATTERNS`, plus a keyed `=>` separator, `authorization` / `credential` / `private_key` keys, a bare JWT shape (three base64url segments starting `eyJ`) and a URL userinfo shape (`scheme://user:` then password up to `@`). The existing substitution `m.group(1) + "***MASKED***"` is kept; the bare-JWT pattern uses an empty group 1. The diagnostic content is typically a JSON object, so patterns must also work on JSON-escaped text.
- Apply order: patterns run sequentially on one string and an earlier mask can hide a later match (secmask001 records the `token: Bearer abc` case); new patterns are placed after secmask001's and tested with ordering cases, and the bare-JWT and URL patterns are anchored on their own delimiters so they do not depend on the key patterns.
- The pattern-count test is updated to the new count by this Plan after secmask001 has set its own.
- Error handling: unchanged. The guard still raises `RuntimeError` with the same message from `DiagnosticStore.save()`.

## Implementation steps
1. **Phase 1: Tests first (revertable alone)**
   - [ ] Add failing refusal and no-false-positive tests for the new shapes, the old shapes, the already-masked and empty-value cases, the encrypted path, the `_filter_failed` carve-out and the `sensitive_fields`-first path (REQ-002, REQ-003, REQ-004; tests/agent/test_diagnostic_store_security.py)
   - [ ] Add failing masker tests for the new masked shapes, idempotence and ordering (REQ-005; tests/agent/test_secrets_masker.py)
2. **Phase 2: Shared detection and patterns**
   - [ ] Extend `SECRET_PATTERNS` and add the shared detection function, leaving `_mask_secrets`' signature and substitution unchanged (REQ-001, REQ-003, REQ-005; scripts/agent/secrets_masker.py)
   - [ ] Update the pattern-count assertion to the final count (REQ-005; tests/agent/test_secrets_masker.py)
3. **Phase 3: Consolidate the guard**
   - [ ] Remove `_SENSITIVE_PATTERNS` and the unused `re` import, and call the shared function in `DiagnosticStore.save()` with the same `RuntimeError` (REQ-001, REQ-004; scripts/agent/diagnostic_store.py)
4. **Phase 4: Documentation**
   - [ ] Reword the fail-closed bullet in the accepted-storage-posture section (REQ-006; docs/23_agent/agent_09_01_data-layer-session-db.md)
   - [ ] Update the masker-shapes section after secmask001's edit (REQ-006; docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md)
5. **Phase 5: Deployment & Verification**
   - [ ] Run the Validation plan sequence; confirm the regression tests pass; hand off to `skills/deploy/SKILL.md` for the `scripts/` changes (prerequisite: the change is committed and pushed first; deploying is the user's decision) (REQ-001, REQ-004; scripts/agent/diagnostic_store.py, scripts/agent/secrets_masker.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/secrets_masker.py, tests/agent/test_secrets_masker.py | Unit | `uv run pytest tests/agent/test_secrets_masker.py` | New and regression tests pass |
| scripts/agent/diagnostic_store.py, tests/agent/test_diagnostic_store_security.py | Unit | `uv run pytest tests/agent/test_diagnostic_store_security.py tests/agent/test_diagnostic_store.py tests/agent/test_regression_diagnostic_persist.py` | New and existing guard tests pass |
| Callers | Integration (regression) | `uv run pytest tests/agent/test_session_persister.py tests/agent/test_http_lifecycle_command_validator.py tests/agent/test_startup_mcp_starter.py` | Pass unchanged |
| Both sources | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml` per `rules/toolchain.md` | Clean |
| Both sources | Size gate | `uv run python tools/check_module_size.py` | Pass |
| Both sources | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` per `rules/toolchain.md` | At or above threshold |
| Both docs | Docs checks | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent` | Pass |

## Risks
- **Risk**: Wider detection raises false refusals of legitimate diagnostics (prose such as `Invalid token: expired` once secmask001's colon patterns exist; empty-value JSON), and `save()` callers that do not catch `RuntimeError` (`session.py`, `llm_transport_errors.py`, `error_injection_service.py`) would surface it as a turn failure (likelihood Medium) → **Mitigation**: no-false-positive and empty-value tests (AC-4); UNK-01 default; the exposure itself is recorded as UNK-03 for an owner decision because the Issue forbids changing the raise contract.
- **Risk**: A pattern placed before or after another leaves part of a secret unmasked or breaks idempotence (the `token: Bearer abc` case recorded by secmask001) → **Mitigation**: ordering and double-application tests (AC-3, AC-5); implement after secmask001.
- **Risk**: A bare-JWT or URL-userinfo pattern also masks harmless text in logs (for example `scheme://user:x@host` examples in error messages) → **Mitigation**: patterns anchored on `eyJ` three-segment shape and `://user:...@`; negative tests with ordinary URLs without userinfo.
- **Risk**: Catastrophic backtracking from the new patterns on large diagnostic payloads (partial LLM text can be long) (likelihood Low) → **Mitigation**: bounded, non-nested quantifiers and a large-input test.
- **Risk**: The pattern-count test and secmask001's own edits collide (both change `SECRET_PATTERNS`, its count test and the operations doc section) → **Mitigation**: ordering recorded in Scope Dependencies and UNK-04; re-run the overlap check if the order changes.
- **Risk**: The Fernet-encrypted path or `_filter_failed` carve-out regresses while the guard block is rewritten → **Mitigation**: AC-4 tests for both.
- **Risk**: The `scripts/` change takes effect only after deploy → **Mitigation**: Phase 5 hand-off to `skills/deploy/SKILL.md` after commit and push.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first: guard and masker tests for the new shapes (tests/agent/test_diagnostic_store_security.py, tests/agent/test_secrets_masker.py) | In Progress | — | — |  |
| 2 | Shared detection function and extended patterns; update pattern-count assertion (scripts/agent/secrets_masker.py, tests/agent/test_secrets_masker.py) | In Progress | — | — |  |
| 3 | Consolidate the guard onto the shared detector (scripts/agent/diagnostic_store.py) | In Progress | — | — |  |
| 4 | Documentation: data-layer fail-closed bullet and masker shapes (docs/23_agent/agent_09_01_data-layer-session-db.md, docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md) | In Progress | — | — |  |
| 5 | Deployment and verification: validation sequence, regression tests, deploy hand-off (scripts/agent/diagnostic_store.py, scripts/agent/secrets_masker.py) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-132614_04_tests_agent_test_diagnostic_store_security.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-132614_03_tests_agent_test_secrets_masker.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261102-132614_01_scripts_agent_secrets_masker.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-132614_02_scripts_agent_diagnostic_store.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-132614_05_docs_23_agent_agent_09_01_data-layer-session-db.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261102-132614_06_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-140448
- **Related target files**: scripts/agent/secrets_masker.py, scripts/agent/diagnostic_store.py, tests/agent/test_secrets_masker.py, tests/agent/test_diagnostic_store_security.py, docs/23_agent/agent_09_01_data-layer-session-db.md, docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (replace standalone pattern); Acceptance Criteria 1 | scripts/agent/secrets_masker.py | 2 | AC-1 | Tests: guard refuses what the shared function flags | Explicit in issue |
| REQ-001 | Issue Required Changes; `_SENSITIVE_PATTERNS` used only in `save()` | scripts/agent/diagnostic_store.py | 3 | AC-1 | Tests: guard refuses what the shared function flags | Confirmed by repository evidence |
| REQ-002 | Existing refusal tests; probe run shows masker misses `client_secret` / `bearer` / `auth_token` JSON keys | tests/agent/test_diagnostic_store_security.py | 1 | AC-2 | Tests: parametrized old and new shapes | Derived from confirmed evidence |
| REQ-002 | Probe run (masker changes nothing for those JSON keys) | scripts/agent/secrets_masker.py | 2 | AC-2 | Tests: parametrized old and new shapes | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (extend pattern set); Problem gaps; probe run | scripts/agent/secrets_masker.py | 2 | AC-3 | Tests: new shapes refused and masked | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (tests for bare JWT, URL credential, unlisted key) | tests/agent/test_diagnostic_store_security.py | 1 | AC-3 | Tests: new shapes refused | Explicit in issue |
| REQ-003 | Issue "for example" key names and "other separators" without a list | scripts/agent/secrets_masker.py | 2 | AC-3 | Tests: REQ-003 minimum set | Needs confirmation |
| REQ-004 | Issue Constraints (encrypted path, RuntimeError unchanged) | scripts/agent/diagnostic_store.py | 3 | AC-4 | Tests: encrypted path, carve-out, message | Explicit in issue |
| REQ-004 | Probe run: old guard ignores values under 16 characters; masker has no minimum | tests/agent/test_diagnostic_store_security.py | 1 | AC-4 | Tests: no-false-positive, already-masked, empty value | Derived from confirmed evidence |
| REQ-005 | Existing count test pins 6; masker call sites; idempotence | tests/agent/test_secrets_masker.py | 1, 2 | AC-5 | Tests: new shapes, idempotence, count | Confirmed by repository evidence |
| REQ-005 | Issue Implementation Intent (shared pattern set also for log masking) | scripts/agent/secrets_masker.py | 2 | AC-5 | `git diff` check, regression tests | Derived from confirmed evidence |
| REQ-006 | Data-layer doc names `_SENSITIVE_PATTERNS` (Issue Documentation Impact says N/A) | docs/23_agent/agent_09_01_data-layer-session-db.md | 4 | AC-6 | Validation plan: docs checkers | Confirmed by repository evidence |
| REQ-006 | Operations doc lists masker shapes ("three shapes") | docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | 4 | AC-6 | Validation plan: docs checkers | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-132614 -->