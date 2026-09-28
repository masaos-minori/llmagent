---
title: "Issue and Uncertainty Management"
area: governance
tags:
  - governance
related:
  - ../00_index.md
  - ../01_overview/overview_00_document-guide.md
---

# Issue and Uncertainty Management

## Purpose

This document defines how to track currently active discrepancies between documentation and implementation (Known Issues) and currently active unverified claims (Needs Confirmation). It ensures unconfirmed statements are trackable and actionable, preventing them from being silently accepted as facts.

## Part 1: Known Issues

### Entry Template

Each active Known Issue entry must contain these 17 fields: ID, Title, Status, Severity, Area, Type, Source, Owner, First Found, Target, Related, Summary, Current Description, Observed Implementation, Impact, Recommended Action, Resolution Target.

### Status Values

- **open** — Issue acknowledged but not yet investigated
- **investigating** — Investigation underway
- **deferred** — Resolution postponed to future work

An item is removed from this active inventory once it is resolved or no longer
applies to the current system; it is not retained here with a closed-out status.

### Type Values

- **document-code-mismatch** — Documentation contradicts code behavior
- **document-document-mismatch** — Two documents contradict each other
- **obsolete-description** — Description refers to removed/deprecated feature
- **missing-documentation** — Feature exists without documentation
- **ambiguous-behavior** — Behavior unclear due to insufficient specification
- **implementation-bug** — Code does not match documented intent
- **design-gap** — Missing design consideration
- **operational-gap** — Missing operational guidance

### Severity Values

- **High** — Requires immediate attention; affects safety or critical functionality
- **Medium** — Should be addressed soon; affects correctness or clarity
- **Low** — Can be deferred; minor inconsistency or formatting issue

### Owner Values

- **Unassigned** — No owner assigned
- **[Name]** — Assigned to specific person
- **Team** — Assigned to team decision

### Area Values

Overview, Deployment, RAG, MCP, Agent, EventBus, Shared/DB, Governance

### Lifecycle

Open → Investigating → Deferred, or removed from this inventory once resolved or no
longer applicable to the current system.

### Review Cadence

Part 1 entries are reviewed quarterly, consistent with the cadence documented for Part 2 Needs Confirmation items and "Proposed" ADRs in `docs/governance_01_documentation-policy.md` line 521.

### Consolidation Note

The area-specific `~~rag_90_inconsistencies_and_known_issues~~ (deleted).md`,
`~~mcp_90_inconsistencies_and_known_issues~~ (deleted).md`,
`~~agent_90_inconsistencies_and_known_issues~~ (deleted).md`,
`~~eventbus_90_inconsistencies_and_known_issues~~ (deleted).md`, and
`~~shared_90_inconsistencies_and_known_issues~~ (deleted).md` files were consolidated into this
section on 2026-09-03 and deleted; this document is now the single system of record
for Known Issues across all areas. Existing IDs were preserved as-is (`RAG-*`,
`EVENTBUS-*`, `SHARED-*`, `CI-*`, `DESIGN-*`); one previously untitled RAG entry was
assigned a new ID (`RAG-005`) since the 16-field template requires one. EventBus
entries used a distinct 18-field format with no direct equivalent for `Component`,
`Workaround`, or the `*-Justification` fields — these were folded into `Source`,
`Recommended Action`, and `Current Description`/`Resolution Notes` respectively, per
this template. `CI-*` entries (originally filed under Shared/DB regardless of actual
subject) were re-assigned to the Area their cited ADR/Decision actually concerns,
since several concern RAG, MCP, or Agent behavior rather than Shared/DB.

Two non-Known-Issue notes from the deleted files, with no active items depending on
them, are preserved here rather than lost:

