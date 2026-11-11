# 素材来源

- 墨痕、备用墨痕与旋转墨圈：从用户提供的参考图提取，保留实际笔迹，去除底色并调整透明度与画布比例。参考原图保存在 `reference/ink-reference.png`。这些笔触不是本项目原创绘画。
- 竹材及束绳纹理：Titus Tscharntke，Bamboo table texture；作者将照片置于公共领域。本项目裁切、旋转、调亮并重组为单片竹简。
  - 来源页面：https://commons.wikimedia.org/wiki/File:Bamboo_table_texture.jpg
  - 原照片：https://upload.wikimedia.org/wikipedia/commons/7/79/Bamboo_table_texture.jpg
  - 本地来源文件：`reference/bamboo-table.jpg`
- 山水背景与纸纹：由本项目固定种子的 Python 脚本生成。
- 原生模块：基于本机 Herdr 0.1.13 自带模块独立修改，记录 `cloned_from`；没有使用 Traveler 的人物、建筑或地图素材。

- 仙鹤：鹤身与羽毛从本次用户提供的水墨画参考提取，原图在 `reference/crane-ink-reference.png`。分层蒙版与扇翅插值合成由脚本完成；当前仅用原动作01–06，末尾保持飞行姿态。这些水墨笔迹不是本项目原创绘画。

- v9细分隔线和小印边缘均由原参考墨迹的覆盖纹理生成；SVG水墨环保留原扫描的缺口与浓淡。竹简比例调整仍沿用原公共领域摄影。

水墨数字 1–15 由本项目按手写中心线、笔压与干笔纹理生成，透明底 PNG，生成脚本为 scripts/make_numbers.py。

字体：LXGW WenKai Mono Regular v1.530，由 lxgw 维护，SIL Open Font License 1.1。随包保留原字体及 OFL.txt；来源与 SHA-256 见 font-source-v12.json。宋体使用 macOS 已有 Songti SC，未复制或分发系统字体文件。

Hede Ink Mono 为 LXGW WenKai Mono v1.530 的字宽微调衍生版，已重命名以遵守保留字体名称条款，原版权及 OFL.txt 保留；仅水平 advance 增加1.6%，字形轮廓未变。
何德字标以 Zhi Mang Xing（https://github.com/google/fonts/tree/main/ofl/zhimangxing，SIL OFL 1.1）两字字形渲染为透明 PNG，加固定干笔纹理；源字体子集及原许可置于 reference/Zhi-Mang-Xing-brand.ttf、reference/zhimangxing-OFL.txt。


## 侧栏小物件 v15

15种古风小物件为本项目原创程序绘制，未使用第三方图标或摄影。SVG由 scripts/make_space_objects.py 描述，rsvg-convert 输出256×256透明PNG，在界面以24px显示；柔和阴影与渐变表现棋子、笔、卷轴等物件体积。字体未嵌入物件素材。


## 毛笔水墨物件 v16（当前版）

替代v15的渐变矢量外观。15种物件均由项目脚本原创绘制，以插值笔路、动态笔压、分叉笔毫、透明墨层叠加和纸面颗粒模拟水墨；无第三方插画或素材，不依赖外部生成服务。输出为256×256透明PNG，实际显示24px。

选中标签竹叶标记由本项目的贝塞尔叶形、叶脉与固定干笔纹理生成，透明 PNG；脚本 scripts/make_tab_leaf.py。

标签鹤羽F：来自Hugging Face官方公开 black-forest-labs/FLUX.1-schnell 文生图原画，提取羽毛主体后通过vtracer转换为多层灰阶路径SVG；运行资源 mods/ink-chrome/art/tab-feather-v22.svg。生成请求、原画及转换对照保存在 candidates/ink-generation-D-F。

GPT Image 2 鹤羽：通过用户配置的Magpie codex/gpt-image-2生成，原生透明PNG；界面资源tab-feather-gpt-v23.png。生成请求及原图保存在 candidates/gpt-image-2-crane-feather，未使用前一版FLUX原画。
