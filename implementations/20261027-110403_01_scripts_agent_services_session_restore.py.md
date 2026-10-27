## Goal

Add a load-time orphan-tool-call repair step to `scripts/agent/services/session_restore.py`. Currently `restore_session` (lines 47-105) fetches messages via `fetch_messages`, converts the persisted `undo_floor` boundary to a history index via `_boundary_to_index` (lines 26-44), and calls `replace_history` with no pairing check, so an assistant row carrying `tool_calls` with no matching tool-result rows flows straight into restored history. This row inserts a pure module-level repair between `fetch_messages` and the boundary computation so resumed sessions always present a paired sequence to the backend.

## Scope

- **In-Scope** (`scripts/agent/services/session_restore.py` only):
  - Add the module-level repair function `repair_orphan_tool_calls` (new): detection of assistant rows whose `tool_calls` ids are not answered by a following tool-row run, synthesis of the missing tool-result rows using a module-level marker constant and a whitelist-conformant shape, and a single warning log with session id and repaired-row count.
  - Integrate the repair into `restore_session` between the `fetch_messages` call (line 53) and the boundary computation / `replace_history` call.
  - Account for synthesized insertions in the `undo_floor` boundary-index conversion so the floor lands on the same turn as before repair.
- **Out-of-Scope** (owned by other artifacts):
  - Any change to `scripts/agent/session_message_repo.py` (the `fetch_messages` producer) — left byte-identical (`REQ-006`, `AC-005`).
  - Writing synthesized rows to the DB (memory-only; trivially idempotent).
  - Turn write-path changes (frozen Plan `plans/20261027-070403_turn001_atomic-turn-persistence.md`).

## Assumptions

- `restore_session` is the sole session-history load path (only `cmd_session._load_session` calls it); no other load path bypasses the repair.
- The fetched `messages` list is ordered by ascending `message_id`, so a contiguous run of `role="tool"` messages immediately following an assistant row is exactly the tool round that produced it (mirrors the production emit order in `tool_runner._collect_tool_result_msgs`).
- Synthesized rows are whitelist-conformant (`role` / `content` / `tool_call_id`, optional `name`) so `replace_history` validation keeps them (see `ROLE_KEY_WHITELIST` in `message_schema.py`).

## Design decisions

- **Pure module-level function.** Confine the repair to a single helper in this module rather than a new module, matching Path A in the Plan. The helper takes the fetched list and session id and returns the repaired list plus the number of synthesized rows that precede the boundary snapshot.
- **Contiguous tool-run pairing.** For each assistant message with `tool_calls`, search the immediately following contiguous run of `role="tool"` messages for matching `tool_call_id`s; synthesize only the missing ids in `tool_calls` order. This mirrors the production emit order and avoids misclassifying a legitimate multi-round sequence.
- **Synthesis over stripping.** Synthesized rows carry `role="tool"`, the original `tool_call_id`, and the marker constant content, mirroring the synthetic-failure rows built by `tool_preparation._reject`. Stripping would rewrite assistant semantics.
- **Marker constant.** A module-level string constant holds the identifiable interrupted-marker text so logs and history expose a recognizable signature; the value is whitelist-conformant text content.
- **Boundary accounting.** `_boundary_to_index` gains an additive insertion-offset keyword so synthesized rows before the compression snapshot shift the floor consistently.

## Alternatives considered

- **Strip dangling `tool_calls`.** Rejected: rewriting assistant semantics loses the model's record of what it attempted; synthesis preserves it.
- **Repair inside `session_message_repo.fetch_messages`.** Rejected: `REQ-006` forbids changing the repository; the repair belongs at the load facade `restore_session`.

## Implementation

### Target file

`scripts/agent/services/session_restore.py` (existing; extended)

### Procedure

1. Add the module-level marker constant near the top of the module (after the `logger`), holding the interrupted-tool-call marker text.
2. Add the module-level repair function `repair_orphan_tool_calls` (new) that returns a two-tuple: the repaired message list and the count of synthesized rows inserted before the boundary snapshot.
3. Inside the repair function, iterate the fetched messages; for each assistant message carrying `tool_calls`, collect the `tool_call_id`s answered by the following contiguous `role="tool"` run, then synthesize a tool row for each un-answered id in `tool_calls` order.
4. Each synthesized row is shaped `{"role": "tool", "tool_call_id": <id>, "content": <marker constant>}` with an optional `"name"` copied from the answered run, so it conforms to the role-key whitelist.
5. Log a single warning through the module `logger` including the session id and the total synthesized-row count whenever the count is greater than zero.
6. In `restore_session`, pass the repaired list to the boundary computation instead of the raw fetched list, threading the synthesized-before-boundary count into `_boundary_to_index` as an additive offset.
7. Keep the existing clamp logic (lines 80-96) as the outer safety net; the repair offset only shifts the pre-clamp index.
8. Run the validation sequence (`routing.md`).

### Method

The current `restore_session` body (lines 47-105) fetches, computes the boundary from the raw fetched list, then calls `replace_history`. The repair sits between fetch and boundary:

