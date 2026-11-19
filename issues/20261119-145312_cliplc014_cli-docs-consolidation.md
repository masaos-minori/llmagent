# Consolidate CLI and MCP lifecycle documentation after contract stabilization

## Priority
Low

## Summary
Produce one coherent CLI and MCP lifecycle documentation set that reflects the corrected implementation, removes duplicate specifications, and passes Markdown and command-consistency validation.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 14). The CLI documents exist under `docs/23_agent/` as `agent_07_01` through `agent_07_10` (`Explicit in code`, by `git ls-files`); the backlog's paths without the `23_agent/` directory do not exist. The listed defects (duplicate command definitions, misleading file names, empty sections, punctuation errors, contradictory shutdown guarantees, obsolete delayed-input behavior) are backlog claims and `Needs confirmation`. The MCP lifecycle and operations documents are `Unknown`.

## Problem
Duplicate and contradictory documentation may mislead operators and implementers; updating it before the implementation settles would recreate drift.

## Reason for Change
Last step in the order; documentation follows stable contracts. A mismatch that makes an operator take a wrong action would be higher priority; none is cited here.

## Implementation Intent
One authoritative specification per command and lifecycle concept; navigation, filenames, examples, and guidance match the final implementation; automated checks catch future drift. Follow `skills/DESIGN.md` (no implementation-reference duplication).

## Target Files or Areas
- `docs/23_agent/agent_07_01` through `agent_07_10` (CLI reference, CLIView, command registry, REPL I/O, hot reload, slash commands)
- MCP lifecycle and operations documentation (`Unknown`)

## Required Changes
- One canonical command specification per command; rename files whose names do not match their content; remove or complete empty sections; fix navigation links, spacing, punctuation, indentation, and command blocks.
- Update input handoff, Ctrl-C, shutdown, maintenance jobs, history compression, reload, MCP lifecycle, health, logging, and command semantics; document the state machines and result codes.
- Add Markdown lint, broken-link, duplicate-usage, and command-reference consistency checks.

## Constraints
- Do not merge before the behavior it documents. An ADR content change needs a maintainer approval record (governance_01, governance_05); do not write or simulate it.
- Documents must pass the repository's docs checkers.

## Acceptance Criteria
- [ ] No duplicate authoritative command specifications remain; all documented commands exist.
- [ ] Documentation matches tested implementation behavior.
- [ ] Markdown lint, link checks, and command-reference checks pass.

## Testing Expectations
- Docs checkers (`check_docs_quality`, content policy, link checks) and the new command-reference check; run them on the changed files.

## Documentation Impact
This issue is the documentation change: intent, boundaries, failure behavior, and Known Issues.

## Out of Scope
- Behavior changes owned by the other issues of this backlog.

## Dependencies
- Depends on `issues/20261119-145259_cliplc001_repl-input-controller.md` through `issues/20261119-145311_cliplc013_api-field-cleanup.md`.

## Unresolved Questions
- `不明`: the exact MCP lifecycle and operations documents to update.

## AI Implementation Instruction
Verify each statement against current source and a test before writing it. Edit documentation only. Stop and report any statement that no test proves.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145312
- **Related target files**: `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`, `docs/23_agent/agent_07_02_cli-and-commands-cliview.md`, `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`, `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`, `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`, `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`, `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md`, `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`, `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`
