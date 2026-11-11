from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from desktop_todo.repository import TodoRepository
from desktop_todo.ui.main_window import MainWindow


def test_phone_page_navigation_and_menu_persistence(tmp_path):
    app = QApplication.instance() or QApplication([])
    repo = TodoRepository(tmp_path / "todo.db")
    path = str(tmp_path / "settings.ini")
    window = MainWindow(repo, QSettings(path, QSettings.Format.IniFormat), tray_available=False)
    window.resize(330, 400)
    window.show()
    window.page_buttons.button(2).click()
    for _ in range(10):
        app.processEvents()
    assert window.pages.currentWidget() == window.phone_page
    assert not window.date_bar.isVisible()
    assert window.phone_page.horizontalScrollBar().maximum() == 0
    window.phone_page.save_menu("走一走\n读两页书")
    assert "读两页书" in window.phone_page.menu_label.text()
    window.page_buttons.button(0).click()
    assert window.date_bar.isVisible()
    window.prepare_quit()
    window.close()
    reopened = MainWindow(repo, QSettings(path, QSettings.Format.IniFormat), tray_available=False)
    assert reopened.phone_page.menu_text() == "走一走\n读两页书"
    reopened.phone_page.save_menu("")
    assert "还没有" in reopened.phone_page.menu_label.text()
    reopened.prepare_quit()
    reopened.close()
    repo.close()
