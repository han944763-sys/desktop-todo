from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "DesktopTodo"


def is_frozen_application() -> bool:
    main_module = sys.modules.get("__main__")
    return bool(getattr(sys, "frozen", False)) or bool(
        main_module and "__compiled__" in vars(main_module)
    )


def startup_command() -> str:
    if is_frozen_application():
        arguments = [str(Path(sys.executable).resolve()), "--autostart"]
    else:
        arguments = [
            str(Path(sys.executable).resolve()),
            "-m",
            "desktop_todo",
            "--autostart",
        ]
    return subprocess.list2cmdline(arguments)


class StartupManager:
    def __init__(self) -> None:
        if os.name != "nt":
            raise OSError("开机启动仅支持 Windows")

    @staticmethod
    def _winreg():
        import winreg

        return winreg

    def command(self) -> str | None:
        winreg = self._winreg()
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                value, _ = winreg.QueryValueEx(key, VALUE_NAME)
                return str(value)
        except FileNotFoundError:
            return None

    def is_enabled(self) -> bool:
        return self.command() is not None

    def set_enabled(self, enabled: bool) -> None:
        winreg = self._winreg()
        if enabled:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                winreg.SetValueEx(
                    key, VALUE_NAME, 0, winreg.REG_SZ, startup_command()
                )
            return
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, VALUE_NAME)
        except FileNotFoundError:
            pass

    def refresh_enabled_command(self) -> None:
        if self.is_enabled() and self.command() != startup_command():
            self.set_enabled(True)

