from datetime import date
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QInputMethodEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from desktop_todo.repository import TodoRepository
from desktop_todo.ui.main_window import MainWindow
from desktop_todo.ui.dialogs import TaskDialog, ProjectDialog


def test_ime_preedit_commit_and_outside_dismiss(tmp_path):
    app = QApplication.instance() or QApplication([])
    repo = TodoRepository(tmp_path / "ime.db")
    window = MainWindow(repo, QSettings(str(tmp_path / "ime.ini"), QSettings.Format.IniFormat), tray_available=False)
    window.show()
    dialog = TaskDialog(window, date.today())
    def enter_chinese():
        assert app.activePopupWidget() is None
        dialog.editor.setFocus()
        app.sendEvent(dialog.editor, QInputMethodEvent("zhongwen", []))
        assert dialog._composing
        assert dialog.isVisible()
        assert dialog.editor.text() == ""
        commit = QInputMethodEvent()
        commit.setCommitString("中文任务：检查机器人")
        app.sendEvent(dialog.editor, commit)
        assert dialog.textValue() == "中文任务：检查机器人"
        assert not dialog._composing
        QTest.keyClick(dialog.editor, Qt.Key.Key_Return)
    QTimer.singleShot(50, enter_chinese)
    QTimer.singleShot(1500, dialog.reject)
    assert dialog.exec() == 1
    task = repo.create_task(dialog.textValue(), date.today())
    assert repo.get_task(task.id).title == "中文任务：检查机器人"
    project = ProjectDialog(window)
    project.show()
    app.processEvents()
    for editor in (project.name_edit, project.goal_edit, project.stage_edit, project.action_edit):
        editor.setFocus()
        commit = QInputMethodEvent()
        commit.setCommitString("中文内容")
        app.sendEvent(editor, commit)
    assert set(project.values().values()) == {"中文内容"}
    QTest.mouseClick(window.date_label, Qt.MouseButton.LeftButton)
    assert not project.isVisible()
    assert project.result() == 0
    window.prepare_quit()
    window.close()
    repo.close()
