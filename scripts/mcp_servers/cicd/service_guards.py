#!/usr/bin/env python3
"""mcp_servers/cicd/service_guards.py

CiCdService security guard mixin: repo_allowlist + workflow_allowlist enforcement.

Dependency direction: service_guards → models, service_defs
"""

from __future__ import annotations

import logging

from mcp_servers.cicd.models import CicdAuthorizationError
from mcp_servers.cicd.service_defs import CiBackend

logger = logging.getLogger(__name__)


class CiCdGuards:
    """Mixin providing repo/workflow allowlist guards for CiCdService."""

    def __init__(
        self,
        backend: CiBackend,
        repo_allowlist: list[str],
        workflow_allowlist: list[str],
    ) -> None:
        """Initialize the CI/CD guard mixin with backend and allowlists for repos and workflows."""
        self._backend = backend
        # Empty allowlist = deny all (fail-closed, U-3)
        self._repo_allowlist: list[str] = list(repo_allowlist)
        # Empty allowlist = deny all (fail-closed, same as repo_allowlist)
        self._workflow_allowlist: list[str] = list(workflow_allowlist)

        if not self._repo_allowlist:
            logger.warning(
                "cicd-mcp: repo_allowlist is empty — all repository operations will be denied",
            )
        if not self._workflow_allowlist:
            logger.warning(
                "cicd-mcp: workflow_allowlist is empty — all workflow triggers will be denied",
            )

    def _assert_allowed_repo(self, repo: str) -> None:
        """Raise CicdAuthorizationError when repo is not in the allowlist.

        Empty allowlist = deny all (fail-closed per U-3).
        """
        if not self._repo_allowlist:
            raise CicdAuthorizationError(
                (
                    f"Repository '{repo}' is denied: repo_allowlist is empty (fail-closed mode)"
                ),
            )
        if repo not in self._repo_allowlist:
            raise CicdAuthorizationError(
                f"Repository not in repo_allowlist: {repo}",
            )

    def _assert_allowed_workflow(self, workflow: str) -> None:
        """Raise CicdAuthorizationError when workflow is not in workflow_allowlist.

        Empty allowlist = deny all (fail-closed).
        """
        if not self._workflow_allowlist:
            raise CicdAuthorizationError(
                "workflow_allowlist is empty — all workflow triggers denied (fail-closed). "
                "Add allowed workflow patterns to config."
            )
        if workflow not in self._workflow_allowlist:
            raise CicdAuthorizationError(
                f"Workflow not in workflow_allowlist: {workflow}",
            )
