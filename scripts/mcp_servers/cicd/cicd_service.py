#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_service.py

Re-export stub for mcp/cicd/service modules.

Split layout:
  service_defs.py           — Constants, CiBackend protocol
  service_init.py           — build_service factory
  service_business.py       — CiCdService class
  service_github_actions.py — GitHubActionsBackend class
"""

from .cicd_service_business import CiCdService
from .cicd_service_defs import (
    _GH_API_VERSION,
    _GITHUB_API_BASE,
    _MAX_JOBS_FOR_LOGS,
    GITHUB_REPO_PARTS_COUNT,
    CiBackend,
)
from .cicd_service_github_actions import GitHubActionsBackend
from .cicd_service_init import build_service

__all__ = [
    "CiCdService",
    "CiBackend",
    "GitHubActionsBackend",
    "GITHUB_REPO_PARTS_COUNT",
    "_GITHUB_API_BASE",
    "_GH_API_VERSION",
    "_MAX_JOBS_FOR_LOGS",
    "build_service",
]
