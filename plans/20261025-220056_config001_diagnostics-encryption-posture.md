# Plan: config001 diagnostics encryption posture

## Goal
- Record the owner's decision (Option B: formally accept the plaintext-with-redaction
  posture for `session_diagnostics`) as an explicit operational note in the agent
  diagnostics documentation, and point the repo config comment at that decision. No
  code or production-config change.

## Priority
Medium

## Scope
- **In-Scope**:
  - Add an accepted-posture operational note to
    `docs/23_agent/agent_09_01_data-layer-session-db.md`: decision (encryption remains
    disabled in production), the active defense layers (unconditional
    `_filter_sensitive_fields` redaction; `_SENSITIVE_PATTERNS` detection that raises
    `RuntimeError` and refuses the write when a key is unset and filtering succeeded;
    lazy 30-day purge), key-handling rules for any future Option A adoption (never
    committed, deployed config only), and the disposition of pre-existing rows.
  - Update the `[diagnostics]` comment block in `config/agent.toml` so the empty-key
    comment references the documented accepted posture.
- **Out-of-Scope**:
  - Enabling a Fernet key in any config (Option A was declined by the owner on
    2026-10-25). No key is generated, committed, or pasted anywhere (`skills/DESIGN.md`
    no-secrets rule).
  - Any change to `scripts/agent/diagnostic_store.py`, `save()`'s `encrypt=False`
    default, `_SENSITIVE_PATTERNS`/`_SENSITIVE_FIELDS`, or encryption of other tables.
  - `/opt/llm/config/agent.toml` (shared infrastructure; unchanged because Option B
    requires no production edit).
- **Dependencies**: N/A: none.

## Background
Review finding F-006: `DiagnosticStore` supports Fernet encryption, but every shipped
config sets `encryption_key = ""` and `save()` defaults to `encrypt=False`; no
production call site passes `encrypt=True` (verified: only tests use `encrypt=True`).
The posture existed only as a code default plus a config comment, with no endorsing
operational decision in `docs/`. The owner was presented both options with their
operational cost and selected Option B (accept plaintext-with-redaction).

## Problem
Whether plaintext diagnostic storage is accepted for production was unstated, and the
docs contain a factually stale claim: `agent_09_01` documents the encryption/retention
semantics but never states the accepted posture, the fail-closed guard, or the decision
record. The Issue itself also misdescribed the guard as persist-on-detection; the code
at HEAD `b0415bd3d` raises `RuntimeError` and blocks the write (`diagnostic_store.py:170-175`)
except when `_filter_sensitive_fields` itself failed. This correction is recorded in
this Plan, not by editing the Issue.

## Reason for Change
A security-relevant posture needs a decision implementers and operators can rely on.
With Option B chosen, the remaining work is documentation; without it, the posture
remains an implicit code default.

## Implementation Intent
Documentation-only: one accepted-posture note (with the corrected failure behavior) in
the session-DB diagnostics section, plus a pointer comment in the repo config. Existing
behavior is already the accepted posture, so no code aligns to the decision — the docs
align to the code.

## Requirements
- `REQ-001`: `docs/23_agent/agent_09_01_data-layer-session-db.md` records the posture
  decision: encryption deliberately disabled in production (as of 2026-10-25); defense
  layers as implemented; fail-closed `RuntimeError` on detected-sensitive content with
  no key (with the filter-failure carve-out); key-handling rule for any future adoption
  (out-of-band, never committed); residual risk stated (pattern detection is
  best-effort; filter-failure path persists unencrypted content).
- `REQ-002`: The disposition of pre-existing plaintext rows is stated: N/A — the
  production DB `/opt/llm/agent.db` contains no tables, so `session_diagnostics` has no
  stored rows (verified via `sqlite3 .tables`); future rows expire via the 30-day
  lazy purge.
- `REQ-003`: `config/agent.toml` `[diagnostics]` comment references the documented
  accepted posture; the key value stays `""` and no secret appears in any file.
