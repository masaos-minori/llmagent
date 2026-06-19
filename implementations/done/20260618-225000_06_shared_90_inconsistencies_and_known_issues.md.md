# Implementation: ArtifactEvent Future Envelope — Known Issues Doc

## Goal

Verify UNIMPL-01 in `docs/06_shared_90_inconsistencies_and_known_issues.md` correctly references the future envelope design.

## Scope

- `docs/06_shared_90_inconsistencies_and_known_issues.md` — verify/update UNIMPL-01

## Assumptions

1. No substantive changes needed — UNIMPL-01 already mentions envelope fields and links to 06_shared_02.
2. The new "Future event envelope" subsection in 06_shared_02 (from the other impl doc) will make this reference accurate.

## Current State

### UNIMPL-01 (`06_shared_90_inconsistencies_and_known_issues.md:82-88`)

```markdown
### UNIMPL-01: `ArtifactEvent` has no event bus (RESOLVED)

- **Type:** Unimplemented (resolved)
- **Impact scope:** `shared/events.py::ArtifactEvent`
- **Description:** `ArtifactEvent` is a TypedDict with no delivery system, no consumers. Future event-envelope fields (`event_id`, `source`, `correlation_id`) are documented as aspirational in the module docstring and in [06_shared_02](06_shared_90_inconsistencies_and_known_issues.md).
- **Current safe interpretation:** Creating an `ArtifactEvent` instance triggers no action. It is a type annotation only.
- **Recommended action:** Complete. Future envelope design is documented; implementation is deferred.
```

**Assessment:** Already accurate. Mentions:
- Envelope fields (`event_id`, `source`, `correlation_id`)
- Links to 06_shared_02 for envelope design
- Status is "RESOLVED" with "implementation is deferred"

No changes needed to this file. The impl doc serves as verification that the existing content is correct.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Manual review | Read UNIMPL-01 | Mentions envelope fields, links to 06_shared_02 |
| Cross-reference | Check 06_shared_02 after other impl doc changes | Link resolves to actual future envelope subsection |
