# Ink Study v18：减少常驻信息并补齐水墨细节

用户授权：直接实现统一水墨方案，保留 v17 的可恢复存档，次日验收。

- 单 pane 去掉路径栏（lone=false）；分屏时保留 hover 路径与分屏、缩放、关闭入口，不再增加固定路径行。
- 去掉底部 28px This computer / agents 常驻栏。需要关注的 blocked 数与远程主机名出现在现有侧栏 footer 内，不新增常驻行。完整路径在顶部悬停栏；命令面板仍可通过键盘和侧栏搜索进入。
- 左上空白边缘增加淡竹，保留原有右下山水，正文区域维持干净。
- pretty-tui 的 opt-in inkStyle 下，仅转换 footer 容器的三个图标：✦ 小墨星、🧠 书卷、⚡ 风叶。使用已有 Kitty 图层，保留原字符宽度、全部状态文字、ANSI 语义颜色、鼠标和复制行为。非 Herdr、无 Kitty、暗色主题或 inkStyle 关闭时沿用原渲染。
- 图层与现有背景图层共同处理同步刷新、覆盖层隐藏、图像重置和 session_shutdown 清理。图标资产固定生成，不在渲染热路径里读盘。
- 新版需 /reload 更新 pretty-tui 闭包与原型，外层 Herdr 布局可直接热更新；不需要 restart。
- 不改其他 agent 的会话、不重启终端、不发送模型请求。使用本地 synthetic transcript 验证新 footer，并检查真实窗口的布局。
- 本机 pi-extension 仓库有既存未提交工作，完整保留。只把本次精确文件与恢复所需原始快照纳入 ink-study 的新检查点，不夹带其他改动提交。

验证：footer 字符宽度/内容与绘图清理、三种 icon 原生截图、空状态与非 Kitty 回退、原生布局检查、hover 路径和分屏操作入口，最后核对 v17 标签未移动。
