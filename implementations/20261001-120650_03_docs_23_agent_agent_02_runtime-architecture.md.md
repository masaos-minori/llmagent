## Goal
- REQ-003: translate the Japanese prose in `## Preflight Gate Coverage`; the file ends with no Japanese or full-width characters and no new checker findings (REQ-007: no regression).

## Scope
- In: the lines listed under Implementation > Details in `docs/23_agent/agent_02_runtime-architecture.md`.
- Out: every other line of `docs/23_agent/agent_02_runtime-architecture.md` and every other file.

## Assumptions
- Current content re-verified on 2026-10-01 (plan-to-implementation-procedure Step 3a); line numbers are a locating aid and may shift — locate by content.
- No prerequisite gate: this row does not depend on langadr001 output.

## Design decisions
- Preserve the obligation strength ('requires') and the backtick identifier `check_preflight()` unchanged.
- Edit only the Japanese/full-width text and the minimal surrounding words (Plan Implementation intent).

## Alternatives considered
- N/A: direct translation of two sentences; no structural alternative.

## Implementation
### Target file
- `docs/23_agent/agent_02_runtime-architecture.md`

### Procedure
1. Check the prerequisite gate in Assumptions (if any); stop and log a blocker if unmet.
2. Locate each line listed in Details by content.
3. Apply the change described in Details.
4. Run the Validation plan.
5. Self-review the meaning and record the result in Execution Status Notes.

### Method
- Targeted single-line edits; confirm with `git diff -U0 docs/23_agent/agent_02_runtime-architecture.md` that only the listed lines changed.

### Details
- Current lines:
  - 56: `` `check_preflight()` の呼び出しサイトとそのテストカバレッジを文書化する。 ``
  - 57: `未テストの実行経路はゲートを迂回する可能性があるため、すべての経路にテストまたは正当化が必要。`
- Change:
  - Replace with: 'Document the call sites of `check_preflight()` and their test coverage. Because an untested execution path may bypass the gate, every path requires a test or a justification.' (Plan Design proposed wording).

## Compatibility considerations
- `uv run python tools/check_docs_consistency.py --domain agent` checks backtick function references; `check_preflight()` stays unchanged.

## Security considerations
- N/A: documentation wording change only.

## Rollback considerations
- Revert with `git checkout -- docs/23_agent/agent_02_runtime-architecture.md`; no other file in this Plan depends on this edit.

## Validation plan
- `uv run python tools/check_docs_japanese.py` — file not listed.
- Full-width grep (AC-007 pattern) on the file — no output.
- `uv run python tools/check_docs_consistency.py --domain agent` — no new finding.
- `uv run python tools/check_docs_quality.py` — no new line for this file (baseline 4).

## Completion criteria
- No Japanese characters remain; meaning preserved (self-review recorded).
- Only the listed lines changed.

## Out of scope
- Pre-existing findings in this file listed in the Plan Design baseline; any line not listed in Details; ADR files; tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Details | Completed | 20261001-135901 | 20261001-135901 |  |
| 2 | Run the Validation plan and compare with the Plan Design baseline | Completed | 20261001-135901 | 20261001-135901 |  |
| 3 | Self-review meaning and record result in Notes | Completed | 20261001-135901 | 20261001-135901 | Two Japanese sentences (lines 56-57) translated with the procedure's proposed wording; check_preflight() identifier unchanged; check_docs_consistency --domain agent unchanged; all checks unchanged vs batch baseline; full suite deferred to batch end per user decision; docs-mapping step N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-007 (AC-003, AC-007) — Plan Implementation steps Step 4
- **Source issue**: issues/20261001-104622_langdoc001_remove-japanese-text-from-non-adr-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-110459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-120650
- **Related target files**: docs/23_agent/agent_02_runtime-architecture.md