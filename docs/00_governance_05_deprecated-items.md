---
title: "Deprecated Items"
category: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---
## Purpose

This document manages references to old configuration files, concepts, and commands across the design documentation set. It prevents readers from following outdated information and ensures deprecated items are clearly distinguished from current specifications.

## Deprecated Configuration Files

Old configuration file names and their replacements:

- **config/rag_pipeline.toml**
  - Current Replacement: config/rag_pipeline_mcp_server.toml
  - Status: Confirmed
  - Notes: Each MCP server now loads its own `<key>_mcp_server.toml` per rules/coding.md MCP server addition convention
  - Evidence: scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py:99-101, scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py:130,193, implementations/done/20260722-181341_03_rag_stale_config_references.md

- **common.toml**
  - Current Replacement: config/agent.toml "Infrastructure (common)" section (lines 5-18)
  - Status: Confirmed
  - Notes: Consolidated into agent.toml which contains common, llm, http, rag, context, tools, memory, otel, security, system_prompts, tools_definitions, *_mcp_server transport sections
  - Evidence: config/agent.toml lines 1-3 (header), lines 5-18 (Infrastructure (common))

## Deprecated Concepts

Obsolete architectural concepts:

- **workflow optional mode**
  - Current Replacement: none (replacement unknown)
  - Status: Confirmed
  - Notes: WorkflowEngine is now required, not optional
  - Evidence: Confirmed by current implementation

- **shared common config**
  - Current Replacement: config/agent.toml "Infrastructure (common)" section (lines 5-18)
  - Status: Confirmed
  - Notes: Same deprecated architecture as common.toml entry below — one names the abstract concept, the other the specific file that embodied it; see common.toml entry for consolidated config details
  - Evidence: config/agent.toml lines 1-3 (header), lines 5-18 (Infrastructure (common))

## Deprecated Commands

Removed slash commands:

- **/note** — Replaced by note-taking conventions in Known Issues documents
- **/ingest** — Functionality moved to separate ingestion pipeline
- **/debug audit** — Replaced by /audit prefix command
- **/db** — Database operations handled through operational tools

## Deprecated Document References

Links to removed or superseded documents:

- **diagnostics.jsonl** — No longer written; session diagnostics stored in memory only
- **Old direct execution fallback explanations** — Removed; WorkflowEngine is now required

## How to Refer to Deprecated Items

Guidelines for referencing deprecated content:

- Always mark deprecated items with the "Deprecated" evidence label
- Include both the deprecated name and its replacement (or "none" if fully removed)
- Never remove deprecated items from this document without documenting what replaced them

## Maintenance Rule

Rules for adding/removing items:

- New deprecations must be added within one week of the change being made
- Items cannot be removed without documenting what replaced them
- "Needs confirmation" items must be reviewed quarterly

## Related Governance Documents

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [AI Reading Metadata](00_governance_06_ai-reading-metadata.md)
- [Needs Confirmation Inventory](00_governance_07_needs-confirmation-inventory.md)
- [Terminology Glossary](00_governance_09_terminology-glossary.md)
