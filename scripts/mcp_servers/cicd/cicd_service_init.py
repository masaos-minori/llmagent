#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_service_init.py

build_service factory for cicd-mcp.

The HTTP client is injected by the caller (the server's lifespan owns it), so this
factory never creates one and has no shutdown path of its own. Tests inject their own
client through the same parameter.

Constants and CiBackend protocol live in service_defs.py to avoid circular imports.
"""

from __future__ import annotations

import logging

import httpx

from mcp_servers.cicd.cicd_credential import resolve_effective_credential
from mcp_servers.cicd.cicd_models import CicdConfig

from .cicd_service_business import CiCdService
from .cicd_service_defs import CiBackend

logger = logging.getLogger(__name__)


def build_service(cfg: CicdConfig, http: httpx.AsyncClient) -> CiCdService:
    """Construct a CiCdService from a typed config object and the injected client."""
    github_token = resolve_effective_credential(cfg)
    if not github_token:
        logger.warning(
            "cicd-mcp: GITHUB_TOKEN is not set; API rate limit will be 60 req/hr",
        )
    from .cicd_service_github_actions_composite import (
        GitHubActionsCompositeBackend,
    )

    backend: CiBackend = GitHubActionsCompositeBackend(
        github_token=github_token,
        max_log_size_kb=cfg.max_log_size_kb,
        http=http,
    )
    return CiCdService(cfg=cfg, backend=backend)
