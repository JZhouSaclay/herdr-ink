# Ink Study：原生细竖线输入光标

用户希望替换输入框中的黑色方块。Pi 默认 showHardwareCursor=false，焦点字符经 fake-cursor marker 变成反色方块，与 Herdr 自身的 cursor 颜色不同。

方案：仅在启用 inkStyle 的 Herdr 浅色 UI 中，使用 Pi 的 setShowHardwareCursor(true)，由原生光标替代反色字符；发送标准 DECSCUSR 6（不闪烁竖线）与 OSC 12 墨绿 #58695b。保持 CURSOR_MARKER、输入文字和列宽，沿用原生中文 IME 定位。

通过 inkCursor 配置支持 bar / underline / block / default；默认 bar，default 保留原来的行为。关闭水墨或退出/重载时恢复原硬件光标开关，并重置形状和终端颜色。只对本扩展触及的 TUI 实例操作。

检查：开关与原值恢复；切换形状不重复写入；异常/不支持的终端不改变光标；原生标记与字符宽度不变；现有 footer、输入框和气泡测试。保存独立候选 Git 标签，不移动已存档的 v17/v18。

上一次延迟重载没有执行：检测时会话已不再符合 idle 条件，守卫跳过。本轮重新核对原生 hc 的状态和空编辑器条件；如无法可靠自动重载，明确告知使用 /reload，不把已排队当作已生效。

后续用户实测发现初版重载后仍显示反色块。修复点：控制器的缓存条件同时检查硬件开关；每次编辑器渲染在 fake-cursor marker 解析前重新校正。以实际 `/reload` 后强制关闭开关的原生夹具和新增回归测试验证。
