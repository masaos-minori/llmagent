#!/usr/bin/env python3
"""Apply all fixes: add helpers + update enabled fixtures."""

filepath = "/home/sugimoto/llmagent/tests/mcp_servers/git/test_git_security_compliance.py"

with open(filepath, "r") as f:
    content = f.read()

# Step 1: Add _CFG_ATTRS, _SVC_ATTRS, _snap, _rst after imports (before first class)
helpers_block = '''
# Mutable attribute names for GitConfig (_cfg) and GitService (_service)
_CFG_ATTRS = frozenset((
    "allowed_repo_paths",
    "read_only",
    "protected_branches",
    "allow_detached_head",
    "auth_token",
    "max_log_entries",
    "audit_log_path",
    "allowed_remote_urls",
))

_SVC_ATTRS = frozenset((
    "_allowed_repo_paths",
    "_read_only",
    "_protected_branches",
    "_allow_detached_head",
    "_max_log_entries",
    "_config",
))


def _snap(obj, attrs):
    """Snapshot mutable attributes; deep-copy lists to avoid mutation during restoration."""
    snap = {}
    for attr in attrs:
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            snap[attr] = list(val) if isinstance(val, list) else val
    return snap


def _rst(obj, snap):
    """Restore mutable attributes from snapshot."""
    if obj is None:
        return
    for attr, val in snap.items():
        if hasattr(obj, attr):
            setattr(obj, attr, val)

'''

# Insert after "from mcp_servers.git.repository_state import RepositoryState"
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
        from scripts.mcp_servers.git import git_server

        cfg_snap = _snap(git_server._cfg, _CFG_ATTRS) if hasattr(git_server, "_cfg") else {}
        svc_snap = _snap(git_server._service, _SVC_ATTRS) if hasattr(git_server, "_service") else {}
        try:
            git_server._cfg.allowed_repo_paths = [str(repo_dir)]
            git_server._cfg.read_only = False
            git_server._service._allowed_repo_paths = [str(repo_dir)]
            git_server._service._read_only = False
            yield
        finally:
            _rst(git_server._cfg, cfg_snap)
            _rst(git_server._service, svc_snap)'''

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
        from scripts.mcp_servers.git import git_server

        cfg_snap = _snap(git_server._cfg, _CFG_ATTRS) if hasattr(git_server, "_cfg") else {}
        svc_snap = _snap(git_server._service, _SVC_ATTRS) if hasattr(git_server, "_service") else {}
        try:
            git_server._cfg.allowed_repo_paths = [str(repo_dir)]
            git_server._cfg.read_only = False
            git_server._service._allowed_repo_paths = [str(repo_dir)]
            git_server._service._read_only = False
            yield
        finally:
            _rst(git_server._cfg, cfg_snap)
            _rst(git_server._service, svc_snap)

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
        from scripts.mcp_servers.git import git_server

        cfg_snap = _snap(git_server._cfg, _CFG_ATTRS) if hasattr(git_server, "_cfg") else {}
        svc_snap = _snap(git_server._service, _SVC_ATTRS) if hasattr(git_server, "_service") else {}
        try:
            git_server._cfg.allowed_repo_paths = [str(repo_dir)]
            git_server._cfg.read_only = False
            git_server._service._allowed_repo_paths = [str(repo_dir)]
            git_server._service._read_only = False
            yield
        finally:
            _rst(git_server._cfg, cfg_snap)
            _rst(git_server._service, svc_snap)

    def test_induced_git_service_error_is_caught_by_registered_handler('''

content = content.replace(old_error_handler_enabled, new_error_handler_enabled)

with open(filepath, "w") as f:
    f.write(content)

print("Done")
