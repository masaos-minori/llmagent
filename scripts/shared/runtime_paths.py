#!/usr/bin/env python3
"""scripts/shared/runtime_paths.py

Standard-library-only resolvers for the shared package that locate (a) the agent
config directory, (b) the Sudachi dictionary path, and (c) the registry directory
so all three resolve correctly inside a Nuitka ``--onefile`` binary while remaining
backward compatible with ``uv run``.

Implements (config-dir resolver), (Sudachi-dict resolver), and (registry-dir
resolver).
Callers import the symbols they need::

    from shared.runtime_paths import resolve_config_dir, resolve_registry_dir
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

# A Nuitka ``--onefile`` binary lives at ``/opt/llm/bin/<binary>`` (two levels
# below the install root), so the adjacent ``config/`` root is ``sys.argv[0]``'s
# parent.parent. Computed at import; only *used* behind the ``__compiled__``
# guard below, so it is harmless during a ``uv run`` development run.
_COMPILED_CONFIG_ROOT = Path(sys.argv[0]).resolve().parent.parent / "config"
# Installed Sudachi dictionary used by a compiled binary.
_COMPILED_SUDACHI_DICT = "/opt/llm/dict/system.dic"
# Legacy repository-root ``config/`` used outside a compiled binary.
_REPO_ROOT_CONFIG = Path(__file__).resolve().parent.parent.parent / "config"
# Registry directory deployed beside the install root (a compiled binary's
# ``__file__`` lives under a randomized /tmp onefile payload, so it cannot
# locate the repository-relative ``registry/`` on its own).
_COMPILED_REGISTRY_ROOT = Path(sys.argv[0]).resolve().parent.parent / "registry"
# Legacy repository-root ``registry/`` used outside a compiled binary.
_REPO_ROOT_REGISTRY = Path(__file__).resolve().parent.parent.parent / "registry"


def _assert_env_path(env_value: str, *, must_be_dir: bool) -> Path:
    """Return ``env_value`` as a ``Path``, failing fast if it does not exist.

    Raises:
        FileNotFoundError: If the path is missing, or is a file where a
            directory is required (or vice versa). The message names the
            offending path so callers get an actionable error instead of a
            silent fallback.
    """
    path = Path(env_value)
    if must_be_dir:
        if not path.is_dir():
            raise FileNotFoundError(f"Directory not found: {path}")
    elif not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    return path


def resolve_config_dir(config_dir: str | Path | None = None) -> Path:
    """Resolve the agent config directory.

    Precedence: explicit ``config_dir`` argument > ``LLMAGENT_CONFIG_DIR`` (must
    exist) > compiled-adjacent ``config/`` (only when ``__compiled__`` is
    present) > legacy repository-root ``config/``.

    Raises:
        FileNotFoundError: If ``LLMAGENT_CONFIG_DIR`` is set to a missing path.
    """
    if config_dir is not None:
        return Path(config_dir)
    if env := os.environ.get("LLMAGENT_CONFIG_DIR"):
        return _assert_env_path(env, must_be_dir=True)
    if "__compiled__" in globals():
        return Path(_COMPILED_CONFIG_ROOT)
    return Path(_REPO_ROOT_CONFIG)


def resolve_registry_dir(registry_dir: str | Path | None = None) -> Path:
    """Resolve the directory holding the machine-readable registries.

    Precedence: explicit ``registry_dir`` argument > ``LLMAGENT_REGISTRY_DIR``
    (must exist) > compiled-adjacent ``registry/`` (only when ``__compiled__``
    is present) > legacy repository-root ``registry/``.

    Raises:
        FileNotFoundError: If ``LLMAGENT_REGISTRY_DIR`` is set to a missing path.
    """
    if registry_dir is not None:
        return Path(registry_dir)
    if env := os.environ.get("LLMAGENT_REGISTRY_DIR"):
        return _assert_env_path(env, must_be_dir=True)
    if "__compiled__" in globals():
        return Path(_COMPILED_REGISTRY_ROOT)
    return Path(_REPO_ROOT_REGISTRY)


def resolve_sudachi_dict_path(
    dict_path: str | None = None,
) -> Path | Literal["core"]:
    """Resolve the Sudachi dictionary argument for ``Dictionary(...)``.

    Precedence: ``LLMAGENT_SUDACHI_DICT`` (must exist) > compiled default
    ``/opt/llm/dict/system.dic`` (only when ``__compiled__`` is present) > the
    literal ``"core"`` for ``uv run`` development.

    Raises:
        FileNotFoundError: If ``LLMAGENT_SUDACHI_DICT`` or the compiled default
            points at a missing file.
    """
    if env := os.environ.get("LLMAGENT_SUDACHI_DICT"):
        return _assert_env_path(env, must_be_dir=False)
    if "__compiled__" in globals():
        default = Path(_COMPILED_SUDACHI_DICT)
        if not default.is_file():
            raise FileNotFoundError(f"Sudachi dictionary not found: {default}")
        return default
    return "core"
