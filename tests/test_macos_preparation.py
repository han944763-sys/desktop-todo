import importlib.util
from pathlib import Path

from desktop_todo import paths


def test_mac_database_location(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("LOCALAPPDATA", "ignored-on-mac")
    assert paths.database_path() == tmp_path / "Library/Application Support/DesktopTodo/todo.db"


def test_mac_builder_refuses_windows(monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts/build_macos.py"
    spec = importlib.util.spec_from_file_location("build_macos", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.sys, "platform", "win32")
    assert module.main() == 2
