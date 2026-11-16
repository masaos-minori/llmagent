## Goal
Make compatibility reviews repeatable by finishing the terminology that separates backward compatibility from operational fallback, replay, and idempotency: add the missing Replay and Idempotency glossary rows to `governance_02`, and add a classification rule to the compatibility-review guidance in `governance_04` so a `fallback` or `legacy` search hit is classified (backward compatibility, operational fallback, replay, idempotency, or other) with evidence before a removal issue is filed. Reword EventBus wording only where ambiguity is confirmed.

## Priority
Low

## Scope
- **In-Scope**: Add category-level `Replay` and `Idempotency` rows to the Compatibility and Lifecycle Terminology table in `docs/00_governance/governance_02_documentation-metadata.md`; add a short classification rule to the Backward Compatibility Check section of `docs/00_governance/governance_04_documentation-checks.md` requiring classification evidence before a compatibility removal issue is filed; review the EventBus, agent, and DB documents for current-tense wording that presents resume, replay, idempotent publication, or post-commit resilience as a compatibility shim and reword only where the ambiguity is confirmed.
- **Out-of-Scope**: Changing any EventBus, workflow, or DB behavior; changes to the compatibility checker (separate issue); rewriting documents that do not use the ambiguous wording; the EventBus facade (`scripts/eventbus/db.py` already deleted and guarded); adding a parallel glossary or a separate review-checklist file when the guidance already has a home.
- **Dependencies**: Recommended after `issues/20261116-114912_compat003_workflow-lease-docs-runbook.md` so current behavioral documentation is corrected first (order only). No other open issue or in-flight plan touches these documents (sibling check passed).
  - **Depends on**: `plans/20261116-224307_compat003_workflow-lease-docs-runbook.md` | phase all | sequencing-only: correct current behavioral documentation first so the replay/idempotency examples reference corrected text; not a technical dependency.

## Background
Documentation only. `docs/00_governance/governance_02_documentation-metadata.md` ("Compatibility and Lifecycle Terminology") already defines Backward Compatibility, Operational Fallback, Default, Lenient Parsing, Migration, Obsolete, and Dead Code, and states that a fallback is a per-call runtime decision distinct from backward compatibility — so the memo's request to define the first two terms is already met. The glossary holds project-specific terms only and its examples describe categories and name no specific symbol. Two behaviors the memo wants named exist in the repository: stream/consumer replay via a stored position (EventBus `event_repo.py`, `delivery_repo.py`, `subscribe_route.py`, `ack_route.py` resume from offset / `Last-Event-ID` and re-deliver unacked events) and idempotent duplicate handling (dedup / at-most-once publication referenced across `scripts/`). Not found anywhere in `docs/` or `skills/` is a human compatibility-review checklist that requires classifying a `fallback`/`legacy` hit before a removal issue is created; the single compatibility-review guidance is the Backward Compatibility Check section (`check_compat_shims.py`) of `governance_04`. The EventBus docs use "fallback" for `Last-Event-ID` precedence and low-water-mark resume (`eventbus_03_dlq_operations.md:74`, `eventbus_05_dlq_offsets_and_delivery_semantics.md:115,133`); per the existing Operational Fallback definition these are runtime-resume / precedence concepts, not backward-compatibility shims, so whether they are ambiguous is `Needs confirmation`.

## Problem
A search for `fallback`, `legacy`, or `compatibility` returns both removable compatibility paths and valid runtime resilience (SSE resume through `Last-Event-ID`, consumer-offset replay, idempotent duplicate publication, preserving a committed event when a post-commit step fails). Without a classification step, such a hit can turn into a false-positive removal task and risk deleting a current reliability feature. The glossary does not yet name replay and idempotency as separate categories, and no review guidance demands classification first.

## Reason for Change
Review accuracy and maintainability: compatibility reviews are run repeatedly, and each unclassified hit costs triage time or risks a wrong deletion. The change is documentation only and not time-sensitive.

## Implementation Intent
Extend the existing glossary rather than add a parallel one: add the missing terms (Replay, Idempotency) with a repository-specific, category-level example each (no specific symbol, per the glossary rule), and add a short classification rule to the compatibility-review guidance wherever it lives (`governance_04` Backward Compatibility Check section). Keep terminology edits separate from behavior changes; reword EventBus wording only where ambiguity is confirmed, and open a separate issue if a concrete obsolete path is found.

