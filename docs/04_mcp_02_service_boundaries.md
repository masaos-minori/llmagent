---
title: "MCP Service Boundaries"
category: mcp
tags:
  - mcp
  - service-boundaries
  - responsibilities
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_01_tool_ownership_matrix.md
source:
  - scripts/shared/tool_constants.py
---

# MCP Service Boundaries

## Per-Server Responsibility Definitions

### file-read-mcp (port 8005)

**Responsibilities:**
- Read-only local file operations (read, list, search, metadata)

**Explicit Non-responsibilities:**
- File write/delete operations
- Remote repository operations
- Code analysis

**Ownership rationale:**
Provides least-privilege access for reading local files.

### file-write-mcp (port 8007)

**Responsibilities:**
- Local file write operations (write, edit, create directory, move)

**Explicit Non-responsibilities:**
- File read/delete operations
- Remote repository operations
- Code analysis

**Ownership rationale:**
Provides least-privilege access for writing local files.

### file-delete-mcp (port 8008)

**Responsibilities:**
- Local file/directory deletion

**Explicit Non-responsibilities:**
- File read/write operations
- Remote repository operations
- Code analysis

**Ownership rationale:**
Provides least-privilege access for deleting local files.

### rag-pipeline-mcp (port 8010)

**Responsibilities:**
- RAG ingestion pipeline execution
- Document indexing and retrieval
- Pipeline debugging and diagnostics

**Explicit Non-responsibilities:**
- Local file system operations
- Repository content modification
- Code analysis

**Ownership rationale:**
Isolates RAG pipeline operations to prevent accidental interference with other subsystems and ensure proper data lifecycle management.

### cicd-mcp (port 8012)

**Responsibilities:**
- GitHub Actions workflow triggering and monitoring
- CI/CD pipeline status reporting
- Workflow log retrieval

**Explicit Non-responsibilities:**
- Local file operations
- Code modification
- Repository content changes

**Ownership rationale:**
Provides focused CI/CD integration without exposing broader GitHub API capabilities that could interfere with code workflows.

### mdq-mcp (port 8013)

**Responsibilities:**
- Markdown structural search and retrieval
- Index management (creation, refresh)
- Documentation statistics

**Explicit Non-responsibilities:**
- Local file operations
- Repository operations
- Code analysis beyond markdown structure

**Ownership rationale:**
Specialized for markdown structural analysis; FTS5 search is production-ready while hybrid search remains unimplemented.

### git-mcp (port 8014)

**Responsibilities:**
- Local Git operations (status, log, diff, branch, commit, checkout)
- Git history inspection
- Pull/push operations

**Explicit Non-responsibilities:**
- Remote repository content modification
- File content analysis
- RAG operations

**Ownership rationale:**
Local Git operations require different authentication and error handling than remote GitHub operations.

### shell-mcp (port 8009)

**Responsibilities:**
- Shell command execution

**Explicit Non-responsibilities:**
- File operations
- Repository operations
- Network requests

**Ownership rationale:**
Minimal surface area for shell execution; isolated from other systems to prevent unintended side effects.

### web-search-mcp (port 8004)

**Responsibilities:**
- Web search functionality
- Browser page fetch and text extraction

**Explicit Non-responsibilities:**
- Local file operations
- Repository operations
- Code modification

**Ownership rationale:**
Consolidated from retired browser-mcp server; focuses on read-only web interaction.

### github-mcp (port 8006)

**Responsibilities:**
- GitHub repository operations (search, branches, commits, issues, PRs)
- Code content retrieval
- Branch/commit/PR creation and modification
- Dangerous operations (file deletion, PR merging)

**Explicit Non-responsibilities:**
- Local file operations
- RAG operations
- CI/CD operations

**Ownership rationale:**
Comprehensive GitHub integration requires careful separation of read/write/dangerous operations for security.

For authoritative tool-to-server and risk-tier mapping, see [MCP Tool Ownership Matrix](04_mcp_01_tool_ownership_matrix.md).

## Key Boundary Rules

### Local vs Remote Git

- `git-mcp`: Local Git operations only (no remote API calls)
- `github-mcp`: Remote GitHub API operations only (no local Git commands)

### File Operations vs RAG

- `file-*`: Direct file I/O within allowed_dirs (split into read, write, delete)
- `rag-pipeline-mcp`: Pipeline orchestration only; does not directly manipulate files outside rag_src_dir

### MDQ vs RAG

- `mdq-mcp`: Markdown structural analysis only (FTS5 search implemented, hybrid search not implemented)
- `rag-pipeline-mcp`: Full RAG pipeline including embedding generation and vector storage

## Unconfirmed Items

- [NC-004](00_governance_07_needs-confirmation-inventory.md#nc-004): Cross-server tool coordination protocol

## Related Documents

- [MCP Documentation Guide](04_mcp_00_document-guide.md)
- [MCP Tool Ownership Matrix](04_mcp_01_tool_ownership_matrix.md)

## Keywords

mcp
service-boundaries
responsibilities
capabilities
