## Goal

Correct `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`'s Note (section 4.3) about `fetch_result` staleness in HTTP mode — replace the disconfirmed "`self.run()` not called" claim with the actual callback-based update mechanism and its one genuine staleness condition (empty `selected_hits`) (REQ-001).

## Scope

- Rewrite the Note at `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` section 4.3 to accurately describe the current `last_fetch_result` update mechanism and its one genuine staleness condition

## Assumptions

- The callback wiring at `pipeline.py:119` (`set_fetch_result=lambda fr: setattr(self, "last_fetch_result", fr)`) remains the current mechanism
- The `_forward_fetch_result()` guard at `augment.py:102-110` (`if selected_hits:`) remains the current staleness condition boundary
- `AugmentRefiner._last_fetch_result` is never reassigned anywhere in the class (confirmed via `grep -n "_last_fetch_result" scripts/rag/augment.py` — only `__init__` initialization and property getter exist)
- No other documentation file repeats this same disconfirmed claim about `_run_http_augment()`/`self.run()`

## Design decisions

1. Correct the Note rather than leave it as a "resolved, no action needed" dead issue — an inaccurate Note actively misleads future readers/investigators
2. Do not remove the dead-code re-check in `RagPipeline.augment()` (`pipeline.py:298-301`) as part of this Plan — it is harmless (never executes its body) and unrelated to the documentation's accuracy

## Alternatives considered

1. Leaving the Note as-is since the underlying code behavior is correct — rejected because an inaccurate Note actively misleads future readers/investigators
2. Implementing either of the Issue's Recommended Action options (update `fetch_result` before returning from `_run_http_augment()`, or adding a separate HTTP-mode-specific diagnostic field) — rejected because both are premised on a bug that does not exist per re-verification

## Implementation

### Target file

`docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`

### Procedure

1. Re-confirm the callback chain and staleness condition before writing the corrected Note
2. Replace the Note at line 85 with corrected text describing the callback-based update mechanism and the empty-`selected_hits` staleness condition

### Method

Phase 1: Preparation — confirm evidence line numbers
- Re-confirm `pipeline.py:119`'s callback wiring and `augment.py:102-110`'s `if selected_hits:` guard are still current before writing the corrected Note (REQ-001; `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`)

Phase 2: Core Logic — rewrite the Note
- Replace the Note at line 85 with corrected text describing the callback-based update mechanism and the empty-`selected_hits` staleness condition (REQ-001; `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`)

### Details

**Phase 1:** Verify via grep/read that:
- `pipeline.py:119` still contains: `set_fetch_result=lambda fr: setattr(self, "last_fetch_result", fr)`
- `augment.py:102-110` still contains: `def _forward_fetch_result(self, selected_hits: list[dict[str, Any]]) -> None:` with `if selected_hits:` guard at line 104
- `augment.py:66` still initializes `self._last_fetch_result` to `None` with no subsequent reassignment

**Phase 2:** Replace the Note at line 85 with text stating:
1. `last_fetch_result` is updated via a callback (`AugmentRefiner._forward_fetch_result()` → the `RagPipeline.__init__`-supplied `set_fetch_result` callback) at the point `HttpAugment` reports fetch hits, not via `self.run()`
2. The one genuine staleness condition is when the HTTP call succeeds but returns zero hits (`selected_hits` empty), in which case the callback is not invoked and `last_fetch_result` retains its prior value

## Compatibility considerations

This is a documentation-only change. No backward compatibility concerns.

## Security considerations

No security impact — documentation correction only.

## Rollback considerations

Simple revert: restore the original Note text at line 85.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md | Manual — verify corrected Note's claims against cited code | Manual inspection of `pipeline.py:119`, `augment.py:102-110` | Note accurately describes current behavior |

## Completion criteria

- [ ] The Note no longer claims `fetch_result` staleness is caused by `RagPipeline._run_http_augment()` not calling `self.run()` (REQ-001)
- [ ] The Note describes the actual callback-based update path (`AugmentRefiner._forward_fetch_result()` → `RagPipeline.__init__`'s `set_fetch_result` callback) (REQ-001)
- [ ] The Note describes the one genuine staleness condition: HTTP success with zero hits (`selected_hits` empty) leaves `last_fetch_result` at its prior value (REQ-001)

## Out of scope

- Changing any source code behavior
- Adding a separate HTTP-mode-specific diagnostic field
- Removing the dead/redundant code path in `RagPipeline.augment()` (UNK-01 — tracked separately)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm the callback chain and staleness condition | Completed | 20260914-001407 | 20260914-001407 |  |
| 2 | Phase 2: Rewrite the Note | Completed | 20260914-001407 | 20260914-001407 |  |
| 3 | Verification: manual review | Completed | 20260914-001408 | 20260914-001408 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-183005_stale_fetch_result_http_mode.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-203417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-223825
- **Related target files**: docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md