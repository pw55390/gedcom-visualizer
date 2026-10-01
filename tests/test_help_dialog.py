"""
Unit test for HelpDialog GEDCOM Reference module.
"""

from PySide6.QtWidgets import QApplication
from src.gui.views.help_dialog import HelpDialog


def test_help_dialog_initialization():
    app = QApplication.instance() or QApplication([])
    dialog = HelpDialog()

    assert dialog.tab_widget.count() == 3
    assert dialog.tags_table.rowCount() > 20

    # Test filtering tags
    dialog.tag_search_input.setText("OCCU")
    assert dialog.tags_table.rowCount() == 1
    assert dialog.tags_table.item(0, 0).text() == "OCCU"
