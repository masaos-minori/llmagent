# Implementation Procedure: Add audit record validation tests for auth failures; verify no credential leakage

## Goal

Update `tests/eventbus/test_eventbus_auth.py` to add audit record validation tests for auth failures and verify no credential leakage.

## Scope

- Add audit record validation tests for auth failures.
- Verify no credential leakage in audit records.

## Assumptions

- A: The existing `scripts/eventbus/audit.py` module provides the infrastructure for structured audit logging — confirmed by `audit.py:45-145`.
- B: The `log_auth_failure()` and `log_privileged_action()` functions already exist with the correct signature — confirmed by `audit.py:94-145`.
- C: The `_build_audit_record()` function accepts `consumer_id`, `route`, `target`, `outcome`, `error_type`, and optional `detail` — confirmed by `audit.py:59-91`.
- D: The `X-Request-Id` header is already injected by the auth middleware — confirmed by `auth.py:276-281`.
- E: CI-005 has already been resolved and removed from the active inventory — confirmed by `docs/00_governance_03_issue-and-uncertainty-management.md:313-315`.

## Design decisions

- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Backward compatibility**: Preserve existing behavior for healthy subscription states.

## Alternatives considered

- **Keep single-token design**: Continue using only `auth_token` and per-role tokens. This was rejected because it doesn't provide the granularity needed for REQ-007—REQ-009.
- **Separate authorization config file**: Have a separate YAML/TOML file for authorization rules. This adds complexity without security benefit.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original EventBusConfig dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Implementation

### Target file

`tests/eventbus/test_eventbus_auth.py`

### Procedure

#### Step 1: Add auth failure (401) audit record validation test (REQ-001, REQ-003)

Add a new test method after the existing `TestSubscribeAuth::test_subscribe_without_token` method:

New code:
```python
    def test_auth_failure_401_produces_structured_audit_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """T-1: Auth failure (401) produces structured audit record with request_id, route, target."""
        from unittest.mock import MagicMock, patch
        
        # Capture the log output to verify audit record emission
        captured_records = []
        
        def capture_log(record):
            captured_records.append(record)
        
        # Patch the logger to capture audit records
        with patch("scripts.eventbus.audit.logger.warning", side_effect=capture_log):
            response = self.client.get(
                "/subscribe",
                params={"topic": "test", "consumer_id": "consumer_a"},
                headers={"Authorization": "Bearer invalid-token"},
            )
            assert response.status_code == 401
        
        # Verify at least one audit record was emitted
        assert len(captured_records) > 0
        
        # Parse the JSON-lines audit record
        import json
        audit_record = json.loads(captured_records[0])
        
        # Verify required fields
        assert "request_id" in audit_record
        assert "route" in audit_record
        assert "target" in audit_record
        assert "outcome" in audit_record
        assert "error_type" in audit_record
        
        # Verify error type is authentication_failed
        assert audit_record["error_type"] == "authentication_failed"
        assert audit_record["outcome"] == "rejected"
        
        # Verify no raw tokens in the audit record
        assert "invalid-token" not in str(audit_record)
```

Key changes:
- Added test for auth failure (401) audit record validation.
- Verifies required fields in audit record.
- Verifies no raw tokens in audit record.

#### Step 2: Add auth failure (403) audit record validation test (REQ-001, REQ-003)

Add a new test method after the previous one:

New code:
```python
    def test_auth_failure_403_produces_structured_audit_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """T-2: Auth failure (403) produces structured audit record with role mismatch details."""
        from unittest.mock import MagicMock, patch
        
        # Capture the log output to verify audit record emission
        captured_records = []
        
        def capture_log(record):
            captured_records.append(record)
        
        # Patch the logger to capture audit records
        with patch("scripts.eventbus.audit.logger.warning", side_effect=capture_log):
            response = self.client.post(
                "/events/test-event-id/ack",
                params={"consumer_id": "consumer_a"},
                headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
            )
            assert response.status_code == 403
        
        # Verify at least one audit record was emitted
        assert len(captured_records) > 0
        
        # Parse the JSON-lines audit record
        import json
        audit_record = json.loads(captured_records[0])
        
        # Verify required fields
        assert "request_id" in audit_record
        assert "route" in audit_record
        assert "target" in audit_record
        assert "outcome" in audit_record
        assert "error_type" in audit_record
        
        # Verify error type is authorization_failed
        assert audit_record["error_type"] == "authorization_failed"
        assert audit_record["outcome"] == "rejected"
        
        # Verify no raw tokens in the audit record
        assert "publisher-token" not in str(audit_record)
```

Key changes:
- Added test for auth failure (403) audit record validation.
- Verifies required fields in audit record.
- Verifies no raw tokens in audit record.

#### Step 3: Add consumer identity rejection audit record validation test (REQ-001, REQ-003)

Add a new test method after the previous one:

