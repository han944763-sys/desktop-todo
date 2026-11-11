from __future__ import annotations

import os
import sys
import tempfile
from datetime import date
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from desktop_todo.repository import TodoRepository
from desktop_todo.ui.main_window import MainWindow
from desktop_todo.ui.glass_style import theme_style


def main() -> int:
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/ui-preview.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="desktop-todo-preview-") as temp_dir:
        temp = Path(temp_dir)
        app = QApplication.instance() or QApplication([])
        app.setStyleSheet(theme_style())
        settings = QSettings(str(temp / "settings.ini"), QSettings.Format.IniFormat)
        repository = TodoRepository(temp / "todo.db")
        first = repository.create_task("调试机器人红外模块", date.today())
        repository.create_task("修改论文图标题", date.today())
        repository.create_task("英语听力 20 分钟", date.today())
        repository.set_task_completed(first.id, True)
        project = repository.create_project(
            "机器人自动回充",
            "完成稳定、可重复的实体回充流程",
            "红外结构验证",
            "完成红外传感器建模",
        )
        linked, _ = repository.add_next_action_to_date(project.id, date.today())
        repository.set_task_completed(linked.id, True)
        repository.create_project(
            "英语能力提升",
            "能够进行日常英文交流",
            "基础恢复",
            "完成 20 分钟听力训练",
        )

        window = MainWindow(repository, settings, tray_available=False)
        if os.environ.get("PREVIEW_NARROW"):
            long_project = repository.create_project("半年学习｜机器人回充与结构仿真（2026 年计划）" * 3, "目标", "阶段", "行动")
            repository.create_task("检查 ANSYS 可用情况；记录版本及待确认项。" * 10, date.today(), project_id=long_project.id)
            repository.create_task("ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 10, date.today())
            window.refresh_all()
            window.resize(330, 620)
        window.apply_appearance(os.environ.get("PREVIEW_COLOR", "#FFFFFF"),
                                int(os.environ.get("PREVIEW_OPACITY", "88")))
        window.show()
        for _ in range(10):
            app.processEvents()
        if os.environ.get("PREVIEW_PAGE") == "projects":
            window.page_buttons.button(1).click()
            app.processEvents()
        if os.environ.get("PREVIEW_PAGE") == "phone":
            window.page_buttons.button(2).click()
            for _ in range(10):
                app.processEvents()
        if os.environ.get("PREVIEW_PAGE") == "calendar":
            from desktop_todo.ui.calendar_dialog import CalendarDialog
            calendar = CalendarDialog(window, repository, date.today())
            calendar.show()
            app.processEvents()
            calendar.grab().save(str(output.with_stem(output.stem + "-calendar")), "PNG")
            calendar.close()
        if os.environ.get("PREVIEW_PAGE") == "task":
            from desktop_todo.ui.dialogs import TaskDialog
            task_dialog = TaskDialog(window, date.today())
            task_dialog.show()
            app.processEvents()
            task_dialog.grab().save(str(output.with_stem(output.stem + "-task")), "PNG")
            task_dialog.close()
        if os.environ.get("PREVIEW_PAGE") in ("appearance", "year"):
            from desktop_todo.ui.appearance import AppearanceDialog
            from desktop_todo.ui.calendar_dialog import YearMonthDialog
            popup = (AppearanceDialog(window, window.glass_card.color.name(), 88)
                     if os.environ["PREVIEW_PAGE"] == "appearance" else YearMonthDialog(window, 2026, 9))
            popup.show()
            app.processEvents()
            popup.grab().save(str(output.with_stem(output.stem + "-popup")), "PNG")
            popup.close()
        if not window.grab().save(str(output), "PNG"):
            raise RuntimeError(f"无法保存预览图：{output}")
        window.prepare_quit()
        window.close()
        repository.close()
        app.quit()
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
