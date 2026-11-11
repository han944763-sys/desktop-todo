from datetime import date, timedelta
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox
from desktop_todo.repository import TodoRepository
from desktop_todo.ui.main_window import MainWindow
from desktop_todo.ui.widgets import TaskRow


def rows(layout):
    return [layout.itemAt(i).widget() for i in range(layout.count())
            if isinstance(layout.itemAt(i).widget(), TaskRow)]


def test_task_groups_complete_restore_reopen_delete(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    repo = TodoRepository(tmp_path / "todo.db")
    project = repo.create_project("项目", "目标", "阶段", "下一步")
    first = repo.create_task("第一条", date.today())
    second, _ = repo.add_next_action_to_date(project.id, date.today())
    repo.create_task("昨天", date.today() - timedelta(days=1))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = MainWindow(repo, settings, tray_available=False)
    window.show()
    app.processEvents()
    assert [r.task.id for r in rows(window.tasks_layout)] == [first.id, second.id]
    assert not rows(window.completed_layout)
    rows(window.tasks_layout)[0].checkbox.setChecked(True)
    assert [r.task.id for r in rows(window.tasks_layout)] == [second.id]
    assert [r.task.id for r in rows(window.completed_layout)] == [first.id]
    rows(window.tasks_layout)[0].checkbox.setChecked(True)
    assert not rows(window.tasks_layout)
    assert [r.task.id for r in rows(window.completed_layout)] == [first.id, second.id]
    assert len(repo.recent_completed_tasks(project.id)) == 1
    rows(window.completed_layout)[0].checkbox.setChecked(False)
    assert [r.task.id for r in rows(window.tasks_layout)] == [first.id]
    window.prepare_quit()
    window.close()
    repo.close()
    repo = TodoRepository(tmp_path / "todo.db")
    window = MainWindow(repo, settings, tray_available=False)
    assert [r.task.id for r in rows(window.tasks_layout)] == [first.id]
    assert [r.task.id for r in rows(window.completed_layout)] == [second.id]
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window._delete_task(second.id)
    assert not rows(window.completed_layout)
    window._move_date(-1)
    assert [r.task.title for r in rows(window.tasks_layout)] == ["昨天"]
    assert not rows(window.completed_layout)
    window.prepare_quit()
    window.close()
    repo.close()
