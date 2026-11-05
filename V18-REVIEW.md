# v18 待验收版本

本次候选标签：`ink-study-v18-preview`。已认可的 `ink-study-v17` 保持原提交不动。

这次包括外层 Herdr 布局与 Pi 的 pretty-tui 两部分：

- 单窗口移除固定路径行；分屏保留悬停路径和操作入口。
- 移除底部机器与 Agent 统计栏；待确认数量、远程机器名收进现有侧栏 footer。
- 输入框 footer 中的模型、思考、速度图标换成透明底的墨星、书卷、风叶；状态文字与列宽保持不变。
- 左上边缘添淡竹，与原来的右下山水相映。

原生本地样例已验证图像效果与字符对齐。现有会话要在空闲时 `/reload` 才能加载 pretty-tui；不需要 `/restart`。本次只为当前 t12 安排一次空闲后重载，结果写入 `/Users/jiezhou/herdr-ink-study/.checkpoints/v18-reload-result.json`；其他已打开会话下次自行 `/reload` 或新开会话后使用新版图标。

本次原生样例与新增分屏均已清理，焦点恢复至原会话。锁屏后 Herdr 截图会返回缓存帧，因此分屏使用命令返回与布局检查验证，未把缓存帧当成新的分屏截图。

## 完整恢复包

文件：`/Users/jiezhou/herdr-ink-study/.checkpoints/ink-study-v18-preview.zip`

包内同时保存 v18 的 pretty-tui 和修改前的完整扩展快照，并保留 v17 外层布局的两个变化文件。因此既能恢复新版，也能完整回退到此前认可的 v17 视觉。

先检查，不改文件：

```bash
python3 /Users/jiezhou/herdr-ink-study/scripts/restore_ui_checkpoint.py --archive /Users/jiezhou/herdr-ink-study/.checkpoints/ink-study-v18-preview.zip
```

恢复 v18：

```bash
python3 /Users/jiezhou/herdr-ink-study/scripts/restore_ui_checkpoint.py --archive /Users/jiezhou/herdr-ink-study/.checkpoints/ink-study-v18-preview.zip --apply
```

完整回退 v17（包含旧的 footer 图标）：

```bash
python3 /Users/jiezhou/herdr-ink-study/scripts/restore_ui_checkpoint.py --archive /Users/jiezhou/herdr-ink-study/.checkpoints/ink-study-v18-preview.zip --version ink-study-v17 --apply
```

恢复前会备份将覆盖的两部分文件到 `/Users/jiezhou/.config/herdr-app/backups/`，并逐文件校验。会话、终端、共享状态、个人设置与其他扩展保留。Herdr 布局热更新；Pi 会话需空闲时 `/reload`。如果工作目录本身被改坏，可在新目录解压 ZIP 后使用包内恢复脚本。

`/Users/jiezhou/herdr-ink-study/integrations/pretty-tui-v17/` 是修改前的完整快照；`/Users/jiezhou/herdr-ink-study/integrations/pretty-tui-v18/` 是本次版本。部署目标是现有软链指向的 `/Users/jiezhou/Desktop/公司其他/pi-extension/extensions/pretty-tui/`，恢复脚本按文件写入，保留软链与该仓库的其他工作。

## 复查

```bash
python3 /Users/jiezhou/herdr-ink-study/scripts/verify.py
node --test /Users/jiezhou/herdr-ink-study/integrations/ink-footer.test.mjs /Users/jiezhou/herdr-ink-study/integrations/ink-style.test.mjs
```

生成图标和背景的脚本分别是 `/Users/jiezhou/herdr-ink-study/scripts/make_footer_icons.py` 与 `/Users/jiezhou/herdr-ink-study/scripts/make_corner.py`。原始图形为本次自绘；Kitty 图像层不改变真实状态数据，不发送模型请求。
