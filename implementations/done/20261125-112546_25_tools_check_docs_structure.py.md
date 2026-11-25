## Goal

Re-record the per-file ceiling for `docs/23_agent/agent_14_reference-api-subpackages-generated.md` at the size the
regenerated block reaches, so the documentation size gate accepts the rows this Plan adds (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `SIZE_EXCEPTIONS` resolves per file before `MAX_SIZE` (32,768 B), and the recorded exception equals the accepted
  size, so growth past it must be re-accepted rather than exempted silently.
- The accepted size is the rendered document, not the current file: the gate and the ceiling test both measure the
  document as the generator renders it from live sources.

## Design decisions
- Re-accept at 33,392 B with a dated comment naming this procedure, following the convention already used by the
  other entries in `SIZE_EXCEPTIONS`.
- The comment must not grow the tool file: `tools/check_module_size.py --scripts-dir tools` fails on growth past
  the recorded baseline entry (`check_docs_structure.py` 25,584 B), so the re-acceptance comment replaces the
  existing four-line comment with a shorter one.

## Alternatives considered
- Split the generated document to get under `MAX_SIZE` — rejected: the document boundary is the generator's domain
  split, and moving rows between `agent_13` and `agent_14` would change the generator's contract for a size that is
  only 624 B over a recorded exception.
- Raise `MAX_SIZE` — rejected: it would re-accept every document in the domain, not this one.

## Implementation
### Target file
`tools/check_docs_structure.py`

### Procedure
1. Replace the `agent_14_reference-api-subpackages-generated.md` entry value `33078` with `33392`.
2. Replace its four-line comment with a shorter dated comment naming this procedure and the cause (the three
   generated rows), keeping the file at or below 25,584 B.

### Method
Edit the `SIZE_EXCEPTIONS` entry; no logic change.

### Details
- The new comment records: re-accepted at 33,392 (2026-11-25, mcpai004 procedure 20261125-112546_25), the subpackage
  index grew 33,078 → 33,392 with `TurnControl`, `reconstruct_replay_directives`, and the changed `record_tool_call`
  signature; the ceiling equals the accepted size.
- The replacement comment is 326 B against the existing 361 B, so the tool file shrinks by 35 B and the tools
  module-size gate stays green.

## Compatibility considerations
- Runs before the documentation gate for plan row 23 can pass; the generator run itself is unaffected.
- `tests/tools/test_generate_reference_table.py::TestSymbolEntries::test_generated_agent_index_stays_within_the_document_ceiling`
  reads `SIZE_EXCEPTIONS` from this module, so the test and the checker resolve the ceiling through the same entry.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tools/check_docs_structure.py` | Test | `uv run pytest tests/tools/test_generate_reference_table.py -q` | The ceiling test passes at 33,392 |
| `tools/check_docs_structure.py` | Gate | `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | No growth past the recorded baseline |
| `tools/check_docs_structure.py` | Gate | `uv run python tools/check_docs_structure.py docs/23_agent/agent_14_reference-api-subpackages-generated.md` | No finding |

## Completion criteria
The regenerated document passes the size gate at its recorded ceiling and the ceiling test passes.

## Out of Scope
The generated document content (plan row 23), the manifest (plan row 24), and the generator itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-record the `agent_14` ceiling at 33,392 with a dated comment | Completed | — | 2026-11-25 | comment must not grow the tool file |
| 2 | Run the documentation and module-size checkers (`rules/tool-gates.md`) | Completed | — | 2026-11-25 |  |

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
- **Requirement ID**: `REQ-007` (the generated reference block stays in step with the new symbols)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `tools/check_docs_structure.py`