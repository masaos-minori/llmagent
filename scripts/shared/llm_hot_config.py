#!/usr/bin/env python3
"""shared/llm_hot_config.py — LLMClient hot-reloadable config fields."""

from typing import Any, TypeVar

_F = TypeVar("_F")


class LlmHotConfigHandler:
    """Hot-reloadable configuration for LLMClient instances."""

    HOT_CONFIG_FIELDS: tuple[tuple[str, str], ...] = (
        ("_temperature", "temperature"),
        ("_max_tokens", "max_tokens"),
        ("_max_retries", "max_retries"),
        ("_retry_base_delay", "retry_base_delay"),
        ("_sse_heartbeat_timeout", "sse_heartbeat_timeout"),
        ("_sse_malformed_retry", "sse_malformed_retry"),
        ("_sse_reconnect_max", "sse_reconnect_max"),
        ("_llm_stream_retry_on_heartbeat_timeout", "stream_retry_on_heartbeat_timeout"),
        ("_llm_stream_retry_on_malformed_chunk", "stream_retry_on_malformed_chunk"),
    )

    @staticmethod
    def apply_one(instance: object, field: str, kwarg: str, value: Any) -> None:
        """Set a single config field on an instance."""
        setattr(instance, field, value)

    @staticmethod
    def apply_config(
        instance: object,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
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
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, kwarg, value)
