#!/usr/bin/env python3
"""Apply comprehensive isolation via autouse fixture + replace module-level singletons."""

filepath = "/home/sugimoto/llmagent/tests/mcp_servers/git/test_git_security_compliance.py"

with open(filepath, "r") as f:
    content = f.read()

# Step 1: Add copy import and autouse fixture after imports
autouse_block = '''
import copy

@pytest.fixture(autouse=True)
def isolate_git_singletons():
    """Replace _cfg and _service in BOTH modules with fresh copies before each test."""
    from scripts.mcp_servers.git import git_server as server_module
    from mcp_servers.git import server as http_module
    from mcp_servers.git.git_models import GitConfig
    from mcp_servers.git.git_service import build_service

    # Snapshot both modules' singletons
    server_orig_cfg = server_module._cfg
    server_orig_svc = server_module._service
    http_orig_cfg = http_module._cfg
    http_orig_svc = http_module._service

    # Replace with fresh instances (both modules get clean state)
    server_module._cfg = GitConfig(
        allowed_repo_paths=[],
        read_only=True,
        protected_branches=[],
        allow_detached_head=False,
        auth_token="",
        max_log_entries=50,
        audit_log_path=None,
        allowed_remote_urls=[],
    )
    server_module._service = build_service(server_module._cfg)
    http_module._cfg = GitConfig(
        allowed_repo_paths=[],
        read_only=True,
        protected_branches=[],
        allow_detached_head=False,
        auth_token="",
        max_log_entries=50,
        audit_log_path=None,
        allowed_remote_urls=[],
    )
    http_module._service = build_service(http_module._cfg)

    yield

    # Restore originals
    server_module._cfg = server_orig_cfg
    server_module._service = server_orig_svc
    http_module._cfg = http_orig_cfg
    http_module._service = http_orig_svc

'''

insert_after = 'from mcp_servers.git.repository_state import RepositoryState\n'
parts = content.split(insert_after, 1)
if len(parts) == 2:
    content = parts[0] + insert_after + autouse_block + parts[1]

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
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        yield

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
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        yield

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
        git_server._cfg.allowed_repo_paths = [str(repo_dir)]
        git_server._cfg.read_only = False
        git_server._service._allowed_repo_paths = [str(repo_dir)]
        git_server._service._read_only = False
        yield

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