- **Agent 5-Tier Scheme (historical, superseded by this consolidation):** `agent_90`'s design intent
  had, for Agent-area entries only, used a 5-tier classification (Design Decision /
  Implementation Bug / Documentation Gap / Needs Confirmation / Operational
  Observation) as a documented exception to this document's common template,
  reasoning that the common Status/Type fields conflate "accepted design choice"
  with "acknowledged bug awaiting fix." At the time of this consolidation the
  Agent-area file had zero open entries. This consolidation ends that exception —
  all areas, including Agent, now use only this document's common template — since
  a per-area exception has no purpose once there is only one canonical inventory.
- **EventBus schema/implementation note (informational, no issue):** `06_eventbus_90` recorded that
  `acked_at`, `delivery_failure_count`, `dlq_requeue_count`, and `dlq_at` are all
  documented in the schema and all in active use, with no discrepancy — retained
  here only because the source file no longer exists to hold it.

### Active Items

Active Items follow an ordering convention: entries are grouped by ID-prefix (RAG-*, DESIGN-*, EVENTBUS-*, SHARED-*, CI-*), each group's entries in ascending numeric order.


**Removal-placeholder-reference policy**: A `Related`/`Target` field may cite a removed entry's ID only when a removal-placeholder paragraph exists for that ID; without such a placeholder, the citation is treated as a dangling reference (Warning severity if the placeholder exists but no heading, Blocking if neither exists).


**EventBus-specific verification (REQ-006)**: Verified by configuration test confirming `ConfigMissingError` is raised when a required config file is missing. The EventBus `load_config()` function (`scripts/eventbus/config.py`) validates required keys via `_REQUIRED_CONFIG_KEYS` and raises `ValueError` for missing keys — consistent with the fail-closed behavior described in CI-005.

#### CI-012

