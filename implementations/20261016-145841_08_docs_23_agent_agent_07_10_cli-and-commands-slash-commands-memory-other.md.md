## Goal
- Make every registered `/memory` usage appear in the chapter as an inline code span in the registry's notation, and every documented `/memory` form match a registered usage, without changing the contract the chapter describes.

## Scope
- The Memory Category table and the paragraph about `rebuild` in `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`.

## Assumptions
- The chapter already states the target behavior (confirmations, defaults, pin limit, change events); the registry and handlers are brought to it by other rows.
- `check_command_contracts` requires: each registered usage as an inline code span in one of the command chapters; each documented `/memory ...` span to be a registered usage, a subcommand name, or the bare command; a default declared in the registry to be stated next to its usage.
- The docs are written in English and follow the content policy (no line numbers, no implementation file mappings).

## Design decisions
- Split the combined `pin` / `unpin` row into two rows with the forms `/memory pin <memory_id>` and `/memory unpin <memory_id>`.
- Rewrite the `rebuild` form to the flat rendering `/memory rebuild [--confirm] [--allow-loss]` and state in the existing paragraph that `--allow-loss` is honored only together with `--confirm`.
- Keep the `list` row (default 20, at most 200) and the `prune` row (default `memory_retention_days`) as they are; they already carry the defaults the registry declares.

## Alternatives considered
Teaching the registry to render the nested `rebuild` form: rejected, since `ArgSpec` renders flat tokens and the paragraph can express the dependency in words.

## Implementation
### Target file
`docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`

### Procedure
- In the Memory Category table, replace the `pin` / `unpin` row with a `pin` row (`/memory pin <memory_id>`, "Fixes a memory; no confirmation; refused at the pin limit") and an `unpin` row (`/memory unpin <memory_id>`, "Releases a memory; no confirmation").
- Change the `rebuild` row's form to `/memory rebuild [--confirm] [--allow-loss]`.
- In the paragraph that describes `rebuild`, state that `--allow-loss` takes effect only together with `--confirm`.

### Method
- Escape the pipe in `semantic|episodic` and `--fts|--vec` inside table cells as the table already does; the checker unescapes `\|` when it reads code spans.
- Edit only the rows named above; keep the surrounding text.

### Details
- After the registry row is applied, run the agent-domain consistency check; any remaining finding names the form that still differs.
- The documented `list` form must read `/memory list [n] [--type semantic\|episodic] [--pinned] [--query <text>]`, which the registry now renders.

## Compatibility considerations
N/A: documentation notation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria
- Every registered `/memory` usage is documented and every documented `/memory` form is registered; the agent-domain check reports no `/memory` finding.
- The docs checkers report no new finding.

## Out of scope
- The contract text (confirmations, defaults, change events), other chapters, and the registry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the table rows and the `rebuild` paragraph | Pending | — | — | |
| 2 | Run the docs checkers and the consistency check after the registry change | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (chapter notation matches the registry)
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-143248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145841
- **Related target files**: docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md
