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

### Component Responsibilities

**Build artifacts** — Compiles and maintains the inference runtime. Owns the compiled shared libraries and headers produced by the build process. Consumed by the deployment layer.

**Model assets** — Chat and embedding model weights acquired independently. Consumed by their respective LLM processes. Dependency direction flows from model acquisition into these components.

### Deployment Artifacts

**Build scripts** — One-time setup operations: sqlite-vec extension compilation, Python script and configuration deployment, and SQLite schema initialization. Each runs sequentially; later steps depend on earlier ones completing successfully.

**Service orchestration** — Starts MCP server group and LLM service group as independent subprocesses. Requires workflow definitions validated and database tables present before starting.

**Agent launcher** — Starts the AgentREPL process. Prefers the production pyproject.toml over development alternatives. Dependent on service orchestration completing first.

### Startup Sequence Dependencies

Workflow validation is a hard prerequisite for both deployment and service orchestration. Database existence check is a precondition for service orchestration.

Startup order: build scripts → deployment → schema initialization → service orchestration → agent launcher

### Reason for Process Separation

Deployment scripts are separated because:
- Failure isolation: a failure in one step does not affect others.
- Independent scaling: write-heavy domains may require different resource allocation than read-only domains.
- Deployment independence: individual scripts can be updated or restarted without affecting the entire system.

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
