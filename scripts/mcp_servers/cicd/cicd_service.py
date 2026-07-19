#!/usr/bin/env python3
"""mcp_servers/cicd/service.py

Re-export stub for mcp/cicd/service modules.

Split layout:
  service_init.py        — Constants, CiBackend protocol, build_service factory
  service_business.py    — GitHubActionsBackend, CiCdService classes
"""

from .service_business import CiCdService
from .service_defs import (
    _GH_API_VERSION,
    _GITHUB_API_BASE,
    _MAX_JOBS_FOR_LOGS,
    GITHUB_REPO_PARTS_COUNT,
    CiBackend,
)
from .service_github_actions import GitHubActionsBackend
from .service_init import build_service

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
