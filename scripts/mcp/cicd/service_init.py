#!/usr/bin/env python3
"""mcp/cicd/service_init.py

build_service factory for cicd-mcp.

Constants and CiBackend protocol live in service_defs.py to avoid circular imports.
"""

from __future__ import annotations

import logging
import os

import httpx
from mcp.cicd.models import CicdConfig

from .service_business import CiCdService
from .service_defs import CiBackend

logger = logging.getLogger(__name__)


def build_service(cfg: CicdConfig) -> CiCdService:
    """Construct a CiCdService from a typed config object."""
    github_token = os.environ.get("GITHUB_TOKEN", cfg.github_token)
    if not github_token:
        logger.warning(
            "cicd-mcp: GITHUB_TOKEN is not set; API rate limit will be 60 req/hr",
        )
    http = httpx.AsyncClient(timeout=30.0)
    from .service_github_actions_composite import (  # noqa: PLC0415
        GitHubActionsCompositeBackend,
    )

    backend: CiBackend = GitHubActionsCompositeBackend(
        github_token=github_token,
        max_log_size_kb=cfg.max_log_size_kb,
        http=http,
    )
    return CiCdService(cfg=cfg, backend=backend)
