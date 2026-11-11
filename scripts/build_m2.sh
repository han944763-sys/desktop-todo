#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "$(uname -s)" != "Darwin" ]; then
    echo "请在 Mac 上运行此脚本。" >&2
    exit 2
fi
if [ "$(uname -m)" != "arm64" ]; then
    echo "请使用 M2 的原生终端，不要通过 Rosetta 运行。" >&2
    exit 2
fi
if ! command -v uv >/dev/null 2>&1; then
    echo "未找到 uv，请按 开始使用-M2.md 安装后重新打开终端。" >&2
    exit 2
fi
uv sync --locked
uv run --locked python -c 'import platform; assert platform.machine() == "arm64", "Python 不是 arm64，请使用原生环境"'
uv run --locked pytest
uv run --locked python scripts/build_macos.py
open dist
