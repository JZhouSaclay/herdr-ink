# 单格微型落叶光标

版本：`ink-cursor-particles-v1`。

默认光标为七片极小的墨绿叶子，在一个字符格里错落地随风飘下、无限循环。24 帧、每帧 100ms，透明背景；叶子像素覆盖率约 2.7%–3.3%，可以叠在现有文字上。只重绘光标图层，不刷新整段对话，也不改输入文字和列宽。

动画每一帧都在图像命令之后重新写回 Pi 的文字光标坐标。原生硬件开关保留开启来取消反色方块，实际硬件竖线隐藏，由叶群代替；原生文本位置和 CURSOR_MARKER 保留。图层会随焦点标记、覆盖层、终端停止和重载隐藏/清理。

设计预览：`/Users/jiezhou/herdr-ink-study/ink-cursor-leaf-preview.gif`。这是设计示意，叶群叠在“留”字上，并非原生窗口截图。18 项光标、图片清理、动效生命周期、footer 和输入框检查通过；另用独立后台 Pi 验证位置与重载，不切换工作窗口。中文输入法的实际候选窗仍需在当前会话加载后使用确认。

当前会话在回复结束后输入 `/reload` 加载。配置文件是 `/Users/jiezhou/.pi/agent/pretty-tui.json`：

- `"inkCursor": "leaf"`：循环微型叶群，默认。
- `"inkCursor": "ink"`：静态干笔墨痕。
- `"inkCursor": "bar"`：此前修正位置的细竖线。
- `"inkCursorMotion": false`：保留静态叶群，停止动画。

本次备份仅覆盖 pretty-tui，保留当前 Herdr 布局和其他正在修改的界面文件。扩展完整快照在 `/Users/jiezhou/herdr-ink-study/integrations/pretty-tui-cursor-particles/`；原有 v17、v18 和光标 fix2 标签与恢复包继续保留。

恢复包：`/Users/jiezhou/herdr-ink-study/.checkpoints/ink-cursor-particles-v1.zip`。检查后加 `--apply` 恢复扩展，覆盖前自动备份：

```bash
python3 /Users/jiezhou/herdr-ink-study/scripts/restore_ui_checkpoint.py --archive /Users/jiezhou/herdr-ink-study/.checkpoints/ink-cursor-particles-v1.zip
```
