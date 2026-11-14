# Desktop Todo · 桌面清单

[简体中文](README.md) | English

A small Chinese-language desktop to-do app that brings daily tasks and the next actions for long-term projects into one desktop window. The Windows edition uses Python and PySide6. The native macOS edition, Daily Note (每日便签), uses Swift, AppKit, and SwiftUI. Both store task data locally in SQLite.

## Download for macOS

[Download Daily Note for Apple silicon](https://github.com/han944763-sys/desktop-todo/releases/download/macos-v1.0.0/DailyNote-macOS-arm64.dmg) · [Release notes](https://github.com/han944763-sys/desktop-todo/releases/tag/macos-v1.0.0) · [Source and user guide (Chinese)](macos/)

Requires macOS 13 or later. Open the DMG and drag 每日便签 into Applications. This build is ad hoc signed and has no Apple notarization. If macOS blocks it, follow the [local build instructions](macos/#构建与检查).

## Download for Windows

Open the **[Releases download page](https://github.com/han944763-sys/desktop-todo/releases/tag/v0.1.0)**, expand Assets, and choose an EXE. Double-click the downloaded file to run it; no Python installation is required.

| Version / original release label | Direct download | What's included |
| --- | --- | --- |
| Less Phone — 桌面清单-少看手机版.exe | [DesktopTodo-LessPhone.exe](https://github.com/han944763-sys/desktop-todo/releases/download/v0.1.0/DesktopTodo-LessPhone.exe) | Task grouping, plus a third page with four reminders about phone use and an editable menu of activities for spare moments. |
| Task Groups — 桌面清单-完成分组版.exe | [DesktopTodo-TaskGroups.exe](https://github.com/han944763-sys/desktop-todo/releases/download/v0.1.0/DesktopTodo-TaskGroups.exe) | An earlier version that separates daily tasks into unfinished and completed groups. Checking a task moves it immediately; unchecking it restores it. |

Downloads use English filenames, while Release asset labels retain the original Chinese names. File contents are identical to the original EXEs. Both EXEs are existing historical builds and were not rebuilt for this release. This repository contains the current source, including task grouping and Less Phone features; a separate source snapshot for the older Task Groups build is unavailable. See the [release notes (Chinese)](docs/releases/v0.1.0.md) for file sizes and SHA-256 checksums.

## Windows features

- Add, edit, complete, restore, and delete tasks by date. The calendar marks dates that have tasks.
- Completed tasks move to a separate group. Both groups preserve creation order; unfinished tasks do not automatically carry over to the next day.
- Record a goal, current stage, and next action for each long-term project, then add its next action to a day's task list.
- A borderless window, always-on-top mode, system tray, single-instance operation, and saved window position.
- Adjustable theme colors and background opacity. Optional startup at Windows sign-in for the current user, disabled by default.
- Automatic saving to SQLite, with a database backup before schema upgrades.
- The Less Phone version offers reminders and an editable activity menu. It does not monitor or lock your phone, or track phone usage time.

## Usage and data

The window's close button hides it to the system tray by default. Restore it from the tray; to quit completely, right-click the tray icon and select **退出** (Quit).

The Windows task database is stored at:

```text
%LOCALAPPDATA%\DesktopTodo\todo.db
```

Both versions share the same data directory and single-instance mechanism. Quit completely from the tray before switching versions, and back up this data directory first. Data is not automatically synchronized to another computer. Preferences are also stored locally.

## Run the Windows edition from source

The project uses Python 3.12. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```powershell
git clone https://github.com/han944763-sys/desktop-todo.git
cd desktop-todo
uv sync --locked
uv run python main.py
```

uv prepares Python and dependencies using the project configuration. On Windows, you can also run `scripts/run.ps1`.

## Tests and builds

```powershell
uv run pytest
.\scripts\build.ps1
```

The default Windows output is `dist/桌面清单.exe`. The build script first tries `pyside6-deploy`, then falls back to PyInstaller if the target EXE was not produced. You can also choose an output filename:

```powershell
.\scripts\build.ps1 -OutputName 'DesktopTodo-Custom.exe'
```

The filename option only changes the output name. Builds always use the current source and do not restore an older version's features.

## Building the Python edition on macOS

The Python/PySide6 edition also has macOS build scripts. See the [macOS build guide](MACOS.md) and [M2 build steps](开始使用-M2.md), both in Chinese.

## Validation scope

On November 11, 2026, all 25 automated tests for the current source passed in the existing Windows Python environment, including tests for task grouping, the Less Phone page, and data persistence. This does not establish complete manual validation of the two historical EXEs, real input-method candidate windows, startup after a Windows restart, multiple monitors, or long-running operation.

The source repository excludes personal task databases, personal learning plans, local virtual environments, and historical build directories. Windows EXEs and the macOS DMG are available as Release assets.
