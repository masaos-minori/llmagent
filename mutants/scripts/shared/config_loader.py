#!/usr/bin/env python3
"""scripts/shared/config_loader.py

Shared configuration loader for agent pipeline modules.
Supports both TOML (.toml) and JSON (.json) config files.
"""

from __future__ import annotations

import logging
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import orjson

from shared.config_errors import (
    ConfigMissingError,
    ConfigParseError,
    ConfigPermissionError,
    ConfigReadError,
)

logger = logging.getLogger(__name__)


_BASE_CONFIG_FILES: tuple[str, ...] = ("agent.toml",)

_REQUIRED_CONFIG_FILES: frozenset[str] = frozenset(("agent.toml",))


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁConfigLoaderǁrestrict_to__mutmut: MutantDict = {}  # type: ignore
mutants_xǁConfigLoaderǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁConfigLoaderǁload__mutmut: MutantDict = {}  # type: ignore
mutants_xǁConfigLoaderǁload_all__mutmut: MutantDict = {}  # type: ignore
mutants_xǁConfigLoaderǁ_check_permission__mutmut: MutantDict = {}  # type: ignore
mutants_xǁConfigLoaderǁ_validate_names__mutmut: MutantDict = {}  # type: ignore
mutants_xǁConfigLoaderǁ_load_single__mutmut: MutantDict = {}  # type: ignore
mutants_xǁConfigLoaderǁ_resolve_path__mutmut: MutantDict = {}  # type: ignore
mutants_xǁConfigLoaderǁ_filter_meta_keys__mutmut: MutantDict = {}  # type: ignore
mutants_xǁConfigLoaderǁ_merge_one_level__mutmut: MutantDict = {}  # type: ignore


