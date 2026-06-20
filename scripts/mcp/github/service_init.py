#!/usr/bin/env python3
"""mcp/github/service_init.py
GitHub client initialization and lazy singleton proxy.

Produces:
  _gh          — PyGithub Github instance (singleton)
  build_service(cfg) → GitHubService

Import from here:  from mcp.github.service_init import build_service
"""

import logging
import os

from github import Auth, Github

# GITHUB_TOKEN is set in /etc/conf.d/github-mcp; OpenRC loads it as an env var
_github_token = os.environ.get("GITHUB_TOKEN", "")
_GITHUB_TOKEN = _github_token
if not _github_token:
    _gh = Github()
else:
    _gh = Github(auth=Auth.Token(_github_token))

if not _github_token:
    logging.getLogger(__name__).warning(
        "GITHUB_TOKEN is not set; API rate limit will be 60 req/hr"
    )


def build_service(cfg):
    """Construct a GitHubService from a typed config object."""
    from mcp.github.service_dispatch import GitHubService  # noqa: PLC0415

    return GitHubService(gh=_gh, cfg=cfg)
