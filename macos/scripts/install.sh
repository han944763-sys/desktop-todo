#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/build.sh
DEST="$HOME/Applications/每日便签.app"
if pgrep -x DailyNote >/dev/null; then
    echo '应用正在运行，请从菜单栏退出每日便签后重试安装。' >&2
    exit 1
fi
mkdir -p "$HOME/Applications"
if [ -d "$DEST" ]; then
    BACKUP="$HOME/Applications/每日便签-backup-$(date +%Y%m%d-%H%M%S).app"
    mv "$DEST" "$BACKUP"
fi
ditto 'build/每日便签.app' "$DEST"
open "$DEST"
echo "已安装：$DEST"
