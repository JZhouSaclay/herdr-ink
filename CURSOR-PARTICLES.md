# 一个汉字宽的落叶光标

版本：`ink-cursor-particles-v3`。

默认光标为七片取自指定 SVG 的水墨柳叶，在一个汉字宽（两个终端半角列）内从右上往左下错落地飘落、无限循环。24 帧、每帧 100ms，透明背景；叶子像素覆盖率约 8.6%–13.7%，可以叠在现有文字上。只重绘光标图层，不刷新整段对话，也不改输入文字和列宽。

动画每一帧都在图像命令之后重新写回 Pi 的文字光标坐标。原生硬件开关保留开启来取消反色方块，实际硬件竖线隐藏，由叶群代替；原生文本位置和 CURSOR_MARKER 保留。图层会随焦点标记、覆盖层、终端停止和重载隐藏/清理。

设计预览：`/Users/jiezhou/herdr-ink-study/ink-cursor-leaf-v3-preview.gif`。这是设计示意，叶群叠在“留”字上，并非原生窗口截图。19 项光标、图片清理、动效生命周期、footer 和输入框检查通过；初版曾用独立后台 Pi 验证位置与重载。本版修改图像尺寸与叶片大小，增加了右边缘边界检查，定位仍沿用原生坐标。中文输入法的实际候选窗仍需在当前会话加载后使用确认。

当前会话在回复结束后输入 `/reload` 加载。配置文件是 `/Users/jiezhou/.pi/agent/pretty-tui.json`：

- `"inkCursor": "leaf"`：循环微型叶群，默认。
- `"inkCursor": "ink"`：静态干笔墨痕。
- `"inkCursor": "bar"`：此前修正位置的细竖线。
- `"inkCursorMotion": false`：保留静态叶群，停止动画。

本次备份仅覆盖 pretty-tui，保留当前 Herdr 布局和其他正在修改的界面文件。扩展完整快照在 `/Users/jiezhou/herdr-ink-study/integrations/pretty-tui-cursor-particles/`；原有 v17、v18 和光标 fix2 标签与恢复包继续保留。

恢复包：`/Users/jiezhou/herdr-ink-study/.checkpoints/ink-cursor-particles-v3.zip`。检查后加 `--apply` 恢复扩展，覆盖前自动备份：

```bash
python3 /Users/jiezhou/herdr-ink-study/scripts/restore_ui_checkpoint.py --archive /Users/jiezhou/herdr-ink-study/.checkpoints/ink-cursor-particles-v3.zip
```

v2 根据实际截图扩大范围：原先一个半角格只有约半个汉字宽，现为一个汉字宽；叶片加大并加深墨色，轨迹横向铺开。最右一列自动缩到剩余宽度，定位不向左偏移。

v3 使用用户提供的 `/Users/jiezhou/herdr-ink-study/candidates/ink-generation-D-F/D-ink-vector.svg`，原样备份到 `/Users/jiezhou/herdr-ink-study/reference/cursor-willow-D.svg`。由 resvg 渲染真实路径，保留原叶形与浓淡笔触，缩小时增强淡墨的可见度。七片柳叶走平行而略错开的右上至左下轨迹，并轻微转动；所有非循环跳转的步骤都检查为 x 减小、y 增大。放大示意见 `/Users/jiezhou/herdr-ink-study/ink-cursor-leaf-v3-detail.gif`。
