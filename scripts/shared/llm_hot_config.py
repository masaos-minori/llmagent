#!/usr/bin/env python3
"""scripts/shared/llm_hot_config.py — LLMClient hot-reloadable config fields.

`apply_config` is the restart-time entry.  `snapshot` and `restore` are the pair the
reload transaction uses to undo an applied LLM change, and `apply_one` returns the
undo token captured at the point of mutation (REQ-006).
"""

from typing import Any

from shared.config_undo import ServiceSnapshot, UndoToken


class LlmHotConfigHandler:
    """Hot-reloadable configuration for LLMClient instances."""

    HOT_CONFIG_FIELDS: tuple[tuple[str, str], ...] = (
        ("_temperature", "temperature"),
        ("_max_tokens", "max_tokens"),
        ("_retry_base_delay", "retry_base_delay"),
        ("_sse_heartbeat_timeout", "sse_heartbeat_timeout"),
        ("_sse_malformed_retry", "sse_malformed_retry"),
        ("_sse_reconnect_max", "sse_reconnect_max"),
        ("_llm_stream_retry_on_heartbeat_timeout", "stream_retry_on_heartbeat_timeout"),
        ("_llm_stream_retry_on_malformed_chunk", "stream_retry_on_malformed_chunk"),
    )

    @staticmethod
    def snapshot(instance: object) -> ServiceSnapshot:
        """Capture the current values of the hot-reloadable LLM fields.

        Only the fields `apply_one` can change are captured, so a restore cannot
        overwrite unrelated instance state (REQ-006).
        """
        return ServiceSnapshot(
            service="llm",
            values={
                attr: getattr(instance, attr)
                for attr, _ in LlmHotConfigHandler.HOT_CONFIG_FIELDS
            },
        )

    @staticmethod
    def restore(instance: object, snapshot: ServiceSnapshot) -> None:
        """Write the captured values back into the same instance.

        The instance is not replaced: the live `LLMClient` and the reload service
        hold references to the same object.
        """
        for attr, _ in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if attr in snapshot.values:
                setattr(instance, attr, snapshot.values[attr])

    @staticmethod
    def apply_one(instance: object, field: str, value: Any) -> UndoToken:
        """Set a single config field on an instance and return the token that undoes it.

        The previous value is captured before the `setattr`, so the token restores
        exactly what this call replaced.  Callers that ignore the return value are
        unaffected.
        """
        previous = getattr(instance, field, None)
        setattr(instance, field, value)
        return UndoToken(
            service="llm",
            field_paths=(field,),
            restore=lambda: setattr(instance, field, previous),
        )

    @staticmethod
    def apply_config(
        instance: object,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        args = dict(
            temperature=temperature,
            max_tokens=max_tokens,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)
