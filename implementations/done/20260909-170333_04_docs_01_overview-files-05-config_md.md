## Goal

Rewrite `docs/01_overview-files-05-config.md` to comply with `skills/DESIGN.md` Docs content policy — remove/retain — by removing ASCII directory trees and per-file descriptions, replacing them with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, and design boundaries. [REQ-001, REQ-003]

## Scope

**In scope**: Remove the ASCII directory tree (lines 27-47) and its inline per-file descriptions; replace with design-intent prose preserving existing design-intent subsections without loss of content.

**Out of scope**: Merging or deleting this file outright (File Split Rule's 400-line threshold); modifying any other file outside this one.

## Assumptions

- The four thematic groups (Agent config, MCP server configs, Crawler/Ingester configs, Shared configs) map to distinct operational concerns that should remain separate sections.
- The `Implementation Notes` subsection contains design-relevant information about validation and drift detection that should be preserved.
- Cross-references in other `docs/*.md` files will be updated separately if section headings change.

## Design decisions

- Keep the four thematic grouping structure as prose section headers rather than a single flat list.
- Replace file enumeration with component-level descriptions of what each group does, owns, and depends on.
- Preserve the `Implementation Notes` subsection since it describes operational constraints, not file layout.

## Alternatives considered

- Consolidating all four groups into a single prose narrative: rejected because each group serves fundamentally different lifecycle phases and has distinct failure modes.
- Removing the entire `## 3. File Structure` section: rejected because the section title itself is misleading — the content is about configuration topology, not file listing.

## Implementation

### Target file

`docs/01_overview-files-05-config.md`

### Procedure

1. Remove the ASCII directory tree block (lines 27-47) including the ```` text` fence markers.
2. Replace the removed content with prose describing the four thematic groups:
   a. Agent configuration (`config/agent.toml`) — describe what this component is responsible for, what state it owns, and which direction dependencies run.
   b. MCP server configurations (`config/<key>_mcp_server.toml`) — describe what this component is responsible for, what state it owns, and which direction dependencies run.
   c. Crawler/Ingester configurations (`config/crawler.toml`, `config/ingester.toml`) — describe what this component is responsible for, what state it owns, and which direction dependencies run.
   d. Shared configurations (`config/shared.toml`, `config/logging.toml`) — describe what this component is responsible for, what state it owns, and which direction dependencies run.
3. Preserve the `Implementation Notes` subsection unchanged.
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
Directory structure for deployment:

``` text
/opt/llm/config/
├─ agent.toml                               # AgentREPL config (LLM URLs, chunk splitter settings, prompt templates, MCP server URLs)
│   ├─ [llm]                                # LLM service endpoints...
│   │   └─ llm_url = ...                    # Agent-LLM endpoint
│   │   └─ embed_url = ...                  # Embedding-LLM endpoint
│   ├─ [rag]                                # RAG pipeline settings...
│   │   └─ chunk_splitter = ...             # Chunk splitter name
│   │   └─ chunk_size = ...                 # Chunk size in tokens
│   │   └─ overlap = ...                    # Overlap between chunks
│   ├─ [prompt]                             # Prompt templates...
│   │   └─ system_prompt = ...              # System prompt template
│   │   └─ user_prompt = ...                # User prompt template
│   ├─ [mcp_servers]                        # MCP server URLs...
│   │   └─ web_search_mcp = ...             # Web Search MCP URL
│   │   └─ file_read_mcp = ...              # File Read MCP URL
│   │   └─ github_mcp = ...                 # GitHub MCP URL
│   │   └─ file_write_mcp = ...             # File Write MCP URL
│   │   └─ file_delete_mcp = ...            # File Delete MCP URL
│   │   └─ shell_mcp = ...                  # Shell MCP URL
│   │   └─ rag_pipeline_mcp = ...           # RAG Pipeline MCP URL
│   │   └─ cicd_mcp = ...                   # CI/CD MCP URL
│   │   └─ mdq_mcp = ...                    # MDQ MCP URL
│   │   └─ git_mcp = ...                    # Git MCP URL
│   └─ [eventbus]                           # Event Bus configuration...
│       └─ eventbus_url = ...               # Event Bus URL
├─ <key>_mcp_server.toml                    # Per-MCP-server config...
├─ crawler.toml                             # Crawler config...
├─ ingester.toml                            # Ingester config...
├─ shared.toml                              # Shared config (DB paths, logging level)...
└─ logging.toml                             # Logging config...
```
```

With prose such as:

```markdown
### Agent Configuration

The `/opt/llm/config/agent.toml` file holds the AgentREPL configuration including LLM service endpoints, RAG pipeline settings, prompt templates, MCP server URLs, and Event Bus configuration. This component is responsible for coordinating the agent's behavior across all subsystems. It owns transient runtime configuration but is read-only during normal operation. Dependencies flow outward from this configuration toward the LLM services, MCP servers, and Event Bus.

### MCP Server Configurations

Each MCP server has its own configuration file under `/opt/llm/config/<key>_mcp_server.toml`. These components are responsible for configuring individual MCP server behavior independently. Each file owns its own configuration namespace and is read-only during normal operation. Dependencies flow inward from the MCP server processes toward their respective configuration files.

### Crawler/Ingester Configurations

The `/opt/llm/config/crawler.toml` and `/opt/llm/config/ingester.toml` files hold configuration for the RAG pipeline components. These components are responsible for defining crawl targets, chunking parameters, and ingestion rules. They own transient pipeline configuration and are read-only during normal operation. Dependencies flow inward from the crawler and ingester processes toward these configuration files.

### Shared Configurations

The `/opt/llm/config/shared.toml` and `/opt/llm/config/logging.toml` files provide common configuration values used across multiple processes. These components are responsible for centralizing cross-cutting concerns like database paths and logging levels. They own persistent shared configuration and are read-only during normal operation. Dependencies flow inward from all processes that require shared values toward these configuration files.
```

Reference the current file layout with a single sentence: "see `scripts/shared/` for the current file layout."

## Compatibility considerations

Section heading changes may break cross-references in other `docs/*.md` files. If the rewritten section heading differs from `## 3. File Structure`, update links in:
- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-06-misc.md`
- `01_overview-arch-01-process.md`

## Security considerations

No security impact. The change removes implementation-detail content (file paths, TOML section names, literal port numbers) that could leak internal architecture details.

## Rollback considerations

Rolling back means restoring the ASCII tree blocks. Since no source code or production configuration is modified, rollback is straightforward: revert the file to its pre-modification state via git checkout.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-files-05-config.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-files-05-config.md` | Zero findings; structure check passes |

## Completion criteria

- No ASCII tree-drawing blocks (`├─`/`│`/`└─`) remain in the file
- No per-entry descriptions attached to tree entries remain
- Prose covers component responsibility, owned state, and allowed dependency direction for each thematic group
- Existing design-intent subsections are preserved without loss of content
- `uv run python tools/check_docs_content_policy.py` reports zero findings for this file
- `uv run python tools/check_docs_structure.py docs/01_overview-files-05-config.md` passes

## Out of scope

- Modifying any other file under `docs/`
- Deciding whether to merge this file with others (deferred until after rewrite)
- Updating cross-references in other `docs/*.md` files unless section headings change

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove ASCII tree and per-file descriptions | Pending | — | — | |
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
- **Related target files**: docs/01_overview-files-05-config.md
