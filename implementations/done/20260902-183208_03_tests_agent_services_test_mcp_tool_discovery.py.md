## Goal

Add `security_profile` as a second parametrized axis to the existing
`TestDiscoverAllCrossProfileEquivalence::test_classification_equivalent_across_security_profiles`
test class, closing REQ-002's still-unexercised claim that classification is identical
under both `SecurityProfile.LOCAL` and `SecurityProfile.PRODUCTION`.

## Scope

Modify exactly one existing test method's `@pytest.mark.parametrize` decorator and body
in `tests/agent/services/test_mcp_tool_discovery.py` (the
`TestDiscoverAllCrossProfileEquivalence` class, added by an earlier implementation
cycle — see Assumptions). Do not add a new test class; do not touch any other test in
this file.

## Assumptions

- **Partially-implemented discrepancy found during adversarial verification**: a prior
  implementation cycle (`implementations/done/20260902-121047_003_test_mcp_tool_discovery_cross_profile_equivalence.md`,
  same `Source plan`/`Related target files` as this document) already added the
  `TestDiscoverAllCrossProfileEquivalence` class and its
  `test_classification_equivalent_across_security_profiles` method — confirmed present
  at current line 792 — but that document's own Scope/Method only parametrized
  `required_value`, never `security_profile`. Direct read confirms
  `_make_ctx()` is called at line 811 with no `security_profile` argument, so it
  always defaults to `SecurityProfile.LOCAL` (the default at line 73 of `_make_ctx()`'s
  signature). The Plan's own row (`plans/20260901-102432_plan.md`, row 3) explicitly
  identifies this exact gap as the remaining action — this document implements only
  that remainder, per `plan-to-implementation-procedure` Step 3's "Partially
  implemented" handling: reference the matched existing document for the
  already-covered portion (the test class/method's existence) instead of repeating it.
- `_make_ctx(servers, http, security_profile=..., tool_definitions_strict=...)`
  accepts `security_profile` as its third parameter (confirmed at
  `tests/agent/services/test_mcp_tool_discovery.py` lines 70-73) — no signature change
  needed to pass it explicitly.
- `McpToolDiscoveryService.discover_all()`'s classification branch reads `cfg.required`
  directly with no `security_profile` involvement (confirmed at
  `scripts/agent/services/mcp_tool_discovery.py` line 130) — so the expected outcome
  (`FATAL` for `required=True`, `WARNING` for `required=False`) must be identical
  regardless of which `security_profile` is passed; that identity is exactly what this
  test proves.

## Design decisions

Add `security_profile` as a second parametrized axis on the same
`@pytest.mark.parametrize` decorator (a `pytest.mark.parametrize` stack or a combined
tuple list), rather than duplicating the test method per profile — consistent with the
existing method's own single-method, parametrized-tuple style (see Method below).

## Alternatives considered

Adding a second, separate test method for `SecurityProfile.PRODUCTION` — rejected:
duplicates the existing method's setup/assertion logic; a second parametrized axis on
the same method proves the equivalence claim directly (same method, same assertions,
two profile values) rather than requiring the reader to compare two separate methods.

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

Widen the existing `test_classification_equivalent_across_security_profiles`
method's parametrization to cover both `SecurityProfile.LOCAL` and
`SecurityProfile.PRODUCTION`, passing the new axis into `_make_ctx()`.

### Method

Current method (lines 792-818):
```python
class TestDiscoverAllCrossProfileEquivalence:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "required_value,expected_status",
        [
            (True, StartupCheckStatus.FATAL),
            (False, StartupCheckStatus.WARNING),
        ],
    )
    async def test_classification_equivalent_across_security_profiles(
        self, required_value: bool, expected_status: StartupCheckStatus
    ) -> None:
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            required=required_value,
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx = _make_ctx({"srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == expected_status for f in mcp_findings)
```

Replace with (adds `security_profile` as a second parametrize decorator, and passes it
to `_make_ctx()`):
```python
class TestDiscoverAllCrossProfileEquivalence:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "security_profile",
        [SecurityProfile.LOCAL, SecurityProfile.PRODUCTION],
    )
    @pytest.mark.parametrize(
        "required_value,expected_status",
        [
            (True, StartupCheckStatus.FATAL),
            (False, StartupCheckStatus.WARNING),
        ],
    )
    async def test_classification_equivalent_across_security_profiles(
        self,
        required_value: bool,
        expected_status: StartupCheckStatus,
        security_profile: SecurityProfile,
    ) -> None:
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            required=required_value,
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx = _make_ctx({"srv": srv_cfg}, http, security_profile=security_profile)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == expected_status for f in mcp_findings)
```

### Details

`SecurityProfile` is already imported in this file (used elsewhere, e.g.
`TestDiscoverAllDuplicates._dup_ctx`'s `security_profile: SecurityProfile` parameter at
line 822) — no new import required. Stacking two `@pytest.mark.parametrize` decorators
produces the cross-product (4 cases: 2 `required_value`/`expected_status` pairs × 2
`security_profile` values), which is exactly the "identical outcome... under both
profiles" claim REQ-002 states — each `required_value` is now checked under both
profiles independently, not just once under the `LOCAL` default.

## Compatibility considerations

Test-only change; no production code touched. The four pre-existing tests this class's
sibling methods do not touch remain unaffected — only this one method's decorator/
signature/`_make_ctx()` call changes.

## Security considerations

N/A: no security-relevant content in a test-coverage change.

## Rollback considerations

Trivially revertable via `git revert`/`git checkout` of this single file — reverts to
the prior (LOCAL-only) parametrization, re-opening the gap this document closes.

## Validation plan

- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllCrossProfileEquivalence -v` — expect 4 passing cases (2×2 parametrize cross-product).
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` — full module, no new failures.
- Full standard validation sequence per `rules/toolchain.md` (`ruff format`/`check`, `mypy`, `lint-imports`, `bandit`) — per the Plan's own Phase 3 step, this is the first item in this Plan to actually change a file, so this is also where the full sequence first applies.

## Completion criteria

The test method exercises all 4 combinations of `required_value` × `security_profile`
(2×2), each asserting the same `expected_status` regardless of `security_profile` —
directly proving REQ-002's cross-profile equivalence claim (AC-1, AC-4).

## Out of scope

Modifying `scripts/agent/services/mcp_tool_discovery.py` or any other production file
(already implemented, per the Plan's struck-through rows). Modifying
`tests/shared/test_mcp_config.py` (separate, already-implemented row). Updating
ADR-004 (separate row, seq 06 of this same Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | Already implemented — `security_profile` parametrization exists |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | All 4 test cases pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | N/A: test-only change, no docs/00_index.md task-scope mapping applies |

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
- **Requirement ID**: REQ-002 (cross-profile classification equivalence — the
  `security_profile` axis specifically; the test class/method itself was already
  delivered by a prior cycle, see Assumptions)
- **Source issue**: `issues/20260831-192510_adr004_05_mcp_config_alignment_superseded_by_policy_reversal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-102432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-183208
- **Related target files**: `tests/agent/services/test_mcp_tool_discovery.py`
