# Implementation: Add Future Event Envelope Subsection to types_and_protocols.md

## Goal

Add a "Future event envelope" subsection to the `ArtifactEvent` section in `docs/06_shared_02_types_and_protocols.md` so developers can see the planned extension direction alongside the current data-only definition.

## Scope

- `docs/06_shared_02_types_and_protocols.md` — insert a "Future event envelope" subsection after the existing ArtifactEvent Note (line 160)

Out of scope:
- Code changes
- `events.py` (already updated — docstring already contains envelope fields, step 1 done)
- `06_shared_90_inconsistencies_and_known_issues.md` (already updated — UNIMPL-01 marked RESOLVED, step 3 done)

## Assumptions

1. Steps 1 and 3 are already implemented (confirmed by grep).
2. The envelope field list in the plan matches what is already in `events.py` docstring (confirmed).
3. `timestamp` is already a current field of `ArtifactEvent`; the subsection should note this.
4. Insertion point is after line 160 (the Note blockquote) and before the `---` separator on line 162.

## Implementation

### Target file

`docs/06_shared_02_types_and_protocols.md`

### Procedure

1. Open the file at line 145 (start of `## 8. ArtifactEvent`).
2. After the Note blockquote (line 160) and before the `---` separator (line 162), insert the new subsection.

### Method

Insert a `### Future event envelope` subsection as a plain Markdown block with a field table. Mark fields clearly as aspirational/not implemented.

### Details

**Insertion point:** between line 160 and line 162 in `docs/06_shared_02_types_and_protocols.md`.

Insert:
```markdown
### Future event envelope (aspirational — not implemented)

These fields are reserved for a future event-bus layer. They are documented
in `shared/events.py` as design direction only. Do not assume they exist on
any current `ArtifactEvent` instance.

| Field            | Type | Purpose                                    |
|------------------|------|--------------------------------------------|
| `event_id`       | str  | UUID v7 — unique identifier per event      |
| `source`         | str  | Emitting module (e.g. `"mcp/github"`)      |
| `timestamp`      | str  | ISO-8601 UTC — already present as a field  |
| `correlation_id` | str  | Trace ID linking related events            |

When an event bus is implemented, these fields will be added to `ArtifactEvent`
and populated by the emitter before delivery to subscribers.
```

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Pre-commit | `pre-commit run --all-files` | pass |
| Manual review | Read the ArtifactEvent section end-to-end | "data-only now" and "envelope fields reserved" are both clear |
| Consistency | Compare field list with `events.py` docstring (lines 10-16) | `event_id`, `source`, `timestamp`, `correlation_id` match |
