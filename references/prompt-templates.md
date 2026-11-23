# 提示词模板与手动组装

先完成并复核 [设计 brief](design-brief-schema.md)。把每一份提示词写成可独立粘贴的十段。包裹文字写目标宽高比、生成一张、参考怎么附、负面段如何移入平台字段。默认交付中文与英文指令，每种语言各有 full、minimal、none 三份可选稿。按用户或 brief 的首选模式排在前面。没有代码执行能力时也按本页组装。脚本输出见 [完整提示词示例](../assets/prompt-package.example.md)。

## 十段主模板

将表格中写出的 brief 字段转换为相应的中英文设计描述。把字段提示从成品中去掉。中英文指令使用相同布局、位置和数值。使用 `meta.language` 选择图内字的语种，英文指令内可以保留逐字指定的中文标注。

| 段 | 中文主句 | English pattern | 从 brief 接入 |
| --- | --- | --- | --- |
| 1 总述 | 绘制一张指定竖版比例的完整婚礼手绘提案板，呈现一个婚礼区域。 | Create one complete portrait wedding design concept board presenting a single decor area. Use the specified aspect ratio. | `meta.aspect_ratio` |
| 2 画风与媒介 | 用浅米做旧水彩纸、细针管笔与钢笔轮廓、透明水彩叠色和柔和马克笔。保留纸纹、自然笔触与柔和投影。需要文字时使用清楚的手写字。 | Work on lightly aged ivory watercolor paper with fine pen lines, translucent watercolor washes and restrained marker. Keep visible strokes, soft shadows and legible lettering when required. | `concept.style_keywords`、`concept.mood`。B 类追加 `concept.reference_style.medium` 并优先沿用可见媒介和笔触。 |
| 3 版式 | 留约 4% 安全边距，上区左对齐标题与手绘下划线、主透视、左上说明、右引线。中下区左 2×2 四视图，右竖排特写。底带左材质、右一排色票。 | Leave about 4% safe margins. Build the top-left title and drawn underline, hero perspective, upper-left note and right leaders. Below put the 2×2 views left and stacked details right, with materials and swatches along the bottom. | [版式比例](board-layout-spec.md)、引线数。B 类追加 `concept.reference_style.layout`，按来源保留主要分区关系，补齐所需模块。 |
| 4 主效果图 | 画出指定场地、功能区、光线、主骨架与构件、花艺形态和落点、布艺起止和固定点、焦点与座椅等。把每条引线指向具体构件。 | Depict the setting, area, lighting, main frame and components, floral form and locations, fabric drape and attachment points, focal decor and furniture. Land each leader on its specified part. | `scene`、`structure`、`florals`、`fabrics`、`focal_elements`、`furniture_props`、`callouts[].target` |
| 5 技术图 | 四个小图用同一外包宽、高、进深，统一毫米。说明哪几轴在哪个视图，并列出相同骨架、花艺和布艺的投影关系。数字只在白名单指定位置出现。 | Use the same installation envelope for all views, in millimeters. Identify the axes in each view. Match frame, floral placement, and drapery across the studies. Draw numbers only where the whitelist permits. | `structure.dimensions`、`views` |
| 6 细节特写 | 按栏内顺序逐一放大指定细节，留可读的说明区域。 | Crop each named detail in sequence, retaining clear space for its caption. | `detail_zooms[].subject` |
| 7 图例与色板 | 逐一画指定材质纹理，配一排指定颜色。色名和 HEX 用于调色。 | Draw the listed material chips and place swatches in order. Use names and HEX values as paint instructions. | `materials_legend`、`palette` |
| 8 图内文字清单 | 逐字复制引号内的文字，去掉引号。斜线只表示同位置换行。只写白名单允许的内容。 | Render only the strings in quotation marks, omitting the quotation marks. Slashes indicate a line break at the same position. | 用下节规则生成 `full`、`minimal`、`none`。 |
| 9 参考图作用 | 写清有无附图、保留项、允许更改项、来源类型。 | State how the image is supplied, what carries over, what changes, and which kind of reference it is. | `meta.input_type`、`meta.fidelity_mode`、适配器 |
| 10 负面约束 | 避免照片质感、3D 渲染感、水印、品牌标识、真实可识别人像、额外人物、乱码、清单外字形、无支撑构件、跨视图矛盾和多页拼贴。 | Avoid photographic or 3D-render textures, watermarks, brand marks, real identifiable portraits, extra people, garbled or unlisted text, unsupported objects, inconsistent geometry, and multi-page collages. | 默认约束，可追加已观察到的具体缺陷。 |

## 文字段的组装

- **full**。按从上到下的顺序列出顶端标题、左上说明、右侧引线、四个视图名及六个数字、右栏标题和逐个特写、底部两栏标题及材质条目。用“位置 → `"第一行" / "第二行"`”表示一个块。主图左上首行为“设计说明”或 “Design note”，下接 brief 的说明行。细节、材质和色彩的固定标题分别为“细节放大图”“材质说明”“色彩方案”，英文为 “Detail studies”, “Materials”, “Color palette”。总量至多 28 块。
- **minimal**。仅保留标题和四视图题签，正视题签次行的单位/估算标记，以及六个尺寸数字。其余字区留白，分区、图形和引线保持在位。
- **none**。明确白名单为空，保留空白题签区域、手绘下划线、引线与尺寸线。制止输出文字、数字、字母、伪字和原参考标签。技术数据仍指导几何，按完整模式另交付后期叠字定位清单。
- **估算文字**。正视、侧视、俯视、结构分解对应 “Front elevation”, “Side elevation”, “Plan view”, “Exploded view”。估算时正视题签下增加“尺寸估算 · mm”或 “Estimated · mm”，已有来源值写“单位 · mm”或 “Units · mm”。其余视图共享毫米。按正视宽与高、侧视高与进深、俯视宽与进深排列六个数字。
- **英文标注**。将图内语言改为 `en`，从同一 brief 的 `en` 字段重建第 8 段和叠字清单。可运行 `python3 scripts/build_prompt.py design-brief.json --board-language en --lang both --stdout`。

## 参考段与参数

- **faithful**。写“保留参考图中的结构、花材、配色与空间关系，仅改变表现形式为手绘方案板”。不可见处用 brief 明示的补全。英文写 “Preserve the reference structure, florals, palette and spatial relationships. Change the presentation to a hand-drawn proposal board.”
- **reinterpret**。列出 brief 已更新的主题、配色或构件。保留用户要求继承的风格及不变的空间关系。
- **B 类**。加上“沿用参考图的版式与笔触风格”或 “Carry over the reference board's layout character and stroke style.” 使用 brief 记录的媒介和分区信息。
- **A 类与 C 类**。A 交代由实景或 3D 转绘到针管笔和水彩。C 锁定可见片段，按照 brief 补全遮挡与场地关系。
- **平台适配**。有参考图接口时附一张原图。纯文本时使用解析内容。参数字段单独设置目标竖版比例和一张输出。示例 3:4 可用 1536 × 2048，实际支持值见 [模型适配](model-adapters.md)。有独立负面框时可摘出第 10 段填入。
