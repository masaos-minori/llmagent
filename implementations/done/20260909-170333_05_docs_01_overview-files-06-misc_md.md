## Goal

Rewrite `docs/01_overview-files-06-misc.md` to comply with `skills/DESIGN.md` Docs content policy — remove/retain — by removing ASCII directory trees and per-file descriptions, replacing them with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, and design boundaries. [REQ-001, REQ-003]

## Scope

**In scope**: Remove the ASCII directory trees (lines 26-45 and 52-58) and their inline per-file descriptions; replace with design-intent prose preserving existing design-intent subsections without loss of content.

**Out of scope**: Merging or deleting this file outright (File Split Rule's 400-line threshold); modifying any other file outside this one.

## Assumptions

- The two thematic groups (AgentREPL scripts vs AgentREPL config) map to distinct operational concerns that should remain separate sections.
- The `Implementation Notes` subsection contains design-relevant information about startup orchestration that should be preserved.
- Cross-references in other `docs/*.md` files will be updated separately if section headings change.

## Design decisions

- Keep the two thematic grouping structure as prose section headers rather than a single flat list.
- Replace file enumeration with component-level descriptions of what each group does, owns, and depends on.
- Preserve the `Implementation Notes` subsection since it describes operational constraints, not file layout.

## Alternatives considered

- Consolidating both groups into a single prose narrative: rejected because the scripts and config serve fundamentally different lifecycle phases.
- Removing the entire `## 3. File Structure` section: rejected because the section title itself is misleading — the content is about agent deployment topology, not file listing.

## Implementation

### Target file

`docs/01_overview-files-06-misc.md`

### Procedure

1. Remove the first ASCII directory tree block (lines 26-45) including the ```` text` fence markers.
2. Remove the second ASCII tree block (lines 52-58) including the ```` text` fence markers.
3. Replace the removed content with prose describing the two thematic groups:
   a. AgentREPL scripts directory (`scripts/agent/`) — describe what this component is responsible for, what state it owns, and which direction dependencies run.
   b. AgentREPL config directory (`config/agent.toml`) — describe what this component is responsible for, what state it owns, and which direction dependencies run.
4. Preserve the `Implementation Notes` subsection unchanged.
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
Directory structure for deployment:

``` text
/opt/llm/
├─ venv/                              # Python virtual environment
│   └─ uv.lock                        # Python dependency list (uv managed)
├─ scripts/
│   ├─ agent/                         # AgentREPL scripts...
│   │   ├─ __main__.py                # Entry point for running the agent REPL
│   │   ├─ repl.py                    # AgentREPL class definition
│   │   ├─ startup.py                 # StartupOrchestrator class
│   │   └─ prompts/                   # Prompt templates
│   │       ├─ system_prompt.txt      # System prompt template
│   │       └─ user_prompt.txt        # User prompt template
│   └─ shared/
│       ├─ config_loader.py           # Common TOML/JSON configuration loader
│       └─ ...
├─ config/
│   └─ agent.toml                     # AgentREPL config (LLM URLs, chunk splitter settings, prompt templates, MCP server URLs)
```

## Related Documents

...

## Keywords

agent-repl
file-structure
deployment

# File Structure

Architecture Overview → ...

## 3b. File Structure

Treating `scripts/shared/` as the source of truth. Below is a loosely grouped list of files by theme.

**AgentREPL Config**
- `agent.toml` — AgentREPL configuration (LLM URLs, chunk splitter settings, prompt templates, MCP server URLs)...
```

With prose such as:

```markdown
### AgentREPL Scripts

The `/opt/llm/scripts/agent/` directory holds the AgentREPL entry point, REPL class, startup orchestrator, and prompt templates. This component is responsible for managing the interactive agent session lifecycle. It owns transient session state and prompt rendering logic. Dependencies flow outward from these scripts toward the LLM services, MCP servers, and Event Bus.

### AgentREPL Configuration

The `/opt/llm/config/agent.toml` file holds the AgentREPL configuration including LLM service endpoints, RAG pipeline settings, prompt templates, MCP server URLs, and Event Bus configuration. This component is responsible for coordinating the agent's behavior across all subsystems. It owns transient runtime configuration but is read-only during normal operation. Dependencies flow outward from this configuration toward the LLM services, MCP servers, and Event Bus.
```

Reference the current file layout with a single sentence: "see `scripts/shared/` for the current file layout."

## Compatibility considerations

Section heading changes may break cross-references in other `docs/*.md` files. If the rewritten section heading differs from `## 3. File Structure`, update links in:
- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`
- `01_overview-arch-01-process.md`

## Security considerations

No security impact. The change removes implementation-detail content (file paths, module names, script names) that could leak internal architecture details.

## Rollback considerations

Rolling back means restoring both ASCII tree blocks. Since no source code or production configuration is modified, rollback is straightforward: revert the file to its pre-modification state via git checkout.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-files-06-misc.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-files-06-misc.md` | Zero findings; structure check passes |

## Completion criteria

- No ASCII tree-drawing blocks (`├─`/`│`/`└─`) remain in the file
- No per-entry descriptions attached to tree entries remain
- Prose covers component responsibility, owned state, and allowed dependency direction for each thematic group
- Existing design-intent subsections are preserved without loss of content
- `uv run python tools/check_docs_content_policy.py` reports zero findings for this file
- `uv run python tools/check_docs_structure.py docs/01_overview-files-06-misc.md` passes

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260905-153715_dcp002_overview_file_structure_docs_redesign.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-210427_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-170333
- **Related target files**: docs/01_overview-files-06-misc.md