- `REQ-004`: `DiagnosticStore` behavior is unchanged; its existing tests
  (redaction, purge, decrypt-on-read) pass unchanged, and docs checkers pass.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| docs/23_agent/agent_09_01_data-layer-session-db.md | Add the accepted-posture operational note (Known Issue style) to the diagnostics section | Only doc that documents `save()`/diagnostics semantics today; contains no posture decision record today | REQ-001, REQ-002 / AC-1, AC-2 | agent_09_01:64,68 document redaction/rotation but no posture; docs/00_index.md:152 maps "Session / DB persistence" to this doc | docs checkers (`check_docs_structure.py`) | Verified |
| config/agent.toml | Update the `[diagnostics]` comment block only | Comment should point implementers to the recorded posture instead of leaving the empty key as an unendorsed default | REQ-003 / AC-3 | config/agent.toml `[diagnostics]` block: comment + `encryption_key = ""`, `retention_days = 30` | none (comment-only; covered by REQ-004 suite run) | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/diagnostic_store.py | Ground truth for the note: unconditional redaction in `save()` (:160), fail-closed `RuntimeError` (:170-175), encrypt path (:178-179), read-side decrypt on `gAAAAA` prefix (:205-208), lazy purge | REQ-001, REQ-004 |
| docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | Already states `encryption_key` semantics accurately (:108, "empty string = encryption disabled"); verified it needs no change — keep scope minimal | REQ-001 |
| docs/23_agent/agent_10_05_operations-and-observability-monitoring.md | Lists `[diagnostics]` settings (:84) without posture claims; verified no change needed | REQ-001 |
| config/agent.toml | Current `[diagnostics]` block is the input to the comment edit | REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001): agent_09_01 contains a posture-decision section stating Option B,
  the defense layers, the corrected fail-closed behavior, key-handling rules, residual
  risk, and the decision date; contains no key material.
- `AC-2` (REQ-002): The section states the existing-rows disposition (no production
  rows exist; future rows expire via retention).
- `AC-3` (REQ-003): `config/agent.toml` `[diagnostics]` comment references the doc;
  `encryption_key = ""` unchanged; grep confirms no secret material in any changed file.
- `AC-4` (REQ-004): `uv run pytest tests/agent/test_diagnostic_store.py
  tests/agent/test_diagnostic_store_security.py -q` passes unchanged; docs checkers
  pass.

## Tests
- `REQ-004`: Run existing DiagnosticStore suites unchanged (tests/agent/test_diagnostic_store.py,
  tests/agent/test_diagnostic_store_security.py) — they already cover redaction,
  encrypt-on-save, no-key raise-on-sensitive behavior, and decrypt-on-read. No new
  tests: docs-and-comment-only change.

## Documentation Impact
Required and fully captured by the frozen target row: per `docs/00_index.md`'s
"Session / DB persistence" task mapping, the doc is
`docs/23_agent/agent_09_01_data-layer-session-db.md` (REQ-001). Verified no other agent
doc needs an update (agent_08_04:108 and agent_10_05:84 already describe the settings
without posture claims).

## Assumptions
- Option B is a posture decision for the current production environment, revisitable;
  the note states it as of 2026-10-25 so a future Option A adoption explicitly replaces
  the record.
- The repo config comment edit is acceptable for the deployed copy (deploy.sh syncs
  configs); a comment-only change carries no behavioral difference, and the deployed
  file already has the same empty key.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner decision: enable production encryption (Option A) or accept plaintext-with-redaction (Option B) | N/A — it was a decision, not an evidence gap | Resolved 2026-10-25: owner selected Option B after being presented both options with operational costs (Option A rejected: would additionally require `encrypt=True` at 3 production call sites because a key with `encrypt=False` skips the detection guard) | False (resolved) |
| UNK-02 | Disposition of already-stored plaintext rows within the retention window | Was: production row count unknown | Resolved by inspection: `/opt/llm/agent.db` has no tables (`.tables` empty) — `session_diagnostics` was never created; nothing to dispose of | False (resolved) |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| docs/23_agent/agent_09_01_data-layer-session-db.md | New docs subsection | Docs readers only | N/A: Path A skipped historical analysis | N/A: Path A skipped historical analysis | docs rsynced by deploy.sh; no new dependencies; no service restarts required |
| config/agent.toml | Comment-only edit | None (TOML comments inert) | N/A: Path A skipped historical analysis | N/A: Path A skipped historical analysis | Repo config rsynced to `/opt/llm/config/` — comment-only, no behavior change; no restarts required; production key value untouched |

