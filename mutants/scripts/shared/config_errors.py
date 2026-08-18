#!/usr/bin/env python3
"""scripts/shared/config_errors.py — Configuration loading error classes."""


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


class ConfigMissingError(ValueError):
    """Config file does not exist."""


class ConfigParseError(ValueError):
    """Config file exists but cannot be parsed."""


class ConfigReadError(ValueError):
    """Config file exists but cannot be read (permission, I/O)."""


class ConfigPermissionError(RuntimeError):
    """Process attempted to load a config file it is not permitted to access."""
mutants_xǁConfigLoadErrorǁ__init____mutmut: MutantDict = {}  # type: ignore


class ConfigLoadError(RuntimeError):
    """Raised when configuration files cannot be loaded."""

    @_mutmut_mutated(mutants_xǁConfigLoadErrorǁ__init____mutmut)
    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize with an optional chained exception cause."""
        if cause is not None:
            full_message = (
                f"Config load failed ({type(cause).__name__}: {cause}): {message}"
            )
        else:
            full_message = message
        super().__init__(full_message)

    def xǁConfigLoadErrorǁ__init____mutmut_orig(self, message: str, cause: Exception | None = None) -> None:
        """Initialize with an optional chained exception cause."""
        if cause is not None:
            full_message = (
                f"Config load failed ({type(cause).__name__}: {cause}): {message}"
            )
        else:
            full_message = message
        super().__init__(full_message)

    def xǁConfigLoadErrorǁ__init____mutmut_1(self, message: str, cause: Exception | None = None) -> None:
        """Initialize with an optional chained exception cause."""
        if cause is None:
            full_message = (
                f"Config load failed ({type(cause).__name__}: {cause}): {message}"
            )
        else:
            full_message = message
        super().__init__(full_message)

    def xǁConfigLoadErrorǁ__init____mutmut_2(self, message: str, cause: Exception | None = None) -> None:
        """Initialize with an optional chained exception cause."""
        if cause is not None:
            full_message = None
        else:
            full_message = message
        super().__init__(full_message)

    def xǁConfigLoadErrorǁ__init____mutmut_3(self, message: str, cause: Exception | None = None) -> None:
        """Initialize with an optional chained exception cause."""
        if cause is not None:
            full_message = (
                f"Config load failed ({type(None).__name__}: {cause}): {message}"
            )
        else:
            full_message = message
        super().__init__(full_message)

    def xǁConfigLoadErrorǁ__init____mutmut_4(self, message: str, cause: Exception | None = None) -> None:
        """Initialize with an optional chained exception cause."""
        if cause is not None:
            full_message = (
                f"Config load failed ({type(cause).__name__}: {cause}): {message}"
            )
        else:
            full_message = None
        super().__init__(full_message)

    def xǁConfigLoadErrorǁ__init____mutmut_5(self, message: str, cause: Exception | None = None) -> None:
        """Initialize with an optional chained exception cause."""
        if cause is not None:
            full_message = (
                f"Config load failed ({type(cause).__name__}: {cause}): {message}"
            )
        else:
            full_message = message
        super().__init__(None)

mutants_xǁConfigLoadErrorǁ__init____mutmut['_mutmut_orig'] = ConfigLoadError.xǁConfigLoadErrorǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁConfigLoadErrorǁ__init____mutmut['xǁConfigLoadErrorǁ__init____mutmut_1'] = ConfigLoadError.xǁConfigLoadErrorǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁConfigLoadErrorǁ__init____mutmut['xǁConfigLoadErrorǁ__init____mutmut_2'] = ConfigLoadError.xǁConfigLoadErrorǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁConfigLoadErrorǁ__init____mutmut['xǁConfigLoadErrorǁ__init____mutmut_3'] = ConfigLoadError.xǁConfigLoadErrorǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁConfigLoadErrorǁ__init____mutmut['xǁConfigLoadErrorǁ__init____mutmut_4'] = ConfigLoadError.xǁConfigLoadErrorǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁConfigLoadErrorǁ__init____mutmut['xǁConfigLoadErrorǁ__init____mutmut_5'] = ConfigLoadError.xǁConfigLoadErrorǁ__init____mutmut_5 # type: ignore # mutmut generated
