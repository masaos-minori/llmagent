---
title: "Issue and Uncertainty Management"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---

# Issue and Uncertainty Management

## Purpose

This document defines how to track currently active discrepancies between documentation and implementation (Known Issues) and currently active unverified claims (Needs Confirmation). It ensures unconfirmed statements are trackable and actionable, preventing them from being silently accepted as facts.

## Part 1: Known Issues

### Entry Template

Each active Known Issue entry must contain these 16 fields: ID, Title, Status, Severity, Area, Type, Source, Owner, First Found, Target, Related, Summary, Current Description, Observed Implementation, Impact, Recommended Action.

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

#### NC-019

- **Source File**: `04_mcp_04_05_git.md`
- **Section**: Implementation Notes (also referenced from Write protection policy)
- **Line Number**: ~92
- **Question**: Is absence of command-specific guards distinguishing `git_checkout`/`git_pull`/`git_push` from other write tools an intentional design decision or missing security feature?
- **Evidence**: All five write tools share one common guard path (`allowed_repo_paths` + `read_only`) with no per-command validation; confirmed exploitable gap (forced checkout/push)
- **Impact**: If unintentional, leaves confirmed exploitable gap unresolved; if intentional, design intent should be documented rather than left implicit
- **Required Action**: Decision from tool owner on whether ADR-012's target guards (protected-branch, ref/remote validation, Force-Push rejection) should be implemented
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-08-21
- **Priority**: High
- **Related NC**: NC-020
- **Resolution Target**: Owner decision, then implementation per ADR-012
- **Blocking**: No — tracked in parallel with Known Issue MCP-003

#### NC-020

- **Source File**: `04_mcp_04_05_git.md`
- **Section**: Write protection policy → Audit
- **Line Number**: ~147
- **Question**: Does Git MCP audit call site's `target` field actually end up empty for every call?
- **Evidence**: Confirmed by code inspection — `req.args.get("repo", "")` uses wrong key; fixed by Row 1 changing to `repo_path` key and consuming resolved canonical path from Row 2
- **Impact**: If confirmed, Git MCP audit entries carry no repository identity, weakening audit trail for High-Severity write surface — RESOLVED
- **Required Action**: Capture actual audit log line for git-mcp call and check whether `target` is empty; fix key to `repo_path` if confirmed — COMPLETED
- **Status**: fixed
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-08-29
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next investigation of Git MCP audit logging
- **Blocking**: No
- **Resolution Notes**: Root cause was key mismatch (`"repo"` vs `"repo_path"`). Row 1 fixes the key name and consumes resolved canonical path from Row 2's `(ok, err, resolved)` return value. Audit records will now contain canonical repository identity.

#### NC-021

- **Source File**: `90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
- **Section**: 9.3 Integrity-result model (target design)
- **Line Number**: ~39
- **Question**: Is the target structured integrity-result classification (healthy / confirmed corruption / lock contention / permission / invalid format / unknown) the classification model the owner intends to implement?
- **Evidence**: `_run_integrity_check()` currently returns only pass/fail-ish result plus free-form exception string; no structured classification exists
- **Impact**: Implementing wrong classification model would require rework; leaving unconfirmed risks divergent interpretations
- **Required Action**: Owner review of the classification model defined in ADR-008 (Decision Details #14, merged from former ADR-011) before implementation begins
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-08-21
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Before implementing Known Issue SHARED-001/SHARED-002 fixes
- **Blocking**: No

No other active items beyond NC-019 through NC-021 above.

## Non-Goals

Topics explicitly excluded from this document:

- Resolving individual items — resolution requires separate investigation
- Modifying source documents during extraction — this document is read-only relative to sources
- Defining new evidence labels beyond those already established
- Changing the common template itself

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_01_documentation-policy.md)
- [Documentation Metadata](00_governance_02_documentation-metadata.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)

## Keywords

known issues
needs confirmation
inconsistencies
template
evidence labels
resolution workflow
