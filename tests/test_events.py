"""
tests/test_events.py
Unit tests for shared/events.py.
"""

from __future__ import annotations

from shared.events import ArtifactEvent


class TestArtifactEvent:
    def test_empty_dict_is_valid(self) -> None:
        ev: ArtifactEvent = {}
        assert isinstance(ev, dict)

    def test_all_fields_constructable(self) -> None:
        ev: ArtifactEvent = {
            "event_type": "artifact.updated",
            "repo": "owner/repo",
            "branch": "main",
            "commit": "abc12345",
            "path": "scripts/agent/repl.py",
            "pr_number": 42,
            "session_id": 7,
            "timestamp": "2026-06-17T00:00:00Z",
        }
        assert ev["event_type"] == "artifact.updated"
        assert ev["repo"] == "owner/repo"
        assert ev["branch"] == "main"
        assert ev["commit"] == "abc12345"
        assert ev["path"] == "scripts/agent/repl.py"
        assert ev["pr_number"] == 42
        assert ev["session_id"] == 7
        assert ev["timestamp"] == "2026-06-17T00:00:00Z"

    def test_partial_fields(self) -> None:
        ev: ArtifactEvent = {"event_type": "artifact.created", "repo": "a/b"}
        assert ev["event_type"] == "artifact.created"
        assert "branch" not in ev

    def test_event_types(self) -> None:
        for et in ("artifact.updated", "artifact.created", "artifact.deleted"):
            ev: ArtifactEvent = {"event_type": et}
            assert ev["event_type"] == et
