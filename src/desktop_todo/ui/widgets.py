from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPoint, Qt, Signal, QSize
from PySide6.QtGui import QAction, QFont, QMouseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from desktop_todo.models import Project, Task
from desktop_todo.ui.icons import icon_button


class HeaderBar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("headerBar")
        self._drag_offset: QPoint | None = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class WrappingLabel(QLabel):
    edit_requested = Signal()

    def __init__(self, text=""):
        super().__init__(text)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setWordWrap(True)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def minimumSizeHint(self):
        return QSize(0, self.fontMetrics().height())

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_requested.emit()
        super().mouseDoubleClickEvent(event)


class WrappingCard(QFrame):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.layout():
            height = self.layout().totalHeightForWidth(self.width())
            if height > 0:
                self.setMinimumHeight(height)


class TaskRow(WrappingCard):
    changed = Signal()

    def __init__(
        self,
        task: Task,
        *,
        project_name: str | None,
        on_toggle: Callable[[int, bool], None],
        on_rename: Callable[[int, str], None],
        on_delete: Callable[[int], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("taskRow")
        self.task = task
        self._saved_title = task.title
        self._on_toggle = on_toggle
        self._on_rename = on_rename
        self._on_delete = on_delete

        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 6, 7, 6)
        layout.setSpacing(5)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(task.is_completed)
        self.checkbox.setToolTip("恢复任务" if task.is_completed else "标记完成")
        self.checkbox.toggled.connect(self._toggle)
        layout.addWidget(self.checkbox)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        self.editor = WrappingLabel(task.title)
        self.editor.setObjectName("taskEditor")
        self.editor.setToolTip("双击修改任务，或通过右侧菜单编辑")
        self.editor.edit_requested.connect(self._edit)
        text_layout.addWidget(self.editor)
        if project_name:
            badge = WrappingLabel(f"来自：{project_name}")
            badge.setObjectName("secondary")
            text_layout.addWidget(badge)
        layout.addLayout(text_layout, 1)

        more = icon_button("more", "任务操作")
        more.clicked.connect(self._show_menu)
        layout.addWidget(more)
        self._apply_completed_style(task.is_completed)

    def _apply_completed_style(self, completed: bool) -> None:
        font = QFont(self.editor.font())
        font.setStrikeOut(completed)
        self.editor.setFont(font)
        self.editor.setProperty("completed", completed)
        self.editor.style().unpolish(self.editor)
        self.editor.style().polish(self.editor)

    def _toggle(self, completed: bool) -> None:
        self._on_toggle(self.task.id, completed)
        self._apply_completed_style(completed)
        self.checkbox.setToolTip("恢复任务" if completed else "标记完成")

    def _rename(self) -> None:
        title = self.editor.text().strip()
        if not title:
            self.editor.setText(self._saved_title)
            return
        if title == self._saved_title:
            return
        self._on_rename(self.task.id, title)
        self._saved_title = title

    def _edit(self):
        from desktop_todo.ui.dialogs import TaskDialog
        dialog = TaskDialog(self.window(), self.task.task_date)
        dialog.editor.setText(self._saved_title)
        dialog.editor.selectAll()
        # Reuse the task form without changing the stored date.
        for label in dialog.findChildren(QLabel):
            if label.objectName() == "sectionTitle":
                label.setText("修改任务")
        from PySide6.QtWidgets import QDialogButtonBox
        dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save).setText("保存")
        if dialog.exec() and dialog.textValue().strip():
            self.editor.setText(dialog.textValue().strip())
            self._rename()
            self.updateGeometry()

    def _show_menu(self) -> None:
        menu = QMenu(self)
        edit_action = menu.addAction("修改任务")
        edit_action.triggered.connect(self._edit)
        delete_action = QAction("删除任务", self)
        delete_action.triggered.connect(lambda: self._on_delete(self.task.id))
        menu.addAction(delete_action)
        menu.exec(self.mapToGlobal(self.rect().bottomRight()))


class ProjectCard(WrappingCard):
    edit_requested = Signal(int)
    archive_requested = Signal(int)
    add_today_requested = Signal(int)

    def __init__(
        self,
        project: Project,
        recent_tasks: list[Task],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("projectCard")
        self.project = project
        root = QVBoxLayout(self)
        root.setContentsMargins(11, 10, 9, 10)
        root.setSpacing(6)

        top = QHBoxLayout()
        name = WrappingLabel(project.name)
        name.setObjectName("projectName")
        name.setWordWrap(True)
        top.addWidget(name, 1)
        more = icon_button("more", "项目操作")
        more.clicked.connect(self._show_menu)
        top.addWidget(more)
        root.addLayout(top)

        if project.goal:
            goal = WrappingLabel(project.goal)
            goal.setObjectName("projectMeta")
            goal.setWordWrap(True)
            root.addWidget(goal)
        if project.current_stage:
            stage = WrappingLabel(f"当前阶段：{project.current_stage}")
            stage.setObjectName("projectMeta")
            stage.setWordWrap(True)
            root.addWidget(stage)

        action_row = QHBoxLayout()
        action = WrappingLabel(
            f"下一步：{project.next_action}" if project.next_action else "还没有设置下一步行动"
        )
        action.setWordWrap(True)
        action_row.addWidget(action, 1)
        add_button = icon_button("calendar", "将下一步行动加入今天")
        add_button.setEnabled(bool(project.next_action.strip()))
        add_button.clicked.connect(
            lambda: self.add_today_requested.emit(self.project.id)
        )
        action_row.addWidget(add_button)
        root.addLayout(action_row)

        if recent_tasks:
            recent_text = "最近完成：" + " · ".join(task.title for task in recent_tasks)
            recent = WrappingLabel(recent_text)
            recent.setObjectName("recentLabel")
            recent.setWordWrap(True)
            root.addWidget(recent)

    def _show_menu(self) -> None:
        menu = QMenu(self)
        edit_action = QAction("编辑项目", self)
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.project.id))
        archive_action = QAction("归档项目", self)
        archive_action.triggered.connect(
            lambda: self.archive_requested.emit(self.project.id)
        )
        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(archive_action)
        menu.exec(self.mapToGlobal(self.rect().bottomRight()))
