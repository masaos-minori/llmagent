# prompts/05_skills.md restates a stale copy of the canonical dependency-direction diagram

## Priority
Medium

## Summary
`prompts/05_skills.md`'s `### Architectural Principles` section restates the
repository's layer dependency-direction diagram in full, in violation of
`skills/DESIGN.md`'s explicit instruction that the canonical diagram lives only
in `rules/env.md` Architecture and must not be restated elsewhere. The restated
copy is also stale: it omits the `eventbus` layer's full isolation rule and the
"installer use only" qualifier on `agent`'s dependency on `mcp_servers`, both of
which the canonical source documents.

## Background
This issue was discovered while investigating a separate, narrower consolidation
task scoped to `prompts/05_skills.md`'s internal sections (`### Architectural
Principles`, `### Normative vs. Descriptive Content`, `### Canonical
References`, compared against `### Canonical Ownership Model` and
`### Deduplication Rules`). That investigation found no confirmed duplicate
among those specific comparisons, but surfaced this separate, more concrete
finding involving a file outside that investigation's scope
(`rules/env.md`), which is filed here instead of folded into the original task.

## Problem
`prompts/05_skills.md`, `### Architectural Principles`, "dependency direction"
bullet, currently states:

    Apply this direction: `agent -> rag/mcp -> db -> shared`. The arrow means
    "may depend on or reference".
    - `agent` may reference `rag`, `mcp`, `db`, and `shared`.
    - `rag` and `mcp` may reference `db` and `shared`.
    - `db` may reference `shared`.
    - `shared` must not reference higher layers.
    - A lower layer must not reference a higher layer.
    - `rag` and `mcp` are sibling layers.
    - `rag` and `mcp` must not reference each other unless an approved rule
      explicitly allows it.

`rules/env.md`, `## Architecture`, currently states (confirmed by direct read):

    shared  -> external only (leaf layer, no dependency on other layers)
    db      -> shared
    rag     -> db, shared
    mcp_servers -> db, shared
    agent   -> rag, db, shared, mcp_servers (installer use only)
    eventbus -> fully independent of every other layer (not even a dependency
                on shared)

`skills/DESIGN.md`'s `### Import layer contract` section states: "The canonical
layer diagram lives in `rules/env.md` Architecture (includes the current
`eventbus` isolation rule and `agent`'s actual scope) — do not restate or
re-derive the diagram here." `prompts/05_skills.md` restates the diagram anyway,
and the restated version is missing two things the canonical source documents:
the `eventbus` layer entirely, and the "installer use only" qualifier on
`agent -> mcp_servers`.

## Reason for Change
- Direct violation of `skills/DESIGN.md`'s explicit "do not restate or
  re-derive the diagram here" instruction — `prompts/05_skills.md` is exactly
  the kind of restatement that instruction was written to prevent.
- Documentation drift risk: the restated copy has already drifted (missing
  `eventbus`'s isolation rule and the `agent`/`mcp_servers` "installer only"
  qualifier). Anyone reading only `prompts/05_skills.md` gets an incomplete
  picture of the actual dependency contract.
- Maintenance risk: two independent copies of the same architectural contract
  must be kept in sync by hand; this issue's own discovery shows that
  synchronization has already failed once.

## Implementation Intent
Replace `Architectural Principles`' "dependency direction" bullet's inline
diagram with a short statement of the rule plus a reference to `rules/env.md`
Architecture as the canonical source, consistent with `skills/DESIGN.md`'s
`### Import layer contract` section (which already does this correctly — it
states the rule exists and points to `rules/env.md` without restating the
diagram). Keep the general principle statement ("a lower layer must not
reference a higher layer") since it is the operative constraint this workflow
needs to apply; remove the specific layer names/arrows and the sibling-layer
detail, since those belong solely to `rules/env.md`.

## Target Files or Areas
- `prompts/05_skills.md` — `### Architectural Principles`, "dependency
  direction" bullet
- `rules/env.md` — `## Architecture` (read-only reference; not modified by this
  issue)
- `skills/DESIGN.md` — `### Import layer contract` (read-only reference; not
  modified by this issue, cited as the precedent pattern to follow)

## Required Changes
- Rewrite `Architectural Principles`' "dependency direction" bullet to state
  the general constraint (lower layers must not reference higher layers) and
  reference `rules/env.md` Architecture for the specific layer diagram, instead
  of restating the diagram inline.
- Verify no other bullet in `Architectural Principles` depends on the removed
  layer-name detail (e.g. the "rag and mcp are sibling layers" statement) —
  if any downstream section within `prompts/05_skills.md` relies on that detail
  being spelled out locally, keep only the minimum needed and still reference
  `rules/env.md` for the authoritative list.

## Constraints
- Must not change the actual dependency-direction rule itself (no architectural
  redesign) — this is a documentation-consolidation fix, not a policy change.
- Must not edit `rules/env.md` or `skills/DESIGN.md` — they are the reference
  targets, already correct.

## Acceptance Criteria
- `Architectural Principles` no longer restates the specific layer names or
  arrows from the dependency-direction diagram.
- `Architectural Principles` retains the general principle ("a lower layer must
  not reference a higher layer") and adds a reference to `rules/env.md`
  Architecture in the `### Canonical References` format already defined in the
  same file.
- No content unique to `prompts/05_skills.md`'s restated diagram (if any is
  found not to exist in `rules/env.md`) is silently dropped without being
  either preserved or explicitly flagged as a `rules/env.md` gap.

## Testing Expectations
Not required in the automated-test sense (Markdown-only change, no executable
code path). Manual verification expected: diff review confirming the general
principle survives, the reference resolves correctly, and no other section of
`prompts/05_skills.md` depended on the removed layer-name detail.

## Documentation Impact
This issue is itself a documentation consolidation, correcting a drifted
restatement to bring `prompts/05_skills.md` back into compliance with
`skills/DESIGN.md`'s `### Import layer contract` rule. No `docs/*.md` file is
affected.

## Out of Scope
- Any change to `rules/env.md`'s or `skills/DESIGN.md`'s content.
- Any change to the actual dependency-direction policy.
- The separate consolidation task this issue was discovered during (comparison
  among `Architectural Principles`, `Normative vs. Descriptive Content`, and
  `Canonical References`) — that investigation found no confirmed duplicate and
  is closed independently of this issue.

## Dependencies
N/A: none — this issue is self-contained and does not depend on any other
currently-filed issue or plan.

## Unresolved Questions
- Does any other file in the repository also restate this diagram (beyond
  `prompts/05_skills.md`)? Not checked as part of this issue's discovery; a
  repository-wide search (`rg` for the arrow notation or layer names together)
  should be run during implementation to confirm `prompts/05_skills.md` is the
  only offender.

## AI Implementation Instruction
- Do not rewrite `prompts/05_skills.md` from scratch; edit only the
  "dependency direction" bullet under `### Architectural Principles`.
- Do not edit `rules/env.md` or `skills/DESIGN.md`.
- Preserve the general principle; replace only the specific, restated diagram
  detail with a reference.
- Run a repository-wide search for other restatements of this diagram before
  closing, per Unresolved Questions above, and file a follow-up issue for any
  additional occurrence found rather than fixing it inline in this same change.
- Stop and report back if `rules/env.md`'s Architecture section content no
  longer matches what is quoted in this issue's Problem section (it may have
  changed since this issue was filed).