class ConfigLoader:
    """Load and merge TOML or JSON config files from the config/ directory."""

    # Set by restrict_to() at process startup; None means unrestricted.
    _allowed_files: frozenset[str] | None = None

    @classmethod
    @_mutmut_mutated(mutants_xǁConfigLoaderǁrestrict_to__mutmut, is_classmethod = True)
    def restrict_to(cls, *filenames: str) -> None:
        """Restrict this process to loading only the specified config files.

        Call once at process startup (before any config is loaded). Any
        subsequent call to load() or load_all() that touches a file not in
        this set raises ConfigPermissionError.
        """
        if not filenames:
            raise ValueError("restrict_to() requires at least one filename.")
        cls._allowed_files = frozenset(filenames)

    @classmethod
    def xǁConfigLoaderǁrestrict_to__mutmut_orig(cls, *filenames: str) -> None:
        """Restrict this process to loading only the specified config files.

        Call once at process startup (before any config is loaded). Any
        subsequent call to load() or load_all() that touches a file not in
        this set raises ConfigPermissionError.
        """
        if not filenames:
            raise ValueError("restrict_to() requires at least one filename.")
        cls._allowed_files = frozenset(filenames)

    @classmethod
    def xǁConfigLoaderǁrestrict_to__mutmut_1(cls, *filenames: str) -> None:
        """Restrict this process to loading only the specified config files.

        Call once at process startup (before any config is loaded). Any
        subsequent call to load() or load_all() that touches a file not in
        this set raises ConfigPermissionError.
        """
        if filenames:
            raise ValueError("restrict_to() requires at least one filename.")
        cls._allowed_files = frozenset(filenames)

    @classmethod
    def xǁConfigLoaderǁrestrict_to__mutmut_2(cls, *filenames: str) -> None:
        """Restrict this process to loading only the specified config files.

        Call once at process startup (before any config is loaded). Any
        subsequent call to load() or load_all() that touches a file not in
        this set raises ConfigPermissionError.
        """
        if not filenames:
            raise ValueError(None)
        cls._allowed_files = frozenset(filenames)

    @classmethod
    def xǁConfigLoaderǁrestrict_to__mutmut_3(cls, *filenames: str) -> None:
        """Restrict this process to loading only the specified config files.

        Call once at process startup (before any config is loaded). Any
        subsequent call to load() or load_all() that touches a file not in
        this set raises ConfigPermissionError.
        """
        if not filenames:
            raise ValueError("XXrestrict_to() requires at least one filename.XX")
        cls._allowed_files = frozenset(filenames)

    @classmethod
    def xǁConfigLoaderǁrestrict_to__mutmut_4(cls, *filenames: str) -> None:
        """Restrict this process to loading only the specified config files.

        Call once at process startup (before any config is loaded). Any
        subsequent call to load() or load_all() that touches a file not in
        this set raises ConfigPermissionError.
        """
        if not filenames:
            raise ValueError("RESTRICT_TO() REQUIRES AT LEAST ONE FILENAME.")
        cls._allowed_files = frozenset(filenames)

    @classmethod
    def xǁConfigLoaderǁrestrict_to__mutmut_5(cls, *filenames: str) -> None:
        """Restrict this process to loading only the specified config files.

        Call once at process startup (before any config is loaded). Any
        subsequent call to load() or load_all() that touches a file not in
        this set raises ConfigPermissionError.
        """
        if not filenames:
            raise ValueError("restrict_to() requires at least one filename.")
        cls._allowed_files = None

    @classmethod
    def xǁConfigLoaderǁrestrict_to__mutmut_6(cls, *filenames: str) -> None:
        """Restrict this process to loading only the specified config files.

        Call once at process startup (before any config is loaded). Any
        subsequent call to load() or load_all() that touches a file not in
        this set raises ConfigPermissionError.
        """
        if not filenames:
            raise ValueError("restrict_to() requires at least one filename.")
        cls._allowed_files = frozenset(None)

    @_mutmut_mutated(mutants_xǁConfigLoaderǁ__init____mutmut)
    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize with optional config directory path."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._config_dir = config_dir or repo_root / "config"

    def xǁConfigLoaderǁ__init____mutmut_orig(self, config_dir: Path | None = None) -> None:
        """Initialize with optional config directory path."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._config_dir = config_dir or repo_root / "config"

    def xǁConfigLoaderǁ__init____mutmut_1(self, config_dir: Path | None = None) -> None:
        """Initialize with optional config directory path."""
        repo_root = None
        self._config_dir = config_dir or repo_root / "config"

    def xǁConfigLoaderǁ__init____mutmut_2(self, config_dir: Path | None = None) -> None:
        """Initialize with optional config directory path."""
        repo_root = Path(None).resolve().parent.parent.parent
        self._config_dir = config_dir or repo_root / "config"

    def xǁConfigLoaderǁ__init____mutmut_3(self, config_dir: Path | None = None) -> None:
        """Initialize with optional config directory path."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._config_dir = None

    def xǁConfigLoaderǁ__init____mutmut_4(self, config_dir: Path | None = None) -> None:
        """Initialize with optional config directory path."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._config_dir = config_dir and repo_root / "config"

    def xǁConfigLoaderǁ__init____mutmut_5(self, config_dir: Path | None = None) -> None:
        """Initialize with optional config directory path."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._config_dir = config_dir or repo_root * "config"

    def xǁConfigLoaderǁ__init____mutmut_6(self, config_dir: Path | None = None) -> None:
        """Initialize with optional config directory path."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._config_dir = config_dir or repo_root / "XXconfigXX"

    def xǁConfigLoaderǁ__init____mutmut_7(self, config_dir: Path | None = None) -> None:
        """Initialize with optional config directory path."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        self._config_dir = config_dir or repo_root / "CONFIG"

    # -- Public API ---------------------------------------------------------

    @_mutmut_mutated(mutants_xǁConfigLoaderǁload__mutmut)
    def load(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files; keys starting with '_' are excluded; raises ValueError on missing/parse error."""
        self._validate_names(names)
        self._check_permission(names)
        merged: dict[str, Any] = {}
        for name in names:
            filtered = self._filter_meta_keys(self._load_single(name))
            merged.update(filtered)
        return merged

    # -- Public API ---------------------------------------------------------

    def xǁConfigLoaderǁload__mutmut_orig(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files; keys starting with '_' are excluded; raises ValueError on missing/parse error."""
        self._validate_names(names)
        self._check_permission(names)
        merged: dict[str, Any] = {}
        for name in names:
            filtered = self._filter_meta_keys(self._load_single(name))
            merged.update(filtered)
        return merged

    # -- Public API ---------------------------------------------------------

    def xǁConfigLoaderǁload__mutmut_1(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files; keys starting with '_' are excluded; raises ValueError on missing/parse error."""
        self._validate_names(None)
        self._check_permission(names)
        merged: dict[str, Any] = {}
        for name in names:
            filtered = self._filter_meta_keys(self._load_single(name))
            merged.update(filtered)
        return merged

    # -- Public API ---------------------------------------------------------

    def xǁConfigLoaderǁload__mutmut_2(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files; keys starting with '_' are excluded; raises ValueError on missing/parse error."""
        self._validate_names(names)
        self._check_permission(None)
        merged: dict[str, Any] = {}
        for name in names:
            filtered = self._filter_meta_keys(self._load_single(name))
            merged.update(filtered)
        return merged

    # -- Public API ---------------------------------------------------------

    def xǁConfigLoaderǁload__mutmut_3(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files; keys starting with '_' are excluded; raises ValueError on missing/parse error."""
        self._validate_names(names)
        self._check_permission(names)
        merged: dict[str, Any] = None
        for name in names:
            filtered = self._filter_meta_keys(self._load_single(name))
            merged.update(filtered)
        return merged

    # -- Public API ---------------------------------------------------------

    def xǁConfigLoaderǁload__mutmut_4(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files; keys starting with '_' are excluded; raises ValueError on missing/parse error."""
        self._validate_names(names)
        self._check_permission(names)
        merged: dict[str, Any] = {}
        for name in names:
            filtered = None
            merged.update(filtered)
        return merged

    # -- Public API ---------------------------------------------------------

    def xǁConfigLoaderǁload__mutmut_5(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files; keys starting with '_' are excluded; raises ValueError on missing/parse error."""
        self._validate_names(names)
        self._check_permission(names)
        merged: dict[str, Any] = {}
        for name in names:
            filtered = self._filter_meta_keys(None)
            merged.update(filtered)
        return merged

    # -- Public API ---------------------------------------------------------

    def xǁConfigLoaderǁload__mutmut_6(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files; keys starting with '_' are excluded; raises ValueError on missing/parse error."""
        self._validate_names(names)
        self._check_permission(names)
        merged: dict[str, Any] = {}
        for name in names:
            filtered = self._filter_meta_keys(self._load_single(None))
            merged.update(filtered)
        return merged

    # -- Public API ---------------------------------------------------------

    def xǁConfigLoaderǁload__mutmut_7(self, *names: str) -> dict[str, Any]:
        """Read and merge one or more TOML or JSON config files; keys starting with '_' are excluded; raises ValueError on missing/parse error."""
        self._validate_names(names)
        self._check_permission(names)
        merged: dict[str, Any] = {}
        for name in names:
            filtered = self._filter_meta_keys(self._load_single(name))
            merged.update(None)
        return merged

    @_mutmut_mutated(mutants_xǁConfigLoaderǁload_all__mutmut)
    def load_all(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_orig(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_1(self, strict: bool = True) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_2(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(None, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_3(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, None)
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_4(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission("load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_5(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, )
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_6(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "XXload_all()XX")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_7(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "LOAD_ALL()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_8(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = None
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_9(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = None
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_10(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(None)
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_11(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(None))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_12(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(None, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_13(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, None)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_14(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_15(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, )
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_16(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict or name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_17(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name not in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_18(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug(None, name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_19(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", None)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_20(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug(name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_21(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("Config file not found: %s", )
        return merged

    def xǁConfigLoaderǁload_all__mutmut_22(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("XXConfig file not found: %sXX", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_23(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("config file not found: %s", name)
        return merged

    def xǁConfigLoaderǁload_all__mutmut_24(self, strict: bool = False) -> dict[str, Any]:
        """Load all base config files from config/ in dependency order.

        Args:
            strict: If True, raise ConfigMissingError for any missing required
                config file. Required files are defined in _REQUIRED_CONFIG_FILES.
                If False (default), missing files are skipped with a debug log.

        Dict-valued keys are merged one level deep so that multiple MCP server
        config files can each contribute a [mcp_servers.<key>] section without
        overwriting entries from previously loaded files.
        """
        self._check_permission(_BASE_CONFIG_FILES, "load_all()")
        merged: dict[str, Any] = {}
        for name in _BASE_CONFIG_FILES:
            try:
                data = self._filter_meta_keys(self._load_single(name))
                self._merge_one_level(merged, data)
            except ConfigMissingError:
                if strict and name in _REQUIRED_CONFIG_FILES:
                    raise
                logger.debug("CONFIG FILE NOT FOUND: %S", name)
        return merged

    # -- Private helpers ----------------------------------------------------

    @_mutmut_mutated(mutants_xǁConfigLoaderǁ_check_permission__mutmut)
    def _check_permission(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(name).name
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg += f" via {context}."
                msg += f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_orig(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(name).name
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg += f" via {context}."
                msg += f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_1(self, names: tuple[str, ...], context: str = "XXXX") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(name).name
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg += f" via {context}."
                msg += f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_2(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is not None:
            return
        for name in names:
            basename = Path(name).name
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg += f" via {context}."
                msg += f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_3(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = None
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg += f" via {context}."
                msg += f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_4(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(None).name
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg += f" via {context}."
                msg += f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_5(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(name).name
            if basename in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg += f" via {context}."
                msg += f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_6(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(name).name
            if basename not in self._allowed_files:
                msg = None
                if context:
                    msg += f" via {context}."
                msg += f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_7(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(name).name
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg = f" via {context}."
                msg += f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_8(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(name).name
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg -= f" via {context}."
                msg += f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_9(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(name).name
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg += f" via {context}."
                msg = f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_10(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(name).name
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg += f" via {context}."
                msg -= f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_11(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(name).name
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg += f" via {context}."
                msg += f" Allowed: {sorted(None)}"
                raise ConfigPermissionError(msg)

    # -- Private helpers ----------------------------------------------------

    def xǁConfigLoaderǁ_check_permission__mutmut_12(self, names: tuple[str, ...], context: str = "") -> None:
        if self._allowed_files is None:
            return
        for name in names:
            basename = Path(name).name
            if basename not in self._allowed_files:
                msg = f"This process is not permitted to load '{basename}'."
                if context:
                    msg += f" via {context}."
                msg += f" Allowed: {sorted(self._allowed_files)}"
                raise ConfigPermissionError(None)

    @staticmethod
    @_mutmut_mutated(mutants_xǁConfigLoaderǁ_validate_names__mutmut)
    def _validate_names(names: tuple[Any, ...]) -> None:
        """Ensure all names are non-empty strings."""
        if not names:
            raise ValueError("At least one config file name must be provided.")
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    @staticmethod
    def xǁConfigLoaderǁ_validate_names__mutmut_orig(names: tuple[Any, ...]) -> None:
        """Ensure all names are non-empty strings."""
        if not names:
            raise ValueError("At least one config file name must be provided.")
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    @staticmethod
    def xǁConfigLoaderǁ_validate_names__mutmut_1(names: tuple[Any, ...]) -> None:
        """Ensure all names are non-empty strings."""
        if names:
            raise ValueError("At least one config file name must be provided.")
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    @staticmethod
    def xǁConfigLoaderǁ_validate_names__mutmut_2(names: tuple[Any, ...]) -> None:
        """Ensure all names are non-empty strings."""
        if not names:
            raise ValueError(None)
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    @staticmethod
    def xǁConfigLoaderǁ_validate_names__mutmut_3(names: tuple[Any, ...]) -> None:
        """Ensure all names are non-empty strings."""
        if not names:
            raise ValueError("XXAt least one config file name must be provided.XX")
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    @staticmethod
    def xǁConfigLoaderǁ_validate_names__mutmut_4(names: tuple[Any, ...]) -> None:
        """Ensure all names are non-empty strings."""
        if not names:
            raise ValueError("at least one config file name must be provided.")
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    @staticmethod
    def xǁConfigLoaderǁ_validate_names__mutmut_5(names: tuple[Any, ...]) -> None:
        """Ensure all names are non-empty strings."""
        if not names:
            raise ValueError("AT LEAST ONE CONFIG FILE NAME MUST BE PROVIDED.")
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    @staticmethod
    def xǁConfigLoaderǁ_validate_names__mutmut_6(names: tuple[Any, ...]) -> None:
        """Ensure all names are non-empty strings."""
        if not names:
            raise ValueError("At least one config file name must be provided.")
        for name in names:
            if not isinstance(name, str) and not name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    @staticmethod
    def xǁConfigLoaderǁ_validate_names__mutmut_7(names: tuple[Any, ...]) -> None:
        """Ensure all names are non-empty strings."""
        if not names:
            raise ValueError("At least one config file name must be provided.")
        for name in names:
            if isinstance(name, str) or not name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    @staticmethod
    def xǁConfigLoaderǁ_validate_names__mutmut_8(names: tuple[Any, ...]) -> None:
        """Ensure all names are non-empty strings."""
        if not names:
            raise ValueError("At least one config file name must be provided.")
        for name in names:
            if not isinstance(name, str) or name.strip():
                raise TypeError(
                    f"Config file name must be a non-empty str, got: {name!r}"
                )

    @staticmethod
    def xǁConfigLoaderǁ_validate_names__mutmut_9(names: tuple[Any, ...]) -> None:
        """Ensure all names are non-empty strings."""
        if not names:
            raise ValueError("At least one config file name must be provided.")
        for name in names:
            if not isinstance(name, str) or not name.strip():
                raise TypeError(
                    None
                )

    @_mutmut_mutated(mutants_xǁConfigLoaderǁ_load_single__mutmut)
    def _load_single(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_orig(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_1(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = None
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_2(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(None)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_3(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = None
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_4(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.upper()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_5(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix != ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_6(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == "XX.tomlXX":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_7(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".TOML":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_8(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(None)
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_9(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding=None))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_10(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="XXutf-8XX"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_11(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="UTF-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_12(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = None
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_13(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(None)
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_14(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_15(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    None
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_16(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(None).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_17(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(None)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_18(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(None) from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_19(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(None) from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_20(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(None) from exc
        except OSError as exc:
            raise ConfigReadError(f"Cannot read config file {path}: {exc}") from exc

    def xǁConfigLoaderǁ_load_single__mutmut_21(self, name: str) -> dict[str, Any]:
        """Load and parse a single config file (TOML or JSON)."""
        path = self._resolve_path(name)
        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                return tomllib.loads(path.read_text(encoding="utf-8"))
            parsed = orjson.loads(path.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Config file {path} must be a top-level mapping, got {type(parsed).__name__}"
                )
            return dict(parsed)
        except FileNotFoundError as exc:
            raise ConfigMissingError(f"Config file not found: {path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(f"Invalid TOML in {path}: {exc}") from exc
        except orjson.JSONDecodeError as exc:
            raise ConfigParseError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigReadError(None) from exc

    @_mutmut_mutated(mutants_xǁConfigLoaderǁ_resolve_path__mutmut)
    def _resolve_path(self, name: str) -> Path:
        """Resolve a config name to its full filesystem path, appending .toml extension if needed."""
        p = Path(name) if name.endswith((".toml", ".json")) else Path(f"{name}.toml")
        return self._config_dir / p.name

    def xǁConfigLoaderǁ_resolve_path__mutmut_orig(self, name: str) -> Path:
        """Resolve a config name to its full filesystem path, appending .toml extension if needed."""
        p = Path(name) if name.endswith((".toml", ".json")) else Path(f"{name}.toml")
        return self._config_dir / p.name

    def xǁConfigLoaderǁ_resolve_path__mutmut_1(self, name: str) -> Path:
        """Resolve a config name to its full filesystem path, appending .toml extension if needed."""
        p = None
        return self._config_dir / p.name

    def xǁConfigLoaderǁ_resolve_path__mutmut_2(self, name: str) -> Path:
        """Resolve a config name to its full filesystem path, appending .toml extension if needed."""
        p = Path(None) if name.endswith((".toml", ".json")) else Path(f"{name}.toml")
        return self._config_dir / p.name

    def xǁConfigLoaderǁ_resolve_path__mutmut_3(self, name: str) -> Path:
        """Resolve a config name to its full filesystem path, appending .toml extension if needed."""
        p = Path(name) if name.endswith(None) else Path(f"{name}.toml")
        return self._config_dir / p.name

    def xǁConfigLoaderǁ_resolve_path__mutmut_4(self, name: str) -> Path:
        """Resolve a config name to its full filesystem path, appending .toml extension if needed."""
        p = Path(name) if name.endswith(("XX.tomlXX", ".json")) else Path(f"{name}.toml")
        return self._config_dir / p.name

    def xǁConfigLoaderǁ_resolve_path__mutmut_5(self, name: str) -> Path:
        """Resolve a config name to its full filesystem path, appending .toml extension if needed."""
        p = Path(name) if name.endswith((".TOML", ".json")) else Path(f"{name}.toml")
        return self._config_dir / p.name

    def xǁConfigLoaderǁ_resolve_path__mutmut_6(self, name: str) -> Path:
        """Resolve a config name to its full filesystem path, appending .toml extension if needed."""
        p = Path(name) if name.endswith((".toml", "XX.jsonXX")) else Path(f"{name}.toml")
        return self._config_dir / p.name

    def xǁConfigLoaderǁ_resolve_path__mutmut_7(self, name: str) -> Path:
        """Resolve a config name to its full filesystem path, appending .toml extension if needed."""
        p = Path(name) if name.endswith((".toml", ".JSON")) else Path(f"{name}.toml")
        return self._config_dir / p.name

    def xǁConfigLoaderǁ_resolve_path__mutmut_8(self, name: str) -> Path:
        """Resolve a config name to its full filesystem path, appending .toml extension if needed."""
        p = Path(name) if name.endswith((".toml", ".json")) else Path(None)
        return self._config_dir / p.name

    def xǁConfigLoaderǁ_resolve_path__mutmut_9(self, name: str) -> Path:
        """Resolve a config name to its full filesystem path, appending .toml extension if needed."""
        p = Path(name) if name.endswith((".toml", ".json")) else Path(f"{name}.toml")
        return self._config_dir * p.name

    @staticmethod
    @_mutmut_mutated(mutants_xǁConfigLoaderǁ_filter_meta_keys__mutmut)
    def _filter_meta_keys(data: Mapping[str, Any]) -> dict[str, Any]:
        """Remove keys starting with underscore from the config data."""
        return {k: v for k, v in data.items() if not k.startswith("_")}

    @staticmethod
    def xǁConfigLoaderǁ_filter_meta_keys__mutmut_orig(data: Mapping[str, Any]) -> dict[str, Any]:
        """Remove keys starting with underscore from the config data."""
        return {k: v for k, v in data.items() if not k.startswith("_")}

    @staticmethod
    def xǁConfigLoaderǁ_filter_meta_keys__mutmut_1(data: Mapping[str, Any]) -> dict[str, Any]:
        """Remove keys starting with underscore from the config data."""
        return {k: v for k, v in data.items() if k.startswith("_")}

    @staticmethod
    def xǁConfigLoaderǁ_filter_meta_keys__mutmut_2(data: Mapping[str, Any]) -> dict[str, Any]:
        """Remove keys starting with underscore from the config data."""
        return {k: v for k, v in data.items() if not k.startswith(None)}

    @staticmethod
    def xǁConfigLoaderǁ_filter_meta_keys__mutmut_3(data: Mapping[str, Any]) -> dict[str, Any]:
        """Remove keys starting with underscore from the config data."""
        return {k: v for k, v in data.items() if not k.startswith("XX_XX")}

    @staticmethod
    @_mutmut_mutated(mutants_xǁConfigLoaderǁ_merge_one_level__mutmut)
    def _merge_one_level(merged: dict[str, Any], data: Mapping[str, Any]) -> None:
        """Merge `data` into `merged` in place, combining dict values one level deep."""
        for key, val in data.items():
            if isinstance(val, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **val}
            else:
                merged[key] = val

    @staticmethod
    def xǁConfigLoaderǁ_merge_one_level__mutmut_orig(merged: dict[str, Any], data: Mapping[str, Any]) -> None:
        """Merge `data` into `merged` in place, combining dict values one level deep."""
        for key, val in data.items():
            if isinstance(val, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **val}
            else:
                merged[key] = val

    @staticmethod
    def xǁConfigLoaderǁ_merge_one_level__mutmut_1(merged: dict[str, Any], data: Mapping[str, Any]) -> None:
        """Merge `data` into `merged` in place, combining dict values one level deep."""
        for key, val in data.items():
            if isinstance(val, dict) or isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **val}
            else:
                merged[key] = val

    @staticmethod
    def xǁConfigLoaderǁ_merge_one_level__mutmut_2(merged: dict[str, Any], data: Mapping[str, Any]) -> None:
        """Merge `data` into `merged` in place, combining dict values one level deep."""
        for key, val in data.items():
            if isinstance(val, dict) and isinstance(merged.get(key), dict):
                merged[key] = None
            else:
                merged[key] = val

    @staticmethod
    def xǁConfigLoaderǁ_merge_one_level__mutmut_3(merged: dict[str, Any], data: Mapping[str, Any]) -> None:
        """Merge `data` into `merged` in place, combining dict values one level deep."""
        for key, val in data.items():
            if isinstance(val, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **val}
            else:
                merged[key] = None

mutants_xǁConfigLoaderǁrestrict_to__mutmut['_mutmut_orig'] = ConfigLoader.xǁConfigLoaderǁrestrict_to__mutmut_orig # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁrestrict_to__mutmut['xǁConfigLoaderǁrestrict_to__mutmut_1'] = ConfigLoader.xǁConfigLoaderǁrestrict_to__mutmut_1 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁrestrict_to__mutmut['xǁConfigLoaderǁrestrict_to__mutmut_2'] = ConfigLoader.xǁConfigLoaderǁrestrict_to__mutmut_2 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁrestrict_to__mutmut['xǁConfigLoaderǁrestrict_to__mutmut_3'] = ConfigLoader.xǁConfigLoaderǁrestrict_to__mutmut_3 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁrestrict_to__mutmut['xǁConfigLoaderǁrestrict_to__mutmut_4'] = ConfigLoader.xǁConfigLoaderǁrestrict_to__mutmut_4 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁrestrict_to__mutmut['xǁConfigLoaderǁrestrict_to__mutmut_5'] = ConfigLoader.xǁConfigLoaderǁrestrict_to__mutmut_5 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁrestrict_to__mutmut['xǁConfigLoaderǁrestrict_to__mutmut_6'] = ConfigLoader.xǁConfigLoaderǁrestrict_to__mutmut_6 # type: ignore # mutmut generated

mutants_xǁConfigLoaderǁ__init____mutmut['_mutmut_orig'] = ConfigLoader.xǁConfigLoaderǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ__init____mutmut['xǁConfigLoaderǁ__init____mutmut_1'] = ConfigLoader.xǁConfigLoaderǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ__init____mutmut['xǁConfigLoaderǁ__init____mutmut_2'] = ConfigLoader.xǁConfigLoaderǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ__init____mutmut['xǁConfigLoaderǁ__init____mutmut_3'] = ConfigLoader.xǁConfigLoaderǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ__init____mutmut['xǁConfigLoaderǁ__init____mutmut_4'] = ConfigLoader.xǁConfigLoaderǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ__init____mutmut['xǁConfigLoaderǁ__init____mutmut_5'] = ConfigLoader.xǁConfigLoaderǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ__init____mutmut['xǁConfigLoaderǁ__init____mutmut_6'] = ConfigLoader.xǁConfigLoaderǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ__init____mutmut['xǁConfigLoaderǁ__init____mutmut_7'] = ConfigLoader.xǁConfigLoaderǁ__init____mutmut_7 # type: ignore # mutmut generated

mutants_xǁConfigLoaderǁload__mutmut['_mutmut_orig'] = ConfigLoader.xǁConfigLoaderǁload__mutmut_orig # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload__mutmut['xǁConfigLoaderǁload__mutmut_1'] = ConfigLoader.xǁConfigLoaderǁload__mutmut_1 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload__mutmut['xǁConfigLoaderǁload__mutmut_2'] = ConfigLoader.xǁConfigLoaderǁload__mutmut_2 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload__mutmut['xǁConfigLoaderǁload__mutmut_3'] = ConfigLoader.xǁConfigLoaderǁload__mutmut_3 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload__mutmut['xǁConfigLoaderǁload__mutmut_4'] = ConfigLoader.xǁConfigLoaderǁload__mutmut_4 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload__mutmut['xǁConfigLoaderǁload__mutmut_5'] = ConfigLoader.xǁConfigLoaderǁload__mutmut_5 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload__mutmut['xǁConfigLoaderǁload__mutmut_6'] = ConfigLoader.xǁConfigLoaderǁload__mutmut_6 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload__mutmut['xǁConfigLoaderǁload__mutmut_7'] = ConfigLoader.xǁConfigLoaderǁload__mutmut_7 # type: ignore # mutmut generated

mutants_xǁConfigLoaderǁload_all__mutmut['_mutmut_orig'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_orig # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_1'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_1 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_2'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_2 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_3'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_3 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_4'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_4 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_5'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_5 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_6'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_6 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_7'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_7 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_8'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_8 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_9'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_9 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_10'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_10 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_11'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_11 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_12'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_12 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_13'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_13 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_14'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_14 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_15'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_15 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_16'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_16 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_17'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_17 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_18'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_18 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_19'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_19 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_20'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_20 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_21'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_21 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_22'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_22 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_23'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_23 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁload_all__mutmut['xǁConfigLoaderǁload_all__mutmut_24'] = ConfigLoader.xǁConfigLoaderǁload_all__mutmut_24 # type: ignore # mutmut generated

mutants_xǁConfigLoaderǁ_check_permission__mutmut['_mutmut_orig'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_orig # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_1'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_1 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_2'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_2 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_3'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_3 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_4'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_4 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_5'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_5 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_6'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_6 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_7'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_7 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_8'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_8 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_9'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_9 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_10'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_10 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_11'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_11 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_check_permission__mutmut['xǁConfigLoaderǁ_check_permission__mutmut_12'] = ConfigLoader.xǁConfigLoaderǁ_check_permission__mutmut_12 # type: ignore # mutmut generated

mutants_xǁConfigLoaderǁ_validate_names__mutmut['_mutmut_orig'] = ConfigLoader.xǁConfigLoaderǁ_validate_names__mutmut_orig # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_validate_names__mutmut['xǁConfigLoaderǁ_validate_names__mutmut_1'] = ConfigLoader.xǁConfigLoaderǁ_validate_names__mutmut_1 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_validate_names__mutmut['xǁConfigLoaderǁ_validate_names__mutmut_2'] = ConfigLoader.xǁConfigLoaderǁ_validate_names__mutmut_2 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_validate_names__mutmut['xǁConfigLoaderǁ_validate_names__mutmut_3'] = ConfigLoader.xǁConfigLoaderǁ_validate_names__mutmut_3 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_validate_names__mutmut['xǁConfigLoaderǁ_validate_names__mutmut_4'] = ConfigLoader.xǁConfigLoaderǁ_validate_names__mutmut_4 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_validate_names__mutmut['xǁConfigLoaderǁ_validate_names__mutmut_5'] = ConfigLoader.xǁConfigLoaderǁ_validate_names__mutmut_5 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_validate_names__mutmut['xǁConfigLoaderǁ_validate_names__mutmut_6'] = ConfigLoader.xǁConfigLoaderǁ_validate_names__mutmut_6 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_validate_names__mutmut['xǁConfigLoaderǁ_validate_names__mutmut_7'] = ConfigLoader.xǁConfigLoaderǁ_validate_names__mutmut_7 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_validate_names__mutmut['xǁConfigLoaderǁ_validate_names__mutmut_8'] = ConfigLoader.xǁConfigLoaderǁ_validate_names__mutmut_8 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_validate_names__mutmut['xǁConfigLoaderǁ_validate_names__mutmut_9'] = ConfigLoader.xǁConfigLoaderǁ_validate_names__mutmut_9 # type: ignore # mutmut generated

mutants_xǁConfigLoaderǁ_load_single__mutmut['_mutmut_orig'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_orig # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_1'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_1 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_2'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_2 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_3'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_3 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_4'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_4 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_5'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_5 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_6'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_6 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_7'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_7 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_8'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_8 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_9'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_9 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_10'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_10 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_11'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_11 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_12'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_12 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_13'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_13 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_14'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_14 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_15'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_15 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_16'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_16 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_17'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_17 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_18'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_18 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_19'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_19 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_20'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_20 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_load_single__mutmut['xǁConfigLoaderǁ_load_single__mutmut_21'] = ConfigLoader.xǁConfigLoaderǁ_load_single__mutmut_21 # type: ignore # mutmut generated

mutants_xǁConfigLoaderǁ_resolve_path__mutmut['_mutmut_orig'] = ConfigLoader.xǁConfigLoaderǁ_resolve_path__mutmut_orig # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_resolve_path__mutmut['xǁConfigLoaderǁ_resolve_path__mutmut_1'] = ConfigLoader.xǁConfigLoaderǁ_resolve_path__mutmut_1 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_resolve_path__mutmut['xǁConfigLoaderǁ_resolve_path__mutmut_2'] = ConfigLoader.xǁConfigLoaderǁ_resolve_path__mutmut_2 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_resolve_path__mutmut['xǁConfigLoaderǁ_resolve_path__mutmut_3'] = ConfigLoader.xǁConfigLoaderǁ_resolve_path__mutmut_3 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_resolve_path__mutmut['xǁConfigLoaderǁ_resolve_path__mutmut_4'] = ConfigLoader.xǁConfigLoaderǁ_resolve_path__mutmut_4 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_resolve_path__mutmut['xǁConfigLoaderǁ_resolve_path__mutmut_5'] = ConfigLoader.xǁConfigLoaderǁ_resolve_path__mutmut_5 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_resolve_path__mutmut['xǁConfigLoaderǁ_resolve_path__mutmut_6'] = ConfigLoader.xǁConfigLoaderǁ_resolve_path__mutmut_6 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_resolve_path__mutmut['xǁConfigLoaderǁ_resolve_path__mutmut_7'] = ConfigLoader.xǁConfigLoaderǁ_resolve_path__mutmut_7 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_resolve_path__mutmut['xǁConfigLoaderǁ_resolve_path__mutmut_8'] = ConfigLoader.xǁConfigLoaderǁ_resolve_path__mutmut_8 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_resolve_path__mutmut['xǁConfigLoaderǁ_resolve_path__mutmut_9'] = ConfigLoader.xǁConfigLoaderǁ_resolve_path__mutmut_9 # type: ignore # mutmut generated

mutants_xǁConfigLoaderǁ_filter_meta_keys__mutmut['_mutmut_orig'] = ConfigLoader.xǁConfigLoaderǁ_filter_meta_keys__mutmut_orig # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_filter_meta_keys__mutmut['xǁConfigLoaderǁ_filter_meta_keys__mutmut_1'] = ConfigLoader.xǁConfigLoaderǁ_filter_meta_keys__mutmut_1 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_filter_meta_keys__mutmut['xǁConfigLoaderǁ_filter_meta_keys__mutmut_2'] = ConfigLoader.xǁConfigLoaderǁ_filter_meta_keys__mutmut_2 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_filter_meta_keys__mutmut['xǁConfigLoaderǁ_filter_meta_keys__mutmut_3'] = ConfigLoader.xǁConfigLoaderǁ_filter_meta_keys__mutmut_3 # type: ignore # mutmut generated

mutants_xǁConfigLoaderǁ_merge_one_level__mutmut['_mutmut_orig'] = ConfigLoader.xǁConfigLoaderǁ_merge_one_level__mutmut_orig # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_merge_one_level__mutmut['xǁConfigLoaderǁ_merge_one_level__mutmut_1'] = ConfigLoader.xǁConfigLoaderǁ_merge_one_level__mutmut_1 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_merge_one_level__mutmut['xǁConfigLoaderǁ_merge_one_level__mutmut_2'] = ConfigLoader.xǁConfigLoaderǁ_merge_one_level__mutmut_2 # type: ignore # mutmut generated
mutants_xǁConfigLoaderǁ_merge_one_level__mutmut['xǁConfigLoaderǁ_merge_one_level__mutmut_3'] = ConfigLoader.xǁConfigLoaderǁ_merge_one_level__mutmut_3 # type: ignore # mutmut generated
