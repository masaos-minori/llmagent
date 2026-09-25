---
title: "Documentation Metadata"
area: governance
tags:
  - governance
related:
  - ../00_index.md
  - overview_00_document-guide.md
---

# Documentation Metadata

## Purpose

This document consolidates metadata conventions for AI agents to select relevant documents, terminology glossary, link rules, and markdown syntax rules for the LLM agent design documentation set.

## Existing Metadata Fields

The following four metadata fields are required in every document's front matter:

- **title** — Document title
- **area** — Document area: one of `overview`, `deployment`, `rag`, `mcp`, `agent`, `eventbus`, `shared`, `governance`. ADR documents (`docs/adr/`) and security documents (`docs/00_security_*.md`) use `area: governance` — resolved 2026-09-14 (`NC-030`) rather than carrying their own top-level values, since both are cross-cutting governance/policy content rather than a distinct runtime area.
- **tags** — Keywords describing the document content
- **related** — Links to related documents
- **category** — Not a valid front-matter key. Do not use this field.

`keywords` is not a front-matter key. Every document instead uses a `## Keywords` body-section heading — see `tools/check_docs_structure.py`'s own check, which looks for that heading, not a front-matter key.

## Recommended Additional Fields

Two optional metadata fields beyond the four required fields in "Existing Metadata Fields":

### status

Current state of the document. Optional — defaults to `stable` when absent. A
document that would otherwise need `deprecated` or `superseded` is removed from
the active set rather than marked with a historical status.

- Allowed values: `stable` (default), `draft`
- Example:
```yaml
status: stable
```

### class

Document class (see `governance_01_documentation-policy.md`'s Document
Classification). Optional — no default; a document without this field has an
unclassified status, not an error.

- Allowed values: `Governance`, `Guide`, `Specification`, `Reference`, `Operations`, `Note`, `Known Issues`
- Example:
```yaml
class: Reference
```

## Front Matter Example

Complete Front Matter block showing the four required fields plus the one
optional field:

```yaml
---
title: Agent Reorganization
area: agent
tags: [architecture, reorganization]
related: [governance_01_documentation-policy.md]
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
| Operational Fallback | A runtime behavior that automatically switches to an alternate code path when a primary path fails or is unavailable, without requiring manual intervention. Distinct from Backward Compatibility (a static interface-preservation property): a fallback is a live, per-call runtime decision. | RAG's `call_rag_service()` falls back to in-process execution when the remote RAG service call fails (`docs/rag_03_01_query_pipeline-overview_00_document-guide.md`). |
| Default | A value substituted when a configuration key is absent or `None`, applied at load time. Distinct from Lenient Parsing: a present-but-wrong-typed value still raises rather than silently falling back to the default. | `get_typed(d, "field_name", int, "an integer", default=DEFAULT_VALUE)` (`rules/coding.md` Type-coercion policy) returns `default` only when the key is missing or `None`. |
| Lenient Parsing | Tolerating an unexpected or partially-invalid input by skipping or degrading gracefully rather than raising, when that input is not itself the primary contract being validated. | `scripts/shared/production_config_validator.py`'s best-effort tool-registry lookup is skipped (not failed) on an unexpected exception during production config validation (`# noqa: BLE001` — justified inline as best-effort). |
| Migration | A structural or schema change applied incrementally to an existing system's persisted state, without discarding existing data. | `workflow.sqlite`'s `db/schema_sql.py::apply_workflow_migrations()` applies a sequential list of (ID, SQL) pairs as incremental column additions to existing databases; a no-op for new databases (`docs/41_db/db_03_db_architecture_and_schema-migration-and-scaling.md`). |
| Obsolete | A named entity (function, class, config key) that still exists in source and remains callable, but is no longer the current production path for its original purpose — superseded by a different mechanism. | `read_json_file()` (`scripts/rag/ingestion/pipeline_utils.py`) is retained in code but no longer documented as the current production reader (`plans/done/20260903-085152_plan.md`). |
| Dead Code | A named entity that exists in source with zero current callers anywhere in the codebase — distinct from Obsolete, which may still be reachable via a legacy path. | `shared/tool_executor_helpers.py::is_side_effect()` is defined but has zero call sites in current source (confirmed by repository-wide search); `docs/mcp_03_01_dispatch-and-routing.md` accurately describes it as "deprecated (no longer used after TTL cache removal)". |

## Link Rules

When referencing other documents:

- Use relative paths from the current document's directory
- Include anchor links where applicable (e.g., `#section-name`)
- For cross-area references, use full filenames with path
- For same-area references, use just the filename without extension
- For ADR references, use the ADR number format (ADR-001) rather than the filename

### Link Format Examples

Same area: `[Agent Guide](agent_01_system-overview_00_document-guide.md)`
Cross area: `[RAG Specification](rag_01_system_overview_00_document-guide.md)`
ADR: `[ADR-001](/home/sugimoto/llmagent/docs/10_adr/ADR-001-workflow-engine-mandatory.md)`
Internal anchor: `[Section](agent_01_system-overview_00_document-guide.md#workflow-engine)`

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

Content in the "Delete or Compress" category below is removable when all three
conditions hold: it is verifiable from code, configuration, or schema alone; it
changes only when the code changes; and a wrong statement about it is caught by
execution (a test failing, a config load erroring), not by review.

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
- Correlated constraints and their rationale (e.g. why two fields must satisfy a relationship, not just that they do)
- Security-boundary defaults and why they are set that way
- The absence of a documented rationale, when that absence is itself operationally significant (e.g. "no retry policy is intentional, not an oversight")
- Operational pitfalls (a config combination that is valid but inadvisable)

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

- [Documentation Policy](/home/sugimoto/llmagent/docs/00_governance/governance_01_documentation-policy.md)
- [Issue and Uncertainty Management](/home/sugimoto/llmagent/docs/00_governance/governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](/home/sugimoto/llmagent/docs/00_governance/governance_04_documentation-checks.md)

## Keywords

metadata
terminology
glossary
link rules
markdown syntax
front matter
evidence labels
