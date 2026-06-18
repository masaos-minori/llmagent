# Implementation: ArtifactEvent Future Envelope — Types Doc

## Goal

Add "Future event envelope" subsection after the ArtifactEvent section in `docs/06_shared_02_types_and_protocols.md`.

## Scope

- `docs/06_shared_02_types_and_protocols.md` — add subsection after line 161

## Assumptions

1. `scripts/shared/events.py` already documents future envelope fields in its module docstring (lines 10-16).
2. UNIMPL-01 in `06_shared_90_inconsistencies_and_known_issues.md` already references these fields but links to 06_shared_02 which lacks the subsection.

## Current State

### ArtifactEvent section (`06_shared_02_types_and_protocols.md:145-161`)

```markdown
## 8. `ArtifactEvent` (`shared/events.py`)

```python
class ArtifactEvent(TypedDict, total=False):
    event_type: str   # "artifact.updated" | "artifact.created" | "artifact.deleted"
    repo: str         # "owner/repo"
    branch: str
    commit: str       # commit SHA or empty string
    path: str         # file path or empty string
    pr_number: int    # PR number or 0
    session_id: int
    timestamp: str    # ISO-8601 UTC
```

> **Note:** `ArtifactEvent` is a data definition only. No event bus is implemented.
> See [06_shared_90 UNIMPL-01](06_shared_90_inconsistencies_and_known_issues.md).

---

## 9. `ShellPolicy` (`shared/protocols/shell.py`)
```

**Gap:** No "Future event envelope" subsection between lines 161 and 163. UNIMPL-01 references 06_shared_02 for envelope design but the subsection doesn't exist yet.

### Module docstring (`scripts/shared/events.py:10-16`)

```python
Future event-envelope fields (aspirational, not implemented):
    event_id: str        # UUID v7
    source: str          # module name (e.g. "mcp/github")
    timestamp: str       # ISO-8601 UTC (already present)
    correlation_id: str  # trace ID linking related events
These fields are documented here as design direction only; they are not required
and must not be assumed to exist on any event instance.
```

Already complete — no changes needed.

## Proposed Changes

### `docs/06_shared_02_types_and_protocols.md` after line 161

Insert a new subsection before the `---` separator:

```markdown
> **Note:** `ArtifactEvent` is a data definition only. No event bus is implemented.
> See [06_shared_90 UNIMPL-01](06_shared_90_inconsistencies_and_known_issues.md).

### Future event envelope (aspirational)

The following fields are reserved for a future event-bus implementation. They are
NOT part of the current `ArtifactEvent` type and MUST NOT be assumed to exist on
any event instance produced today.

| Field | Type | Description |
|---|---|---|
| `event_id` | `str` | UUID v7 unique identifier for the event |
| `source` | `str` | Module name that produced the event (e.g. `"mcp/github"`) |
| `timestamp` | `str` | ISO-8601 UTC timestamp (already present in current type) |
| `correlation_id` | `str` | Trace ID linking related events across modules |

These fields are documented as design direction only. Implementation is deferred.
See [06_shared_90 UNIMPL-01](06_shared_90_inconsistencies_and_known_issues.md).

---
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Manual review | Read updated doc | Future envelope subsection is present, clearly marked aspirational |
| Cross-reference | Check UNIMPL-01 in 06_shared_90 | Links to 06_shared_02 now resolve to actual content |
