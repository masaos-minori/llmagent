"""scripts/agent/security_audit_config.py

Narrow API for security audit access to MCP server config models.

This is the ONLY agent module permitted to import from MCP server config models.
All security audit checks must go through this module.
"""

from __future__ import annotations

from dataclasses import dataclass


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@dataclass(frozen=True)
class ShellAuditConfig:
    """Security audit configuration for shell command execution."""

    sandbox_backend: str
    command_allowlist: list[str]


@dataclass(frozen=True)
class GitAuditConfig:
    """Security audit configuration for git operations."""

    allowed_repo_paths: list[str]


@dataclass(frozen=True)
class GitHubAuditConfig:
    """Security audit configuration for GitHub API operations."""

    allowed_repos: list[str]
    allow_force_push: bool
    require_pr_review: bool


@dataclass(frozen=True)
class CicdAuditConfig:
    """Security audit configuration for CI/CD pipeline operations."""

    workflow_allowlist: list[str]
mutants_x_load_shell_audit_config__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_load_shell_audit_config__mutmut)
def load_shell_audit_config() -> ShellAuditConfig | None:
    """Load shell config for audit. Returns None if not installed."""
    try:
        from mcp_servers.shell.shell_models import ShellConfig
    except ImportError:
        return None
    try:
        cfg = ShellConfig.load()
        return ShellAuditConfig(
            sandbox_backend=cfg.shell_sandbox_backend,
            command_allowlist=list(cfg.command_allowlist),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load shell config: {exc}"
        ) from exc


def x_load_shell_audit_config__mutmut_orig() -> ShellAuditConfig | None:
    """Load shell config for audit. Returns None if not installed."""
    try:
        from mcp_servers.shell.shell_models import ShellConfig
    except ImportError:
        return None
    try:
        cfg = ShellConfig.load()
        return ShellAuditConfig(
            sandbox_backend=cfg.shell_sandbox_backend,
            command_allowlist=list(cfg.command_allowlist),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load shell config: {exc}"
        ) from exc


def x_load_shell_audit_config__mutmut_1() -> ShellAuditConfig | None:
    """Load shell config for audit. Returns None if not installed."""
    try:
        from mcp_servers.shell.shell_models import ShellConfig
    except ImportError:
        return None
    try:
        cfg = None
        return ShellAuditConfig(
            sandbox_backend=cfg.shell_sandbox_backend,
            command_allowlist=list(cfg.command_allowlist),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load shell config: {exc}"
        ) from exc


def x_load_shell_audit_config__mutmut_2() -> ShellAuditConfig | None:
    """Load shell config for audit. Returns None if not installed."""
    try:
        from mcp_servers.shell.shell_models import ShellConfig
    except ImportError:
        return None
    try:
        cfg = ShellConfig.load()
        return ShellAuditConfig(
            sandbox_backend=None,
            command_allowlist=list(cfg.command_allowlist),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load shell config: {exc}"
        ) from exc


def x_load_shell_audit_config__mutmut_3() -> ShellAuditConfig | None:
    """Load shell config for audit. Returns None if not installed."""
    try:
        from mcp_servers.shell.shell_models import ShellConfig
    except ImportError:
        return None
    try:
        cfg = ShellConfig.load()
        return ShellAuditConfig(
            sandbox_backend=cfg.shell_sandbox_backend,
            command_allowlist=None,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load shell config: {exc}"
        ) from exc


def x_load_shell_audit_config__mutmut_4() -> ShellAuditConfig | None:
    """Load shell config for audit. Returns None if not installed."""
    try:
        from mcp_servers.shell.shell_models import ShellConfig
    except ImportError:
        return None
    try:
        cfg = ShellConfig.load()
        return ShellAuditConfig(
            command_allowlist=list(cfg.command_allowlist),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load shell config: {exc}"
        ) from exc


def x_load_shell_audit_config__mutmut_5() -> ShellAuditConfig | None:
    """Load shell config for audit. Returns None if not installed."""
    try:
        from mcp_servers.shell.shell_models import ShellConfig
    except ImportError:
        return None
    try:
        cfg = ShellConfig.load()
        return ShellAuditConfig(
            sandbox_backend=cfg.shell_sandbox_backend,
            )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load shell config: {exc}"
        ) from exc


def x_load_shell_audit_config__mutmut_6() -> ShellAuditConfig | None:
    """Load shell config for audit. Returns None if not installed."""
    try:
        from mcp_servers.shell.shell_models import ShellConfig
    except ImportError:
        return None
    try:
        cfg = ShellConfig.load()
        return ShellAuditConfig(
            sandbox_backend=cfg.shell_sandbox_backend,
            command_allowlist=list(None),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load shell config: {exc}"
        ) from exc


