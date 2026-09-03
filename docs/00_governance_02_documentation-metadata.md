---
title: "Documentation Metadata"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---

# Documentation Metadata

## Purpose

This document consolidates metadata conventions for AI agents to select relevant documents, terminology glossary, link rules, and markdown syntax rules for the LLM agent design documentation set.

## Existing Metadata Fields

The following four metadata fields are required in every document's front matter:

- **title** — Document title
- **area** — Document area: one of `overview`, `deployment`, `rag`, `mcp`, `agent`, `eventbus`, `shared`, `governance`, `adr`, `security`. The sole category-style field — `category` is not a valid front-matter key.
- **tags** — Keywords describing the document content
- **related** — Links to related documents

`keywords` is not a front-matter key. Every document instead uses a `## Keywords` body-section heading — see `tools/check_docs_structure.py`'s own check, which looks for that heading, not a front-matter key.

## Recommended Additional Fields

One optional metadata field beyond the four required fields in "Existing Metadata Fields":

### status

Current state of the document. Optional — defaults to `stable` when absent. A
document that would otherwise need `deprecated` or `superseded` is removed from
the active set rather than marked with a historical status.

- Allowed values: `stable` (default), `draft`
- Example:
```yaml
status: stable
```

## Front Matter Example

Complete Front Matter block showing the four required fields plus the one
optional field:

```yaml
---
title: Agent Reorganization
area: agent
tags: [architecture, reorganization]
related: [00_governance_01_documentation-policy.md]
status: stable
---
```

## Metadata Requirements for Active Documents

Every document in the active documentation set must carry the four required
metadata fields (title, area, tags, related). `status` is optional: when
present, it must use one of the two allowed values (`stable`, `draft`); when
absent, it defaults to `stable`.

## Non-Goals

Topics explicitly excluded from this document:

- Defining how AI agents parse or use these metadata fields
- Specifying enforcement mechanisms for metadata compliance
- Defining metadata for non-document assets (code, configuration files)

## Terminology Glossary

| Term | Preferred Form | Alternative Forms | Notes |
|------|---------------|-------------------|-------|
| Constraint | Constraint | constraint | Capitalize when referring to design constraints |
| Decision | Decision | decision | Capitalize when referring to design decision |
| Alternative | Alternative | alternative | Capitalize when referring to considered alternatives |
| Trade-off | Trade-off | tradeoff | Hyphenate as noun; "tradeoff" acceptable as single word |
| Specification | Specification | specification | Capitalize when referring to formal spec document |
| Standardization | Standardization | standardisation | Use American English spelling (z) per project convention |
| Localization | Localization | Localisation | Use American English spelling (z) per project convention |
| Authorization | Authorization | Authorisation | Use American English spelling (or) per project convention |
| Behavior | Behavior | Behaviour | Use American English spelling (or) per project convention |
| Optimize | Optimize | Optimise | Use American English spelling (ze) per project convention |
| Organize | Organize | Organise | Use American English spelling (ze) per project convention |

### Usage Rules

1. **Proper nouns**: Always capitalize CamelCase terms (EventBus, ToolRegistry, WorkflowEngine).
2. **Abbreviations**: Always use uppercase form (MQ, NC, DLQ, ACK, DTO, etc.).
3. **Bilingual text**: Use English preferred form with Japanese alternative in parentheses on first occurrence.
4. **Hyphenation**: Use hyphens for compound adjectives (at-least-once delivery, fail-closed mode).
5. **Plurals**: Plural forms are acceptable when referring to multiple items (Known Issues, Needs Confirmations).
6. **First occurrence**: On first use in a document, include both preferred and alternative forms: "Needs Confirmation (Requires Confirmation)".
7. **Subsequent occurrences**: Use only the preferred form after first definition.

### Compatibility and Lifecycle Terminology

