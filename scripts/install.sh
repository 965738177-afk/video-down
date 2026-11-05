#!/bin/bash
set -euo pipefail
# Install isolated Python dependencies and reuse a supported local FFmpeg.
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! "$PYTHON_BIN" -c 'import sys; assert sys.version_info >= (3,10)' 2>/dev/null; then
  if command -v brew >/dev/null; then
    brew install python
    PYTHON_BIN="$(brew --prefix)/bin/python3"
  else
    echo '需要 Python 3.10+。设置 PYTHON_BIN 指向已有 Python，或安装 Python 后重试。' >&2
    exit 1
  fi
fi
if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  if command -v brew >/dev/null; then
    brew install ffmpeg
  elif [[ -z "${FFMPEG_LOCATION:-}" ]]; then
    echo '请安装 FFmpeg，或设置 FFMPEG_LOCATION 指向同时包含 ffmpeg 和 ffprobe 的目录。' >&2
    exit 1
  fi
fi
if [[ -n "${FFMPEG_LOCATION:-}" ]]; then
  "$FFMPEG_LOCATION/ffmpeg" -version >/dev/null
  "$FFMPEG_LOCATION/ffprobe" -version >/dev/null
fi
VIDEO_DOWN_ENV="${VIDEO_DOWN_ENV:-$HOME/.local/share/video-down/venv}"
"$PYTHON_BIN" -m venv "$VIDEO_DOWN_ENV"
"$VIDEO_DOWN_ENV/bin/python" -m pip install --upgrade 'yt-dlp[default]' pycryptodomex
"$VIDEO_DOWN_ENV/bin/python" -m yt_dlp --version
echo "Python installed at $VIDEO_DOWN_ENV/bin/python"
