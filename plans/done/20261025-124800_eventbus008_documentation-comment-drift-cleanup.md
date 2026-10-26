## Goal
A focused editorial cleanup of the EventBus area: remove resolved implementation history from source comments, tests and generated references, collapse the duplicated default-path constants in `config.py`, replace the inaccurate "no authentication" runtime message with the current loopback-defense rationale, classify the 41 `REQ-0xx` tag comments as active-invariant (kept) versus resolved-history (removed), correct spelling/grammar, and regenerate machine-owned reference tables through their generator instead of hand-editing them — all without any behavior change.

## Priority
Low

## Scope
- **In-Scope**:
  - Collapse the duplicated `_DEFAULT_CONFIG_PATH` / `_DEFAULT_SCHEMA_PATH` definitions in `scripts/eventbus/config.py` (identical assignments at lines 13-14 and 23-24) into a single definition; the name is read at `config.py:29,34,280` so removal of one copy is behavior-preserving.
  - Replace the inaccurate runtime message `The API has no authentication — this is a security risk.` (`config.py:69` in `_validate_deployment_mode`, and `config.py:124` in `EventBusConfig.__post_init__`) with the current loopback-defense rationale (a non-loopback bind without auth is the real exposure; the API now has Bearer-token + role-based auth per ADR-013).
  - Remove stale narrative comments that narrate removed implementation history: `scripts/eventbus/ack_route.py:16` (`write_offset removed — replaced by ...`); the resolved-history parenthetical in `ack_route.py:183` (`REQ-004: events.acked_at removed; ...`); and the legacy-counter narrative in `scripts/eventbus/delivery_repo.py:110-112` (`... the events-level failure counters are legacy and no longer written ...`).
  - Classify all 41 `REQ-0xx` tag comments (`grep -rn "REQ-0" scripts/eventbus/*.py`) into active traceability/invariant markers (kept) versus resolved-history narratives (removed or rewritten to state the current invariant). Produce the concrete kept/removed list at planning time.
  - Correct spelling, grammar, capitalization and terminology in the affected English text (source comments, tests, docs).
  - Regenerate machine-owned reference tables through `tools/generate_reference_table.py` (never hand-edit guarded `AUTO-GENERATED` blocks); `--check` must pass afterward.
  - Locate and fix any malformed endpoint paths via `tools/generate_reference_table.py --check` and the docs link/path checkers before finalizing scope.
- **Out-of-Scope**:
  - Any behavior change, contract change, or change to transaction/concurrency/authorization/durability/fail-closed boundaries.
  - Editing `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` or `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` for wording: adversarial verification found their "no authentication"/"no longer" references are correct-context ADR language (current-state accuracy at adr_013:36; alternative-analysis at adr_013:100/116-120; template phrases at adr_006:61/287-288), not EventBus comment drift. Editing governance records would corrupt the ADR record.
  - The `to_thread()` warning from `check_docs_consistency.py --domain eventbus` is a false positive (stdlib `asyncio.to_thread`); not a real drift.
  - The memo's `published_at` comment claim (not found in current source).
  - Lazy loading of the Step 0 mandatory-load set — no action required (fixed load absorbed by prompt cache, user decision 2026-10-24).
- **Dependencies**:
  - Depends on H-01 to M-02 (replacement contracts must exist first). No open issue under `issues/` overlaps.

