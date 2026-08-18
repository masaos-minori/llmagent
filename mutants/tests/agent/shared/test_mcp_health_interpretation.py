"""tests/test_mcp_health_interpretation.py — Tests for health body interpretation helpers."""

from __future__ import annotations

from agent.shared.health_models import (
    HealthInterpretation,
    extract_health_reason,
    interpret_health_body,
    summarize_dependencies,
    summarize_details,
)


class TestInterpretHealthBody:
    """Tests for interpret_health_body()."""

    def test_empty_body_returns_unknown_status(self) -> None:
        result = interpret_health_body({})
        assert isinstance(result, HealthInterpretation)
        assert result.self_reported_status == "unknown"
        assert result.ready is False
        assert result.dependency_summary == []
        assert result.details_summary == []
        assert result.restart_recommended is False
        assert result.operator_action_required is False
        assert result.parse_failure_reason is None

    def test_full_body_extracts_all_fields(self) -> None:
        body = {
            "status": "ok",
            "ready": True,
            "dependencies": [{"name": "db", "status": "down", "required": True}],
            "details": [{"component": "cache", "status": "degraded"}],
            "restart_recommended": False,
            "operator_action_required": False,
        }
        result = interpret_health_body(body)
        assert isinstance(result, HealthInterpretation)
        assert result.self_reported_status == "ok"
        assert result.ready is True
        assert len(result.dependency_summary) > 0
        assert len(result.details_summary) > 0
        assert result.restart_recommended is False
        assert result.operator_action_required is False
        assert result.parse_failure_reason is None

    def test_missing_status_defaults_to_unknown(self) -> None:
        result = interpret_health_body({"ready": True})
        assert result.self_reported_status == "unknown"

    def test_parse_exception_sets_failure_reason(self) -> None:
        bad_body: dict[str, object] = {}

        class BadBool:
            def __bool__(self) -> bool:
                raise ValueError("broken")

        bad_body["ready"] = BadBool()
        result = interpret_health_body(bad_body)
        assert result.parse_failure_reason is not None
        assert "broken" in result.parse_failure_reason

    def test_trusted_source_not_injected_by_interpreter(self) -> None:
        body = {"status": "ok", "ready": True}
        result = interpret_health_body(body)
        assert result.operator_action_required is False
        assert result.restart_recommended is False


class TestExtractHealthReason:
    """Tests for extract_health_reason()."""

    def test_priority_1_reason_field(self) -> None:
        body: dict[str, object] = {"reason": "database down"}
        assert extract_health_reason(body) == "database down"

    def test_priority_2_message_field_when_reason_absent(self) -> None:
        body: dict[str, object] = {"message": "service degraded"}
        assert extract_health_reason(body) == "service degraded"

    def test_priority_3_dependencies_when_no_reason_or_message(self) -> None:
        body: dict[str, object] = {
            "dependencies": [{"name": "db", "status": "down", "required": True}],
        }
        reason = extract_health_reason(body)
        assert reason is not None and "Dependency failure" in reason

    def test_priority_4_details_when_deps_and_reason_absent(self) -> None:
        body: dict[str, object] = {
            "details": [{"component": "cache", "status": "slow"}],
        }
        reason = extract_health_reason(body)
        assert reason is not None and "Issue:" in reason

    def test_priority_5_operator_action_required(self) -> None:
        body: dict[str, object] = {"operator_action_required": True}
        assert extract_health_reason(body) == "Operator action required"

    def test_priority_6_restart_recommended(self) -> None:
        body: dict[str, object] = {"restart_recommended": True}
        assert extract_health_reason(body) == "Restart recommended"

    def test_no_reason_when_everything_absent(self) -> None:
        body: dict[str, object] = {}
        assert extract_health_reason(body) is None

    def test_reason_overrides_message(self) -> None:
        body: dict[str, object] = {
            "reason": "explicit reason",
            "message": "fallback message",
        }
        assert extract_health_reason(body) == "explicit reason"

    def test_dependencies_override_details(self) -> None:
        body: dict[str, object] = {
            "dependencies": [{"name": "db", "status": "down"}],
            "details": [{"component": "cache", "status": "slow"}],
        }
        reason = extract_health_reason(body)
        assert reason is not None and "Dependency failure" in reason

    def test_none_body_returns_none(self) -> None:
        assert extract_health_reason(None) is None  # type: ignore[arg-type]


