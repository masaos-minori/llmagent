## Goal

Rewrite `docs/01_overview-files-04-shared.md` to comply with `skills/DESIGN.md` Docs content policy — remove/retain — by removing ASCII directory trees and per-file descriptions, replacing them with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, and design boundaries. [REQ-001, REQ-002, REQ-003]

## Scope

**In scope**: Remove the ASCII directory tree (lines 21-46) and its inline per-file descriptions (lines 66-124); replace with design-intent prose preserving the existing `### Design Intent and Operational Specifications` subsection without loss of content.

**Out of scope**: Merging or deleting this file outright (File Split Rule's 400-line threshold); modifying any other file outside this one.

## Assumptions

- The four thematic groups (DB layer, LLM Client/Transport, Tool Routing/Execution, Configuration) map to distinct operational concerns that should remain separate sections.
- The `Design Intent and Operational Specifications` subsection contains design-relevant information about caching and drift validation that should be preserved.
- Cross-references in other `docs/*.md` files will be updated separately if section headings change.

## Design decisions

- Keep the four thematic grouping structure (DB layer, LLM Client/Transport, Tool Routing/Execution, Configuration) as prose section headers rather than a single flat list.
- Replace file enumeration with component-level descriptions of what each group does, owns, and depends on.
- Preserve the `Design Intent and Operational Specifications` subsection as-is since it describes operational constraints, not file layout.

## Alternatives considered

- Consolidating all four groups into a single prose narrative: rejected because each group serves fundamentally different lifecycle phases and has distinct failure modes.
- Removing the entire `## 3. File Structure` section: rejected because the section title itself is misleading — the content is about shared infrastructure topology, not file listing.

## Implementation

### Target file

`docs/01_overview-files-04-shared.md`

### Procedure

1. Remove the first ASCII directory tree block (lines 21-46) including the ```` text` fence markers.
2. Remove the second ASCII tree / per-file description block (lines 66-124) including the `## 3b. File Structure` heading.
3. Replace the removed content with prose describing the four thematic groups:
   a. DB layer package (`scripts/db/`) — describe what this component is responsible for, what state it owns, and which direction dependencies run.
   b. LLM Client/Transport group — describe what this component is responsible for, what state it owns, and which direction dependencies run.
   c. Tool Routing/Execution group — describe what this component is responsible for, what state it owns, and which direction dependencies run.
   d. Configuration group — describe what this component is responsible for, what state it owns, and which direction dependencies run.
4. Preserve the `### Design Intent and Operational Specifications` subsection unchanged.
5. Ensure Front Matter (title, area, tags, related, etc.) remains intact.

### Method

Apply `skills/python-design/SKILL.md` narrow usage: draw only the few relevant bullets from its broader 12-section template for the Design-decisions-family fields. For each thematic group, write a short paragraph covering:
- Component responsibility: what the group of components is responsible for
- State owned: what data or runtime state belongs to this group
- Allowed dependency direction: which direction dependencies run (reference `rules/env.md` Architecture's layer diagram, do not restate it)
- Reason for process separation: why this concern runs as its own process rather than in-process

### Details

Replace the current structure:

```
## 3. File Structure

Directory structure at deployment target:

``` text
/opt/llm/
├─ venv/                              # Python virtual environment
│   └─ uv.lock                        # Python dependency list (uv managed)
├─ db/
│   ├─ rag.sqlite                     # RAG vector DB...
│   ├─ session.sqlite                 # Agent sessions + messages...
│   ├─ workflow.sqlite                # Task tracking + event processing...
│   └─ eventbus.sqlite                # Event Bus event/offset/delivery/DLQ state...
├─ scripts/
│   ├─ db/                                  # DB layer package...
│   │   ├─ __init__.py                      # Module initialization
│   │   ├─ create_schema.py                 # SQLite schema initialization
│   │   ...
│   └─ protocols/
│       ├─ protocols/__init__.py            # Protocol package initialization
│       └─ protocols/shell.py               # ShellPolicy protocol
```

## Related Documents

...

## Keywords

shared
db
sqlite
file-structure

# File Structure

Architecture Overview → ...

## 3b. File Structure

Treating `scripts/shared/` as the source of truth. Below is a loosely grouped list of files by theme.

**LLM Client/Transport**
- `llm_client.py` — LLMClient: SSE streaming & exponential backoff retry
- `llm_types.py` — LLMUsage / LLMResponse dataclasses
...
**Tool Routing/Execution**
- `tool_executor.py` — ToolExecutor: MCP server routing
...
**Configuration**
- `config_loader.py` — Common TOML/JSON configuration loader
...
**Other Utilities**
- `types.py` — Common type definitions
...
**`protocols/`**
- `protocols/__init__.py` — Protocol package initialization
- `protocols/shell.py` — ShellPolicy protocol
```

With prose such as:

```markdown
### DB Layer Package

The `/opt/llm/db/` directory holds four SQLite databases (rag.sqlite, session.sqlite, workflow.sqlite, eventbus.sqlite), each operating in WAL mode and isolated by domain. This component is responsible for persistent storage across the system. It owns database files and their WAL/shm sidecar files. Dependencies flow outward from these databases toward the store implementations in `scripts/db/`.

The `scripts/db/` package provides the abstraction layer over these databases. This component is responsible for schema management, connection pooling, and query execution. It owns the store protocols and implementations. Dependencies flow inward from higher layers toward this package.

### LLM Client/Transport Group

The LLM client/transport group under `scripts/shared/` is responsible for connecting to external LLM services via HTTP/SSE transport. This component owns streaming connections, retry logic, and error handling for LLM communication. It manages transient connection state but does not persist LLM responses. Dependencies flow outward from this group toward the LLM service endpoints.

### Tool Routing/Execution Group

The tool routing/execution group under `scripts/shared/` is responsible for dispatching tool calls to the appropriate MCP server. This component owns the tool registry, route resolution, and execution lifecycle. It manages in-memory tool metadata and routing state. Dependencies flow inward from agent processes toward this group, and outward toward MCP servers.

### Configuration Group

The configuration group under `scripts/shared/` is responsible for loading, validating, and providing typed access to configuration values from TOML/JSON sources. This component owns configuration dataclasses and validators. It reads configuration at startup and does not modify it during runtime. Dependencies flow inward from all processes that require configuration.
```

Reference the current file layout with a single sentence: "see `scripts/shared/` for the current file layout."

## Compatibility considerations

Section heading changes may break cross-references in other `docs/*.md` files. If the rewritten section heading differs from `## 3. File Structure`, update links in:
- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`
- `01_overview-arch-01-process.md`

## Security considerations

No security impact. The change removes implementation-detail content (file paths, class names, module names) that could leak internal architecture details.

## Rollback considerations

Rolling back means restoring both ASCII tree blocks and the per-file description section. Since no source code or production configuration is modified, rollback is straightforward: revert the file to its pre-modification state via git checkout.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-files-04-shared.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-files-04-shared.md` | Zero findings; structure check passes |

## Completion criteria

- No ASCII tree-drawing blocks (`├─`/`│`/`└─`) remain in the file
- No per-entry descriptions attached to tree entries remain
- Prose covers component responsibility, owned state, and allowed dependency direction for each thematic group
- Existing design-intent subsections are preserved without loss of content
- `uv run python tools/check_docs_content_policy.py` reports zero findings for this file
- `uv run python tools/check_docs_structure.py docs/01_overview-files-04-shared.md` passes

## Out of scope

- Modifying any other file under `docs/`
- Deciding whether to merge this file with others (deferred until after rewrite)
- Updating cross-references in other `docs/*.md` files unless section headings change

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove ASCII trees and per-file descriptions | Pending | — | — | |
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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260905-153715_dcp002_overview_file_structure_docs_redesign.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-210427_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-170333
- **Related target files**: docs/01_overview-files-04-shared.md
