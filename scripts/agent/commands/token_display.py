"""token_display.py — Token count display logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.commands.output_port import OutputPort

# TokenDisplay is a mixin that provides token count display methods.


def _token_source_label(token_is_exact: bool, tokenize_configured: bool) -> str:
    """Return a human-readable label for the token count source."""
    if token_is_exact:
        return "LLM usage"
    if tokenize_configured:
        return "/tokenize (next turn)"
    return "category-aware estimate"


class TokenDisplay:
    """Provides token count display methods."""

    _out: OutputPort  # provided by MixinBase via MRO

    def _print_token_line(self, state: Any) -> None:  # ContextStateView
        """Print token count / estimate with source label and optional limit info."""
        token_estimate = state.token_estimate or 0
        token_limit = state.token_limit
        token_limit_str = f"{token_limit:,}" if token_limit > 0 else "disabled"
        token_label = "Token count  " if state.token_is_exact else "Token estimate"
        src = _token_source_label(state.token_is_exact, state.tokenize_configured)
        if token_limit > 0:
            token_pct = int(token_estimate * 100 / token_limit)
            token_value = f"{token_estimate:,} ({src}, limit={token_limit:,} [active] {token_pct}%)"
        else:
            token_value = f"{token_estimate:,} ({src})"
        self._out.write_kv(
            [
                (token_label, token_value),
                ("Token limit     ", token_limit_str),
            ]
        )