| Term | Definition | Example |
|------|------------|---------|
| Backward Compatibility | Preserving an old public interface or API surface so existing callers continue to work unchanged after the underlying implementation changes. | `scripts/agent/__init__.py`'s module docstring: "Exports all component classes and the AgentREPL facade for backward compatibility" — old import paths through the package's `__init__.py` keep working. |
| Operational Fallback | A runtime behavior that automatically switches to an alternate code path when a primary path fails or is unavailable, without requiring manual intervention. Distinct from Backward Compatibility (a static interface-preservation property): a fallback is a live, per-call runtime decision. | RAG's `call_rag_service()` falls back to in-process execution when the remote RAG service call fails (`docs/03_rag_03_01_query_pipeline-overview.md`). |
| Default | A value substituted when a configuration key is absent or `None`, applied at load time. Distinct from Lenient Parsing: a present-but-wrong-typed value still raises rather than silently falling back to the default. | `get_typed(d, "field_name", int, "an integer", default=DEFAULT_VALUE)` (`rules/coding.md` Type-coercion policy) returns `default` only when the key is missing or `None`. |
| Lenient Parsing | Tolerating an unexpected or partially-invalid input by skipping or degrading gracefully rather than raising, when that input is not itself the primary contract being validated. | `scripts/shared/production_config_validator.py`'s best-effort tool-registry lookup is skipped (not failed) on an unexpected exception during production config validation (`# noqa: BLE001` — justified inline as best-effort). |
| Migration | A structural or schema change applied incrementally to an existing system's persisted state, without discarding existing data. | `workflow.sqlite`'s `db/schema_sql.py::apply_workflow_migrations()` applies a sequential list of (ID, SQL) pairs as incremental column additions to existing databases; a no-op for new databases (`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`). |
| Obsolete | A named entity (function, class, config key) that still exists in source and remains callable, but is no longer the current production path for its original purpose — superseded by a different mechanism. | `read_json_file()` (`scripts/rag/ingestion/pipeline_utils.py`) is retained in code but no longer documented as the current production reader (`plans/done/20260903-085152_plan.md`). |
| Dead Code | A named entity that exists in source with zero current callers anywhere in the codebase — distinct from Obsolete, which may still be reachable via a legacy path. | `shared/tool_executor_helpers.py::is_side_effect()` is defined but has zero call sites in current source (confirmed by repository-wide search); `docs/04_mcp_03_01_dispatch-and-routing.md` accurately describes it as "deprecated (no longer used after TTL cache removal)". |

## Link Rules

When referencing other documents:

- Use relative paths from the current document's directory
- Include anchor links where applicable (e.g., `#section-name`)
- For cross-area references, use full filenames with path
- For same-area references, use just the filename without extension
- For ADR references, use the ADR number format (ADR-001) rather than the filename

### Link Format Examples

Same area: `[Agent Guide](05_agent_01_system-overview.md)`
Cross area: `[RAG Specification](03_rag_01_system_overview.md)`
ADR: `[ADR-001](adr/ADR-001-workflow-engine-mandatory.md)`
Internal anchor: `[Section](05_agent_01_system-overview.md#workflow-engine)`

## Markdown Syntax Rules

### Code Blocks

- Wrap Python code with ```python
- Wrap shell commands with ```bash
- Wrap JSON with ```json

### Tables

- Use English headings for tables
- Include original (English) terminology alongside technical terms where necessary

### Keywords

- Mandatory: Must, Prohibited, Always
- Recommended: Recommended, Should, Avoid
- Optional: Optional, As needed

### Document Boundaries

- Separate sections using `##`
- Do not nest sections within sections
- Clearly separate sections with blank lines

## Guidelines for Recording Information Verifiable via Implementation Reference

Criteria for deciding whether to include implementation details in design documents.

### Information to be Deleted or Compressed Normally

- Implementation details at the file path or line number level
- Detailed module dependency structures or import hierarchies
- Default values of configuration settings (if verifiable in code)
- Enumeration of existing file structures
- Complete references to CLI arguments
- Redundant descriptions of JSON examples
- Full definitions of API schemas

### Information to be Retained

- Design intent and reasons for architectural decisions
- Boundaries and responsibilities between components
- Design decisions regarding error handling
- Design decisions regarding performance
- Design decisions regarding security
- Decisions regarding future extensibility

### Decision Categories

| Category | Condition | Example |
|----------|-----------|---------|
| Delete | Details verifiable through implementation alone | File paths, line numbers, import structures |
| Compress | Context is needed but details are not | CLI arguments → main options only |
| Replace with Source Reference | Implementation is the sole authority | Schema definition → "Refer to implementation" |
| Retain | Design decisions and intent | Error handling design decisions |
| Move to Known Issues | Discrepancy between implementation and documentation | Inconsistency between docs and code |
| Move to Needs Confirmation | Unknown matters | Unclear implementation intent |

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_01_documentation-policy.md)
- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)

## Keywords

metadata
terminology
glossary
link rules
markdown syntax
front matter
evidence labels
