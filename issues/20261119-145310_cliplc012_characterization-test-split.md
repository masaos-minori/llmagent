# Separate characterization tests from authoritative security and lifecycle contracts

## Priority
Medium

## Summary
Move tests that document unsafe legacy behavior into an explicit characterization suite and create authoritative contract tests for the corrected behavior.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 12). The listed legacy behaviors (delayed-input handoff, process-record deletion before confirmed exit, restart after unconfirmed termination, permissive command confinement, shared credential inheritance, `filter_env(None)`, SIGINT absorption, rename-only log rotation) are backlog claims and `Needs confirmation`; the first of them is at least documented in `scripts/agent/stdin_reader.py:39-43` (`Explicit in code`).

## Problem
The suite locks behaviors that must change, and some tests carry requirement numbers or ordinary placement that makes them look normative, so corrections conflict with "requirements".

## Reason for Change
Each implementation issue must be able to reverse legacy expectations without a conflict; timing follows the implementation issues.

## Implementation Intent
CI distinguishes historical behavior from required security and reliability contracts; migrate as each contract changes.

## Target Files or Areas
- `tests/agent/`, `tests/shared/`, HTTP lifecycle test modules
- CLI input, approval, reload, persistence, and maintenance tests

## Required Changes
- Add a characterization marker or directory; identify authoritative security, lifecycle, persistence, and CLI contract tests; mark every requirement-numbered test authoritative or characterization; reverse or remove unsafe expectations as fixes land; remove contradictory docstrings; add dependency-aware integration tests matching the consolidated issues.

## Constraints
- Marker configuration must work with the project's pytest and CI setup (parallel execution, `tests/conftest.py` fixtures).

## Acceptance Criteria
- [ ] CI reports characterization and contract suites separately.
- [ ] Unsafe legacy tests do not block implementation corrections.
- [ ] Every High-priority issue of this backlog has authoritative acceptance tests.

## Testing Expectations
- Run the full suite with the marker selection both ways; run the checkers that validate pytest markers and test structure.

## Documentation Impact
Yes. The test taxonomy and where authoritative tests live.

## Out of Scope
- Fixing the underlying behavior (owned by the other issues of this backlog).

## Dependencies
- Depends on `issues/20261119-145259_cliplc001_repl-input-controller.md` through `issues/20261119-145309_cliplc011_export-command-contracts.md`.

## Unresolved Questions
- `不明`: marker versus directory for characterization tests.

## AI Implementation Instruction
Classify tests without changing assertions unless the owning issue has landed. Stop and report any test whose intent cannot be determined.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145310
- **Related target files**: `tests/agent/`, `tests/shared/`
