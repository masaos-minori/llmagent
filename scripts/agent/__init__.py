"""scripts/agent/__init__.py

Agent module public API.

Exports all component classes and the AgentREPL facade for backward compatibility.
"""

from agent.repl import AgentREPL
from agent.repl_input_loop import ReplInputLoop
from agent.resource_shutdown_coordinator import ResourceShutdownCoordinator
from agent.session_persister import SessionPersister
from agent.signal_handler import SignalHandler
from agent.startup_banner import StartupBanner
from agent.wal_checkpoint_manager import WalCheckpointManager

__all__ = [
    "ReplInputLoop",
    "SessionPersister",
    "WalCheckpointManager",
    "ResourceShutdownCoordinator",
    "StartupBanner",
    "SignalHandler",
    "AgentREPL",
]
