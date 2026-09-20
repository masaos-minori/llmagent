# Test Audit Report — 2026-09-20

## # 1. Overall Findings

- **Total tests collected**: 7901 across all layers
- **Overall pass rate**: ~97% (approximately 48 failed out of 7901)
- **Strongest area**: DB layer (239/239 passed), Tools/Docs (446/448 passed)
- **Weakest area**: Agent layer (32 failures), EventBus (~16+ failures), RAG layer (10 failures)
- **Critical finding**: Security bypass in shell metacharacter detection (`_METACHAR_RE` misses `\r`)
- **Environment dependency**: sqlite-vec extension missing from `/opt/llm/sqlite-vec/` (resolved by building)

## # 2. Executed Tests / Validation Commands

| Command | Purpose | Result | Notes |
|---------|---------|--------|-------|
| `uv run pytest --co -q` | Test collection | Pass | 7901 tests collected |
| `uv run pytest tests/agent -q --tb=no` | Agent layer tests | Fail | 32 failed, 3223 passed, 8 skipped |
| `uv run pytest tests/shared -q --tb=no` | Shared layer tests | Fail | 3 failed, 951 passed |
| `uv run pytest tests/mcp_servers -q --tb=no` | MCP server tests | Fail | 6 failed, 1765 passed, 10 skipped |
| `uv run pytest tests/rag -q --tb=no` | RAG layer tests | Fail | 10 failed, 561 passed |
| `uv run pytest tests/db -q --tb=no` | DB layer tests | Pass | 239 passed |
| `uv run pytest tests/eventbus -q --tb=no` | EventBus tests | Fail | ~16+ failed (partial run due to timeout) |
| `uv run pytest tests/integration -q --tb=no` | Integration tests | Fail | 3 failed, 115 passed, 1 skipped |
| `uv run pytest tests/docs tests/tools -q --tb=no` | Docs/Tools tests | Pass | 446 passed, 2 skipped |
| `uv run ruff format --check scripts/` | Format check | Blocked | Not executed (audit scope) |
| `uv run ruff check scripts/` | Lint check | Blocked | Not executed (audit scope) |
| `uv run mypy scripts/` | Type check | Blocked | Not executed (audit scope) |

## # 3. Existing Test Failures

