#!/usr/bin/env python3
"""Unit tests for mcp.file.read_service.ReadFileService."""

import base64
from pathlib import Path

import pytest
from mcp.file.common import FileAuthorizationError, FileValidationError
from mcp.file.read_models import FileEntry, TreeNode
from mcp.file.read_service import ReadFileService


@pytest.fixture()
def service(tmp_path: Path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "subdir").mkdir()
    (root / "subdir" / "nested.txt").write_text("nested content", encoding="utf-8")
    (root / "file_a.py").write_text("# Python file\nprint('hello')\n", encoding="utf-8")
    (root / "file_b.log").write_text(
        "INFO line 1\nWARN line 2\nERROR line 3\n", encoding="utf-8"
    )
    (root / "binary.bin").write_bytes(b"\x89PNG\r\n\x1a\n")
    (root / "large.txt").write_text("x" * 2048, encoding="utf-8")

    return ReadFileService(
        allowed_dirs=[root],
        max_read_bytes=1024,
        max_tree_depth=3,
        max_search_results=50,
    ), root


# -- Security wrapper tests --------------------------------------------------


class TestSecurityWrappers:
    def test_resolve_safe_allows_in_allowed_dir(self, service):
        svc, tmp_workspace = service
        result = svc._resolve_safe(str(tmp_workspace / "file_a.py"))
        assert result == tmp_workspace / "file_a.py"

    def test_resolve_safe_rejects_outside_allowed_dirs(self, service):
        svc, _ = service
        with pytest.raises(FileAuthorizationError):
            svc._resolve_safe("/etc/passwd")

    def test_resolve_safe_rejects_proc_self_environ(self, service):
        svc, _ = service
        with pytest.raises(FileAuthorizationError):
            svc._resolve_safe("/proc/self/environ")

    def test_resolve_safe_rejects_traversal_etc_shadow(self, service):
        svc, tmp_workspace = service
        with pytest.raises(FileAuthorizationError):
            svc._resolve_safe(str(tmp_workspace / "../../etc/shadow"))

    def test_resolve_safe_rejects_symlink_outside_allowed(self, tmp_path: Path):
        root = tmp_path / "workspace"
        root.mkdir()
        target = tmp_path / "outside" / "secret.txt"
        target.parent.mkdir()
        target.write_text("secret", encoding="utf-8")
        link = root / "link_to_secret"
        link.symlink_to(target)

        svc = ReadFileService(
            allowed_dirs=[root],
            max_read_bytes=1024,
            max_tree_depth=3,
            max_search_results=50,
        )
        with pytest.raises(FileAuthorizationError):
            svc._resolve_safe(str(link))

    def test_resolve_safe_allows_symlink_inside_allowed(self, tmp_path: Path):
        root = tmp_path / "workspace"
        root.mkdir()
        inside = root / "inside_link"
        inside.write_text("inside", encoding="utf-8")

        svc = ReadFileService(
            allowed_dirs=[root],
            max_read_bytes=1024,
            max_tree_depth=3,
            max_search_results=50,
        )
        result = svc._resolve_safe(str(inside))
        assert result == inside.resolve()

    def test_require_file_raises_for_directory(self, service):
        svc, tmp_workspace = service
        with pytest.raises(FileValidationError):
            svc._require_file(tmp_workspace, "some_path")

    def test_require_dir_raises_for_file(self, service):
        svc, tmp_workspace = service
        with pytest.raises(FileValidationError):
            svc._require_dir(tmp_workspace / "file_a.py", "some_path")

    def test_check_size_limit_passes_under_limit(self, service):
        svc, tmp_workspace = service
        result = svc._check_size_limit(tmp_workspace / "file_a.py")
        assert result == (tmp_workspace / "file_a.py").stat().st_size

    def test_check_size_limit_raises_over_limit(self, service):
        svc, tmp_workspace = service
        with pytest.raises(FileValidationError):
            svc._check_size_limit(tmp_workspace / "large.txt")


# -- Static helper tests -----------------------------------------------------


