# Implementation: Promote Database Ownership Note to Section 2 Intro

## Goal

Strengthen ownership boundary wording in `docs/03_rag_04_data_model_and_interfaces.md` by adding a dedicated "Database Ownership" paragraph at the start of section 2 (before the table list), explicitly stating RAG-owned tables only.

## Scope

- **In-Scope**: Add "Database Ownership" paragraph to section 2 intro in `docs/03_rag_04_data_model_and_interfaces.md`
- **Out-of-Scope**: Modifying any runtime code; moving Agent session tables into RAG; changing schema definitions

## Assumptions

- Phase 1 verification confirmed: no session ownership wording exists in `docs/03_rag_02`, `03_rag_03`, `03_rag_05`
- Phase 1 verification confirmed: `docs/05_agent_09_data-layer.md` exists as cross-reference target
- Phase 1 verification confirmed: `tests/test_create_schema.py::test_no_session_tables_in_rag_db` already passes

## Implementation

### Target file

`docs/03_rag_04_data_model_and_interfaces.md`

### Procedure

1. Insert a "Database Ownership" paragraph after the section 2 header (line 71: `## 2. SQLite Schema (\`rag.sqlite\`)`) and before the subsection 2.0 table list.
2. After inserting, evaluate whether the existing inline Note at lines 84-87 becomes redundant. If redundant, remove it; if it still provides value as an inline reminder, keep it.

### Method

Direct file edit — insert text between section header and subsection content.

### Details

Insert the following paragraph after line 71 (`## 2. SQLite Schema (\`rag.sqlite\`)`):

```markdown
### 2.0 Database Ownership

**RAG-owned tables only** — `rag.sqlite` contains exclusively RAG-layer tables:

- `documents` — URL-level document management
- `chunks` — Split chunk body text
- `chunks_fts` — FTS5 virtual table for full-text search
- `chunks_vec` — sqlite-vec virtual table for vector search

Agent session tables (`sessions`, `messages`, `tool_results`, `memories`, etc.) reside in a separate SQLite file (`session.sqlite`) and are owned exclusively by the Agent layer. See [05_agent_09_data-layer.md](05_agent_09_data-layer.md) for the Agent session schema.
```

This replaces the current `### 2.0 テーブル一覧` header with a new structure:

- Keep `### 2.0 テーブル一覧` as-is (it is in Japanese and already present)
- Add the "Database Ownership" paragraph before `### 2.0 テーブル一覧`

Or alternatively, rename `### 2.0 テーブル一覧` to include the ownership statement:

```markdown
### 2.0 テーブル一覧 (RAG-owned tables only)

**RAG-owned tables:** `documents`, `chunks`, `chunks_fts`, `chunks_vec` — all in `rag.sqlite`.

Agent session tables (`sessions`, `messages`, `tool_results`, `memories`, etc.) reside in a separate SQLite file (`session.sqlite`) and are owned exclusively by the Agent layer. See [05_agent_09_data-layer.md](05_agent_09_data-layer.md) for the Agent session schema.
```

Then remove the existing inline Note at lines 84-87 if it becomes redundant after this change.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_04_data_model_and_interfaces.md` | Manual review | Read section 2 intro and table list | Section 2 explicitly states RAG-owned tables only; no implication of session ownership in RAG |
| `tests/test_create_schema.py` | Run existing test | `uv run pytest tests/test_create_schema.py::TestCreateRagSchema::test_no_session_tables_in_rag_db -v` | PASSED — RAG schema has no sessions/messages tables |
