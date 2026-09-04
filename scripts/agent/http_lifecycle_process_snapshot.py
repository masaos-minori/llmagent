"""Process snapshot provider using /proc filesystem (no psutil dependency)."""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from scripts.agent.http_lifecycle import HttpServerLifecycleManager


@dataclass(frozen=True)
class ProcessInfoSnapshot:
    """Immutable snapshot of process information."""

    pid: int
    name: str
    cmdline: list[str]
    cwd: str | None
    status: dict[str, str]
    open_files: list[str]
    connections: list[tuple[str, str, str]]
    memory_info: dict[str, int]
    io_counters: dict[str, int]
    num_threads: int
    create_time: float | None
    cpu_times: dict[str, float]
    env_vars: dict[str, str]
    maps: list[tuple[str, str, str, str, str]]
    cgroups: list[tuple[int, str, str]]
    oom_score: int
    oom_score_adj: int
    sched_stat: tuple[int, int, int]
    numa_maps: dict[str, dict[str, int]]
    syscall_info: dict[str, int]
    stack_trace: list[tuple[str, str]]
    limits: list[tuple[str, str, str, str]]
    fd_list: list[tuple[int, str]]

    @classmethod
    def from_proc_pid(cls, pid: int) -> ProcessInfoSnapshot:
        """Create snapshot from /proc/[pid] filesystem.

        Args:
            pid: Process ID to inspect.

        Returns:
            ProcessInfoSnapshot instance.

        Raises:
            FileNotFoundError: If /proc/[pid] does not exist.
        """
        proc_dir = f"/proc/{pid}"

        if not os.path.exists(proc_dir):
            raise FileNotFoundError(f"/proc/{pid} does not exist")

        name = cls._read_name(pid)
        cmdline = cls._read_cmdline(pid)
        cwd = cls._read_cwd(pid)
        status = cls._read_status(pid)
        open_files = cls._read_open_files(pid)
        connections = cls._read_connections(pid)
        memory_info = cls._read_memory_info(pid)
        io_counters = cls._read_io_counters(pid)
        num_threads = cls._read_num_threads(pid, status)
        create_time = cls._read_create_time(pid, status)
        cpu_times = cls._read_cpu_times(pid, status)
        env_vars = cls._read_env_vars(pid)
        maps = cls._read_maps(pid)
        cgroups = cls._read_cgroups(pid)
        oom_score = cls._read_oom_score(pid)
        oom_score_adj = cls._read_oom_score_adj(pid)
        sched_stat = cls._read_sched_stat(pid)
        numa_maps = cls._read_numa_maps(pid)
        syscall_info = cls._read_syscall_info(pid)
        stack_trace = cls._read_stack_trace(pid)
        limits = cls._read_limits(pid)
        fd_list = cls._read_fd_list(pid)

        return cls(
            pid=pid,
            name=name,
            cmdline=cmdline,
            cwd=cwd,
            status=status,
            open_files=open_files,
            connections=connections,
            memory_info=memory_info,
            io_counters=io_counters,
            num_threads=num_threads,
            create_time=create_time,
            cpu_times=cpu_times,
            env_vars=env_vars,
            maps=maps,
            cgroups=cgroups,
            oom_score=oom_score,
            oom_score_adj=oom_score_adj,
            sched_stat=sched_stat,
            numa_maps=numa_maps,
            syscall_info=syscall_info,
            stack_trace=stack_trace,
            limits=limits,
            fd_list=fd_list,
        )

    @staticmethod
    def _read_name(pid: int) -> str:
        """Read process name from /proc/[pid]/comm."""
        path = f"/proc/{pid}/comm"
        try:
            with open(path, "r") as f:
                return f.read().strip()
        except OSError:
            return ""

    @staticmethod
    def _read_cmdline(pid: int) -> list[str]:
        """Read command line from /proc/[pid]/cmdline."""
        path = f"/proc/{pid}/cmdline"
        try:
            with open(path, "rb") as f:
                raw = f.read()
            if not raw:
                return []
            parts = raw.split(b"\x00")
            return [p.decode("utf-8", errors="replace") for p in parts if p]
        except OSError:
            return []

    @staticmethod
    def _read_cwd(pid: int) -> str | None:
        """Read current working directory from /proc/[pid]/cwd symlink."""
        link_path = f"/proc/{pid}/cwd"
        try:
            return os.readlink(link_path)
        except OSError:
            return None

    @staticmethod
    def _read_status(pid: int) -> dict[str, str]:
        """Read process status from /proc/[pid]/status."""
        path = f"/proc/{pid}/status"
        result: dict[str, str] = {}
        try:
            with open(path, "r") as f:
                for line in f:
                    if ":" in line:
                        key, _, value = line.partition(":")
                        result[key.strip()] = value.strip()
        except OSError:
            pass
        return result

    @staticmethod
    def _read_open_files(pid: int) -> list[str]:
        """Read open files from /proc/[pid]/fd symlinks."""
        fd_dir = f"/proc/{pid}/fd"
        open_files: list[str] = []
        try:
            for fd_name in os.listdir(fd_dir):
                fd_path = os.path.join(fd_dir, fd_name)
                try:
                    target = os.readlink(fd_path)
                    open_files.append(target)
                except OSError:
                    pass
        except OSError:
            pass
        return open_files

    @staticmethod
    def _read_connections(pid: int) -> list[tuple[str, str, str]]:
        """Read network connections from /proc/[pid]/net/tcp and tcp6."""
        connections: list[tuple[str, str, str]] = []
        for net_file in ("tcp", "tcp6"):
            path = f"/proc/{pid}/net/{net_file}"
            try:
                with open(path, "r") as f:
                    next(f)  # skip header
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            local = parts[1]
                            remote = parts[2]
                            state = parts[3]
                            connections.append((local, remote, state))
            except OSError:
                pass
        return connections

    @staticmethod
    def _read_memory_info(pid: int) -> dict[str, int]:
        """Read memory info from /proc/[pid]/statm."""
        path = f"/proc/{pid}/statm"
        result: dict[str, int] = {}
        try:
            with open(path, "r") as f:
                values = f.read().strip().split()
                keys = ["size", "resident", "shared", "text", "lib", "data", "dt"]
                for i, val in enumerate(values):
                    if i < len(keys):
                        result[keys[i]] = int(val)
        except OSError:
            pass
        return result

    @staticmethod
    def _read_io_counters(pid: int) -> dict[str, int]:
        """Read I/O counters from /proc/[pid]/io."""
        path = f"/proc/{pid}/io"
        result: dict[str, int] = {}
        try:
            with open(path, "r") as f:
                for line in f:
                    if ":" in line:
                        key, _, value = line.partition(":")
                        result[key.strip()] = int(value.strip())
        except OSError:
            pass
        return result

    @staticmethod
    def _read_num_threads(pid: int, status: dict[str, str]) -> int:
        """Get number of threads from status or stat."""
        threads_str = status.get("Threads", "")
        if threads_str:
            try:
                return int(threads_str)
            except ValueError:
                pass
        path = f"/proc/{pid}/stat"
        try:
            with open(path, "r") as f:
                content = f.read()
            start = content.find("(") + 1
            end = content.rfind(")")
            if start > 0 and end > start:
                fields_after_comm = content[end + 2:].split()
                if len(fields_after_comm) >= 19:
                    return int(fields_after_comm[19])
        except OSError:
            pass
        return 1

    @staticmethod
    def _read_create_time(pid: int, status: dict[str, str]) -> float | None:
        """Get process creation time from status starttime field."""
        starttime_str = status.get("starttime", "")
        if starttime_str:
            try:
                clk_tck = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
                uptime = os.times().tms_utime + os.times().tms_stime
                create_time = uptime - (float(starttime_str) / clk_tck)
                return create_time
            except (ValueError, KeyError, AttributeError):
                pass
        return None

    @staticmethod
    def _read_cpu_times(pid: int, status: dict[str, str]) -> dict[str, float]:
        """Get CPU times from /proc/[pid]/stat."""
        path = f"/proc/{pid}/stat"
        result: dict[str, float] = {"user": 0.0, "system": 0.0}
        try:
            with open(path, "r") as f:
                content = f.read()
            start = content.find("(") + 1
            end = content.rfind(")")
            if start > 0 and end > start:
                fields_after_comm = content[end + 2:].split()
                if len(fields_after_comm) >= 13:
                    result["user"] = float(fields_after_comm[13]) / os.sysconf(os.sysconf_names["SC_CLK_TCK"])
                    result["system"] = float(fields_after_comm[14]) / os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        except OSError:
            pass
        return result

    @staticmethod
    def _read_env_vars(pid: int) -> dict[str, str]:
        """Read environment variables from /proc/[pid]/environ."""
        path = f"/proc/{pid}/environ"
        result: dict[str, str] = {}
        try:
            with open(path, "rb") as f:
                raw = f.read()
            for part in raw.split(b"\x00"):
                if b"=" in part:
                    key, _, value = part.partition(b"=")
                    result[key.decode("utf-8", errors="replace")] = value.decode("utf-8", errors="replace")
        except OSError:
            pass
        return result

    @staticmethod
    def _read_maps(pid: int) -> list[tuple[str, str, str, str, str]]:
        """Read memory mappings from /proc/[pid]/maps."""
        path = f"/proc/{pid}/maps"
        result: list[tuple[str, str, str, str, str]] = []
        try:
            with open(path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        addr_range = parts[0]
                        perms = parts[1]
                        offset = parts[2]
                        dev = parts[3]
                        pathname = parts[4] if len(parts) > 4 else ""
                        start, end = addr_range.split("-")
                        result.append((start, end, perms, offset, dev))
        except OSError:
            pass
        return result

    @staticmethod
    def _read_cgroups(pid: int) -> list[tuple[int, str, str]]:
        """Read cgroup information from /proc/[pid]/cgroup."""
        path = f"/proc/{pid}/cgroup"
        result: list[tuple[int, str, str]] = []
        try:
            with open(path, "r") as f:
                for line in f:
                    parts = line.strip().split(":")
                    if len(parts) == 3:
                        try:
                            hierarchy_id = int(parts[0])
                            subsystems = parts[1]
                            cgroup_path = parts[2]
                            result.append((hierarchy_id, subsystems, cgroup_path))
                        except ValueError:
                            pass
        except OSError:
            pass
        return result

    @staticmethod
    def _read_oom_score(pid: int) -> int:
        """Read OOM score from /proc/[pid]/oom_score."""
        path = f"/proc/{pid}/oom_score"
        try:
            with open(path, "r") as f:
                return int(f.read().strip())
        except OSError:
            return 0

    @staticmethod
    def _read_oom_score_adj(pid: int) -> int:
        """Read OOM score adjustment from /proc/[pid]/oom_score_adj."""
        path = f"/proc/{pid}/oom_score_adj"
        try:
            with open(path, "r") as f:
                return int(f.read().strip())
        except OSError:
            return 0

    @staticmethod
    def _read_sched_stat(pid: int) -> tuple[int, int, int]:
        """Read scheduling statistics from /proc/[pid]/schedstat."""
        path = f"/proc/{pid}/schedstat"
        try:
            with open(path, "r") as f:
                values = f.read().strip().split()
                return (int(values[0]), int(values[1]), int(values[2]))
        except (OSError, IndexError):
            return (0, 0, 0)

    @staticmethod
    def _read_numa_maps(pid: int) -> dict[str, dict[str, int]]:
        """Read NUMA memory policy from /proc/[pid]/numa_maps."""
        path = f"/proc/{pid}/numa_maps"
        result: dict[str, dict[str, int]] = {}
        try:
            with open(path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        address = parts[0]
                        policies: dict[str, int] = {}
                        for p in parts[1:]:
                            if "=" in p:
                                k, _, v = p.partition("=")
                                try:
                                    policies[k] = int(v)
                                except ValueError:
                                    pass
                        result[address] = policies
        except OSError:
            pass
        return result

    @staticmethod
    def _read_syscall_info(pid: int) -> dict[str, int]:
        """Read system call information from /proc/[pid]/syscall."""
        path = f"/proc/{pid}/syscall"
        result: dict[str, int] = {}
        try:
            with open(path, "r") as f:
                values = f.read().strip().split()
                if len(values) >= 3:
                    result["nr"] = int(values[0])
                    result["arg0"] = int(values[1])
                    result["arg1"] = int(values[2])
        except (OSError, IndexError, ValueError):
            pass
        return result

    @staticmethod
    def _read_stack_trace(pid: int) -> list[tuple[str, str]]:
        """Read kernel stack trace from /proc/[pid]/stack."""
        path = f"/proc/{pid}/stack"
        result: list[tuple[str, str]] = []
        try:
            with open(path, "r") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("[") and "]" in stripped:
                        func_start = stripped.index("[") + 1
                        func_end = stripped.index("]")
                        func_name = stripped[func_start:func_end]
                        rest = stripped[func_end + 1:].strip()
                        result.append((func_name, rest))
        except OSError:
            pass
        return result

    @staticmethod
    def _read_limits(pid: int) -> list[tuple[str, str, str, str]]:
        """Read resource limits from /proc/[pid]/limits."""
        path = f"/proc/{pid}/limits"
        result: list[tuple[str, str, str, str]] = []
        try:
            with open(path, "r") as f:
                header_skipped = False
                for line in f:
                    if not header_skipped:
                        if "Limit" in line and "Soft" in line and "Hard" in line:
                            header_skipped = True
                        continue
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        limit_name = parts[0]
                        soft_limit = parts[1]
                        hard_limit = parts[2]
                        unit = parts[3]
                        result.append((limit_name, soft_limit, hard_limit, unit))
        except OSError:
            pass
        return result

    @staticmethod
    def _read_fd_list(pid: int) -> list[tuple[int, str]]:
        """Read file descriptor list from /proc/[pid]/fd."""
        fd_dir = f"/proc/{pid}/fd"
        result: list[tuple[int, str]] = []
        try:
            for fd_name in os.listdir(fd_dir):
                try:
                    fd_num = int(fd_name)
                    fd_path = os.path.join(fd_dir, fd_name)
                    target = os.readlink(fd_path)
                    result.append((fd_num, target))
                except (ValueError, OSError):
                    pass
        except OSError:
            pass
        return result


class ProcessSnapshotProvider:
    """Provides process snapshots via /proc filesystem access."""

    @staticmethod
    def get_info(
        server_key: str,
        proc: subprocess.Popen[bytes],
        pgid: int | None,
    ) -> ProcessInfoSnapshot | None:
        """Return a ``ProcessInfoSnapshot`` for *server_key* or ``None``.

        Falls back to the parent PID when the child has already exited.
        """
        pid = getattr(proc, "pid", None)
        if pid is None:
            logger.debug("%s: no PID available on proc object", server_key)
            return None
        try:
            return ProcessInfoSnapshot.from_proc_pid(pid)
        except FileNotFoundError:
            # Child may have exited; fall back to parent group leader.
            if pgid is not None:
                try:
                    return ProcessInfoSnapshot.from_proc_pid(pgid)
                except FileNotFoundError:
                    pass
            logger.debug("%s: /proc/%d does not exist", server_key, pid)
            return None

    @staticmethod
    def get_snapshot(
        server_key: str,
        proc: subprocess.Popen[bytes],
        pgid: int | None,
    ) -> dict | None:
        """Return a JSON-serialisable snapshot of *server_key*.

        Returns ``None`` when no snapshot can be obtained.
        """
        info = ProcessSnapshotProvider.get_info(server_key, proc, pgid)
        if info is None:
            return None
        return asdict(info)

    @staticmethod
    def list_processes(manager: HttpServerLifecycleManager) -> list[ProcessInfoSnapshot]:
        """Return snapshots for every managed server whose process is alive."""
        results: list[ProcessInfoSnapshot] = []
        for server_key in manager._servers:
            proc = manager._servers[server_key].get("proc")
            if proc is None:
                continue
            pgid = getattr(proc, "pgid", None) or getattr(proc, "pgrp", None)
            if pgid is None:
                try:
                    pgid = os.getpgid(proc.pid)
                except OSError:
                    pass
            snapshot = ProcessSnapshotProvider.get_info(server_key, proc, pgid)
            if snapshot is not None:
                results.append(snapshot)
        return results
