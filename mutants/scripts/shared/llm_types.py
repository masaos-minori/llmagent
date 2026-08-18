"""scripts/shared/llm_types.py

Typed DTOs for LLM response handling.

Defined separately from llm_client.py so callers can import the DTOs
without importing the full LLMClient.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.types import LLMMessage


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@dataclass(frozen=True)
class LLMUsage:
    """Token usage reported by one LLM API call."""

    prompt_tokens: int
    completion_tokens: int


@dataclass(frozen=True)
class LLMResponse:
    """Structured result from LLMClient.call() or .stream()."""

    message: LLMMessage
    finish_reason: str | None
    usage: LLMUsage | None = None
