## rag.sqlite

- **Owner**: Agent team
- **Config source**: `config/rag_pipeline_mcp_server.toml` (`rag_db_path`)
- **Path**: `/opt/llm/db/rag.sqlite`
- **Schema authority**: `scripts/db/schema_sql.py` (`build_rag_schema_sql(dims)`)
- **WAL policy**: Enabled (journal_mode=WAL)
- **Lifecycle**: Created on first RAG pipeline use; persists until deleted
- **Backup responsibility**: Agent team (daily cron)
- **Vector schema**: `chunks_vec(embedding float[1024], distance_metric=L2)` per `QWEN3_EMBEDDING_DIMS=1024`

## session.sqlite

- **Owner**: Agent team
- **Config source**: `config/agent.toml` (`session_db_path`)
- **Path**: `/opt/llm/db/session.sqlite`
- **Schema authority**: `scripts/db/schema_sql.py` (`build_session_schema_sql(dims)`)
- **WAL policy**: Enabled (journal_mode=WAL)
- **Lifecycle**: Created on first agent use; persists until deleted
- **Backup responsibility**: Agent team (daily cron)
- **Vector schema**: `memories_vec(embedding float[1024], distance_metric=L2)` per `QWEN3_EMBEDDING_DIMS=1024`

## workflow.sqlite

- **Owner**: Agent team
- **Config source**: `config/agent.toml` (`workflow_db_path`, default `/opt/llm/db/workflow.sqlite`)
- **Path**: `/opt/llm/db/workflow.sqlite`
- **Schema authority**: `scripts/db/schema_sql.py` (`build_workflow_schema_sql()`)
- **WAL policy**: Enabled (journal_mode=WAL)
- **Lifecycle**: Created on first workflow use; persists until deleted
- **Backup responsibility**: Agent team (daily cron)
- **Tables**: tasks, attempts, processed_events, artifacts, approvals, workflow_schema_version

## eventbus.sqlite

- **Owner**: Agent team
- **Config source**: `config/eventbus.toml` (`eventbus_db_path`, default `/opt/llm/db/eventbus.sqlite`)
- **Path**: `/opt/llm/db/eventbus.sqlite`
- **Schema authority**: `scripts/db/schema_sql.py` (`build_eventbus_schema_sql()`)
- **WAL policy**: Enabled (journal_mode=WAL)
- **Lifecycle**: Created on first event bus use; persists until deleted
- **Backup responsibility**: Agent team (daily cron)
- **Tables**: events

## mdq.sqlite

- **Owner**: Agent team
- **Config source**: `config/mdq_mcp_server.toml` (`db_path`, default `/opt/llm/db/mdq.sqlite`)
- **Path**: `/opt/llm/db/mdq.sqlite`
- **Schema authority**: `scripts/mcp_servers/mdq/db_schema.py`
- **WAL policy**: Enabled (busy_timeout configured)
- **Lifecycle**: Created on first MDQ use; persists until deleted
- **Backup responsibility**: Agent team (on-demand)
