title: "Deployment Guide (Part 1)"
category: deployment
tags:
  - deployment
  - environment
  - setup
related:
  - 01_overview.md
source:
  - 02_deployment.md


# Environment Setup & Service Startup

## Embedding: multilingual-E5-small (384 dim)

### 1.1 Gentoo Linux Package Installation

For OS package installation procedures, please refer to [docs/02_deployment-provisioning.md](docs/02_deployment-provisioning.md).

> If the Python `sqlite3` module does not support loadable extensions:
> ```bash
> echo 'dev-lang/python sqlite' >> /etc/portage/package.use/python
> emerge --ask dev-lang/python
> ```

### 1.2 Python Environment Setup (using uv)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --dev --system-certs
```

Dependency management is centralized in `pyproject.toml`/`uv.lock` (`requirements.txt` does not exist).
Running `uv sync` installs all dependency packages for both runtime and development.

### 1.3 Building llama.cpp

For build instructions, please refer to [docs/02_deployment-provisioning.md](docs/02_deployment-provisioning.md).

### 1.4 Obtaining LLM Models

Place model files in `/opt/llm/models/`. File names must match the names used in each service configuration (e.g., `model-path`).

> **Canonical source** — This table is the canonical source for model filenames. `docs/01_overview-files-01-build.md` and `docs/03_rag_05_1-configuration-reference.md` refer to this.

| Model | Filename |
|---|---|
| multilingual-e5-small (Embedding) | multilingual-e5-small-Q8_0.gguf |
| gemma-4-e4b-it (LLM) | gemma-4-e4b-it-Q4_K_M.gguf |
| Qwopus3.6-35B-A3B-v1 (LLM) | Qwopus3.6-35B-A3B-v1-MTP-Q4_K_M.gguf |

---

## 2. Service Configuration

### 2.1 Building sqlite-vec (first time only)

SQLite vector approximate nearest neighbor (KNN: K-Nearest Neighbor) extension. Provides vector embedding storage and similarity search via the `vec0` virtual table.

```bash
bash deploy/build_sqlite_vec.sh
```

Install path: `/opt/llm/sqlite-vec/vec0.so` (must match `sqlite_vec_so` in `agent.toml`)
*Note: Previous documentation and scripts referred to `config/common.toml`, but this has been corrected to `config/agent.toml`.*

### 2.2 Deploying scripts

`deploy/deploy.sh` performs bulk copying of scripts, config files, and SQL files.

```bash
bash deploy/deploy.sh
```

deploy.sh copies the runtime artifacts required for production operation (dependency definitions, scripts, configuration, and schemas) into `/opt/llm/` and creates the necessary directory structure. For exact details, refer to the comments in `deploy/deploy.sh`.

**Workflow artifact responsibilities (deploy.sh):**
- Checks that `config/workflows/default.json` exists — aborts before any copy if missing
- Validates the workflow definition (parseable JSON, required fields/stages/retry-policy) via `python -m agent.workflow.validate`
- Copies `config/workflows/` to `/opt/llm/config/workflows/`
- Prints workflow name, version, stage list, and SHA256 checksums (source and deployed); aborts if the checksums differ

The workflow definition is a **required workflow deployment artifact**:
source `config/workflows/default.json` → deployed to `/opt/llm/config/workflows/default.json`.
There is no disable, fallback, or workflow-optional mode.

### 2.3 Registering and starting LLM services

`deploy/setup_services.sh` initializes the LLM services.

MCP servers (ports 8004-8014) auto-start as agent-managed subprocesses on agent startup.

**Workflow pre-flight responsibilities (setup_services.sh):**
- Re-checks that the deployed workflow definition (`/opt/llm/config/workflows/default.json`) exists and re-validates it
- Re-checks that `workflow.sqlite` exists with all required tables and a matching schema version
- Services (Event Bus, LLM, MCP) are started **only if** all workflow checks pass — a failure here aborts before any service is spawned

```bash
bash deploy/setup_services.sh
```

After starting services, verify connectivity to health check endpoints for both embed-llm and agent-llm. See [docs/02_deployment-operations.md](docs/02_deployment-operations.md) for specific command examples.

### Implementation Supplement (Startup Method)

`deploy/start_agent.sh` automatically detects whether to use production (`/opt/llm`) or development (repository root) based on the presence of `/opt/llm/pyproject.toml`, and executes `python -m agent` (`scripts/agent/__main__.py`) in the corresponding root. (Explicit in code)

> API Key Configuration:
> - Web Search: DuckDuckGo — No API key required
> - GitHub Operations: Export `GITHUB_TOKEN` in shell or source `conf.d/github-mcp` before startup

### 2.4 Verifying MCP Servers

MCP servers automatically start as uvicorn subprocesses according to the `startup_mode = "subprocess"` setting when the agent starts. You can check the status of each server after agent startup using `/mcp status`.

---

## Related Documents

- `01_overview.md`
- `02_deployment.md`

## Keywords

deployment
environment
setup
installation
llama-cpp
sqlite-vec
db-initialization

# DB Initialization & Failure Modes

## 3. DB Initialization

### 3.0 Platform DB overview

The agent uses four SQLite databases. Three have explicit path keys in
`agent.toml`; `workflow_db_path` has no literal entry there and falls back to
`DbConfig`'s Python-level default (`scripts/db/config.py`).

| DB | Default path | Config key | Purpose |
|---|---|---|---|
| `rag.sqlite` | `/opt/llm/db/rag.sqlite` | `rag_db_path` | RAG documents, chunks, embeddings |
| `session.sqlite` | `/opt/llm/db/session.sqlite` | `session_db_path` | Agent sessions, messages |
| `workflow.sqlite` | `/opt/llm/db/workflow.sqlite` | `workflow_db_path` (code default; no `agent.toml` entry) | Task tracking, event processing |
| `eventbus.sqlite` | `/opt/llm/db/eventbus.sqlite` | `eventbus_db_path` | Event Bus records |

Schema details: `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`

### 3.1 Applying Schema

```bash
bash deploy/init_db.sh
```

**Responsibilities of init_db.sh:**
- Creates `workflow.sqlite` and 5 mandatory tables (tasks, attempts, processed_events, artifacts, approvals)
- Applies incremental schema migrations (idempotent)
- Verifies all 5 tables exist; aborts if any are missing
- Records the schema version

### 3.2 Deployment Checklist

- [ ] `config/workflows/default.json` exists
- [ ] `deploy.sh` finished successfully (no [FATAL] errors)
- [ ] `init_db.sh` reported all 5 tables and correct schema version
- [ ] `setup_services.sh` passed pre-flight checks

### 3.3 Failure Modes

| Symptom | Failing Script | Remediation |
|---|---|---|
| `[FATAL] Missing required workflow definition` | deploy.sh | Add `config/workflows/default.json` |
| `[FATAL] Workflow definition failed validation; aborting deployment.` | deploy.sh | Fix JSON validation error |
| `[FATAL] Deployed workflow definition checksum does not match source; deployment corrupted.` | deploy.sh | Re-run `deploy.sh`, check filesystem integrity |
| `[FATAL] Workflow database schema is missing or incomplete.` | init_db.sh / setup_services.sh | Re-run `init_db.sh` |
| `[FATAL] Workflow schema version mismatch: expected <X>, found <Y>.` | setup_services.sh | Apply migrations via `init_db.sh` |

For detailed diagnosis and recovery commands per failure mode, see [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook).

For the production `require_approval` category policy (which categories require a post-execution approval gate, and the local-dev exception), see [Approval Gate](05_agent_03_03_turn-processing-flow-workflow-engine.md#approval-gate).

Regarding why these deployment requirements are mandatory (design decisions for auditing, recovery, and persistence of approval state), see [ADR-Workflow-Mandatory](05_agent_03_03_turn-processing-flow-workflow-engine.md#workflow-execution-mandatory-adr-workflow-mandatory).

## Related Documents

- `01_overview.md`
- `02_deployment.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine.md`

## Keywords

deployment
environment
setup
installation
llama-cpp
sqlite-vec
db-initialization

### DB Path Reference (auto-generated)

<!-- AUTO-GENERATED: gen_deployment_reference.py db-path-reference -->
Generated from `scripts/db/config.py` and `config/agent.toml`. Do not hand-edit between the guard comments; run `python tools/gen_deployment_reference.py` to refresh.

| DB | Default path | Config key | Set in `agent.toml`? |
|---|---|---|---|
| `eventbus.sqlite` | `/opt/llm/db/eventbus.sqlite` | `eventbus_db_path` | Yes |
| `rag.sqlite` | `/opt/llm/db/rag.sqlite` | `rag_db_path` | Yes |
| `session.sqlite` | `/opt/llm/db/session.sqlite` | `session_db_path` | Yes |
| `workflow.sqlite` | `/opt/llm/db/workflow.sqlite` | `workflow_db_path` | No (Python-level default in `scripts/db/config.py`) |
<!-- END AUTO-GENERATED -->
