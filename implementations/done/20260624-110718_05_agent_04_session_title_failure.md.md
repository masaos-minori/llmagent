# Implementation: Session Title Failure Behavior

## Goal

Document authoritative session title failure behavior in `05_agent_04` and add a SPEC entry in `05_agent_90`.

## Scope

**In:**
- `docs/05_agent_04_session_and_persistence.md` — add failure-behavior section
- `docs/05_agent_90_specifications_and_design_contracts.md` — add/update SPEC entry

**Out:** No code changes.

## Assumptions

1. Session title generation is a non-blocking LLM call.
2. Failure fallback: "Session {session_id[:8]}" or "Untitled" (to confirm from code).
3. All failure cases log at WARNING level.

## Implementation

### Target file

`docs/05_agent_04_session_and_persistence.md`, `docs/05_agent_90_specifications_and_design_contracts.md`

### Procedure

1. Grep for session title generation in agent code:
   ```bash
   grep -rn "session.*title\|title.*generat\|generate_title" agent/ --include="*.py" | head -20
   ```
2. Confirm fallback behavior from code.
3. Read `docs/05_agent_04_session_and_persistence.md` session title section.
4. Add/update failure-behavior documentation.
5. Read `docs/05_agent_90_specifications_and_design_contracts.md` to check for existing session title SPEC.
6. Add SPEC-SESSION-01 if not present.

### Method

Bash grep → Read docs → Edit patches.

### Details

**Failure behavior section for `05_agent_04`:**

```markdown
### Session Title Generation Failure Behavior

Session title is generated via an LLM call on the first turn.

| Failure case | Behavior | Log |
|---|---|---|
| LLM timeout | Fallback: `"Session {session_id[:8]}"` | WARNING |
| Empty / invalid response | Same fallback | WARNING |
| Title generation disabled | `title = None` (displayed as "Untitled") | INFO |
| API error | Same fallback; retried once | WARNING |

All failure cases are non-blocking. The session continues normally.
Fallback title is persisted to session storage.
```

**SPEC entry for `05_agent_90`:**

```markdown
### SPEC-SESSION-01: Session Title Generation
**Status:** Implemented
Session title is generated non-blocking on first turn. All failure modes use a deterministic fallback (`"Session {session_id[:8]}"`) — the session is never blocked by title generation failure.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Failure behavior documented | `grep -n "title.*fallback\|fallback.*title\|Untitled" docs/05_agent_04_session_and_persistence.md` | found |
| SPEC entry present | `grep -n "SPEC-SESSION-01\|session.*title.*spec" docs/05_agent_90_specifications_and_design_contracts.md` | found |
| No code changes | `git diff agent/` | empty |
