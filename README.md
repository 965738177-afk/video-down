# video-down

macOS Codex skill，覆盖 Safari 抓取 HLS 链接、yt-dlp 下载与续传、FFmpeg 封装 MP4 和文件检查。

## 安装 skill

```bash
git clone https://github.com/965738177-afk/video-down.git ~/.codex/skills/video-down
bash ~/.codex/skills/video-down/scripts/install.sh
```

需要 Python 3.10+ 与 FFmpeg。安装脚本创建独立 venv，安装 yt-dlp 和 pycryptodomex。已有 Homebrew 时可补装 Python 与 FFmpeg。没有 Homebrew 时请先提供工具，可设置 PYTHON_BIN、FFMPEG_LOCATION 与 VIDEO_DOWN_ENV。

重新开启 Codex 会话后，说“使用 video-down 下载 Safari 正在播放的视频”。Safari 抓链由 Codex 的 computer-use 工具操作可见的控制台或网络面板。下载脚本接收已确认的 URL，不会单独控制 Safari。详见 [SKILL.md](SKILL.md)。

## 手动下载

```bash
~/.local/share/video-down/venv/bin/python \
  ~/.codex/skills/video-down/scripts/download.py 'https://example.com/index.m3u8' \
  --referer 'https://example.com/play' --job video-001 --output ./outputs
```

按需加 --origin、--user-agent、--ffmpeg-location。刷新签名后续传须核对视频身份、时长及分片数，保留相同 job。不同视频使用不同 job。

默认遇到损坏分片停止。显式 --recover-ts 会恢复异常 AES 分片中对齐的完整 TS 包，丢弃损坏尾部数据并记录恢复次数，可能产生局部音画异常。详见 [Safari 抓链说明](references/safari.md)。

已用本机合成 HLS 视频验证下载、封装与 ffprobe 检查。原始工作流曾下载 AES-128 视频，整理后的恢复选项仍需按实际异常视频检查。验证报告只确认容器与轨道，不代表完整解码无错误。脚本不绕过 DRM、登录或付费限制。

依赖来自 [yt-dlp](https://github.com/yt-dlp/yt-dlp)、[FFmpeg](https://ffmpeg.org/) 和 [PyCryptodome](https://www.pycryptodome.org/)。依赖在安装时获取。
