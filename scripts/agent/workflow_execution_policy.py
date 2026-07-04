#!/usr/bin/env python3
"""agent/workflow_execution_policy.py — Centralizes workflow_mode decisions."""

from __future__ import annotations


class WorkflowExecutionPolicy:
    """Centralizes workflow_mode decisions for Orchestrator and startup checks.

    mode="disabled": always use direct LLM path; no workflow definition required.
    mode="required": require workflow definition at startup; fail startup on errors.
    mode="auto":     allow startup degradation; fail-closed at turn time.
    """

    _VALID_MODES: frozenset[str] = frozenset({"disabled", "auto", "required"})

    def __init__(self, mode: str = "auto") -> None:
        if mode not in self._VALID_MODES:
            raise ValueError(
                f"Invalid workflow_mode {mode!r}. Must be one of: {sorted(self._VALID_MODES)}"
            )
        self._mode = mode

    @property
    def mode(self) -> str:
        return self._mode

    def is_workflow_enabled(self) -> bool:
        return self._mode != "disabled"

    def requires_startup_definition(self) -> bool:
        return self._mode == "required"

    def allow_startup_fallback(self) -> bool:
        return self._mode == "auto"

    def allow_turn_fallback(self, error: Exception) -> bool:
        return False  # fail-closed in all modes where workflow is used

    def fail_closed_on_creation_error(self) -> bool:
        return True  # WorkflowCreationError never triggers direct-execution fallback