def x_load_shell_audit_config__mutmut_7() -> ShellAuditConfig | None:
    """Load shell config for audit. Returns None if not installed."""
    try:
        from mcp_servers.shell.shell_models import ShellConfig
    except ImportError:
        return None
    try:
        cfg = ShellConfig.load()
        return ShellAuditConfig(
            sandbox_backend=cfg.shell_sandbox_backend,
            command_allowlist=list(cfg.command_allowlist),
        )
    except Exception as exc:
        raise RuntimeError(
            None
        ) from exc

mutants_x_load_shell_audit_config__mutmut['_mutmut_orig'] = x_load_shell_audit_config__mutmut_orig # type: ignore # mutmut generated
mutants_x_load_shell_audit_config__mutmut['x_load_shell_audit_config__mutmut_1'] = x_load_shell_audit_config__mutmut_1 # type: ignore # mutmut generated
mutants_x_load_shell_audit_config__mutmut['x_load_shell_audit_config__mutmut_2'] = x_load_shell_audit_config__mutmut_2 # type: ignore # mutmut generated
mutants_x_load_shell_audit_config__mutmut['x_load_shell_audit_config__mutmut_3'] = x_load_shell_audit_config__mutmut_3 # type: ignore # mutmut generated
mutants_x_load_shell_audit_config__mutmut['x_load_shell_audit_config__mutmut_4'] = x_load_shell_audit_config__mutmut_4 # type: ignore # mutmut generated
mutants_x_load_shell_audit_config__mutmut['x_load_shell_audit_config__mutmut_5'] = x_load_shell_audit_config__mutmut_5 # type: ignore # mutmut generated
mutants_x_load_shell_audit_config__mutmut['x_load_shell_audit_config__mutmut_6'] = x_load_shell_audit_config__mutmut_6 # type: ignore # mutmut generated
mutants_x_load_shell_audit_config__mutmut['x_load_shell_audit_config__mutmut_7'] = x_load_shell_audit_config__mutmut_7 # type: ignore # mutmut generated
mutants_x_load_git_audit_config__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_load_git_audit_config__mutmut)
def load_git_audit_config() -> GitAuditConfig | None:
    """Load git config for audit. Returns None if not installed."""
    try:
        from mcp_servers.git.git_models import GitConfig
    except ImportError:
        return None
    try:
        cfg = GitConfig.load()
        return GitAuditConfig(allowed_repo_paths=list(cfg.allowed_repo_paths))
    except Exception as exc:
        raise RuntimeError(f"Security audit: failed to load git config: {exc}") from exc


def x_load_git_audit_config__mutmut_orig() -> GitAuditConfig | None:
    """Load git config for audit. Returns None if not installed."""
    try:
        from mcp_servers.git.git_models import GitConfig
    except ImportError:
        return None
    try:
        cfg = GitConfig.load()
        return GitAuditConfig(allowed_repo_paths=list(cfg.allowed_repo_paths))
    except Exception as exc:
        raise RuntimeError(f"Security audit: failed to load git config: {exc}") from exc


def x_load_git_audit_config__mutmut_1() -> GitAuditConfig | None:
    """Load git config for audit. Returns None if not installed."""
    try:
        from mcp_servers.git.git_models import GitConfig
    except ImportError:
        return None
    try:
        cfg = None
        return GitAuditConfig(allowed_repo_paths=list(cfg.allowed_repo_paths))
    except Exception as exc:
        raise RuntimeError(f"Security audit: failed to load git config: {exc}") from exc


def x_load_git_audit_config__mutmut_2() -> GitAuditConfig | None:
    """Load git config for audit. Returns None if not installed."""
    try:
        from mcp_servers.git.git_models import GitConfig
    except ImportError:
        return None
    try:
        cfg = GitConfig.load()
        return GitAuditConfig(allowed_repo_paths=None)
    except Exception as exc:
        raise RuntimeError(f"Security audit: failed to load git config: {exc}") from exc


def x_load_git_audit_config__mutmut_3() -> GitAuditConfig | None:
    """Load git config for audit. Returns None if not installed."""
    try:
        from mcp_servers.git.git_models import GitConfig
    except ImportError:
        return None
    try:
        cfg = GitConfig.load()
        return GitAuditConfig(allowed_repo_paths=list(None))
    except Exception as exc:
        raise RuntimeError(f"Security audit: failed to load git config: {exc}") from exc


def x_load_git_audit_config__mutmut_4() -> GitAuditConfig | None:
    """Load git config for audit. Returns None if not installed."""
    try:
        from mcp_servers.git.git_models import GitConfig
    except ImportError:
        return None
    try:
        cfg = GitConfig.load()
        return GitAuditConfig(allowed_repo_paths=list(cfg.allowed_repo_paths))
    except Exception as exc:
        raise RuntimeError(None) from exc

