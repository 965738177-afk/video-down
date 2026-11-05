# Safari 抓链

用当前环境提供的 computer-use API 获取 Safari，每次动作前后读取最新界面。快捷键 `⌥⌘C` 可显示 JavaScript 控制台，也可从“开发”菜单进入。不要在终端用 AppleScript 或浏览器私有接口代替受控 UI。

优先在正在播放的页面读取已加载资源，避免刷新导致失去播放状态。有些网站在检查器开启或刷新时跳转，先确认页面 URL。

在可见的控制台提示输入以下只读表达式，回车后从结果复制完整 URL。

```javascript
performance.getEntriesByType('resource')
  .filter(e => e.name.split('?')[0].endsWith('.m3u8'))
  .map(e => e.name).join(' | ')
```

结果为空时使用 Safari 网络面板。筛选是左上角“过滤完整 URL”，底部搜索框只搜索控制台。保持“全部”类型，播放视频后观察新增的 Fetch/XHR 和媒体请求。用响应以 `#EXTM3U` 开头确认无后缀播放列表。

可用下列只读表达式列出近期分片资源，帮助定位来源。

```javascript
performance.getEntriesByType('resource')
  .filter(e => /m3u8|\.ts(?:\?|$)|\.m4s(?:\?|$)/i.test(e.name))
  .slice(-20).map(e => e.name).join(' | ')
```

`video.currentSrc` 有时只是 `blob:`，需要追溯真正的播放列表。相同目录中的不同资源可能使用不同签名，不能把 ts 的签名直接拼到 m3u8。

下载发生 403 时使用最新播放请求，同时核对 Referer、Origin 和 User-Agent。只有确实需要登录状态时才在本机按授权使用 Cookie，不写入仓库。
