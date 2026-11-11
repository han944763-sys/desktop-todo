from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen


def main() -> None:
    target = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "desktop_todo"
        / "assets"
        / "icon.ico"
    )
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#6C63FF"))
    painter.drawRoundedRect(QRectF(16, 16, 224, 224), 56, 56)

    check = QPainterPath(QPointF(70, 132))
    check.lineTo(QPointF(108, 170))
    check.lineTo(QPointF(186, 86))
    pen = QPen(
        QColor("#FFFFFF"),
        24,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin,
    )
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(check)
    painter.end()

    target.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(target), "ICO"):
        raise RuntimeError(f"无法生成图标：{target}")
    print(target)


if __name__ == "__main__":
    main()

