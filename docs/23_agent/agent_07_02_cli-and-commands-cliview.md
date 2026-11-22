---
title: "Agent CLI and Commands"
area: agent
tags:
  - agent
  - cli
  - commands
related:
  - agent_00_document-guide.md
  - agent_07_01_cli-and-commands-cli-reference.md
  - agent_07_03_cli-and-commands-command-registry.md
  - agent_07_04_cli-and-commands-purpose.md
  - agent_07_05_cli-and-commands-repl-io.md
  - agent_07_06_cli-and-commands-hot-reload.md
  - agent_07_07_cli-and-commands-slash-commands-session-mcp.md
  - agent_07_08_cli-and-commands-slash-commands-context-plan.md
  - agent_07_09_cli-and-commands-slash-commands-workflow-debug.md
  - agent_07_10_cli-and-commands-slash-commands-memory-other.md
  - agent_01_system-overview.md
---
# Agent CLI and Commands

- System Overview → [agent_01_system-overview.md](agent_01_system-overview.md)

## Purpose

To document the responsibilities of `CLIView`, which handles only the presentation layer, and the injection of callbacks into various components.

## Design Intent

### CLIView Responsibility Separation

`CLIView` resides in `agent/cli_view.py` and is responsible **only for the presentation layer**. It does not manage state or business logic; instead, it is injected into each component as a set of callbacks.

### Callback Injection

Each component that needs terminal output receives a `CLIView` method as an injected callback instead of importing the view: token streaming (`LLMClient`), compression notice (`HistoryManager`), and turn start/end and LLM error reporting (`Orchestrator`). Components therefore depend on callback signatures, not on `CLIView` itself.

### Spinner and Tokens

Token output stops the spinner first, so streaming tokens always interrupt the spinner display.

## Responsibility Boundary

- **Presentation Layer Only**: Does not hold state management or business logic.
- **No Input Policy**: `CLIView` does not read stdin, own multiline continuation, or hold input state; stdin ownership and Ctrl-C state live in the input controller (see the REPL input/output document).
- **Test Protocols**: The `Writer` base (`WriterBase`, output operations) lets partial test doubles stand in during testing.

## Keywords

- CLIView
- render only
- responsibility boundary
- callbacks
