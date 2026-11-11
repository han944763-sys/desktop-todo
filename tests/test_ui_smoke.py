from __future__ import annotations

import os
from datetime import date

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from desktop_todo.repository import TodoRepository  # noqa: E402
from desktop_todo.ui.main_window import MainWindow  # noqa: E402


def test_main_window_renders_tasks_and_projects(tmp_path):
    app = QApplication.instance() or QApplication([])
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    repository = TodoRepository(tmp_path / "todo.db")
    repository.create_task("界面任务", date.today())
    repository.create_project("长期项目", "目标", "阶段", "下一步")

    window = MainWindow(repository, settings, tray_available=False)
    window.show()
    app.processEvents()

    assert window.windowTitle() == "桌面清单"
    assert window.tasks_layout.count() == 1
    assert window.projects_layout.count() == 1
    assert window.is_pinned() is True

    window._has_saved_geometry = True
    window.move(-10000, -10000)
    window.ensure_visible()
    assert any(
        screen.availableGeometry().intersects(window.frameGeometry())
        for screen in app.screens()
    )

    window.prepare_quit()
    window.close()
    repository.close()


def test_pages_calendar_and_task_dialog(tmp_path, monkeypatch):
    from datetime import timedelta
    from PySide6.QtCore import QDate
    from PySide6.QtWidgets import QLineEdit
    from desktop_todo.ui.dialogs import TaskDialog
    from desktop_todo.ui.calendar_dialog import CalendarDialog

    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "pages.ini"), QSettings.Format.IniFormat)
    repository = TodoRepository(tmp_path / "todo.db")
    yesterday = date.today() - timedelta(days=1)
    task = repository.create_task("昨天的任务", yesterday)
    repository.set_task_completed(task.id, True)
    window = MainWindow(repository, settings, tray_available=False)
    window.show()
    app.processEvents()
    assert window.pages.count() == 3
    assert window.date_bar.geometry().bottom() < window.page_buttons.button(0).geometry().top()
    assert not window.findChildren(QLineEdit)  # No permanent add field on empty today.
    window.page_buttons.button(1).click()
    assert window.pages.currentIndex() == 1
    assert window.date_bar.isVisible()
    window.page_buttons.button(0).click()
    assert window.date_bar.isVisible()

    dialog = CalendarDialog(window, repository, date.today())
    assert yesterday in dialog.calendar.marked_dates
    assert date.today() not in dialog.calendar.marked_dates
    dialog.calendar.setCurrentPage(2028, 2)
    assert not dialog.calendar.marked_dates
    dialog.choose(QDate(yesterday.year, yesterday.month, yesterday.day))
    assert dialog.chosen_date == yesterday
    monkeypatch.setattr(CalendarDialog, "exec", lambda self: (self.choose(QDate(yesterday.year, yesterday.month, yesterday.day)) or 1))
    window._show_calendar()
    assert window._selected_date == yesterday
    assert window.tasks_layout.count() == 1
    monkeypatch.setattr(TaskDialog, "exec", lambda self: 1)
    monkeypatch.setattr(TaskDialog, "textValue", lambda self: " 新添加 ")
    window._add_task()
    assert [t.title for t in repository.list_tasks(yesterday)] == ["昨天的任务", "新添加"]
    monkeypatch.setattr(TaskDialog, "exec", lambda self: 0)
    window._add_task()
    assert len(repository.list_tasks(yesterday)) == 2
    window._go_today()
    assert window._selected_date == date.today()
    assert not repository.list_tasks(date.today())
    repository.delete_task(task.id)
    assert yesterday in repository.task_dates(yesterday, yesterday)
    repository.delete_task(repository.list_tasks(yesterday)[0].id)
    assert not repository.task_dates(yesterday, yesterday)
    window.prepare_quit()
    window.close()
    repository.close()


