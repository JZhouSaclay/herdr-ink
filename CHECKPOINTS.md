# 稳定版本存档与恢复

这份存档固定了当前认可的 v17：水墨小物件、会话名卡片、未选中用第二种墨痕、选中用第一种墨痕并播放仙鹤、略加深的墨色和竹简。

## 已保存的位置

- Git 仓库：`/Users/jiezhou/herdr-ink-study`
- 固定标签：`ink-study-v17`
- 独立恢复包：`/Users/jiezhou/herdr-ink-study/.checkpoints/ink-study-v17.zip`
- Git 完整备份：`/Users/jiezhou/herdr-ink-study/.checkpoints/ink-study-v17.bundle`
- 存档校验：`/Users/jiezhou/herdr-ink-study/.checkpoints/SHA256SUMS`

标签固定指向这一版。后续优化继续提交到 main，不移动这个标签。

这都是本机存档。ZIP 和 bundle 可以另外复制到移动硬盘或云盘，防止整台机器或目录丢失；目前没有上传到任何远端。

## 怎么恢复窗口

可以直接对助手说：“恢复到 ink-study-v17”。

也可以先运行只检查、不写入的命令：

```bash
python3 /Users/jiezhou/herdr-ink-study/scripts/restore_checkpoint.py --archive /Users/jiezhou/herdr-ink-study/.checkpoints/ink-study-v17.zip
```

确认恢复时加 `--apply`：

```bash
python3 /Users/jiezhou/herdr-ink-study/scripts/restore_checkpoint.py --archive /Users/jiezhou/herdr-ink-study/.checkpoints/ink-study-v17.zip --apply
```

脚本逐文件检查 SHA-256，恢复前先把将覆盖的现有文件备份到 `/Users/jiezhou/.config/herdr-app/backups/`。随后恢复六个 ink-* 模块、素材、字体、ink-study 布局和主题，并检查恢复文件。它保留会话、终端、其他模块、个人设置与共享状态。窗口在使用 ink-study 布局时会自动热更新。

这个命令恢复的是窗口中的已安装布局，不会覆盖开发仓库中尚未保存的修改。恢复后如要以 v17 继续开发，应另建分支或工作目录，不要直接硬重置现有工作。

若当前目录内的恢复脚本也被改坏，可把独立 ZIP 解压到新目录，使用其中的 `scripts/restore_checkpoint.py`，并传入同一个 ZIP 路径。

## 怎么查看和继续存档

查看标签与提交：

```bash
git -C /Users/jiezhou/herdr-ink-study log --oneline --decorate -10
git -C /Users/jiezhou/herdr-ink-study tag --list
```

查看后续版本相对于当前稳定版改了什么：

```bash
git -C /Users/jiezhou/herdr-ink-study diff ink-study-v17 -- mods layouts themes scripts
```

之后每当满意一个阶段，就让助手“把现在这版再做一个 Git checkpoint”，使用新的提交与标签，并重新核对正在运行的窗口、生成对应的校验清单和独立恢复包。当前 `checkpoint-manifest.json` 只描述 v17，不应原样用于其他版本。

## Git 仓库本身损坏时

bundle 保存了本次所有 Git 提交和标签。可以恢复到一个新目录：

```bash
git clone /Users/jiezhou/herdr-ink-study/.checkpoints/ink-study-v17.bundle /Users/jiezhou/herdr-ink-study-recovered
```

历史截图、源码、生成脚本和必要字体随 Git 存档保存；运行时缓存、测试窗口、本机终端记录与凭据不纳入此存档。

## v18 待验收版本

后续 UI 优化另存为 `ink-study-v18-preview`，原 `ink-study-v17` 不移动。本次涉及 pretty-tui 扩展，完整回退请使用新恢复包中同时包含两部分的脚本；详见 `/Users/jiezhou/herdr-ink-study/V18-REVIEW.md`。
