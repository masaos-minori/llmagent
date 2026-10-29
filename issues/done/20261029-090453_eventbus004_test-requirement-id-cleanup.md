# Replace ambiguous requirement identifiers in EventBus test comments with canonical references

## Priority
Low

## Summary
Requirement identifiers such as `REQ-002`, `REQ-004`, `UNK-01`, `AC-2` and `H-03` appear in comments and docstrings across `tests/eventbus/`, and the same identifier means different things in different files. Map each retained identifier to a canonical, current definition (an ADR invariant or a `docs/24_eventbus/` section), or remove it, and stop using plan-local numbering in test comments.

## Background
Source: `memo-issue.md` item 06 (requirement identifiers), re-verified against current source on 2026-10-29. The archived `issues/done/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md` listed this item, but the plan generated from it, `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`, covers only fixture and prefix terminology and does not touch these identifiers. No open issue or plan covers them.

Evidence (`Explicit in code`):
- The same identifier carries different meanings by file. `REQ-002` is "per-consumer DLQ promotion" in `tests/eventbus/test_eventbus_dlq_promotion.py` and "startup failure and schema-shape gate" in `tests/eventbus/test_eventbus_startup.py`. `REQ-004` is "total and items describe one snapshot" in `test_eventbus_dlq_promotion.py` and "readiness and loopback binding" in `test_eventbus_startup.py`.
- No document under `docs/24_eventbus/` or `docs/10_adr/` defines a `REQ-nnn` identifier. The only hits for `UNK-01`, `H-01` and `H-03` in `docs/24_eventbus/` are references to owner decisions, not definitions (`eventbus_09_publish_durability.md`, `eventbus_03_dlq_operations.md`).
- `REQ-*` numbering also appears in production comments under `scripts/eventbus/` (for example `ack_route.py`, `subscribe_route.py`, `app.py`, `delivery_repo.py`, `dlq.py`).
- Canonical identifiers already exist: ADR invariants such as `INV-nn` in `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` and `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, and `dlq.py` already cites `ADR-006 INV-13` in one place.

The `REQ-*` numbers originate in per-plan requirement lists in `plans/` and `plans/done/`, which are not a lasting definition source.

## Problem
A reader cannot resolve a test comment such as `REQ-004` to a requirement, and a search for the identifier returns unrelated meanings. The comments also describe plan history instead of current behavior.

## Reason for Change
Identifiers without a stable definition mislead reviewers and implementers and hide the real contract a test protects. The cost is readability only; no behavior is affected, so the priority is Low and the change is not time-sensitive.

## Implementation Intent
For each identifier, in order of preference: replace it with the ADR invariant or the doc section that states the rule, rewrite the comment to state the rule in plain words, or delete it when the surrounding text already says enough. Do not create a new numbering scheme in the tests. If an identifier has no canonical home and the rule matters, record the gap as an owner question instead of inventing a definition. Keep the change to comments and docstrings.

## Target Files or Areas
- `tests/eventbus/*.py` comments and docstrings that carry `REQ-nnn`, `UNK-nn`, `AC-n`, `SEQ-nn` or `H-nn` identifiers, including `test_eventbus_config.py`, `test_eventbus_auth.py`, `test_eventbus_dlq.py`, `test_eventbus_startup.py`, `test_eventbus_requeue_edge_cases.py`, `test_eventbus_dlq_promotion.py`, `test_eventbus_dlq_pagination.py` and `test_eventbus_shutdown.py`
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` and `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` (read for the canonical invariants; edit only if a needed invariant is missing and the owner approves)
- Production comments under `scripts/eventbus/`: see Unresolved Questions

## Required Changes
- Inventory every identifier in `tests/eventbus/` with its meaning in context, using a read-only search.
- Map each identifier to an ADR invariant or `docs/24_eventbus/` section, or mark it for removal.
- Rewrite or remove the comments accordingly, and delete plan-history commentary in the lines touched.
- Record identifiers that need a new canonical definition as owner questions instead of defining them in tests.

## Constraints
- Comments and docstrings only; no assertion, fixture, name, or behavior changes. Renaming test functions is out of scope.
- Comments stay in English (`rules/coding.md`).
- Docs edits, if any, follow `skills/DESIGN.md` Docs content policy: no implementation-location mapping, no file trees, and no signature tables.
- Do not cite source line numbers in docs.

## Acceptance Criteria
- No `REQ-nnn` identifier remains in `tests/eventbus/` unless it resolves to a definition reachable from the repository docs, and each retained one is cited with that definition.
- No identifier in `tests/eventbus/` carries two different meanings.
- `uv run pytest tests/eventbus` passes and the diff shows comment and docstring changes only.
- Owner questions for identifiers without a canonical definition are listed in the change description.

## Testing Expectations
- `uv run pytest tests/eventbus` before and after, with the same pass count.
- `uv run ruff check tests/eventbus` and `uv run ruff format --check tests/eventbus` pass.
- If an ADR or doc is edited: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, and `uv run python tools/check_docs_consistency.py --domain eventbus`.

## Documentation Impact
Usually none. A doc or ADR changes only if a rule that a test protects has no canonical statement; in that case document the rule's intent and boundary, not an identifier.

## Out of Scope
- Renaming tests or variables and the `x_*` prefix audit (`plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`).
- Fixture and lifecycle changes (`issues/20261029-090402_eventbus003_test-lifecycle-production-path.md`).
- Production comments under `scripts/eventbus/`, unless the owner approves the extension in Unresolved Questions.
- A validation script that rejects unknown identifiers.

## Dependencies
- Land after `issues/20261029-090402_eventbus003_test-lifecycle-production-path.md` and the plans it lists, or rebase carefully: they edit some of the same test files (`test_eventbus_health.py`, helpers, restart-resume), although in different regions.
- Related, no ordering required: `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md` produces an audit report of the same files for prefix terminology.

## Unresolved Questions
- `Needs confirmation`: whether to extend this cleanup to `REQ-*` comments in `scripts/eventbus/`. The memo scoped the item to tests; production comments carry the same ambiguity.
- `Needs confirmation`: where a retained requirement should be defined, an ADR invariant or a `docs/24_eventbus/` section, per identifier. This depends on the content of each ADR and should be decided while inventorying.
- `Needs confirmation`: whether `H-nn` and `UNK-nn` identifiers in `docs/24_eventbus/` (owner-decision references) should also be replaced; they are outside this issue's target files.

## AI Implementation Instruction
- Change comments and docstrings in `tests/eventbus/` only; do not change code, names, or assertions.
- Do not invent a requirement definition; if no canonical source exists, remove the identifier and list the gap as an owner question.
- Keep the diff reviewable: one commit per group of related test files.
- Stop and report if an identifier's meaning cannot be established from the surrounding test and docs.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-090453
- **Related target files**: `tests/eventbus/*.py`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
