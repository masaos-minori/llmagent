#!/usr/bin/env python3
"""agent/commands/cmd_notes.py
Persistent notes mixin for CommandRegistry.

Provides _NotesMixin with:
  _cmd_note  — /note: add/list/delete persistent notes
"""

from agent.commands.formatter import (
    print_no_data,
    print_success,
    print_table,
    print_validation_error,
)
from agent.commands.mixin_base import MixinBase
from agent.commands.utils import parse_command_args


class _NotesMixin(MixinBase):
    """Persistent notes slash-command handlers."""

    def _note_add(self, text: str) -> None:
        """Add a new persistent note."""
        if not text:
            print_validation_error("/note add <text>")
            return
        note_id = self._ctx.session.add_note(text)
        if note_id is not None:
            print_success(f"Note added (id={note_id}).")
        else:
            print_validation_error("Failed to add note.")

    def _note_list(self) -> None:
        """List all persistent notes."""
        notes = self._ctx.session.list_notes()
        if not notes:
            print_no_data("No notes.")
            return
        rows = [
            [
                str(n["note_id"]),
                n["created_at"][:19],
                (n["content"][:41] + "..." if len(n["content"]) > 44 else n["content"]),
            ]
            for n in notes
        ]
        print_table(["ID", "Created", "Content"], rows)

    def _note_delete(self, arg: str) -> None:
        """Delete a note by id."""
        if not arg.isdigit():
            print_validation_error("/note delete <id>")
            return
        ok = self._ctx.session.delete_note(int(arg))
        if ok:
            print_success(f"Note {arg} deleted.")
        else:
            print_no_data(f"Note {arg} not found.")

    def _cmd_note(self, args: str) -> None:
        """Manage persistent cross-session notes.

        Usage:
          /note add <text>   Add a new note
          /note list         List all notes
          /note delete <id>  Delete a note by ID
        """
        tokens = args.strip().split(None, 1)
        parsed = parse_command_args(tokens)
        rest = parsed.positional[0].strip() if parsed.positional else ""
        dispatch = {
            "add": lambda: self._note_add(rest),
            "list": self._note_list,
            "delete": lambda: self._note_delete(rest),
        }
        handler = dispatch.get(parsed.subcommand or "")
        if handler:
            handler()
        else:
            print_validation_error("/note add <text> | /note list | /note delete <id>")
