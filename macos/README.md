# 每日便签

仅本机使用的中文 macOS 桌面任务便签。Swift + AppKit 窗口与原生毛玻璃，SwiftUI 内容，SQLite 存储，无第三方运行时依赖、账号、联网或屏幕采集。

[下载 Apple 芯片版](https://github.com/han944763-sys/desktop-todo/releases/tag/macos-v1.0.0) · [返回项目首页](../README.md)

## 使用

安装后从「应用程序」打开「每日便签」。点击「今日待办」右侧加号展开输入栏，输入文字并回车添加，提交后自动收起。再次点击加号位置的关闭图标或按 Escape 可收起，未提交文字会保留到本次应用退出。主界面不显示日期，历史日历入口保留在顶栏。点击圆圈完成，任务移到下方并划线；再次点击可恢复。任务右侧菜单可编辑或删除，底栏提供撤销删除。双击任务文字也能编辑。

- 顶部图钉：切换置顶；齿轮：设置；日历：查看历史。
- 底部「每日重复」：添加、修改、停用固定事项。创建时生成今天的任务；改名只影响下一次生成，停用不删除已经生成的任务。
- 昨日未完成任务只留在历史，不顺延。应用打开、跨日或唤醒时生成当天重复任务，不补关机期间的漏打卡。
- 顶部分类切换：「短期 · 今日」显示当日待办与已完成；「长期目标」单独展示持续计划，避免混在一起。
- 长期目标：目标、手动进度、下一步行动。下一步可「加入今日」；同一项目的相同行动一天一条，点击不会重置已完成状态。编辑项目可看最近 20 条完成记录。
- 默认窗口约 300 × 420，最小约 280 × 300，可移动、缩放，内容多时滚动，关闭只隐藏。菜单栏勾选图标可重新显示或完全退出。
- 首次启动尝试开启登录自启动，状态以系统设置为准。应用设置可关闭；如果系统要求批准，点「打开登录项设置」。
- 外观跟随系统，使用原生毛玻璃，减少透明度时使用实底；并非实时黑白反色。

## 构建与检查

需要 macOS 13+ 和 Swift 5.9+（Xcode Command Line Tools 即可）。在仓库根目录运行：

```sh
cd macos
swift build
swift run TaskCoreChecks
python3 scripts/check-cli.py
bash scripts/install.sh
```

安装脚本先构建 release 和本机 ad-hoc 签名，再安装到当前用户 Applications；不覆盖任务数据库。更新前先从菜单栏退出应用，旧 `.app` 自动备份。`swift test` 不是本项目的测试入口，独立检查程序不依赖完整 Xcode 的 XCTest SDK。

## Codex 与手动填写共用数据

以下命令使用源码安装脚本的路径。若通过 DMG 将应用拖入系统「应用程序」，将路径中的 `$HOME/Applications` 改为 `/Applications`。

```sh
"$HOME/Applications/每日便签.app/Contents/MacOS/tasknote" help
"$HOME/Applications/每日便签.app/Contents/MacOS/tasknote" add "阅读 20 分钟"
"$HOME/Applications/每日便签.app/Contents/MacOS/tasknote" list
"$HOME/Applications/每日便签.app/Contents/MacOS/tasknote" repeat "散步"
"$HOME/Applications/每日便签.app/Contents/MacOS/tasknote" projects
```

命令返回 JSON，支持完整任务 ID 的完成、恢复、编辑、删除、撤销，以及项目字段更新。通过 `help` 查看完整指令。界面每秒刷新数据；请调用 CLI，不要直接改数据库。测试可传 `--db /临时目录/tasks.db`，不影响真实任务。

## 数据与恢复

数据库：`~/Library/Application Support/DailyTaskNote/tasks.sqlite3`。使用 WAL、外键、唯一约束、事务和 busy timeout，GUI/CLI 的修改按记录及字段更新。两方同时修改同一个字段时，最后提交的值生效。项目编辑器只提交实际改动字段。

备份前退出应用并停止 CLI，再复制整个 `DailyTaskNote` 目录（包括可能存在的 `-wal`、`-shm` 文件）。不要只复制正在使用的主数据库。数据库检查失败会提示路径并保留文件，不会静默重建。无自动云同步。

删除任务采用软删除，可在界面当前会话中撤销，或用 CLI 的 `restore ID` 恢复。窗口位置、置顶状态和首启标记存储在应用偏好中。

卸载：先在设置关闭登录自启动，退出并移走 `.app`；任务数据保留，除非你另外主动删除数据目录。

## 官方接口依据

- [AppKit 原生背景融合](https://developer.apple.com/documentation/appkit/nsvisualeffectview/blendingmode-swift.enum/behindwindow)
- [SMAppService 登录自启动](https://developer.apple.com/documentation/servicemanagement/smappservice)

当前安装为本机签名版本，未做 App Store 分发或 Developer ID 公证；实际注销/重新登录的启动行为需要在用户方便时验证。
