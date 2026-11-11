from __future__ import annotations

import argparse
import sys

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from desktop_todo.paths import asset_path, database_path
from desktop_todo.repository import DatabaseError, TodoRepository
from desktop_todo.single_instance import SingleInstance
from desktop_todo.ui.main_window import MainWindow
from desktop_todo.ui.glass_style import theme_style
from desktop_todo.windows import StartupManager


def _parse_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="桌面清单")
    parser.add_argument(
        "--autostart", action="store_true", help="由 Windows 开机启动项启动"
    )
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    _parse_arguments(sys.argv[1:] if arguments is None else arguments)

    app = QApplication(sys.argv if arguments is None else [sys.argv[0], *arguments])
    app.setApplicationName("桌面清单")
    app.setApplicationDisplayName("桌面清单")
    app.setOrganizationName("DesktopTodo")
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(theme_style())

    icon = QIcon(str(asset_path("icon.svg")))
    app.setWindowIcon(icon)

    single_instance = SingleInstance()
    if not single_instance.acquire_or_notify():
        return 0

    try:
        repository = TodoRepository(database_path())
    except DatabaseError as exc:
        QMessageBox.critical(
            None,
            "桌面清单无法启动",
            f"{exc}\n\n程序没有覆盖现有数据库。",
        )
        return 1

    startup_manager: StartupManager | None = None
    try:
        startup_manager = StartupManager()
        startup_manager.refresh_enabled_command()
    except OSError:
        startup_manager = None

    tray_available = QSystemTrayIcon.isSystemTrayAvailable()
    settings = QSettings()
    window = MainWindow(
        repository,
        settings,
        tray_available=tray_available,
    )

    tray: QSystemTrayIcon | None = None
    if tray_available:
        tray = QSystemTrayIcon(icon, app)
        tray.setToolTip("桌面清单")
        menu = QMenu()
        show_action = QAction("显示/隐藏", menu)
        show_action.triggered.connect(window.toggle_visible)
        pin_action = QAction("始终置顶", menu)
        pin_action.setCheckable(True)
        pin_action.setChecked(window.is_pinned())
        pin_action.toggled.connect(window.set_pinned)
        window.pin_changed.connect(pin_action.setChecked)
        startup_action = QAction("开机启动", menu)
        startup_action.setCheckable(True)
        startup_action.setEnabled(startup_manager is not None)
        if sys.platform == "darwin":
            startup_action.setText("登录时启动（请在系统设置中添加）")
        if startup_manager is not None:
            startup_action.setChecked(startup_manager.is_enabled())

            def change_startup(enabled: bool) -> None:
                try:
                    startup_manager.set_enabled(enabled)
                except OSError as exc:
                    startup_action.blockSignals(True)
                    startup_action.setChecked(not enabled)
                    startup_action.blockSignals(False)
                    QMessageBox.critical(window, "开机启动设置失败", str(exc))

            startup_action.toggled.connect(change_startup)

        exit_action = QAction("退出", menu)

        def quit_application() -> None:
            window.prepare_quit()
            app.quit()

        exit_action.triggered.connect(quit_application)
        menu.addAction(show_action)
        menu.addAction(pin_action)
        menu.addAction(startup_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        tray.setContextMenu(menu)
        tray.activated.connect(
            lambda reason: window.show_and_activate()
            if reason
            in (
                QSystemTrayIcon.ActivationReason.Trigger,
                QSystemTrayIcon.ActivationReason.DoubleClick,
            )
            else None
        )
        tray.show()

        shown_tray_notice = False

        def notify_hidden() -> None:
            nonlocal shown_tray_notice
            if shown_tray_notice or tray is None:
                return
            shown_tray_notice = True
            tray.showMessage("桌面清单仍在运行", "可从系统托盘重新打开或彻底退出。")

        window.hidden_to_tray.connect(notify_hidden)
    else:
        app.setQuitOnLastWindowClosed(True)

    single_instance.activation_requested.connect(window.show_and_activate)
    app.aboutToQuit.connect(repository.close)
    window.show_and_activate()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