## Background
Confirmed against HEAD (adversarial re-verification):
- `scripts/eventbus/config.py` defines `_DEFAULT_CONFIG_PATH` and `_DEFAULT_SCHEMA_PATH` twice — identical assignments at lines 13-14 and again at lines 23-24. The names are read at `config.py:29` (`get_config_path`), `config.py:34` (`get_schema_path`) and `config.py:280`; collapsing to one definition is behavior-preserving.
- `config.py:69` (`_validate_deployment_mode`) and `config.py:124` (`EventBusConfig.__post_init__`) both emit `The API has no authentication — this is a security risk.` The implemented model is Bearer-token + role-based access (ADR-013 line 36); the real exposure is a non-loopback bind without auth, which the message misstates as "no authentication".
- Stale narrative comments remain: `ack_route.py:16` (`# write_offset removed — replaced by ack_event_for_consumer() transactional path`), `ack_route.py:183` (`# Then check events-level DLQ state only (REQ-004: events.acked_at removed; dlq_at is the authoritative DLQ indicator)`), and `delivery_repo.py:110-112` (`# ... the events-level failure counters are legacy and no longer written to under the per-consumer model.`).
- `grep -rn "REQ-0" scripts/eventbus/*.py` returns exactly 41 matches across `app.py`, `ack_route.py`, `dlq.py`, `delivery_repo.py`, `subscribe_route.py`. Most are active traceability/invariant markers (e.g. `ack_route.py:43` "REQ-004: consumer_id is mandatory", `delivery_repo.py:179` "REQ-005: Verify event existence BEFORE writing", `subscribe_route.py` heartbeat/validation invariants); a minority narrate resolved history.
- `tools/generate_reference_table.py` exists and writes the EventBus class/function reference table into the guarded block of `docs/24_eventbus/eventbus_08_reference_api.md`. `--check` currently reports "No drift found"; the generated table renders signatures and summaries correctly with no malformed endpoint paths.
- `check_docs_quality.py` (172 files), `check_docs_structure.py`, `check_docs_content_policy.py` and `check_adr_reference.py` all report no issues for the EventBus domain. `check_docs_consistency.py --domain eventbus` reports one false-positive warning about `to_thread()` (stdlib), not real drift.
- No test asserts the exact runtime message `The API has no authentication — this is a security risk.`, and no test references the stale comments; removing/rewriting them cannot break a test.
- The memo's `spelling and grammar across test text` and `malformed endpoint paths` claims were not enumerated. Direct byte reads (`read`/`sed`/`grep|cat -A`) show the EventBus test comments are correct ("before events are delivered", "redelivered, permanently"); the apparent corruption seen in some tool output was an artifact, not real text. The malformed-path location is deferred to the generator/link checker per the issue's own Unresolved Questions.

## Problem
Source comments, and a runtime validation message, keep resolved implementation history and inaccurate wording; two default-path constants are defined twice; 41 `REQ-0xx` tag comments mix active traceability markers with resolved-history narratives; and machine-owned reference tables must be regenerated rather than hand-edited — which obscures the current contract and risks a future change restoring removed behavior.

## Reason for Change
Active documentation should describe current invariants and failure behavior, and stale comments can lead a future change to restore removed behavior; duplicate definitions and inaccurate security wording obscure the real contract.

## Implementation Intent
Remove pre-fix, completed-issue, removed-test, legacy-offset and resolved-path narratives; collapse the duplicated default-path constants; replace the inaccurate "no authentication" message with the loopback-defense rationale; classify and prune the resolved-history portion of the 41 `REQ-0xx` comments while keeping active invariant markers; correct spelling/grammar; and regenerate the EventBus reference table through its generator — with no behavior change.

## Requirements
- `REQ-001`: No active comment MAY present removed behavior as current. (Acceptance 1)
- `REQ-002`: The runtime security message MUST match the implemented Bearer-token + role-based model and state the loopback-defense rationale. (Acceptance 2)
- `REQ-003`: The duplicated `_DEFAULT_CONFIG_PATH` / `_DEFAULT_SCHEMA_PATH` definitions MUST be collapsed to one, behavior unchanged. (Acceptance 4)
- `REQ-004`: Endpoint paths render correctly and generated reference blocks are regenerated (not hand-edited). (Acceptance 3)
- `REQ-005`: Spelling, grammar, capitalization and terminology in the affected English text are corrected. (Acceptance 4)
- `REQ-006`: No behavior, contract, or transaction/concurrency/authorization/durability/fail-closed boundary changes. (Constraint)

