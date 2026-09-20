#!/usr/bin/env python3
"""Final comprehensive fix: modify attrs in place + snapshot after setup."""

filepath = "/home/sugimoto/llmagent/tests/mcp_servers/git/test_git_security_compliance.py"

with open(filepath, "r") as f:
    content = f.read()

# Step 1: Add copy import after imports
insert_after = 'from mcp_servers.git.repository_state import RepositoryState\n'
parts = content.split(insert_after, 1)
if len(parts) == 2:
    content = parts[0] + insert_after + 'import copy\n' + parts[1]

# Step 2: Update TestNewlyReachableToolsViaHTTP.enabled fixture
old_first = '''    @pytest.fixture
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

class TestRemoteAuthorizationViaHTTP:'''

new_first = '''    @pytest.fixture
    def enabled(self, repo_dir):
        from scripts.mcp_servers.git import git_server
        # Modify attributes IN PLACE (app holds refs to these objects)
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._cfg.protected_branches = []
        git_server._cfg.allow_detached_head = False
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        git_server._service._protected_branches = []
        git_server._service._allow_detached_head = False
        # Snapshot AFTER setup so restore goes back to clean state
        cfg_snap = copy.deepcopy(git_server._cfg.__dict__)
        svc_snap = copy.deepcopy(git_server._service.__dict__)
        try:
            yield
        finally:
            git_server._cfg.__dict__.update(cfg_snap)
            git_server._service.__dict__.update(svc_snap)

class TestRemoteAuthorizationViaHTTP:'''

content = content.replace(old_first, new_first)

# Step 3: Update TestRemoteAuthorizationViaHTTP.enabled fixture
old_second = '''    @pytest.fixture
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

new_second = '''    @pytest.fixture
    def enabled(self, repo_dir):
        from scripts.mcp_servers.git import git_server
        # Modify attributes IN PLACE (app holds refs to these objects)
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._cfg.protected_branches = []
        git_server._cfg.allow_detached_head = False
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        git_server._service._protected_branches = []
        git_server._service._allow_detached_head = False
        # Snapshot AFTER setup so restore goes back to clean state
        cfg_snap = copy.deepcopy(git_server._cfg.__dict__)
        svc_snap = copy.deepcopy(git_server._service.__dict__)
        try:
            yield
        finally:
            git_server._cfg.__dict__.update(cfg_snap)
            git_server._service.__dict__.update(svc_snap)

    def test_pull_rejects_unauthorized_remote'''

content = content.replace(old_second, new_second)

# Step 4: Update TestGitServiceErrorHandlerIdentity.enabled fixture
old_third = '''    @pytest.fixture
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

new_third = '''    @pytest.fixture
    def enabled(self, repo_dir):
        from scripts.mcp_servers.git import git_server
        # Modify attributes IN PLACE (app holds refs to these objects)
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._cfg.protected_branches = []
        git_server._cfg.allow_detached_head = False
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        git_server._service._protected_branches = []
        git_server._service._allow_detached_head = False
        # Snapshot AFTER setup so restore goes back to clean state
        cfg_snap = copy.deepcopy(git_server._cfg.__dict__)
        svc_snap = copy.deepcopy(git_server._service.__dict__)
        try:
            yield
        finally:
            git_server._cfg.__dict__.update(cfg_snap)
            git_server._service.__dict__.update(svc_snap)

    def test_induced_git_service_error_is_caught_by_registered_handler('''

content = content.replace(old_third, new_third)

# Step 5: Fix mock_repo_state_snapshot_dynamic teardown
old_mock = '''        monkeypatch.setattr(WriteProtectionPipeline, "run", mock_pipeline_run)

    @pytest.mark.asyncio
    async def test_checkout_protected_branch_denied('''

new_mock = '''        monkeypatch.setattr(WriteProtectionPipeline, "run", mock_pipeline_run)
        orig_snapshot = RepositoryState.snapshot
        orig_run = WriteProtectionPipeline.run
        yield
        # Restore originals after tests complete
        RepositoryState.snapshot = orig_snapshot
        WriteProtectionPipeline.run = orig_run

    @pytest.mark.asyncio
    async def test_checkout_protected_branch_denied('''

content = content.replace(old_mock, new_mock)

with open(filepath, "w") as f:
    f.write(content)

print("Done")
