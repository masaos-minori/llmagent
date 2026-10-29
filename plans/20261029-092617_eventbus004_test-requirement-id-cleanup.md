# Plan: Replace ambiguous requirement identifiers in EventBus test comments with canonical references

## Goal
- Remove plan-local identifiers (`REQ-nnn`, `UNK-nn`, `AC-n`, `SEQ-nn`) from comments and docstrings under `tests/eventbus/`, replacing each with a reference to a canonical definition (an ADR invariant or a `docs/24_eventbus/` section) or with plain wording, so that no identifier carries two meanings and no identifier lacks a reachable definition, with no change to code behavior.

## Priority
Low

## Scope
- **In-Scope**: comments and docstrings that carry `REQ-nnn`, `UNK-nn`, `AC-n`, or `SEQ-nn` identifiers in the 18 test files listed under `Implementation Target Files`; a read-only inventory with the meaning of each identifier in context; owner questions for identifiers without a canonical definition, listed in the change description.
- **Out-of-Scope**: renaming test functions or variables and the `x_*` prefix audit (`plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`); fixture and lifecycle changes (`plans/20261029-092424_eventbus003_test-lifecycle-production-path.md`); production comments under `scripts/eventbus/` (see UNK-01); `H-nn` / `UNK-nn` references in `docs/24_eventbus/` (see UNK-03); editing an ADR; a validation script that rejects unknown identifiers; any assertion, fixture, name, or behavior change.
- **Dependencies**: land after `plans/20261029-092424_eventbus003_test-lifecycle-production-path.md` and the Plans it lists (`plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md`, `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`), or rebase carefully: they edit some of the same test files in different regions, and line numbers in this Plan will drift, so the implementation re-runs the inventory search instead of trusting recorded lines (sequencing dependency, neither blocks this Plan). `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md` is otherwise related, with no ordering required.

## Background
The same identifier carries different meanings by file. `REQ-002` is "per-consumer DLQ promotion" in `tests/eventbus/test_eventbus_dlq_promotion.py:259,498` and "startup failure and schema-shape gate" in `tests/eventbus/test_eventbus_startup.py:213,259,288`; it also labels DLQ requeue rollback in `test_eventbus_requeue_edge_cases.py` and `test_eventbus_dlq.py` and `${ENV:...}` token resolution in `test_eventbus_config.py`. `REQ-004` is "total and items describe one snapshot" in `test_eventbus_dlq_promotion.py:277` and "readiness and loopback binding" in `test_eventbus_startup.py:158,310,378`.

