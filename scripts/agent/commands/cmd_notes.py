#!/usr/bin/env python3
"""agent/commands/cmd_notes.py
Persistent notes mixin for CommandRegistry.

Provides _NotesMixin with:
  _cmd_note  — /note: add/list/delete persistent notes
"""

from agent.commands.exceptions import UnknownSubcommandError
from agent.commands.mixin_base import MixinBase
from agent.commands.utils import parse_command_args

NOTE_CONTENT_MAX_CHARS = 44
NOTE_CONTENT_TRUNCATE_AT = NOTE_CONTENT_MAX_CHARS - 3


class _NotesMixin(MixinBase):
    """Persistent notes slash-command handlers."""

    def _note_add(self, text: str) -> None:
        """Add a new persistent note."""
        if not text:
            self._out.write_validation_error("/note add <text>")
            return
        note_id = self._ctx.session.add_note(text)
        if note_id is not None:
            self._out.write_success(f"Note added (id={note_id}).")
        else:
            self._out.write_validation_error("Failed to add note.")

    def _note_list(self) -> None:
        """List all persistent notes."""
        notes = self._ctx.session.list_notes()
        if not notes:
            self._out.write_no_data("No notes.")
            return
        rows = [
            [
                str(n["note_id"]),
                "✓" if n.get("pinned") else "",
                n["created_at"][:19],
                (
                    n["content"][:NOTE_CONTENT_TRUNCATE_AT] + "..."
                    if len(n["content"]) > NOTE_CONTENT_MAX_CHARS
                    else n["content"]
                ),
            ]
            for n in notes
        ]
        self._out.write_table(["ID", "Pin", "Created", "Content"], rows)

    def _note_delete(self, arg: str) -> None:
        """Delete a note by id."""
        if not arg.isdigit():
            self._out.write_validation_error("/note delete <id>")
            return
        ok = self._ctx.session.delete_note(int(arg))
        if ok:
            self._out.write_success(f"Note {arg} deleted.")
        else:
            self._out.write_no_data(f"Note {arg} not found.")

    def _note_pin(self, arg: str) -> None:
        """Pin a note by id."""
        if not arg.isdigit():
            self._out.write_validation_error("/note pin <id>")
            return
        ok = self._ctx.session.pin_note(int(arg))
        if ok:
            self._out.write_success(f"Note {arg} pinned.")
        else:
            self._out.write_no_data(f"Note {arg} not found.")

    def _note_unpin(self, arg: str) -> None:
        """Unpin a note by id."""
        if not arg.isdigit():
            self._out.write_validation_error("/note unpin <id>")
            return
        ok = self._ctx.session.unpin_note(int(arg))
        if ok:
            self._out.write_success(f"Note {arg} unpinned.")
        else:
            self._out.write_no_data(f"Note {arg} not found.")

    def _note_search(self, query: str) -> None:
        """Search notes by content."""
        if not query:
            self._out.write_validation_error("/note search <query>")
            return
        notes = self._ctx.session.search_notes(query)
        if not notes:
            self._out.write_no_data("No matching notes.")
            return
        rows = [
            [
                str(n["note_id"]),
                "✓" if n.get("pinned") else "",
                n["created_at"][:19],
                (
                    n["content"][:NOTE_CONTENT_TRUNCATE_AT] + "..."
                    if len(n["content"]) > NOTE_CONTENT_MAX_CHARS
                    else n["content"]
                ),
            ]
            for n in notes
        ]
        self._out.write_table(["ID", "Pin", "Created", "Content"], rows)

    def _cmd_note(self, args: str) -> None:
        """Manage persistent cross-session notes.

        Usage:
          /note add <text>    Add a new note
          /note list          List all notes (pinned column included)
          /note delete <id>   Delete a note by ID
          /note pin <id>      Pin a note (injected at session start)
          /note unpin <id>    Unpin a note
          /note search <q>    Search notes by content (LIKE)
        """
        tokens = args.strip().split(None, 1)
        parsed = parse_command_args(tokens)
        rest = parsed.positional[0].strip() if parsed.positional else ""
        dispatch = {
            "add": lambda: self._note_add(rest),
            "list": self._note_list,
            "delete": lambda: self._note_delete(rest),
            "pin": lambda: self._note_pin(rest),
            "unpin": lambda: self._note_unpin(rest),
            "search": lambda: self._note_search(rest),
        }
        handler = dispatch.get(parsed.subcommand or "")
        if handler:
            handler()
        else:
            raise UnknownSubcommandError(
                parsed.subcommand or "", tuple(dispatch.keys())
            )
