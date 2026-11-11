from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from desktop_todo import paths
from desktop_todo import windows


def test_database_uses_local_app_data(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert paths.database_path() == tmp_path / "DesktopTodo" / "todo.db"


def test_source_startup_command_is_quoted_and_uses_module(monkeypatch, tmp_path):
    executable = tmp_path / "Python Folder" / "python.exe"
    monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setattr(windows, "is_frozen_application", lambda: False)

    command = windows.startup_command()
    expected = subprocess.list2cmdline(
        [str(Path(executable).resolve()), "-m", "desktop_todo", "--autostart"]
    )
    assert command == expected


def test_frozen_startup_command_targets_executable(monkeypatch, tmp_path):
    executable = tmp_path / "桌面清单.exe"
    monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setattr(windows, "is_frozen_application", lambda: True)

    assert windows.startup_command() == subprocess.list2cmdline(
        [str(executable.resolve()), "--autostart"]
    )


def test_startup_manager_writes_refreshes_and_removes_registry_value(monkeypatch):
    values: dict[str, str] = {}

    class Key:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

    class FakeWinreg:
        HKEY_CURRENT_USER = object()
        REG_SZ = 1
        KEY_SET_VALUE = 2

        @staticmethod
        def OpenKey(*_args):
            if not values:
                raise FileNotFoundError
            return Key()

        @staticmethod
        def CreateKey(*_args):
            return Key()

        @staticmethod
        def QueryValueEx(_key, name):
            if name not in values:
                raise FileNotFoundError
            return values[name], FakeWinreg.REG_SZ

        @staticmethod
        def SetValueEx(_key, name, _reserved, _kind, value):
            values[name] = value

        @staticmethod
        def DeleteValue(_key, name):
            if name not in values:
                raise FileNotFoundError
            del values[name]

    manager = object.__new__(windows.StartupManager)
    monkeypatch.setattr(manager, "_winreg", lambda: FakeWinreg)
    monkeypatch.setattr(windows, "startup_command", lambda: '"C:\\App\\DesktopTodo.exe" --autostart')

    assert manager.is_enabled() is False
    manager.set_enabled(True)
    assert manager.command() == '"C:\\App\\DesktopTodo.exe" --autostart'
    values[windows.VALUE_NAME] = '"C:\\Old\\DesktopTodo.exe" --autostart'
    manager.refresh_enabled_command()
    assert manager.command() == '"C:\\App\\DesktopTodo.exe" --autostart'
    manager.set_enabled(False)
    assert manager.is_enabled() is False
