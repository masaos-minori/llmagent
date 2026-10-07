---
title: "Deployment Guide"
area: deployment
tags:
  - deployment
  - environment
  - setup
  - installation
  - provisioning
  - operations
  - llama-cpp
  - sqlite-vec
  - db-initialization
related:
  - overview_00_document-guide.md
  - agent_03_03_turn-processing-flow-workflow-engine.md
  - db_01_architecture_and_schema-overview-and-config.md
---

# Deployment Guide

## 1. Environment Setup

### 1.1 OS Provisioning (Gentoo Linux)

The provisioning procedure in this repository targets Gentoo Linux. The deployment scripts (`deploy/*.sh`) are plain bash and contain no distribution-specific commands, and the `conf.d/` files follow the Gentoo `/etc/conf.d/<service>` layout. (Explicit in code — `deploy/deploy.sh`, `conf.d/`)

```bash
# Required Packages
emerge --ask sys-devel/gcc sys-devel/make dev-util/cmake dev-util/ninja dev-db/sqlite dev-lang/python:3.13 dev-libs/libxml2 dev-libs/libxslt dev-vcs/git
```

> If the Python `sqlite3` module does not support loadable extensions:
> ```bash
> echo 'dev-lang/python sqlite' >> /etc/portage/package.use/python
> emerge --ask dev-lang/python
> ```

### 1.2 Python Environment Setup (using uv)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Dependency management is centralized in `pyproject.toml`/`uv.lock` (`requirements.txt` does not exist). Runtime dependencies are declared in `[project].dependencies`; development tools are declared separately in the `dev` dependency group.

The deployment scripts do not run `uv sync`. `deploy/deploy.sh` copies `pyproject.toml` and `uv.lock` into the production install root, and `deploy/deploy.sh`, `deploy/setup_services.sh` and `deploy/start_agent.sh` invoke Python through `uv run` with `UV_SYSTEM_CERTS=true`; none of them passes a flag that selects or excludes the `dev` dependency group. (Explicit in code — `deploy/deploy.sh`, `deploy/start_agent.sh`, `pyproject.toml`) The `uv sync --dev --system-certs` command in `rules/toolchain.md` is the development-checkout setup, not a production step.

### 1.3 Building llama.cpp

Illustrative commands (`<install-root>` is the production install root used by `deploy/deploy.sh`):

```bash
git clone https://github.com/ggerganov/llama.cpp.git <install-root>/llama.cpp
cd <install-root>/llama.cpp
cmake -B build -DGGML_NATIVE=ON -DLLAMA_SERVER=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)
```

### 1.4 Obtaining LLM Models

Place model files under the models directory of the production install root (the same root `deploy/deploy.sh` populates). File names must match the names used in each service configuration (e.g., `model-path`).

> **Canonical source** — This section is the canonical source for model provisioning. `docs/01_overview/overview_02_files.md` and `docs/21_rag/rag_05_01-configuration-reference.md` refer to this.

Two model roles are required: an embedding model (served as `embed-llm`) and a chat LLM (served as `agent-llm`). The embedding model must match the embedding dimension used by the RAG schema (see `scripts/db/store_protocols.py::get_embedding_dims()`). The concrete model files and quantizations are operator choices recorded in each LLM service's start configuration, not in this document.

---

## 2. Service Configuration

### 2.1 Building sqlite-vec (first time only)

SQLite vector approximate nearest neighbor (KNN: K-Nearest Neighbor) extension. Provides vector embedding storage and similarity search via the `vec0` virtual table.

```bash
bash deploy/build_sqlite_vec.sh
```

The build output path must match `sqlite_vec_so` in `config/agent.toml`.

### 2.2 Deploying scripts

`deploy/deploy.sh` performs bulk copying of scripts, config files, and SQL files.

```bash
bash deploy/deploy.sh
```

deploy.sh copies the runtime artifacts required for production operation (dependency definitions, scripts, configuration, and schemas) into the production install root and creates the necessary directory structure. For exact details, refer to the comments in `deploy/deploy.sh`.