New code:
```python
    def test_consumer_identity_rejection_produces_structured_audit_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """T-3: Consumer identity rejection (403) produces structured audit record with consumer_id."""
        from unittest.mock import MagicMock, patch
        
        # Capture the log output to verify audit record emission
        captured_records = []
        
        def capture_log(record):
            captured_records.append(record)
        
        # Patch the logger to capture audit records
        with patch("scripts.eventbus.audit.logger.warning", side_effect=capture_log):
            response = self.client.get(
                "/subscribe",
                params={"topic": "test", "consumer_id": "unauthorized-consumer"},
                headers={"Authorization": f"Bearer {self.cfg.consumer_token}"},
            )
            assert response.status_code == 403
        
        # Verify at least one audit record was emitted
        assert len(captured_records) > 0
        
        # Parse the JSON-lines audit record
        import json
        audit_record = json.loads(captured_records[0])
        
        # Verify required fields
        assert "request_id" in audit_record
        assert "route" in audit_record
        assert "target" in audit_record
        assert "outcome" in audit_record
        assert "error_type" in audit_record
        
        # Verify error type is consumer_identity_rejected
        assert audit_record["error_type"] == "consumer_identity_rejected"
        assert audit_record["outcome"] == "rejected"
        
        # Verify no raw tokens in the audit record
        assert "consumer-token" not in str(audit_record)
```

Key changes:
- Added test for consumer identity rejection audit record validation.
- Verifies required fields in audit record.
- Verifies no raw tokens in audit record.

#### Step 4: Add topic authorization rejection audit record validation test (REQ-001, REQ-003)

Add a new test method after the previous one:

New code:
```python
    def test_topic_authorization_rejection_produces_structured_audit_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """T-4: Topic authorization rejection (403) produces structured audit record with topic."""
        from unittest.mock import MagicMock, patch
        
        # Capture the log output to verify audit record emission
        captured_records = []
        
        def capture_log(record):
            captured_records.append(record)
        
        # Patch the logger to capture audit records
        with patch("scripts.eventbus.audit.logger.warning", side_effect=capture_log):
            response = self.client.get(
                "/subscribe",
                params={"topic": "disallowed-topic", "consumer_id": "consumer_a"},
                headers={"Authorization": f"Bearer {self.cfg.consumer_token}"},
            )
            assert response.status_code == 403
        
        # Verify at least one audit record was emitted
        assert len(captured_records) > 0
        
        # Parse the JSON-lines audit record
        import json
        audit_record = json.loads(captured_records[0])
        
        # Verify required fields
        assert "request_id" in audit_record
        assert "route" in audit_record
        assert "target" in audit_record
        assert "outcome" in audit_record
        assert "error_type" in audit_record
        
        # Verify error type is topic_authorization_rejected
        assert audit_record["error_type"] == "topic_authorization_rejected"
        assert audit_record["outcome"] == "rejected"
        
        # Verify no raw tokens in the audit record
        assert "consumer-token" not in str(audit_record)
```

Key changes:
- Added test for topic authorization rejection audit record validation.
- Verifies required fields in audit record.
- Verifies no raw tokens in audit record.

#### Step 5: Add credential leakage prevention test (REQ-003)

Add a new test method after the previous one:

New code:
```python
    def test_no_credential_leakage_in_audit_records(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """T-7: No raw tokens/credentials in any audit record."""
        from unittest.mock import MagicMock, patch
        
        # Capture the log output to verify audit record emission
        captured_records = []
        
        def capture_log(record):
            captured_records.append(record)
        
        # Test multiple auth failure scenarios
        scenarios = [
            ("Bearer invalid-token", 401),
            (f"Bearer {self.cfg.publisher_token}", 403),
        ]
        
        for header_value, expected_status in scenarios:
            captured_records.clear()
            
            with patch("scripts.eventbus.audit.logger.warning", side_effect=capture_log):
                if expected_status == 401:
                    response = self.client.get(
                        "/subscribe",
                        params={"topic": "test", "consumer_id": "consumer_a"},
                        headers={"Authorization": header_value},
                    )
                else:
                    response = self.client.post(
                        "/events/test-event-id/ack",
                        params={"consumer_id": "consumer_a"},
                        headers={"Authorization": header_value},
                    )
                assert response.status_code == expected_status
            
            # Verify no raw tokens in any audit record
            for record in captured_records:
                import json
                audit_record = json.loads(record)
                
                # Verify no raw tokens in the audit record
                assert "invalid-token" not in str(audit_record)
                assert "publisher-token" not in str(audit_record)
                assert "consumer-token" not in str(audit_record)
                assert "operator-token" not in str(audit_record)
                assert "admin-token" not in str(audit_record)
```

Key changes:
- Added test for credential leakage prevention.
- Verifies no raw tokens in any audit record across multiple scenarios.

### Details

- REQ-001: Audit logging integrated into all three auth failure paths.
- REQ-003: Request ID included in audit records; raw tokens never exposed.
- REQ-004: Duplicate audit prevention verified under concurrent requests.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original EventBusConfig dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/auth.py | Unit: audit record emission for auth failures; Integration: no credential leakage | uv run pytest tests/eventbus/test_eventbus_auth.py -v | New audit tests pass; existing tests unchanged |
| scripts/eventbus/auth.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/auth.py | Type checking | uv run mypy scripts/eventbus/auth.py | No new type errors |

## Completion criteria

- [ ] Auth failure (401) audit record validation test added.
- [ ] Auth failure (403) audit record validation test added.
- [ ] Consumer identity rejection audit record validation test added.
- [ ] Topic authorization rejection audit record validation test added.
- [ ] Credential leakage prevention test added.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-010).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add auth failure (401) audit record validation test | Pending | — | — | |
| 2 | Add auth failure (403) audit record validation test | Pending | — | — | |
| 3 | Add consumer identity rejection audit record validation test | Pending | — | — | |
| 4 | Add topic authorization rejection audit record validation test | Pending | — | — | |
| 5 | Add credential leakage prevention test | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260914-102405_eventbus05_structured-auth-audit-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-173340_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-225600
- **Related target files**: tests/eventbus/test_eventbus_auth.py
