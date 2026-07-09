#!/usr/bin/env python3
"""mcp/file/read_static_helpers.py

Static helper functions for ReadFileService, extracted to reduce read_service.py size.

These helpers have no instance state — they operate purely on their arguments.
"""

from __future__ import annotations

import logging
from pathlib import Path

from mcp.file.read_models import FileEntry, TreeNode
from shared.formatters import fmt_size

logger = logging.getLogger(__name__)


def build_tree(path: Path, current_depth: int, max_depth: int) -> TreeNode:
    """Recursively build a directory tree.

    When current_depth >= max_depth, directories are not expanded and
    depth_limited is set to True if the directory has any contents.
    """
    is_dir = path.is_dir()
    size = path.stat().st_size if path.is_file() else 0
    node = TreeNode(
        name=path.name,
        path=str(path),
        type="dir" if is_dir else "file",
        size=size,
        children=[],
    )
    if not is_dir:
        return node
    if current_depth < max_depth:
        try:
            for child in sorted(path.iterdir()):
                node.children.append(
                    build_tree(child, current_depth + 1, max_depth),
                )
        except PermissionError as e:
            logger.debug("Permission denied listing directory %s: %s", path, e)
    else:
        try:
            node.depth_limited = any(path.iterdir())
        except PermissionError:
            pass
    return node


def count_tree_nodes(node: TreeNode) -> int:
    """Count the total number of nodes in the tree."""
    return 1 + sum(count_tree_nodes(c) for c in node.children)


def slice_lines(content: str, head: int | None, tail: int | None) -> str:
    """Return a line-sliced view of content using head or tail. No-op when both are None."""
    if head is None and tail is None:
        return content
    all_lines = content.splitlines(keepends=True)
    if head is not None:
        return "".join(all_lines[:head])
    assert tail is not None, "Both head and tail cannot be None here"
    return "".join(all_lines[-tail:])


def fmt_tree_node(node: TreeNode, indent: int = 0) -> str:
    """Recursively format a directory tree node with type and size annotations."""
    prefix = "  " * indent
    if node.type == "dir":
        depth_note = " (depth limit reached)" if node.depth_limited else ""
        size_note = f" ({fmt_size(node.size)})" if node.size > 0 else ""
        line = f"{prefix}[DIR] {node.name}/{size_note}{depth_note}"
    else:
        line = f"{prefix}[FILE] {node.name} ({fmt_size(node.size)})"
    lines: list[str] = [line]
    for child in node.children:
        lines.append(fmt_tree_node(child, indent + 1))
    return "\n".join(lines)


def fmt_dir_entries(entries: list[FileEntry]) -> str:
    """Format a list of FileEntry objects into a human-readable string."""
    if not entries:
        return "(empty directory)"
    lines = [
        f"{'[DIR]' if e.type == 'dir' else '[FILE]'} {e.name} ({fmt_size(e.size)})"
        for e in entries
    ]
    return f"[{len(entries)} entries]\n" + "\n".join(lines)


def has_depth_limit(node: TreeNode) -> bool:
    """Return True if any node in the tree was truncated by the depth limit."""
    if node.depth_limited:
        return True
    return any(has_depth_limit(c) for c in node.children)
