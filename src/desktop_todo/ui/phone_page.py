from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QPushButton, QTextEdit, QDialogButtonBox
from desktop_todo.ui.widgets import WrappingCard, WrappingLabel
from desktop_todo.ui.popup import PopupDialog


DEFAULT_MENU = "喝水，走动一下\n看窗外，让眼睛歇一会儿\n读两页提前选好的书\n整理桌面的一小块\n写下脑中一个想法"


class PhonePage(QScrollArea):
    """A quiet, evergreen reference page; no daily counters or monitoring."""
    def __init__(self, window, settings):
        super().__init__()
        self.window_owner = window
        self.settings = settings
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(1, 2, 5, 2)
        layout.setSpacing(9)
        for heading, text in (
            ("先停一下", "想拿手机时，先问自己：\n“我是在休息，还是在逃避？”"),
            ("① 短暂无聊", "忍住不填满。\n等电梯、排队、短暂空隙，不急着拿手机。"),
            ("② 较长碎片", "从提前准备的小菜单里选一件。\n可以休息，不必把每段空闲都变成任务。"),
        ):
            layout.addWidget(self.make_card(heading, text))
        menu_card = WrappingCard()
        menu_card.setObjectName("projectCard")
        menu_layout = QVBoxLayout(menu_card)
        top = QHBoxLayout()
        label = QLabel("我的小菜单")
        label.setObjectName("sectionTitle")
        top.addWidget(label, 1)
        edit = QPushButton("编辑")
        edit.clicked.connect(self.edit_menu)
        top.addWidget(edit)
        menu_layout.addLayout(top)
        self.menu_label = WrappingLabel()
        menu_layout.addWidget(self.menu_label)
        layout.addWidget(menu_card)
        layout.addWidget(self.make_card("③ 工作学习", "把手机放到够不着的地方，关闭通知。\n先整理环境，再开始眼前的一件事。"))
        layout.addWidget(self.make_card("④ 休息，还是逃避？", "如果是休息：给自己一段真正的休息。\n如果在逃避：把眼前任务缩成一个小动作，再试着开始。"))
        layout.addStretch(1)
        self.setWidget(body)
        self.refresh_menu()

    @staticmethod
    def make_card(heading, text):
        card = WrappingCard()
        card.setObjectName("projectCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        title = WrappingLabel(heading)
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        layout.addWidget(WrappingLabel(text))
        return card

    def menu_text(self):
        return self.settings.value("phone/menu", DEFAULT_MENU, type=str)

    def refresh_menu(self):
        lines = [line.strip() for line in self.menu_text().splitlines() if line.strip()]
        self.menu_label.setText("\n".join(f"· {line}" for line in lines) if lines else "还没有小菜单，点击编辑准备几件想做的小事。")

    def save_menu(self, text):
        self.settings.setValue("phone/menu", text.strip())
        self.settings.sync()
        self.refresh_menu()

    def edit_menu(self):
        dialog = PopupDialog(self.window_owner, text_input=True)
        dialog.setFixedWidth(320)
        title = QLabel("碎片时间小菜单")
        title.setObjectName("sectionTitle")
        dialog.content.addWidget(title)
        dialog.content.addWidget(QLabel("每行一件小事，保存后长期保留。"))
        editor = QTextEdit()
        editor.setAcceptRichText(False)
        editor.setPlainText(self.menu_text())
        dialog.content.addWidget(editor)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog.content.addWidget(buttons)
        editor.setFocus()
        if dialog.exec():
            self.save_menu(editor.toPlainText())
