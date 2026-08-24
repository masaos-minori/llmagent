---
title: "Governance Migration Mapping.Md"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---

# Governance Document Migration Mapping

## Overview

This document maps each pre-consolidation governance document to its post-consolidation destination. Old documents MAY remain as short redirect documents during the migration period.

## Migration Table

### 1. 00_governance_01_documentation-governance.md

| Field | Value |
|-------|-------|
| Responsibility | Cross-cutting rules, policies, standards for documentation set |
| Consolidation Destination | `00_governance_12_documentation-policy.md` |
| Sections to Migrate | Document Classification, Update Rule, Review Rule, Change Impact Rule |
| Duplicate Sections to Delete | None (policy-level content moved to documentation-policy.md) |
| History to Archive | Original cross-cutting rule definitions |
| Redirect Required | Yes |
| Incoming References Count | 11+ (see Related Governance Documents section) |
| Link Update Targets | All references to this doc → `00_governance_12_documentation-policy.md` |
| Final Status | Redirect |

### 2. 00_governance_02_canonical-source-rule.md

| Field | Value |
|-------|-------|
| Responsibility | Canonical source rules for resolving conflicts between documents and between code and documents |
| Consolidation Destination | `00_governance_12_documentation-policy.md` |
| Sections to Migrate | General Rule, Conflict Resolution Rule, Code vs Document Conflict Rule, Known Issues Registration Rule |
| Duplicate Sections to Delete | None (canonical source rules merged into documentation-policy.md Decision Target Canonical Source Matrix) |
| History to Archive | Original five-category classification (Outdated code, Design deviation, Provisional implementation, Bug, Missing documentation) |
| Redirect Required | Yes |
| Incoming References Count | 5+ (referenced in multiple area guides) |
| Link Update Targets | All references to this doc → `00_governance_12_documentation-policy.md` |
| Final Status | Redirect |

### 3. 00_governance_03_evidence-labels.md

| Field | Value |
|-------|-------|
| Responsibility | Evidence labels for indicating strength of implementation grounding and confirmation status |
| Consolidation Destination | `00_governance_12_documentation-policy.md` |
| Sections to Migrate | Seven evidence label definitions (Explicit in code, Strongly implied by code, Documentation only, Needs confirmation, Deprecated, Superseded, Unknown) |
| Duplicate Sections to Delete | None (evidence labels are core policy content) |
| History to Archive | Original seven-label spectrum definitions |
| Redirect Required | Yes |
| Incoming References Count | 8+ (referenced across area specifications) |
| Link Update Targets | All references to this doc → `00_governance_12_documentation-policy.md` |
| Final Status | Redirect |

### 4. 00_governance_04_known-issues-template.md

| Field | Value |
|-------|-------|
| Responsibility | Common entry template for Known Issues / Inconsistencies documents |
| Consolidation Destination | `00_governance_14_issue-and-uncertainty-management.md` |
| Sections to Migrate | 17-field entry template, Status values, Type values, Severity values |
| Duplicate Sections to Delete | None (template definition moved to issue-and-uncertainty-management.md Part 1) |
| History to Archive | Original field-by-field descriptions |
| Redirect Required | Yes |
| Incoming References Count | 5+ (area-specific Known Issues documents reference this) |
| Link Update Targets | All references to this doc → `00_governance_14_issue-and-uncertainty-management.md` |
| Final Status | Redirect |

### 5. 00_governance_05_deprecated-items.md

| Field | Value |
|-------|-------|
| Responsibility | Management of deprecated configuration files, concepts, and commands |
| Consolidation Destination | `00_governance_14_issue-and-uncertainty-management.md` |
| Sections to Migrate | Deprecated Items lifecycle rules, naming convention for deprecated items |
| Duplicate Sections to Delete | Specific deprecated item entries (config/rag_pipeline.toml, common.toml, workflow optional mode, shared common config, /note command) |
| History to Archive | Specific deprecated item entries with their evidence references |
| Redirect Required | Yes |
| Incoming References Count | 3+ (referenced in coding.md and other governance docs) |
| Link Update Targets | All references to this doc → `00_governance_14_issue-and-uncertainty-management.md` |
| Final Status | Redirect |

### 6. 00_governance_06_ai-reading-metadata.md

