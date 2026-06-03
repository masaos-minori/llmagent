"""agent/commands/cmd_rag.py
Backward-compatibility shim.

Contents split into:
  cmd_tooling.py  — _ToolingMixin  (/tool, /plan)
  cmd_notes.py    — _NotesMixin    (/note)
  cmd_debug.py    — _DebugMixin    (/debug)
"""

from agent.commands.cmd_debug import _DebugMixin
from agent.commands.cmd_notes import _NotesMixin
from agent.commands.cmd_tooling import _ToolingMixin

__all__ = ["_ToolingMixin", "_NotesMixin", "_DebugMixin"]