## Requirements
- `REQ-001`: Add category-level `Replay` and `Idempotency` rows to the Compatibility and Lifecycle Terminology table in `governance_02`, distinct from Backward Compatibility and Operational Fallback, each with a repository-specific, category-level example that names no specific symbol. (`docs/00_governance/governance_02_documentation-metadata.md`)
- `REQ-002`: Add a short classification rule to the Backward Compatibility Check section of `governance_04` stating that a `fallback` or `legacy` search hit must be classified (backward compatibility, operational fallback, replay, idempotency, or other) with evidence before a compatibility removal issue is filed. (`docs/00_governance/governance_04_documentation-checks.md`)
- `REQ-003`: Review the EventBus, agent, and DB documents for current-tense wording that presents resume, replay, idempotent publication, or post-commit resilience as a compatibility shim; reword only where the ambiguity is confirmed. (`docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` — conditional)

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/00_governance/governance_02_documentation-metadata.md` | Add `Replay` and `Idempotency` rows to the Compatibility and Lifecycle Terminology table, category-level examples naming no specific symbol. | REQ-001; AC: glossary distinguishes backward compatibility, operational fallback, replay, idempotency; examples category-level and behaviors exist in repo. | Glossary exists with 7 terms but no Replay/Idempotency row; examples-name-no-symbol rule at `governance_02:108`; replay/idempotency behaviors present in `scripts/` (`event_repo.py`, `delivery_repo.py`, dedup across `scripts/`). None | Verified |
| `docs/00_governance/governance_04_documentation-checks.md` | Add the classification-before-removal rule to the Backward Compatibility Check section. | REQ-002; AC: review guidance requires classification evidence before a removal issue is filed. | Section 4 is the sole compatibility-review guidance; it already notes manual review covers still-defined-but-superseded functions (`governance_04:110-111`). None | Verified |

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
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Confirm the `fallback` wording (`Last-Event-ID` precedence) is runtime-resume/precedence, not a backward-compatibility shim; reword only if ambiguity is confirmed. | `docs/24_eventbus/eventbus_03_dlq_operations.md` (`REQ-003`) |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Confirm the low-water-mark and `Last-Event-ID` `fallback` usages are operational resume/precedence per the Operational Fallback definition; reword only if ambiguity is confirmed. | `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` (`REQ-003`) |
| `docs/00_governance/governance_01_documentation-policy.md` | Confirm the compatibility-review guidance does not already live here (spec/source conflict classification, not compat removal); it does not, so no rule is added here. | `docs/00_governance/governance_04_documentation-checks.md` (`REQ-002`) |
| `docs/00_governance/governance_02_documentation-metadata.md` | Source of truth for the glossary format and the no-symbol rule when adding the new rows. | `docs/00_governance/governance_02_documentation-metadata.md` (`REQ-001`) |

## Acceptance Criteria
- [ ] The glossary distinguishes backward compatibility, operational fallback, replay, and idempotency as separate categories. (`REQ-001`, AC line 43)
- [ ] Review guidance requires classification evidence before a compatibility removal issue is filed. (`REQ-002`, AC line 44)
- [ ] EventBus resume and post-commit resilience are not described as compatibility shims in current documents. (`REQ-003`, AC line 45)
- [ ] Examples are category-level and consistent with the glossary's no-symbol rule, and the behaviors they describe exist in the repository. (`REQ-001`, AC line 46)

## Tests
Documentation-only. Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain eventbus`, `uv run python tools/check_docs_japanese.py`, and `uv run python tools/check_compat_shims.py`. (`Testing Expectations`)
- If a Needs Confirmation marker is added or resolved: `uv run python tools/check_needs_confirmation_inventory.py`. (`Documentation Impact`)
- Manual: confirm the new Replay/Idempotency examples describe behaviors that actually exist (`scripts/eventbus/*` resume/re-delivery; idempotent/dedup handling in `scripts/`), and that no added example names a specific symbol.

## Documentation Impact
This is a documentation change: definitions and review guidance (intent and boundaries of each term). Driven by `REQ-001` through `REQ-003`. The target docs, resolved by task via `docs/00_index.md` / `routing.md`: the governance metadata doc under `docs/00_governance/` (`governance_02`) for the glossary rows, and the governance checks doc under `docs/00_governance/` (`governance_04`) for the classification rule; the EventBus docs under `docs/24_eventbus/` (`eventbus_03`, `eventbus_05`) only if ambiguity is confirmed.