```
fetch_messages(session_id)
        v
messages (raw DB rows, ordered by message_id)
        v
repair_orphan_tool_calls(messages, session_id, boundary_index=n_snapshot)
        v  -> repaired list, synthesized_before_boundary
_boundary_to_index(n_snapshot, repaired, insertions=synthesized_before_boundary)
        v
replace_history(repaired)   # sanitization/validation may still drop rows
        v
clamp undo_floor to live history length (existing lines 80-96)
```

Illustrative reference implementation (the boundary-offset accounting must be validated against `AC-004`):

```
INTERRUPTED_TOOL_CALL_MARKER = (
    "[interrupted] tool call did not complete before session termination"
)


def repair_orphan_tool_calls(messages, session_id, *, boundary_index=None):
    repaired = []
    synthesized_before = 0
    total_synthesized = 0
    i = 0
    n = len(messages)
    while i < n:
        msg = messages[i]
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            called_ids = [tc["id"] for tc in msg["tool_calls"]]
            j = i + 1
            answered = set()
            names = {}
            while j < n and messages[j].get("role") == "tool":
                answered.add(messages[j].get("tool_call_id"))
                names[messages[j].get("tool_call_id")] = messages[j].get("name")
                j += 1
            for tc_id in called_ids:
                repaired.append(messages[i])
                if tc_id not in answered:
                    row = {
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": INTERRUPTED_TOOL_CALL_MARKER,
                    }
                    extra = names.get(tc_id)
                    if extra is not None:
                        row["name"] = extra
                    repaired.append(row)
                    total_synthesized += 1
                    if boundary_index is not None and j <= boundary_index:
                        synthesized_before += 1
                i += 1
                continue
            i = j
            continue
        repaired.append(messages[i])
        i += 1
    if total_synthesized:
        logger.warning(
            "Session %s repaired %d orphaned tool call(s) at load",
            session_id,
            total_synthesized,
        )
    return repaired, synthesized_before
```

### Details

- **`REQ-001` / `AC-001` (detection):** the repair inspects every assistant row with `tool_calls`; an id is "answered" only if a following `role="tool"` message carries the same `tool_call_id`.
- **`REQ-002` / `AC-001` (synthesis):** missing ids are synthesized in `tool_calls` order, right after the last tool row of the run (or right after the assistant row when no run exists — the hard-kill crash case).
- **`REQ-003` / `AC-002` (log):** one warning per load with session id and synthesized-row count, emitted through the module `logger`.
- **`REQ-004` / `AC-003` (idempotency):** the helper is a pure function over the fetched list; no DB write occurs, so a second load reproduces identical output.
- **`REQ-005` / `AC-004` (boundary):** `_boundary_to_index` adds the synthesized-before-boundary count to its returned index; the existing clamp (lines 80-96) remains the outer guard.
- **`REQ-006` / `AC-005`:** `session_message_repo.py` and the turn write path are untouched.

## Compatibility considerations

- Additive: one new constant, one new module-level function, and a two-line integration in `restore_session`. `_boundary_to_index` gains an internal keyword-only parameter with a default, so no external caller breaks.

## Security considerations

- Synthesized rows are validated by the existing `replace_history` path (untrusted restore source); the marker is plain text content and introduces no new input surface.

## Rollback considerations

- Revert the file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/services/session_restore.py` | Unit: crafted orphaned-session fixture | `uv run pytest tests/agent/test_session_restore.py` | Paired history, idempotent, floor correct, warning logged |
| `scripts/agent/session_message_repo.py` (unchanged) | Regression | `uv run pytest tests/agent/test_session_message_repo.py` | Passes with zero changes to the file |
| Static + regression | mypy / ruff | `uv run mypy scripts/`, `uv run ruff check scripts/` | Clean |

## Completion criteria

- `restore_session` runs the repair between fetch and boundary, synthesizes missing tool rows with the marker constant, logs the warning, and adjusts the `undo_floor` index.
- `session_message_repo.py` is byte-identical.
- `mypy` / `ruff` pass.

## Out of Scope

- `scripts/agent/session_message_repo.py` (`REQ-006`, `AC-005`).
- Turn write-path changes (frozen turn001 Plan).
- Persisting synthesized rows to the DB.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the repair function + integrate into `restore_session` | Pending | — | — | REQ-001..REQ-005 |
| 2 | Add regression tests | Pending | — | — | Row 02 |
| 3 | Run validation sequence | Pending | — | — | mypy/ruff |
| 4 | Update state/persistence doc | Pending | — | — | Row 03 |

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
- **Requirement ID**: `REQ-001`..`REQ-006`
- **Source issue**: `issues/20261026-224729_turn002_repair-orphan-tool-call-rows.md`
- **Source plan**: `plans/20261027-071546_turn002_repair-orphan-tool-call-rows.md`
- **Generated at**: 20261027-110403
- **Related target files**: `scripts/agent/services/session_restore.py`
