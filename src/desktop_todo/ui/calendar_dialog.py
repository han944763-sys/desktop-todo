from datetime import date

from PySide6.QtCore import QDate, QLocale, Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from desktop_todo.ui.popup import PopupDialog
from desktop_todo.ui.icons import icon_button, icon
from desktop_todo.ui.glass_style import dark_color
from PySide6.QtWidgets import QCalendarWidget, QHBoxLayout, QLabel, QMessageBox, QPushButton, QGridLayout, QSpinBox, QButtonGroup


class TaskCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.marked_dates: set[date] = set()
        self.setMinimumSize(260, 204)
        self.setNavigationBarVisible(False)
        self.dark = False
        self.background = QColor("#FFFFFF")
        self.setLocale(QLocale(QLocale.Language.Chinese, QLocale.Country.China))
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.NoHorizontalHeader)

    def paintCell(self, painter, rect, day):
        painter.save()
        painter.fillRect(rect, self.background)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        selected = day == self.selectedDate()
        current_month = day.month() == self.monthShown()
        cell = QRectF(rect).adjusted(3, 3, -3, -3)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#9985D9") if selected else Qt.BrushStyle.NoBrush)
        if day == QDate.currentDate() and not selected:
            painter.setPen(QPen(QColor("#AB98E2"), 1))
        painter.drawRoundedRect(cell, 12, 12)
        color = "#FFFFFF" if selected else (("#E9E6F6" if self.dark else "#3C4056") if current_month else ("#757889" if self.dark else "#BBB8C8"))
        painter.setPen(QColor(color))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(day.day()))
        if day.toPython() in self.marked_dates:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#FFFFFF" if selected else "#A08BCF"))
            painter.drawEllipse(rect.center().x() - 2, rect.bottom() - 7, 4, 4)
        painter.restore()


class CalendarDialog(PopupDialog):
    def __init__(self, parent, repository, selected: date):
        super().__init__(parent)
        self.setWindowTitle("选择日期")
        self.repository = repository
        self.chosen_date = selected
        layout = self.content
        self.setFixedWidth(300)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        header = QHBoxLayout()
        self.month_label = QPushButton()
        self.month_label.setToolTip("选择年份和月份")
        self.month_label.setAccessibleName("选择年份和月份")
        self.month_label.clicked.connect(self.select_year_month)
        header.addWidget(self.month_label, 1)
        self.calendar = TaskCalendar(self)
        self.calendar.dark = dark_color(self.card.color.name())
        self.calendar.background = QColor(self.card.color)
        for symbol, tooltip, callback in (("previous", "上个月", self.calendar.showPreviousMonth), ("next", "下个月", self.calendar.showNextMonth)):
            button = icon_button(symbol, tooltip)
            button.setIcon(icon(symbol, "#DDD7EE" if self.calendar.dark else "#77708A"))
            button.clicked.connect(callback)
            header.addWidget(button)
        layout.addLayout(header)
        weekdays = QHBoxLayout()
        for name in ("一", "二", "三", "四", "五", "六", "日"):
            label = QLabel(name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setObjectName("secondary")
            weekdays.addWidget(label)
        layout.addLayout(weekdays)
        self.calendar.setStyleSheet("QCalendarWidget QWidget { background: transparent; } QCalendarWidget QAbstractItemView { background: transparent; border: none; outline: none; }")
        self.calendar.setSelectedDate(QDate(selected.year, selected.month, selected.day))
        self.calendar.currentPageChanged.connect(self.refresh_marks)
        self.calendar.clicked.connect(self.choose)
        self.calendar.activated.connect(self.choose)
        layout.addWidget(self.calendar)
        footer = QHBoxLayout()
        hint = QLabel("● 有任务")
        hint.setToolTip("包括已完成任务")
        hint.setObjectName("secondary")
        footer.addWidget(hint, 1)
        today = QPushButton("回到今天")
        today.clicked.connect(lambda: self.choose(QDate.currentDate()))
        footer.addWidget(today)
        layout.addLayout(footer)
        self.refresh_marks(self.calendar.yearShown(), self.calendar.monthShown())

    def select_year_month(self):
        selector = YearMonthDialog(self, self.calendar.yearShown(), self.calendar.monthShown())
        if selector.exec():
            self.calendar.setCurrentPage(selector.year.value(), selector.months.checkedId())

    def refresh_marks(self, year, month):
        self.month_label.setText(f"{year} 年 {month} 月")
        first = QDate(year, month, 1)
        # Include adjacent-month cells in the six-week calendar grid.
        start = first.addDays(1 - first.dayOfWeek() - 7)
        try:
            self.calendar.marked_dates = self.repository.task_dates(
                start.toPython(), first.addMonths(1).addDays(14).toPython()
            )
        except Exception as exc:
            self.calendar.marked_dates = set()
            QMessageBox.warning(self, "读取日历失败", str(exc))
        self.calendar.updateCells()

    def choose(self, day):
        self.chosen_date = day.toPython()
        self.accept()


class YearMonthDialog(PopupDialog):
    def __init__(self, parent, year, month):
        super().__init__(parent)
        self.setFixedWidth(280)
        title = QLabel("选择年月")
        title.setObjectName("sectionTitle")
        self.content.addWidget(title)
        self.year = QSpinBox()
        self.year.setRange(1752, 9998)
        self.year.setValue(year)
        self.year.setSuffix(" 年")
        self.year.setAccessibleName("年份")
        self.year.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content.addWidget(self.year)
        grid = QGridLayout()
        self.months = QButtonGroup(self)
        for value in range(1, 13):
            button = QPushButton(f"{value}月")
            button.setCheckable(True)
            button.setChecked(value == month)
            self.months.addButton(button, value)
            grid.addWidget(button, (value - 1) // 3, (value - 1) % 3)
        self.content.addLayout(grid)
        done = QPushButton("确定")
        done.clicked.connect(self.accept)
        self.content.addWidget(done)
