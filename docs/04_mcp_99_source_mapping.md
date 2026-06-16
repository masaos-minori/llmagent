# MCP Documentation Source Mapping

Audit table mapping content from the 13 original source files to the 9 restructured output files.

Status: **Preserved** / **Summarized+Link** / **Merged** / **Flag(90)**

---

## Source File Inventory

| Source file | Lines | Primary content |
|---|---|---|
| `04_spec_mcp.md` | 324 | System spec, server table, startup modes, error handling, known issues |
| `04_mcp-protocol.md` | 284 | Protocol format, transport modes, watchdog, routing, new server procedure |
| `04_mcp-file.md` | 372 | file-read/write/delete + shell-mcp specs |
| `04_mcp-github.md` | 286 | github-mcp spec |
| `04_mcp-web-search.md` | 185 | web-search-mcp spec |
| `04_mcp-rag.md` | 206 | rag-pipeline-mcp spec |
| `04_mcp-sqlite.md` | 102 | sqlite-mcp spec |
| `04_mcp-cicd.md` | 162 | cicd-mcp spec |
| `04_mcp-git.md` | 159 | git-mcp spec |
| `04_mcp-mdq.md` | 202 | mdq-mcp spec |
| `04_mcp-servers.md` | 16 | Index only (links to per-server files) |
| `06_ref-mcp.md` | 453 | Protocol layer modules, tool_executor, ToolRouteResolver, McpServerHealthRegistry |
| Total | 2751 | — |

---

## 1. `04_spec_mcp.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| §1 Purpose | `04_mcp_01` | §Purpose | Preserved |
| §2 Scope | `04_mcp_01` | §Scope | Preserved |
| §3 Background | `04_mcp_01` | §Transport Mechanisms | Merged |
| §4 Prerequisites | `04_mcp_06` | §Verification Methods | Merged |
| §5 Constraints | `04_mcp_01` | §Major Constraints | Preserved |
| §6.1 Common features | `04_mcp_02` | §Common Endpoints | Preserved |
| §6.2 Server table | `04_mcp_01` | §Server Catalog | Preserved |
| §7.1 HTTP transport | `04_mcp_02` | §HTTP Transport | Preserved |
| §7.2 stdio transport | `04_mcp_02` | §stdio Transport | Preserved |
| §8.1 Tool call flow | `04_mcp_03` | §Tool Call Dispatch Flow | Preserved |
| §8.2 Routing priority | `04_mcp_03` | §ToolRouteResolver | Preserved |
| §9.1 McpServerConfig | `04_mcp_06` | §McpServerConfig Fields | Preserved |
| §9.2 Startup mode table | `04_mcp_01` | §Startup Modes | Preserved |
| §9.3 MCPServer attributes | `04_mcp_02` | §MCPServer Base Class | Preserved |
| §9.4 McpServerHealthState | `04_mcp_03` | §McpServerHealthRegistry | Preserved |
| §9.5 McpServerHealthRegistry | `04_mcp_03` | §McpServerHealthRegistry | Preserved |
| §9.6 TruncationResult | `04_mcp_02` | §Response Truncation | Merged |
| §10 Public interfaces | `04_mcp_03` | §ToolExecutor, §ToolRouteResolver | Summarized+Link |
| §11 Error handling | `04_mcp_02` | §Common Error Shape | Preserved |
| §12 Validation plan | — | (internal; not republished) | — |
| §13 Known issues | `04_mcp_90` | All entries | Preserved |

---

## 2. `04_mcp-protocol.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| §1 HTTP API table | `04_mcp_02` | §Common Endpoints | Merged |
| §2 Transport modes | `04_mcp_03` | §_ServerLifecycleRouter, startup_mode | Merged |
| §2.1 Tool definition check | `04_mcp_06` | §Verification Methods | Preserved |
| §2.2 Watchdog | `04_mcp_03` | §Watchdog | Preserved |
| §2.2.1 Audit log format | `04_mcp_02` | §Audit Log Format | Preserved |
| §2.3 Startup modes | `04_mcp_03` | §startup_mode behavior | Preserved |
| §2.4 stdio operation examples | `04_mcp_06` | §stdio Subprocess Operation | Preserved |
| §2.5 Transport class table | `04_mcp_03` | §HttpTransport, §StdioTransport | Summarized+Link |
| §2.7 tool_constants frozensets | `04_mcp_03` | §ToolRouteResolver | Summarized+Link |
| §2.8 Module utilities | `04_mcp_03` | §ToolExecutor | Merged |
| §2.9 GitHub allowlist | `04_mcp_05` | §Repository Controls | Preserved |
| §2.10 New server procedure | `04_mcp_03` | §Adding a New MCP Server | Preserved |

