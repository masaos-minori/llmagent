# Implementation Procedure: `scripts/rag/pipeline.py` (RAGCORPUS001 Phase 3)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-003, REQ-004, REQ-009)

## Goal
Insert the fallback identity gate: before a remote-to-local fallback is accepted,
compare remote identity against local identity; apply policy (`reject` default /
`degraded` by explicit config); record the corpus generation used on every accepted
result.

## Scope
- `class RagPipeline` `:55`; stage status `Literal["success","fallback","failure"]`
  `:128`/`:156`; `fallback_reason=stage_reason` `:167`; `async def augment` `:197` with
  the documented fallback conditions in its docstring `:213-222`; HTTP dispatch calls
  `self._augment_refiner.run_http_augment(...)` `:245`.
- Auth-error rule to preserve verbatim: HTTP 401/403 → `RagPipelineError`, fail closed,
  no fallback (docstring `:216-217`; ADR-010 INV-03..05). The gate must not touch this
  path.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `_identity_gate(remote_identity, local_identity) -> GateDecision` (new): pure decision
  helper — inputs are `CorpusIdentity`-shaped values (remote side may be `None` when the
  server predates identity exposure); returns accept / reject(reason) / accept-degraded.
  Missing identity on either side = unverifiable = reject (REQ-003, Risk `:227`).
- Policy lookup `rag_identity_mismatch_policy` (config key from doc 14; values `reject`
  default, `degraded` only by explicit approval). Loaded once at pipeline construction
  via the existing config access pattern; no per-request file reads.
- On reject: return the failure stage status with reason `identity_mismatch` (new
  reason string) through the existing `fallback_reason` channel `:167`; nothing is
  re-executed. On accept (identities match): existing local re-execution proceeds
  unchanged (INV-05 preserved); status stays `fallback`. On `degraded` policy mismatch:
  local re-execution proceeds, status `fallback`, and the result is marked degraded via
  doc 12's field, logged with both identities' `corpus_id`s (hashes/ids only — no
  secrets).
- Every accepted result records `corpus_generation` (the generation of the corpus that
  produced the served content) via doc 12 (REQ-004).
- `scripts/rag/stages/augment.py` is Reference Files only — read its wiring, do not
  edit.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Add the gate call at the point where a fallback-triggering outcome is decided
   (between `:245` result inspection and local re-execution), keeping auth-error
   short-circuit earlier and untouched.
2. Keep `_get_stage_status` `:126` and all public signatures; the gate is additive.

## Compatibility considerations
**Dependencies**:
- Upstream: docs 01/06 (local identity), 09/10/11 (remote identity plumbing), 12
**Blocks**: docs 16, 18

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/rag/test_rag_http_mode.py` (doc 16 integration matrix).

## Completion criteria
- No silent mismatched fallback; auth-error behavior byte-identical (regression test in
  doc 16); `get_diagnostics` `:296` output carries the generation field.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Completed | 20261030-140156 | 20261031-131124 | Anchors re-verified against current source (pipeline.py augment/get_diagnostics, corpus_identity, diagnostics, models_result). |
| 2 | Apply the Implementation procedure | Completed | 20261030-140156 | 20261031-131130 | Implemented additive fallback identity gate: _identity_gate pure helper, _local_identity (lazy, read from meta table), gate call in augment() fallback path, corpus_generation + identity_degraded surfaced via get_diagnostics post-process. |
| 3 | Run the Validation plan gates | Completed | 20261030-140156 | 20261031-131136 | Gates passed: pytest tests/rag (615 incl. test_rag_http_mode 4) / mypy 448 files / ruff 0 / bandit pre-existing-only. User-approved gate semantics (reject/degraded only when both present+unequal) preserves fallback; test_in_process_fallback_sets_result_source_fallback green. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_01_scripts_rag_corpus_identity.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Post-archive refactor (module-size gate)

The gate logic below was extracted from `scripts/rag/pipeline.py` into a dedicated
leaf module `scripts/rag/identity_gate.py` after this procedure was archived, to keep
`pipeline.py` under the `check_module_size` gate (was 21443 B > 20480 B after the
additive gate; now 17669 B). Moved: `_META_TABLE`, `GateDecision`, `_identity_gate`,
`_safe_corpus_id`, and the lazy `_local_identity` (now `compute_local_identity(db,
*, schema_version)`). `SCHEMA_VERSION` stays in `pipeline.py` (doc 08 target file).

- Fixed a latent bug uncovered by direct unit tests (`tests/rag/test_identity_gate.py`):
  `GateDecision.reject` originally returned `not self.proceed`, which is also `True`
  for a `degraded` mismatch. Since the pipeline checks `if gate.reject: return ""`
  before `if gate.degraded`, the `degraded` policy was unreachable. `reject` now reads
  `not self.proceed and self.reason != "identity_degraded"`, matching the design above
  (degraded mismatch proceeds to local re-execution and marks the result degraded).
  Dormant today — the fallback path carries `remote_identity=None` always — so no
  existing test exercised it.

- `(new)` markers applied: `_identity_gate`, `identity_mismatch` (Contract section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-004, REQ-009
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 08
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/rag/pipeline.py`