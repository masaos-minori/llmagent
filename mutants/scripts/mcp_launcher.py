#!/usr/bin/env python3
"""scripts/mcp_launcher.py

Unified standalone launcher for individual MCP servers. Discovers every
MCPServer subclass under mcp_servers.* by reflection and launches one by key,
for local development/debugging without hand-editing sys.path or memorizing
each server's entry-point module path.

Usage:
    uv run python scripts/mcp_launcher.py --list
    uv run python scripts/mcp_launcher.py <server_key>
    uv run python scripts/mcp_launcher.py <server_key> --force
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import pkgutil
import sys

import httpx
from mcp_servers.server import MCPServer


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_discover_servers__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_discover_servers__mutmut)
def discover_servers() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_orig() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_1() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = None
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_2() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        None, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_3() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix=None
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_4() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_5() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_6() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="XXmcp_servers.XX"
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_7() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="MCP_SERVERS."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_8() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(None)[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_9() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.partition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_10() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition("XX.XX")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_11() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[3] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_12() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] != "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_13() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "XX__main__XX":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_14() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__MAIN__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_15() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            break
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_16() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = None
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_17() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(None)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_18() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(None, file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_19() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=None)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_20() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_21() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", )
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_22() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            break
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_23() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(None, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_24() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, None):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_25() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_26() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, ):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_27() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) or obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_28() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(None, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_29() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, None) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_30() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_31() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, ) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_32() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_33() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = None
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_34() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) and obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_35() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(None, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_36() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, None, None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_37() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr("server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_38() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_39() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", ) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_40() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "XXserver_keyXX", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_41() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "SERVER_KEY", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_42() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    None
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_43() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removeprefix(
                    "-mcp"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_44() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "XX-mcpXX"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_45() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-MCP"
                )
                registry[key] = obj
    return registry


def x_discover_servers__mutmut_46() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = None
    return registry

mutants_x_discover_servers__mutmut['_mutmut_orig'] = x_discover_servers__mutmut_orig # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_1'] = x_discover_servers__mutmut_1 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_2'] = x_discover_servers__mutmut_2 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_3'] = x_discover_servers__mutmut_3 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_4'] = x_discover_servers__mutmut_4 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_5'] = x_discover_servers__mutmut_5 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_6'] = x_discover_servers__mutmut_6 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_7'] = x_discover_servers__mutmut_7 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_8'] = x_discover_servers__mutmut_8 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_9'] = x_discover_servers__mutmut_9 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_10'] = x_discover_servers__mutmut_10 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_11'] = x_discover_servers__mutmut_11 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_12'] = x_discover_servers__mutmut_12 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_13'] = x_discover_servers__mutmut_13 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_14'] = x_discover_servers__mutmut_14 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_15'] = x_discover_servers__mutmut_15 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_16'] = x_discover_servers__mutmut_16 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_17'] = x_discover_servers__mutmut_17 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_18'] = x_discover_servers__mutmut_18 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_19'] = x_discover_servers__mutmut_19 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_20'] = x_discover_servers__mutmut_20 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_21'] = x_discover_servers__mutmut_21 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_22'] = x_discover_servers__mutmut_22 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_23'] = x_discover_servers__mutmut_23 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_24'] = x_discover_servers__mutmut_24 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_25'] = x_discover_servers__mutmut_25 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_26'] = x_discover_servers__mutmut_26 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_27'] = x_discover_servers__mutmut_27 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_28'] = x_discover_servers__mutmut_28 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_29'] = x_discover_servers__mutmut_29 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_30'] = x_discover_servers__mutmut_30 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_31'] = x_discover_servers__mutmut_31 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_32'] = x_discover_servers__mutmut_32 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_33'] = x_discover_servers__mutmut_33 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_34'] = x_discover_servers__mutmut_34 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_35'] = x_discover_servers__mutmut_35 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_36'] = x_discover_servers__mutmut_36 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_37'] = x_discover_servers__mutmut_37 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_38'] = x_discover_servers__mutmut_38 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_39'] = x_discover_servers__mutmut_39 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_40'] = x_discover_servers__mutmut_40 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_41'] = x_discover_servers__mutmut_41 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_42'] = x_discover_servers__mutmut_42 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_43'] = x_discover_servers__mutmut_43 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_44'] = x_discover_servers__mutmut_44 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_45'] = x_discover_servers__mutmut_45 # type: ignore # mutmut generated
mutants_x_discover_servers__mutmut['x_discover_servers__mutmut_46'] = x_discover_servers__mutmut_46 # type: ignore # mutmut generated
mutants_x_port_is_responding__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_port_is_responding__mutmut)
def port_is_responding(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=timeout)
        is_up: bool = resp.status_code < 500
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def x_port_is_responding__mutmut_orig(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=timeout)
        is_up: bool = resp.status_code < 500
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def x_port_is_responding__mutmut_1(port: int, timeout: float = 1.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=timeout)
        is_up: bool = resp.status_code < 500
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def x_port_is_responding__mutmut_2(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = None
        is_up: bool = resp.status_code < 500
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def x_port_is_responding__mutmut_3(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(None, timeout=timeout)
        is_up: bool = resp.status_code < 500
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def x_port_is_responding__mutmut_4(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=None)
        is_up: bool = resp.status_code < 500
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def x_port_is_responding__mutmut_5(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(timeout=timeout)
        is_up: bool = resp.status_code < 500
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def x_port_is_responding__mutmut_6(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", )
        is_up: bool = resp.status_code < 500
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def x_port_is_responding__mutmut_7(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=timeout)
        is_up: bool = None
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def x_port_is_responding__mutmut_8(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=timeout)
        is_up: bool = resp.status_code <= 500
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def x_port_is_responding__mutmut_9(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=timeout)
        is_up: bool = resp.status_code < 501
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def x_port_is_responding__mutmut_10(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=timeout)
        is_up: bool = resp.status_code < 500
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return True

mutants_x_port_is_responding__mutmut['_mutmut_orig'] = x_port_is_responding__mutmut_orig # type: ignore # mutmut generated
mutants_x_port_is_responding__mutmut['x_port_is_responding__mutmut_1'] = x_port_is_responding__mutmut_1 # type: ignore # mutmut generated
mutants_x_port_is_responding__mutmut['x_port_is_responding__mutmut_2'] = x_port_is_responding__mutmut_2 # type: ignore # mutmut generated
mutants_x_port_is_responding__mutmut['x_port_is_responding__mutmut_3'] = x_port_is_responding__mutmut_3 # type: ignore # mutmut generated
mutants_x_port_is_responding__mutmut['x_port_is_responding__mutmut_4'] = x_port_is_responding__mutmut_4 # type: ignore # mutmut generated
mutants_x_port_is_responding__mutmut['x_port_is_responding__mutmut_5'] = x_port_is_responding__mutmut_5 # type: ignore # mutmut generated
mutants_x_port_is_responding__mutmut['x_port_is_responding__mutmut_6'] = x_port_is_responding__mutmut_6 # type: ignore # mutmut generated
mutants_x_port_is_responding__mutmut['x_port_is_responding__mutmut_7'] = x_port_is_responding__mutmut_7 # type: ignore # mutmut generated
mutants_x_port_is_responding__mutmut['x_port_is_responding__mutmut_8'] = x_port_is_responding__mutmut_8 # type: ignore # mutmut generated
mutants_x_port_is_responding__mutmut['x_port_is_responding__mutmut_9'] = x_port_is_responding__mutmut_9 # type: ignore # mutmut generated
mutants_x_port_is_responding__mutmut['x_port_is_responding__mutmut_10'] = x_port_is_responding__mutmut_10 # type: ignore # mutmut generated
mutants_x_main__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_main__mutmut)
def main() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_orig() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_1() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = None
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_2() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=None)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_3() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        None, nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_4() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs=None, help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_5() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help=None
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_6() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_7() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_8() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_9() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "XXserver_keyXX", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_10() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "SERVER_KEY", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_11() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="XX?XX", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_12() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="XXServer key to launch (see --list)XX"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_13() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_14() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="SERVER KEY TO LAUNCH (SEE --LIST)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_15() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        None, action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_16() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action=None, help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_17() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help=None
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_18() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_19() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_20() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_21() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "XX--listXX", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_22() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--LIST", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_23() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="XXstore_trueXX", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_24() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="STORE_TRUE", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_25() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="XXList all discovered server keysXX"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_26() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="list all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_27() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="LIST ALL DISCOVERED SERVER KEYS"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_28() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        None, action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_29() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action=None, help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_30() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help=None
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_31() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_32() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_33() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_34() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "XX--forceXX", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_35() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--FORCE", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_36() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="XXstore_trueXX", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_37() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="STORE_TRUE", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_38() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="XXBypass the port-collision guardXX"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_39() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_40() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="BYPASS THE PORT-COLLISION GUARD"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_41() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = None

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_42() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = None
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_43() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list and not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_44() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_45() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(None):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_46() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(None)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_47() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = None
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_48() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(None)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_49() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is not None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_50() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            None,
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_51() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=None,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_52() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_53() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_54() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(None)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_55() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(2)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_56() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = None
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_57() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = None
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_58() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force or port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_59() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_60() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(None):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_61() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            None,
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_62() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=None,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_63() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_64() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_65() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "XXUse --force to start anyway.XX",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_66() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_67() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "USE --FORCE TO START ANYWAY.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()


def x_main__mutmut_68() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(None)
    instance.run_http()


def x_main__mutmut_69() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(2)
    instance.run_http()

mutants_x_main__mutmut['_mutmut_orig'] = x_main__mutmut_orig # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_1'] = x_main__mutmut_1 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_2'] = x_main__mutmut_2 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_3'] = x_main__mutmut_3 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_4'] = x_main__mutmut_4 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_5'] = x_main__mutmut_5 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_6'] = x_main__mutmut_6 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_7'] = x_main__mutmut_7 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_8'] = x_main__mutmut_8 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_9'] = x_main__mutmut_9 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_10'] = x_main__mutmut_10 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_11'] = x_main__mutmut_11 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_12'] = x_main__mutmut_12 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_13'] = x_main__mutmut_13 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_14'] = x_main__mutmut_14 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_15'] = x_main__mutmut_15 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_16'] = x_main__mutmut_16 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_17'] = x_main__mutmut_17 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_18'] = x_main__mutmut_18 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_19'] = x_main__mutmut_19 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_20'] = x_main__mutmut_20 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_21'] = x_main__mutmut_21 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_22'] = x_main__mutmut_22 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_23'] = x_main__mutmut_23 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_24'] = x_main__mutmut_24 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_25'] = x_main__mutmut_25 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_26'] = x_main__mutmut_26 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_27'] = x_main__mutmut_27 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_28'] = x_main__mutmut_28 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_29'] = x_main__mutmut_29 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_30'] = x_main__mutmut_30 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_31'] = x_main__mutmut_31 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_32'] = x_main__mutmut_32 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_33'] = x_main__mutmut_33 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_34'] = x_main__mutmut_34 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_35'] = x_main__mutmut_35 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_36'] = x_main__mutmut_36 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_37'] = x_main__mutmut_37 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_38'] = x_main__mutmut_38 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_39'] = x_main__mutmut_39 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_40'] = x_main__mutmut_40 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_41'] = x_main__mutmut_41 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_42'] = x_main__mutmut_42 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_43'] = x_main__mutmut_43 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_44'] = x_main__mutmut_44 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_45'] = x_main__mutmut_45 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_46'] = x_main__mutmut_46 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_47'] = x_main__mutmut_47 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_48'] = x_main__mutmut_48 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_49'] = x_main__mutmut_49 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_50'] = x_main__mutmut_50 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_51'] = x_main__mutmut_51 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_52'] = x_main__mutmut_52 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_53'] = x_main__mutmut_53 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_54'] = x_main__mutmut_54 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_55'] = x_main__mutmut_55 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_56'] = x_main__mutmut_56 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_57'] = x_main__mutmut_57 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_58'] = x_main__mutmut_58 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_59'] = x_main__mutmut_59 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_60'] = x_main__mutmut_60 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_61'] = x_main__mutmut_61 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_62'] = x_main__mutmut_62 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_63'] = x_main__mutmut_63 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_64'] = x_main__mutmut_64 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_65'] = x_main__mutmut_65 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_66'] = x_main__mutmut_66 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_67'] = x_main__mutmut_67 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_68'] = x_main__mutmut_68 # type: ignore # mutmut generated
mutants_x_main__mutmut['x_main__mutmut_69'] = x_main__mutmut_69 # type: ignore # mutmut generated


if __name__ == "__main__":
    main()