---

## 3. `04_mcp-file.md` (covers file-mcp + shell-mcp)

| Source section | New file | New section | Status |
|---|---|---|---|
| §1 file-mcp overview | `04_mcp_04` | §file-read-mcp / file-write-mcp / file-delete-mcp | Preserved |
| §1.2 Service files | `04_mcp_06` | §Configuration File Inventory | Summarized+Link |
| §1.5 Config items | `04_mcp_06` | §Per-server config files | Summarized+Link |
| §1.6 Implementation | `04_mcp_04` | (merged into server spec) | Merged |
| §1.7 I/O interface | `04_mcp_04` | per-server tool input/output | Preserved |
| §1.8 Error handling | `04_mcp_04` | (per-server) | Preserved |
| §1.9 Logs | `04_mcp_06` | §Per-server log files | Preserved |
| §2 shell-mcp | `04_mcp_04` | §shell-mcp | Preserved |
| §2.3 Config | `04_mcp_05` | §Command Allowlist; `04_mcp_06` §Config | Preserved |
| §2.5 I/O interface | `04_mcp_04` | §shell-mcp tool inputs/outputs | Preserved |
| §2.7 Audit log | `04_mcp_05` | §dry_run; `04_mcp_04` shell audit log | Preserved |

---

## 4. `04_mcp-github.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| §1.1 Feature overview | `04_mcp_04` | §github-mcp | Preserved |
| §1.1 Security controls | `04_mcp_05` | §Repository Controls, §Branch and Path Denylist | Preserved |
| §1.5 Config | `04_mcp_05` | §Repository Controls; `04_mcp_06` | Preserved |
| §1.7 I/O | `04_mcp_04` | §github-mcp tool inputs/outputs | Preserved |
| §1.8 Error handling | `04_mcp_04` | §Domain exceptions | Preserved |
| §1.9 Logs | `04_mcp_06` | §Per-server log files | Preserved |
| §1.10 Class API | `04_mcp_04` | §github-mcp | Summarized+Link |

---

## 5. `04_mcp-web-search.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| §1.1 Feature overview | `04_mcp_04` | §web-search-mcp | Preserved |
| §1.5 Config | `04_mcp_04` | §web-search-mcp config; `04_mcp_06` | Preserved |
| §1.7 I/O | `04_mcp_04` | §web-search-mcp tools | Preserved |
| §1.8 Error handling | `04_mcp_04` | fallback logic | Preserved |
| §1.9 Logs | `04_mcp_06` | §Per-server log files | Preserved |

---

## 6. `04_mcp-rag.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| §1 Overview | `04_mcp_04` | §rag-pipeline-mcp | Preserved |
| §3 MCP tools | `04_mcp_04` | tool definitions | Preserved |
| §4 /v1/search | `04_mcp_04` | backward compat endpoint | Preserved |
| §5 Config | `04_mcp_06` | §Per-server config files; `04_mcp_04` | Preserved |
| §6 Class API | `04_mcp_04` | §rag-pipeline-mcp | Summarized+Link |
| §7 agent.toml integration | `04_mcp_06` | §New MCP Server Addition Checklist | Merged |
| §8 Design notes | `04_mcp_04` | design note | Preserved |

---

## 7. `04_mcp-sqlite.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| §1 Overview | `04_mcp_04` | §sqlite-mcp | Preserved |
| §2 Security model | `04_mcp_05` | §Access Control by Server; `04_mcp_04` | Preserved |
| §3 Tool spec | `04_mcp_04` | §sqlite-mcp tools | Preserved |
| §4 DB schema reference | `04_mcp_04` | §Databases | Preserved |
| §5 Config | `04_mcp_06` | §Per-server config files; `04_mcp_04` | Preserved |