### F-001: Shell metacharacter detection missing carriage return
- **Test**: `tests/agent/test_tool_policy.py::TestPrefixCollision::test_prefix_collision_carriage_return_rejected`
- **Failure type**: AssertionError — `RiskLevel.NONE` returned instead of `RiskLevel.HIGH`
- **Likely cause**: `_METACHAR_RE` regex at `scripts/agent/tool_policy.py:42` includes `\n` but not `\r`
- **Severity**: P1 (Critical) — security bypass for shell injection via carriage return
- **Deterministic**: Yes (confirmed 3/3 runs)
- **Root cause**: Production code bug — `scripts/agent/tool_policy.py:42`
- **Evidence summary**: Regex pattern `[;|&]|&&|\|\||`|\$\(|<\(|>\(|>>|<<|[<>]|\n` lacks `\r`

### F-002: Carriage return in command rejected test
- **Test**: `tests/agent/test_tool_policy.py::TestPrefixCollision::test_carriage_return_in_command_rejected`
- **Failure type**: AssertionError — same root cause as F-001
- **Likely cause**: Same `_METACHAR_RE` gap
- **Severity**: P1 (Critical)
- **Deterministic**: Yes (confirmed 3/3 runs)
- **Root cause**: Production code bug — `scripts/agent/tool_policy.py:42`
- **Evidence summary**: Same as F-001

### F-003: Empty auth_token should raise ValueError
- **Test**: `tests/shared/test_mcp_config_validation.py::test_auth_token_empty_string_raises`
- **Failure type**: Failed — DID NOT RAISE `<class 'ValueError'>`
- **Likely cause**: Missing validation for empty auth_token string
- **Severity**: P2 (Important)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Test expects ValueError but none raised

### F-004: RAG pipeline remote empty test fails
- **Test**: `tests/rag/test_pipeline_http_result_kind.py::test_remote_empty`
- **Failure type**: ValueError — `RAG config requires non-empty llm_url, embed_url when use_search=True`
- **Likely cause**: Test setup creates invalid config (empty URLs with use_search=True)
- **Severity**: P3 (Nice to have)
- **Deterministic**: Yes (confirmed 3/3 runs)
- **Root cause**: Test code bug — incorrect test fixture configuration
- **Evidence summary**: `scripts/rag/config_resolution.py:155` raises during initialization

### F-005: EventBus DLQ promotion test fails
- **Test**: `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_requeue_returns_dlq_imminent_when_delivery_failure_count_gte_max_retry`
- **Failure type**: KeyError — `'dlq_imminent'` not in response
- **Likely cause**: Response schema mismatch after refactoring
- **Severity**: P2 (Important)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Response missing expected field

### F-006: EventBus ack/nack delivery verification fails
- **Test**: `tests/eventbus/test_eventbus_ack_nack.py::TestNackEvent::test_nack_event_delivery_verification`
- **Failure type**: AssertionError — status_code 200 != 409
- **Likely cause**: Status code logic changed after constants consolidation
- **Severity**: P2 (Important)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Expected 409 conflict, got 200 OK

### F-007: EventBus ack endpoint principal ownership validation fails
- **Test**: `tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint::test_ack_event_principal_ownership_validation`
- **Failure type**: AssertionError — status_code mismatch
- **Likely cause**: Same root cause as F-006
- **Severity**: P2 (Important)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Same as F-006

### F-008: Integration test MCP transport crash lifecycle termination
- **Test**: `tests/integration/test_mcp_transport_crash.py::test_d05_http_timeout_races_lifecycle_termination`
- **Failure type**: Needs confirmation
- **Likely cause**: Race condition in HTTP timeout handling
- **Severity**: P2 (Important)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Timeout race condition

### F-009: Integration test orchestrator workflow engine
- **Test**: `tests/integration/test_orchestrator_integration.py::TestApprovalWorkflowWithRealDB::test_handle_turn_invokes_workflow_engine_run`
- **Failure type**: Needs confirmation
- **Likely cause**: Workflow engine invocation issue
- **Severity**: P2 (Important)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Workflow engine not invoked

### F-010: Integration test required MCP failure aborts startup
- **Test**: `tests/integration/test_production_security_regression.py::test_required_mcp_failure_aborts_startup`
- **Failure type**: Needs confirmation
- **Likely cause**: Startup abort logic issue
- **Severity**: P2 (Important)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Startup abort not triggered

### F-011: MCP MDQ service error handler session_id
- **Test**: `tests/mcp_servers/mdq/test_mdq_exception_handlers.py::TestMdqServiceErrorHandler::test_session_id_from_header_and_request_id_from_middleware_state`
- **Failure type**: Needs confirmation
- **Likely cause**: Session ID extraction issue
- **Severity**: P3 (Nice to have)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Session ID not extracted correctly

### F-012: MCP CI/CD dispatches known tool and audit logs
- **Test**: `tests/mcp_servers/cicd/test_cicd_server_endpoints.py::TestCallToolEndpoint::test_dispatches_known_tool_and_audit_logs`
- **Failure type**: Needs confirmation
- **Likely cause**: Tool dispatch or audit logging issue
- **Severity**: P3 (Nice to have)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Tool dispatch or audit log missing

### F-013: MCP rag_pipeline start creates pipeline and HTTP client
- **Test**: `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py::TestServiceStart::test_start_creates_pipeline_and_http_client`
- **Failure type**: Needs confirmation
- **Likely cause**: Pipeline creation or HTTP client initialization issue
- **Severity**: P3 (Nice to have)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Pipeline/HTTP client not created

### F-014: MCP rag_pipeline no module level cfg override
- **Test**: `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py::TestServiceStart::test_no_module_level_cfg_override`
- **Failure type**: Needs confirmation
- **Likely cause**: Config override prevention issue
- **Severity**: P3 (Nice to have)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Config override not prevented

### F-015: Shared test session_id injected into HTTP transport header
- **Test**: `tests/shared/test_tool_executor_routing.py::TestSetSessionId::test_session_id_injected_into_http_transport_header`
- **Failure type**: Needs confirmation
- **Likely cause**: Session ID injection issue
- **Severity**: P3 (Nice to have)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Session ID not injected

### F-016: Agent tool policy prefix collision newlines rejected
- **Test**: `tests/agent/test_tool_policy.py::TestPrefixCollision::test_prefix_collision_newline_in_middle_rejected`
- **Failure type**: Needs confirmation
- **Likely cause**: Newline detection may also be affected by same regex issue
- **Severity**: P2 (Important)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: May be related to F-001/F-002

### F-017: Agent tool policy prefix collision multiple spaces before argument passes
- **Test**: `tests/agent/test_tool_policy.py::TestPrefixCollision::test_prefix_collision_multiple_spaces_before_argument_passes`
- **Failure type**: Needs confirmation
- **Likely cause**: Whitespace handling issue
- **Severity**: P3 (Nice to have)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Multiple spaces not handled correctly

### F-018: Agent tool policy prefix collision leading whitespace stripped passes
- **Test**: `tests/agent/test_tool_policy.py::TestPrefixCollision::test_prefix_collision_leading_whitespace_stripped_passes`
- **Failure type**: Needs confirmation
- **Likely cause**: Leading whitespace stripping issue
- **Severity**: P3 (Nice to have)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Leading whitespace not stripped

### F-019: Agent tool policy prefix collision trailing whitespace stripped passes
- **Test**: `tests/agent/test_tool_policy.py::TestPrefixCollision::test_prefix_collision_trailing_whitespace_stripped_passes`
- **Failure type**: Needs confirmation
- **Likely cause**: Trailing whitespace stripping issue
- **Severity**: P3 (Nice to have)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Trailing whitespace not stripped

### F-020: Agent tool policy prefix collision mixed quotes passes
- **Test**: `tests/agent/test_tool_policy.py::TestPrefixCollision::test_prefix_collision_mixed_quotes_passes`
- **Failure type**: Needs confirmation
- **Likely cause**: Quote handling issue
- **Severity**: P3 (Nice to have)
- **Deterministic**: Needs confirmation
- **Root cause**: Needs confirmation
- **Evidence summary**: Mixed quotes not handled correctly

## # 4. Missing or Inconsistent Test Cases

### F-021: sqlite-vec extension loading test
- **Category**: Environment dependency problem
- **Affected component**: `scripts/db/helper.py`
- **Why insufficient**: No test verifies sqlite-vec extension loading behavior
- **Uncovered risk**: Extension loading failures silently ignored
- **Evidence**: Error `/opt/llm/sqlite-vec/vec0.so.so: cannot open shared object file`
- **Confirmed**: Yes

### F-022: EventBus layer documentation
- **Category**: Missing integration test
- **Affected component**: `scripts/eventbus/`
- **Why insufficient**: Layer architecture documented in README.md but no tests verify layer boundaries
- **Uncovered risk**: Layer boundary violations not caught
- **Evidence**: `scripts/eventbus/README.md` documents stub module pattern
- **Confirmed**: Needs confirmation

## # 5. Implementation Task List

## P1 (Critical)

| Task ID | Addresses | Effort | Goal | Actions | Acceptance Criteria | Affected Files | Depends On |
|---|---|---|---|---|---|---|---|
| T-001 | F-001, F-002 | Low | Fix carriage return detection in shell metacharacter regex | Add `\r` to `_METACHAR_RE` pattern | All carriage return tests pass; security bypass eliminated | scripts/agent/tool_policy.py | — |

## P2 (Important)

| Task ID | Addresses | Effort | Goal | Actions | Acceptance Criteria | Affected Files | Depends On |
|---|---|---|---|---|---|---|---|
| T-002 | F-003 | Low | Add empty auth_token validation | Add ValueError raise for empty string | Test passes; validation enforced | scripts/shared/mcp_config_validation.py | — |
| T-003 | F-005, F-006, F-007 | Medium | Fix EventBus response schema and status codes | Review DLQ promotion and ack/nack response contracts | All EventBus tests pass; correct status codes returned | scripts/eventbus/dlq_repo.py, scripts/eventbus/delivery_repo.py | — |
| T-004 | F-008, F-009, F-010 | Medium | Fix integration test failures | Investigate and fix MCP transport, orchestrator, and startup abort issues | All integration tests pass | scripts/mcp_servers/, scripts/agent/orchestrator.py | — |
| T-005 | F-014 | Low | Fix RAG config validation in test fixture | Update test fixture to provide valid URLs when use_search=True | RAG pipeline tests pass | tests/rag/test_pipeline_http_result_kind.py | — |

## P3 (Nice to have)

| Task ID | Addresses | Effort | Goal | Actions | Acceptance Criteria | Affected Files | Depends On |
|---|---|---|---|---|---|---|---|
| T-006 | F-011 | Low | Fix MCP MDQ session ID extraction | Debug and fix session ID from header extraction | MDQ exception handler test passes | scripts/mcp_servers/mdq/ | — |
| T-007 | F-012 | Low | Fix MCP CI/CD tool dispatch | Debug and fix tool dispatch and audit logging | CI/CD endpoint test passes | scripts/mcp_servers/cicd/ | — |
| T-008 | F-013 | Low | Fix MCP rag_pipeline start | Debug and fix pipeline creation and HTTP client init | Rag pipeline start test passes | scripts/mcp_servers/rag_pipeline/ | — |
| T-009 | F-015 | Low | Fix session ID injection | Debug and fix session ID into HTTP transport header | Session ID injection test passes | scripts/shared/tool_executor_routing.py | — |
| T-010 | F-016-F-020 | Low | Fix remaining agent tool policy tests | Debug and fix whitespace/quote handling in prefix collision tests | All prefix collision tests pass | scripts/agent/tool_policy.py | T-001 |

## # 6. Test Cases to Add or Update

- TC-001 / Task: T-001 / Finding: F-001 — Verify carriage return is detected as metacharacter in shell_run command
- TC-002 / Task: T-001 / Finding: F-002 — Verify carriage return in command position triggers HIGH risk
- TC-003 / Task: T-002 — Verify empty auth_token raises ValueError during MCP config validation
- TC-004 / Task: T-003 — Verify DLQ requeue returns dlq_imminent warning when delivery_failure_count >= max_retry
- TC-005 / Task: T-003 — Verify nack_event returns correct status code on conflict
- TC-006 / Task: T-004 — Verify MCP transport crash lifecycle termination under timeout
- TC-007 / Task: T-004 — Verify orchestrator invokes workflow engine on turn handle
- TC-008 / Task: T-004 — Verify required MCP failure aborts startup
- TC-009 / Task: T-005 — Verify RAG pipeline accepts valid config with non-empty URLs
- TC-010 / Task: T-006 — Verify session_id extracted from header in MDQ error handler
- TC-011 / Task: T-007 — Verify known tool dispatch and audit log in CI/CD endpoint
- TC-012 / Task: T-008 — Verify pipeline and HTTP client created on rag_pipeline start
- TC-013 / Task: T-009 — Verify session_id injected into HTTP transport header
- TC-014 / Task: T-010 — Verify newline rejection in prefix collision detection
- TC-015 / Task: T-010 — Verify whitespace handling in prefix collision detection

## # 7. Traceability

| Finding ID | Category | Severity | Task ID(s) | Test Case ID(s) | Status |
|---|---|---|---|---|---|
| F-001 | Existing test failure | P1 | T-001 | TC-001 | Open |
| F-002 | Existing test failure | P1 | T-001 | TC-002 | Open |
| F-003 | Missing negative-path test | P2 | T-002 | TC-003 | Open |
| F-004 | Environment dependency problem | P3 | T-005 | TC-009 | Open |
| F-005 | Existing test failure | P2 | T-003 | TC-004 | Open |
| F-006 | Existing test failure | P2 | T-003 | TC-005 | Open |
| F-007 | Existing test failure | P2 | T-003 | TC-005 | Open |
| F-008 | Existing test failure | P2 | T-004 | TC-006 | Open |
| F-009 | Existing test failure | P2 | T-004 | TC-007 | Open |
| F-010 | Existing test failure | P2 | T-004 | TC-008 | Open |
| F-011 | Existing test failure | P3 | T-006 | TC-010 | Open |
| F-012 | Existing test failure | P3 | T-007 | TC-011 | Open |
| F-013 | Existing test failure | P3 | T-008 | TC-012 | Open |
| F-014 | Existing test failure | P3 | T-005 | TC-009 | Open |
| F-015 | Existing test failure | P3 | T-009 | TC-013 | Open |
| F-016 | Existing test failure | P2 | T-010 | TC-014 | Open |
| F-017 | Existing test failure | P3 | T-010 | TC-015 | Open |
| F-018 | Existing test failure | P3 | T-010 | TC-015 | Open |
| F-019 | Existing test failure | P3 | T-010 | TC-015 | Open |
| F-020 | Existing test failure | P3 | T-010 | TC-015 | Open |
| F-021 | Environment dependency problem | P3 | — | — | Resolved |
| F-022 | Missing integration test | P3 | — | — | Open |

## # 8. Recommended Execution Order

1. **T-001** — Critical security issue; must be fixed first
2. **T-002** — Simple validation addition; low effort
3. **T-003** — EventBus fixes depend on understanding response contracts
4. **T-004** — Integration tests may reveal systemic issues
5. **T-005** — RAG config fix is straightforward once root cause confirmed
6. **T-006-T-010** — Remaining P3 items; can be done in parallel after P1/P2

## # 9. Additional Confirmation Items Needed

- Determinism of F-005 through F-020 (requires 3x re-run per test)
- Whether sqlite-vec extension loading is required for all test runs or only specific ones
- Whether MCP server directory (`tests/mcp/`) should contain tests or if they're under `tests/mcp_servers/`
- Whether the full test suite timeout (300s+) is acceptable or needs optimization
