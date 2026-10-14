---
title: "Deployment Guide"
area: deployment
class: Reference
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
  - overview_02_files.md
  - rag_05_01-configuration-reference.md
  - governance_03_issue-and-uncertainty-management.md
  - mcp_06_14_mcp-authentication-setup.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - adr_02_001_workflow-engine-mandatory.md
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

The deployment scripts do not run `uv sync`. `deploy/deploy.sh` copies `pyproject.toml` and `uv.lock` into the production install root, and `deploy/deploy.sh`, `deploy/setup_services.sh`, `deploy/init_db.sh` and `deploy/start_agent.sh` invoke their Python helper steps (workflow-definition validation, schema creation and version checks, configuration reads) through `uv run` with `UV_SYSTEM_CERTS=true`; each of them passes `--frozen --no-dev` (through `UV_PROD_FLAGS`), so the production environment never installs the `dev` dependency group and never rewrites the lockfile. The agent and the MCP servers themselves are not started through `uv run`; they run as compiled binaries (see section 2.6). (Explicit in code — `deploy/deploy.sh`, `deploy/start_agent.sh`, `pyproject.toml`) The `uv sync --dev --system-certs` command in `rules/toolchain.md` is the development-checkout setup, not a production step.

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

### 2.2a Starting the LLM Services

The two LLM services are `llama-server` processes built in section 1.3. No script in this repository starts them; the operator runs them as system services before running `deploy/setup_services.sh`, which waits until both `/health` endpoints answer. The services may run on a different host from the agent; their addresses are set by the operator in the configuration files below.

| Service | Role | Address must match |
|---|---|---|
| `embed-llm` | Embedding model (section 1.4) | `embed_url` in `config/agent.toml`, `config/ingester.toml`, `config/rag_pipeline_mcp_server.toml` |
| `agent-llm` | Chat model (section 1.4) | `llm_url` in `config/agent.toml`, `config/rag_pipeline_mcp_server.toml` |

Illustrative commands (`<install-root>`, model file names, addresses, ports and thread counts are operator choices):

```bash
# embed-llm
<install-root>/llama.cpp/build/bin/llama-server \
  --model <install-root>/models/<embedding-model>.gguf \
  --embedding --host <bind_address> --port <embed_port> --threads <n>

# agent-llm
<install-root>/llama.cpp/build/bin/llama-server \
  --model <install-root>/models/<chat-model>.gguf \
  --host <bind_address> --port <llm_port> --ctx-size <n_ctx> --threads <n>
```

To run them as OpenRC services (Gentoo, section 1.1), create one init script per service. Example for `embed-llm`:

```sh
#!/sbin/openrc-run
# /etc/init.d/embed-llm
command="<install-root>/llama.cpp/build/bin/llama-server"
command_args="${EMBED_LLM_ARGS}"
command_user="llm:llm"
command_background=true
pidfile="/run/${RC_SVCNAME}.pid"
output_log="/var/log/${RC_SVCNAME}.log"
error_log="/var/log/${RC_SVCNAME}.log"
```

Put the arguments in `/etc/conf.d/embed-llm` (`EMBED_LLM_ARGS="--model ... --embedding --host <bind_address> --port <embed_port>"`), then:

```bash
rc-update add embed-llm default
rc-service embed-llm start
```

Create `agent-llm` the same way. Verify both with the `curl` commands in section 2.3 before starting the agent.

### 2.3 Starting Services

`deploy/setup_services.sh` runs the workflow pre-flight checks and starts the Event Bus. It does not start LLM services — it validates their remote `/health` endpoints (read from `config/agent.toml`) and blocks until both are healthy before proceeding, rather than spawning them — or MCP servers. Start the LLM services first (section 2.2a).

MCP servers (ports defined per server in `config/agent.toml`) auto-start as agent-managed subprocesses on agent startup.