Inventory measured with `rg -e '\b(REQ|UNK|AC|SEQ|H)-[0-9]+' tests/eventbus` (checked in Step 2): 109 occurrences in 18 files — 95 `REQ-`, 11 `AC-`, 2 `UNK-`, 1 `SEQ-`, 0 `H-`. All of them sit in comments or docstrings; a search for an identifier inside `assert`, `match=`, `raises`, `pytest.mark`, `def test_`, or `parametrize` lines found none (checked in Step 2). No `REQ-nnn` is defined in `docs/24_eventbus/` or `docs/10_adr/` (`rg`, checked in Step 2). Canonical identifiers exist: ADR-006 invariants `INV-01` to `INV-16` (`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md:172-187`) and ADR-013 invariants `INV-01` to `INV-07` (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md:187-193`). The `REQ-*` numbers come from per-Plan requirement lists in `plans/` and `plans/done/`, which are not a lasting definition source. Tools under `tools/` use their own `REQ-` labels internally and do not scan test comments (checked in Step 3).

Corrections to the Issue (Step 2 findings):
- `H-nn` does not occur in `tests/eventbus/`; it occurs only in `docs/24_eventbus/eventbus_03_dlq_operations.md:146` (`H-01`). `UNK-` occurs twice in tests (`test_admin_topics_authorization.py:146` `UNK-02`, `test_eventbus_ack_endpoint.py:403` `UNK-01`).
- `scripts/eventbus/dlq.py` cites `ADR-006 INV-13` three times (lines 62, 77, 92), not once.
- The target list in the Issue ("including ...") names 8 files; the search finds 18, all in the Implementation Target Files table.
- A fifth style of plan-local identifier, `EVENTBUS-nnn` (for example `test_eventbus_auth.py:1051,1101`), exists outside the Issue's pattern list (see UNK-04).

## Problem
A reader cannot resolve a test comment such as `REQ-004` to a requirement, and a search for the identifier returns unrelated meanings. The comments describe plan history instead of current behavior.

## Reason for Change
Identifiers without a stable definition mislead reviewers and implementers and hide the real contract a test protects. The cost is readability only; no behavior is affected, so the priority is Low and the change is not time-sensitive.

## Implementation Intent
For each identifier, in order of preference: replace it with the ADR invariant or the `docs/24_eventbus/` section that states the rule; rewrite the comment to state the rule in plain words; or delete the identifier when the surrounding text already says enough. Do not create a new numbering scheme in the tests. If an identifier has no canonical home and the rule matters, record the gap as an owner question in the change description instead of inventing a definition. Keep the diff to comments and docstrings, in small commits per group of related test files.

## Requirements
- `REQ-001`: before editing, produce an inventory of every identifier in the 18 files with its meaning in context (read-only search), and map each to an ADR invariant, a `docs/24_eventbus/` section, plain wording, or removal; an identifier whose meaning cannot be established from the surrounding test and docs is reported, not guessed.
- `REQ-002`: in each target file, rewrite or remove every identifier per the mapping, and delete plan-history commentary in the lines touched; identifiers are replaced only in comments and docstrings, in English.
- `REQ-003`: after the change, no `REQ-nnn` remains in `tests/eventbus/` unless it resolves to a definition reachable from the repository docs and is cited with it, and no remaining identifier carries two different meanings.
- `REQ-004`: the diff contains comment and docstring changes only (no assertion, fixture, name, or behavior change, no renamed test) and `uv run pytest tests/eventbus` reports the same pass count before and after.
- `REQ-005`: identifiers that need a new canonical definition are listed as owner questions in the change description and are not defined in the tests.

## Implementation Target Files
**Freeze status**: Frozen (every row is `Verified`; `issue-to-plan` Step 8b
Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/eventbus/test_eventbus_config.py | Modify | Replace or remove `REQ-001` to `REQ-009` labels in config test docstrings | REQ-002, REQ-003; AC-1, AC-2 | `REQ-` at lines 95, 181, 208, 225, 264, 280, 296, 346, 446, 462, 478, 494, 530, 548, 568, 588, 607, 626, 646, 666 (checked in Step 2) | tests/eventbus/test_eventbus_config.py | Verified |
| tests/eventbus/test_eventbus_auth.py | Modify | Replace or remove `AC-2`, `REQ-001` to `REQ-010`, and `SEQ-07` labels | REQ-002, REQ-003; AC-1, AC-2 | `AC-2` at lines 347, 404, 494, 536, 573, 627, 663; `REQ-` at 1051, 1101, 1376, 1409, 1443, 1574; `SEQ-07` at 1709 (checked in Step 2) | tests/eventbus/test_eventbus_auth.py | Verified |
| tests/eventbus/test_eventbus_dlq.py | Modify | Replace or remove `REQ-001` to `REQ-003` labels | REQ-002, REQ-003; AC-1, AC-2 | `REQ-` at lines 79, 102, 130, 148, 149, 179, 246, 317, 578, 642 (checked in Step 2) | tests/eventbus/test_eventbus_dlq.py | Verified |
| tests/eventbus/test_eventbus_startup.py | Modify | Replace or remove `REQ-002`, `REQ-004`, `AC-1`, `AC-4` labels | REQ-002, REQ-003; AC-1, AC-2 | `REQ-` / `AC-` at lines 158, 213, 214, 217, 259, 288, 310, 358, 378 (checked in Step 2) | tests/eventbus/test_eventbus_startup.py | Verified |
| tests/eventbus/test_eventbus_requeue_edge_cases.py | Modify | Replace or remove `REQ-002` and `REQ-005` labels | REQ-002, REQ-003; AC-1, AC-2 | `REQ-` at lines 101, 107, 162, 168, 232, 238, 385, 519, 561 (checked in Step 2) | tests/eventbus/test_eventbus_requeue_edge_cases.py | Verified |
| tests/eventbus/test_eventbus_dlq_pagination.py | Modify | Replace or remove `REQ-001`, `REQ-002`, `REQ-004`, `REQ-005` labels | REQ-002, REQ-003; AC-1, AC-2 | `REQ-` at lines 65, 67, 113, 144, 162 (checked in Step 2) | tests/eventbus/test_eventbus_dlq_pagination.py | Verified |
| tests/eventbus/test_eventbus_dlq_promotion.py | Modify | Replace or remove `REQ-002`, `REQ-004`, `REQ-006` labels | REQ-002, REQ-003; AC-1, AC-2 | `REQ-` at lines 259, 277, 498 (checked in Step 2) | tests/eventbus/test_eventbus_dlq_promotion.py | Verified |
| tests/eventbus/test_eventbus_ack_nack.py | Modify | Replace or remove `REQ-001`, `REQ-003`, `REQ-004` labels | REQ-002, REQ-003; AC-1, AC-2 | `REQ-` at lines 50, 317, 606, 609, 672 (checked in Step 2) | tests/eventbus/test_eventbus_ack_nack.py | Verified |
| tests/eventbus/test_eventbus_ack_endpoint.py | Modify | Replace or remove `REQ-002`, `REQ-004`, `REQ-006`, `UNK-01` labels | REQ-002, REQ-003; AC-1, AC-2 | `REQ-` / `UNK-01` at lines 210, 366, 403 (checked in Step 2) | tests/eventbus/test_eventbus_ack_endpoint.py | Verified |
| tests/eventbus/test_eventbus_subscribe.py | Modify | Replace or remove `AC-3`, `REQ-001`, `REQ-006` labels | REQ-002, REQ-003; AC-1, AC-2 | `AC-3` at line 204; `REQ-` at 224, 268 (checked in Step 2) | tests/eventbus/test_eventbus_subscribe.py | Verified |
| tests/eventbus/test_eventbus_shutdown.py | Modify | Replace or remove `REQ-001`, `REQ-003`, `REQ-004` labels | REQ-002, REQ-003; AC-1, AC-2 | `REQ-` at lines 108, 145, 160, 236 (checked in Step 2) | tests/eventbus/test_eventbus_shutdown.py | Verified |
| tests/eventbus/test_admin_topics_authorization.py | Modify | Replace or remove `UNK-02`, `REQ-003`, `REQ-004` labels | REQ-002, REQ-003; AC-1, AC-2 | `UNK-02` at line 146; `REQ-` at 290, 349 (checked in Step 2) | tests/eventbus/test_admin_topics_authorization.py | Verified |
| tests/eventbus/test_eventbus_crash_ack.py | Modify | Replace or remove `REQ-006` labels | REQ-002, REQ-003; AC-1, AC-2 | `REQ-006` at lines 83, 93 (checked in Step 2) | tests/eventbus/test_eventbus_crash_ack.py | Verified |
| tests/eventbus/test_eventbus_publish.py | Modify | Replace or remove the `REQ-006` label | REQ-002, REQ-003; AC-1, AC-2 | `REQ-006` at line 121 (checked in Step 2) | tests/eventbus/test_eventbus_publish.py | Verified |
| tests/eventbus/test_eventbus_health.py | Modify | Replace or remove the `REQ-005` label | REQ-002, REQ-003; AC-1, AC-2 | `REQ-005` at line 98 (checked in Step 2) | tests/eventbus/test_eventbus_health.py | Verified |
| tests/eventbus/test_eventbus_consumer_authorization.py | Modify | Replace or remove `REQ-001`, `REQ-005` labels | REQ-002, REQ-003; AC-1, AC-2 | `REQ-` at line 278 (checked in Step 2) | tests/eventbus/test_eventbus_consumer_authorization.py | Verified |
| tests/eventbus/test_eventbus_concurrent.py | Modify | Replace or remove the `REQ-002` label | REQ-002, REQ-003; AC-1, AC-2 | `REQ-002` at line 170 (checked in Step 2) | tests/eventbus/test_eventbus_concurrent.py | Verified |
| tests/eventbus/eventbus_helpers.py | Modify | Replace or remove the `REQ-003` and `REQ-004` labels in the `eventbus_test_tokens` docstring | REQ-002, REQ-003; AC-1, AC-2 | `REQ-003`, `REQ-004` at line 73 (checked in Step 2) | tests/eventbus/test_eventbus_auth.py and the other callers of the helper | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md | Canonical `INV-01` to `INV-16` for persistence, ACK, DLQ, subscribe, and shutdown rules; edit only if the owner approves a missing invariant | REQ-001, REQ-002 |
| docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md | Canonical `INV-01` to `INV-07` for authentication, authorization, and configuration rules | REQ-001, REQ-002 |
| docs/24_eventbus/eventbus_03_dlq_operations.md | Candidate canonical section for DLQ promotion, requeue, and pagination labels | REQ-001, REQ-002 |
| docs/24_eventbus/eventbus_07_configuration-and-operations.md | Candidate canonical section for configuration, startup, and token-resolution labels | REQ-001, REQ-002 |
| docs/24_eventbus/eventbus_10_health_endpoint.md | Candidate canonical section for readiness and health labels | REQ-001, REQ-002 |
| docs/00_index.md | "Document References by Task" locates the Event Bus docs for the inventory | REQ-001 |
| skills/DESIGN.md | Docs content policy (no implementation-location mapping) if an owner-approved doc edit is later made | REQ-005 |

## Acceptance Criteria
- `AC-1` (REQ-002, REQ-003): `rg -e '\b(REQ|UNK|AC|SEQ)-[0-9]+' tests/eventbus` finds no identifier that lacks a definition reachable from the repository docs; each retained identifier is cited together with that definition.
- `AC-2` (REQ-003): no identifier remaining in `tests/eventbus/` has two different meanings (checked by listing each remaining identifier with its files).
- `AC-3` (REQ-004): `uv run pytest tests/eventbus` reports the same pass count before and after, and the diff of each changed file is comment and docstring only.
- `AC-4` (REQ-001, REQ-005): the change description contains the inventory result and the list of owner questions for identifiers without a canonical definition.

## Tests
- `T1` (REQ-004): `uv run pytest tests/eventbus` before and after; compare the pass counts.
- `T2` (REQ-004): for each changed file, compare the AST against `HEAD` with docstrings removed; the comparison must report no difference (one-off check; if the same script is needed three or more times it goes under `tools/` per `AGENTS.md` Global Rule 7).
- `T3` (REQ-003): `rg -e '\b(REQ|UNK|AC|SEQ)-[0-9]+' tests/eventbus` after the change, reviewed against `AC-1` and `AC-2`.
- `T4` (REQ-004): `uv run ruff check tests/eventbus` and `uv run ruff format --check tests/eventbus`.

## Documentation Impact
N/A: no `docs/*.md` update required. A doc or ADR changes only if a rule that a test protects has no canonical statement and the owner approves; in that case the rule's intent and boundary is documented, not an identifier (`skills/DESIGN.md` Docs content policy), and the docs checkers in `routing.md` Tools run. This Plan makes no such edit.

## Assumptions
- The comment-only constraint holds because every occurrence found sits in a comment or docstring (checked in Step 2); falsifiable by the AST comparison `T2`.
- Docstring text is not asserted by any test; the `T1` pass-count comparison confirms it.
- Replacing an identifier with plain wording is preferred when no ADR invariant or doc section states the rule; no new definition is written into the tests or the ADRs here.
- Sequencing with `plans/20261029-092424_eventbus003_test-lifecycle-production-path.md` and the other open Plans (overlaps on `test_eventbus_health.py`, `eventbus_helpers.py`, `test_eventbus_shutdown.py`, `test_admin_topics_authorization.py`, `test_eventbus_dlq.py`, `test_eventbus_dlq_pagination.py`): compatible, because they change code and fixtures while this Plan changes comments, but the implementation re-runs the inventory search against the then-current files.
- The `x_*` prefix audit and test renaming stay with `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether to extend the cleanup to the `REQ-*` comments in `scripts/eventbus/` (46 occurrences of `REQ-`, `UNK-`, `AC-`, `SEQ-` in 10 files, for example `subscribe_route.py`, `ack_route.py`, `app.py`) | Owner decision; the memo scoped the item to tests | Separate Issue if the owner approves; this Plan leaves `scripts/` untouched | False |
| UNK-02 | Where each retained requirement should be defined (an ADR invariant or a `docs/24_eventbus/` section), per identifier | Depends on the content of each ADR and the per-identifier inventory | Decided during the Phase 1 inventory; an identifier with no canonical home becomes an owner question (REQ-005) | False |
| UNK-03 | Whether `H-nn` and `UNK-nn` references in `docs/24_eventbus/` (`eventbus_09_publish_durability.md:85`, `eventbus_03_dlq_operations.md:146`) should also be replaced | Owner decision; outside this Plan's target files | Separate Issue if the owner approves | False |
| UNK-04 | Whether `EVENTBUS-nnn` identifiers (for example `test_eventbus_auth.py:1051,1101`) are in scope; they are outside the Issue's identifier list | Owner decision; occurrence count measured only in `test_eventbus_auth.py` (3 occurrences) | Report the inventory result; add to this cleanup only with the owner's approval, otherwise leave unchanged | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tests/eventbus/test_eventbus_config.py | Modify | Low — comments and docstrings only, no importers affected | 7 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_auth.py | Modify | Low — comments and docstrings only | 15 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_dlq.py | Modify | Low — comments and docstrings only | 13 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_startup.py | Modify | Low — comments and docstrings only | 4 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_requeue_edge_cases.py | Modify | Low — comments and docstrings only | 11 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_dlq_pagination.py | Modify | Low — comments and docstrings only | 12 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_dlq_promotion.py | Modify | Low — comments and docstrings only | 16 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_ack_nack.py | Modify | Low — comments and docstrings only | 16 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_ack_endpoint.py | Modify | Low — comments and docstrings only | 10 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_subscribe.py | Modify | Low — comments and docstrings only | 8 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_shutdown.py | Modify | Low — comments and docstrings only | 3 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_admin_topics_authorization.py | Modify | Low — comments and docstrings only | 7 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_crash_ack.py | Modify | Low — comments and docstrings only | 7 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_publish.py | Modify | Low — comments and docstrings only | 5 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_health.py | Modify | Low — comments and docstrings only | 4 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_consumer_authorization.py | Modify | Low — comments and docstrings only | 5 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_concurrent.py | Modify | Low — comments and docstrings only | 10 commits | N/A | not applicable (rsynced) |
| tests/eventbus/eventbus_helpers.py | Modify | Low — one docstring; the helper has 7 call sites that are not affected by a docstring change | 7 commits | N/A | not applicable (rsynced) |

## Design
Path B classification (18 target files, more than 3). The change is comment and docstring text only, so the Path B analyses are light: architecture — the code and imports do not change, and `PYTHONPATH=scripts uv run lint-imports` reports 6 contracts kept, 0 broken (same command, unchanged `scripts/` and imports, reused from this session); dependency — no symbol, import, or call site changes, and `tools/` scripts use their own `REQ-` labels without scanning test comments (checked in Step 3); historical — 30-day churn is listed in Affected areas and `git shortlog` gave no output, so bus factor is `N/A`; operational — no port, database, or dependency is involved. Validation quality baseline (Step 5): `N/A: no Python target under scripts/ or tools/`.

Mapping procedure for the implementation (no new numbering scheme):
1. Inventory by a read-only search, listing each identifier with the file, the line, and its meaning from the surrounding test, docs, and the originating Plan (for context only, since Plans are not a lasting source).
2. For each identifier, choose in order: (a) cite the ADR-006 or ADR-013 invariant or the `docs/24_eventbus/` section that states the rule; (b) restate the rule in plain words; (c) delete the identifier when the text already says enough. Examples of candidate canonical homes from Background: the DLQ promotion label to ADR-006 `INV-13`, the loopback-binding label to ADR-006 `INV-15` or ADR-013 `INV-06`, the role-isolation `AC-2` labels in `test_eventbus_auth.py` to ADR-013 `INV-02` or `INV-03`, the empty-authorization label to ADR-013 `INV-07`. These are starting hypotheses to confirm against each test, not decisions.
3. If an identifier has no canonical home and the rule matters, remove the identifier and list the gap as an owner question.

Grouping for small, independently revertable commits: configuration and lifecycle files; authentication and authorization files; DLQ files; ACK, publish, subscribe, and concurrency files.

## Implementation steps
1. **Phase 1: Inventory and mapping (read-only)**
   - [ ] Run the identifier search over the 18 target files (and `EVENTBUS-nnn` for UNK-04), record each identifier's meaning and chosen mapping or removal, and list owner questions (REQ-001, REQ-005; File Path: tests/eventbus/test_eventbus_config.py, tests/eventbus/test_eventbus_auth.py, tests/eventbus/test_eventbus_dlq.py, tests/eventbus/test_eventbus_startup.py, tests/eventbus/test_eventbus_requeue_edge_cases.py, tests/eventbus/test_eventbus_dlq_pagination.py, tests/eventbus/test_eventbus_dlq_promotion.py, tests/eventbus/test_eventbus_ack_nack.py, tests/eventbus/test_eventbus_ack_endpoint.py, tests/eventbus/test_eventbus_subscribe.py, tests/eventbus/test_eventbus_shutdown.py, tests/eventbus/test_admin_topics_authorization.py, tests/eventbus/test_eventbus_crash_ack.py, tests/eventbus/test_eventbus_publish.py, tests/eventbus/test_eventbus_health.py, tests/eventbus/test_eventbus_consumer_authorization.py, tests/eventbus/test_eventbus_concurrent.py, tests/eventbus/eventbus_helpers.py)
2. **Phase 2: Configuration and lifecycle files**
   - [ ] Apply the mapping to comments and docstrings (REQ-002, REQ-003, REQ-004; File Path: tests/eventbus/test_eventbus_config.py, tests/eventbus/test_eventbus_startup.py, tests/eventbus/test_eventbus_shutdown.py, tests/eventbus/test_eventbus_health.py, tests/eventbus/eventbus_helpers.py)
3. **Phase 3: Authentication and authorization files**
   - [ ] Apply the mapping to comments and docstrings (REQ-002, REQ-003, REQ-004; File Path: tests/eventbus/test_eventbus_auth.py, tests/eventbus/test_admin_topics_authorization.py, tests/eventbus/test_eventbus_consumer_authorization.py)
4. **Phase 4: DLQ files**
   - [ ] Apply the mapping to comments and docstrings (REQ-002, REQ-003, REQ-004; File Path: tests/eventbus/test_eventbus_dlq.py, tests/eventbus/test_eventbus_dlq_pagination.py, tests/eventbus/test_eventbus_dlq_promotion.py, tests/eventbus/test_eventbus_requeue_edge_cases.py)
5. **Phase 5: ACK, publish, subscribe, and concurrency files**
   - [ ] Apply the mapping to comments and docstrings (REQ-002, REQ-003, REQ-004; File Path: tests/eventbus/test_eventbus_ack_nack.py, tests/eventbus/test_eventbus_ack_endpoint.py, tests/eventbus/test_eventbus_subscribe.py, tests/eventbus/test_eventbus_crash_ack.py, tests/eventbus/test_eventbus_publish.py, tests/eventbus/test_eventbus_concurrent.py)
6. **Phase 6: Verification**
   - [ ] Run the validation plan; report the inventory result and the owner questions in the change description; deployment: N/A, no `scripts/` or `config/` change, so no `skills/deploy/SKILL.md` hand-off (REQ-003, REQ-004, REQ-005; File Path: tests/eventbus/test_eventbus_config.py, tests/eventbus/test_eventbus_auth.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus | Regression (before and after each group) | `uv run pytest tests/eventbus` | Same pass count before and after |
| changed test files | Comment-only check | AST comparison against `HEAD` with docstrings removed, per changed file (one-off) | No difference |
| tests/eventbus | Identifier search | `rg -e '\b(REQ|UNK|AC|SEQ)-[0-9]+' tests/eventbus` | Only cited identifiers with a reachable definition remain |
| tests/eventbus | Static | `uv run ruff check tests/eventbus`; `uv run ruff format --check tests/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean |
| whole change | Scope | `git diff --stat` | Only the 18 target files |

## Risks
- **Risk**: an identifier is mapped to the wrong invariant, creating a new misleading reference → **Mitigation**: each mapping is checked against the test's behavior and the ADR text during the Phase 1 inventory; when the meaning cannot be established, the identifier is removed and reported (REQ-001).
- **Risk**: an edit slips into executable code → **Mitigation**: the `T2` AST comparison and the `AC-3` pass-count check; each group is a separate commit that can be reverted.
- **Risk**: a large diff across 18 files conflicts with the open Plans that edit the same files (code changes, different regions) → **Mitigation**: land after them or rebase, re-run the inventory search against current files, and keep one commit per file group.
- **Risk**: the cleanup scope creeps into production comments or docs → **Mitigation**: UNK-01 and UNK-03 record those as separate owner decisions, and the frozen target table excludes them.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Inventory identifiers in the 18 target files and decide the mapping (read-only) | Pending | — | — | REQ-001, REQ-005 |
| 2 | Clean configuration and lifecycle files (tests/eventbus/test_eventbus_config.py, tests/eventbus/test_eventbus_startup.py, tests/eventbus/test_eventbus_shutdown.py, tests/eventbus/test_eventbus_health.py, tests/eventbus/eventbus_helpers.py) | Pending | — | — | REQ-002, REQ-003, REQ-004 |
| 3 | Clean authentication and authorization files (tests/eventbus/test_eventbus_auth.py, tests/eventbus/test_admin_topics_authorization.py, tests/eventbus/test_eventbus_consumer_authorization.py) | Pending | — | — | REQ-002, REQ-003, REQ-004 |
| 4 | Clean DLQ files (tests/eventbus/test_eventbus_dlq.py, tests/eventbus/test_eventbus_dlq_pagination.py, tests/eventbus/test_eventbus_dlq_promotion.py, tests/eventbus/test_eventbus_requeue_edge_cases.py) | Pending | — | — | REQ-002, REQ-003, REQ-004 |
| 5 | Clean ACK, publish, subscribe, and concurrency files (tests/eventbus/test_eventbus_ack_nack.py, tests/eventbus/test_eventbus_ack_endpoint.py, tests/eventbus/test_eventbus_subscribe.py, tests/eventbus/test_eventbus_crash_ack.py, tests/eventbus/test_eventbus_publish.py, tests/eventbus/test_eventbus_concurrent.py) | Pending | — | — | REQ-002, REQ-003, REQ-004 |
| 6 | Run the validation plan; report the inventory and owner questions; no deploy (tests only) | Pending | — | — | REQ-003, REQ-004, REQ-005 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-090453_eventbus004_test-requirement-id-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-092617
- **Related target files**: tests/eventbus/test_eventbus_config.py, tests/eventbus/test_eventbus_auth.py, tests/eventbus/test_eventbus_dlq.py, tests/eventbus/test_eventbus_startup.py, tests/eventbus/test_eventbus_requeue_edge_cases.py, tests/eventbus/test_eventbus_dlq_pagination.py, tests/eventbus/test_eventbus_dlq_promotion.py, tests/eventbus/test_eventbus_ack_nack.py, tests/eventbus/test_eventbus_ack_endpoint.py, tests/eventbus/test_eventbus_subscribe.py, tests/eventbus/test_eventbus_shutdown.py, tests/eventbus/test_admin_topics_authorization.py, tests/eventbus/test_eventbus_crash_ack.py, tests/eventbus/test_eventbus_publish.py, tests/eventbus/test_eventbus_health.py, tests/eventbus/test_eventbus_consumer_authorization.py, tests/eventbus/test_eventbus_concurrent.py, tests/eventbus/eventbus_helpers.py

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (inventory, mapping); inventory measured by `rg` over `tests/eventbus` (Step 2) | N/A: read-only inventory across all 18 files in `Implementation Target Files` | Phase 1 | AC-4 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background (per-file evidence) | tests/eventbus/test_eventbus_config.py | Phase 2 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_startup.py | Phase 2 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_shutdown.py | Phase 2 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_health.py | Phase 2 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/eventbus_helpers.py | Phase 2 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_auth.py | Phase 3 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_admin_topics_authorization.py | Phase 3 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_consumer_authorization.py | Phase 3 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_dlq.py | Phase 4 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_dlq_pagination.py | Phase 4 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_dlq_promotion.py | Phase 4 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_requeue_edge_cases.py | Phase 4 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_ack_nack.py | Phase 5 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_ack_endpoint.py | Phase 5 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_subscribe.py | Phase 5 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_crash_ack.py | Phase 5 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_publish.py | Phase 5 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (rewrite or remove) / Background | tests/eventbus/test_eventbus_concurrent.py | Phase 5 | AC-1 | T3 | Confirmed by repository evidence |
| REQ-003 | Acceptance Criteria 1-2 (no unresolved `REQ-nnn`, no two meanings) | N/A: repository-wide outcome verified by search over all 18 files in `Implementation Target Files` | Phases 2-5 | AC-1, AC-2 | T3 | Explicit in issue |
| REQ-004 | Constraints (comments and docstrings only); Acceptance Criteria 3 | N/A: constraint on every file in `Implementation Target Files`, verified by AST comparison | Phases 2-6 | AC-3 | T1, T2, T4 | Explicit in issue |
| REQ-005 | Required Changes (owner questions); Acceptance Criteria 4 | N/A: change-description output, no file modification | Phases 1, 6 | AC-4 | T3 | Explicit in issue |
