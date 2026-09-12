# Filename Collision Retry Policy

Applies to any workflow step that writes a newly generated document to a path it computes
itself (a Plan, an Issue, or another generated artifact) and finds that the computed path
already exists.

## Collision Retry Bound

- An existing file MUST NOT be overwritten.
- Regenerate a disambiguated candidate path using the calling workflow's own naming
  scheme (e.g. a zero-padded sequence suffix, or a numeric suffix on an id/slug
  component) — this file does not define the disambiguation scheme itself, only the
  retry/stop behavior around it.
- Retry up to 3 times (per `AGENTS.md` Loop Prevention > Attempt Limit — this collision
  retry is an instance of that rule, not a separate bound).
- After 3 collisions, stop and report `Blocked: repeated filename collision — {path}`
  rather than continuing to increment.