**Workflow artifact responsibilities (deploy.sh):**
- Checks that `config/workflows/default.json` exists — aborts before any copy if missing
- Validates the workflow definition (parseable JSON, required fields/stages/retry-policy) via `python -m agent.workflow.validate`
- Copies `config/workflows/` into the production install root
- Prints workflow name, version, stage list, and SHA256 checksums (source and deployed); aborts if the checksums differ

The workflow definition is a **required workflow deployment artifact**:
source `config/workflows/default.json` → deployed to the same relative path under the production install root.
There is no disable, fallback, or workflow-optional mode.

### 2.3 Starting Services

`deploy/setup_services.sh` runs the workflow pre-flight checks and starts the Event Bus. It does not start LLM services (it only echoes their names and later queries their health endpoints) or MCP servers.

No script, unit file or configuration in this repository starts the LLM services (`embed-llm`, `agent-llm`): they must already be running before the agent starts. The start procedure is outside the repository and is tracked as DEPLOY-001 in `governance_03_issue-and-uncertainty-management.md`.

MCP servers (ports defined per server in `config/agent.toml`) auto-start as agent-managed subprocesses on agent startup.

**Workflow pre-flight responsibilities (setup_services.sh):**
- Re-checks that the deployed workflow definition (`config/workflows/default.json` under the production install root) exists and re-validates it
- Re-checks that `workflow.sqlite` exists with all required tables and a matching schema version
- The Event Bus is started **only if** all workflow checks pass — a failure here aborts before any service is spawned

```bash
bash deploy/setup_services.sh
```

After the LLM services are running, verify connectivity to the health-check endpoints for both `embed-llm` and `agent-llm`:

```bash
# Illustrative: use the hosts/ports from llm.llm_url and rag.embed_url in config/agent.toml
curl -s http://<host>:<port>/health   # embed-llm
curl -s http://<host>:<port>/health   # agent-llm

bash deploy/start_agent.sh
```

### Implementation Supplement (Startup Method)

`deploy/start_agent.sh` automatically detects whether to use the production install root or development (repository root) based on the presence of `pyproject.toml` in the production install root, and executes `python -m agent` (`scripts/agent/__main__.py`) in the corresponding root. (Explicit in code)

> API Key Configuration:
> - Web Search: DuckDuckGo — No API key required; `BRAVE_API_KEY` and `BING_API_KEY` (see `conf.d/web-search-mcp`) enable the optional providers
> - GitHub Operations: Export `GITHUB_TOKEN` in shell or source `conf.d/github-mcp` before startup
> - CI/CD: `conf.d/cicd-mcp` holds `GITHUB_TOKEN` for `cicd-mcp`
>
> `conf.d/` contains environment files only for the `cicd-mcp`, `git-mcp`, `github-mcp` and `web-search-mcp` servers; `git-mcp` defines no variables there (comments only). `deploy/deploy.sh` does not copy `conf.d/`. The MCP authentication tokens (`MCP_<SERVER_KEY>_AUTH_TOKEN`) are not part of `conf.d/`; they are set as environment variables (see Section 2.5). (Explicit in code — `conf.d/`, `deploy/deploy.sh`, `config/agent.toml`)

### 2.4 Verifying MCP Servers

MCP servers automatically start as uvicorn subprocesses according to the `startup_mode = "subprocess"` setting when the agent starts. You can check the status of each server after agent startup using `/mcp status`.

---

### 2.5 MCP Authentication Tokens

Every enabled `[mcp_servers.*]` entry in `config/agent.toml` holds an `"${ENV:VAR_NAME}"` reference as its `auth_token` rather than a literal secret. Set the corresponding `MCP_<SERVER_KEY_UPPER>_AUTH_TOKEN` environment variable (for example `MCP_SHELL_AUTH_TOKEN`, `MCP_GIT_AUTH_TOKEN`) for every server before starting the agent; an unset variable raises `ValueError` at config-load time (fail-closed). `git_mcp_server.toml` and `cicd_mcp_server.toml` use the same variable value as the corresponding `agent.toml` entry (shared secret between client and server); `web_search_mcp_server.toml`'s `browser_auth_token` is a distinct credential. Changes to authentication, MCP server definitions, or bind addresses take effect only after a full agent restart (not `/reload`). (Explicit in code — `config/agent.toml`, `scripts/shared/config_utils.py`) For setup and troubleshooting, see [`mcp_06_14_mcp-authentication-setup.md`](../22_mcp/mcp_06_14_mcp-authentication-setup.md).

