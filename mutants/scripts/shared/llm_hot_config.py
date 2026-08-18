#!/usr/bin/env python3
"""scripts/shared/llm_hot_config.py — LLMClient hot-reloadable config fields."""

from typing import Any


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁLlmHotConfigHandlerǁapply_one__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut: MutantDict = {}  # type: ignore


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
    @_mutmut_mutated(mutants_xǁLlmHotConfigHandlerǁapply_one__mutmut)
    def apply_one(instance: object, field: str, value: Any) -> None:
        """Set a single config field on an instance."""
        setattr(instance, field, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_one__mutmut_orig(instance: object, field: str, value: Any) -> None:
        """Set a single config field on an instance."""
        setattr(instance, field, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_one__mutmut_1(instance: object, field: str, value: Any) -> None:
        """Set a single config field on an instance."""
        setattr(None, field, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_one__mutmut_2(instance: object, field: str, value: Any) -> None:
        """Set a single config field on an instance."""
        setattr(instance, None, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_one__mutmut_3(instance: object, field: str, value: Any) -> None:
        """Set a single config field on an instance."""
        setattr(instance, field, None)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_one__mutmut_4(instance: object, field: str, value: Any) -> None:
        """Set a single config field on an instance."""
        setattr(field, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_one__mutmut_5(instance: object, field: str, value: Any) -> None:
        """Set a single config field on an instance."""
        setattr(instance, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_one__mutmut_6(instance: object, field: str, value: Any) -> None:
        """Set a single config field on an instance."""
        setattr(instance, field, )

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut)
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
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_orig(
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
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_1(
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
        args = None
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_2(
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
            temperatureXX=temperature,
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
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_3(
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
            max_tokensXX=max_tokens,
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
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_4(
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
            max_retriesXX=max_retries,
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

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_5(
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
            retry_base_delayXX=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_6(
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
            sse_heartbeat_timeoutXX=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_7(
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
            sse_malformed_retryXX=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_8(
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
            sse_reconnect_maxXX=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_9(
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
            stream_retry_on_heartbeat_timeoutXX=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_10(
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
            stream_retry_on_malformed_chunkXX=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_11(
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
            temperature=None,
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
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_12(
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
            max_tokens=None,
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
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_13(
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
            max_retries=None,
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

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_14(
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
            retry_base_delay=None,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_15(
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
            sse_heartbeat_timeout=None,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_16(
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
            sse_malformed_retry=None,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_17(
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
            sse_reconnect_max=None,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_18(
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
            stream_retry_on_heartbeat_timeout=None,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_19(
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
            stream_retry_on_malformed_chunk=None,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_20(
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
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_21(
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
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_22(
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

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_23(
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
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_24(
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
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_25(
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
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_26(
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
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_27(
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
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_28(
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
            )
        for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
            if (value := args.get(kwarg)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_29(
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
            if (value := args.get(None)) is not None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_30(
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
            if (value := args.get(kwarg)) is None:
                LlmHotConfigHandler.apply_one(instance, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_31(
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
                LlmHotConfigHandler.apply_one(None, attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_32(
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
                LlmHotConfigHandler.apply_one(instance, None, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_33(
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
                LlmHotConfigHandler.apply_one(instance, attr, None)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_34(
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
                LlmHotConfigHandler.apply_one(attr, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_35(
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
                LlmHotConfigHandler.apply_one(instance, value)

    @staticmethod
    def xǁLlmHotConfigHandlerǁapply_config__mutmut_36(
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
                LlmHotConfigHandler.apply_one(instance, attr, )

mutants_xǁLlmHotConfigHandlerǁapply_one__mutmut['_mutmut_orig'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_one__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_one__mutmut['xǁLlmHotConfigHandlerǁapply_one__mutmut_1'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_one__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_one__mutmut['xǁLlmHotConfigHandlerǁapply_one__mutmut_2'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_one__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_one__mutmut['xǁLlmHotConfigHandlerǁapply_one__mutmut_3'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_one__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_one__mutmut['xǁLlmHotConfigHandlerǁapply_one__mutmut_4'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_one__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_one__mutmut['xǁLlmHotConfigHandlerǁapply_one__mutmut_5'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_one__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_one__mutmut['xǁLlmHotConfigHandlerǁapply_one__mutmut_6'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_one__mutmut_6 # type: ignore # mutmut generated

mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['_mutmut_orig'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_1'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_2'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_3'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_4'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_5'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_6'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_7'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_8'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_9'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_10'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_11'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_12'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_13'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_14'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_15'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_16'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_17'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_18'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_19'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_20'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_21'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_22'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_23'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_24'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_25'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_26'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_27'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_28'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_29'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_30'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_31'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_32'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_33'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_34'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_35'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLlmHotConfigHandlerǁapply_config__mutmut['xǁLlmHotConfigHandlerǁapply_config__mutmut_36'] = LlmHotConfigHandler.xǁLlmHotConfigHandlerǁapply_config__mutmut_36 # type: ignore # mutmut generated
