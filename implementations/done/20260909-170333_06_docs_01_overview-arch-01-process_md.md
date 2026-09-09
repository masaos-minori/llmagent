## Goal

Rewrite `docs/01_overview-arch-01-process.md` to comply with `skills/DESIGN.md` Docs content policy — remove/retain — by removing ASCII directory trees and per-file descriptions, replacing them with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, and design boundaries. [REQ-001, REQ-003]

## Scope

**In scope**: Remove the ASCII process topology diagram (lines 36-48) and its inline per-line descriptions; replace with design-intent prose preserving existing design-intent subsections without loss of content.

**Out of scope**: Merging or deleting this file outright (File Split Rule's 400-line threshold); modifying any other file outside this one.

## Assumptions

- The process topology maps to distinct operational concerns (AgentREPL vs LLM services vs MCP servers) that should remain separate sections.
- The `Configuration File Isolation Policy` subsection contains design-relevant information about process independence that should be preserved.
- Cross-references in other `docs/*.md` files will be updated separately if section headings change.

## Design decisions

- Keep the three-tier process topology structure (AgentREPL → LLM services → MCP servers) as prose section headers rather than a single flat list.
- Replace ASCII diagram with prose describing what each tier is responsible for, what state it owns, and which direction dependencies run.
- Preserve the `Configuration File Isolation Policy` subsection since it describes operational constraints, not file layout.

## Alternatives considered

- Consolidating all three tiers into a single prose narrative: rejected because each tier serves fundamentally different lifecycle phases and has distinct failure modes.
- Removing the entire `## 2. Architecture` section: rejected because the section title itself is misleading — the content is about process topology, not file listing.

## Implementation

### Target file

`docs/01_overview-arch-01-process.md`

### Procedure

1. Remove the ASCII process topology diagram block (lines 36-48) including the ```` text` fence markers.
2. Replace the removed content with prose describing the three thematic groups:
   a. AgentREPL process — describe what this component is responsible for, what state it owns, and which direction dependencies run.
   b. LLM service processes — describe what this component is responsible for, what state it owns, and which direction dependencies run.
   c. MCP server group — describe what this component is responsible for, what state it owns, and which direction dependencies run.
3. Preserve the `Configuration File Isolation Policy` subsection unchanged.
4. Ensure Front Matter (title, area, tags, related, etc.) remains intact.

### Method

Apply `skills/python-design/SKILL.md` narrow usage: draw only the few relevant bullets from its broader 12-section template for the Design-decisions-family fields. For each thematic group, write a short paragraph covering:
- Component responsibility: what the group of components is responsible for
- State owned: what data or runtime state belongs to this group
- Allowed dependency direction: which direction dependencies run (reference `rules/env.md` Architecture's layer diagram, do not restate it)
- Reason for process separation: why this concern runs as its own process rather than in-process

### Details

Replace the current structure:

```
### 2.1 Process Configuration

``` text
User
    │ Interaction input (agent[chat]> / agent[code]> Prompt)
    ▼
┌──────────────────────────────────────────────────────┐
│  agent.py (CLI REPL Tool)                           │
│  Input → RAG Search → LLM Call → MCP Tool Exec → Response  │
└───────┬─────────────┬──────────────────┬─────────────┘
        │             │                  │
        ▼             ▼                  ▼
:8081 embed-LLM  :8080 agent-LLM   MCP Server Group (http)
(During RAG search)                 (Count/Ports refer to `[mcp_servers.*]` in `config/agent.toml`)
```

#### Implementation Notes

...
```

With prose such as:

```markdown
### 2.1 Process Topology

The User initiates interaction through the AgentREPL CLI tool, which handles input routing, RAG search, LLM calls, and MCP tool execution before returning a response. This component is responsible for orchestrating the end-to-end user session. It owns transient session state and prompt rendering logic. Dependencies flow outward from the AgentREPL toward both LLM services and MCP servers.

The LLM service tier consists of two processes: the agent-LLM (:8080) providing chat/code generation capabilities, and the embed-LLM (:8081) providing text-to-vector conversion for RAG operations. These components are responsible for inference and embedding computation. They own model weights and inference state. Dependencies flow inward from the AgentREPL toward these LLM services.

The MCP server group provides specialized tool execution capabilities via HTTP transport. This tier is responsible for isolating individual tool domains (web search, file I/O, git operations, CI/CD, etc.) into independent processes. Each MCP server owns its own tool registry and execution context. Dependencies flow inward from the AgentREPL toward the MCP server group.
```

Reference the current file layout with a single sentence: "see `scripts/shared/` for the current file layout."

## Compatibility considerations

Section heading changes may break cross-references in other `docs/*.md` files. If the rewritten section heading differs from `## 2. Architecture`, update links in:
- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`

## Security considerations

No security impact. The change removes implementation-detail content (port numbers, process names) that could leak internal architecture details.

## Rollback considerations

Rolling back means restoring the ASCII diagram. Since no source code or production configuration is modified, rollback is straightforward: revert the file to its pre-modification state via git checkout.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-arch-01-process.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-arch-01-process.md` | Zero findings; structure check passes |

## Completion criteria

- No ASCII tree-drawing blocks (`├─`/`│`/`└─`) remain in the file
- No per-entry descriptions attached to tree entries remain
- Prose covers component responsibility, owned state, and allowed dependency direction for each thematic group
- Existing design-intent subsections are preserved without loss of content
- `uv run python tools/check_docs_content_policy.py` reports zero findings for this file
- `uv run python tools/check_docs_structure.py docs/01_overview-arch-01-process.md` passes

## Out of scope

- Modifying any other file under `docs/`
- Deciding whether to merge this file with others (deferred until after rewrite)
- Updating cross-references in other `docs/*.md` files unless section headings change

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove ASCII diagram and per-line descriptions | Pending | — | — | |
| 2 | Write design-intent prose for each thematic group | Pending | — | — | |
| 3 | Preserve existing design-intent subsections | Pending | — | — | |
| 4 | Validate with checkers | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260905-153715_dcp002_overview_file_structure_docs_redesign.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-210427_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-170333
- **Related target files**: docs/01_overview-arch-01-process.md
