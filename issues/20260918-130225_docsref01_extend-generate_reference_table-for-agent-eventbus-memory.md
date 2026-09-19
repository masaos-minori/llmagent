# Extend generate_reference_table.py to cover Agent, EventBus, and Memory reference generation

## Priority
Medium

## Summary
If the Reference-class ADR (see Dependencies) adopts the generated-artifact option,
`tools/generate_reference_table.py` — which already generates MCP/RAG/deployment
reference tables from source into `<!-- AUTO-GENERATED -->`-guarded blocks — needs new
`--type agent`, `--type eventbus`, and `--type memory` generators to cover the
hand-written "Agent Reference API", "Event Bus: Reference API", and "Memory Layer —
Module Reference" documents a proposed slimming policy identifies as
mechanical-content-heavy.

## Background
`tools/generate_reference_table.py` currently supports exactly three types (`rag`,
`mcp`, `deployment`), each mapped to its own `generate_*_table()` function, guard-
comment pair, and target document.
`docs/00_governance_04_documentation-checks.md`'s `GV-021` already exempts this tool's
guarded output from mechanical-content warnings, establishing the pattern this issue
extends.

## Problem
N/A: covered by Background/Summary — no defect in the existing tool, this is a scope
extension.

## Reason for Change
Without a generation path, converting the Agent/EventBus/Memory reference documents to
the recommended generated-artifact model (per the Reference-class ADR) has no
implementation route other than continuing to hand-maintain them, which is the
drift-prone status quo the ADR is meant to move away from.

## Implementation Intent
Add three new `generate_*_table()` functions following the existing
`generate_rag_config_table`/`generate_mcp_reference_table`/
`generate_deployment_reference_table` pattern, each sourcing from the relevant
module's docstrings/signatures (Agent: `scripts/agent/`; EventBus:
`scripts/eventbus/`; Memory: the memory-layer module(s)) via the same AST/docstring-
reading approach already used by the existing generators. Register each under
`--type agent`/`--type eventbus`/`--type memory` with its own guard-comment pair and
target document mapping, matching the existing `REFERENCE_DOC_*`/`GUARD_START_*`/
`GUARD_END` dictionaries' structure.

## Target Files or Areas
`tools/generate_reference_table.py`; the Agent, EventBus, and Memory Layer reference
documents (exact target document paths to be confirmed — see Unresolved Questions)

## Required Changes
- Add `generate_agent_reference_table()`, `generate_eventbus_reference_table()`,
  `generate_memory_reference_table()` functions, each producing an
  `<!-- AUTO-GENERATED -->`-guarded block from source.
- Register each under a new `--type` value in the existing type-dispatch
  dictionaries.
- Identify and confirm the exact target document path for each of the three new
  types before implementation (currently only described by name in the source
  memo, not yet confirmed against `docs/00_index.md`'s Document References by Task
  table).
- Run each new generator once and verify its output replaces the corresponding
  hand-written Reference-class content correctly.

## Constraints
Do not change the behavior of the existing `rag`/`mcp`/`deployment` generators. Do not
implement this issue until the Reference-class ADR is Accepted with Option B, since
building this tooling before that decision risks wasted or wrong-shaped work.

## Acceptance Criteria
- `python tools/generate_reference_table.py --type agent|eventbus|memory` each runs
  successfully and refreshes its guarded block in place.
- `--dry-run` previews the output without writing, matching the existing generators'
  behavior.
- `tools/check_docs_content_policy.py`'s checks do not flag content inside any of the
  three new guarded blocks.

## Testing Expectations
Add or extend unit tests for the three new generator functions (following any
existing test coverage pattern for `generate_reference_table.py`, to be confirmed at
implementation time). Run `uv run pytest` plus a manual `--dry-run` invocation of each
new `--type` against real repository source before trusting its output.

## Documentation Impact
Each of the three target documents gains an `<!-- AUTO-GENERATED -->` block per
`tools/TOOL_DESCRIPTIONS.md`'s convention for this tool; no other `docs/*.md` file
requires updating.

## Out of Scope
Deciding which specific document is the correct target for each new type beyond a
first reasonable guess (a Needs-Confirmation item, see Unresolved Questions); removing
the corresponding hand-written content is part of this issue's Required Changes only
for the specific block replaced by the guarded output, not a broader mechanical-content
sweep of the target document.

## Dependencies
Blocked by the Reference-class ADR issue reaching Accepted status with Option B
chosen. Complements the `check_docs_content_policy.py` extension issue, which should
treat this tool's guarded output the same way `GV-021` already does.

## Unresolved Questions
The exact target document path for each of the three new `--type` values was not
confirmed during this issue's drafting (the source memo names them descriptively —
"Agent Reference API — Part 1/2", "Event Bus: Reference API", "Memory Layer — Module
Reference" — without citing exact filenames). Confirm each via `docs/00_index.md`'s
Document References by Task table before implementation.

## AI Implementation Instruction
Do not begin implementation until the Reference-class ADR is Accepted with Option B —
if it resolves otherwise (Option A or C), this issue should be closed as
no-longer-applicable rather than implemented. Confirm each target document path
against `docs/00_index.md` before writing any generator, per Unresolved Questions.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260918-130225
- **Related target files**: tools/generate_reference_table.py
