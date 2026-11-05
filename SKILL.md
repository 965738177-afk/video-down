---
name: video-down
description: 在 macOS Safari 中为用户正在播放的视频查找真实 HLS/m3u8 请求，用 yt-dlp 下载、断点续传并封装成 MP4，检查音视频与异常分片。
---

# Safari 视频下载

使用用户指定的播放页和输出位置。先检测 Python、yt-dlp、FFmpeg 与 ffprobe。需要安装时运行 `scripts/install.sh`，已有工具可直接复用。此 skill 需要可控制 Safari 的 computer-use 工具。缺少工具时可指导用户复制网络请求，不能声称已经自动抓链。

## 找到实际播放地址

按 [references/safari.md](references/safari.md) 读取 Safari 中当前视频的实际资源请求。优先复用已在播放的页面，连接右侧浏览器失败时检查 Safari。不要用相邻 ts 路径猜测 m3u8。记录播放页、播放列表、Referer 和必要的请求头，仅在本地使用。

## 下载与续传

使用安装脚本输出的 Python 执行下载工具。已有 Python 环境须具备 `yt-dlp` 和 `pycryptodomex`。

```bash
python scripts/download.py '完整m3u8地址' \
  --referer '播放页地址' --job video-001 --output ./outputs
```

脚本将所有分片下载后用 FFmpeg 封装 MP4，通过 ffprobe 验证音视频与时长后交付。临时文件和恢复记录保存在输出目录的 `.video-down/<job>` 中。失败时保留断点。相同 job 的已交付 MP4 会被验证和复用。

403 时重新抓取正在播放的页面地址，核实属于同一视频后用同一 job 重试。不同视频必须换 job。对比页面内容、时长及分片总数，变化时不要拼接旧断点。最多刷新链接并重试两次，仍失败则说明具体阻塞。不得绕过登录、付费或 DRM。

AES 填充错误先隔离报错分片的缓存，再下载该分片。保留完整 `.part` 和 `.ytdl`。正常恢复失败时，可显式传入 `--recover-ts`，仅保留异常分片中逐包验证通过的完整 MPEG-TS 包。该模式属于有损恢复，必须向用户披露恢复次数和可能的局部音画异常。默认严格失败，不跳过分片。

## 检查与交付

读取生成的 `.verification.json`，确认 ffprobe 返回有效视频、时长、分辨率及音轨。根据播放页时长核对成片，并使用 FFmpeg 检查损坏位置附近及首尾解码。验证不完整时如实说明。完成后提供 MP4 文件链接、时长、分辨率及已知缺陷。

分享此 skill 时只上传本目录的代码与说明。播放链接、签名、Cookie、用户视频及运行日志保留在本地。
