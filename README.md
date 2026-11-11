# 桌面清单 · Desktop Todo

一个常驻桌面的中文待办小工具，把每日任务和长期项目的下一步行动放在同一个小窗里。使用 Python、PySide6 和 SQLite，任务数据保存在本机。

## 下载 Windows 版

前往 **[Releases 下载页面](https://github.com/han944763-sys/desktop-todo/releases/tag/v0.1.0)**，展开 Assets，选择需要的 EXE。下载后双击运行，无需安装 Python。

| 文件 | 版本区别 |
| --- | --- |
| 桌面清单-少看手机版.exe | 包含完成分组，以及第三页“少看手机”：四点提醒和可编辑的碎片时间小菜单。 |
| 桌面清单-完成分组版.exe | 较早的版本，每日任务按“未完成”和“已完成”分组，打勾后即时移动，取消勾选后恢复。 |

两个 EXE 为原有历史构建，本次发布未重新编译。仓库保存当前源码，已包含完成分组和少看手机功能；不提供完成分组旧版的独立源码快照。文件大小和 SHA-256 见 [发布说明](docs/releases/v0.1.0.md)。

## 功能

- 按日期添加、修改、完成、恢复和删除任务，月历支持查看有任务的日期。
- 完成项移入已完成分组，两组内部保持创建顺序；未完成任务不会自动顺延到第二天。
- 长期项目记录目标、当前阶段和下一步行动，可把下一步加入当天任务。
- 无边框小窗、始终置顶、系统托盘、单实例运行和窗口位置保存。
- 主题颜色和背景透明度可调整；可选择开启当前用户的开机启动，默认关闭。
- SQLite 自动保存，数据库升级前自动备份。
- 少看手机版提供提醒及可编辑小菜单，不监控手机、不锁机、不统计手机使用时长。

## 使用与数据

关闭按钮默认隐藏窗口，可从系统托盘恢复；完全退出请右键托盘图标，选择“退出”。

Windows 任务数据库位于：

```text
%LOCALAPPDATA%\DesktopTodo\todo.db
```

两个版本使用相同的数据目录和单实例机制。切换版本前先从托盘完全退出，建议先备份上述数据目录；新电脑不会自动同步原电脑的数据。偏好设置也保存在本机。

## 从源码运行

当前项目使用 Python 3.12。安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 后，在终端执行：

```powershell
git clone https://github.com/han944763-sys/desktop-todo.git
cd desktop-todo
uv sync --locked
uv run python main.py
```

uv 会按照项目配置准备 Python 和依赖。Windows 也可以运行 `scripts/run.ps1`。

## 测试与构建

```powershell
uv run pytest
.\scripts\build.ps1
```

Windows 默认输出 `dist/桌面清单.exe`。构建脚本优先使用 `pyside6-deploy`，未生成目标 EXE 时回退到 PyInstaller。也可指定输出文件名：

```powershell
.\scripts\build.ps1 -OutputName '桌面清单-自定义版.exe'
```

指定文件名只影响产物名称；构建内容始终来自当前源码，不会还原旧版功能。

## macOS 状态

已准备 macOS 适配和构建脚本，尚未在 Mac 上构建或完成实机验证，本次不提供 Mac 安装包。详见 [macOS 构建说明](MACOS.md) 和 [M2 构建步骤](开始使用-M2.md)。

## 验证范围

2026-11-11 在 Windows 的现有 Python 环境中运行，当前源码的 25 项自动测试通过，包括任务分组、少看手机页面及数据保存等用例。这不代表已完成两个历史 EXE 的完整人工交互、真实输入法候选框、重启自启动、多显示器和长期运行验证。

源码仓库不包含个人待办数据库、个人学习计划、本地虚拟环境或历史构建目录；Windows EXE 作为 Release 附件单独提供。
