"""scripts/agent/__init__.py

Agent module public API.

Exports all component classes and the AgentREPL facade for backward compatibility.
"""

from agent.audit_event_emitter import AuditEventEmitter
from agent.bg_task_monitor import BgTaskMonitor
from agent.conversation_state_manager import ConversationStateManager
from agent.llm_turn_executor import LlmTurnExecutor
from agent.repl import AgentREPL
from agent.repl_input_loop import ReplInputLoop
from agent.resource_shutdown_coordinator import ResourceShutdownCoordinator
from agent.session_persister import SessionPersister
from agent.signal_handler import SignalHandler
from agent.startup_banner import StartupBanner
from agent.turnd_coordinator import TurnCoordinator
from agent.wal_checkpoint_manager import WalCheckpointManager
from agent.workflow_engine_adapter import WorkflowEngineAdapter

__all__ = [
    "ReplInputLoop",
    "SessionPersister",
    "WalCheckpointManager",
    "ResourceShutdownCoordinator",
    "StartupBanner",
    "SignalHandler",
    "AgentREPL",
    "BgTaskMonitor",
    "AuditEventEmitter",
    "ConversationStateManager",
    "TurnCoordinator",
    "LlmTurnExecutor",
    "WorkflowEngineAdapter",
]