class TestStaticHelpers:
    def test_slice_lines_no_args_returns_content(self):
        content = "line1\nline2\nline3\n"
        assert ReadFileService._slice_lines(content, None, None) == content

    def test_slice_lines_head_only(self):
        content = "line1\nline2\nline3\nline4\nline5\n"
        assert ReadFileService._slice_lines(content, 2, None) == "line1\nline2\n"

    def test_slice_lines_tail_only(self):
        content = "line1\nline2\nline3\nline4\nline5\n"
        assert ReadFileService._slice_lines(content, None, 2) == "line4\nline5\n"

    def test_slice_lines_head_overrides_tail(self):
        content = "line1\nline2\nline3\n"
        assert ReadFileService._slice_lines(content, 1, 10) == "line1\n"

    def test_fmt_tree_node_file(self):
        node = TreeNode(
            name="test.txt", path="/x/test.txt", type="file", size=100, children=[]
        )
        result = ReadFileService._fmt_tree_node(node)
        assert "[FILE] test.txt (100 B)" in result

    def test_fmt_tree_node_dir(self):
        node = TreeNode(name="mydir", path="/x/mydir", type="dir", size=0, children=[])
        result = ReadFileService._fmt_tree_node(node)
        assert "[DIR] mydir/" in result

    def test_fmt_tree_node_depth_limit_note(self):
        node = TreeNode(
            name="limited",
            path="/x",
            type="dir",
            size=0,
            children=[],
            depth_limited=True,
        )
        result = ReadFileService._fmt_tree_node(node)
        assert "(depth limit reached)" in result

    def test_fmt_dir_entries_empty(self):
        result = ReadFileService._fmt_dir_entries([])
        assert result == "(empty directory)"

    def test_fmt_dir_entries_with_files(self):
        entries = [
            FileEntry(name="a.py", path="/x/a.py", type="file", size=50),
            FileEntry(name="b_dir", path="/x/b_dir", type="dir", size=0),
        ]
        result = ReadFileService._fmt_dir_entries(entries)
        assert "[2 entries]" in result
        assert "[FILE] a.py (50 B)" in result
        assert "[DIR] b_dir" in result

    def test_has_depth_limit_true(self):
        node = TreeNode(
            name="x", path="/x", type="dir", size=0, children=[], depth_limited=True
        )
        assert ReadFileService._has_depth_limit(node) is True

    def test_has_depth_limit_false(self):
        node = TreeNode(
            name="x", path="/x", type="dir", size=0, children=[], depth_limited=False
        )
        assert ReadFileService._has_depth_limit(node) is False

    def test_build_tree_single_file(self, service):
        svc, tmp_workspace = service
        node = ReadFileService._build_tree(tmp_workspace / "file_a.py", 0, 3)
        assert node.name == "file_a.py"
        assert node.type == "file"
        assert node.children == []

    def test_build_tree_empty_directory(self, service):
        svc, tmp_workspace = service
        empty_dir = tmp_workspace / "empty"
        empty_dir.mkdir()
        node = ReadFileService._build_tree(empty_dir, 0, 3)
        assert node.type == "dir"
        assert node.children == []

    def test_build_tree_expands_subdirs_within_depth(self, service):
        svc, tmp_workspace = service
        node = ReadFileService._build_tree(tmp_workspace / "subdir", 0, 3)
        assert node.type == "dir"
        names = [c.name for c in node.children]
        assert "nested.txt" in names

    def test_build_tree_respects_max_depth(self, service):
        svc, tmp_workspace = service
        deep = tmp_workspace / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        (deep / "deep_file.txt").write_text("deep", encoding="utf-8")
        node = ReadFileService._build_tree(tmp_workspace, 0, 2)

        def _find_depth_limited(n):
            if n.depth_limited:
                return True
            return any(_find_depth_limited(c) for c in n.children)

        assert _find_depth_limited(node) is True

    def test_count_tree_nodes(self, service):
        svc, tmp_workspace = service
        node = ReadFileService._build_tree(tmp_workspace, 0, 3)
        count = ReadFileService._count_tree_nodes(node)
        assert count >= 4


# -- list_dir_entries tests --------------------------------------------------