## Design
No code design. Documentation placement rationale: the posture note belongs where
`save()` semantics are documented (agent_09_01, mapped by docs/00_index.md), not in the
config-reference docs, so implementers reading behavior docs see the decision. The
Issue's stale claim (persist-on-detection) is corrected plan-side only, per the
pipeline's Issue-immutability rule.

## Implementation steps

1. **Phase 1: Docs posture note**
   - [ ] Add the accepted-posture section to the diagnostics part of the doc, including the corrected fail-closed behavior and row disposition (REQ-001, REQ-002; docs/23_agent/agent_09_01_data-layer-session-db.md)
2. **Phase 2: Config comment**
   - [ ] Update the `[diagnostics]` comment to reference the documented posture; key stays `""` (REQ-003; config/agent.toml)
3. **Phase 3: Verification**
   - [ ] Run docs checkers on the changed doc (REQ-004; docs/23_agent/agent_09_01_data-layer-session-db.md)
   - [ ] Run `uv run pytest tests/agent/test_diagnostic_store.py tests/agent/test_diagnostic_store_security.py -q` (REQ-004; docs/23_agent/agent_09_01_data-layer-session-db.md)
   - [ ] Deployment validation: doc and config comment are rsynced by deploy.sh; no key material introduced anywhere; no service restart required (REQ-003; config/agent.toml)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/23_agent/agent_09_01_data-layer-session-db.md | Docs gate | `uv run python tools/check_docs_structure.py` + fast gate `manage_frontmatter` (add-missing) | Pass |
| config/agent.toml | No-secret + inertness check | `grep -n "encryption_key" config/agent.toml` | `encryption_key = ""` unchanged; no key material in repo diff |
| scripts/agent/diagnostic_store.py (unchanged) | Regression (existing suites) | `uv run pytest tests/agent/test_diagnostic_store.py tests/agent/test_diagnostic_store_security.py -q` | all pass unchanged |

## Risks
- **Risk**: A future implementer reads "posture accepted" and adds sensitive payload
  types beyond `_SENSITIVE_FIELDS` coverage, relying on best-effort pattern detection.
  → **Mitigation**: the note explicitly states the residual risk and the filter-failure
  carve-out (that path persists unencrypted content), and requires updating the decision
  record if the posture is revisited.
- **Risk**: Docs drift if Option A is later adopted. → **Mitigation**: the note is dated
  (2026-10-25) and names Option A's preconditions (deployed-only key + `encrypt=True` at
  call sites), making the replacement edit explicit.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add posture note to agent_09_01 | Pending | — | — | Phase 1 |
| 2 | Update config/agent.toml [diagnostics] comment | Pending | — | — | Phase 2 |
| 3 | Docs checkers + DiagnosticStore suites + deploy check | Pending | — | — | Phase 3 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: owner decision obtained 2026-10-25 (Option B); former blocker UNK-01 resolved | Yes | 20261025 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261025-210357_config001_diagnostics-encryption-posture.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-220056
- **Related target files**: docs/23_agent/agent_09_01_data-layer-session-db.md, config/agent.toml

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes item 3 / Documentation Impact; owner decision 2026-10-25; code ground truth diagnostic_store.py:160-208 | docs/23_agent/agent_09_01_data-layer-session-db.md | Phase 1 | AC-1 | Validation plan row 1 | Explicit in issue |
| REQ-002 | Issue Required Changes item 4 / Unresolved Questions; resolved by `/opt/llm/agent.db` inspection | docs/23_agent/agent_09_01_data-layer-session-db.md | Phase 1 | AC-2 | Validation plan row 1 | Derived from confirmed evidence |
| REQ-003 | Issue Target Files item 1 (repo-side posture documentation) | config/agent.toml | Phase 2 | AC-3 | Validation plan row 2 | Explicit in issue |
| REQ-004 | Issue Constraints / Acceptance Criteria (no behavior regression) | docs/23_agent/agent_09_01_data-layer-session-db.md | Phase 3 | AC-4 | Validation plan row 3 | Explicit in issue |