- **ID**: CI-012
- **Title**: ADR-006 INV-01 — EventBus offset monotonicity, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: operational-gap
- **Source**: `scripts/eventbus/offsets.py::write_offset()`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-03
- **Target**: `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related**: ADR-006, EVENTBUS-001
- **Summary**: ADR-006 states that EventBus offsets must be monotonically increasing.
- **Current Description**: This has been verified via code inspection (`seq > current` enforcement confirmed in `write_offset()`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for offset-monotonicity enforcement.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

#### CI-014

- **ID**: CI-014
- **Title**: ADR-009 INV-01 — `normalized_content` LLM-output prohibition, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: operational-gap
- **Source**: `_format_chunks()`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-15
- **Target**: `docs/10_adr/ADR-009-rag-ft5-text-separation.md`
- **Related**: ADR-009
- **Summary**: ADR-009 states that `normalized_content` must not appear in LLM output.
- **Current Description**: This has been verified via code inspection (`_format_chunks()` uses `c.content`, not `c.normalized_content`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for the `normalized_content` prohibition.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

#### CI-016

- **ID**: CI-016
- **Title**: ADR-004 Decision #12/INV-14 — undefined component criticality treatment relies on a safe default, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: operational-gap
- **Source**: `scripts/shared/mcp_config.py` (`required: bool = True` default), `scripts/agent/services/mcp_tool_discovery.py`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-15
- **Target**: `docs/10_adr/ADR-004-environment-failure-handling-policy.md`
- **Related**: ADR-004
- **Summary**: ADR-004 Decision #12/INV-14 requires that undefined or undeterminable component criticality never be assumed non-required and be treated as an unresolved design/config error.
- **Current Description**: `McpServerConfig.required` enforces a safety net for unspecified criticality values, preventing silent treatment as non-required. However, no automated test verifies this default-required safety net, and no distinct code path flags "criticality was never explicitly configured" as its own design/config error per Decision #12's literal wording — ADR-004's own Completion Checklist and Manual Review notes still list INV-14 as unverified/Manual-Review-only.
- **Observed Implementation**: Verified by code inspection only (default value inspection); no automated test.
- **Impact**: Without test coverage, a future change to the default value (e.g. `required: bool = False`) would silently violate INV-14 with no automated check to catch the regression.
- **Recommended Action**: Add a unit test asserting the required field behavior for unspecified criticality values, and/or a test asserting undefined-criticality components are never routed as non-required.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

Note on CI-012, CI-014, CI-016 batching: These three structurally identical "ADR invariant verified by code inspection, no automated test" entries are treated as one initiative (originally nine members; CI-008, CI-009, CI-010, CI-011, CI-013, and CI-015 were removed once test coverage was added). Their Area fields span EventBus (CI-012), RAG (CI-014), and Agent (CI-016) — one member per area — and no single existing RACI role is accountable for a cross-area ADR-invariant-test-suite initiative. This Plan flags the decision for human determination: create a new cross-cutting role vs. revert to per-area ownership.

## Part 2: Needs Confirmation Inventory

### Purpose

A centralized inventory of all "Needs confirmation" items found across the design documentation set. It makes unconfirmed statements trackable and actionable, preventing them from being silently accepted as facts.

### Inventory Entry Fields

Each entry must contain these fifteen fields: ID, Source File, Section, Line Number, Question, Evidence, Impact, Required Action, Status, Assigned To, Last Reviewed, Priority, Related NC, Resolution Target, Blocking.

### Status Values

- **open** — Acknowledged but not investigated
- **investigating** — Underway
- **deferred** — Postponed

An item is removed from the Active Items list below once it is resolved through a
code or docs update, or once it no longer applies to the current system; it is not
retained here with a closed-out status.

### Priority Values

- **High** — Must resolve before next release
- **Medium** — Resolve within sprint
- **Low** — Nice-to-have

### Extraction Process

Search `docs/` for "Needs confirmation", populate fields from context, add sequential ID, never modify source documents.

### Active Items

#### NC-021

- **Source File**: `~~db_07_db_api_and_operations-recovery-and-reference~~ (deleted).md`
- **Section**: 9.3 Integrity-result model (target design)
- **Line Number**: ~39
- **Question**: ADR-008 (Decision Details #14, merged from former ADR-011) already settles that `INVALID_FORMAT` is kept as a defined-but-currently-unreachable classification, not removed as dead code — the remaining open question is narrower: should a test be added to cover this branch (e.g. via a fixture that triggers it), or is "verified unreachable by design" sufficient?
- **Evidence**: The structured six-state `DbCondition` classification is implemented (`scripts/db/recovery.py`), but `INVALID_FORMAT` is defined and dispatched-on without any code path that produces it — the branch is currently unreachable. ADR-008 Decision Details #14 already resolves the keep-vs-remove question in favor of keeping the enum value and dispatch branch.
- **Impact**: Leaving this unconfirmed risks an untested branch silently diverging from its intended (unreachable-by-design) behavior if the classification logic changes
- **Required Action**: Owner decision on whether test coverage for the unreachable `INVALID_FORMAT` branch is required, or whether "verified unreachable by design per ADR-008 #14" is an acceptable resolution
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-27
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Confirm whether the unreachable `INVALID_FORMAT` branch needs dedicated test coverage, given ADR-008 #14 already settles that it should be kept rather than removed.
- **Blocking**: No

#### NC-027

- **Source File**: `rag_02_03_ingestion_pipeline-chunksplitter.md`
- **Section**: 3. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`) — Module-level Constants
- **Line Number**: ~40
- **Question**: What is the rationale for `MIN_HEADING_LINES_FOR_MARKDOWN = 2` (the minimum heading-line count threshold used to decide Markdown heading-based chunking)?
- **Evidence**: The document already carries an inline marker: "the rationale for `MIN_HEADING_LINES_FOR_MARKDOWN = 2` is unconfirmed (Needs Confirmation)"; the constant is defined in `scripts/rag/ingestion/chunk_splitter.py` with no rationale comment
- **Impact**: Changing this value without knowing its rationale risks unintended changes to heading-based chunk splitting, e.g. short Markdown sections being split incorrectly
- **Required Action**: Owner confirmation, or investigate how this value was originally derived (test cases, empirical validation)
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next ChunkSplitter specification review
- **Blocking**: No