mutants_x_load_git_audit_config__mutmut['_mutmut_orig'] = x_load_git_audit_config__mutmut_orig # type: ignore # mutmut generated
mutants_x_load_git_audit_config__mutmut['x_load_git_audit_config__mutmut_1'] = x_load_git_audit_config__mutmut_1 # type: ignore # mutmut generated
mutants_x_load_git_audit_config__mutmut['x_load_git_audit_config__mutmut_2'] = x_load_git_audit_config__mutmut_2 # type: ignore # mutmut generated
mutants_x_load_git_audit_config__mutmut['x_load_git_audit_config__mutmut_3'] = x_load_git_audit_config__mutmut_3 # type: ignore # mutmut generated
mutants_x_load_git_audit_config__mutmut['x_load_git_audit_config__mutmut_4'] = x_load_git_audit_config__mutmut_4 # type: ignore # mutmut generated
mutants_x_load_github_audit_config__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_load_github_audit_config__mutmut)
def load_github_audit_config() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = GitHubConfig.load()
        return GitHubAuditConfig(
            allowed_repos=list(cfg.allowed_repos),
            allow_force_push=cfg.allow_force_push,
            require_pr_review=cfg.require_pr_review,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load GitHub config: {exc}"
        ) from exc


def x_load_github_audit_config__mutmut_orig() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = GitHubConfig.load()
        return GitHubAuditConfig(
            allowed_repos=list(cfg.allowed_repos),
            allow_force_push=cfg.allow_force_push,
            require_pr_review=cfg.require_pr_review,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load GitHub config: {exc}"
        ) from exc


def x_load_github_audit_config__mutmut_1() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = None
        return GitHubAuditConfig(
            allowed_repos=list(cfg.allowed_repos),
            allow_force_push=cfg.allow_force_push,
            require_pr_review=cfg.require_pr_review,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load GitHub config: {exc}"
        ) from exc


def x_load_github_audit_config__mutmut_2() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = GitHubConfig.load()
        return GitHubAuditConfig(
            allowed_repos=None,
            allow_force_push=cfg.allow_force_push,
            require_pr_review=cfg.require_pr_review,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load GitHub config: {exc}"
        ) from exc


def x_load_github_audit_config__mutmut_3() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = GitHubConfig.load()
        return GitHubAuditConfig(
            allowed_repos=list(cfg.allowed_repos),
            allow_force_push=None,
            require_pr_review=cfg.require_pr_review,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load GitHub config: {exc}"
        ) from exc


def x_load_github_audit_config__mutmut_4() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = GitHubConfig.load()
        return GitHubAuditConfig(
            allowed_repos=list(cfg.allowed_repos),
            allow_force_push=cfg.allow_force_push,
            require_pr_review=None,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load GitHub config: {exc}"
        ) from exc


def x_load_github_audit_config__mutmut_5() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = GitHubConfig.load()
        return GitHubAuditConfig(
            allow_force_push=cfg.allow_force_push,
            require_pr_review=cfg.require_pr_review,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load GitHub config: {exc}"
        ) from exc


def x_load_github_audit_config__mutmut_6() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = GitHubConfig.load()
        return GitHubAuditConfig(
            allowed_repos=list(cfg.allowed_repos),
            require_pr_review=cfg.require_pr_review,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load GitHub config: {exc}"
        ) from exc


def x_load_github_audit_config__mutmut_7() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = GitHubConfig.load()
        return GitHubAuditConfig(
            allowed_repos=list(cfg.allowed_repos),
            allow_force_push=cfg.allow_force_push,
            )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load GitHub config: {exc}"
        ) from exc


def x_load_github_audit_config__mutmut_8() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = GitHubConfig.load()
        return GitHubAuditConfig(
            allowed_repos=list(None),
            allow_force_push=cfg.allow_force_push,
            require_pr_review=cfg.require_pr_review,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load GitHub config: {exc}"
        ) from exc


def x_load_github_audit_config__mutmut_9() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = GitHubConfig.load()
        return GitHubAuditConfig(
            allowed_repos=list(cfg.allowed_repos),
            allow_force_push=cfg.allow_force_push,
            require_pr_review=cfg.require_pr_review,
        )
    except Exception as exc:
        raise RuntimeError(
            None
        ) from exc

