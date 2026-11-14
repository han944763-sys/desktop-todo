# 每日便签 1.0.0 · macOS

首次公开发布 Swift 原生版。支持每日待办、完成分组、历史日历、每日重复和长期目标，桌面小窗和 `tasknote` 命令行工具共用本机任务数据库。

## 下载和安装

下载 `DailyNote-macOS-arm64.dmg`，适用于 macOS 13 或以上的 Apple 芯片 Mac。打开 DMG，将「每日便签」拖入「应用程序」。

此构建使用 ad-hoc 签名，未经过 Apple 公证。如果系统拦截下载的应用，可在 Mac 上按[源码安装说明](https://github.com/han944763-sys/desktop-todo/tree/macos-v1.0.0/macos#构建与检查)构建安装。

- 文件大小 447,681 字节
- SHA-256 `38ad7a0e18e9a23014efaccf3c05bbea765a9da88697dfc14c256c6928619c13`

## 验证

在 Apple 芯片 Mac 上通过 Debug 和 Release 构建、7 组核心检查以及 CLI 集成测试。已验证 DMG 校验和、挂载后应用签名，以及包内 `tasknote` 对临时数据库的读取。
