#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_credential.py

Effective-credential resolution policy for cicd-mcp — the environment variable wins, the config value is the fallback (REQ-001).

Policy-only module: no I/O, no logging, no config access. Service construction,
startup posture, and health read the effective credential only through this
function so they cannot disagree.

Import from here:
    from mcp_servers.cicd.cicd_credential import resolve_effective_credential
"""

from __future__ import annotations

import os

from .cicd_models import CicdConfig


def resolve_effective_credential(cfg: CicdConfig) -> str:
    """Return the effective GitHub credential.

    The environment variable wins; the config value is the fallback. An empty
    environment variable falls back to the config value. The value is returned
    without recording it, mirroring require_auth_token() in scripts/mcp_servers/server.py.
    """
    env_token = os.environ.get("GITHUB_TOKEN")
    if env_token:
        return env_token
    return cfg.github_token