## Assumptions
- The human compatibility-review guidance has no existing home in `docs/` or `skills/`; the sole compatibility-review guidance is the Backward Compatibility Check section of `governance_04`, so the classification rule goes there. This resolves `UNK-01` as non-blocking.
- The EventBus `fallback` wording is operational resume / precedence, not a backward-compatibility shim, per the existing Operational Fallback definition ("a live, per-call runtime decision"); therefore the EventBus part is likely empty and rewording is conditional on a confirmed ambiguity. This partially resolves `UNK-02`.
- Replay and Idempotency belong as glossary rows (not only a review rule), because the Issue's acceptance criteria require the glossary to distinguish all four categories. This resolves `UNK-03`.
- The new glossary examples can stay category-level and name no specific symbol while still describing repository behaviors that exist (`scripts/eventbus/*` resume/re-delivery; idempotent/dedup handling).
- Documentation changes have no runtime blast radius; `deploy.sh` serves docs statically (rsynced), so there is no deploy-gate impact.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Where does the compatibility review checklist live, and is it separate from the glossary and `governance_04`? | None — no checklist exists in `docs/` or `skills/`; `governance_04` section 4 is the sole compatibility-review guidance. | Resolved: add the classification rule to `governance_04` section 4. | False |
| UNK-02 | Is the EventBus `fallback` wording actually mistaken for compatibility anywhere? | None beyond a final read at implementation — the existing usage reads as runtime-resume/precedence. | Resolved: conditional; reword only if a concrete misreading is found during the doc review. If none, the EventBus part is empty. | False |
| UNK-03 | Should replay and idempotency be glossary terms or covered by the review rule only? | None — the Issue's AC requires the glossary to distinguish all four categories. | Resolved: add them as glossary rows. | False |

