## Goal

Note the `0`/negative `tool_concurrency_limits` semantics ("unlimited" — no semaphore
created) in the config reference doc `docs/23_agent/agent_08_03_configuration-tools-memory.md`,
next to the `tool_concurrency_limits` entry under "Parallel Execution", consistent with the
`_ensure_semaphores` docstring (see the companion procedure for `tool_transport_invoker.py`).

## Scope

- **In-Scope**: Add one clause to the `tool_concurrency_limits` bullet under "Parallel
  Execution" in `docs/23_agent/agent_08_03_configuration-tools-memory.md` stating that a
  `0`/negative value means "unlimited" (no semaphore created). (REQ-001)
- **Out-of-Scope**: Modifying `docs/22_mcp/mcp_03_02_tool-registry.md` (read to avoid
  contradiction, but out of frozen scope), changing any `scripts/shared/` code, or altering
  other config entries.

## Assumptions

- Option (a) is the resolved semantics (`0`/negative = unlimited); the doc records it.
- The "Parallel Execution" section currently documents `tool_concurrency_limits` without
  mentioning `0`; the note extends that single bullet.
- Editing this doc triggers the repo's docs checker (per `routing.md`), which the
  implementation phase must run.

## Design decisions

- **Single-bullet extension**: append the `0` clause to the existing `tool_concurrency_limits`
  bullet rather than adding a new bullet, keeping the config reference dense and scannable.
- **Consistent wording**: mirror the `_ensure_semaphores` docstring wording ("unlimited — no
  semaphore created") so code and docs cannot drift (per the Plan's Risk mitigation).

## Alternatives considered
N/A: coercing `0` → `1` is rejected by the Plan; this doc records only the resolved option (a).

## Implementation
### Target file
`docs/23_agent/agent_08_03_configuration-tools-memory.md`

### Procedure
1. Open `docs/23_agent/agent_08_03_configuration-tools-memory.md` and locate the
   `#### Parallel Execution` section (line 46) and its `tool_concurrency_limits` bullet
   (line 48):
   ```markdown
   #### Parallel Execution

   - `tool_concurrency_limits`: Server key → Maximum number of concurrent calls.
   ```
2. Pre-read `docs/22_mcp/mcp_03_02_tool-registry.md` to confirm the new clause does not
   contradict the documented runtime `concurrency_limits` mechanism; if it does, reconcile
   the wording (do not modify `mcp_03_02_tool-registry.md` — report any needed change as a
   Plan gap).
3. Extend the `tool_concurrency_limits` bullet to state the `0`/negative semantics:
   ```markdown
   #### Parallel Execution

   - `tool_concurrency_limits`: Server key → Maximum number of concurrent calls. A `0` (or
     negative) value means "unlimited" — no per-server semaphore is created — consistent
     with the unconfigured default.
   ```
4. Run the applicable docs checker for this file per `routing.md` Tools → "When to run
   which tool" (docs/ edit). Fix any findings. (REQ-001)
5. Do not modify any other doc, or any file under `scripts/shared/`.

### Method
One-line extension to a single config-reference bullet; then run the docs checker.

### Details
Current "Parallel Execution" section (lines 46-48):
```markdown
#### Parallel Execution

- `tool_concurrency_limits`: Server key → Maximum number of concurrent calls.
```
Proposed:
```markdown
#### Parallel Execution

- `tool_concurrency_limits`: Server key → Maximum number of concurrent calls. A `0` (or
  negative) value means "unlimited" — no per-server semaphore is created — consistent with
  the unconfigured default.
```
The config-field contract (`# Per-server concurrent call limit; empty = unlimited`,
`scripts/agent/config_dataclasses.py` lines 199-200) corroborates the "unlimited" reading.
The companion procedure for `scripts/shared/tool_transport_invoker.py` documents the same
semantics in the `_ensure_semaphores` docstring; keep the wording aligned.

## Compatibility considerations
N/A: documentation-only; no code or public API change. The note clarifies existing behavior
(`0` already resolves to the unconfigured default).

## Security considerations
N/A: documentation only; no secret handling or fail-closed path.

## Rollback considerations
Revert the commit.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Docs checker for the edited config reference | Applicable checker per `routing.md` Tools → "When to run which tool" | passes |
| `scripts/shared/` + `tests/shared/` | Static analysis + suite (companion row) | `ruff check` · `mypy` · `uv run pytest tests/shared/` | all pass |

## Completion criteria
The `tool_concurrency_limits` bullet under "Parallel Execution" notes that a `0`/negative
value means "unlimited" (no semaphore), the docs checker passes, and the companion code/test
rows validate.

## Out of scope
`scripts/shared/tool_transport_invoker.py` (REQ-001/REQ-002) and the test
(`tests/shared/test_tool_transport_invoker.py`, REQ-003) are separate rows.
`docs/22_mcp/mcp_03_02_tool-registry.md` is read-only (out of frozen scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 2 | Document `0`/negative = unlimited in `_ensure_semaphores` docstring, emit warning for `0`/negative known-key limit (`tool_transport_invoker.py`), and note `0` semantics in the config reference doc (`agent_08_03_configuration-tools-memory.md`) | Completed | — | 20261013-154442 | REQ-001, REQ-002 |
| 3 | Add `0`-limit (unlimited + warning) and positive-limit (bounded) test; run ruff/mypy/shared-suite; run docs checker | Completed | — | 20261013-154442 | REQ-003, REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: structural non-issue | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (note `0` semantics for `tool_concurrency_limits` in the config reference doc)
- **Source issue**: `issues/20261012-185224_mcp003_concurrency-limit-of-zero-silently-disables-the-per-server-semaphore-in-tooltransportinvoker.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261012-232916_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-092101
- **Related target files**: `docs/23_agent/agent_08_03_configuration-tools-memory.md`