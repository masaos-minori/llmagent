"""mcp/github/formatter.py
Presentation helpers extracted from service.py.

dry_run_preview: formats a dry-run operation preview string.
Full fmt_* function extraction is deferred (service.py retains instance methods
as backward-compat wrappers for the dispatch table).
"""


def dry_run_preview(preview: str) -> str:
    """Wrap a dry-run preview message with a standard prefix."""
    return f"[DRY RUN] The following would be executed:\n{preview}"
