## Goal

Remove the literal port number from the MDQ category description and replace with prose describing what the setting controls rather than its current value.

## Scope

Modify `docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`: remove the literal port number "8013" at line 30 and confirm the surrounding sentence still reads coherently.

## Assumptions

- Line 30 contains a literal port number "8013" that duplicates `config/agent.toml` and goes stale when the port changes.
- Removing the port number does not break the sentence structure.
- The surrounding prose ("All `/mdq` commands call MCP tools of `mdq-mcp` via the agent's tool executor") remains coherent after removal.

## Design decisions

- Replace the literal port number with a reference to the configuration surface where the authoritative port assignment is defined.
- Preserve the rest of the sentence describing what the setting controls.

## Alternatives considered

- Retain the port number with a note that it is illustrative: rejected because the policy targets literal port numbers in prose regardless of intent.
- Remove the entire sentence about mdq-mcp: rejected because the sentence describes component responsibility, which is retain-category content.

## Implementation

### Target file

`docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

### Procedure

1. Read line 30 and its surrounding paragraph to confirm the context of the literal port number.
2. Remove the literal port number "8013".
3. Replace with prose describing what the setting controls (the mdq-mcp server's transport URL) rather than its current value.
4. Confirm the surrounding sentence still reads coherently.
5. Run `uv run python tools/check_docs_content_policy.py` to verify zero findings.

### Method

Read line 30: "All `/mdq` commands call MCP tools of `mdq-mcp` (port 8013) via the agent's tool executor."

Replace "(port 8013)" with prose describing the mdq-mcp server's role without referencing its current port assignment. The replacement should maintain the sentence's grammatical coherence while removing the concrete configuration value.

### Details

Line 30 currently reads:
```
All `/mdq` commands call MCP tools of `mdq-mcp` (port 8013) via the agent's tool executor.
```

The literal port number "8013" appears in parentheses as a parenthetical clarification of which mdq-mcp server is being referenced. This is a concrete configuration value that duplicates `config/agent.toml` and goes stale when the port changes.

Replace with:
```
All `/mdq` commands call MCP tools of `mdq-mcp` via the agent's tool executor.
```

The sentence remains grammatically coherent without the parenthetical port number. The mdq-mcp server's identity is established by its name; the specific port is an implementation detail best sourced from the configuration file.

## Compatibility considerations

- The replacement must maintain the same information coverage as the original sentence. The mdq-mcp server's identity is preserved; only the concrete port number is removed.
- Cross-references to other documents (e.g., [MDQ vs RAG Boundary](04_mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary)) must be preserved.

## Security considerations

- None identified. This is a documentation-only change removing a literal port number.

## Rollback considerations

- If the prose replacement loses critical identification of the mdq-mcp server, the original sentence can be restored temporarily while a better replacement is drafted.
- The rollback path is straightforward: revert the edit and restore the original sentence.

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md` | Zero literal-port-number findings; structure check passes |

## Completion criteria

- The literal port number at line 30 has been removed.
- The surrounding sentence remains coherent and still describes what the setting controls.
- `check_docs_content_policy.py` reports zero literal-port-number findings for this file.

## Out of scope

- Modifying any other content in this file beyond the flagged port number and its immediate sentence.
- Any other file or section of this document.
- Any file outside the Agent domain.

## execution status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read line 30 and its surrounding paragraph | Completed | — | — | Confirmed context of literal port number |
| 2 | Remove the literal port number and replace with prose | Completed | — | — | Removed "(port 8013)" parenthetical; sentence remains coherent |
| 3 | Run validation checks | Completed | — | — | Zero literal-port-number findings; structure check has pre-existing "Related Documents" issue unrelated to this change |

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
- **Requirement ID**: REQ-001: Each of the 48 flagged lines has an explicit disposition recorded
- **Source issue**: issues/20260905-153715_dcp004_agent_docs_content_policy_cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-211530_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-000740
- **Related target files**: docs/05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
