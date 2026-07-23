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

### file-mcp (port 8004)

**Responsibilities:**
- Local file system operations within configured allowed directories
- File read/write/delete/create operations
- Directory listing and tree traversal
- File metadata retrieval

**Explicit Non-responsibilities:**
- Remote repository operations
- Code analysis or semantic understanding
- Cross-repository search

**Allowed operation types:**
- File I/O within allowed_dirs boundaries
- Metadata queries

**Forbidden operation types:**
- Network requests
- Remote API calls
- Operations outside allowed_dirs

**Ownership rationale:**
Centralizes all local file operations in a single server to enforce consistent access control via allowed_dirs configuration.

### rag-pipeline-mcp (port 8005)

**Responsibilities:**
- RAG ingestion pipeline execution
- Document indexing and retrieval
- Pipeline debugging and diagnostics

**Explicit Non-responsibilities:**
- Local file system operations
- Repository content modification
- Code analysis

**Allowed operation types:**
- Pipeline execution (crawl, chunk, ingest)
- Document CRUD operations
- Pipeline diagnostics

**Forbidden operation types:**
- Direct database manipulation
- File system operations outside rag_src_dir
- External network requests

**Ownership rationale:**
Isolates RAG pipeline operations to prevent accidental interference with other subsystems and ensure proper data lifecycle management.

### cicd-mcp (port 8006)

**Responsibilities:**
- GitHub Actions workflow triggering and monitoring
- CI/CD pipeline status reporting
- Workflow log retrieval

**Explicit Non-responsibilities:**
- Local file operations
- Code modification
- Repository content changes

**Allowed operation types:**
- Workflow triggering
- Status polling
- Log retrieval

**Forbidden operation types:**
- Workflow cancellation
- Workflow configuration changes
- Repository modifications

**Ownership rationale:**
Provides focused CI/CD integration without exposing broader GitHub API capabilities that could interfere with code workflows.

### mdq-mcp (port 8007)

**Responsibilities:**
- Markdown structural search and retrieval
- Index management (creation, refresh)
- Documentation statistics

**Explicit Non-responsibilities:**
- Local file operations
- Repository operations
- Code analysis beyond markdown structure

**Allowed operation types:**
- FTS5-based search
- Index path registration
- Index refresh
- Statistics queries

**Forbidden operation types:**
- Content modification
- File system operations
- Network requests

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

**Allowed operation types:**
- Git read operations
- Git write operations (add, commit, push, pull)
- Branch management

**Forbidden operation types:**
- Remote repository content changes
- Direct database operations
- File system operations outside Git context

**Ownership rationale:**
Local Git operations require different authentication and error handling than remote GitHub operations.

### shell-mcp (port 8008)

**Responsibilities:**
- Shell command execution

**Explicit Non-responsibilities:**
- File operations
- Repository operations
- Network requests

**Allowed operation types:**
- Command execution

**Forbidden operation types:**
- Interactive sessions
- Background processes
- Privilege escalation

**Ownership rationale:**
Minimal surface area for shell execution; isolated from other systems to prevent unintended side effects.

### web-search-mcp (port 8009)

**Responsibilities:**
- Web search functionality
- Browser page fetch and text extraction

**Explicit Non-responsibilities:**
- Local file operations
- Repository operations
- Code modification

**Allowed operation types:**
- Web search queries
- HTTP GET requests with rendering

**Forbidden operation types:**
- POST requests
- Authentication flows
- Local file access

**Ownership rationale:**
Consolidated from retired browser-mcp server; focuses on read-only web interaction.

### github-mcp (port 8012)

**Responsibilities:**
- GitHub repository operations (search, branches, commits, issues, PRs)
- Code content retrieval
- Branch/commit/PR creation and modification
- Dangerous operations (file deletion, PR merging)

**Explicit Non-responsibilities:**
- Local file operations
- RAG operations
- CI/CD operations

**Allowed operation types:**
- GitHub API read operations
- GitHub API write operations
- Dangerous operations (with approval)

**Forbidden operation types:**
- Local file operations
- Database manipulation
- Network requests outside GitHub API

**Ownership rationale:**
Comprehensive GitHub integration requires careful separation of read/write/dangerous operations for security.

## Key Boundary Rules

### Local vs Remote Git

- `git-mcp`: Local Git operations only (no remote API calls)
- `github-mcp`: Remote GitHub API operations only (no local Git commands)

### File Operations vs RAG

- `file-mcp`: Direct file I/O within allowed_dirs
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
