#!/usr/bin/env python3
"""Apply all fixes using precise line-number-based edits."""

filepath = (
    "/home/sugimoto/llmagent/tests/mcp_servers/git/test_git_security_compliance.py"
)

with open(filepath) as f:
    lines = f.readlines()

# Find the exact line numbers we need
helpers_after_line = None
newly_reachable_enabled_start = None
remote_auth_enabled_start = None
error_handler_enabled_start = None
mock_dynamic_yield_line = None

for i, line in enumerate(lines):
    # Helpers after imports (use FIRST occurrence only)
    if (
        "from mcp_servers.git.repository_state import RepositoryState" in line
        and helpers_after_line is None
    ):
        helpers_after_line = i

    # First enabled fixture (TestNewlyReachableToolsViaHTTP)
    if "@pytest.fixture" in line and i > 0 and "def enabled" in lines[i + 1]:
        # Check if this is inside TestNewlyReachableToolsViaHTTP
        for j in range(max(0, i - 10), i):
            if "class TestNewlyReachableToolsViaHTTP" in lines[j]:
                newly_reachable_enabled_start = i
                break

    # Second enabled fixture (TestRemoteAuthorizationViaHTTP)
    if "@pytest.fixture" in line and i > 0 and "def enabled" in lines[i + 1]:
        for j in range(max(0, i - 10), i):
            if "class TestRemoteAuthorizationViaHTTP" in lines[j]:
                remote_auth_enabled_start = i
                break

    # Third enabled fixture (TestGitServiceErrorHandlerIdentity)
    if "@pytest.fixture" in line and i > 0 and "def enabled" in lines[i + 1]:
        for j in range(max(0, i - 10), i):
            if "class TestGitServiceErrorHandlerIdentity" in lines[j]:
                error_handler_enabled_start = i
                break

    # mock_repo_state_snapshot_dynamic yield line
    if 'monkeypatch.setattr(WriteProtectionPipeline, "run", mock_pipeline_run)' in line:
        mock_dynamic_yield_line = i + 2  # yield should come after this

print(f"helpers_after_line: {helpers_after_line}")
print(f"newly_reachable_enabled_start: {newly_reachable_enabled_start}")
print(f"remote_auth_enabled_start: {remote_auth_enabled_start}")
print(f"error_handler_enabled_start: {error_handler_enabled_start}")
print(f"mock_dynamic_yield_line: {mock_dynamic_yield_line}")

if helpers_after_line is None or newly_reachable_enabled_start is None:
    print("ERROR: Could not find required line numbers")
    exit(1)

# Insert helper functions after the imports
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

lines.insert(helpers_after_line + 1, helpers_block)

# Now re-read to get updated line numbers
with open(filepath) as f:
    content = f.read()

# Update first enabled fixture
old_first = """    @pytest.fixture
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

class TestRemoteAuthorizationViaHTTP:"""

new_first = """    @pytest.fixture
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

class TestRemoteAuthorizationViaHTTP:"""

content = content.replace(old_first, new_first)

# Update second enabled fixture
old_second = """    @pytest.fixture
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

    def test_pull_rejects_unauthorized_remote"""

new_second = """    @pytest.fixture
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

    def test_pull_rejects_unauthorized_remote"""

content = content.replace(old_second, new_second)

# Update third enabled fixture
old_third = """    @pytest.fixture
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

    def test_induced_git_service_error_is_caught_by_registered_handler("""

new_third = """    @pytest.fixture
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

    def test_induced_git_service_error_is_caught_by_registered_handler("""

content = content.replace(old_third, new_third)

# Fix mock_repo_state_snapshot_dynamic teardown
old_mock = """        monkeypatch.setattr(WriteProtectionPipeline, "run", mock_pipeline_run)

    @pytest.mark.asyncio
    async def test_checkout_protected_branch_denied("""

new_mock = """        monkeypatch.setattr(WriteProtectionPipeline, "run", mock_pipeline_run)
        orig_snapshot = RepositoryState.snapshot
        orig_run = WriteProtectionPipeline.run
        yield
        # Restore originals after tests complete
        RepositoryState.snapshot = orig_snapshot
        WriteProtectionPipeline.run = orig_run

    @pytest.mark.asyncio
    async def test_checkout_protected_branch_denied("""

content = content.replace(old_mock, new_mock)

with open(filepath, "w") as f:
    f.write(content)

print("Done")