class TestListDirEntries:
    def test_list_dir_returns_entries(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ListDirectoryRequest

        result = svc.list_dir_entries(
            ListDirectoryRequest(path=str(tmp_workspace)),
            include_dir_sizes=False,
        )
        names = {e.name for e in result.entries}
        assert "file_a.py" in names
        assert "subdir" in names

    def test_list_dir_excludes_dir_sizes(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ListDirectoryRequest

        result = svc.list_dir_entries(
            ListDirectoryRequest(path=str(tmp_workspace)),
            include_dir_sizes=False,
        )
        dir_entry = next(e for e in result.entries if e.type == "dir")
        assert dir_entry.size == 0

    def test_list_dir_with_sizes_includes_dir_st_size(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ListDirectoryRequest

        result = svc.list_dir_entries(
            ListDirectoryRequest(path=str(tmp_workspace)),
            include_dir_sizes=True,
        )
        dir_entry = next(e for e in result.entries if e.type == "dir")
        assert dir_entry.size >= 0

    def test_list_dir_path_not_allowed(self, service):
        svc, _ = service
        from mcp.file.read_models import ListDirectoryRequest

        with pytest.raises(FileAuthorizationError):
            svc.list_dir_entries(
                ListDirectoryRequest(path="/etc"),
                include_dir_sizes=False,
            )

    def test_list_dir_path_is_file_raises(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ListDirectoryRequest

        with pytest.raises(FileValidationError):
            svc.list_dir_entries(
                ListDirectoryRequest(path=str(tmp_workspace / "file_a.py")),
                include_dir_sizes=False,
            )


# -- build_directory_tree tests ----------------------------------------------


class TestBuildDirectoryTree:
    def test_build_tree_root_contains_all_files(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import DirectoryTreeRequest

        result = svc.build_directory_tree(
            DirectoryTreeRequest(path=str(tmp_workspace), depth=3)
        )
        names = {c.name for c in result.root.children}
        assert "file_a.py" in names
        assert "subdir" in names
        assert "binary.bin" in names

    def test_build_tree_depth_one(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import DirectoryTreeRequest

        result = svc.build_directory_tree(
            DirectoryTreeRequest(path=str(tmp_workspace), depth=1)
        )
        for child in result.root.children:
            if child.name == "subdir":
                assert child.children == []

    def test_build_tree_response_has_root(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import DirectoryTreeRequest

        result = svc.build_directory_tree(
            DirectoryTreeRequest(path=str(tmp_workspace), depth=3)
        )
        assert result.root is not None
        assert result.root.type == "dir"


# -- read_text_file tests ----------------------------------------------------


class TestReadTextFile:
    def test_read_text_returns_content(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadTextFileRequest

        result = svc.read_text_file(
            ReadTextFileRequest(path=str(tmp_workspace / "file_a.py"))
        )
        assert "# Python file" in result.content
        assert result.size > 0

    def test_read_text_with_head(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadTextFileRequest

        result = svc.read_text_file(
            ReadTextFileRequest(path=str(tmp_workspace / "file_b.log"), head=1)
        )
        assert "INFO line 1" in result.content
        assert "ERROR line 3" not in result.content

    def test_read_text_with_tail(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadTextFileRequest

        result = svc.read_text_file(
            ReadTextFileRequest(path=str(tmp_workspace / "file_b.log"), tail=1)
        )
        assert "ERROR line 3" in result.content
        assert "INFO line 1" not in result.content

    def test_read_text_unicode_decode_error(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadTextFileRequest

        with pytest.raises(FileValidationError):
            svc.read_text_file(
                ReadTextFileRequest(path=str(tmp_workspace / "binary.bin"))
            )

    def test_read_text_size_limit_exceeded(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadTextFileRequest

        with pytest.raises(FileValidationError):
            svc.read_text_file(
                ReadTextFileRequest(path=str(tmp_workspace / "large.txt"))
            )

    def test_read_text_nonexistent_path(self, service):
        svc, _ = service
        from mcp.file.read_models import ReadTextFileRequest

        with pytest.raises(FileAuthorizationError):
            svc.read_text_file(ReadTextFileRequest(path="/nonexistent/file.txt"))

    def test_read_text_response_fields(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadTextFileRequest

        result = svc.read_text_file(
            ReadTextFileRequest(path=str(tmp_workspace / "file_a.py"))
        )
        assert result.path == str(tmp_workspace / "file_a.py")
        assert isinstance(result.size, int)

    def test_read_text_permission_error_raises_file_authorization_error(self, service):
        import os

        from mcp.file.read_models import ReadTextFileRequest

        svc, tmp_workspace = service
        no_perm = tmp_workspace / "no_perm.txt"
        no_perm.write_text("secret", encoding="utf-8")

        if os.getuid() == 0:
            pytest.skip("root can read files regardless of permissions")

        no_perm.chmod(0o000)
        try:
            with pytest.raises(FileAuthorizationError):
                svc.read_text_file(ReadTextFileRequest(path=str(no_perm)))
        finally:
            no_perm.chmod(0o644)

    def test_read_text_file_not_found_in_allowed_dir_raises_file_not_found_error(self, service):
        from mcp.file.read_models import ReadTextFileRequest

        svc, tmp_workspace = service
        with pytest.raises(FileNotFoundError):
            svc.read_text_file(
                ReadTextFileRequest(path=str(tmp_workspace / "ghost.txt"))
            )


# -- read_media_file tests ---------------------------------------------------


class TestReadMediaFile:
    def test_read_media_returns_base64(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadMediaFileRequest

        result = svc.read_media_file(
            ReadMediaFileRequest(path=str(tmp_workspace / "binary.bin"))
        )
        decoded = base64.b64decode(result.content_base64)
        assert b"PNG" in decoded

    def test_read_media_mime_type(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadMediaFileRequest

        result = svc.read_media_file(
            ReadMediaFileRequest(path=str(tmp_workspace / "binary.bin"))
        )
        assert result.mime_type is not None
        assert len(result.mime_type) > 0

    def test_read_media_size(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadMediaFileRequest

        result = svc.read_media_file(
            ReadMediaFileRequest(path=str(tmp_workspace / "binary.bin"))
        )
        assert result.size > 0

    def test_read_media_file_too_large(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadMediaFileRequest

        with pytest.raises(FileValidationError):
            svc.read_media_file(
                ReadMediaFileRequest(path=str(tmp_workspace / "large.txt"))
            )


# -- read_multiple_files tests ------------------------------------------------


class TestReadMultipleFiles:
    def test_read_multiple_success(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadMultipleFilesRequest

        result = svc.read_multiple_files(
            ReadMultipleFilesRequest(
                paths=[
                    str(tmp_workspace / "file_a.py"),
                    str(tmp_workspace / "file_b.log"),
                ]
            )
        )
        assert len(result.results) == 2
        assert all(r.content is not None for r in result.results)

    def test_read_multiple_with_errors(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import ReadMultipleFilesRequest

        result = svc.read_multiple_files(
            ReadMultipleFilesRequest(
                paths=[
                    str(tmp_workspace / "file_a.py"),
                    "/nonexistent/path.txt",
                ]
            )
        )
        assert len(result.results) == 2
        assert result.results[0].content is not None
        assert result.results[1].error is not None

    def test_read_multiple_empty_paths(self, service):
        svc, _ = service
        from mcp.file.read_models import ReadMultipleFilesRequest

        # Empty paths returns empty results (no error raised)
        result = svc.read_multiple_files(ReadMultipleFilesRequest(paths=[]))
        assert len(result.results) == 0

    def test_read_multiple_outside_allowed_dirs(self, service):
        svc, _ = service
        from mcp.file.read_models import ReadMultipleFilesRequest

        result = svc.read_multiple_files(
            ReadMultipleFilesRequest(paths=["/etc/passwd"])
        )
        assert len(result.results) == 1
        assert result.results[0].error is not None


# -- search_files tests ------------------------------------------------------


class TestSearchFiles:
    def test_search_files_matches(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import SearchFilesRequest

        result = svc.search_files(
            SearchFilesRequest(path=str(tmp_workspace), pattern="*.py")
        )
        assert len(result.matches) >= 1
        assert any("file_a.py" in m for m in result.matches)

    def test_search_files_no_match(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import SearchFilesRequest

        result = svc.search_files(
            SearchFilesRequest(path=str(tmp_workspace), pattern="*.xyz")
        )
        assert result.matches == []

    def test_search_files_respects_max_results(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import SearchFilesRequest
        from mcp.file.read_service import ReadFileService

        test_svc = ReadFileService(
            allowed_dirs=[tmp_workspace],
            max_read_bytes=1024,
            max_tree_depth=3,
            max_search_results=1,
        )
        result = test_svc.search_files(
            SearchFilesRequest(path=str(tmp_workspace), pattern="*")
        )
        assert len(result.matches) <= 1

    def test_search_files_outside_allowed(self, service):
        svc, _ = service
        from mcp.file.read_models import SearchFilesRequest

        with pytest.raises(FileAuthorizationError):
            svc.search_files(SearchFilesRequest(path="/etc", pattern="*"))


# -- grep_files tests --------------------------------------------------------


class TestGrepFiles:
    def test_grep_files_finds_matches(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import GrepFilesRequest

        result = svc.grep_files(
            GrepFilesRequest(
                path=str(tmp_workspace),
                pattern="ERROR",
                file_pattern="*.log",
                max_matches=50,
            )
        )
        assert len(result.matches) >= 1
        assert any("ERROR line" in m.line for m in result.matches)

    def test_grep_files_no_match(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import GrepFilesRequest

        result = svc.grep_files(
            GrepFilesRequest(
                path=str(tmp_workspace),
                pattern="ZZZNOTFOUND",
                file_pattern="*.log",
                max_matches=50,
            )
        )
        assert result.matches == []
        assert result.truncated is False

    def test_grep_files_invalid_regex(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import GrepFilesRequest

        with pytest.raises(FileValidationError):
            svc.grep_files(
                GrepFilesRequest(
                    path=str(tmp_workspace),
                    pattern="[invalid",
                    file_pattern="*",
                    max_matches=50,
                )
            )

    def test_grep_files_truncated(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import GrepFilesRequest

        result = svc.grep_files(
            GrepFilesRequest(
                path=str(tmp_workspace),
                pattern=".*",
                file_pattern="*.log",
                max_matches=1,
            )
        )
        assert result.truncated is True


# -- get_file_info tests -----------------------------------------------------


class TestGetFileInfo:
    def test_get_file_info_returns_metadata(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import GetFileInfoRequest

        result = svc.get_file_info(
            GetFileInfoRequest(path=str(tmp_workspace / "file_a.py"))
        )
        assert result.info.name == "file_a.py"
        assert result.info.type == "file"
        assert result.info.size > 0
        assert result.info.permissions is not None

    def test_get_file_info_directory(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import GetFileInfoRequest

        result = svc.get_file_info(
            GetFileInfoRequest(path=str(tmp_workspace / "subdir"))
        )
        assert result.info.type == "dir"

    def test_get_file_info_not_found(self, service):
        svc, tmp_workspace = service
        from mcp.file.read_models import GetFileInfoRequest

        with pytest.raises(FileNotFoundError):
            svc.get_file_info(
                GetFileInfoRequest(path=str(tmp_workspace / "nonexistent.txt"))
            )

    def test_get_file_info_path_outside_allowed(self, service):
        svc, _ = service
        from mcp.file.read_models import GetFileInfoRequest

        with pytest.raises(FileAuthorizationError):
            svc.get_file_info(GetFileInfoRequest(path="/etc/passwd"))


# -- Async formatter tests ---------------------------------------------------


class TestAsyncFormatters:
    @pytest.fixture()
    def svc_with_tmp(self, tmp_path: Path):
        root = tmp_path / "workspace"
        root.mkdir()
        (root / "test.txt").write_text("hello world\nline2\n", encoding="utf-8")
        return ReadFileService(
            allowed_dirs=[root],
            max_read_bytes=1024,
            max_tree_depth=3,
            max_search_results=50,
        ), root

    @pytest.mark.asyncio
    async def test_fmt_read_text_file(self, svc_with_tmp):
        svc, root = svc_with_tmp
        args = {"path": str(root / "test.txt")}
        result = await svc.fmt_read_text_file(args)
        assert "hello world" in result

    @pytest.mark.asyncio
    async def test_fmt_list_directory(self, svc_with_tmp):
        svc, root = svc_with_tmp
        args = {"path": str(root)}
        result = await svc.fmt_list_directory(args)
        assert "test.txt" in result

    @pytest.mark.asyncio
    async def test_fmt_list_directory_with_sizes(self, svc_with_tmp):
        svc, root = svc_with_tmp
        args = {"path": str(root)}
        result = await svc.fmt_list_directory_with_sizes(args)
        assert "test.txt" in result

    @pytest.mark.asyncio
    async def test_fmt_search_files(self, svc_with_tmp):
        svc, root = svc_with_tmp
        args = {"path": str(root), "pattern": "*.txt"}
        result = await svc.fmt_search_files(args)
        assert "test.txt" in result

    @pytest.mark.asyncio
    async def test_fmt_grep_files(self, svc_with_tmp):
        svc, root = svc_with_tmp
        args = {
            "path": str(root),
            "pattern": "hello",
            "file_pattern": "*.txt",
            "max_matches": 50,
        }
        result = await svc.fmt_grep_files(args)
        assert "hello" in result

    @pytest.mark.asyncio
    async def test_fmt_get_file_info(self, svc_with_tmp):
        svc, root = svc_with_tmp
        args = {"path": str(root / "test.txt")}
        result = await svc.fmt_get_file_info(args)
        assert "test.txt" in result
        assert "size:" in result

    @pytest.mark.asyncio
    async def test_fmt_read_multiple_files(self, svc_with_tmp):
        svc, root = svc_with_tmp
        args = {"paths": [str(root / "test.txt")]}
        result = await svc.fmt_read_multiple_files(args)
        assert "test.txt" in result

    @pytest.mark.asyncio
    async def test_fmt_directory_tree(self, svc_with_tmp):
        svc, root = svc_with_tmp
        args = {"path": str(root), "depth": 3}
        result = await svc.fmt_directory_tree(args)
        assert "[Tree:" in result
        assert "nodes" in result

    @pytest.mark.asyncio
    async def test_fmt_read_media_file(self, svc_with_tmp):
        svc, root = svc_with_tmp
        args = {"path": str(root / "test.txt")}
        result = await svc.fmt_read_media_file(args)
        assert "base64:" in result


# -- Dispatch table tests ----------------------------------------------------


class TestDispatchTable:
    def test_get_dispatch_table_has_all_keys(self, service):
        svc, _ = service
        table = svc.get_dispatch_table()
        expected = {
            "list_directory",
            "list_directory_with_sizes",
            "directory_tree",
            "read_text_file",
            "read_media_file",
            "read_multiple_files",
            "search_files",
            "grep_files",
            "get_file_info",
        }
        assert set(table.keys()) == expected

    def test_dispatch_table_values_are_callable(self, service):
        svc, _ = service
        table = svc.get_dispatch_table()
        for key, handler in table.items():
            assert callable(handler)


# -- Error-path tests (domain exceptions) ------------------------------------


class TestErrorPaths:
    def test_check_size_limit_raises_file_validation_error(
        self, tmp_path: Path
    ) -> None:
        from mcp.file.common import FileValidationError, check_size_limit

        f = tmp_path / "big.txt"
        f.write_text("x" * 200, encoding="utf-8")
        with pytest.raises(FileValidationError, match="exceeds"):
            check_size_limit(f, max_bytes=10)

    def test_grep_files_invalid_regex_raises_file_validation_error(
        self, service
    ) -> None:
        from mcp.file.common import FileValidationError
        from mcp.file.read_models import GrepFilesRequest

        svc, root = service
        req = GrepFilesRequest(path=str(root), pattern="[invalid(regex")
        with pytest.raises(FileValidationError, match="Invalid regular expression"):
            svc.grep_files(req)

    def test_read_service_max_tree_depth_property(self, service) -> None:
        svc, _ = service
        assert svc.max_tree_depth == 3
