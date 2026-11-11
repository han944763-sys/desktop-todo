from PySide6.QtCore import Qt, QPoint, QRectF, QEvent, QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QWidget
from PySide6.QtGui import QColor, QPainterPath, QRegion


class PopupDialog(QDialog):
    """Dismissible card: outside click and Escape reject, never save."""
    def __init__(self, parent, *, text_input=False):
        self.text_input = text_input
        self._composing = False
        # Native popup/menu windows can prevent Windows IME activation.
        kind = Qt.WindowType.Dialog if text_input else Qt.WindowType.Popup
        super().__init__(parent, kind | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        from desktop_todo.ui.appearance import GlassCard
        self.setObjectName("floatingPopup")
        self.setStyleSheet("QDialog#floatingPopup { background: transparent; border: none; }")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.card = GlassCard()
        source_card = getattr(parent, "glass_card", getattr(parent, "card", None))
        self.card.color = QColor(source_card.color) if source_card else QColor("#FFFFFF")
        self.card.opacity = 100
        outer.addWidget(self.card)
        self.content = QVBoxLayout(self.card)
        self.content.setContentsMargins(20, 20, 20, 20)
        self.content.setSpacing(14)

    def exec(self):
        if not self.text_input:
            return super().exec()
        # Keep the parent clickable for outside dismissal without a popup grab.
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setResult(0)
        loop = QEventLoop(self)
        self.finished.connect(loop.quit)
        self.show()
        self.raise_()
        self.activateWindow()
        loop.exec()
        self.finished.disconnect(loop.quit)
        loop.deleteLater()
        return self.result()

    def eventFilter(self, watched, event):
        if self.text_input and self.isVisible():
            if event.type() == QEvent.Type.InputMethod and isinstance(watched, QWidget) and self.isAncestorOf(watched):
                self._composing = bool(event.preeditString())
            elif event.type() == QEvent.Type.MouseButtonPress and isinstance(watched, QWidget):
                if watched is not self and not self.isAncestorOf(watched):
                    self.reject()
                    return True
            elif event.type() == QEvent.Type.ApplicationDeactivate:
                QTimer.singleShot(150, self._dismiss_if_inactive)
        return super().eventFilter(watched, event)

    def _dismiss_if_inactive(self):
        if self.isVisible() and not self._composing and QApplication.applicationState() == Qt.ApplicationState.ApplicationInactive:
            self.reject()

    def hideEvent(self, event):
        if self.text_input:
            QApplication.instance().removeEventFilter(self)
        super().hideEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Clip the native popup surface as well as its painted card on Windows.
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 24, 24)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def showEvent(self, event):
        super().showEvent(event)
        if self.text_input:
            QApplication.instance().installEventFilter(self)
            self._composing = False
        parent = self.parentWidget()
        if parent:
            point = parent.mapToGlobal(QPoint((parent.width() - self.width()) // 2, 100))
            area = parent.screen().availableGeometry()
            point.setX(max(area.left(), min(point.x(), area.right() - self.width() + 1)))
            point.setY(max(area.top(), min(point.y(), area.bottom() - self.height() + 1)))
            self.move(point)

    def mousePressEvent(self, event):
        if not self.rect().contains(event.position().toPoint()):
            self.reject()
            return
        super().mousePressEvent(event)
