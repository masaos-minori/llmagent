#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_service_init.py — GitHub client construction
from typed configuration.

Produces:
  build_client(token, connect_timeout_sec, read_timeout_sec) → Github
  build_service(cfg) → GitHubService

The client is built per service, not at import time: there is no module-level
`_gh` singleton. Library retry is disabled so a write is sent at most once per
call (mcpai006 REQ-002); reads rely on the Agent transport's safe read retry.

Import from here:  from mcp_servers.github.github_service_init import build_service
"""

import logging
import os

from github import Auth, Github

# GITHUB_TOKEN is set via environment variable or config file
_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def build_client(
    token: str, connect_timeout_sec: float, read_timeout_sec: float
) -> Github:
    """Build a no-retry Github client with the configured timeouts.

    `retry=None` disables PyGithub's built-in retry, which re-sends every 5xx
    and 403 including writes. `Github.__init__` asserts `isinstance(timeout, int)`,
    so the `(connect, read)` tuple is applied afterwards on the requester's
    private timeout, which `requests` accepts verbatim.
    """
    logger = logging.getLogger(__name__)
    if not token:
        logger.warning("GITHUB_TOKEN is not set; API rate limit will be 60 req/hr")
    gh = Github(
        auth=Auth.Token(token) if token else None,
        timeout=0,
        retry=None,
    )
    object.__setattr__(
        gh.requester, "_Requester__timeout", (connect_timeout_sec, read_timeout_sec)
    )
    return gh


def build_service(cfg):
    """Construct a GitHubService from a typed config object."""
    from mcp_servers.github.github_service_dispatch import GitHubService

    return GitHubService(
        gh=build_client(_GITHUB_TOKEN, cfg.connect_timeout_sec, cfg.read_timeout_sec),
        cfg=cfg,
    )
