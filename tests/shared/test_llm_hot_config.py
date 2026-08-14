"""Characterization tests for LlmHotConfigHandler."""

from shared.llm_hot_config import LlmHotConfigHandler


class MockInstance:
    """Mock instance with all hot-configurable fields initialized."""

    _temperature: float = 0.7
    _max_tokens: int = 100
    _max_retries: int = 3
    _retry_base_delay: float = 1.0
    _sse_heartbeat_timeout: float = 30.0
    _sse_malformed_retry: int = 3
    _sse_reconnect_max: int = 5
    _llm_stream_retry_on_heartbeat_timeout: bool = True
    _llm_stream_retry_on_malformed_chunk: bool = True


def test_apply_one_sets_field() -> None:
    """apply_one sets a single field via setattr."""
    inst = MockInstance()
    LlmHotConfigHandler.apply_one(inst, "_temperature", 0.9)
    assert inst._temperature == 0.9


def test_apply_one_sets_non_float_field() -> None:
    """apply_one works with non-float types (int, bool)."""
    inst = MockInstance()
    LlmHotConfigHandler.apply_one(inst, "_max_tokens", 200)
    assert inst._max_tokens == 200
    LlmHotConfigHandler.apply_one(
        inst,
        "_llm_stream_retry_on_heartbeat_timeout",
        False,
    )
    assert inst._llm_stream_retry_on_heartbeat_timeout is False


def test_apply_config_applies_only_non_none_values() -> None:
    """apply_config applies only non-None values; other fields remain unchanged."""
    inst = MockInstance()
    original_max_tokens = inst._max_tokens
    LlmHotConfigHandler.apply_config(inst, temperature=0.9)
    assert inst._temperature == 0.9
    assert inst._max_tokens == original_max_tokens  # unchanged


def test_apply_config_partial_update() -> None:
    """apply_config updates only specified fields; others stay at their defaults."""
    inst = MockInstance()
    LlmHotConfigHandler.apply_config(inst, temperature=0.9, max_tokens=200)
    assert inst._temperature == 0.9
    assert inst._max_tokens == 200
    assert inst._max_retries == 3  # unchanged default


def test_apply_config_all_fields() -> None:
    """apply_config with all fields updates every field correctly."""
    inst = MockInstance()
    LlmHotConfigHandler.apply_config(
        inst,
        temperature=0.9,
        max_tokens=200,
        max_retries=5,
        retry_base_delay=2.0,
        sse_heartbeat_timeout=60.0,
        sse_malformed_retry=5,
        sse_reconnect_max=10,
        stream_retry_on_heartbeat_timeout=False,
        stream_retry_on_malformed_chunk=False,
    )
    assert inst._temperature == 0.9
    assert inst._max_tokens == 200
    assert inst._max_retries == 5
    assert inst._retry_base_delay == 2.0
    assert inst._sse_heartbeat_timeout == 60.0
    assert inst._sse_malformed_retry == 5
    assert inst._sse_reconnect_max == 10
    assert inst._llm_stream_retry_on_heartbeat_timeout is False
    assert inst._llm_stream_retry_on_malformed_chunk is False


def test_apply_config_no_updates_when_all_none() -> None:
    """When all kwargs are None, no fields are modified."""
    inst = MockInstance()
    orig_attrs = {
        attr: getattr(inst, attr) for attr, _ in LlmHotConfigHandler.HOT_CONFIG_FIELDS
    }
    LlmHotConfigHandler.apply_config(inst)
    for attr in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
        assert getattr(inst, attr[0]) == orig_attrs[attr[0]]


def test_apply_config_false_bool_value_is_applied() -> None:
    """Boolean False is applied because it is not None."""
    inst = MockInstance()
    LlmHotConfigHandler.apply_config(inst, stream_retry_on_heartbeat_timeout=False)
    assert inst._llm_stream_retry_on_heartbeat_timeout is False


def test_apply_config_zero_value_is_applied() -> None:
    """Integer zero is applied because it is not None."""
    inst = MockInstance()
    LlmHotConfigHandler.apply_config(inst, sse_malformed_retry=0)
    assert inst._sse_malformed_retry == 0