| Field | Value |
|-------|-------|
| Responsibility | Metadata conventions for AI agents to select relevant documents |
| Consolidation Destination | `00_governance_13_documentation-metadata.md` |
| Sections to Migrate | Five existing metadata fields, eight recommended additional fields, metadata usage rules |
| Duplicate Sections to Delete | None (metadata conventions directly mapped to documentation-metadata.md) |
| History to Archive | Original field-by-field descriptions for scope, audience, status, priority, etc. |
| Redirect Required | Yes |
| Incoming References Count | 4+ (referenced in index documents) |
| Link Update Targets | All references to this doc → `00_governance_13_documentation-metadata.md` |
| Final Status | Redirect |

### 7. 00_governance_07_needs-confirmation-inventory.md

| Field | Value |
|-------|-------|
| Responsibility | Centralized inventory of "Needs confirmation" items across the documentation set |
| Consolidation Destination | `00_governance_14_issue-and-uncertainty-management.md` |
| Sections to Migrate | Entry field definitions (15 fields), Status values, Priority values, Extraction Process |
| Duplicate Sections to Delete | Specific NC item entries (NC-001 through NC-018 compressed into table format) |
| History to Archive | Individual NC entries with their source file references and line numbers |
| Redirect Required | Yes |
| Incoming References Count | 6+ (referenced in area specifications) |
| Link Update Targets | All references to this doc → `00_governance_14_issue-and-uncertainty-management.md` |
| Final Status | Redirect |

### 8. 00_governance_08_known-issues-migration-plan.md

| Field | Value |
|-------|-------|
| Responsibility | Migration plan for transitioning area-specific Known Issues documents to common template |
| Consolidation Destination | `00_governance_14_issue-and-uncertainty-management.md` |
| Sections to Migrate | Migration priority criteria, suggested order of migration |
| Duplicate Sections to Delete | Current Format Summary for each area (RAG, MCP, Agent, EventBus, Shared/DB) — superseded by actual migration execution |
| History to Archive | Baseline format records for each area's Known Issues document |
| Redirect Required | No (this is a planning document; its purpose is fulfilled upon migration completion) |
| Incoming References Count | 2+ |
| Link Update Targets | N/A if no redirect needed |
| Final Status | Archive or Remove after migration |

### 9. 00_governance_09_terminology-glossary.md

| Field | Value |
|-------|-------|
| Responsibility | Project-specific terminology glossary and usage rules |
| Consolidation Destination | `00_governance_13_documentation-metadata.md` |
| Sections to Migrate | Term table entries, Usage Rules (proper nouns, abbreviations, bilingual text, hyphenation, plurals, first occurrence, subsequent occurrences) |
| Duplicate Sections to Delete | None (glossary is core metadata content) |
| History to Archive | Original term entries and their alternative forms |
| Redirect Required | Yes |
| Incoming References Count | 3+ |
| Link Update Targets | All references to this doc → `00_governance_13_documentation-metadata.md` |
| Final Status | Redirect |

### 10. 00_governance_10_governance-framework.md

| Field | Value |
|-------|-------|
| Responsibility | Governance framework including canonical-source precedence and area canonical maps |
| Consolidation Destination | `00_governance_12_documentation-policy.md` |
| Sections to Migrate | Canonical-Source Precedence table, Area Canonical Maps concept |
| Duplicate Sections to Delete | Specific area canonical map entries (Overview, Deployment, RAG, MCP, Agent, EventBus, Shared/DB) — replaced by Decision Target Canonical Source Matrix |
| History to Archive | Original area-by-area canonical document listings |
| Redirect Required | Yes |
| Incoming References Count | 4+ |
| Link Update Targets | All references to this doc → `00_governance_12_documentation-policy.md` |
| Final Status | Redirect |

### 11. 00_governance_11_adr-index.md

| Field | Value |
|-------|-------|
| Responsibility | ADR Index listing all Architecture Decision Records |
| Consolidation Destination | `00_governance_12_documentation-policy.md` |
| Sections to Migrate | ADR indexing methodology, ADR ID format rules |
| Duplicate Sections to Delete | Specific ADR entries (ADR-001 through ADR-013) — these should be maintained as a separate ADR Index document, not embedded in policy |
| History to Archive | Original ADR list with dates and statuses |
| Redirect Required | Partial (methodology goes to policy, specific entries need separate maintenance) |
| Incoming References Count | 5+ |
| Link Update Targets | Policy references → `00_governance_12_documentation-policy.md`; ADR entries → maintain as separate ADR Index document |
| Final Status | Redirect + Separate ADR Index Document |

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_12_documentation-policy.md)
- [Canonical Source Matrix](canonical-source-matrix.md)

## Keywords

migration
governance
document mapping
redirect
