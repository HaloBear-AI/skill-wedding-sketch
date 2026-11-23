# 生图模型适配

先按 [design-brief-schema.md](design-brief-schema.md) 校验 brief，再按 [prompt-templates.md](prompt-templates.md) 组装提示词。按具体生图入口选适配器。能读取原图、能生成图片、能把参考图送入生成请求是三项独立能力。

## 选择适配器

| `--adapter` | 何时选用 | 如何使用参考图 |
| --- | --- | --- |
| `通用`（默认） | 尚未选模型，或同一包要给不同工具 | 提示词写明参考图的作用，用户在支持图像输入的入口附加原图。只收文字的入口可根据 brief 中完整的视觉描述作图。 |
| `支持参考图` | 当前界面或接口已有生图用的图像输入 | 将原图作为实际图像输入附加，在提示词里说明图 1 的角色。有专门的图像提示、风格参考或编辑入口时，按此次任务选用。 |
| `不支持参考图` | 目标生图入口只收文本，或目标请求没有可附的原图 | 把结构、花群、配色和位置关系直接写进提示词。省略上传指令、图号、文件名和空洞的“按参考图生成”。 |

L1 按能力选适配器并生成。L2 用已解析的 brief 交付提示词包。L3 从已给的描述或模板整理 brief，再走 L2。若用户接下来能在目标入口附原图，仍可使用通用版或参考图版提示词，并写明本次 brief 基于文字描述。若 L1 的生成入口只收文本，使用 `不支持参考图`，在结果中说明原图只用于分析、未送入生成模型。

A 类 `faithful` 将参考图用于锁定结构、花材、色彩和空间关系。B 类用来沿用分区、纸张和笔触，明确换主题色时用 `reinterpret`，在提示词中具体写出新颜色。C 类以可见局部为依据，从 brief 补入设计和结构，并在 `inferred_fields` 登记对应的 JSON Pointer。三种入口都从同一组 `width_mm`、`height_mm`、`depth_mm` 派生正、侧、顶视图的标签。

## 按实际入口设置参数

以下是官方原生入口示例，文档核对日期为 2026-11-23。产品页面、第三方中转和本地工作流的输入控件、长度和参数可能不同，发送前查看所用版本的参数说明。比例均按宽比高书写。

