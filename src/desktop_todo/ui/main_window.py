from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import QEvent, QSettings, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QCloseEvent, QGuiApplication, QShowEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QInputDialog,
    QStackedWidget,
    QButtonGroup,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QVBoxLayout,
    QWidget,
)

from desktop_todo.models import Project
from desktop_todo.repository import DatabaseError, TodoRepository
from desktop_todo.ui.dialogs import ProjectDialog, TaskDialog
from desktop_todo.ui.calendar_dialog import CalendarDialog
from desktop_todo.ui.phone_page import PhonePage
from desktop_todo.ui.widgets import HeaderBar, ProjectCard, TaskRow
from desktop_todo.ui.icons import icon, icon_button
from desktop_todo.ui.appearance import AppearanceDialog, GlassCard
from desktop_todo.ui.glass_style import theme_style, dark_color


WEEKDAYS = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")


class MainWindow(QWidget):
    pin_changed = Signal(bool)
    hidden_to_tray = Signal()

    def __init__(
        self,
        repository: TodoRepository,
        settings: QSettings,
        *,
        tray_available: bool,
    ) -> None:
        super().__init__()
        self.repository = repository
        self.settings = settings
        self.tray_available = tray_available
        self._allow_quit = False
        self._has_saved_geometry = False
        self._selected_date = date.today()
        self._last_wall_date = date.today()
        self._project_names: dict[int, str] = {}

        self.setWindowTitle("桌面清单")
        self.setMinimumSize(330, 400)
        self.resize(360, 560)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self._build_ui()
        self.apply_appearance(
            self.settings.value("appearance/color", "#FFFFFF", type=str),
            self.settings.value("appearance/opacity", 88, type=int),
        )

        self._pin_enabled = self.settings.value("window/pinned", True, type=bool)
        self.pin_button.setChecked(self._pin_enabled)
        self._apply_pin_flag(self._pin_enabled, show_after=False)
        geometry = self.settings.value("window/geometry")
        if geometry is not None:
            self._has_saved_geometry = self.restoreGeometry(geometry)

        self.day_timer = QTimer(self)
        self.day_timer.setInterval(30_000)
        self.day_timer.timeout.connect(self._check_day_change)
        self.day_timer.start()
        self.refresh_all()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(7, 7, 7, 7)
        card = GlassCard()
        self.glass_card = card
        outer.addWidget(card)
        root = QVBoxLayout(card)
        root.setContentsMargins(16, 12, 12, 8)
        root.setSpacing(12)

        header = HeaderBar()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(2, 0, 0, 0)
        header_layout.setSpacing(5)
        logo = QLabel()
        logo.setPixmap(icon("check", "#9585D9").pixmap(24, 24))
        logo.setToolTip("桌面清单 · 拖动顶部移动窗口")
        logo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        header_layout.addWidget(logo)
        header_layout.addStretch(1)
        self.date_label = QLabel()
        self.date_label.setObjectName("dateLabel")

        previous_button = self._icon_button("previous", "前一天")
        previous_button.clicked.connect(lambda: self._move_date(-1))
        next_button = self._icon_button("next", "后一天")
        next_button.clicked.connect(lambda: self._move_date(1))
        today_button = self._icon_button("calendar", "打开月历 · 选择日期")
        today_button.clicked.connect(self._show_calendar)
        self.pin_button = self._icon_button("pin", "始终置顶")
        self.pin_button.setCheckable(True)
        self.pin_button.toggled.connect(self.set_pinned)
        appearance_button = self._icon_button("palette", "外观：颜色与透明度")
        appearance_button.clicked.connect(self._show_appearance)
        minimize_button = self._icon_button("minus", "最小化")
        minimize_button.clicked.connect(self.showMinimized)
        close_button = self._icon_button("close", "隐藏到托盘")
        close_button.clicked.connect(self.close)
        for button in (
            appearance_button,
            self.pin_button,
            minimize_button,
            close_button,
        ):
            header_layout.addWidget(button)
        root.addWidget(header)

        tabs = QHBoxLayout()
        self.page_buttons = QButtonGroup(self)
        for index, title in enumerate(("今日任务", "长期项目", "少看手机")):
            button = QPushButton(title)
            button.setStyleSheet("padding: 7px 4px;")
            button.setCheckable(True)
            button.setChecked(index == 0)
            self.page_buttons.addButton(button, index)
            tabs.addWidget(button)
        root.addLayout(tabs)
        self.pages = QStackedWidget()
        self.page_buttons.idClicked.connect(self.pages.setCurrentIndex)
        root.addWidget(self.pages, 1)

        task_page = QWidget()
        task_page_layout = QVBoxLayout(task_page)
        task_page_layout.setContentsMargins(0, 0, 0, 0)
        self.pages.addWidget(task_page)
        self.date_bar = QWidget()
        date_row = QHBoxLayout(self.date_bar)
        date_row.setContentsMargins(0, 0, 0, 0)
        date_row.setSpacing(3)
        date_row.addWidget(self.date_label, 1)
        for button in (previous_button, today_button, next_button):
            date_row.addWidget(button)
        root.insertWidget(1, self.date_bar)

        scroll = QScrollArea()
        self.task_scroll = scroll
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(1, 2, 5, 2)
        self.body_layout.setSpacing(8)

        add_row = QHBoxLayout()
        self.task_title = QLabel("今日任务")
        self.task_title.setObjectName("sectionTitle")
        add_row.addWidget(self.task_title, 1)
        add_task_button = self._icon_button("plus", "添加任务")
        self.add_task_button = add_task_button
        add_task_button.clicked.connect(self._add_task)
        add_row.addWidget(add_task_button)
        task_page_layout.addLayout(add_row)

        self.pending_title = QLabel("未完成 · 0")
        self.pending_title.setObjectName("sectionTitle")
        self.body_layout.addWidget(self.pending_title)
        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(6)
        self.body_layout.addWidget(self.tasks_container)
        self.completed_title = QLabel("已完成 · 0")
        self.completed_title.setObjectName("sectionTitle")
        self.body_layout.addWidget(self.completed_title)
        self.completed_container = QWidget()
        self.completed_layout = QVBoxLayout(self.completed_container)
        self.completed_layout.setContentsMargins(0, 0, 0, 0)
        self.completed_layout.setSpacing(6)
        self.body_layout.addWidget(self.completed_container)
        self.body_layout.addStretch(1)
        scroll.setWidget(body)
        task_page_layout.addWidget(scroll, 1)

        project_scroll = QScrollArea()
        project_scroll.setWidgetResizable(True)
        project_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        project_body = QWidget()
        project_layout = QVBoxLayout(project_body)
        project_layout.setContentsMargins(1, 2, 5, 2)
        project_layout.setSpacing(8)

        projects_header = QHBoxLayout()
        projects_title = QLabel("长期项目")
        projects_title.setObjectName("sectionTitle")
        projects_header.addWidget(projects_title, 1)
        add_project_button = self._icon_button("plus", "新建长期项目")
        add_project_button.clicked.connect(self._create_project)
        projects_header.addWidget(add_project_button)
        project_layout.addLayout(projects_header)

        self.projects_container = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_container)
        self.projects_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_layout.setSpacing(7)
        project_layout.addWidget(self.projects_container)
        project_layout.addStretch(1)
        project_scroll.setWidget(project_body)
        self.pages.addWidget(project_scroll)
        self.phone_page = PhonePage(self, self.settings)
        self.pages.addWidget(self.phone_page)
        self.pages.currentChanged.connect(lambda index: self.date_bar.setVisible(index != 2))

        footer = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        footer.addWidget(self.status_label, 1)
        footer.addWidget(QSizeGrip(self), 0, Qt.AlignmentFlag.AlignBottom)
        root.addLayout(footer)

        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(lambda: self.status_label.setText(""))

    @staticmethod
    def _icon_button(text: str, tooltip: str) -> QPushButton:
        return icon_button(text, tooltip)

    def apply_appearance(self, color: str, opacity: int) -> None:
        color = color if QColor(color).isValid() else "#FFFFFF"
        opacity = max(40, min(100, opacity))
        self.glass_card.color = QColor(color)
        self.glass_card.opacity = opacity
        self.setStyleSheet(theme_style(color))
        self.glass_card.update()
        self.settings.setValue("appearance/color", color)
        self.settings.setValue("appearance/opacity", opacity)
        self.settings.sync()
        self._refresh_icons()

    def _refresh_icons(self):
        color = "#DCE1F2" if dark_color(self.glass_card.color.name()) else "#657087"
        for button in self.findChildren(QPushButton):
            symbol = button.property("symbol")
            if symbol:
                button.setIcon(icon(symbol, "#9985D9" if button.isChecked() else color))

    def _show_appearance(self):
        dialog = AppearanceDialog(self, self.glass_card.color.name(), self.glass_card.opacity)
        dialog.appearance_changed.connect(self.apply_appearance)
        dialog.exec()

    def refresh_all(self) -> None:
        self._refresh_date_label()
        self._refresh_projects()
        self._refresh_tasks()

    def _refresh_date_label(self) -> None:
        today = date.today()
        prefix = "今天 · " if self._selected_date == today else ""
        self.date_label.setText(
            f"{prefix}{self._selected_date.month}月{self._selected_date.day}日 · "
            f"{WEEKDAYS[self._selected_date.weekday()]}"
        )
        self.task_title.setText(
            "今日任务"
            if self._selected_date == today
            else f"{self._selected_date.month}月{self._selected_date.day}日的任务"
        )

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()

    def _refresh_tasks(self) -> None:
        self._clear_layout(self.tasks_layout)
        self._clear_layout(self.completed_layout)
        try:
            tasks = self.repository.list_tasks(self._selected_date)
        except Exception as exc:
            self._show_error("读取任务失败", exc)
            return
        completed_count = sum(task.is_completed for task in tasks)
        self.pending_title.setText(f"未完成 · {len(tasks) - completed_count}")
        self.completed_title.setText(f"已完成 · {completed_count}")
        for task in tasks:
            row = TaskRow(
                task,
                project_name=self._project_names.get(task.project_id or -1),
                on_toggle=self._toggle_task,
                on_rename=self._rename_task,
                on_delete=self._delete_task,
            )
            target = self.completed_layout if task.is_completed else self.tasks_layout
            target.addWidget(row)
        for layout, message in (
            (self.tasks_layout, "这一天还没有任务。" if not tasks else "当天任务已全部完成。"),
            (self.completed_layout, "还没有已完成的任务。"),
        ):
            if not layout.count():
                empty = QLabel(message)
                empty.setObjectName("emptyLabel")
                empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(empty)
        self._refresh_icons()

    def _refresh_projects(self) -> None:
        self._clear_layout(self.projects_layout)
        try:
            projects = self.repository.list_projects()
        except Exception as exc:
            self._show_error("读取长期项目失败", exc)
            return
        self._project_names = {project.id: project.name for project in projects}
        if not projects:
            empty = QLabel("一个目标，从下一步开始。")
            empty.setObjectName("emptyLabel")
            empty.setWordWrap(True)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.projects_layout.addWidget(empty)
            return
        for project in projects:
            recent = self.repository.recent_completed_tasks(project.id, limit=3)
            card = ProjectCard(project, recent)
            card.edit_requested.connect(self._edit_project)
            card.archive_requested.connect(self._archive_project)
            card.add_today_requested.connect(self._add_project_action_today)
            self.projects_layout.addWidget(card)
        self._refresh_icons()

    def _add_task(self) -> None:
        target_date = self._selected_date
        dialog = TaskDialog(self, target_date)
        if not dialog.exec():
            return
        title = dialog.textValue().strip()
        if not title:
            return
        try:
            self.repository.create_task(title, target_date)
        except Exception as exc:
            self._show_error("添加任务失败", exc)
            return
        self._refresh_tasks()
        self._show_status("任务已保存")

    def _toggle_task(self, task_id: int, completed: bool) -> None:
        try:
            task = self.repository.set_task_completed(task_id, completed)
        except Exception as exc:
            self._show_error("更新任务失败", exc)
            self._refresh_tasks()
            return
        self._show_status("已完成" if task.is_completed else "已恢复")
        self._refresh_tasks()
        if task.project_id is not None:
            self._refresh_projects()

    def _rename_task(self, task_id: int, title: str) -> None:
        try:
            self.repository.rename_task(task_id, title)
        except Exception as exc:
            self._show_error("修改任务失败", exc)
            self._refresh_tasks()
            return
        self._show_status("修改已保存")

    def _delete_task(self, task_id: int) -> None:
        if QMessageBox.question(
            self,
            "删除任务",
            "确定删除这条任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            task = self.repository.get_task(task_id)
            self.repository.delete_task(task_id)
        except Exception as exc:
            self._show_error("删除任务失败", exc)
            return
        self._refresh_tasks()
        if task.project_id is not None:
            self._refresh_projects()
        self._show_status("任务已删除")

    def _create_project(self) -> None:
        dialog = ProjectDialog(self)
        if not dialog.exec():
            return
        try:
            self.repository.create_project(**dialog.values())
        except Exception as exc:
            self._show_error("新建项目失败", exc)
            return
        self._refresh_projects()
        self._show_status("长期项目已保存")

    def _edit_project(self, project_id: int) -> None:
        try:
            project = self.repository.get_project(project_id)
        except Exception as exc:
            self._show_error("读取项目失败", exc)
            return
        dialog = ProjectDialog(self, project)
        if not dialog.exec():
            return
        try:
            self.repository.update_project(project_id, **dialog.values())
        except Exception as exc:
            self._show_error("更新项目失败", exc)
            return
        self._refresh_projects()
        self._refresh_tasks()
        self._show_status("项目修改已保存")

    def _archive_project(self, project_id: int) -> None:
        if QMessageBox.question(
            self,
            "归档项目",
            "归档后项目会从主界面隐藏，历史任务仍会保留。确定归档吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            self.repository.set_project_archived(project_id, True)
        except Exception as exc:
            self._show_error("归档项目失败", exc)
            return
        self._refresh_projects()
        self._refresh_tasks()
        self._show_status("项目已归档")

    def _add_project_action_today(self, project_id: int) -> None:
        try:
            _, created = self.repository.add_next_action_to_date(project_id, date.today())
        except Exception as exc:
            self._show_error("加入今天失败", exc)
            return
        if self._selected_date == date.today():
            self._refresh_tasks()
        self._show_status("已加入今天" if created else "这一步今天已经加入过")

    def _move_date(self, days: int) -> None:
        self._selected_date += timedelta(days=days)
        self._refresh_date_label()
        self._refresh_tasks()

    def _go_today(self) -> None:
        self._selected_date = date.today()
        self._refresh_date_label()
        self._refresh_tasks()

    def _show_calendar(self) -> None:
        try:
            dialog = CalendarDialog(self, self.repository, self._selected_date)
            if dialog.exec():
                self._selected_date = dialog.chosen_date
                self._refresh_date_label()
                self._refresh_tasks()
        except Exception as exc:
            self._show_error("读取日历失败", exc)

    def _check_day_change(self) -> None:
        current = date.today()
        if current == self._last_wall_date:
            return
        if self._selected_date == self._last_wall_date:
            self._selected_date = current
            self._refresh_date_label()
            self._refresh_tasks()
        self._last_wall_date = current

    def set_pinned(self, enabled: bool) -> None:
        self._pin_enabled = enabled
        self.pin_button.blockSignals(True)
        self.pin_button.setChecked(enabled)
        self.pin_button.blockSignals(False)
        self._refresh_icons()
        self.settings.setValue("window/pinned", enabled)
        self._apply_pin_flag(enabled, show_after=self.isVisible())
        self.pin_changed.emit(enabled)
        self._show_status("已置顶" if enabled else "已取消置顶")

    def _apply_pin_flag(self, enabled: bool, *, show_after: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        if show_after:
            self.show()
            self.raise_()
            self.activateWindow()

    def is_pinned(self) -> bool:
        return self._pin_enabled

    def show_and_activate(self) -> None:
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.ensure_visible()
        self.raise_()
        self.activateWindow()

    def toggle_visible(self) -> None:
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.show_and_activate()

    def prepare_quit(self) -> None:
        self._allow_quit = True
        self._save_window_state()

    def _save_window_state(self) -> None:
        if not self.isMinimized():
            self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.sync()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._save_window_state()
        if self._allow_quit or not self.tray_available:
            event.accept()
            return
        event.ignore()
        self.hide()
        self.hidden_to_tray.emit()

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            self._save_window_state()
        super().changeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self.ensure_visible)

    def ensure_visible(self) -> None:
        screens = QGuiApplication.screens()
        if not screens:
            return
        frame = self.frameGeometry()
        if not self._has_saved_geometry:
            available = QGuiApplication.primaryScreen().availableGeometry()
            self.move(available.right() - self.width() - 24, available.top() + 48)
            self._has_saved_geometry = True
            return
        if any(screen.availableGeometry().intersects(frame) for screen in screens):
            return
        available = QGuiApplication.primaryScreen().availableGeometry()
        self.move(available.right() - self.width() - 24, available.top() + 48)

    def _show_status(self, message: str) -> None:
        self.status_label.setText(message)
        self.status_timer.start(2600)

    def _show_error(self, title: str, error: Exception) -> None:
        message = str(error)
        if isinstance(error, DatabaseError):
            message += "\n\n数据库未被覆盖，请检查提示后重试。"
        QMessageBox.critical(self, title, message)
