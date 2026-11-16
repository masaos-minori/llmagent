# Classify fallback matches before filing compatibility removal issues

## Priority
Low

## Summary
Make compatibility reviews repeatable by finishing the terminology that separates backward compatibility from operational fallback, replay, and idempotency, and by requiring classification evidence before a `fallback` or `legacy` search hit becomes a removal issue.

## Background
Source: `memo-issue.md` Issue 6 (item L-02), re-verified against current docs.

- Documentation only: `docs/00_governance/governance_02_documentation-metadata.md` ("Compatibility and Lifecycle Terminology") already defines Backward Compatibility, Operational Fallback, Default, Lenient Parsing, Migration, Obsolete, and Dead Code, and states that a fallback is a per-call runtime decision distinct from backward compatibility. The memo's request to define the first two terms is therefore already met.
- Not found: glossary rows for Replay and Idempotency, and any review checklist that requires classifying a `fallback` search hit before a removal issue is created. No such guidance was found in `docs/00_governance/governance_04_documentation-checks.md`, `docs/00_governance/governance_01_documentation-policy.md`, or `skills/python-code-review/workflow.md`; its true home, if any, is `不明`.
- Documentation only: the EventBus docs use the word "fallback" for `Last-Event-ID` handling (`docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`). Whether this wording is ambiguous in practice is `Needs confirmation`.
- The memo's `docs/30_agent/` path does not exist; the agent documents are under `docs/23_agent/`.

## Problem
A search for `fallback`, `legacy`, or `compatibility` returns both removable compatibility paths and valid runtime resilience (SSE resume through `Last-Event-ID`, consumer-offset replay, idempotent duplicate publication, preserving a committed event when a post-commit step fails). Without a classification step, such a hit can turn into a false-positive removal task and risk deleting a current reliability feature. The glossary does not yet name replay and idempotency as separate categories, and no review guidance demands classification first.

## Reason for Change
Review accuracy and maintainability: compatibility reviews are being run repeatedly, and each unclassified hit costs triage time or risks a wrong deletion. The change is documentation only and not time-sensitive.

## Implementation Intent
Extend the existing glossary rather than add a parallel one: add the missing terms (replay, idempotency) with a repository-specific example each, and add a short classification rule to the compatibility-review guidance, wherever that guidance lives. Keep terminology edits separate from behavior changes; open a separate issue if a concrete obsolete path is found.

## Target Files or Areas
- `docs/00_governance/governance_02_documentation-metadata.md`
- `docs/00_governance/governance_04_documentation-checks.md` (if it hosts the compatibility-review guidance)
- `docs/24_eventbus/eventbus_03_dlq_operations.md` and `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` (wording only, if ambiguity is confirmed)
- Compatibility review checklist source: `Unknown`

## Required Changes
- Add glossary rows for Replay and Idempotency, distinct from Backward Compatibility and Operational Fallback, each with a category-level example (the glossary says its examples name no specific symbol).
- Locate the compatibility-review guidance and add the rule that a `fallback` or `legacy` match must be classified (backward compatibility, operational fallback, replay, idempotency, or other) with evidence before a removal issue is filed.
- Review the EventBus, agent, and DB documents for current-tense wording that presents resume, replay, idempotent publication, or post-commit resilience as a compatibility shim, and reword only where the ambiguity is confirmed.

## Constraints
- Docs are written in English and follow `skills/DESIGN.md` "Docs content policy — remove" and "No concrete configuration values".
- The glossary holds project-specific terms only and its examples name no specific symbol (`governance_02` rule).
- No behavior change.

## Acceptance Criteria
- [ ] The glossary distinguishes backward compatibility, operational fallback, replay, and idempotency.
- [ ] Review guidance requires classification evidence before a compatibility removal issue is filed.
- [ ] EventBus resume and post-commit resilience are not described as compatibility shims in current documents.
- [ ] Examples are category-level and consistent with the glossary's no-symbol rule, and the behaviors they describe exist in the repository.

## Testing Expectations
Documentation-only. Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain eventbus`, `uv run python tools/check_docs_japanese.py`, and `uv run python tools/check_compat_shims.py`.

## Documentation Impact
This is a documentation change: definitions and review guidance (intent and boundaries of each term). If a Needs Confirmation marker is added or resolved, run `uv run python tools/check_needs_confirmation_inventory.py`.

## Out of Scope
- Removing or changing any EventBus, workflow, or DB behavior.
- Changes to the compatibility checker (separate issue).
- Rewriting documents that do not use the ambiguous wording.
- The EventBus facade: `scripts/eventbus/db.py` is already deleted and its imports are already guarded, so no facade issue is filed.

## Dependencies
- Recommended after `issues/20261116-114912_compat003_workflow-lease-docs-runbook.md` so that current behavioral documentation is corrected first (order only).
- Sibling check: no other open issue or in-flight plan touches these documents.

## Unresolved Questions
- Where does the compatibility review checklist live, and is it separate from the glossary and `governance_04`? `不明`.
- Is the EventBus `fallback` wording actually mistaken for compatibility anywhere? `Needs confirmation`; if not, the EventBus part of this issue is empty.
- Should replay and idempotency be glossary terms or covered by the review rule only? `不明`, decide at plan time.

## AI Implementation Instruction
Edit only the glossary, the located review guidance, and any EventBus wording confirmed as ambiguous. Do not change behavior or unrelated documents. Run the documentation checkers before finishing. Stop and report if the review-guidance location cannot be found.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261116-115026
- **Related target files**: `docs/00_governance/governance_02_documentation-metadata.md`, `docs/00_governance/governance_04_documentation-checks.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