## Implementation Target Files
**Freeze status**: Frozen (set once `issue-to-plan` Step 8's Implementation Target
Files Validation passed — `check_workitem_structure.py` reports No findings;
`check_plan_target_overlaps.py` reports 12 cross-plan overlaps, ALL between already
Frozen Plans (`plans/...001...`, `...002...`, `...004...`, `...005...`, `...006...`,
`...007...`) on `docs/10_adr/adr_02_04_006...`, `adr_02_04_013...`,
`scripts/eventbus/ack_route.py`, `scripts/eventbus/app.py`, `scripts/eventbus/auth.py`,
`scripts/eventbus/dlq_route.py`, `scripts/eventbus/route_helpers.py` and four test
files. None of the 12 findings involves this Issue 8 Plan (still Draft at check time).
This Plan's edits to `ack_route.py`, `app.py` and `dlq.py` are COMMENT-ONLY (resolved
narrative removal + `REQ-0xx` classification), which is non-contradictory with those
files' BEHAVIORAL edits in the other plans; the issue explicitly orders this cleanup to
FOLLOW the behavioral issues (`eventbus001`–`eventbus007`). After freeze, re-running the
overlap checker adds `ack_route.py`/`app.py` to the shared set (now including this Plan)
— additive, comment-only, no contradiction. Every row is `Verified`.

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/config.py` | Collapse the duplicated `_DEFAULT_CONFIG_PATH` / `_DEFAULT_SCHEMA_PATH` (keep one of lines 13-14 or 23-24); rewrite the runtime message at lines 69 and 124 to the loopback-defense rationale | Duplicate-definition cleanup + inaccurate-security-wording fix | REQ-002, REQ-003; Acceptance 2, 4 | dup defs config.py:13-14 & 23-24; message config.py:69, 124 | none assert the message (verified) | Verified |
| `scripts/eventbus/ack_route.py` | Remove the resolved-history narrative at line 16; rewrite the resolved-history parenthetical at line 183 to the current invariant; classify remaining `REQ-0xx` tags here (lines 34,43,49,114,127,135,139,161,163,174-175,183,191) | Remove implementation history; keep active invariant markers | REQ-001; Acceptance 1 | ack_route.py:16, 183; REQ-0 tags 34-191 | none reference these comments (verified) | Verified |
| `scripts/eventbus/delivery_repo.py` | Rewrite the legacy-counter narrative at lines 110-112 to the current per-consumer invariant; classify remaining `REQ-0xx` tags here (lines 41,179,188) | Remove implementation history; keep active invariant markers | REQ-001; Acceptance 1 | delivery_repo.py:110-112; REQ-0 tags 41,179,188 | none reference these comments (verified) | Verified |
| `scripts/eventbus/app.py` | Classify `REQ-0xx` tags (lines 25,26,249,267) — keep active markers, remove any resolved history | REQ-0 classification sweep | REQ-001; Acceptance 1 | app.py:25,26,249,267 | N/A | Verified |
| `scripts/eventbus/dlq.py` | Classify `REQ-0xx` tags (lines 32,84,132,189) — keep active markers, remove any resolved history | REQ-0 classification sweep | REQ-001; Acceptance 1 | dlq.py:32,84,132,189 | N/A | Verified |
| `scripts/eventbus/subscribe_route.py` | Classify `REQ-0xx` tags (lines 64,78,82,98,107,122,136,190,205,209,231,236,241,258,260,262) — keep active markers, remove any resolved history | REQ-0 classification sweep | REQ-001; Acceptance 1 | subscribe_route.py tags | N/A | Verified |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Regenerate the guarded EventBus class/function reference block via `generate_reference_table.py --type eventbus`; never hand-edit the guarded block | Regenerate machine-owned reference | REQ-004; Acceptance 3 | guarded AUTO-GENERATED block | N/A | Verified |
| `tests/eventbus/*` (EventBus suite) | Correct spelling/grammar in affected English text only; leave behavior and assertions unchanged | Spelling/grammar pass | REQ-005; Acceptance 4 | manual/quality-checker pass | this suite | Verified |
| `tools/generate_reference_table.py` | Read-only use of the generator; no change unless a genuine generator defect is found that blocks regeneration | Tool used, not modified | REQ-004; Acceptance 3 | `--check` = No drift | N/A | Verified |

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
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Confirm the current-state description (line 36) is accurate and the "no authentication" references are alternative-analysis language, so the ADR is correctly excluded from editing | `scripts/eventbus/config.py`; REQ-002 |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Confirm its "no longer" matches are template phrases, not EventBus comment drift, so the ADR is correctly excluded | `scripts/eventbus/delivery_repo.py`; REQ-001 |
| `scripts/eventbus/auth.py` | The Bearer-token + role-based model (ADR-013) the rewritten message must describe accurately | `scripts/eventbus/config.py`; REQ-002 |
| `scripts/eventbus/db.py` | Facade re-exports; confirm nothing imports the collapsed constants indirectly | `scripts/eventbus/config.py`; REQ-003 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | EVENTBUS tracking (Part 1); confirms scope and that deploy/readiness gaps are separate | `docs/24_eventbus/eventbus_08_reference_api.md`; Scope |

## Acceptance Criteria
- No active comment presents removed behavior as current (REQ-001; Acceptance 1).
- The runtime security message matches the implemented authentication/authorization model and states the loopback-defense rationale (REQ-002; Acceptance 2).
- The duplicated default-path constants are collapsed to one with behavior unchanged (REQ-003; Acceptance 4).
- Endpoint paths render correctly and generated reference blocks are regenerated, not hand-edited (REQ-004; Acceptance 3).
- Spelling, grammar, capitalization and terminology in the affected English text are corrected (REQ-005; Acceptance 4).

## Tests
- Config cleanup: `uv run pytest tests/eventbus/test_eventbus_config.py` — the config still loads, `get_config_path()`/`get_schema_path()` resolve, and the non-loopback-without-auth case still raises (message wording may change). (REQ-002, REQ-003)
- Full EventBus suite unchanged in behavior: `uv run pytest tests/eventbus/` — no assertion or behavior regresses from comment/message/ref changes. (REQ-006)
- Generated-reference drift: `uv run python tools/generate_reference_table.py --check` — exits 0 (No drift) after regeneration. (REQ-004)
- Docs quality/structure/content/consistency: `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain eventbus` — no new issues (the `to_thread()` warning is pre-existing and a false positive). (REQ-005)
- Then ruff format and mypy on the touched source files.

## Documentation Impact
Yes. This issue is the documentation/comment update. Generated reference blocks are regenerated through `tools/generate_reference_table.py`, not hand-edited. Target docs named via `docs/00_index.md` / `routing.md` Docs mapping:
- `docs/24_eventbus/eventbus_08_reference_api.md` — regenerate the guarded EventBus class/function reference block.
No deployment-script documentation is in scope. Governance ADRs are intentionally out of scope (adversarial verification found no real drift there).

## Assumptions
- Collapsing one of the two identical `_DEFAULT_CONFIG_PATH` / `_DEFAULT_SCHEMA_PATH` assignments leaves the module-level names resolving to the same values they already resolve to today.
- The 41 `REQ-0xx` comments split cleanly into active-invariant (keep) and resolved-history (remove/rewrite); the distinguishing test is whether the comment states a CURRENT invariant/failure behavior (keep) or narrates a PAST removed implementation (remove).
- Comment/message edits do not change any observable behavior, so the existing EventBus suite should pass unchanged.
- `deploy.sh` rsyncs `scripts/` and `docs/` wholesale to `/opt/llm/`, so every target row's `deploy.sh Impact` is "not applicable (rsynced)".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which of the 41 `REQ-0xx` tag comments are active traceability markers (kept) versus resolved history (removed)? | Not enumerated per-comment in this review | Engineering decision; produce the kept/removed list at planning time; recorded in design; drives `ack_route.py`, `delivery_repo.py`, `app.py`, `dlq.py`, `subscribe_route.py` | False |
| UNK-02 | Where exactly are the malformed endpoint paths, if any? The generator `--check` currently passes. | Not identified; deferred to the generator/link checker per the issue | Locate via `generate_reference_table.py --check` and the docs link/path checkers; record findings; likely none (recorded) | False |
| UNK-03 | Are there genuine spelling/grammar errors in the EventBus test text, or only the tool-output artifact observed earlier? | Direct byte reads showed correct text ("delivered", "redelivered") | Manual/quality-checker pass; record any real errors; likely none (recorded) | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/config.py` | Collapse dup constants + rewrite runtime message | Config validation only; all loaders | 3 (last change 2026-10-22) | N/A (git-fame unavailable) | not applicable (rsynced) |
| `scripts/eventbus/ack_route.py` | Remove/rewrite resolved-history comments; classify REQ-0 tags | Comment-only; ACK/NACK routes | 2 (last change 2026-10-23) | N/A | not applicable (rsynced) |
| `scripts/eventbus/delivery_repo.py` | Rewrite legacy-counter comment; classify REQ-0 tags | Comment-only; delivery layer | 2 (last change 2026-10-23) | N/A | not applicable (rsynced) |
| `scripts/eventbus/app.py` | Classify REQ-0 tags | Comment-only | 1 | N/A | not applicable (rsynced) |
| `scripts/eventbus/dlq.py` | Classify REQ-0 tags | Comment-only | 1 | N/A | not applicable (rsynced) |
| `scripts/eventbus/subscribe_route.py` | Classify REQ-0 tags | Comment-only | 1 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Regenerate guarded reference block | Doc-only | 0 | N/A | not applicable (rsynced) |
| `tests/eventbus/*` | Spelling/grammar corrections only | Test-only | 0 | N/A | not applicable (rsynced) |
| `tools/generate_reference_table.py` | Read-only use | Tool | 0 | N/A | not applicable (rsynced) |

Baseline complexity (radon): `config.py` functions all A(1); `ack_route.py::_do_ack` = C (12), `nack` = B (8); `delivery_repo.py::ack_event_for_consumer` = C (11). Comment/message edits do not change cyclomatic complexity. bandit and vulture are clean on the target files. `lint-imports`: 6 contracts KEPT, 0 broken.

## Design
**North star (REQ-006):** no behavior, contract, or safety-boundary change. Every edit
is editorial: comment text, a runtime validation message, a duplicate constant, and a
regenerated reference table.

**Duplicate constants.** Keep the definition at lines 13-14 and delete the duplicate at
lines 23-24 (or vice versa); both are byte-identical. The names are read at
`config.py:29,34,280`, so collapsing to one assignment is behavior-preserving. Verify no
test or import depends on the second definition (none does — verified).

**Runtime message (UNK-02 wording).** Replace `The API has no authentication — this is a
security risk.` with loopback-defense rationale consistent with ADR-013, e.g.
`Event Bus bound to non-loopback address {cfg.host} without authentication configured; set auth_token or bind to loopback.` Keep it a `ValueError` raised by the same two callers (`_validate_deployment_mode` and `EventBusConfig.__post_init__`). No test asserts the old string, so the wording change is safe.

**REQ-0 classification (UNK-01).** For each of the 41 tags, apply the test: does the
comment state a CURRENT invariant/failure/concurrency/durability rule (KEEP) or narrate a
PAST removed implementation such as "removed", "replaced by", "legacy", "no longer
written" (REMOVE/REWRITE to the current invariant)? Concrete confirmed cases:
- REMOVE/REWRITE: `ack_route.py:16` (full narrative), `ack_route.py:183` parenthetical
  ("events.acked_at removed"), `delivery_repo.py:110-112` ("legacy and no longer written").
- KEEP: `ack_route.py:43` "REQ-004: consumer_id is mandatory", `delivery_repo.py:179`
  "REQ-005: Verify event existence BEFORE writing", `subscribe_route.py` heartbeat/validation
  invariants, and similar current-state markers.
Produce the full kept/removed list at planning time and record it in the implementation
procedure.

**Generated references.** Run `python tools/generate_reference_table.py --type eventbus`
to refresh the guarded block in `docs/24_eventbus/eventbus_08_reference_api.md`; never
edit between the guard comments. Confirm `--check` exits 0 afterward. Comment edits do not
alter the derived class/function table, so the diff is expected to be empty, but the
regeneration step enforces the "regenerate, don't hand-edit" contract.

**Spelling/grammar.** Correct only genuine errors found by manual review plus
`check_docs_quality.py`. The apparent corruption seen in some tool output
("events are n", "redelivered" → "ren") was an artifact; direct byte reads confirm the
test text is correct, so expect no test edits unless a real error surfaces.

**Import-linter:** `eventbus-is-isolated` is KEPT (6 contracts, 0 broken). Comment/message
edits do not touch imports.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: config.py cleanup**
   - [ ] Collapse the duplicated `_DEFAULT_CONFIG_PATH` / `_DEFAULT_SCHEMA_PATH` to one definition in `scripts/eventbus/config.py`. (REQ-003; `scripts/eventbus/config.py`)
   - [ ] Rewrite the runtime message at `config.py:69` and `config.py:124` to the loopback-defense rationale. (REQ-002; `scripts/eventbus/config.py`)
2. **Phase 2: remove resolved-history comments**
   - [ ] Remove the narrative at `scripts/eventbus/ack_route.py:16`; rewrite the resolved-history parenthetical at `ack_route.py:183`. (REQ-001; `scripts/eventbus/ack_route.py`)
   - [ ] Rewrite the legacy-counter narrative at `scripts/eventbus/delivery_repo.py:110-112` to the current per-consumer invariant. (REQ-001; `scripts/eventbus/delivery_repo.py`)
3. **Phase 3: REQ-0 classification sweep**
   - [ ] Classify all 41 `REQ-0xx` tags across `ack_route.py`, `delivery_repo.py`, `app.py`, `dlq.py`, `subscribe_route.py`; keep active invariant markers, remove/rewrite resolved-history narratives. Produce the kept/removed list. (REQ-001; `scripts/eventbus/*.py`)
4. **Phase 4: Spelling/grammar pass**
   - [ ] Correct genuine spelling/grammar/capitalization/terminology errors in source comments, tests and docs via manual review + `check_docs_quality.py`. (REQ-005; `tests/eventbus/*`, `scripts/eventbus/*`, `docs/24_eventbus/*`)
5. **Phase 5: Regenerate references**
   - [ ] Run `python tools/generate_reference_table.py --type eventbus`; confirm `--check` exits 0. (REQ-004; `docs/24_eventbus/eventbus_08_reference_api.md`)
6. **Phase 6: Validation**
   - [ ] Run the EventBus suite, `generate_reference_table.py --check`, the docs quality/structure/content/consistency checkers, then ruff format and mypy. (Acceptance 1-5)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/config.py` | Unit: config loads; paths resolve; non-loopback-without-auth still raises | `uv run pytest tests/eventbus/test_eventbus_config.py` | Config intact; message wording updated; no assertion breaks |
| `scripts/eventbus/*` (comment edits) | Behavior unchanged after comment/message edits | `uv run pytest tests/eventbus/` | Full EventBus suite passes |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Generated-reference drift | `uv run python tools/generate_reference_table.py --check` | Exits 0 (No drift) |
| `docs/24_eventbus/*`, `tests/eventbus/*` | Docs quality/structure/content/consistency | `uv run python tools/check_docs_quality.py tools/check_docs_structure.py tools/check_docs_content_policy.py tools/check_docs_consistency.py --domain eventbus` | No new issues; `to_thread()` warning is pre-existing false positive |
| `scripts/eventbus/*` | Static: complexity, dead code, security, types, format | `uv run radon cc scripts/eventbus/config.py scripts/eventbus/ack_route.py scripts/eventbus/delivery_repo.py`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml`; `uv run mypy`; `uv run ruff` | Complexity unchanged; bandit/vulture/mypy/ruff clean |
| Import boundaries | Architecture contract | `PYTHONPATH=scripts uv run lint-imports` | 6 contracts KEPT, 0 broken |

## Risks
- **Risk**: Rewriting the runtime message changes an error string a monitor or test might match. → **Mitigation**: verified no test asserts the old string; keep it a `ValueError` from the same two callers.
- **Risk**: Over-pruning `REQ-0xx` tags removes useful traceability. → **Mitigation**: keep every comment that states a current invariant/failure/concurrency rule; only remove/rewrite pure resolved-history narratives. Record the kept/removed list.
- **Risk**: Editing a guarded generated block by hand violates ADR-015 INV-01. → **Mitigation**: regenerate via the generator; never hand-edit between guard comments; `--check` must pass.
- **Risk**: Comment edits accidentally change behavior. → **Mitigation**: comment-only edits cannot change behavior; the full EventBus suite is the backstop.
- **Risk**: The duplicate-constant removal breaks an indirect import. → **Mitigation**: verify nothing imports the second definition (verified); the name resolves identically.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: config.py duplicate-constant collapse + runtime-message rewrite | In Progress | — | — |  |
| 2 | Phase 2: remove resolved-history comments in `ack_route.py`, `delivery_repo.py` | In Progress | — | — |  |
| 3 | Phase 3: REQ-0 classification sweep across `scripts/eventbus/*.py` | In Progress | — | — | UNK-01: produce kept/removed list at planning time |
| 4 | Phase 4: spelling/grammar pass | In Progress | — | — | UNK-03: likely none (text verified correct) |
| 5 | Phase 5: regenerate EventBus reference table | In Progress | — | — | UNK-02: `--check` currently passes |
| 6 | Phase 6: validation suite | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | None — Path A (documentation/comment cleanup, no runtime interface change) | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261026-100803_01_scripts_eventbus_config.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261026-100803_02_scripts_eventbus_ack_route.py.md | 2, 3 | Procedure | Pending | — | — |
| implementations/20261026-100803_03_scripts_eventbus_delivery_repo.py.md | 2, 3 | Procedure | Pending | — | — |
| implementations/20261026-100803_04_scripts_eventbus_app.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261026-100803_05_scripts_eventbus_dlq.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261026-100803_06_scripts_eventbus_subscribe_route.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261026-100803_07_docs_24_eventbus_eventbus_08_reference_api.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261026-100803_08_tests_eventbus__.md | 4 | Procedure | Pending | — | — |
| implementations/20261026-100803_09_tools_generate_reference_table.py.md | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261023-154326_eventbus008_documentation-comment-drift-cleanup.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-124800
- **Related target files**: `scripts/eventbus/config.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/app.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/subscribe_route.py`, `docs/24_eventbus/eventbus_08_reference_api.md`, `tests/eventbus/*`, `tools/generate_reference_table.py` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required change 1; Acceptance 1 | `scripts/eventbus/ack_route.py`, `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/app.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/subscribe_route.py` | 2, 3 | No comment presents removed behavior as current | Comment review + suite pass | Draft |
| REQ-002 | Required change 2; Acceptance 2 | `scripts/eventbus/config.py` | 1 | Runtime message matches auth model + loopback rationale | config test | Draft |
| REQ-003 | Required change 3; Acceptance 4 | `scripts/eventbus/config.py` | 1 | Duplicate constants collapsed, behavior unchanged | config test | Draft |
| REQ-004 | Required change 4; Acceptance 3 | `docs/24_eventbus/eventbus_08_reference_api.md`, `tools/generate_reference_table.py` | 5 | Endpoint paths render; refs regenerated not hand-edited | `--check` = No drift | Draft |
| REQ-005 | Required change 5; Acceptance 4 | `tests/eventbus/*`, `scripts/eventbus/*`, `docs/24_eventbus/*` | 4 | Spelling/grammar corrected | `check_docs_quality.py` | Draft |
| REQ-006 | Constraint; Out-of-Scope | all | 6 | No behavior/contract/safety-boundary change | Full EventBus suite | Draft |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261026-100803 -->