**Workflow pre-flight responsibilities (setup_services.sh):**
- Re-checks that the deployed workflow definition (`config/workflows/default.json` under the production install root) exists and re-validates it
- Re-checks that `workflow.sqlite` exists with all required tables and a matching schema version
- The Event Bus is started **only if** all workflow checks pass — a failure here aborts before any service is spawned

```bash
bash deploy/setup_services.sh
```

Once the LLM services are running, `setup_services.sh` validates their health automatically at deploy time; you can also verify connectivity manually for both `embed-llm` and `agent-llm`:

```bash
# Illustrative: use the base URLs from embed_url and llm_url in config/agent.toml
curl -s http://<embed_base>/health   # embed-llm
curl -s http://<llm_base>/health     # agent-llm

bash deploy/start_agent.sh
```

### Implementation Supplement (Startup Method)

`deploy/start_agent.sh` automatically detects whether to use the production install root or development (repository root) based on the presence of `pyproject.toml` in the production install root. That root selects only the `PYTHONPATH`, the `.env` lookup and the `pyproject.toml` check; the script then always launches the compiled `/opt/llm/bin/agent` binary (built by `deploy/build_binaries.sh`) and requires the deployed `/opt/llm/scripts`, `/opt/llm/config` and `/opt/llm/db` files, so a repository checkout alone cannot start the agent. (Explicit in code — `deploy/start_agent.sh`)

> API Key Configuration:
> - Web Search: DuckDuckGo — No API key required. DuckDuckGo is the only search provider the server implements; `BRAVE_API_KEY` and `BING_API_KEY` in `conf.d/web-search-mcp` are not referenced by any code under `scripts/`
> - GitHub Operations: Export `GITHUB_TOKEN` in shell or source `conf.d/github-mcp` before startup
> - CI/CD: `conf.d/cicd-mcp` holds `GITHUB_TOKEN` for `cicd-mcp`
>
> `conf.d/` contains environment files only for the `cicd-mcp`, `git-mcp`, `github-mcp` and `web-search-mcp` servers; `git-mcp` defines no variables there (comments only). `deploy/deploy.sh` does not copy `conf.d/`. The MCP authentication tokens (`MCP_<SERVER_KEY>_AUTH_TOKEN`) are not part of `conf.d/`; they are set as environment variables (see Section 2.5). (Explicit in code — `conf.d/`, `deploy/deploy.sh`, `config/agent.toml`)

### 2.4 Verifying MCP Servers

MCP servers automatically start as uvicorn subprocesses according to the `startup_mode = "subprocess"` setting when the agent starts. You can check the status of each server after agent startup using `/mcp status`.

---

### 2.5 MCP Authentication Tokens

Every enabled `[mcp_servers.*]` entry in `config/agent.toml` holds an `"${ENV:VAR_NAME}"` reference as its `auth_token` rather than a literal secret. Set the corresponding `MCP_<SERVER_KEY_UPPER>_AUTH_TOKEN` environment variable (for example `MCP_SHELL_AUTH_TOKEN`, `MCP_GIT_AUTH_TOKEN`) for every server before starting the agent; an unset variable raises `ValueError` at config-load time (fail-closed). `git_mcp_server.toml` and `cicd_mcp_server.toml` use the same variable value as the corresponding `agent.toml` entry (shared secret between client and server); `web_search_mcp_server.toml` shares `MCP_WEB_SEARCH_AUTH_TOKEN` with its `agent.toml` entry in the same way. Changes to authentication, MCP server definitions, or bind addresses take effect only after a full agent restart (not `/reload`). (Explicit in code — `config/agent.toml`, `scripts/shared/config_utils.py`) For setup and troubleshooting, see [`mcp_06_14_mcp-authentication-setup.md`](../22_mcp/mcp_06_14_mcp-authentication-setup.md).

### 2.5.1 Loading MCP tokens from a .env file

`deploy/start_agent.sh` loads operator secrets from a `.env` file when present, so tokens do not need to be exported manually on every session. The file location depends on the environment:

- Production: `<install-root>/.env` (the production install root used by `deploy/deploy.sh`)
- Development: `<repo-root>/.env`

The loader reads only simple `KEY=value` lines; comment lines (starting with `#`) and blank lines are ignored, and variables already set in the shell are never overridden. Before launching, the startup script validates that every variable referenced by the deployed configuration (`${ENV:...}` entries in `config/agent.toml` and the per-server `*_mcp_server.toml` files) is set and non-empty. Any missing variable aborts startup with a `[FATAL]` message that lists exactly which variables are unset, instead of producing a deep traceback later.

Create the file with one secret per line. Replace the placeholder values below with real secrets:

```bash
# <install-root>/.env
MCP_SHELL_AUTH_TOKEN=
MCP_GIT_AUTH_TOKEN=
MCP_WEB_SEARCH_AUTH_TOKEN=
MCP_FILE_DELETE_AUTH_TOKEN=
MCP_FILE_WRITE_AUTH_TOKEN=
MCP_FILE_READ_AUTH_TOKEN=
MCP_GITHUB_AUTH_TOKEN=
MCP_CICD_AUTH_TOKEN=
MCP_RAG_PIPELINE_AUTH_TOKEN=
MCP_MDQ_AUTH_TOKEN=
```

Keep the `.env` file out of version control (it is gitignored) and restrict its permissions with `chmod 600`. (Explicit in code — `deploy/start_agent.sh`, `.gitignore`)

> **Note:** web-search authenticates with the same shared `MCP_WEB_SEARCH_AUTH_TOKEN` as its `agent.toml` entry. The former separate browser token was retired; an environment file that still defines `MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN` can drop it. (Explicit in code — `config/web_search_mcp_server.toml`, `scripts/mcp_servers/web_search/web_search_server.py`)

### 2.6 Compiled Artifacts (NUITKA `--onefile`)

The agent and its MCP servers are distributed as Nuitka `--onefile` binaries rather than launched through `uv run`. `deploy/build_binaries.sh` builds the 11 binaries (the agent plus one `mcp_<server>` per MCP server) on the build host; `deploy/deploy.sh` copies them into `/opt/llm/bin/`.

Layout on the deployed host:

- `/opt/llm/bin/` holds the 11 binaries (`agent` plus one `mcp_<server>` per MCP server). It must not be group/world-writable; the CommandValidator rejects binaries located under a writable directory.
- `/opt/llm/dict/system.dic` is the external Sudachi dictionary (built by `deploy/build_binaries.sh`, placed by `deploy/deploy.sh`).
- `config/` stays external (copied by `deploy/deploy.sh`).

`deploy/start_agent.sh` exports two variables before launch so the binary resolves these external files:

- `LLMAGENT_CONFIG_DIR=/opt/llm/config`
- `LLMAGENT_SUDACHI_DICT=/opt/llm/dict/system.dic`

A missing config directory or dictionary fails startup with an explicit error naming the path.

**MCP server launch.** Each subprocess-mode MCP server's `cmd` in `config/agent.toml` is the single element `/opt/llm/bin/mcp_<server>`. The agent launch in `deploy/start_agent.sh` is a compiled binary independent of those `cmd` entries. `scripts/` stays deployed alongside the binaries.

---

## 3. DB Initialization

### 3.0 Platform DB Overview

The agent uses the SQLite databases listed below. Each has a path key in
`agent.toml` or falls back to `DbConfig`'s Python-level default
(`scripts/db/config.py`); see the auto-generated DB Path Reference below for which.

| DB | Config key | Purpose |
|---|---|---|
| `rag.sqlite` | `rag_db_path` | RAG documents, chunks, embeddings |
| `session.sqlite` | `session_db_path` | Agent sessions, messages |
| `workflow.sqlite` | `workflow_db_path` | Task tracking, event processing |
| `eventbus.sqlite` | `eventbus_db_path` | Event Bus records |

