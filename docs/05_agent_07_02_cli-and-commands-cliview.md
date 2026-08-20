# Agent CLI and Commands

- System Overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

To document the responsibilities of `CLIView`, which handles only the presentation layer, and the injection of callbacks into various components.

## Design Intent

### CLIView Responsibility Separation

`CLIView` resides in `agent/cli_view.py` and is responsible **only for the presentation layer**. It does not manage state or business logic; instead, it is injected into each component as a set of callbacks.

### Callback Injection

| Callback | Injected Into | Trigger Timing |
|---|---|---|
| `write_token(token)` | `LLMClient(on_token=...)` | Whenever an SSE token arrives |
| `write_compress_notice(n)` | `HistoryManager(on_compress=...)` | When history is compressed |
| `write_turn_start()` | `Orchestrator(on_turn_start=...)` | Before each tool loop turn starts |
| `write_turn_end()` | `Orchestrator(on_turn_end=...)` | After the final LLM response |
| `write_llm_error(e)` | `Orchestrator(on_error=...)` | When an LLM request fails |

### Relationship between Spinner and Tokens

`write_token()` calls `stop_spinner()` immediately before outputting a token, allowing streaming tokens to interrupt the spinner display.

### Startup Banner

`write_startup_banner()` displays the session ID, chunk count, number of tools, memory mode, and workflow state.

## Responsibility Boundary

- **Presentation Layer Only**: Does not hold state management or business logic.
- **Test Protocols**: By defining `Writer` (output operations) and `Reader` (multi-line input) protocols, different implementations can be injected during testing.

## Key Constraints

- `CLIView.__init__(slash_commands)` takes a list of slash commands as a required argument and uses them for tab completion suggestions.

## Operational Notes

- Unknown

## Known Limitations

- Unknown

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

CLIView
responsibility boundary
callbacks
