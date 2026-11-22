"""scripts/agent/prompt_source.py — Typed prompt-source model and the single
reader for prompt content.

Encodes the agentcfg005 single-source contract: prompt content lives only in
``registry/manifests/prompt_source.toml``, and both the startup path
(``agent.startup_prompt_setup``) and the reload path
(``agent.services.config_reload``) read it through this module. The reader is a
read boundary: a missing file or a missing ``default`` entry raises at the read
boundary rather than substituting a silent default. Imports stdlib and the
shared resolver only, so ``shared`` stays a leaf module (import-linter
``shared-is-leaf`` contract).
"""

from __future__ import annotations

import dataclasses
import tomllib
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

from shared.runtime_paths import resolve_registry_dir

# Source file inside the resolved registry directory (manifests/ subdirectory,
# the location recorded by the plan; the whole directory is rsynced by deploy).
_MANIFESTS_DIR = "manifests"
_SOURCE_FILE_NAME = "prompt_source.toml"

# Entry whose absence is an error at the read boundary (no silent default).
_REQUIRED_ENTRY = "default"


class PromptSourceError(Exception):
    """Base error for any missing, unparseable, or malformed prompt source."""


@dataclasses.dataclass(frozen=True)
class PromptSource:
    """Prompt name to content, as read from the single source (read-only)."""

    entries: Mapping[str, str]

    def content(self, name: str) -> str:
        """Return the content for *name*, falling back to ``default``.

        The caller passes the name; this module does not select it. The
        fallback shape matches the historical lookup (requested name, then the
        default entry), which is guaranteed to exist by the reader.
        """
        return self.entries.get(name, self.entries[_REQUIRED_ENTRY])


def default_source_path() -> Path:
    """Return the source file path for the resolved registry directory.

    Resolved per call so an ``LLMAGENT_REGISTRY_DIR`` change takes effect
    without re-importing (a compiled binary cannot locate the repository
    directory through ``__file__``).
    """
    return resolve_registry_dir() / _MANIFESTS_DIR / _SOURCE_FILE_NAME


def _validate_entries(raw: object) -> Mapping[str, str]:
    if not isinstance(raw, dict):
        raise PromptSourceError(
            f"Prompt source top level must be a mapping of name to content, "
            f"got {type(raw).__name__}"
        )
    entries: dict[str, str] = {}
    for name, value in raw.items():
        if not isinstance(name, str) or not name.strip():
            raise PromptSourceError(
                f"Prompt source key {name!r} must be a non-empty string"
            )
        if not isinstance(value, str) or not value.strip():
            raise PromptSourceError(
                f"Prompt source entry {name!r} must be a non-empty string"
            )
        entries[name] = value
    if _REQUIRED_ENTRY not in entries:
        raise PromptSourceError(
            f"Prompt source is missing the required {_REQUIRED_ENTRY!r} entry; "
            "no silent default is applied (single-source contract)."
        )
    return MappingProxyType(entries)


def load_prompt_source(path: str | Path | None = None) -> PromptSource:
    """Load and validate the single prompt source.

    Raises:
        PromptSourceError: If the file is missing, unparseable, has a
            non-mapping top level, a malformed or empty entry, or is missing
            the required ``default`` entry.

    Returns:
        The frozen typed model holding the read-only name-to-content mapping.
    """
    target = Path(path) if path is not None else default_source_path()
    try:
        raw = tomllib.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PromptSourceError(f"Prompt source not found: {target}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise PromptSourceError(
            f"Prompt source is not parseable as TOML: {target}"
        ) from exc
    return PromptSource(entries=_validate_entries(raw))