Default paths are not stated here: the DB Path Reference below shows which keys are set in `agent.toml` and which fall back to a Python-level default.

Schema details: `db_01_architecture_and_schema-overview-and-config.md`

### 3.1 Applying Schema

```bash
bash deploy/init_db.sh
```

**Responsibilities of init_db.sh:**
- Runs `db/create_schema.py` to initialize the rag, session, workflow, and eventbus databases
- Creates `workflow.sqlite` and its mandatory tables (tasks, attempts, processed_events, artifacts)
- Applies the incremental migrations of `workflow.sqlite` and `eventbus.sqlite` (idempotent); `rag.sqlite` and `session.sqlite` are create-only and are not migrated
- Verifies all mandatory tables exist; aborts if any are missing

**Upgrade note (workflow schema 1.1.0):** `init_db.sh` migrates an existing `workflow.sqlite`: tasks that were waiting for the removed approval stage are marked failed and the `approvals` table is dropped. Back up `workflow.sqlite` first, run `init_db.sh` before `setup_services.sh` (which rejects a schema-version mismatch), and make sure the workflow definition no longer contains `require_approval` (the loader rejects the key).
- Records the schema version

**Upgrade note (`/undo` compression boundary):** the `/undo` compression boundary adds `sessions.undo_floor_message_id`. `session.sqlite` has no incremental migration, so the release that introduces the column requires recreating `session.sqlite`; the recreated file is empty, and the memory tables recover separately.

| Step | Action |
|---|---|
| 1. Prepare | Export sessions worth keeping with `/session export`; note the pinned memories |
| 2. Stop | Stop the agent |
| 3. Archive | Archive every DB with `rotate_all_dbs()` (db_07, DB Recreation Procedure, Step 1) |
| 4. Delete | Delete only `session.sqlite` (`session_db_path` in `agent.toml`) |
| 5. Create | Run only `create_session_schema()`; do not touch other DBs |
| 6. Recover memory | Start the agent and run `/memory rebuild` (dry run first, then `--confirm`; add `--allow-loss` if memories exist only in SQLite). Deletes and pins recorded as change events are reproduced; earlier ones are not |
| 7. Verify | Confirm `undo_floor_message_id` with `PRAGMA table_info(sessions)` |

Sessions, messages, and diagnostics are not recovered; past sessions can no longer be loaded.

### 3.2 Deployment Checklist

- [ ] `config/workflows/default.json` exists
- [ ] `deploy.sh` finished successfully (no [FATAL] errors)
- [ ] `init_db.sh` reported all mandatory tables and correct schema version
- [ ] `setup_services.sh` passed pre-flight checks
- [ ] No publisher or consumer process holds the Event Bus `auth_token` or `admin_token` (`eventbus_07_configuration-and-operations.md`, Token Distribution)

### 3.3 Failure Modes

| Symptom | Failing Script | Remediation |
|---|---|---|
| `[FATAL] Missing required workflow definition` | deploy.sh | Add `config/workflows/default.json` |
| `[FATAL] Workflow definition failed validation; aborting deployment.` | deploy.sh | Fix JSON validation error |
| `[FATAL] Deployed workflow definition checksum does not match source; deployment corrupted.` | deploy.sh | Re-run `deploy.sh`, check filesystem integrity |
| `[FATAL] Workflow database schema is missing or incomplete.` | init_db.sh / setup_services.sh | Re-run `init_db.sh` |
| `[FATAL] Workflow schema version mismatch: expected <X>, found <Y>.` | setup_services.sh | Apply migrations via `init_db.sh` |

For detailed diagnosis and recovery commands per failure mode, see [Workflow Deployment Runbook](../23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook).

Regarding why these deployment requirements are mandatory (design decisions for auditing, recovery, and persistence of workflow state), see [ADR-001](../10_adr/adr_02_001_workflow-engine-mandatory.md).

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

- deployment
- environment
- setup
- installation
- provisioning
- operations
- llama-cpp
- sqlite-vec
- db-initialization