mutants_x_load_github_audit_config__mutmut['_mutmut_orig'] = x_load_github_audit_config__mutmut_orig # type: ignore # mutmut generated
mutants_x_load_github_audit_config__mutmut['x_load_github_audit_config__mutmut_1'] = x_load_github_audit_config__mutmut_1 # type: ignore # mutmut generated
mutants_x_load_github_audit_config__mutmut['x_load_github_audit_config__mutmut_2'] = x_load_github_audit_config__mutmut_2 # type: ignore # mutmut generated
mutants_x_load_github_audit_config__mutmut['x_load_github_audit_config__mutmut_3'] = x_load_github_audit_config__mutmut_3 # type: ignore # mutmut generated
mutants_x_load_github_audit_config__mutmut['x_load_github_audit_config__mutmut_4'] = x_load_github_audit_config__mutmut_4 # type: ignore # mutmut generated
mutants_x_load_github_audit_config__mutmut['x_load_github_audit_config__mutmut_5'] = x_load_github_audit_config__mutmut_5 # type: ignore # mutmut generated
mutants_x_load_github_audit_config__mutmut['x_load_github_audit_config__mutmut_6'] = x_load_github_audit_config__mutmut_6 # type: ignore # mutmut generated
mutants_x_load_github_audit_config__mutmut['x_load_github_audit_config__mutmut_7'] = x_load_github_audit_config__mutmut_7 # type: ignore # mutmut generated
mutants_x_load_github_audit_config__mutmut['x_load_github_audit_config__mutmut_8'] = x_load_github_audit_config__mutmut_8 # type: ignore # mutmut generated
mutants_x_load_github_audit_config__mutmut['x_load_github_audit_config__mutmut_9'] = x_load_github_audit_config__mutmut_9 # type: ignore # mutmut generated
mutants_x_load_cicd_audit_config__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_load_cicd_audit_config__mutmut)
def load_cicd_audit_config() -> CicdAuditConfig | None:
    """Load CI/CD config for audit. Returns None if not installed."""
    try:
        from mcp_servers.cicd.cicd_models import CicdConfig
    except ImportError:
        return None
    try:
        cfg = CicdConfig.load()
        return CicdAuditConfig(workflow_allowlist=list(cfg.workflow_allowlist))
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load CI/CD config: {exc}"
        ) from exc


def x_load_cicd_audit_config__mutmut_orig() -> CicdAuditConfig | None:
    """Load CI/CD config for audit. Returns None if not installed."""
    try:
        from mcp_servers.cicd.cicd_models import CicdConfig
    except ImportError:
        return None
    try:
        cfg = CicdConfig.load()
        return CicdAuditConfig(workflow_allowlist=list(cfg.workflow_allowlist))
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load CI/CD config: {exc}"
        ) from exc


def x_load_cicd_audit_config__mutmut_1() -> CicdAuditConfig | None:
    """Load CI/CD config for audit. Returns None if not installed."""
    try:
        from mcp_servers.cicd.cicd_models import CicdConfig
    except ImportError:
        return None
    try:
        cfg = None
        return CicdAuditConfig(workflow_allowlist=list(cfg.workflow_allowlist))
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load CI/CD config: {exc}"
        ) from exc


def x_load_cicd_audit_config__mutmut_2() -> CicdAuditConfig | None:
    """Load CI/CD config for audit. Returns None if not installed."""
    try:
        from mcp_servers.cicd.cicd_models import CicdConfig
    except ImportError:
        return None
    try:
        cfg = CicdConfig.load()
        return CicdAuditConfig(workflow_allowlist=None)
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load CI/CD config: {exc}"
        ) from exc


def x_load_cicd_audit_config__mutmut_3() -> CicdAuditConfig | None:
    """Load CI/CD config for audit. Returns None if not installed."""
    try:
        from mcp_servers.cicd.cicd_models import CicdConfig
    except ImportError:
        return None
    try:
        cfg = CicdConfig.load()
        return CicdAuditConfig(workflow_allowlist=list(None))
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load CI/CD config: {exc}"
        ) from exc


def x_load_cicd_audit_config__mutmut_4() -> CicdAuditConfig | None:
    """Load CI/CD config for audit. Returns None if not installed."""
    try:
        from mcp_servers.cicd.cicd_models import CicdConfig
    except ImportError:
        return None
    try:
        cfg = CicdConfig.load()
        return CicdAuditConfig(workflow_allowlist=list(cfg.workflow_allowlist))
    except Exception as exc:
        raise RuntimeError(
            None
        ) from exc

mutants_x_load_cicd_audit_config__mutmut['_mutmut_orig'] = x_load_cicd_audit_config__mutmut_orig # type: ignore # mutmut generated
mutants_x_load_cicd_audit_config__mutmut['x_load_cicd_audit_config__mutmut_1'] = x_load_cicd_audit_config__mutmut_1 # type: ignore # mutmut generated
mutants_x_load_cicd_audit_config__mutmut['x_load_cicd_audit_config__mutmut_2'] = x_load_cicd_audit_config__mutmut_2 # type: ignore # mutmut generated
mutants_x_load_cicd_audit_config__mutmut['x_load_cicd_audit_config__mutmut_3'] = x_load_cicd_audit_config__mutmut_3 # type: ignore # mutmut generated
mutants_x_load_cicd_audit_config__mutmut['x_load_cicd_audit_config__mutmut_4'] = x_load_cicd_audit_config__mutmut_4 # type: ignore # mutmut generated
