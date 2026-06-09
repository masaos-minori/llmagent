#!/usr/bin/env python3
"""agent/commands/cmd_notes.py
Persistent notes mixin for CommandRegistry.

Provides _NotesMixin with:
  _cmd_note  — /note: add/list/delete persistent notes
"""

from agent.commands.mixin_base import MixinBase


def _format_notes_table(notes: list[dict]) -> list[str]:
    """Format notes list as printable lines for /note list display."""
    lines = [f"{'ID':>4}  {'Created':>19}  Content", "-" * 70]
    for n in notes:
        preview = n["content"][:41] + "..." if len(n["content"]) > 44 else n["content"]
        lines.append(f"{n['note_id']:>4}  {n['created_at'][:19]:>19}  {preview}")
    return lines


class _NotesMixin(MixinBase):
    """Persistent notes slash-command handlers."""

    def _note_add(self, text: str) -> None:
        """Add a new persistent note."""
        if not text:
            print("Usage: /note add <text>")
            return
        note_id = self._ctx.session.add_note(text)
        if note_id is not None:
            print(f"Note added (id={note_id}).")
        else:
            print("Failed to add note.")

    def _note_list(self) -> None:
        """List all persistent notes."""
        notes = self._ctx.session.list_notes()
        if not notes:
            print("No notes.")
            return
        for line in _format_notes_table(notes):
            print(line)

    def _note_delete(self, arg: str) -> None:
        """Delete a note by id."""
        if not arg.isdigit():
            print("Usage: /note delete <id>")
            return
        ok = self._ctx.session.delete_note(int(arg))
        print(f"Note {arg} {'deleted.' if ok else 'not found.'}")

    def _cmd_note(self, args: str) -> None:
        """Manage persistent cross-session notes.

        Usage:
          /note add <text>   Add a new note
          /note list         List all notes
          /note delete <id>  Delete a note by ID
        """
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else ""
        rest = parts[1].strip() if len(parts) > 1 else ""
        if sub == "add":
            self._note_add(rest)
        elif sub == "list":
            self._note_list()
        elif sub == "delete":
            self._note_delete(rest)
        else:
            print("Usage: /note add <text> | /note list | /note delete <id>")
