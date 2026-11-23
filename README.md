# 婚礼方案手绘板

把一张婚礼布置参考图做成单张手绘设计方案板，用于给新人提案或和执行团队沟通。支持把实景和 3D 效果图转绘为手稿、沿用已有手绘板的风格改方案，以及补全局部参考图。先依据参考整理 JSON 设计 brief，再出图或交付可粘贴的中英文生图提示词包。

## 成品示意

标准成品是 3:4 竖版，米白做旧水彩纸上叠加针管笔线稿、水彩、马克笔和手写标注。上部约 55%，放手写标题、主透视图、设计说明和 3–5 条构件引线。中下区约 35%，左边是正视、侧视、俯视和结构分解四个小图，右边放 3–4 个圆形或椭圆特写。底带约 10%，左边放 1–5 项材质，右边是 6–8 色色板。查看 [版式规范](references/board-layout-spec.md) 和 [示例提示词包](assets/prompt-package.example.md)。

## 安装

在要使用 Skill 的项目根目录执行对应的一组命令。保留 `wedding-sketch` 目录名，并把 `SKILL.md` 和随附文件放在同一个目录下。通过 ZIP 安装时，将里面完整的 Skill 文件夹解压到所选宿主的技能目录。

### Codex

```sh
mkdir -p .agents/skills
git clone https://github.com/JackYang0326/halobear-skill-wedding-sketch.git \
  .agents/skills/wedding-sketch
```

在目标项目打开会话并发送参考图。Codex CLI 或 IDE 扩展可用 `$wedding-sketch` 指定 Skill。 [Codex 官方文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

### Claude Code

```sh
mkdir -p .claude/skills
git clone https://github.com/JackYang0326/halobear-skill-wedding-sketch.git \
  .claude/skills/wedding-sketch
```

在目标项目打开 Claude Code 会话，提交参考图并使用 `/wedding-sketch`。 [Claude Code 官方文档](https://code.claude.com/docs/en/skills#choose-where-skills-load)

### Cursor

```sh
mkdir -p .cursor/skills
git clone https://github.com/JackYang0326/halobear-skill-wedding-sketch.git \
  .cursor/skills/wedding-sketch
```

在 Cursor 打开目标项目，在 Agent 对话中发送参考图。也可输入 `/`，搜索并选择 `wedding-sketch`。 [Cursor 官方文档](https://cursor.com/docs/skills)

### 无 Skill 加载功能的模型

将 `SKILL.md` 放进系统提示词或自定义指令。把参考资料和 brief 空模板放进知识库或随对话提供，再上传一张参考图，使用下方任一提问。只有文本输入时，用文字描述场景或填写 brief。没有脚本环境时，按提示词模板手动组装。 [Skill 指令](SKILL.md) · [参考资料](references/) · [brief 空模板](assets/design-brief.template.json) · [提示词模板](references/prompt-templates.md)

## 使用示例

1. **实景花艺拱门**

   > 请把我上传的草坪婚礼拱门实拍图转成一张 3:4 中文手绘婚礼方案板。保留木框、象牙白垂纱、两侧不对称花艺和原来的色调。已量过宽 6000、高 3200、进深 1200 毫米。标题写「草坪婚礼花艺装置」。

2. **沿用手绘板改主题**

   > 请照我上传的宴会厅舞台手绘板的版式、线稿和上色方式，把主题色改成酒红、杏粉和暖白。保留舞台结构和装饰的位置。用精简文字，只排英文标题、视图名和尺寸。

3. **从局部图补全迎宾区**

   > 我只有这张迎宾区花艺和纱幔的近照。请保留近照里的花型和颜色，补全一张手绘方案板，在 brief 里列出推断的背架、挂点和尺寸。我要无字底图和后期文字定位清单。当前环境只读图时，请给我中英文提示词包，我会去生图工具出图。

## 配置

| 选项 | 默认值与用法 |
| --- | --- |
| 保真模式 | `faithful` 忠实保留结构、主花材、主色和空间关系。指定改设计时用 `reinterpret`，按要求改动。 |
| 标题 | 从场景和焦点提炼，也可提供要逐字保留的标题。 |
| 画幅与版式 | 竖版 `3:4`、`classic`。需要放大技术区时用 `detail`，上、中下、底带约为 50%、40%、10%，保留全部模块。 |
| 文字模式 | 默认 `full`，最多 28 个字块。`minimal` 留标题、四个视图名、六个尺寸数字，以及正视图标题下的单位或估算提示。`none` 交付无字符底图及完整的后期文字定位清单。 |
| 语言 | 图面默认中文 `zh`，可选英文 `en`。默认提示词包同时含中英文指令。 |
| 尺寸 | 提供宽、高、进深的毫米值可直接使用。缺少可确认数据时，在 brief 记录估算，技术区的正视图标题下标明“尺寸估算 · mm”。 |

## 可选离线脚本

脚本使用 Python 3.9+ 标准库，无需安装依赖、联网或配置 API 密钥。从安装后的 Skill 根目录运行。

```sh
python3 scripts/validate_skill.py
python3 scripts/validate_brief.py assets/design-brief.example.json
python3 scripts/build_prompt.py assets/design-brief.example.json --stdout
```

填自己的方案时，从空模板开始，按字段规范检查。 [brief 空模板](assets/design-brief.template.json) · [字段规范](references/design-brief-schema.md)

| `build_prompt.py` 参数 | 用法 |
| --- | --- |
| `--lang zh\|en\|both` | 控制提示词包指令的语言，默认 `both`。用英文指令生成中文板时，图面语言继续用 `zh`。 |
| `--board-language zh\|en` | 覆盖 brief 的 `meta.language`。省略时采用 brief 设定，空模板预设 `zh`。文案按字段规范填写中英文。 |
| `--adapter 通用\|支持参考图\|不支持参考图` | 匹配当前工具的参考图入口，默认 `通用`。 |
| `--text-mode full\|minimal\|none` | 指定时只组装所选模式的生图指令。`none` 同时附完整后期定位清单。省略时输出全部模式，把 brief 首选模式放在前面。 |
| `--stdout` 或 `--output` | `--stdout` 打印到终端。`--output` 指向 Skill 目录内的 `.md`。两项均省略时，在 Skill 内运行会写入当前目录的 `prompt-package.md`，在 Skill 目录外运行则打印到终端。 |

每个脚本都提供 `--help`。

## 常见问题

### 当前环境只有读图能力，能交付什么？

可以拿到解析后的 brief 和中英文提示词包，含负面约束、画幅建议和参考图用法。把选定的一套提示词提交给生图工具，有参考图入口时一并提供原图。 [模型适配](references/model-adapters.md)

### 中文出图后有错字，怎么改？

先核对本次提示词里的精确字块。短标注可用 `minimal`，需要逐字可控时用 `none` 出底图，再按定位清单排字并复核尺寸、单位和估算提示。 [排错指南](references/troubleshooting.md)

### 图上有毫米尺寸，可以用来搭建吗？

方案板用于视觉提案。现场执行请另行复核实测尺寸、承重、配重与固定方式。 [质检清单](references/qa-checklist.md)

## 版本记录

- **v1.0.0** 首个版本。包含参考图分流、JSON brief、双语提示词包、三种文字模式、离线校验与成图验收。

MIT 许可。 [LICENSE](LICENSE)