def test_popups_dismiss_without_saving(tmp_path):
    from PySide6.QtCore import Qt, QPoint
    from PySide6.QtTest import QTest
    from desktop_todo.ui.dialogs import TaskDialog, ProjectDialog
    from desktop_todo.ui.calendar_dialog import CalendarDialog
    from desktop_todo.ui.appearance import AppearanceDialog
    app = QApplication.instance() or QApplication([])
    repository = TodoRepository(tmp_path / "popup.db")
    window = MainWindow(repository, QSettings(str(tmp_path / "popup.ini"), QSettings.Format.IniFormat), tray_available=False)
    window.show()
    for dialog in (TaskDialog(window, date.today()), ProjectDialog(window), CalendarDialog(window, repository, date.today()), AppearanceDialog(window, "#FFFFFF", 88)):
        dialog.show()
        app.processEvents()
        assert dialog.windowType() == (Qt.WindowType.Dialog if dialog.text_input else Qt.WindowType.Popup)
        assert not dialog.mask().contains(QPoint(0, 0))
        assert dialog.mask().contains(dialog.rect().center())
        QTest.keyClick(dialog, Qt.Key.Key_Escape)
        assert not dialog.isVisible()
        assert dialog.result() == 0
        dialog.show()
        app.processEvents()
        QTest.mouseClick(dialog, Qt.MouseButton.LeftButton, pos=QPoint(-8, -8))
        assert not dialog.isVisible()
        assert dialog.result() == 0
    assert not repository.list_tasks(date.today())
    assert not repository.list_projects()
    window.prepare_quit()
    window.close()
    repository.close()


def test_calendar_year_month_picker(tmp_path, monkeypatch):
    from desktop_todo.ui.calendar_dialog import CalendarDialog, YearMonthDialog
    from PySide6.QtCore import QPoint
    app = QApplication.instance() or QApplication([])
    repository = TodoRepository(tmp_path / "months.db")
    window = MainWindow(repository, QSettings(str(tmp_path / "months.ini"), QSettings.Format.IniFormat), tray_available=False)
    dialog = CalendarDialog(window, repository, date.today())
    dialog.show()
    app.processEvents()
    assert dialog.width() <= 310
    picker = YearMonthDialog(dialog, 2026, 9)
    assert picker.year.value() == 2026
    assert picker.months.checkedId() == 9
    def pick(self):
        self.year.setValue(2028)
        self.months.button(2).click()
        return 1
    monkeypatch.setattr(YearMonthDialog, "exec", pick)
    dialog.month_label.click()
    assert (dialog.calendar.yearShown(), dialog.calendar.monthShown()) == (2028, 2)
    assert dialog.chosen_date == date.today()
    monkeypatch.setattr(YearMonthDialog, "exec", lambda self: 0)
    dialog.month_label.click()
    assert dialog.calendar.monthShown() == 2
    dialog.close()
    window.prepare_quit()
    window.close()
    repository.close()


def test_appearance_live_change_and_reopen(tmp_path):
    from desktop_todo.ui.appearance import AppearanceDialog
    from PySide6.QtWidgets import QPushButton

    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "appearance.ini"), QSettings.Format.IniFormat)
    repository = TodoRepository(tmp_path / "todo.db")
    window = MainWindow(repository, settings, tray_available=False)
    dialog = AppearanceDialog(window, "#FFFFFF", 88)
    dialog.appearance_changed.connect(window.apply_appearance)
    dialog.set_color("#252B3B")
    dialog.slider.setValue(65)
    app.processEvents()
    assert window.glass_card.color.name() == "#252b3b"
    assert window.glass_card.opacity == 65
    assert window.windowOpacity() == 1.0  # Transparency applies only to the background.
    for button in window.findChildren(QPushButton):
        if button.property("symbol"):
            assert button.text() == ""
            assert not button.icon().isNull()
            assert button.accessibleName()
    dialog.close()
    window.prepare_quit()
    window.close()
    reopened = MainWindow(repository, settings, tray_available=False)
    assert reopened.glass_card.color.name() == "#252b3b"
    assert reopened.glass_card.opacity == 65
    reopened.prepare_quit()
    reopened.close()
    repository.close()
