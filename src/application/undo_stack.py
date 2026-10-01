"""
Undo/Redo Command Architecture for Genealogy System.
Provides transactional undoable operations on domain entities.
"""

from typing import Callable, Any, Optional, List
from PySide6.QtGui import QUndoStack, QUndoCommand


class BaseGenealogyCommand(QUndoCommand):
    """Abstract Base Class for all undoable genealogy actions."""

    def __init__(self, description: str):
        super().__init__(description)
        self.description = description


class UpdatePersonCommand(BaseGenealogyCommand):
    """Command for updating a person's attributes with full undo support."""

    def __init__(
        self,
        person_id: str,
        old_data: dict,
        new_data: dict,
        apply_fn: Callable[[str, dict], None],
        description: str = "Edycja osoby"
    ):
        super().__init__(description)
        self.person_id = person_id
        self.old_data = old_data
        self.new_data = new_data
        self.apply_fn = apply_fn
        self._is_first_run = True

    def redo(self):
        if not self._is_first_run:
            self.apply_fn(self.person_id, self.new_data)
        self._is_first_run = False

    def undo(self):
        self.apply_fn(self.person_id, self.old_data)


class UndoManager:
    """Singleton wrapper for PySide6 QUndoStack."""

    def __init__(self):
        self.stack = QUndoStack()

    def push(self, command: QUndoCommand):
        self.stack.push(command)

    def undo(self):
        if self.stack.canUndo():
            self.stack.undo()

    def redo(self):
        if self.stack.canRedo():
            self.stack.redo()

    def can_undo(self) -> bool:
        return self.stack.canUndo()

    def can_redo(self) -> bool:
        return self.stack.canRedo()

    def undo_text(self) -> str:
        return self.stack.undoText()

    def redo_text(self) -> str:
        return self.stack.redoText()
