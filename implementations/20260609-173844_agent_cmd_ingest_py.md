# Implementation: agent/commands/cmd_ingest.py + registry.py — add /rag search command

## Goal

Add a `/rag search <query> [--debug]` slash command to the agent REPL that runs the in-process RAG pipeline and prints retrieved context chunks. When `--debug` is passed, also print per-stage latency from `RagPipeline.last_timings`.

## Scope

- `scripts/agent/commands/cmd_ingest.py` — add `_cmd_rag()` to `_IngestMixin`
- `scripts/agent/commands/registry.py` — register `/rag` as a prefix command in `_COMMANDS`

## Assumptions

1. `AgentContext` has a `rag_pipeline` attribute that may be `None` when RAG is disabled.
2. `RagPipeline.augment(query, history_context="")` is the correct public API; it returns a context string (empty string when no results).
3. `RagPipeline.last_timings` is a `dict[str, float]` populated after `run()` is called by `augment()`.
4. This is an async command (`is_async=True` in CommandDef) because `augment()` is a coroutine.
5. `print()` is acceptable in command handlers (they are in `agent/commands/`, not library modules).

## Implementation

### Target file

`scripts/agent/commands/cmd_ingest.py` (primary), `scripts/agent/commands/registry.py`

### Procedure

1. Read `scripts/agent/commands/cmd_ingest.py`.
2. Add `_cmd_rag()` as an async method on `_IngestMixin`.
3. Read `scripts/agent/commands/registry.py`.
4. Add `CommandDef("/rag", True, True, "_cmd_rag", "Search RAG knowledge base")` to `_COMMANDS`.
5. Run ruff + mypy on both files.

### Method

New async method in `_IngestMixin`; one entry appended to `_COMMANDS` list.

### Details

**`scripts/agent/commands/cmd_ingest.py` — new method:**
```python
async def _cmd_rag(self, args: str) -> None:
    """Search the RAG knowledge base with the given query.

    Usage:
      /rag search <query>            Run search and print context
      /rag search <query> --debug    Also print per-stage latency
    """
    ctx = self._ctx
    parts = args.strip().split(None, 1)
    sub = parts[0] if parts else ""
    if sub != "search" or len(parts) < 2:
        print("Usage: /rag search <query> [--debug]")
        return

    remainder = parts[1]
    debug = "--debug" in remainder
    query = remainder.replace("--debug", "").strip()
    if not query:
        print("Usage: /rag search <query> [--debug]")
        return

    if ctx.rag_pipeline is None:
        print("RAG pipeline is not initialized (use_search=false).")
        return

    context = await ctx.rag_pipeline.augment(query)
    if not context:
        print("No results found.")
    else:
        print(context)

    if debug:
        timings = ctx.rag_pipeline.last_timings
        if timings:
            print("\n--- Stage timings ---")
            for stage, elapsed in timings.items():
                print(f"  {stage}: {elapsed * 1000:.1f} ms")
```

**`scripts/agent/commands/registry.py` — append to `_COMMANDS`:**

Find the block of prefix async commands and add:
```python
CommandDef(
    "/rag",
    True,   # prefix=True (args passed)
    True,   # is_async=True
    "_cmd_rag",
    "Search the RAG knowledge base (/rag search <query> [--debug])",
),
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/cmd_ingest.py scripts/agent/commands/registry.py` | 0 errors |
| Type | `uv run mypy scripts/agent/commands/cmd_ingest.py` | no new errors |
| Unit tests | `uv run pytest tests/ -k "cmd_ingest or rag" -v` | all pass |
| Manual smoke | `/rag search test query` in REPL | prints context or "No results found." |
| Debug flag | `/rag search test query --debug` | prints timings block |
