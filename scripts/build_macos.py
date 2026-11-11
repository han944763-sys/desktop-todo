"""Run with `uv run python scripts/build_macos.py` on a Mac, not Windows."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "桌面清单"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def make_icon(stage: Path) -> Path:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    iconset = stage / "DesktopTodo.iconset"
    iconset.mkdir()
    renderer = QSvgRenderer(str(ROOT / "src/desktop_todo/assets/icon.svg"))
    if not renderer.isValid():
        raise RuntimeError("无法读取应用图标")
    for size in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            image = QImage(size * scale, size * scale, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            renderer.render(painter)
            painter.end()
            suffix = "@2x" if scale == 2 else ""
            if not image.save(str(iconset / f"icon_{size}x{size}{suffix}.png")):
                raise RuntimeError("无法生成 Mac 图标")
    target = stage / "DesktopTodo.icns"
    run("iconutil", "-c", "icns", str(iconset), "-o", str(target))
    return target


def main() -> int:
    if sys.platform != "darwin":
        print("必须在 macOS 上构建；Windows 不能生成此 DMG。", file=sys.stderr)
        return 2
    if int(platform.mac_ver()[0].split(".")[0]) < 13:
        print("当前锁定的 PySide6 版本要求 macOS 13 或以上。", file=sys.stderr)
        return 2
    arch = platform.machine()
    if arch not in ("arm64", "x86_64"):
        raise RuntimeError(f"不支持的 Python 运行架构：{arch}")
    for command in ("iconutil", "hdiutil", "codesign"):
        if not shutil.which(command):
            raise RuntimeError(f"缺少 macOS 工具：{command}")

    # Every run gets a new directory. Never delete or overwrite previous releases.
    output = ROOT / "dist" / f"macos-{arch}-{datetime.now():%Y%m%d-%H%M%S-%f}"
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="DesktopTodo-macos-") as temp:
        stage = Path(temp)
        icon = make_icon(stage)
        args = [
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--windowed", "--onedir", "--name", APP_NAME,
            "--target-architecture", arch,
            "--osx-bundle-identifier", "local.desktop-todo.app",
            "--icon", str(icon), "--paths", str(ROOT / "src"),
            "--add-data", f"{ROOT / 'src/desktop_todo/assets'}:desktop_todo/assets",
            "--distpath", str(output), "--workpath", str(stage / "work"),
            "--specpath", str(stage),
        ]
        # Optional identity already configured in the Mac's keychain.
        identity = os.environ.get("MACOS_CODESIGN_IDENTITY")
        if identity:
            args.extend(["--codesign-identity", identity])
        run(*args, str(ROOT / "main.py"))
        app = output / f"{APP_NAME}.app"
        if not app.is_dir():
            raise RuntimeError("构建未生成 .app")
        run("codesign", "--verify", "--deep", "--strict", str(app))
        run(str(app / "Contents/MacOS" / APP_NAME), "--help")
        volume = stage / "volume"
        volume.mkdir()
        shutil.copytree(app, volume / app.name, symlinks=True)
        (volume / "Applications").symlink_to("/Applications", target_is_directory=True)
        shutil.copy2(ROOT / "MACOS.md", volume / "使用说明.md")
        dmg = output / f"{APP_NAME}-macOS-{arch}.dmg"
        run("hdiutil", "create", "-volname", APP_NAME, "-srcfolder", str(volume),
            "-format", "UDZO", str(dmg))
        run("hdiutil", "verify", str(dmg))
        print(f"已构建：{dmg}\n尚需 Mac 实机交互验证；未自动进行 Apple 公证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
