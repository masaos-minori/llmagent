#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_server_file.py

GitHub file-operation router.

All four file tools (get_file_contents, create_or_update_file, push_files,
delete_repo_file) are dispatched through /v1/call_tool in github_server.py via the
shared dispatch table; this module keeps an empty APIRouter so github_server.py's
_include_routers() registers it unchanged.
"""

from fastapi import APIRouter

router = APIRouter()
