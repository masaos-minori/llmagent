## Goal
Promote ADR-007's Circuit Breaker state model from Implementation Notes prose to
a first-class Invariant (`INV-11`), per `REQ-001`, `REQ-002`, `REQ-005` —
confirmed warranted because 4 files outside `scripts/shared/mcp_health.py`
depend on the exact state names by equality comparison.

## Scope
- In scope: add new local `INV-11` to `## Invariants`; add its `##
  Verification` entry citing the sibling new test; condense the Circuit
  Breaker Implementation Notes line to a pointer.
- Out of scope: any other ADR-007 section; removing the confirmed-dead
  `McpServerHealthState.UNKNOWN` enum member (a separate, out-of-scope finding
  — see the source Plan's `UNK-01`).

## Assumptions
- `INV-11`'s wording describes the 4 *live* states (`HEALTHY`/`DEGRADED`/
  `UNAVAILABLE`/`HALF_OPEN`) and their actual transition rules from
  `scripts/shared/mcp_health.py`, not the Implementation Notes' own imprecise
  "5-state" framing (which double-counts `HEALTHY` and omits the real, unused
  fifth member `UNKNOWN`).
- The Invariant states name-stability, not transition-order stability toward
  external callers — none of the 4 dependent files compare states relative to
  each other; only `scripts/shared/mcp_health.py`'s own internal methods are
  order-dependent (e.g. `HALF_OPEN` is only reachable from `UNAVAILABLE`).
- This procedure depends on the sibling test procedure
  (`implementations/20260915-190812_02_tests_shared_test_mcp_health.py.md`)
  for the exact test node id `REQ-002`'s Verification entry cites — read that
  document's actual applied test names before writing this entry if processing
  this row first.

## Design decisions
- Follow ADR-007's existing `INV-01`–`INV-10` style exactly: short,
  single-sentence, Japanese, declarative.
- Example target wording (exact phrasing may be refined at implementation
  time, but must stay a single Japanese sentence naming the 4 states and the
  external-dependency rationale): `INV-11:
  McpServerHealthRegistryが管理するMCPサーバーの死活状態（HEALTHY/DEGRADED/
  UNAVAILABLE/HALF_OPEN）の名称は、Transport層外の複数の呼び出し元が直接比較
  するため、暗黙に変更しない。`

## Alternatives considered
- Keep the ADR's original "5-state" phrase verbatim when promoting — rejected;
  it is confirmed inaccurate against the actual enum (double-counts `HEALTHY`,
  omits the real but unused `UNKNOWN` member) and promoting it as-is would
  canonize the inaccuracy into a first-class Invariant.

## Implementation
### Target file
`docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`

### Procedure
1. Re-verify (idempotent recheck) current line numbers: confirm `## Invariants`
   still ends at `INV-10` and `## Implementation Notes`' Circuit Breaker line
   is still the sole remaining bullet there.
2. Add a new bullet immediately after `INV-10`:
   `- INV-11: {single-sentence Japanese wording per Design decisions above}`.
3. In `## Verification` > `### Automated Tests`, add a new entry matching the
   existing field format, citing the sibling procedure's new test (confirm the
   exact test file/function/class names from that document's actual applied
   edit before writing this citation):
   ```
   - **Test**: Circuit Breakerの状態遷移（DEGRADED/UNAVAILABLE閾値到達、HALF_OPEN
     クールダウン、HALF_OPEN失敗時のUNAVAILABLE復帰）が仕様通りであること
     （`tests/shared/test_mcp_health.py`）
     - **Verifies**: INV-11
     - **Type**: Unit
     - **Blocking**: Yes
   ```
4. Replace the Circuit Breaker Implementation Notes line with a short pointer:
   `- Circuit Breaker: INV-11参照（`McpServerHealthRegistry`が実装）`.

### Method
Use `Edit` (exact-string replacement) — one call per step 2-4.

### Details
- Do not touch `INV-01`–`INV-10` or any other `## Verification` entry.
- If the sibling test procedure (seq 02) has not yet been applied when this
  row is processed, use the placeholder test citation above and verify it
  matches the actual test names once both rows are complete — do not leave a
  citation to a test that does not exist.

## Compatibility considerations
N/A: documentation-only change; no code, config, or test reads this ADR's
Invariants/Verification/Notes sections programmatically beyond
`tools/check_adr_invariant_matrix.py` (targets `docs/adr-index.md`, covered by
the sibling procedure).

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`
if validation fails.

## Validation plan
- Manual diff: confirm `INV-11` added after `INV-10`, single-sentence Japanese matching existing style.
- Manual diff: confirm the new `## Verification` entry cites the actual test names applied by the sibling test procedure.
- Manual diff: confirm the Circuit Breaker Notes line is replaced with a pointer, not left duplicated.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` — expect zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` — expect no new finding beyond the 14-finding baseline established this session.
- `uv run python tools/check_adr_invariant_matrix.py` — run after the sibling `docs/adr-index.md` procedure lands too — expect zero findings.

## Completion criteria
- `INV-11` exists, single-sentence Japanese, immediately after `INV-10`.
- A `## Verification` entry for `INV-11` exists citing the new test.
- The Circuit Breaker Notes line is a short pointer, not full prose.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- `McpServerHealthState.UNKNOWN` (dead code, separate finding).
- `tests/shared/test_mcp_health.py` itself — covered by the sibling procedure,
  `implementations/20260915-190812_02_tests_shared_test_mcp_health.py.md`.
- `docs/adr-index.md` — covered by the sibling procedure,
  `implementations/20260915-190812_03_docs_adr-index.md.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-190812 | 20260915-191538 | Added INV-11 (naming the actual 4 live states) + Verification entry citing tests/shared/test_mcp_health.py (real, applied test file); condensed Circuit Breaker Notes line to pointer. Noted (not fixed, out of scope): ADR-007's own Runtime Monitoring/Manual Review subsections contain unrelated copy-pasted EventBus/DLQ text from ADR-006's template — a pre-existing authoring defect, unrelated to this cycle |
| 2 | Add or update tests per Validation plan | Completed | 20260915-191538 | 20260915-191538 | N/A: this document's own scope is documentation only; the new test is the sibling procedure's responsibility N/A: this document's own scope is documentation only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-191538 | 20260915-191538 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 14 pre-existing unrelated findings matching established baseline |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-191538 | 20260915-191538 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-005 — promote Circuit Breaker state model to INV-11 with Verification, condense Notes
- **Source issue**: issues/done/20260914-124601_docqa04_adr-007-circuit-breaker-states-not-in-invariants.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-190322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-190812
- **Related target files**: docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md