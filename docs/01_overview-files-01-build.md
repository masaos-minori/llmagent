---
title: "Build and Models File Structure"
category: overview
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

Directory structure for deployment:

``` text
/opt/llm/
├─ llama.cpp/                                 # llama.cpp source and build artifacts
├─ models/
│   ├─ (chat LLM)  # Refer to [docs/02_deployment.md §1.4](02_deployment.md#14-llm-モデルの取得)
│   └─ (embedding LLM)  # Refer to [docs/02_deployment.md §1.4](02_deployment.md#14-llm-モデルの取得)
```

Deployment scripts (located under the `deploy/` repository, executed with `bash deploy/xxx.sh`):

``` text
deploy/
├─ deploy.sh                                  # Copies Python scripts, configurations, and SQL to /opt/llm/
├─ build_sqlite_vec.sh                        # Downloads and builds sqlite-vec (vec0.so). Run once during initial deployment.
├─ init_db.sh                                 # Initializes SQLite schema. Run once after executing deploy.sh.
├─ setup_services.sh                          # Starts MCP servers (:8004-:8014) and LLM servers (:8080-:8081)
│                                              # as agent management subprocesses
└─ start_agent.sh                             # Starts AgentREPL (prefers /opt/llm/pyproject.toml in production)
```

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
