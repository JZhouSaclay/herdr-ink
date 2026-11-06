# 水墨光标候选版

修复标签：`ink-study-v18-cursor-fix2`。初版 `ink-study-v18-cursor` 仍保留。原 `ink-study-v17`、`ink-study-v18-preview` 不移动。

输入框默认使用不闪烁的墨绿细竖线（#58695b）。Pi 改用原生硬件光标，文字内容、列宽、CURSOR_MARKER 与输入法定位沿用原实现。另修复 footer 图像层嵌套 DEC 保存/恢复光标的错误，避免原生光标停在背景图层的位置。

已有 Pi 会话需在空闲时 `/reload` 加载；不需要重启。上次自动重载守卫跳过了当前会话，因此不把排队当作已生效。新会话直接使用新版。

可在 `/Users/jiezhou/.pi/agent/pretty-tui.json` 设置 `inkCursor`：

- `bar`：细竖线，默认。
- `underline`：下划线。
- `block`：原生方块。
- `default`：保留 Pi 原来的反色光标。

只在 Herdr 开启 inkStyle 且浅色外观时接管光标，退出/重载会恢复原硬件开关与终端默认形状、颜色。

原生样例验证了输入一个字母后细竖线在文字右侧、输入框内；15 项光标、footer 与输入框检查通过。

完整包：`/Users/jiezhou/herdr-ink-study/.checkpoints/ink-study-v18-cursor-fix2.zip`。

检查恢复（不写入）：

```bash
python3 /Users/jiezhou/herdr-ink-study/scripts/restore_ui_checkpoint.py --archive /Users/jiezhou/herdr-ink-study/.checkpoints/ink-study-v18-cursor-fix2.zip
```

加 `--apply` 恢复此版；用 `--version ink-study-v18` 或 `--version ink-study-v17` 可恢复相应历史版本。覆盖前自动备份，保留会话和个人设置；恢复后当前 Pi 仍需 `/reload`。

本次修复：Pi 的 `/reload` 在扩展初始化后重新应用 showHardwareCursor=false；初版只按样式缓存跳过校正，因而当前会话可能仍见黑方块。现改为每次编辑器渲染检查开关。原生夹具实际重载后又强制关闭开关，下一帧重新开启，结果见 `/Users/jiezhou/herdr-ink-study/cursor-reload-proof.json`。

fix2：截图 m00515 证明 fix1 原生光标仍在框左上角。修正图片注入顺序：所有 Kitty 图层绘制放在 Pi 最终 CUP 与光标显隐指令之前，保证文字和 IME 的实际坐标最后生效，不依赖 DEC 保存槽。真实 Pi 终端记录检查输入 abc、向左两格、换行并输入 x，各帧最终坐标与 Pi CURSOR_MARKER 一致；见 `/Users/jiezhou/herdr-ink-study/cursor-position-proof.json`。本次系统锁屏，窗口截图为缓存，已丢弃，不将其宣称为本次视觉验收。当前会话仍需 /reload 后由用户确认。
