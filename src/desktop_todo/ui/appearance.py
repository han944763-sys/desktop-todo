from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QSlider, QColorDialog)
from desktop_todo.ui.popup import PopupDialog


class GlassCard(QWidget):
    """Translucent tint and curved highlights; child content stays opaque."""
    def __init__(self):
        super().__init__()
        self.color = QColor("#FFFFFF")
        self.opacity = 88

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        top = QColor(self.color)
        top.setAlpha(round(255 * min(100, self.opacity + 6) / 100))
        bottom = QColor(self.color)
        bottom.setAlpha(round(255 * self.opacity / 100))
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, top)
        gradient.setColorAt(1, bottom)
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(255, 255, 255, 190), 1.3))
        painter.drawRoundedRect(rect, 24, 24)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(180, 185, 205, 48), 1))
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 22, 22)


class AppearanceDialog(PopupDialog):
    appearance_changed = Signal(str, int)

    def __init__(self, parent, color, opacity):
        super().__init__(parent)
        self.setWindowTitle("外观")
        self.setMinimumWidth(340)
        self.color = color
        layout = self.content
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(18)
        layout.addWidget(QLabel("背景颜色"))
        row = QHBoxLayout()
        for label, value in (("白色", "#FFFFFF"), ("薰衣草", "#EEE8FF"),
                             ("薄荷", "#E3F4EE"), ("深色", "#252B3B")):
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, c=value: self.set_color(c))
            row.addWidget(button)
        layout.addLayout(row)
        custom = QPushButton("自定义颜色…")
        custom.clicked.connect(self.pick_color)
        layout.addWidget(custom)
        self.opacity_label = QLabel(f"背景不透明度  {opacity}%")
        layout.addWidget(self.opacity_label)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(40, 100)
        self.slider.setValue(opacity)
        self.slider.valueChanged.connect(self.publish)
        self.slider.setAccessibleName("背景不透明度")
        layout.addWidget(self.slider)
        hint = QLabel("向左更通透，向右更清晰。\n文字保持清晰，外观自动保存。")
        hint.setObjectName("secondary")
        layout.addWidget(hint)
        done = QPushButton("完成")
        done.clicked.connect(self.accept)
        layout.addWidget(done)

    def set_color(self, color):
        self.color = color
        self.publish()

    def pick_color(self):
        chosen = QColorDialog.getColor(QColor(self.color), self, "选择背景颜色")
        if chosen.isValid():
            self.set_color(chosen.name())

    def publish(self):
        opacity = self.slider.value()
        self.opacity_label.setText(f"背景不透明度  {opacity}%")
        self.appearance_changed.emit(self.color, opacity)
        self.card.color = QColor(self.color)
        self.card.update()