class TestSummarizeDependencies:
    """Tests for summarize_dependencies()."""

    def test_structured_dependencies_handled_correctly(self) -> None:
        deps: list[dict[str, object]] = [
            {
                "name": "db",
                "status": "down",
                "required": True,
                "reason": "connection refused",
            },
            {"name": "cache", "status": "ok", "required": True},
        ]
        summaries = summarize_dependencies(deps)
        assert any("db" in s and "connection refused" in s for s in summaries)
        assert not any("cache" in s for s in summaries)

    def test_string_dependencies_still_work(self) -> None:
        deps: list[str] = ["database unreachable", "cache timeout"]
        summaries = summarize_dependencies(deps)
        assert len(summaries) == 2
        assert "database unreachable" in summaries
        assert "cache timeout" in summaries

    def test_structured_dependency_missing_name_falls_back_to_status(self) -> None:
        deps: list[dict[str, object]] = [{"status": "down", "required": True}]
        summaries = summarize_dependencies(deps)
        assert len(summaries) == 1
        assert "down" in summaries[0]

    def test_ok_status_not_included(self) -> None:
        deps: list[dict[str, object]] = [
            {"name": "db", "status": "ok"},
            {"name": "cache", "status": "ok"},
        ]
        summaries = summarize_dependencies(deps)
        assert summaries == []

    def test_partial_failure_only_failed_shown(self) -> None:
        deps: list[dict[str, object]] = [
            {"name": "db", "status": "down"},
            {"name": "cache", "status": "ok"},
        ]
        summaries = summarize_dependencies(deps)
        assert len(summaries) == 1
        assert "db" in summaries[0]

    def test_no_reason_fallback_to_status(self) -> None:
        deps: list[dict[str, object]] = [{"name": "db", "status": "unreachable"}]
        summaries = summarize_dependencies(deps)
        assert "db" in summaries[0]
        assert "unreachable" in summaries[0]

    def test_large_reason_is_truncated(self) -> None:
        long_reason = "x" * 200
        deps: list[dict[str, object]] = [
            {"name": "db", "status": "down", "reason": long_reason}
        ]
        summaries = summarize_dependencies(deps)
        assert len(summaries[0]) < 200


class TestSummarizeDetails:
    """Tests for summarize_details()."""

    def test_simple_detail_summarization(self) -> None:
        details: list[dict[str, object]] = [
            {"component": "cache", "status": "degraded"},
        ]
        summaries = summarize_details(details)
        assert len(summaries) == 1
        assert "cache" in summaries[0]
        assert "degraded" in summaries[0]

    def test_large_data_payload_is_truncated(self) -> None:
        large_detail: dict[str, object] = {
            "component": "cache",
            "status": "degraded",
            "data": "x" * 1000,
        }
        summaries = summarize_details([large_detail])
        assert len(summaries[0]) < 1000

    def test_missing_component_defaults_to_unknown(self) -> None:
        details: list[dict[str, object]] = [{"status": "down"}]
        summaries = summarize_details(details)
        assert "unknown" in summaries[0]

    def test_multiple_details_preserved(self) -> None:
        details: list[dict[str, object]] = [
            {"component": "a", "status": "ok"},
            {"component": "b", "status": "degraded"},
        ]
        summaries = summarize_details(details)
        assert len(summaries) == 2

    def test_non_string_data_converted_and_truncated(self) -> None:
        details: list[dict[str, object]] = [
            {"component": "cache", "status": "degraded", "data": {"nested": "deeply"}}
        ]
        summaries = summarize_details(details)
        assert len(summaries) == 1
        assert "cache" in summaries[0]