#### NC-028

- **Source File**: `rag_02_08_ingestion_pipeline-shared.md`
- **Section**: FTS5 Query Token Limit
- **Line Number**: ~132
- **Question**: What is the rationale for the FTS5 query token limit of 20 (`_MAX_FTS_TOKENS` in `scripts/rag/repository.py`)? Is it based on measurement or load testing?
- **Evidence**: The document already carries an inline marker: "There is currently no documented rationale within the project for this specific value (20) based on measurement or load testing. As it appears to be a heuristic setting, it should be re-validated during performance tuning."
- **Impact**: An unvalidated limit risks silently truncating long queries (reducing search precision) if too low, or query explosion if raised without validation
- **Required Action**: Re-validate this value against measurement or load testing during RAG query performance tuning
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next RAG query performance tuning pass
- **Blocking**: No

#### NC-029

- **Source File**: `rag_02_09_ingestion_pipeline-shared-utilities.md`
- **Section**: Constants
- **Line Number**: ~47
- **Question**: What is the rationale for `MIN_TEXT_LENGTH_FOR_DETECTION = 100` (the minimum text length required for language detection)?
- **Evidence**: The document already carries an inline marker: "the rationale for `MIN_TEXT_LENGTH_FOR_DETECTION = 100` is unconfirmed (Needs Confirmation)"; the constant is defined in `scripts/rag/utils.py` with no rationale comment
- **Impact**: Changing this threshold without knowing its rationale risks unintended effects on language-detection accuracy for short texts
- **Required Action**: Owner confirmation, or validate against the language-detection library's own empirical guidance
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next language-detection logic review
- **Blocking**: No

#### NC-033

- **Source File**: `rag_02_03_ingestion_pipeline-chunksplitter.md`
- **Section**: lang Field Validation
- **Line Number**: ~194
- **Question**: Is `lang` field enforcement against `LanguageCode` values intended?
- **Evidence**: The document states: "any non-empty string accepted; the en/ja value set (LanguageCode) is convention only — not enforced at parse time (Needs confirmation: whether enforcement is intended)"
- **Impact**: If lang-field enforcement is actually intended but not implemented, downstream language-handling code could behave incorrectly without anyone flagging it as an open question
- **Required Action**: Owner confirmation or investigation of scripts/rag/ validation logic for the lang field
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-14
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next ChunkSplitter specification review
- **Blocking**: No

#### NC-034

- **Source File**: `chunk_splitter.py` / `config/chunk_splitter.toml`
- **Section**: min_chunk / max_chunk / chunk_overlap constants
- **Line Number**: ~70-71, 168-169, 185-186
- **Question**: Why is the minimum chunk size 40 characters, maximum chunk size 500 characters, and overlap 50 characters? What is the historical reason for these specific values?
- **Evidence**: No rationale comment in `chunk_splitter.py` or `config/chunk_splitter.toml`; no ADR or governance entry found. `_min_chunk` (line 70), `_max_chunk` (line 71), and `_chunk_overlap` (line 74) enforce the constraint boundaries documented in `docs/rag_05_1-configuration-reference.md` line 39, but no explanation exists for why 40/500/50 were chosen over any other values.
- **Impact**: Operators cannot understand why sub-40-char chunks are discarded as noise, why sections exceeding 500 chars are split further, or why overlap is set to 50 characters
- **Required Action**: Owner confirmation of the historical reason for these specific values; if resolved, update the chunksplitter documentation accordingly
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-14
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next ChunkSplitter specification review
- **Blocking**: No

#### NC-035