---

## 8. `04_mcp-cicd.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| §1 Overview | `04_mcp_04` | §cicd-mcp | Preserved |
| §2 Tools | `04_mcp_04` | tool definitions | Preserved |
| §3 Architecture | `04_mcp_04` | CiBackend Protocol note | Preserved |
| §4 Security | `04_mcp_05` | §Workflow Allowlist; §Repository Controls (cicd) | Preserved |
| §5 Config | `04_mcp_06` | §Per-server config files; `04_mcp_04` | Preserved |
| §6 Log limits | `04_mcp_04` | §cicd-mcp | Preserved |

---

## 9. `04_mcp-git.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| §1 Overview | `04_mcp_04` | §git-mcp | Preserved |
| §2 Security design | `04_mcp_05` | §Path Controls (allowed_repo_paths); §read_only | Preserved |
| §3 Tools | `04_mcp_04` | §git-mcp tools | Preserved |
| §4 Config | `04_mcp_06` | §Per-server config files; `04_mcp_04` | Preserved |
| §5 agent.toml | `04_mcp_06` | §McpServerConfig Fields example | Merged |

---

## 10. `04_mcp-mdq.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| §1.1 Feature overview | `04_mcp_04` | §mdq-mcp | Preserved |
| §1.1 Note: placeholder | `04_mcp_90` | MISSING-01 | Flag(90) |
| §1.5 Config | `04_mcp_06` | §Per-server config files; `04_mcp_04` | Preserved |
| §1.7 I/O | `04_mcp_04` | §mdq-mcp tools (current vs planned) | Preserved |
| §1.11 Class API | `04_mcp_04` | §mdq-mcp | Summarized+Link |

---

## 11. `04_mcp-servers.md`

| Source section | New file | Status |
|---|---|---|
| Index table (links) | `04_mcp_00` | §File Index | Summarized+Link |

---

## 12. `06_ref-mcp.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| Module overview table | `04_mcp_01` | §Major Components | Preserved |
| §1 mcp/models.py | `04_mcp_02` | §Pydantic Models | Preserved |
| §2 mcp/server.py | `04_mcp_02` | §MCPServer Base Class | Preserved |
| §3 shared/tool_executor.py | `04_mcp_03` | §ToolExecutor, §HttpTransport, §StdioTransport, §ToolRouteResolver | Preserved |
| §3 LifecycleProtocol | `04_mcp_03` | §_ServerLifecycleRouter | Preserved |
| §3 Cache spec | `04_mcp_03` | §Cache behavior | Preserved |
| §3 Side-effect detection | `04_mcp_03` | §Side-effect detection | Preserved |
| §4 shared/tool_constants.py | `04_mcp_03` | §ToolRouteResolver routing table | Summarized+Link |
| §5 shared/route_resolver.py | `04_mcp_03` | §ToolRouteResolver | Summarized+Link |
| §6 shared/mcp_config.py | `04_mcp_03` | §McpServerHealthRegistry | Preserved |
| §7 mcp/dispatch.py | `04_mcp_02` | §dispatch_tool Helper | Preserved |
| §9 mcp/audit.py | `04_mcp_02` | §Audit Log Format | Preserved |

---

## Coverage Summary

| Source file | Mapped | Unmapped |
|---|---|---|
| `04_spec_mcp.md` | All except §12 (internal) | §12 validation |
| `04_mcp-protocol.md` | All | — |
| `04_mcp-file.md` | All | — |
| `04_mcp-github.md` | All | — |
| `04_mcp-web-search.md` | All | — |
| `04_mcp-rag.md` | All | — |
| `04_mcp-sqlite.md` | All | — |
| `04_mcp-cicd.md` | All | — |
| `04_mcp-git.md` | All | — |
| `04_mcp-mdq.md` | All | — |
| `04_mcp-servers.md` | All (index only) | — |
| `06_ref-mcp.md` | All | — |

All significant content from the 13 source files has been mapped to one or more new files.
