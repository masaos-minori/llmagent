---
title: "Build and Models File Structure"
area: overview
tags:
  - build
  - llama-cpp
  - models
  - gguf
  - deployment
  - file-structure
related:
  - 01_overview-files-02-rag.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-04-shared.md
  - 01_overview-files-05-config.md
  - 01_overview-files-06-misc.md
---

# File Structure

Architecture Overview → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. File Structure

See `deploy/` for the current file layout.

### Deployment Targets

**llama.cpp** — Builds and maintains inference runtime artifacts. Depends on the models directory for GGUF model loading. Owns the compiled shared libraries and header files produced by the build process.

**Chat LLM models** — Owned by the model acquisition process defined in `02_deployment.md` section 1.4. Consumed by the :8080 agent-LLM process. Direction of dependency flows from model acquisition into this component.

**Embedding LLM models** — Owned by the model acquisition process. Consumed by the :8081 embed-LLM process. Direction of dependency flows from model acquisition into this component.

### Deployment Scripts

**`build_sqlite_vec.sh`** — Downloads and builds the sqlite-vec extension (vec0.so). Runs once during initial deployment. No upstream dependency other than network access for downloading.

**`deploy.sh`** — Copies Python scripts, configurations, and SQL to /opt/llm/. Requires `config/workflows/default.json` exists with a valid schema. Dependent on `build_sqlite_vec.sh` completing first in the startup sequence.

**`init_db.sh`** — Initializes the SQLite schema. Depends on `deploy.sh` completing first in the startup sequence. Produces the database state required by downstream services.

**`setup_services.sh`** — Starts MCP servers (:8004-:8014) and LLM servers (:8080-:8081) as subprocesses. Requires workflow definitions validated and DB tables present. Dependent on `init_db.sh` completing first in the startup sequence.

**`start_agent.sh`** — Starts AgentREPL. Prefers `/opt/llm/pyproject.toml` in production. Dependent on `setup_services.sh` completing first in the startup sequence.

### Startup Sequence Dependencies

Workflow validation (`default.json` + `python -m agent.workflow.validate`) is a hard prerequisite for both `deploy.sh` and `setup_services.sh`. DB existence check (`/opt/llm/db/workflow.sqlite` and required tables) is a precondition for `setup_services.sh`.

Startup order: `build_sqlite_vec.sh` → `deploy.sh` → `init_db.sh` → `setup_services.sh` → `start_agent.sh`

### Implementation Notes (Current behavior)

- Both `deploy.sh` and `setup_services.sh` require the existence of `config/workflows/default.json` and validation via `python -m agent.workflow.validate`; failure results in a `[FATAL]` error and aborts deployment/startup (exit 1). Operation without workflow definitions is not supported.
  (Evidence classification: Explicit in code — `deploy/deploy.sh`, `deploy/setup_services.sh`)
- `setup_services.sh` further checks for the existence of `/opt/llm/db/workflow.sqlite` and the `tasks/attempts/processed_events/artifacts/approvals` table. It also aborts with `[FATAL]` if they are missing.
  (Evidence classification: Explicit in code — `deploy/setup_services.sh`)

## Related Documents

- `01_overview-files-02-rag.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`
- [01_overview.md](01_overview.md)

## Keywords

build
llama-cpp
models
gguf
deployment
file-structure
