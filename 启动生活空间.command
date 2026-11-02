#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
if ! python3 server.py --open; then
  printf '\n启动失败，请查看上面的提示。\n'
  read -r '?按回车退出…'
  exit 1
fi
