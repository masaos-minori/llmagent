## Goal

Document the token-uniqueness invariant and the `load_config()` mapping pass-through / type-normalization / missing-vs-empty semantics in ADR-013, and close the EVENTBUS-020 known deviation (`REQ-003`, `REQ-005`).

## Scope

- Modify `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` only: add the token-uniqueness invariant, record the mapping pass-through and missing-vs-empty semantics, and convert the EVENTBUS-020 Known Deviations entry to Resolved.
- Do not modify source code or any other document here — the `config.py` / `auth.py` changes are the sibling procedures. This document only records what they implement (`REQ-003`, `REQ-005`).

## Assumptions

- The ADR currently lists EVENTBUS-020 as an open Known Issue at line 231; the Invariants section runs lines 169-177; Decision Details #1 is line 65 and #3 is line 74.
- Every symbol this procedure names already exists: `load_config`, `EventBusConfig`, `_populate_token_maps`, `_TOKEN_PRINCIPAL_MAP` appear in the ADR or the repository; the invariant IDs `INV-01`..`INV-08` and `EVENTBUS-020` are hyphenated tracking identifiers, not Python symbols.

## Design decisions

- **Add a dedicated invariant.** Record token uniqueness as a new `INV-08` after the last existing invariant (line 177) rather than rewriting INV-02/INV-07, keeping the change additive and the numbering stable.
- **Close the deviation explicitly.** Convert the EVENTBUS-020 Known Deviations entry (line 231) from an open Known Issue to a Resolved entry citing `REQ-003` / `REQ-005`.

## Alternatives considered

- Rewriting the five-role model (Decision Details #1/#2) to fold uniqueness in — rejected: the role model is unchanged; only its documentation of token uniqueness and mapping pass-through needs recording.

## Implementation

### Target file

`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure

Make four prose edits to the ADR. Each inserts or rewrites text only — no code, no import statements, no new configuration keys.

1. **Invariants** — after the last existing invariant at line 177, insert one new invariant documenting token uniqueness:

```
- INV-08: Each configured token MUST hold exactly its documented role set. Two distinct token fields sharing a non-empty value MUST be rejected before startup, naming the colliding fields and never logging the values.
```

2. **Decision Details #1** (line 65) — append to the end of the "Authentication mechanism" bullet, after "...resolved from which configured token it presented, not merely from having presented a valid token.", a sentence recording that duplicate non-empty token values are rejected before startup (naming the colliding fields, never the values) and that `load_config()` carries `consumer_authorization` and `topic_authorization` through to `EventBusConfig`, normalizing `topic_authorization` values to `set[str]` and leaving `consumer_authorization` values as `list[str]`.

3. **Decision Details #3** (line 74) — append a clause stating that a missing required mapping still raises while an empty mapping stays deny-all, distinct from a missing mapping.

4. **Known Deviations** (line 231) — replace the EVENTBUS-020 line with a Resolved entry:

```
- **Resolved**: EVENTBUS-020 — resolved by REQ-003 and REQ-005: `load_config()` now passes the authorization mappings through and normalizes their types, and `_populate_token_maps()` rejects duplicate non-empty token values before the maps are built.
```

### Method

The four edits above. Edit 1 appends `INV-08` after line 177; edit 4 rewrites line 231. All inserted text is Markdown prose — no Python, no import statements, no new configuration keys.

### Details

- Edit 2's normalization note matches the `EventBusConfig` annotations (`dict[str, set[str]]` / `dict[str, list[str]]`) that `REQ-002` enforces; it documents the runtime result, it does not change parsing.
- Edit 3 preserves the existing deny-all statement (line 74 already says an empty mapping resolves to deny-all) and adds the missing-mapping-raises side.
- Edit 4 keeps the `EVENTBUS-020` identifier (a hyphenated tracking ID, not a symbol) so the governance cross-reference in `governance_03` stays valid.

## Compatibility considerations

- N/A: documentation-only edit to an accepted ADR; no code, API, or configuration change.

## Security considerations

- The recorded `INV-08` and the closed EVENTBUS-020 make the fail-closed token-uniqueness and mapping-semantics guarantees explicit in the security-boundary ADR (`REQ-003`, `REQ-005`). No secret or token value is introduced.

## Rollback considerations

- N/A: revert the four ADR prose edits (restore the original Known Deviations entry and remove `INV-08`).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | stale_detector: cited ADR line numbers (65, 74, 169-177, 231) and symbols (`load_config`, `_populate_token_maps`) still resolve | `uv run python tools/stale_detector.py implementations/20261025-140926_08_docs_adr_02_04_013_eventbus-authentication-authorization_md.md` | not stale |
| this procedure document | structure: every implementation-procedure section present | `uv run python tools/check_workitem_structure.py --file implementations/20261025-140926_08_docs_adr_02_04_013_eventbus-authentication-authorization_md.md` | no findings |

## Completion criteria

- `INV-08` is present in the Invariants section and states one-role-per-token plus duplicate rejection (`REQ-003`).
- Decision Details documents `load_config()` mapping pass-through and `topic_authorization` -> `set[str]` / `consumer_authorization` -> `list[str]` normalization (`REQ-002`).
- The missing-required-mapping-raises vs empty-mapping-deny-all distinction is recorded (`REQ-005`).
- The EVENTBUS-020 Known Deviations entry is converted to Resolved (`REQ-003`, `REQ-005`).

## Out of Scope

- The `config.py` mapping pass-through and type normalization — handled by the sibling procedure for `scripts/eventbus/config.py` (`REQ-001`, `REQ-002`).
- The `_populate_token_maps()` duplicate rejection and one-role-per-token binding — handled by the sibling procedure for `scripts/eventbus/auth.py` (`REQ-003`, `REQ-004`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the four ADR prose edits described in Implementation > Procedure/Method/Details | Completed | 20261026 | 20261026 | INV-08 inserted; Decision Details #1/#3 appended; EVENTBUS-020 -> Resolved |
| 2 | Run the documentation checkers (`rules/toolchain.md`) | Completed | 20261026 | 20261026 | stale_detector: not stale; check_workitem_structure: no findings |

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
- **Requirement ID**: `REQ-003` (token uniqueness / duplicate rejection), `REQ-005` (missing-vs-empty semantics)
- **Source issue**: `issues/20261023-154326_eventbus002_config-authorization-token-roles.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-101136_eventbus002_config-authorization-token-roles.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-140926
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
