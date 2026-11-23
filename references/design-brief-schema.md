# Design brief 字段规范

从 [空模板](../assets/design-brief.template.json) 填写 UTF-8 JSON，或对照 [完整示例](../assets/design-brief.example.json)。模板的空字符串和 `null` 是待采集输入。将必填空值补齐后再验证。重复键和未定义键会报错。

## 公共类型

- **双语词条**。使用 `{"zh":"木框","en":"Timber frame"}`。为两个文本保留同一含义，每个值都是无换行、无首尾空格的非空字符串。用数组表达多行，翻译不要加进未经确认的花材或结构细节。
- **尺寸**。正整数，单位毫米。记录主装置的安装外包宽、高、进深。纳入附着花艺、布艺、底座等外伸，独立椅子、通道地花、独立地台和留空净距另记。
- **推断路径**。使用从根开始的 [JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901)，例如 `/structure/dimensions/height_mm` 或 `/fabrics/0/fixing_points`。数组从 0 开始。

## 字段

除表中明确可省略的字段，所有键均须提供。

| 字段 | 类型与取值 | 填写要求 |
| --- | --- | --- |
| `meta.input_type` | `A`、`B`、`C` | 实景或 3D、已有手绘板、局部或信息不足。L3 按用户描述来源判型。 |
| `meta.fidelity_mode` | `faithful`、`reinterpret` | 默认 faithful。主题明确改动时用 reinterpret，并把目标值落实到相关字段。 |
| `meta.aspect_ratio` | 如 `"3:4"` | 两个正整数以冒号分隔，宽小于高。 |
| `meta.language` | `zh`、`en` | 图内文字语种，默认 zh。独立于包裹提示词的指令语种。 |
| `meta.text_mode` | `full`、`minimal`、`none` | 本次优先使用的图面文字模式，默认 full。 |
| `meta.layout_variant` | `classic`、`detail` | 可省，默认 classic。选择经典比例或放大中下技术区。 |
| `title` | 双语词条 | 一行。优先用用户原文。保留通用提案标题的音义和焦点。 |
| `concept.style_keywords`、`concept.mood` | 非空双语词条数组、双语词条 | 写笔触或主题关键词，以及拟呈现的气氛。 |
| `concept.description` | 1–3 个双语词条 | 每项为说明一行，中文合计 ≤60 字含标点。勿写无法看出的工程细节。 |
| `concept.reference_style` | 对象，含 `medium`、`layout` 两个双语词条 | B 类必填。写原板媒介和笔触、标题与各区相对位置。A/C 可省略。 |
| `scene.setting`、`scene.zone`、`scene.time_and_lighting` | 双语词条 | 场地、目标功能区、光线方向或软硬。时段看不清时可只写光线。 |
| `structure.type`、`structure.material`、`structure.components` | 双语词条、双语词条、非空双语数组 | 主结构形式、材质与可见或推断的骨架构件。保留地面接触和悬挂关系。 |
| `structure.dimensions` | `width_mm`、`height_mm`、`depth_mm` 正整数，`estimated` 布尔值 | 至少有一轴无法从用户确认值或可信参考标注取得、需要补估时设 `true`。保留已知轴，并在推断中指明具体估算的轴。三轴全部来自用户确认值或自洽的参考标注时设 `false`，交付仍说明来源。 |
| `florals.main/accent/foliage/colors` | 双语词条数组 | 主花、配花、叶材和颜色，可留空。主、配、叶有任何内容时，颜色至少一项。无法确认品种时写形态与色彩。 |
| `florals.form/placement` | 双语词条或 `null` | 写花艺形态与空间落点。有花艺内容时两项均填，无花艺时设 `null`。 |
| `fabrics` | 对象数组，可为空 | 每项 `type`、`color`、`drape` 为双语词条，`fixing_points` 为非空双语数组。删去模板中不需要的布艺行。 |
| `focal_elements`、`furniture_props` | 双语词条数组，可为空 | 大型纸花等焦点及座椅、地台、路引等。写位置或与主体的关系。 |
| `palette` | 6–8 个 `{name, hex}` | `name` 为双语词条，`hex` 为唯一的六位 `#RRGGBB`。选择实际使用的底、主、辅、强调色。 |
| `materials_legend` | 1–5 个 `{name, phrase}` | 两字段均双语，中文名称 ≤8 字。短语写感受、纹理或外观。 |
| `callouts` | 3–5 个 `{target, label, subtitle}` | 目标指得出确切位置，主词中文 ≤8 字。副词可省或填 `null`，提供时 ≤6 字。三个字段的文字均用双语词条。 |
| `views` | `front`、`side`、`top`、`exploded` 四个对象 | 每项含双语 `content` 和对象 `dimensions`，键和值按下表。 |
| `detail_zooms` | 3–4 个 `{subject,title,lines}` | `subject` 和 `title` 双语，中文题签 ≤8 字，`lines` 为 1–3 个双语说明行。 |
| `inferred_fields` | `{path,reason}` 数组，可为空 | `path` 唯一并指向实际设计值，`reason` 为双语词条。C 类至少一项。有估算时记录尺寸对象或具体估算轴。 |

## 尺寸与文字自检

| 视图 | `views.<视图>.dimensions` 精确字段 | 6000 × 3200 × 1200 mm 示例 |
| --- | --- | --- |
| `front` 正视 | `width_mm`、`height_mm` | 6000、3200 |
| `side` 侧视 | `height_mm`、`depth_mm` | 3200、1200 |
| `top` 俯视 | `width_mm`、`depth_mm` | 6000、1200 |
| `exploded` 分解 | 空对象 `{}` | 只展示部件关系 |

使用 `structure.dimensions` 为唯一权威值。三组重复标注逐轴从它复制。读取冲突标注时先核实采用哪个值。必须用估算时，在 `inferred_fields` 中记原因，在正视图题签下加“尺寸估算 · mm”或 “Estimated · mm”。

完整图面按位置计算文字块。用 15 加上引线、特写、材质数量，总计至多 28。将同一位置的主副词、标题与正文视为一块，六个尺寸数字分别计数。中文长度包含标点，说明合计至多 60 字。对英文同样优先用短句，便于放进预留位置。