No item from Step 2 remains `Needs confirmation`; nothing is `BLOCKING`.

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/00_governance/governance_02_documentation-metadata.md` | Modify | Low — governance doc only; defines terms operators rely on for triage | Multiple contributors | not applicable (rsynced) |
| `docs/00_governance/governance_04_documentation-checks.md` | Modify | Low — governance doc only; adds review guidance | Multiple contributors | not applicable (rsynced) |

## Design
Three design decisions the Issue left open are resolved below with rationale and compatibility impact.

### Decision 1 — Replay and Idempotency go in the glossary, not only the review rule
- **Choice**: add `Replay` and `Idempotency` as rows in the Compatibility and Lifecycle Terminology table in `governance_02`, each with a category-level example that names no specific symbol.
- **Alternatives considered**: covering them only via the review rule, or adding a parallel glossary. The Issue's acceptance criteria require the glossary itself to distinguish all four categories, and the glossary rule forbids a parallel register.
- **Rationale for the choice**: the glossary is the canonical place operators consult to classify a hit; naming the terms there is what makes the review rule actionable. Examples stay category-level per `governance_02:108`.
- **Compatibility impact**: additive; the new examples must describe behaviors that exist in the repository (`scripts/eventbus/*` resume/re-delivery; idempotent/dedup handling).

### Decision 2 — The classification rule lives in `governance_04`, not a new file
- **Choice**: add the classification-before-removal rule to the Backward Compatibility Check section (`check_compat_shims.py`) of `governance_04`.
- **Alternatives considered**: creating a new review-checklist document. No human compat-review guidance exists elsewhere in `docs/` or `skills/` (verified), and `governance_04` section 4 already describes how compat reviews work and notes manual review covers still-defined-but-superseded functions.
- **Rationale for the choice**: `governance_04` section 4 is the single compatibility-review guidance; appending the classification rule keeps one home instead of fragmenting guidance across the glossary and a new file.
- **Compatibility impact**: additive guidance; no checker behavior changes.

### Decision 3 — EventBus reword is conditional, and likely empty
- **Choice**: treat the EventBus `fallback` wording as operational resume / precedence (per the Operational Fallback definition) and reword only if a concrete misreading as a compat shim is confirmed during the doc review.
- **Alternatives considered**: rewording all EventBus `fallback` mentions preemptively. That would change current, arguably-correct wording without evidence of harm.
- **Rationale for the choice**: the existing usage (`Last-Event-ID` precedence, low-water-mark resume) matches "a live, per-call runtime decision," so it is not a backward-compatibility shim; the Issue itself says the EventBus part is empty if the wording is not actually mistaken.
- **Compatibility impact**: zero if the review finds no ambiguity (the expected outcome).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Glossary rows (`governance_02`)**
   - [ ] REQ-001; `docs/00_governance/governance_02_documentation-metadata.md` — append `Replay` and `Idempotency` rows to the Compatibility and Lifecycle Terminology table, category-level examples naming no specific symbol and describing repository behaviors that exist.
2. **Phase 2: Classification rule (`governance_04`)**
   - [ ] REQ-002; `docs/00_governance/governance_04_documentation-checks.md` — add the classification-before-removal rule to the Backward Compatibility Check section, listing the categories (backward compatibility, operational fallback, replay, idempotency, other) and requiring evidence before a removal issue is filed.
3. **Phase 3: EventBus/agent/DB wording review (conditional)**
   - [ ] REQ-003; `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` — confirm the `fallback` wording is operational resume/precedence; reword only where ambiguity is confirmed, else leave unchanged and note it.
   - [ ] Review agent and DB documents for current-tense shim-presenting wording; reword only where confirmed.
4. **Phase 4: Documentation checks**
   - [ ] Run the documentation checkers in `Tests`; run `check_needs_confirmation_inventory.py` if a marker was added or resolved.

### Release units
N/A: no release unit. This is a documentation-only change with no runtime callers or tests to break.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `governance_02` | New glossary rows present, distinct categories, category-level no-symbol examples; content-policy clean. | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` | All pass; no new errors. |
| `governance_04` | Classification rule present, structure/content clean. | `uv run python tools/check_docs_quality.py`, `check_docs_content_policy.py` | All pass; no new errors. |
| `eventbus_03`, `eventbus_05` | Cross-checked against EventBus config/source; not described as shims. | `uv run python tools/check_docs_consistency.py --domain eventbus` | Passes; no new errors. |
| Whole change | Full documentation check suite + compat-shim pass. | `check_docs_japanese.py`, `check_compat_shims.py` (+ `check_needs_confirmation_inventory.py` if a marker changed) | All pass. |

## Risks
- **Risk**: Adding glossary examples that name a specific symbol (e.g. `Last-Event-ID`, a specific function) violates the no-symbol rule. → **Mitigation**: keep examples category-level ("resuming a consumer from a stored offset", "re-publishing a duplicate that a dedup check discards"); confirm at implementation against `governance_02:108`.
- **Risk**: Over-deleting or rewording EventBus wording that is correctly describing an operational fallback. → **Mitigation**: reword only where a concrete misreading as a compat shim is confirmed; otherwise leave unchanged (Decision 3).
- **Risk**: Placing the classification rule in the wrong document. → **Mitigation**: `governance_04` section 4 is the sole compatibility-review guidance (verified); `governance_01` handles spec/source conflicts, not compat removal.
- **Risk**: Doc wording drift from `check_docs_content_policy.py` ("No concrete configuration values"). → **Mitigation**: describe categories and behaviors, not config values or specific symbols.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Glossary rows for Replay and Idempotency in `governance_02` | Pending | — | — | Additive |
| 2 | Classification-before-removal rule in `governance_04` | Pending | — | — | Additive guidance |
| 3 | EventBus/agent/DB wording review (conditional reword) | Pending | — | — | Likely empty; reword only if ambiguity confirmed |
| 4 | Documentation checks | Pending | — | — | After edits |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261116-115026_compat005_compat-fallback-terminology.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-000631
- **Related target files**: `docs/00_governance/governance_02_documentation-metadata.md`, `docs/00_governance/governance_04_documentation-checks.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (glossary rows); AC line 43, 46 | `docs/00_governance/governance_02_documentation-metadata.md` | Step 1 | Glossary distinguishes all four categories; examples category-level, behaviors exist | `check_docs_quality.py`, `check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes (classification rule); AC line 44 | `docs/00_governance/governance_04_documentation-checks.md` | Step 2 | Review guidance requires classification evidence before a removal issue | `check_docs_quality.py` | Derived from confirmed evidence (sole compat-review guidance) |
| REQ-003 | Required Changes (wording review); AC line 45 | `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Step 3 | Resume/post-commit resilience not described as shims | `check_docs_consistency.py --domain eventbus` | Conditional; likely no edit needed |
