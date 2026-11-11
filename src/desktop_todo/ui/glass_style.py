from PySide6.QtGui import QColor


def dark_color(color):
    c = QColor(color)
    return .2126 * c.redF() + .7152 * c.greenF() + .0722 * c.blueF() < .45


def theme_style(color="#FFFFFF"):
    dark = dark_color(color)
    text, muted = ("#F5F6FC", "#B5BDD0") if dark else ("#30384A", "#778094")
    surface = "rgba(255,255,255,18)" if dark else "rgba(255,255,255,145)"
    field = "rgba(255,255,255,22)" if dark else "rgba(255,255,255,180)"
    solid = "#272C3A" if dark else "#F9FAFF"
    return f"""
QWidget {{ color: {text}; font-family: "Microsoft YaHei UI", "PingFang SC", "Segoe UI"; font-size: 13px; }}
QLabel, QWidget#headerBar {{ background: transparent; }}
QDialog, QMessageBox {{ background: {solid}; }}
QCalendarWidget QWidget {{ background: {solid}; }}
QCalendarWidget QAbstractItemView {{ background: {solid}; color: {text}; selection-background-color: #9985D9; selection-color: white; border: none; outline: none; }}
QCalendarWidget QToolButton {{ color: {text}; background: transparent; border: none; padding: 6px; }}
QCalendarWidget QSpinBox {{ background: {solid}; color: {text}; }}
QLabel#sectionTitle, QLabel#projectName {{ font-size: 14px; font-weight: 600; }}
QLabel#dateLabel {{ font-size: 13px; font-weight: 500; }}
QLabel#secondary, QLabel#emptyLabel, QLabel#projectMeta, QLabel#recentLabel {{ color: {muted}; font-size: 12px; }}
QLabel#emptyLabel {{ padding: 14px 0; }}
QLabel#statusLabel {{ color: {muted}; font-size: 11px; }}
QPushButton {{ background: {surface}; border: 1px solid rgba(135,145,170,35); border-radius: 11px; padding: 7px 12px; }}
QPushButton:hover {{ background: rgba(150,140,240,35); }}
QPushButton:pressed {{ background: rgba(150,140,240,65); }}
QPushButton:checked {{ background: rgba(130,110,240,45); border-color: rgba(130,110,240,65); }}
QPushButton#iconButton {{ min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; padding: 0; border: none; background: transparent; border-radius: 10px; }}
QPushButton#iconButton:hover {{ background: rgba(150,140,240,35); }}
QPushButton#iconButton:checked {{ background: rgba(130,110,240,48); }}
QPushButton#addButton {{ min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px; padding: 0; background: rgba(130,110,240,32); border-color: rgba(130,110,240,40); }}
QLineEdit, QTextEdit {{ background: {field}; border: 1px solid rgba(135,145,170,40); border-radius: 12px; padding: 8px 10px; selection-background-color: #B5AAF2; }}
QLineEdit:focus, QTextEdit:focus {{ border-color: #AC9FE9; }}
QSpinBox {{ background: {field}; color: {text}; border: 1px solid rgba(135,145,170,40); border-radius: 10px; padding: 8px; }}
QLineEdit#taskEditor {{ background: transparent; border: none; padding: 4px 2px; }}
QLabel#taskEditor {{ padding: 4px 2px; }}
QLabel#taskEditor[completed="true"] {{ color: {muted}; }}
QCheckBox {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid #ADB2C5; border-radius: 6px; background: {surface}; }}
QCheckBox::indicator:checked {{ background: #ABA0E9; border-color: #9585D9; }}
QFrame#taskRow, QFrame#projectCard {{ background: {surface}; border: 1px solid rgba(160,166,190,28); border-radius: 15px; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QScrollBar:vertical {{ width: 4px; background: transparent; margin: 4px 0; }}
QScrollBar::handle:vertical {{ background: rgba(130,135,160,80); border-radius: 2px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QMenu {{ background: {solid}; border: 1px solid rgba(135,145,170,50); padding: 6px; }}
QMenu::item {{ padding: 8px 22px 8px 12px; border-radius: 6px; }}
QMenu::item:selected {{ background: rgba(150,140,240,35); }}
QToolTip {{ color: {text}; background: {solid}; border: 1px solid #C7CADD; padding: 5px; }}
QSlider::groove:horizontal {{ height: 5px; border-radius: 2px; background: #DCDDE8; }}
QSlider::sub-page:horizontal {{ background: #A99BE4; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 16px; margin: -6px 0; border-radius: 8px; background: #FFFFFF; border: 1px solid #A99BE4; }}
"""
