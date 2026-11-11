# 桌面清单 macOS 构建说明

当前状态：已准备源码适配和打包脚本，尚未在 Mac 构建，也未生成可交付 DMG。

## 在 Mac 上构建

要求 macOS 13 或以上（当前锁定的 PySide6 6.11.2 wheel 最低版本为 13.0）、uv，以及系统的 iconutil、hdiutil、codesign。安装命令行工具可使用 `xcode-select --install`。本脚本不上传源码、不修改系统安全设置。

将完整项目复制到 Mac，不要复制 Windows 的 `.venv`、`build`、`dist`。在项目目录打开终端：

```sh
uv sync --locked
uv run pytest
uv run python scripts/build_macos.py
```

输出位于新建的 `dist/macos-架构-时间戳/`：`桌面清单.app` 和 `桌面清单-macOS-架构.dmg`。打开 DMG 后，把应用拖入 Applications。安装后的应用自带 Python，用户不需要安装 Python 或 uv。

默认按构建时 Python 的架构打包：Apple 芯片为 arm64，Intel 为 x86_64。两个版本应分别在对应架构环境构建和验证；不要将其中一种标成通用版。Apple 芯片上应使用原生 arm64 Python，避免意外在 Rosetta 下构建 Intel 版。

## 与 Windows 的差异

- 数据路径：`~/Library/Application Support/DesktopTodo/todo.db`，不存进应用包。
- 关闭窗口隐藏到菜单栏图标；菜单栏图标中选择“退出”彻底关闭。无托盘时关闭即退出。
- Mac 首版不自动写登录启动项，程序内该项禁用；如需要，可在系统设置的登录项中添加应用。
- 本地数据库不自动与 Windows 同步。迁移时先完全退出两端程序并做好备份。

## 签名、公证与验收边界

默认使用 PyInstaller 的临时签名（ad-hoc），不等于 Apple Developer ID 签名或公证。外部分发的应用可能被 Gatekeeper 阻止。正式分发需 Apple 开发者身份、签名与公证；不要通过关闭系统安全机制解决。可通过环境变量 `MACOS_CODESIGN_IDENTITY` 指定钥匙串中已有的签名身份，脚本不会请求或保存证书密码，也不自动提交公证。

脚本只验证签名结构、打包模块导入和 DMG 结构，不等于完成 GUI 验收。Mac 实机仍需检查：启动、菜单栏恢复和退出、重复启动、窗口置顶、输入中文、任务持久化、年月弹窗、点击外部关闭、透明圆角、Retina 显示、拖入 Applications 后启动及系统安全提示。

参考：[PyInstaller 构建说明](https://www.pyinstaller.org/en/stable/usage.html)、[macOS 架构与签名](https://pyinstaller.org/en/stable/feature-notes.html)。