| 模型与入口 | 参考图 | 竖版 3:4 写法 | 图内文字 | 提示词长度 | 官方资料 |
| --- | --- | --- | --- | --- | --- |
| OpenAI `gpt-image-2`，Images API Edits | 支持。向 `POST /v1/images/edits` 的图像字段传原图，multipart 可用 `image[]`。省略 `input_fidelity`，该型号按高保真处理输入图。 | `size="1152x1536"`。 | 用双引号给逐字文案及位置。密集中文小字逐项验收，必要时从精简文字开始。 | Edits 的 `prompt` 上限 32,000 字符。 | [编辑端点](https://developers.openai.com/api/reference/python/resources/images/methods/edit)、[尺寸与输入保真](https://developers.openai.com/api/docs/guides/image-generation)、[图内文字指南](https://developers.openai.com/api/docs/guides/image-prompting) |
| OpenAI `gpt-image-2`，Images API Generations | 此入口为文生图。向 `POST /v1/images/generations` 传独立场景描述。 | `size="1152x1536"`。 | 保留所选模式的精确文字白名单，逐项验收。 | Generations 的 `prompt` 上限 32,000 字符。 | [生成端点](https://developers.openai.com/api/reference/python/resources/images/methods/generate) |
| Google `gemini-3.1-flash-image`，Gemini API Interactions | 支持。向 `input` 传文本与图像内容项。 | `response_format={"type":"image","aspect_ratio":"3:4","image_size":"2K"}`。 | 官方推荐工作语言包含简体中文。明确文字、字体感觉和位置，并校对汉字和重复尺寸数字。 | 模型规格的输入上限是 131,072 tokens，按整个输入核算。 | [图像生成与编辑](https://aistudio.google.com/docs/image-generation)、[模型规格](https://aistudio.google.com/docs/models/gemini-3.1-flash-image) |
| Midjourney V8.2，Web 或 Discord 的 Imagine | 支持。Web 选择 Image Prompt 或 Style Reference。Discord 的图像提示 URL 放在文字前，风格参考使用 `--sref`。 | 将 `--ar 3:4` 放在提示词末尾的参数区。 | 用英文双引号围住实际文案。官方指出拉丁字母短语更容易生成。中文可先试 `minimal`，或用 `none` 后期叠字。 | 官方建议简短具体，提示词指南未给统一的字符或词数上限。 | [版本](https://docs.midjourney.com/hc/en-us/articles/32199405667853-Version)、[图像提示](https://docs.midjourney.com/hc/en-us/articles/32040250122381-Image-Prompts)、[风格参考](https://docs.midjourney.com/hc/en-us/articles/32180011136653-Style-Reference)、[比例](https://docs.midjourney.com/hc/en-us/articles/31894244298125-Aspect-Ratio)、[文字](https://docs.midjourney.com/hc/en-us/articles/32502277092109-Text-Generation)、[长度建议](https://docs.midjourney.com/hc/en-us/articles/32023408776205-Prompt-Basics) |
| Seedream 5.0 pro，火山方舟 Images Generations API | 支持。用 `image` 传参考图 URL 或接口支持的 Base64 输入。 | 直接设 `size="1776x2368"`。若用 `size="2K"` 档位，在正文描述竖版 3:4 并核对实际像素。 | 官方展示中文排版。给定引号内的精确文案及位置，中文小字和毫米数字逐处校对。 | 官方建议中文不超过 300 字，或英文不超过 600 词。该数字是提示词写作建议。 | [火山方舟图像生成 API](https://docs.volcengine.com/docs/ark/image-generation-api?lang=zh)、[中文排版能力](https://seed.bytedance.com/en/blog/beyond-generation-it-understands-design-introducing-seedream-5-0-pro) |
| FLUX.2 [pro]，Black Forest Labs API `/v1/flux-2-pro` | 支持。用 `input_image` 传第一张参考图。 | 整数字段 `width=1152`、`height=1536`。 | 指定带引号的文字与位置。官方指南提供文字与排版示例，中文小字按样图验收。 | 官方指南按任务复杂度给写作长度建议，所引指南未给统一的硬长度阈值。 | [图像编辑](https://docs.bfl.ai/flux_2/flux2_image_editing)、[尺寸与排版指南](https://docs.bfl.ai/guides/prompting_guide_flux2) |

火山方舟在上述入口默认添加可见水印。将请求字段 `watermark` 设为 `false`，并在验收时检查画面。Gemini 图像生成会附加平台的隐形 SynthID 来源标记。[火山方舟水印字段](https://docs.volcengine.com/docs/ark/image-generation-api?lang=zh)、[Gemini 图像生成](https://aistudio.google.com/docs/image-generation)

## 发送与验收

1. 从提示词包选一段可独立执行的提示词。默认包包含中文、英文指令各自的 `full`、`minimal`、`none`。显式指定 `--text-mode` 时只构建所选模式。成图按 brief 或本次明确要求的模式选用。
2. 将提示词指令的语言与图中文字语言分别设置。`--lang zh|en|both` 选择指令语言，默认 `both`。brief 的 `meta.language` 选择画面语言，默认 `zh`。需要覆盖时用 `--board-language zh|en`。例如使用英文提示词生成中文板时，图中文字清单仍逐字保持中文。
3. 使用当前接口的专属参数域。API 的参数放进请求字段，Midjourney 的参数放在 Imagine 指令末尾。没有专用负面字段时，把关键排除条件写在正文。FLUX.2 适配时可改写成正向约束，例如“画面主体为手绘空场装置，纸面留白干净，画面只出现清单指定文字”。[FLUX.2 提示词建议](https://docs.bfl.ai/guides/prompting_guide_flux2)
4. 保留单张竖版和选定的分区比例。classic 为约 55%／35%／10%，detail 为约 50%／40%／10%。遇到固定尺寸入口，选最接近的纵向档位，预留边距。用外框留白或安全裁切达到目标比例，检查四视图、色板和标注仍完整。
5. 长度受限时先删冗余形容词和重复约束，保留参考角色、结构锚点、版式、尺寸及文字白名单。若完整中文仍难以成图，按 [troubleshooting.md](troubleshooting.md) 处理文字。用 `minimal` 留标题、四视图名和六处尺寸数字，单位和适用的估算提示并入正视图名第二行。用 `none` 留图、引线、尺寸线和字区空白，再从提示词块外的完整叠字清单加字。
6. 按 [qa-checklist.md](qa-checklist.md) 检查实际成图的字形与尺寸，即便模型响应同时带有正确的文字描述。全文按位置计算文字块，重复尺寸分开计数。引线主词最多 8 个汉字，副词最多 6 个汉字，全文最多 28 个文字块。
