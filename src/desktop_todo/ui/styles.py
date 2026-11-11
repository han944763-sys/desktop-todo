APP_STYLE = """
QWidget {
    color: #ECECF4;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 13px;
}
QWidget#windowCard {
    background: #191A23;
    border: 1px solid #343646;
    border-radius: 18px;
}
QWidget#headerBar {
    background: transparent;
}
QLabel#appTitle {
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 700;
}
QLabel#dateLabel {
    color: #B7B9C9;
    font-size: 12px;
}
QLabel#sectionTitle {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 700;
}
QLabel#secondary, QLabel#emptyLabel, QLabel#projectMeta, QLabel#recentLabel {
    color: #9295A8;
    font-size: 12px;
}
QLabel#statusLabel {
    color: #A8E6CF;
    font-size: 12px;
}
QPushButton {
    background: #2B2D3B;
    border: 1px solid #3C3F52;
    border-radius: 8px;
    padding: 6px 10px;
}
QPushButton:hover {
    background: #36394A;
}
QPushButton:pressed {
    background: #242633;
}
QPushButton:checked, QPushButton#accentButton {
    background: #6C63FF;
    border-color: #837CFF;
    color: white;
}
QPushButton:disabled {
    color: #676A7B;
    background: #242631;
    border-color: #303240;
}
QPushButton#iconButton {
    min-width: 26px;
    max-width: 26px;
    min-height: 26px;
    max-height: 26px;
    padding: 0;
    border-radius: 7px;
}
QPushButton#dangerButton {
    color: #FF9B9B;
}
QLineEdit, QTextEdit {
    background: #232531;
    border: 1px solid #3A3D4D;
    border-radius: 8px;
    padding: 7px 9px;
    selection-background-color: #6C63FF;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #756DFF;
}
QLineEdit#taskEditor {
    background: transparent;
    border: none;
    padding: 4px 2px;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border: 2px solid #686B80;
    border-radius: 5px;
    background: transparent;
}
QCheckBox::indicator:checked {
    background: #6C63FF;
    border-color: #6C63FF;
}
QFrame#taskRow, QFrame#projectCard {
    background: #21232E;
    border: 1px solid #303342;
    border-radius: 11px;
}
QScrollArea, QScrollArea > QWidget > QWidget {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    width: 7px;
    background: transparent;
    margin: 3px 0;
}
QScrollBar::handle:vertical {
    background: #454859;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QMenu {
    background: #272936;
    border: 1px solid #404355;
    padding: 5px;
}
QMenu::item {
    padding: 7px 22px 7px 10px;
    border-radius: 6px;
}
QMenu::item:selected {
    background: #3B3E50;
}
QToolTip {
    color: #FFFFFF;
    background: #2B2D3B;
    border: 1px solid #46495B;
    padding: 4px;
}
"""

