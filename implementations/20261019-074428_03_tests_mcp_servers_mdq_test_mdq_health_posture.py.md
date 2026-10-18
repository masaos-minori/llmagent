## Goal

Create `tests/mcp_servers/mdq/test_mdq_health_posture.py` asserting the fail-closed startup gate
for `scripts/mcp_servers/mdq/mdq_server.py`: the gate passes on a validated posture and fails closed
(`SystemExit(1)`, logging the failed check ids and reason codes) on an invalid posture, mirroring
`sibling tests/mcp_servers/web_search/test_web_search_health_posture.py::TestBindGate`
(REQ-004 / AC-004).

## Scope

- **In-Scope**:
  - Create `tests/mcp_servers/mdq/test_mdq_health_posture.py` asserting the gate passes on a
    validated posture and fails closed (`SystemExit(1)`, logged reason codes) on an invalid posture.
- **Out-of-Scope**:
  - Changing `mdq_server.py` or `health_check.py` (covered by the sibling documents).
  - Any `docs/*.md` change.

## Assumptions

- The gate reads the module-level `_security_posture`; tests rebuild the posture from patched inputs
  and monkeypatch `mdq_server._security_posture`, exactly as the sibling test does for
  `web_search_server`.
- MDQ's posture is built via `build_mdq_posture(mdq_cfg, db_file_present, schema_error,
  schema_checked, index_stats)`; an invalid posture is produced by supplying inputs that fail a
  check (e.g. `db_file_present=False` with a missing DB, or a non-`None` `schema_error`).
- Importing `mdq_server` in tests does not trigger `SystemExit` (the gate runs only in `__main__`),
  so the module can be imported and its `_security_posture` monkeypatched freely.
- `caplog` is available for asserting the gate logs the failed check ids and reason codes.

## Design decisions

- Mirror the sibling `TestBindGate` structure: one test for the passing path (validated posture,
  gate returns without raising) and one for the failing path (invalid posture, `SystemExit(1)` with
  logged reason codes).
- Rebuild the posture through the real `build_mdq_posture()` so the test exercises the actual
  validation machinery rather than a hand-built stub.

## Alternatives considered

N/A: mirroring the sibling test structure is the lowest-risk approach and preserves cross-server
parity.

## Implementation

### Target file

`tests/mcp_servers/mdq/test_mdq_health_posture.py`

### Procedure

1. Create `tests/mcp_servers/mdq/test_mdq_health_posture.py` with a header docstring citing
   REQ-004 / AC-004 and noting the gate is startup-only (mirrors the sibling header).
2. Import `mdq_server` and `build_mdq_posture`:
   ```python
       from mcp_servers.mdq import mdq_server
       from mcp_servers.mdq.mdq_security_validation import build_mdq_posture
   ```
3. Add a `TestBindGate` class:
   ```python
       class TestBindGate:
           \"\"\"AC-004: mdq-mcp does not bind HTTP when the posture is not validated.\"\"\"

           def test_validated_posture_does_not_block_bind(self) -> None:
               mdq_server._enforce_posture_gate()

           def test_gate_refuses_bind_and_logs_reason_codes(
               self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
           ) -> None:
               posture = build_mdq_posture(
                   mdq_cfg={},
                   db_file_present=False,
                   schema_error=("db_file", "database not found"),
                   schema_checked=True,
                   index_stats=None,
               )
               monkeypatch.setattr(mdq_server, "_security_posture", posture)

               assert posture.validated is False
               with pytest.raises(SystemExit) as excinfo:
                   mdq_server._enforce_posture_gate()

               assert excinfo.value.code == 1
               gate_lines = [
                   record.getMessage()
                   for record in caplog.records
                   if "refusing to bind" in record.getMessage()
               ]
               assert gate_lines, "the gate did not log a refusal"
   ```
   Adjust the invalid-input construction to match `build_mdq_posture`'s actual failure semantics
   (confirm which input makes `.validated` False by reading `validate_mdq_security()`); the example
   above uses a missing DB + schema error as a representative failing case.
4. Confirm the existing `tests/mcp_servers/mdq/` suites still pass, especially
   `test_mdq_security_validation.py` and `test_mdq_health*.py` (REQ-005, REQ-003).
5. Run the new test target and static checks; confirm clean.

### Method

- **Passing path.** Call `_enforce_posture_gate()` against the shipped (validated) posture and assert
  it returns without raising.
- **Failing path.** Rebuild the posture from failing inputs via the real `build_mdq_posture()`,
  monkeypatch `mdq_server._security_posture`, assert `.validated is False`, then assert
  `_enforce_posture_gate()` raises `SystemExit(1)` with code `1` and logs a line containing the
  refused-bind message and the failed check ids / reason codes.
- **Use the real validator.** Do not hand-build a `SecurityPosture`; drive `build_mdq_posture()` so
  the test proves the actual validation → gate chain.

### Details

- `REQ-004`: a `test_mdq_health_posture.py` asserts the gate passes on a validated posture and fails
  closed (`SystemExit(1)`, logging failed check ids and reason codes) on an invalid posture,
  mirroring the sibling tests.
- **UNK-01:** not blocking; the local gate still closes the bind-to-first-probe window.

## Compatibility considerations

New test file only; does not affect production code or the CI exit contract. No `docs/*.md` change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/mdq/test_mdq_health_posture.py` | Unit: gate fails closed on invalid posture, passes on valid posture | `uv run pytest tests/mcp_servers/mdq/test_mdq_health_posture.py` | gate raises `SystemExit(1)` on invalid posture, passes on validated posture |

## Completion criteria

- A test asserting the gate passes on a validated posture (AC-004).
- A test asserting the gate fails closed (`SystemExit(1)`, logged reason codes) on an invalid
  posture (AC-004).
- The existing `tests/mcp_servers/mdq/` suites pass unchanged.

## Out of scope

Changing `mdq_server.py` or `health_check.py`, and any `docs/*.md` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Extract dependency-collection helper from `check_health()` | Pending | — | — | REQ-003; AC-003 |
| 2 | Phase 2a: Build MDQ posture once at import | Pending | — | — | REQ-002; `scripts/mcp_servers/mdq/mdq_server.py` |
| 3 | Phase 2b: Add `_enforce_posture_gate()` and call it in `__main__` | Pending | — | — | REQ-001; `scripts/mcp_servers/mdq/mdq_server.py` |
| 4 | Phase 3: Add `test_mdq_health_posture.py` | Pending | — | — | REQ-004; `tests/mcp_servers/mdq/test_mdq_health_posture.py` |
| 5 | Phase 4: Static checks, MDQ test suite, deploy confirmation | Pending | — | — | REQ-001..REQ-005 |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261018-191517_mcp002_mdq-mcp-server-lacks-pre-bind-fail-closed-security-posture-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-222300_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-074428
- **Related target files**: tests/mcp_servers/mdq/test_mdq_health_posture.py