- **Source File**: `crawler.py` / `config/crawler.toml`
- **Section**: max_depth / max_pages operational limits
- **Line Number**: ~61, 66
- **Question**: Why is the crawl depth limited to 3 hops from the start URL, and why is the maximum pages per site limited to 200? What is the historical reason for these specific operational values? Additionally, why does the code's own fallback default for `max_pages` (500) differ from the deployed `config/crawler.toml` value (200)?
- **Evidence**: No rationale comment in `crawler.py` or `config/crawler.toml`; no ADR or governance entry found. `_max_depth` (line 61) and `_max_pages` (line 66) read from `config/crawler.toml` and stop BFS traversal at the limit, but no explanation exists for why 3 and 200 were chosen over any other values. Additionally, `scripts/rag/ingestion/crawler.py:66` falls back to `cfg.get("max_pages", 500)` if the key is absent, while the deployed `config/crawler.toml:23` sets `max_pages = 200` — a code-default-vs-deployed-config mismatch. `config/crawler.toml:22` already carries an inline comment acknowledging this same discrepancy lacks measured justification.
- **Impact**: Operators cannot understand why crawlers stop after 3 hops or 200 pages per site; new developers may not realize these are operational limits rather than technical constraints. The 500-vs-200 mismatch also means removing or misconfiguring the TOML key would silently change deployed behavior to the code's higher default without anyone noticing.
- **Required Action**: Owner confirmation of the historical reason for these specific operational values, and confirmation of which `max_pages` value (500 or 200) is the intended operational limit; if resolved, update the crawler documentation and reconcile the code default with the deployed config accordingly
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-27
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next crawler operations review
- **Blocking**: No

#### NC-036

- **Source File**: `scripts/rag/pipeline_service.py::call_rag_service()` / `ADR-010-rag-fallback.md`
- **Section**: Decision #9 vs. actual behavior
- **Line Number**: Decision #9 (line 69), `call_rag_service()` ValueError handling
- **Question**: Is the parse-error-triggers-fallback behavior an intentional refinement of Decision #9 or an unintended deviation?
- **Evidence**: ADR-010 Decision #9 states "解析エラーはログに記録し、空結果として扱う" (parse errors should be logged and treated as an empty result); however, `call_rag_service()` returns `None` on parse error, triggering fallback. The test `test_json_parse_error_calls_set_fallback_reason` confirms this behavior is actively defended by a passing test.
- **Impact**: An undocumented ADR deviation actively defended by a passing test — operators may assume parse errors are handled per ADR when they actually trigger fallback
- **Required Action**: Owner/architect judgment required: (1) If intentional, amend ADR-010 via ADR Change Protocol + RACI approval from `@data-eng`; (2) If unintended, fix `call_rag_service()` to treat parse errors as empty results per Decision #9. (Priority intentionally differs from neighboring NC entries: this item documents an active code/ADR contradiction with a named owner requiring architect judgment, not an unknown-rationale documentation question.)
- **Status**: open
- **Assigned To**: @data-eng
- **Last Reviewed**: 2026-09-16
- **Priority**: High
- **Related NC**: None
- **Resolution Target**: Next RAG architecture review
- **Blocking**: No

No other active Needs Confirmation items exist outside the set listed here: NC-021, NC-027, NC-028, NC-029, NC-033, NC-034, NC-035, and NC-036.

## Part 3: Canonical Source Conflict

### Purpose

A centralized inventory of all canonical source conflicts found across the design documentation set. It makes conflicting claims trackable and actionable, preventing them from being silently accepted as facts.

### Entry Template

Each active Canonical Source Conflict entry must contain these 12 fields: ID, Decision target, Claim type, Canonical source, Conflicting source or evidence, Conflict category, Impact, Severity (`High`/`Medium`/`Low`), Blocking status (`Blocking`/`Non-blocking`), Required action, Owner, Validation evidence.

### Status Values

- **open** — Conflict acknowledged but not yet investigated
- **investigating** — Investigation underway
- **resolved** — Exactly one normative source remains; validation evidence confirms the conflict is closed

An item is removed from this active inventory once it is resolved or no longer applies to the current system; it is not retained here with a closed-out status.

### Lifecycle

