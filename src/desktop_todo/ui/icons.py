"""Font-free toolbar symbols, rendered at multiple display densities."""
from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QPushButton


def icon(name, color="#586174"):
    result = QIcon()
    for scale in (1, 2, 3):
        pixmap = QPixmap(24 * scale, 24 * scale)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(scale, scale)
        painter.setPen(QPen(QColor(color), 1.7, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        def line(points):
            path = QPainterPath()
            path.moveTo(*points[0])
            for point in points[1:]:
                path.lineTo(*point)
            painter.drawPath(path)
        if name == "previous":
            line([(14, 6), (8, 12), (14, 18)])
        elif name == "next":
            line([(10, 6), (16, 12), (10, 18)])
        elif name == "close":
            line([(7, 7), (17, 17)])
            line([(17, 7), (7, 17)])
        elif name == "minus":
            line([(6, 12), (18, 12)])
        elif name == "plus":
            line([(6, 12), (18, 12)])
            line([(12, 6), (12, 18)])
        elif name == "pin":
            line([(8, 4), (16, 4), (15, 10), (18, 14), (6, 14), (9, 10), (8, 4)])
            line([(12, 14), (12, 21)])
        elif name == "calendar":
            painter.drawRoundedRect(QRectF(4, 5, 16, 15), 3, 3)
            line([(8, 3), (8, 7)])
            line([(16, 3), (16, 7)])
            line([(4, 10), (20, 10)])
            line([(9, 15), (11, 17), (16, 13)])
        elif name == "palette":
            painter.drawEllipse(QRectF(3, 3, 18, 18))
            for x, y in ((8, 8), (14, 7), (17, 12)):
                painter.drawEllipse(QRectF(x - 1, y - 1, 2, 2))
            line([(7, 17), (10, 14), (13, 17)])
        elif name == "check":
            painter.drawRoundedRect(QRectF(3, 3, 18, 18), 6, 6)
            line([(7, 12), (11, 16), (17, 8)])
        else:
            for x in (5, 12, 19):
                painter.drawEllipse(QRectF(x - .7, 11.3, 1.4, 1.4))
        painter.end()
        pixmap.setDevicePixelRatio(scale)
        result.addPixmap(pixmap)
    return result


def icon_button(name, tooltip):
    button = QPushButton()
    button.setObjectName("iconButton")
    button.setProperty("symbol", name)
    button.setIcon(icon(name))
    button.setIconSize(QSize(19, 19))
    button.setToolTip(tooltip)
    button.setAccessibleName(tooltip)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button
