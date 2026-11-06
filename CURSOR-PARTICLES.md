# 水墨弯叶光标 v4

版本：`ink-cursor-particles-v4`。

用户要求叶子更小、更弯、飘落更飘逸。本次通过 Magpie 本地图片接口调用已配置的 `codex/gpt-image-2`，以原 D 水墨 SVG 为参考，实际生成一片弯曲的写意柳叶；原画保存在 `/Users/jiezhou/herdr-ink-study/reference/gpt-image-curved-leaf-v4.png`。请求提示词和参考来源保存在同名 `.request.json` 中。没有将程序几何形状当作生图结果。

七片叶子较 v3 缩小约两成，保留一个汉字宽的活动范围，从右上往左下沿弧线飘落。每片有不同的风速变化、摇摆与轻微侧翻。64 帧、每帧 60ms，3.84 秒循环；光标移动时继续当前动画，不从头重播。背景透明，叶片覆盖率约 3.8%–7.3%，可以叠在文字上。只刷新光标图层，不重绘整段对话。

设计动图：`/Users/jiezhou/herdr-ink-study/ink-cursor-leaf-v4-preview.gif`。

放大细节：`/Users/jiezhou/herdr-ink-study/ink-cursor-leaf-v4-detail.gif`。

这是设计预览，并非原生窗口截图。20 项光标、缓存、循环连续性、图层清理、输入框和 footer 检查通过；另外使用独立后台 Pi 检查输入、移动、多行和实际重载后的位置，不切换用户窗口。原生文字坐标和 CURSOR_MARKER 保留，实际中文输入法候选窗仍待当前会话使用确认。

当前会话在回复结束后输入 `/reload` 加载。配置文件是 `/Users/jiezhou/.pi/agent/pretty-tui.json`：

- `"inkCursor": "leaf"`：循环弯叶，默认。
- `"inkCursor": "ink"`：静态干笔墨痕。
- `"inkCursor": "bar"`：细竖线。
- `"inkCursorMotion": false`：静态叶群。

本次备份仅覆盖 pretty-tui，保留当前 Herdr 布局与其他正在修改的界面文件。完整扩展快照位于 `/Users/jiezhou/herdr-ink-study/integrations/pretty-tui-cursor-particles/`；此前 v1、v2、v3 标签与恢复包继续保留。

恢复包：`/Users/jiezhou/herdr-ink-study/.checkpoints/ink-cursor-particles-v4.zip`。先检查，再加 `--apply` 恢复；覆盖前自动备份：

```bash
python3 /Users/jiezhou/herdr-ink-study/scripts/restore_ui_checkpoint.py --archive /Users/jiezhou/herdr-ink-study/.checkpoints/ink-cursor-particles-v4.zip
```
