#!/usr/bin/env python3
"""Apply all fixes: add deepcopy-based isolation + update enabled fixtures."""

import copy
import re

filepath = "/home/sugimoto/llmagent/tests/mcp_servers/git/test_git_security_compliance.py"

with open(filepath, "r") as f:
    content = f.read()

# Step 1: Add copy import and helper functions after imports
helpers_block = '''
import copy

def _snap_cfg_svc():
    """Snapshot _cfg and _service singletons for complete isolation."""
    from scripts.mcp_servers.git import git_server
    return {
        "cfg": copy.deepcopy(git_server._cfg.__dict__),
        "svc": copy.deepcopy(git_server._service.__dict__),
    }

def _rst_cfg_svc(snap):
    """Restore _cfg and _service singletons from snapshot."""
    from scripts.mcp_servers.git import git_server
    if snap["cfg"] is not None:
        git_server._cfg.__dict__.update(snap["cfg"])
    if snap["svc"] is not None:
        git_server._service.__dict__.update(snap["svc"])

'''

insert_after = 'from mcp_servers.git.repository_state import RepositoryState'
content = content.replace(insert_after, insert_after + helpers_block)

# Step 2: Update TestNewlyReachableToolsViaHTTP.enabled fixture
old_newly_reachable_enabled = '''    @pytest.fixture
    def enabled(self, repo_dir):
        from scripts.mcp_servers.git import git_server

        original_paths = git_server._cfg.allowed_repo_paths
        original_read_only = git_server._cfg.read_only
        original_svc_paths = git_server._service._allowed_repo_paths
        original_svc_read_only = git_server._service._read_only
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        try:
            yield
        finally:
            git_server._cfg.allowed_repo_paths = original_paths
            git_server._cfg.read_only = original_read_only
            git_server._service._allowed_repo_paths = original_svc_paths
            git_server._service._read_only = original_svc_read_only'''

new_newly_reachable_enabled = '''    @pytest.fixture
    def enabled(self, repo_dir):
        snap = _snap_cfg_svc()
        from scripts.mcp_servers.git import git_server
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._cfg.protected_branches = []
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        git_server._service._protected_branches = []
        try:
            yield
        finally:
            _rst_cfg_svc(snap)'''

content = content.replace(old_newly_reachable_enabled, new_newly_reachable_enabled)

# Step 3: Update TestRemoteAuthorizationViaHTTP.enabled fixture
old_remote_auth_enabled = '''    @pytest.fixture
    def enabled(self, repo_dir):
        from scripts.mcp_servers.git import git_server

        original_paths = git_server._cfg.allowed_repo_paths
        original_read_only = git_server._cfg.read_only
        original_svc_paths = git_server._service._allowed_repo_paths
        original_svc_read_only = git_server._service._read_only
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        try:
            yield
        finally:
            git_server._cfg.allowed_repo_paths = original_paths
            git_server._cfg.read_only = original_read_only
            git_server._service._allowed_repo_paths = original_svc_paths
            git_server._service._read_only = original_svc_read_only

    def test_pull_rejects_unauthorized_remote'''

new_remote_auth_enabled = '''    @pytest.fixture
    def enabled(self, repo_dir):
        snap = _snap_cfg_svc()
        from scripts.mcp_servers.git import git_server
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._cfg.protected_branches = []
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        git_server._service._protected_branches = []
        try:
            yield
        finally:
            _rst_cfg_svc(snap)

    def test_pull_rejects_unauthorized_remote'''

content = content.replace(old_remote_auth_enabled, new_remote_auth_enabled)

# Step 4: Update TestGitServiceErrorHandlerIdentity.enabled fixture
old_error_handler_enabled = '''    @pytest.fixture
    def enabled(self, repo_dir):
        from scripts.mcp_servers.git import git_server

        original_paths = git_server._cfg.allowed_repo_paths
        original_read_only = git_server._cfg.read_only
        original_svc_paths = git_server._service._allowed_repo_paths
        original_svc_read_only = git_server._service._read_only
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        try:
            yield
        finally:
            git_server._cfg.allowed_repo_paths = original_paths
            git_server._cfg.read_only = original_read_only
            git_server._service._allowed_repo_paths = original_svc_paths
            git_server._service._read_only = original_svc_read_only

    def test_induced_git_service_error_is_caught_by_registered_handler('''

new_error_handler_enabled = '''    @pytest.fixture
    def enabled(self, repo_dir):
        snap = _snap_cfg_svc()
        from scripts.mcp_servers.git import git_server
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._cfg.protected_branches = []
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        git_server._service._protected_branches = []
        try:
            yield
        finally:
            _rst_cfg_svc(snap)

    def test_induced_git_service_error_is_caught_by_registered_handler('''

content = content.replace(old_error_handler_enabled, new_error_handler_enabled)

# Step 5: Fix mock_repo_state_snapshot_dynamic teardown
old_mock_dynamic = '''        monkeypatch.setattr(WriteProtectionPipeline, "run", mock_pipeline_run)

    @pytest.mark.asyncio
    async def test_checkout_protected_branch_denied('''

new_mock_dynamic = '''        monkeypatch.setattr(WriteProtectionPipeline, "run", mock_pipeline_run)
        orig_snapshot = RepositoryState.snapshot
        orig_run = WriteProtectionPipeline.run
        yield
        # Restore originals after tests complete
        RepositoryState.snapshot = orig_snapshot
        WriteProtectionPipeline.run = orig_run

    @pytest.mark.asyncio
    async def test_checkout_protected_branch_denied('''

content = content.replace(old_mock_dynamic, new_mock_dynamic)

with open(filepath, "w") as f:
    f.write(content)

print("Done")
