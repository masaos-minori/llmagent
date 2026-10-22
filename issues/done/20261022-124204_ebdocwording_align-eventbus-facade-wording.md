# Align the EventBus facade docstring and README with the current layers

## Priority
Low

## Summary
Correct the module docstring of `scripts/eventbus/db.py` and the layer description in `scripts/eventbus/README.md` so they describe only the layers that exist.

## Background
`memo-issue.md` item M-01 listed several stale compatibility statements. Checked against current source and documents, most are already resolved: the Glossary and governance check text no longer name `read_json_file()`, the Agent package `__init__.py` is a package marker and no document claims it re-exports legacy imports, and the DLQ documents describe the lineage model (fresh event ID, `redelivered_from`). The `offset_migrator.py` docstring item is moot because the module was removed. (Confirmed by search of `docs/` and `scripts/`)

Two stale statements remain:
- The first line of `scripts/eventbus/db.py` says the facade re-exports "connection, event, delivery, DLQ, offset migration" layers; the offset migration layer no longer exists.
- `scripts/eventbus/README.md` describes the schema layer as "Schema definition, migration logic"; that wording stops being true when the EventBus schema-migration removal plan (`plans/done/20261022-093935_plan.md`) is implemented.
The README's "Stub Module Pattern" section already documents `db.py` as the single entry point, which matches the intended wording.

## Problem
A docstring and a README name a removed layer and a removed responsibility, so a reader looks for code that is not there.

## Reason for Change
Keeping navigation text accurate avoids sending developers to deleted modules; the change is small and independent.

## Implementation Intent
Edit the two statements to describe the current layers and keep the stub-module rule unchanged. Do not add a note about what was removed.

## Target Files or Areas
- `scripts/eventbus/db.py` (module docstring only)
- `scripts/eventbus/README.md`

## Required Changes
- Remove "offset migration" from the `db.py` docstring.
- Reword the README schema-layer line to schema definition and creation only, after the schema-migration removal is applied.

## Constraints
- Docstring and README edits only; no code change in `db.py`.
- Follow the repository docstring format check.

## Acceptance Criteria
- Neither file mentions offset migration or schema migration logic as an existing layer.
- `uv run python tools/check_docstrings.py` and the documentation checkers pass.
- The README still states that `db.py` is the single entry point.

## Testing Expectations
- `uv run python tools/check_docstrings.py`, `uv run ruff check scripts/`; documentation checkers if the README is covered.

## Documentation Impact
Yes. One README line and one docstring.

## Out of Scope
- The Glossary, the Agent package documents, and the DLQ documents (already consistent).
- Any code change and the removal of the schema migration itself.

## Dependencies
- Apply the README line after the EventBus schema-migration removal plan (`plans/done/20261022-093935_plan.md`) has been implemented, because it rewrites the same layer.
- Sibling-issue check: no open issue under `issues/` and no active plan under `plans/` touches these files.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Change only the two statements; do not edit other README sections or any code.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261022-124204
- **Related target files**: scripts/eventbus/db.py, scripts/eventbus/README.md
