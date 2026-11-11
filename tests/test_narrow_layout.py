from datetime import date

from PySide6.QtCore import QSettings, QPoint
from PySide6.QtWidgets import QApplication

from desktop_todo.repository import TodoRepository
from desktop_todo.ui.main_window import MainWindow
from desktop_todo.ui.widgets import TaskRow


def test_long_tasks_fit_narrow_window(tmp_path):
    app = QApplication.instance() or QApplication([])
    repo = TodoRepository(tmp_path / "todo.db")
    project = repo.create_project("很长的项目名称" * 15, "目标" * 100, "阶段", "下一步")
    title = "检查 ANSYS 可用情况；记录版本及待确认项。" * 10
    task = repo.create_task(title, date.today(), project_id=project.id)
    repo.create_task("ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 10, date.today())
    window = MainWindow(repo, QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat), tray_available=False)
    window.resize(330, 400)
    window.show()
    for _ in range(5):
        app.processEvents()
    viewport = window.task_scroll.viewport()
    assert window.task_scroll.widget().width() <= viewport.width()
    assert window.task_scroll.horizontalScrollBar().maximum() == 0
    button_pos = window.add_task_button.mapTo(window, QPoint(0, 0))
    assert button_pos.x() + window.add_task_button.width() < window.width()
    rows = window.tasks_container.findChildren(TaskRow)
    assert rows[0].editor.text() == title
    for row in rows:
        assert row.editor.height() >= row.editor.heightForWidth(row.editor.width())
        assert row.editor.height() > row.editor.fontMetrics().height()
        assert row.height() >= row.layout().totalHeightForWidth(row.width())
    assert rows[0].geometry().bottom() < rows[1].geometry().top()
    rows[0].checkbox.setChecked(True)
    assert repo.get_task(task.id).is_completed
    assert rows[0].editor.font().strikeOut()
    window.task_scroll.verticalScrollBar().setValue(window.task_scroll.verticalScrollBar().maximum())
    assert window.add_task_button.isVisible()
    window.resize(520, 620)
    for _ in range(5):
        app.processEvents()
    assert window.task_scroll.horizontalScrollBar().maximum() == 0
    window.prepare_quit()
    window.close()
    repo.close()
