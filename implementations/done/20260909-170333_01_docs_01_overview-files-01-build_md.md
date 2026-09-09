## Goal

Rewrite `docs/01_overview-files-01-build.md` to comply with `skills/DESIGN.md` Docs content policy — remove/retain — by removing ASCII directory trees and per-file descriptions, replacing them with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, and design boundaries. [REQ-001, REQ-003]

## Scope

**In scope**: Remove the ASCII directory tree (lines 27-45) and its inline per-file descriptions; replace with design-intent prose preserving existing design-intent subsections without loss of content.

**Out of scope**: Merging or deleting this file outright (File Split Rule's 400-line threshold); modifying any other file outside this one.

## Assumptions

- The two directory trees under `/opt/llm/` and `deploy/` map to distinct operational concerns (build artifacts vs deployment scripts) that should remain separate sections.
- The `Implementation Notes` subsection contains design-relevant information about deployment validation that should be preserved.
- Cross-references in other `docs/*.md` files will be updated separately if section headings change.

## Design decisions

- Keep the thematic grouping structure (LLM build artifacts vs deploy scripts) as prose section headers rather than a single flat list.
- Replace file enumeration with component-level descriptions of what each group does, owns, and depends on.
- Preserve the `Implementation Notes` subsection as-is since it describes operational constraints, not file layout.

## Alternatives considered

- Consolidating both trees into a single prose narrative: rejected because the build artifacts and deploy scripts serve fundamentally different lifecycle phases.
- Removing the entire `## 3. File Structure` section: rejected because the section title itself is misleading — the content is about deployment topology, not file listing.

## Implementation

### Target file

`docs/01_overview-files-01-build.md`

### Procedure

1. Remove the ASCII directory tree block (lines 27-45) including the ```` text` fence markers.
2. Replace the removed content with prose describing the two thematic groups:
   a. LLM build artifacts directory (`/opt/llm/llama.cpp/`, `/opt/llm/models/`) — describe what these components are responsible for, what state they own, and which direction dependencies run.
   b. Deployment scripts directory (`deploy/`) — describe what these scripts are responsible for, what state they own, and which direction dependencies run.
3. Preserve the `### Implementation Notes (Current behavior)` subsection unchanged.
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
/opt/llm/
├─ llama.cpp/                                 # llama.cpp source and build artifacts
├─ models/
│   ├─ (chat LLM)  # Refer to ...
│   └─ (embedding LLM)  # Refer to ...
```

Deployment scripts (located under the `deploy/` repository, executed with `bash deploy/xxx.sh`):

``` text
deploy/
├─ deploy.sh                                  # Copies Python scripts...
├─ build_sqlite_vec.sh                        # Downloads and builds sqlite-vec...
├─ init_db.sh                                 # Initializes SQLite schema...
├─ setup_services.sh                          # Starts MCP servers (:8004-:8014)...
└─ start_agent.sh                             # Starts AgentREPL...
```
```

With prose such as:

```markdown
### Build Artifacts

The `/opt/llm/llama.cpp/` directory holds the llama.cpp source and build artifacts. This component is responsible for providing the inference engine used by both the agent-LLM and embed-LLM processes. It owns compiled model binaries and shared libraries. Dependencies flow outward from this directory toward the LLM server processes.

The `/opt/llm/models/` directory stores chat LLM and embedding LLM model files. This component owns persistent model weights and is read-only during normal operation. Dependencies flow inward from the LLM server processes toward this directory.

### Deployment Scripts

The `deploy/` directory contains shell scripts for initial deployment and service startup. These scripts are responsible for copying configuration files, building the sqlite-vec extension, initializing the database schema, starting MCP and LLM server processes, and launching the AgentREPL. They own transient deployment state but do not manage runtime state. Dependencies flow from these scripts toward the services they configure.
```

Reference the current file layout with a single sentence: "see `scripts/shared/` for the current file layout."

## Compatibility considerations

Section heading changes may break cross-references in other `docs/*.md` files. If the rewritten section heading differs from `## 3. File Structure`, update links in:
- `01_overview-files-02-rag.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`
- `01_overview-arch-01-process.md`

## Security considerations

No security impact. The change removes implementation-detail content (file paths, script names) that could leak deployment topology information.

## Rollback considerations

Rolling back means restoring the ASCII tree blocks. Since no source code or production configuration is modified, rollback is straightforward: revert the file to its pre-modification state via git checkout.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/01_overview-files-01-build.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/01_overview-files-01-build.md` | Zero findings; structure check passes |

## Completion criteria

- No ASCII tree-drawing blocks (`├─`/`│`/`└─`) remain in the file
- No per-entry descriptions attached to tree entries remain
- Prose covers component responsibility, owned state, and allowed dependency direction for each thematic group
- Existing design-intent subsections are preserved without loss of content
- `uv run python tools/check_docs_content_policy.py` reports zero findings for this file
- `uv run python tools/check_docs_structure.py docs/01_overview-files-01-build.md` passes

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
- **Related target files**: docs/01_overview-files-01-build.md
