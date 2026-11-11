from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop_todo.models import Project
from desktop_todo.ui.popup import PopupDialog


class ProjectDialog(PopupDialog):
    def __init__(self, parent: QWidget, project: Project | None = None) -> None:
        super().__init__(parent, text_input=True)
        self.setWindowTitle("编辑长期项目" if project else "新建长期项目")
        self.setMinimumWidth(420)

        root = self.content
        title = QLabel(self.windowTitle())
        title.setObjectName("sectionTitle")
        root.addWidget(title)
        hint = QLabel("长期项目只保留一个明确的下一步行动。")
        hint.setObjectName("secondary")
        hint.setWordWrap(True)
        root.addWidget(hint)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignTop)
        self.name_edit = QLineEdit(project.name if project else "")
        self.name_edit.setMaxLength(120)
        self.name_edit.setPlaceholderText("例如：机器人自动回充")
        self.goal_edit = QTextEdit(project.goal if project else "")
        self.goal_edit.setPlaceholderText("这个项目最终要达到什么结果？")
        self.goal_edit.setFixedHeight(72)
        self.stage_edit = QLineEdit(project.current_stage if project else "")
        self.stage_edit.setMaxLength(300)
        self.stage_edit.setPlaceholderText("例如：红外结构验证")
        self.action_edit = QLineEdit(project.next_action if project else "")
        self.action_edit.setMaxLength(300)
        self.action_edit.setPlaceholderText("例如：完成红外传感器建模")
        form.addRow("项目名称 *", self.name_edit)
        form.addRow("目标", self.goal_edit)
        form.addRow("当前阶段", self.stage_edit)
        form.addRow("下一步行动", self.action_edit)
        root.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _validate_and_accept(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "无法保存", "项目名称不能为空。")
            self.name_edit.setFocus()
            return
        self.accept()

    def values(self) -> dict[str, str]:
        return {
            "name": self.name_edit.text().strip(),
            "goal": self.goal_edit.toPlainText().strip(),
            "current_stage": self.stage_edit.text().strip(),
            "next_action": self.action_edit.text().strip(),
        }


class TaskDialog(PopupDialog):
    def __init__(self, parent, task_date):
        super().__init__(parent, text_input=True)
        self.setFixedWidth(320)
        title = QLabel("添加任务")
        title.setObjectName("sectionTitle")
        self.content.addWidget(title)
        hint = QLabel(f"{task_date:%Y年%m月%d日}")
        hint.setObjectName("secondary")
        self.content.addWidget(hint)
        self.editor = QLineEdit()
        self.editor.setMaxLength(300)
        self.editor.setPlaceholderText("准备做些什么？")
        self.content.addWidget(self.editor)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        save = buttons.button(QDialogButtonBox.StandardButton.Save)
        save.setText("添加")
        save.setEnabled(False)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        self.editor.textChanged.connect(lambda text: save.setEnabled(bool(text.strip())))
        self.editor.returnPressed.connect(lambda: self.accept() if self.editor.text().strip() else None)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.content.addWidget(buttons)
        self.editor.setFocus()

    def textValue(self):
        return self.editor.text()