---

## 3. DB Initialization

### 3.0 Platform DB Overview

The agent uses the SQLite databases listed below. Each has a path key in
`agent.toml` or falls back to `DbConfig`'s Python-level default
(`scripts/db/config.py`); see the auto-generated DB Path Reference below for which.

| DB | Default path | Config key | Purpose |
|---|---|---|---|
| `rag.sqlite` | `db` dir of install root | `rag_db_path` | RAG documents, chunks, embeddings |
| `session.sqlite` | `db` dir of install root | `session_db_path` | Agent sessions, messages |
| `workflow.sqlite` | `db` dir of install root | `workflow_db_path` | Task tracking, event processing |
| `eventbus.sqlite` | `db` dir of install root | `eventbus_db_path` | Event Bus records |

Schema details: `db_01_architecture_and_schema-overview-and-config.md`

### 3.1 Applying Schema

```bash
bash deploy/init_db.sh
```

**Responsibilities of init_db.sh:**
- Runs `db/create_schema.py` to initialize the rag, session, workflow, and eventbus databases
- Creates `workflow.sqlite` and its mandatory tables (tasks, attempts, processed_events, artifacts, approvals)
- Applies incremental schema migrations (idempotent)
- Verifies all mandatory tables exist; aborts if any are missing
- Records the schema version

### 3.2 Deployment Checklist

- [ ] `config/workflows/default.json` exists
- [ ] `deploy.sh` finished successfully (no [FATAL] errors)
- [ ] `init_db.sh` reported all mandatory tables and correct schema version
- [ ] `setup_services.sh` passed pre-flight checks

### 3.3 Failure Modes

| Symptom | Failing Script | Remediation |
|---|---|---|
| `[FATAL] Missing required workflow definition` | deploy.sh | Add `config/workflows/default.json` |
| `[FATAL] Workflow definition failed validation; aborting deployment.` | deploy.sh | Fix JSON validation error |
| `[FATAL] Deployed workflow definition checksum does not match source; deployment corrupted.` | deploy.sh | Re-run `deploy.sh`, check filesystem integrity |
| `[FATAL] Workflow database schema is missing or incomplete.` | init_db.sh / setup_services.sh | Re-run `init_db.sh` |
| `[FATAL] Workflow schema version mismatch: expected <X>, found <Y>.` | setup_services.sh | Apply migrations via `init_db.sh` |

For detailed diagnosis and recovery commands per failure mode, see [Workflow Deployment Runbook](../23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook).

For the production `require_approval` category policy (which categories require a post-execution approval gate), see [Approval Gates](../23_agent/agent_03_03_turn-processing-flow-workflow-engine.md#approval-gates).

Regarding why these deployment requirements are mandatory (design decisions for auditing, recovery, and persistence of approval state), see [ADR-001](../10_adr/ADR-001-workflow-engine-mandatory.md).

### DB Path Reference (auto-generated)

<!-- AUTO-GENERATED: generate_reference_table.py db-path-reference -->
Generated from `scripts/db/config.py` and `config/agent.toml`. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type deployment` to refresh.

| DB | Config key | Set in `agent.toml`? |
|---|---|---|
| `eventbus.sqlite` | `eventbus_db_path` | Yes |
| `rag.sqlite` | `rag_db_path` | Yes |
| `session.sqlite` | `session_db_path` | Yes |
| `workflow.sqlite` | `workflow_db_path` | No (Python-level default in `scripts/db/config.py`) |
<!-- END AUTO-GENERATED -->

## Keywords

deployment
environment
setup
installation
provisioning
operations
llama-cpp
sqlite-vec
db-initialization
