"""scripts/shared/config_validator.py — Startup validator for RAG config cross-file consistency."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@dataclasses.dataclass
class ConfigValidationResult:
    """Result of RAG configuration validation containing errors and warnings."""

    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        """Return True when there are no validation errors."""
        return len(self.errors) == 0
mutants_xǁRagConfigValidatorǁvalidate__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagConfigValidatorǁ_extract_rag_section__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut: MutantDict = {}  # type: ignore


class RagConfigValidator:
    """Validate RAG configuration for cross-file consistency."""

    @_mutmut_mutated(mutants_xǁRagConfigValidatorǁvalidate__mutmut)
    def validate(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_orig(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_1(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = None
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_2(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(None)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_3(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = None
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_4(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = None

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_5(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = None
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_6(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(None)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_7(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_8(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(None)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_9(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = None
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_10(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(None)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_11(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_12(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(None)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_13(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = None
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_14(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(None)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_15(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_16(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(None)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_17(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=None, warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_18(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=None)

    def xǁRagConfigValidatorǁvalidate__mutmut_19(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(warnings=warnings)

    def xǁRagConfigValidatorǁvalidate__mutmut_20(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, )

    @staticmethod
    @_mutmut_mutated(mutants_xǁRagConfigValidatorǁ_extract_rag_section__mutmut)
    def _extract_rag_section(cfg: Mapping[str, Any]) -> Mapping[str, Any]:
        """Normalize nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) shapes."""
        return cfg["rag"] if "rag" in cfg else cfg

    @staticmethod
    def xǁRagConfigValidatorǁ_extract_rag_section__mutmut_orig(cfg: Mapping[str, Any]) -> Mapping[str, Any]:
        """Normalize nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) shapes."""
        return cfg["rag"] if "rag" in cfg else cfg

    @staticmethod
    def xǁRagConfigValidatorǁ_extract_rag_section__mutmut_1(cfg: Mapping[str, Any]) -> Mapping[str, Any]:
        """Normalize nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) shapes."""
        return cfg["XXragXX"] if "rag" in cfg else cfg

    @staticmethod
    def xǁRagConfigValidatorǁ_extract_rag_section__mutmut_2(cfg: Mapping[str, Any]) -> Mapping[str, Any]:
        """Normalize nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) shapes."""
        return cfg["RAG"] if "rag" in cfg else cfg

    @staticmethod
    def xǁRagConfigValidatorǁ_extract_rag_section__mutmut_3(cfg: Mapping[str, Any]) -> Mapping[str, Any]:
        """Normalize nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) shapes."""
        return cfg["rag"] if "XXragXX" in cfg else cfg

    @staticmethod
    def xǁRagConfigValidatorǁ_extract_rag_section__mutmut_4(cfg: Mapping[str, Any]) -> Mapping[str, Any]:
        """Normalize nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) shapes."""
        return cfg["rag"] if "RAG" in cfg else cfg

    @staticmethod
    def xǁRagConfigValidatorǁ_extract_rag_section__mutmut_5(cfg: Mapping[str, Any]) -> Mapping[str, Any]:
        """Normalize nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) shapes."""
        return cfg["rag"] if "rag" not in cfg else cfg

    @staticmethod
    @_mutmut_mutated(mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut)
    def _check_use_rrf(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get("use_rrf", True):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_use_rrf__mutmut_orig(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get("use_rrf", True):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_use_rrf__mutmut_1(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if rag.get("use_rrf", True):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_use_rrf__mutmut_2(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get(None, True):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_use_rrf__mutmut_3(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get("use_rrf", None):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_use_rrf__mutmut_4(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get(True):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_use_rrf__mutmut_5(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get("use_rrf", ):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_use_rrf__mutmut_6(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get("XXuse_rrfXX", True):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_use_rrf__mutmut_7(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get("USE_RRF", True):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_use_rrf__mutmut_8(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get("use_rrf", False):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_use_rrf__mutmut_9(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get("use_rrf", True):
            return "XXuse_rrf=false degrades retrieval quality; use only for diagnosticsXX"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_use_rrf__mutmut_10(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get("use_rrf", True):
            return "USE_RRF=FALSE DEGRADES RETRIEVAL QUALITY; USE ONLY FOR DIAGNOSTICS"
        return None

    @staticmethod
    @_mutmut_mutated(mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut)
    def _check_semantic_cache_threshold(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get("semantic_cache_threshold", 0.92)
        if threshold < 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_orig(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get("semantic_cache_threshold", 0.92)
        if threshold < 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_1(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = None
        if threshold < 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_2(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get(None, 0.92)
        if threshold < 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_3(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get("semantic_cache_threshold", None)
        if threshold < 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_4(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get(0.92)
        if threshold < 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_5(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get("semantic_cache_threshold", )
        if threshold < 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_6(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get("XXsemantic_cache_thresholdXX", 0.92)
        if threshold < 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_7(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get("SEMANTIC_CACHE_THRESHOLD", 0.92)
        if threshold < 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_8(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get("semantic_cache_threshold", 1.92)
        if threshold < 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_9(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get("semantic_cache_threshold", 0.92)
        if threshold <= 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_10(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get("semantic_cache_threshold", 0.92)
        if threshold < 1.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    @_mutmut_mutated(mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut)
    def _check_semantic_cache_max_size(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get("semantic_cache_max_size", 100)
        if max_size < 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_orig(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get("semantic_cache_max_size", 100)
        if max_size < 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_1(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = None
        if max_size < 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_2(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get(None, 100)
        if max_size < 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_3(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get("semantic_cache_max_size", None)
        if max_size < 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_4(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get(100)
        if max_size < 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_5(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get("semantic_cache_max_size", )
        if max_size < 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_6(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get("XXsemantic_cache_max_sizeXX", 100)
        if max_size < 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_7(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get("SEMANTIC_CACHE_MAX_SIZE", 100)
        if max_size < 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_8(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get("semantic_cache_max_size", 101)
        if max_size < 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_9(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get("semantic_cache_max_size", 100)
        if max_size <= 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

    @staticmethod
    def xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_10(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get("semantic_cache_max_size", 100)
        if max_size < 1:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None

mutants_xǁRagConfigValidatorǁvalidate__mutmut['_mutmut_orig'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_1'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_2'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_3'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_4'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_5'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_6'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_7'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_8'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_9'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_10'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_11'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_12'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_13'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_14'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_15'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_16'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_17'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_18'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_19'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁvalidate__mutmut['xǁRagConfigValidatorǁvalidate__mutmut_20'] = RagConfigValidator.xǁRagConfigValidatorǁvalidate__mutmut_20 # type: ignore # mutmut generated

mutants_xǁRagConfigValidatorǁ_extract_rag_section__mutmut['_mutmut_orig'] = RagConfigValidator.xǁRagConfigValidatorǁ_extract_rag_section__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_extract_rag_section__mutmut['xǁRagConfigValidatorǁ_extract_rag_section__mutmut_1'] = RagConfigValidator.xǁRagConfigValidatorǁ_extract_rag_section__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_extract_rag_section__mutmut['xǁRagConfigValidatorǁ_extract_rag_section__mutmut_2'] = RagConfigValidator.xǁRagConfigValidatorǁ_extract_rag_section__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_extract_rag_section__mutmut['xǁRagConfigValidatorǁ_extract_rag_section__mutmut_3'] = RagConfigValidator.xǁRagConfigValidatorǁ_extract_rag_section__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_extract_rag_section__mutmut['xǁRagConfigValidatorǁ_extract_rag_section__mutmut_4'] = RagConfigValidator.xǁRagConfigValidatorǁ_extract_rag_section__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_extract_rag_section__mutmut['xǁRagConfigValidatorǁ_extract_rag_section__mutmut_5'] = RagConfigValidator.xǁRagConfigValidatorǁ_extract_rag_section__mutmut_5 # type: ignore # mutmut generated

mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut['_mutmut_orig'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_use_rrf__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut['xǁRagConfigValidatorǁ_check_use_rrf__mutmut_1'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_use_rrf__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut['xǁRagConfigValidatorǁ_check_use_rrf__mutmut_2'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_use_rrf__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut['xǁRagConfigValidatorǁ_check_use_rrf__mutmut_3'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_use_rrf__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut['xǁRagConfigValidatorǁ_check_use_rrf__mutmut_4'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_use_rrf__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut['xǁRagConfigValidatorǁ_check_use_rrf__mutmut_5'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_use_rrf__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut['xǁRagConfigValidatorǁ_check_use_rrf__mutmut_6'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_use_rrf__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut['xǁRagConfigValidatorǁ_check_use_rrf__mutmut_7'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_use_rrf__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut['xǁRagConfigValidatorǁ_check_use_rrf__mutmut_8'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_use_rrf__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut['xǁRagConfigValidatorǁ_check_use_rrf__mutmut_9'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_use_rrf__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_use_rrf__mutmut['xǁRagConfigValidatorǁ_check_use_rrf__mutmut_10'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_use_rrf__mutmut_10 # type: ignore # mutmut generated

mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut['_mutmut_orig'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_1'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_2'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_3'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_4'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_5'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_6'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_7'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_8'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_9'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_10'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_threshold__mutmut_10 # type: ignore # mutmut generated

mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut['_mutmut_orig'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_1'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_2'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_3'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_4'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_5'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_6'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_7'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_8'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_9'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut['xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_10'] = RagConfigValidator.xǁRagConfigValidatorǁ_check_semantic_cache_max_size__mutmut_10 # type: ignore # mutmut generated