Open → Investigating → Resolved, or removed from this inventory once resolved or no longer applicable to the current system.

### Resolution Rule

Canonical Source Conflict resolved only when exactly one normative source remains registered.

### Evidence-Required Rule

Evidence is required before any discrepancy is reclassified or removed; a documentation-only edit cannot close a design-vs-code conflict unless required implementation evidence exists.

### Current-Specification-Only Policy Reference

Resolved-item handling for Canonical Source Conflict follows the existing Current-Specification-Only Policy: resolved entries are removed from the active inventory, not retained with a closed-out status.

## Part 4: Configuration Drift

### Purpose

A minimal inventory of discrepancies between deployed operational values and approved operational values. Tracks configuration drift that may affect behavior without changing the approved value.

### Entry Template

Each active Configuration Drift entry must contain these 6 fields: ID, Decision target, Deployed value description, Approved operational value description, Severity, Status.

### Status Values

- **open** — Drift acknowledged but not yet investigated
- **investigating** — Investigation underway
- **resolved** — Deployed and approved values agree, or the approved value has been formally changed

An item is removed from this active inventory once it is resolved or no longer applies to the current system; it is not retained here with a closed-out status.

### Lifecycle

Open → Investigating → Resolved, or removed from this inventory once resolved or no longer applicable to the current system.

### Resolution Rule

Configuration Drift resolved only when deployed and approved values agree, or approved value is formally changed.

### Evidence-Required Rule

Evidence is required before any discrepancy is reclassified or removed.

### Current-Specification-Only Policy Reference

Resolved-item handling for Configuration Drift follows the existing Current-Specification-Only Policy: resolved entries are removed from the active inventory, not retained with a closed-out status.

## Resolution Rules

The following resolution criteria apply across all four parts of this document:

- Known Issue resolved only when implementation and design agree, or design is formally changed
- Configuration Drift resolved only when deployed and approved values agree, or approved value is formally changed
- Needs Confirmation removed only after evidence establishes intent and the canonical source is updated
- Canonical Source Conflict resolved only when exactly one normative source remains registered
- Documentation correction complete only when validation shows no stale statement remains

## Temporary Exception Process

Applies to any automated check finding classified `Warning` (not `Blocking`) in
`docs/governance_04_documentation-checks.md`'s Governance Verification Matrix
— for example, `GV-020`'s removed-name reintroduction findings. A `Warning`
finding does not block merge by itself, but leaving it neither fixed nor formally
excepted is not a complete review (see `docs/governance_04_documentation-checks.md`
`### 13. Merge Condition Validation`).

### Exception Record Fields

A temporary exception must record all three of:
- **Reason**: why the finding is not being fixed now (e.g. the flagged usage is
  intentional and pending a separate follow-up issue).
- **Owner**: who accepted the exception — a specific person, not `Team` or
  `Unassigned`.
- **Expiration Date**: the date by which the exception must be re-reviewed or the
  underlying finding fixed. An exception with no expiration date is not valid.

### Recording an Exception

Record the exception inline, next to the flagged line, as:

`<!-- exception: {rule-id} — {reason} — {owner} — expires {YYYY-MM-DD} -->`

For example: `<!-- exception: GV-020 — read_json_file mention is a historical
comparison, not a current-spec claim — @agent-lead — expires 2026-12-01 -->`

An exception past its expiration date is treated as an unexplained finding (see
`docs/governance_04_documentation-checks.md`
`### 13. Merge Condition Validation`) — not as still-covered.

## Non-Goals

Topics explicitly excluded from this document:

- Resolving individual items — resolution requires separate investigation
- Modifying source documents during extraction — this document is read-only relative to sources
- Defining new evidence labels beyond those already established
- Changing the common template itself

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Overview](../00_index.md)
- [System Overview Index](../01_overview/overview_00_document-guide.md)

## Keywords

known issues
needs confirmation
inconsistencies
template
evidence labels
resolution workflow
