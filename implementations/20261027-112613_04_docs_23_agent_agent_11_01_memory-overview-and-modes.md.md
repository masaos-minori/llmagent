## Goal

Add an additive subsection to the existing memory-layer overview `docs/23_agent/agent_11_01_memory-overview-and-modes.md` documenting the per-turn memory-injection degraded state this Plan introduces (REQ-005 / AC-005). The subsection states when the degraded state appears, that injection is retried automatically on every user prompt, and that the user sees one warning per degradation period. It is placed so it is clearly distinguished from the existing *Degraded mode* (embedding circuit-breaker) discussion.

## Scope

- **In-Scope** (`docs/23_agent/agent_11_01_memory-overview-and-modes.md` only):
  - Insert one new subsection under the Memory Modes area describing the injection-failure degraded state (appearance, per-turn automatic retry, one-warning-per-period signal).
  - Preserve the front matter, existing headings, cross-references, and the *Degraded mode* table.
- **Out-of-Scope**:
  - The flag bookkeeping (`scripts/agent/conversation_state_manager.py`; row 01).
  - The field-comment update (row 02) and the regression module (row 03).

## Assumptions

- The doc is an existing canonical source under `docs/23_agent/`; edits must preserve its front matter and heading hierarchy.
- The degraded state documented here is the per-turn injection-failure latch, which is a different condition from *Degraded mode (circuit open)* in the modes table (an embedding-service failure), and must not be conflated with it.
- Content policy forbids implementation-detail warnings that point away from a canonical source; the subsection stays at the architectural-contract level and references the slash-command status path rather than internal flags.

## Design decisions

- **Additive subsection, no rewrite.** Insert the new subsection between the mode-transitions list and the existing *Implementation Note: Persistence Order and Failure Handling for `on_session_stop`*, so it sits with the mode/failure discussion without altering any existing section.
- **Explicit disambiguation.** The subsection opens by distinguishing itself from *Degraded mode* to prevent reader confusion between injection failure and embedding circuit-breaker trips.
- **Contract-level language.** State the observable behavior (when it appears, automatic recovery, user-visible signal) without embedding method names, line numbers, or flag internals.

## Alternatives considered

- **New standalone doc.** Rejected: `docs/23_agent/agent_00_document-guide.md` maps memory chapter 11 to this file; the injection-degraded note belongs with the existing memory-mode discussion, not as a sibling.
- **Fold it into the Degraded mode row.** Rejected: that row describes the embedding circuit breaker; merging would conflate two distinct conditions.

## Implementation

### Target file

`docs/23_agent/agent_11_01_memory-overview-and-modes.md` (existing; extended)

### Procedure

1. Open `docs/23_agent/agent_11_01_memory-overview-and-modes.md` and locate the end of the *Transitions between modes* list (the last bullet before the *Implementation Note: Persistence Order and Failure Handling for `on_session_stop`* heading).
2. Insert a new `###` subsection titled **Memory Injection Failure (Per-Turn Degraded State)** between that list and the *Implementation Note* heading.
3. Write the subsection to cover exactly three points: (a) when it appears — any turn whose memory-injection call raises; (b) automatic recovery — injection retries on every subsequent user prompt and a successful attempt (including an empty result) clears the state; (c) the user-visible signal — one warning per degradation period, with persistent failures staying quiet on later turns.
4. Open the subsection with one sentence distinguishing it from *Degraded mode* (embedding circuit breaker) so the two are not conflated.
5. Run the doc validation sequence (`routing.md`).

### Method

The current doc orders the Memory Modes area as: the modes table, *Conditions for each mode*, *Transitions between modes*, then *Implementation Note: Persistence Order and Failure Handling for `on_session_stop`*. The new subsection slots between the transitions list and that Implementation Note, preserving the existing hierarchy.

Proposed subsection text (adapt wording; keep it contract-level):

```
### Memory Injection Failure (Per-Turn Degraded State)

This degraded state is distinct from Degraded mode above: it reports a failed
memory-injection call, whereas Degraded mode reports an embedding circuit-breaker
trip during retrieval.

- When it appears: any user prompt whose memory-injection call raises (network
  error, timeout, or backend failure). The state is tracked per turn, not held
  for the whole session.
- Automatic recovery: memory context is retrieved and injected on every user
  prompt with no manual intervention; a successful attempt (including one that
  returns no snippets) clears the state on the next turn.
- User-visible signal: the state is surfaced once per degradation period - a
  single warning on the failing turn and on the recovery turn. Persistent
  failures stay quiet on later turns instead of logging every turn.
```

### Details

- **`REQ-005` / AC-005:** the subsection states the appearance condition, the per-turn automatic retry, and the one-warning-per-degradation-period signal.
- **Backward compatibility:** the modes table, conditions, transitions, and all existing sections are unchanged; the new subsection is purely additive.

## Compatibility considerations

- Additive subsection; front matter, headings, and existing cross-references preserved. No change to sibling docs.

## Security considerations

- Documentation-only; no new input surface or secret handling.

## Rollback considerations

- Revert the doc edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| structural integrity | Format / headings / fences / front matter | `uv run python tools/check_docs_quality.py` | Clean |
| structure | File size, H1 count, front matter, Related Docs, link reachability | `uv run python tools/check_docs_structure.py docs/23_agent/agent_11_01_memory-overview-and-modes.md` | Clean |
| content policy | No implementation-detail warnings pointing away from canonical source | `uv run python tools/check_docs_content_policy.py --strict` | Clean |
| domain consistency | Doc claims match `scripts/` and `config/agent.toml` | `uv run python tools/check_docs_consistency.py --domain agent` | Clean |

## Completion criteria

- The doc has an additive "Memory Injection Failure (Per-Turn Degraded State)" subsection covering appearance, per-turn automatic retry, and the one-warning-per-period signal, clearly distinguished from Degraded mode.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, and `check_docs_consistency.py --domain agent` all pass clean.

## Out of Scope

- Flag bookkeeping (`scripts/agent/conversation_state_manager.py`, row 01).
- Field comments (row 02).
- The regression module (row 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Flag bookkeeping (row 01) | Pending | — | — | Dependency |
| 2 | Regression module (row 03) | Pending | — | — | Dependency |
| 3 | Validation sequence | Pending | — | — | Doc checkers |
| 4 | Add degraded-state section to the memory overview doc | Pending | — | — | This row |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261026-224838_memory001_retry-memory-injection-failure.md`
- **Source plan**: `plans/20261027-072306_memory001_retry-memory-injection-failure.md`
- **Generated at**: 20261027-112613
- **Related target files**: `docs/23_agent/agent_11_01_memory-overview-and-modes.md`
