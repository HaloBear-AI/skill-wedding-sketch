#!/usr/bin/env python3
"""从通过校验的双语 brief 组装可独立粘贴的方案板提示词。"""

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

sys.dont_write_bytecode = True
from validate_brief import DIMENSIONS, LANGUAGES, LAYOUTS, TEXT_MODES, load_brief, validate_brief


ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = ("通用", "支持参考图", "不支持参考图")
VIEW_NAMES = {
    "front": ("正视图", "Front elevation"),
    "side": ("侧视图", "Side elevation"),
    "top": ("俯视图", "Plan view"),
    "exploded": ("结构分解图", "Exploded view"),
}
AXIS_NAMES = {
    "width_mm": ("宽度", "width"),
    "height_mm": ("高度", "height"),
    "depth_mm": ("进深", "depth"),
}


class Block(NamedTuple):
    zh_position: str
    en_position: str
    lines: tuple
    minimal: bool = False


class PromptArguments(argparse.ArgumentParser):
    def error(self, message):
        super().error(f"参数有误，请用 --help 查看用法。{message}")


def localize(lang, zh, en):
    return zh if lang == "zh" else en


def make_blocks(brief, lang):
    def choose(zh, en):
        return localize(lang, zh, en)

    blocks = [
        Block("顶端标题", "top title", (brief["title"][lang],), True),
        Block(
            "主图左上说明",
            "upper-left design note",
            (choose("设计说明", "Design note"), *(line[lang] for line in brief["concept"]["description"])),
        ),
    ]
    for index, label in enumerate(brief["callouts"], 1):
        lines = (label["label"][lang],)
        if label.get("subtitle"):
            lines += (label["subtitle"][lang],)
        blocks.append(Block(f"主图右侧第 {index} 条引线", f"right hero leader {index}", lines))

    dimensions = brief["structure"]["dimensions"]
    for key, axes in DIMENSIONS.items():
        zh_name, en_name = VIEW_NAMES[key]
        lines = (choose(zh_name, en_name),)
        if key == "front":
            if dimensions["estimated"]:
                unit = choose("尺寸估算 · mm", "Estimated · mm")
            else:
                unit = choose("单位 · mm", "Units · mm")
            lines += (unit,)
        blocks.append(Block(f"{zh_name}标题", f"{en_name} heading", lines, True))
        for axis in axes:
            zh_axis, en_axis = AXIS_NAMES[axis]
            mark = str(brief["views"][key]["dimensions"][axis])
            blocks.append(Block(f"{zh_name}{zh_axis}尺寸线", f"{en_name} {en_axis} dimension line", (mark,), True))

    blocks.append(Block("中下区右栏标题", "right detail column heading", (choose("细节放大图", "Detail studies"),)))
    for index, detail in enumerate(brief["detail_zooms"], 1):
        lines = (detail["title"][lang], *(line[lang] for line in detail["lines"]))
        blocks.append(Block(f"右栏第 {index} 个特写旁", f"right column detail {index}", lines))
    blocks.append(Block("底部左栏标题", "bottom-left band heading", (choose("材质说明", "Materials"),)))
    for index, legend in enumerate(brief["materials_legend"], 1):
        lines = (legend["name"][lang], legend["phrase"][lang])
        blocks.append(Block(f"第 {index} 个材质样块旁", f"material chip {index}", lines))
    blocks.append(Block("底部右栏标题", "bottom-right band heading", (choose("色彩方案", "Color palette"),)))
    return blocks


def print_blocks(blocks, lang, mode):
    if mode == "none":
        return localize(
            lang,
            "白名单为空。保留预留字区、手绘下划线、引线和尺寸线。全图禁止文字、数字、字母和伪字，连参考图已有标签也留空。",
            "The whitelist is empty. Keep text space, the drawn underline, leaders and dimension rules. Leave all letters, words, numbers, reference labels and pseudo-glyphs blank.",
        )
    output = []
    for block in blocks:
        if mode == "full" or block.minimal:
            position = localize(lang, block.zh_position, block.en_position)
            copy = " / ".join(json.dumps(line, ensure_ascii=False) for line in block.lines)
            output.append(f"- {position} → {copy}")
    return "\n".join(output)


def reference_role(brief, lang, adapter):
    def choose(zh, en):
        return localize(lang, zh, en)

    kind = brief["meta"]["input_type"]
    fidelity = brief["meta"]["fidelity_mode"]
    use = {
        "通用": choose(
            "如随请求附了参考图，将它按下述角色使用；无图时以本文 brief 为依据。",
            "If an image comes with this request, use it in the role below. Otherwise use the design brief described here.",
        ),
        "支持参考图": choose(
            "把用户的单张原图放入参考／编辑输入。参考图控制下列设计要点，本文规定输出内容及允许的图内文字。",
            "Use the user's one source image as the image input or edit reference. It controls the design points below. This prompt controls the output and verbatim board copy.",
        ),
        "不支持参考图": choose(
            "此生成请求没有附图输入。只根据已解析的下述设计描述和各分区内容作画。",
            "This generation request has no image input. Draw from the analyzed design description and the panel instructions in this prompt.",
        ),
    }[adapter]
    mode = {
        "faithful": choose(
            "保留参考图中的结构、花材、配色与空间关系，仅改变表现形式为手绘方案板。对不可见处只采用 brief 明示的补全。",
            "Preserve the reference structure, florals, palette and spatial relationships. Change the presentation to a hand-drawn proposal board and use the brief's completions only where the source is unclear.",
        ),
        "reinterpret": choose(
            "以 brief 指定的新要求为准，保留可继承的风格与未要求改变的设计关系。",
            "Follow the new design specified in the brief. Carry over the visual style and design relationships outside the requested changes.",
        ),
    }[fidelity]
    kind_note = {
        "A": choose(
            "从实景或 3D 的视线中提取设计，以针管笔和水彩转绘。把相关装置和布置的相对位置带入小图。",
            "Translate the design from a venue photo or render into pen and watercolor. Carry the relevant arrangement into the small views.",
        ),
        "B": choose(
            "沿用参考图的版式与笔触风格，以本页分区要求组织实际模块，图面字只用白名单。",
            "Carry over the reference board's layout character and stroke style. Use the requested panel arrangement and the current text whitelist.",
        ),
        "C": choose(
            "锁定局部参考中可见的结构或花艺，按 brief 补全遮挡和场地关系。",
            "Keep the visible structure or flower arrangement from the partial reference. Complete missing geometry and context from the brief.",
        ),
    }[kind]
    return "\n".join((use, mode, kind_note))


def scene_lines(brief, lang):
    def choose(zh, en):
        return localize(lang, zh, en)

    def values(items):
        return choose("、", ", ").join(item[lang] for item in items)

    scene, structure = brief["scene"], brief["structure"]
    fields = [
        (choose("场景", "Setting"), scene["setting"][lang]),
        (choose("区域", "Area"), scene["zone"][lang]),
        (choose("时间与光线", "Time and lighting"), scene["time_and_lighting"][lang]),
        (choose("结构", "Structure"), values((structure["type"], structure["material"]))),
        (choose("构件", "Components"), values(structure["components"])),
    ]
    florals = brief["florals"]
    floral_names = (
        ("main", "主花", "Primary florals"), ("accent", "配花", "Accent florals"),
        ("foliage", "叶材", "Foliage"), ("colors", "花艺色彩", "Floral colors"),
    )
    for key, zh, en in floral_names:
        if florals[key]:
            fields.append((choose(zh, en), values(florals[key])))
    for key, zh, en in (("form", "花艺形态", "Floral form"), ("placement", "花艺落点", "Floral placement")):
        if florals[key]:
            fields.append((choose(zh, en), florals[key][lang]))

    for index, fabric in enumerate(brief["fabrics"], 1):
        base = values(fabric[key] for key in ("type", "color", "drape"))
        points = values(fabric["fixing_points"])
        fields.append((choose(f"布艺 {index}", f"Fabric {index}"), f"{base} / {choose('固定点', 'Fixing points')} {points}"))
    for key, zh, en in (("focal_elements", "焦点", "Focal decor"), ("furniture_props", "家具与道具", "Furniture and props")):
        if brief[key]:
            fields.append((choose(zh, en), values(brief[key])))
    for index, item in enumerate(brief["callouts"], 1):
        fields.append((choose(f"引线 {index} 落点", f"Leader {index} target"), item["target"][lang]))
    return "\n".join(f"- {name} — {value}" for name, value in fields)


def technical_lines(brief, lang):
    def choose(zh, en):
        return localize(lang, zh, en)

    dimensions = brief["structure"]["dimensions"]
    width, height, depth = (dimensions[key] for key in ("width_mm", "height_mm", "depth_mm"))
    if dimensions["estimated"]:
        source = choose("提案估算，单位统一为毫米", "concept estimates in millimeters")
    else:
        source = choose("采用 brief 中的标注，单位统一为毫米", "brief-supplied values in millimeters")
    lines = [choose(
        f"各视图共用同一外包络，宽 {width}、高 {height}、进深 {depth} mm（{source}）。仅为方案表达。",
        f"Use one common envelope, width {width}, height {height}, depth {depth} mm ({source}). Use for visual communication.",
    )]
    for key, axes in DIMENSIONS.items():
        view = brief["views"][key]
        name = choose(*VIEW_NAMES[key])
        marks = ", ".join(f"{choose(*AXIS_NAMES[axis])} {view['dimensions'][axis]}" for axis in axes)
        size = f" ({marks} mm)" if marks else ""
        lines.append(f"- {name}{size} — {view['content'][lang]}")
    lines.append(choose(
        "四个小图沿用同一个装置的立柱、地面基线、焦点左右顺序与布艺起止。数字只在白名单允许的尺寸线上呈现。",
        "Keep the same posts, ground line, focal left/right order and drape starts and ends across views. Draw numbers only at dimension locations authorized by the whitelist.",
    ))
    return "\n".join(lines)


def render_prompt(brief, lang, board_lang, mode, adapter):
    def choose(zh, en):
        return localize(lang, zh, en)

    ratio = brief["meta"]["aspect_ratio"]
    hero, technical, footer = LAYOUTS[brief["meta"].get("layout_variant", "classic")]
    mood = brief["concept"]["mood"][lang]
    style = choose("、", ", ").join(word[lang] for word in brief["concept"]["style_keywords"])
    blocks = make_blocks(brief, board_lang)
    palette = ", ".join(f"{item['name'][lang]} {item['hex'].upper()}" for item in brief["palette"])
    textures = ", ".join(f"{item['name'][lang]} ({item['phrase'][lang]})" for item in brief["materials_legend"])
    detail = "\n".join(f"- {index}. {item['subject'][lang]}" for index, item in enumerate(brief["detail_zooms"], 1))
    board_language = choose("简体中文", "Simplified Chinese") if board_lang == "zh" else choose("英文", "English")
    copy_rules = choose(
        f"图内语言为{board_language}。只写下列引号内的原文，不画引号。斜线只表示同位置换行。位置、色名、色值和说明性文字只作为绘制指令。",
        f"Render board copy in {board_language}. Typeset only the quoted strings, without the quotation marks. Slashes separate lines within a block. Position descriptors, paint names and HEX values are instructions only.",
    )
    if mode == "none":
        copy_rules = choose(
            "此模式只绘制图形和留白。生成阶段无需叠字。",
            "This mode draws artwork and blank space only. Lettering is a separate pass.",
        )
    source_style = brief["concept"].get("reference_style")
    source_medium, source_layout = "", ""
    if source_style:
        medium, layout = (source_style[key][lang] for key in ("medium", "layout"))
        source_medium = choose(f" 优先沿用原板的媒介描述。{medium}。", f" Match the source medium: {medium}.")
        source_layout = choose(
            f" 沿用原板的主要分区关系。{layout}。比例为排版基准，补齐所需模块。",
            f" Carry over the source panel relationships: {layout}. Treat the percentages as a layout baseline and fill every required panel.",
        )
    section_data = [
        ("总述", "Deliverable", choose(
            f"绘制一张 {ratio} 竖版手绘婚礼设计提案板，用于向新人和团队讲解一个布置区域。单页完整构图。",
            f"Create one complete {ratio} portrait wedding design concept board presenting one decor area to a couple and their team.",
        )),
        ("画风与媒介", "Medium and style", choose(
            f"米白色、轻微做旧的水彩纸，针管笔和钢笔线稿，透明水彩叠色与柔和马克笔，压低阴影对比。保留干湿不均和笔触。需要图内文字时保持字形清楚。风格词为{style}。氛围为{mood}。",
            f"Work on lightly aged ivory watercolor paper with fine fineliner and pen linework, translucent watercolor washes and restrained marker accents. Keep soft shadows, visible strokes and legible handwriting when required. Style: {style}. Mood: {mood}.",
        ) + source_medium),
        ("版式", "Panel layout", choose(
            f"四周留约 4% 安全边距。上区 {hero}% 放左对齐标题位和手绘下划线，下面是主透视手绘。左上预留短说明，右侧排列 {len(brief['callouts'])} 条引线。中下区 {technical}% 左约三分之二做 2×2 四视图，依次正视、侧视、俯视、结构分解。右约三分之一竖排圆形或椭圆细节。底带 {footer}% 左侧为材质图例，右侧为整排色票。",
            f"Leave about 4% safe margins. Upper {hero}%: upper-left title area with a drawn underline, then the main perspective sketch, an upper-left note area and {len(brief['callouts'])} right-hand leaders. Middle-lower {technical}%: place the front, side, top and exploded views in a 2×2 grid in the left two thirds; stack round or oval details in the right third. Bottom {footer}%: arrange material chips on the left and a row of colors on the right.",
        ) + source_layout),
        ("主效果图", "Main perspective", scene_lines(brief, lang)),
        ("技术图", "Technical studies", technical_lines(brief, lang)),
        ("细节特写", "Detail studies", choose("依次放大以下部件，保留特写边缘与说明留白。", "Show these parts in order, keeping the crop edges and space for captions.") + "\n" + detail),
        ("图例与色板", "Material legend and palette", choose(
            f"材质样块依次为 {textures}。色票依次为 {palette}。样块图形展示表面纹理，色票用干净色块表达，颜色名和 HEX 不上图。",
            f"Material chips in order: {textures}. Swatches in order: {palette}. Show material textures and solid color chips. Leave palette names and HEX values off the board.",
        )),
        ("图内文字清单", "Verbatim board copy", copy_rules + "\n" + print_blocks(blocks, lang, mode)),
        ("参考图角色", "Reference role", reference_role(brief, lang, adapter)),
        ("负面约束", "Negative constraints", choose(
            "避免照片质感、3D 渲染质感、塑料高光、水印、品牌标识、额外人物或可识别肖像、乱码和清单外字形。禁止多页拼贴、裁掉底带、改变同一装置的跨视图关系、布艺悬空和结构无支撑的画法。",
            "Avoid photorealism, 3D-render gloss, plastic specular highlights, watermarks, brand marks, extra people, identifiable portraits, garbled or unlisted copy. Avoid multi-page collages, a clipped footer, inconsistent view geometry, floating drapery or unsupported structures.",
        )),
    ]
    return "\n\n".join(f"{index}. {choose(zh, en)}\n{value}" for index, (zh, en, value) in enumerate(section_data, 1))


def text_fence(content):
    marker = chr(96)
    length = max((len(run) for run in re.findall(f"{marker}+", content)), default=0)
    fence = marker * max(3, length + 1)
    return f"{fence}text\n{content}\n{fence}"


def package_for(brief, languages, board_lang, modes, adapter):
    lang = languages[0]

    def choose(zh, en):
        return localize(lang, zh, en)

    adapter_label = choose(adapter, {"通用": "General", "支持参考图": "Image reference", "不支持参考图": "Text only"}[adapter])
    ratio = brief["meta"]["aspect_ratio"]
    preferred = "，例如 1536 × 2048" if ratio == "3:4" else ""
    preferred_en = " (1536 × 2048 is one 3:4 option)" if ratio == "3:4" else ""
    parts = [choose("# 婚礼方案手绘板 · 生图提示词包", "# Wedding Concept Sketch Board · Prompt Package")]
    notes = [
        choose(
            f"- 图内语言 `{board_lang}` · 参考适配 `{adapter_label}` · 优先尝试 `{modes[0]}`。每次只复制一个版本的代码块。",
            f"- Board copy `{board_lang}` · input adapter `{adapter_label}` · start with `{modes[0]}`. Paste one prompt block per attempt.",
        ),
        choose(
            f"- 画幅选择 `{ratio}` 竖版{preferred}。生成数量设为一，选择可用的高细节质量。平台只提供近似比例时等比补纸边，并复核底带。",
            f"- Select a `{ratio}` portrait output{preferred_en}. Generate one image with a high-detail setting when offered. Pad a nearby portrait ratio with matching paper and recheck the footer.",
        ),
        choose(
            "- 有图像输入时附原始参考图，并采用相应参考图角色。纯文本接口用解析内容。平台有专用负面提示框时可把第 10 节移入该字段。",
            "- Attach the source through an image-input field where supported. On text-only interfaces, rely on the parsed brief. Move section 10 into a dedicated negative-prompt field when one exists.",
        ),
    ]
    parts.append("\n".join(notes))
    for language in languages:
        for mode in modes:
            name = localize(language, "中文指令", "English instructions")
            parts.extend((f"## {name} · {mode}", text_fence(render_prompt(brief, language, board_lang, mode, adapter))))

    parts.extend((
        choose("## 后期叠字定位清单", "## Overlay placement inventory"),
        choose(
            "用于无字底图或替换失真的图内文字。引号内为逐字原文。分隔符两侧安排在同一位置分行。校对估算提示和六组毫米数字。可切换图内语言生成另一套提示词和清单。",
            "Use on the blank base or to replace damaged text. Quotes delimit exact copy, and slashes separate lines at the same anchor. Check the estimate note and all six dimension labels. Change the board language to generate a matching alternative prompt and inventory.",
        ),
        text_fence(print_blocks(make_blocks(brief, board_lang), lang, "full")),
    ))
    return "\n\n".join(parts) + "\n"


def write_package(output, content):
    destination = output.resolve()
    if not destination.is_relative_to(ROOT) or destination.suffix.lower() != ".md":
        raise ValueError("输出须为 Skill 目录内的 .md 文件，请改用 --stdout 或改选 --output 路径")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=destination.parent, delete=False,
        ) as file:
            temporary = Path(file.name)
            file.write(content)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination


def main():
    parser = PromptArguments(description="从已验证的 JSON brief 组装中文、英文和文字模式提示词。")
    parser.add_argument("brief", type=Path, help="UTF-8 JSON brief")
    parser.add_argument("--lang", choices=(*LANGUAGES, "both"), default="both", help="提示词指令语言，默认 both")
    parser.add_argument("--adapter", choices=ADAPTERS, default="通用", help="参考图输入能力，默认通用")
    parser.add_argument("--text-mode", choices=TEXT_MODES, help="只生成选定文字模式，省略时输出全部且以 brief 为先")
    parser.add_argument("--board-language", choices=LANGUAGES, help="覆盖图面文字语言，默认沿用 brief")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--stdout", action="store_true", help="仅输出到标准输出")
    output.add_argument("--output", type=Path, help="写到指定的 Skill 目录内 .md 文件")
    args = parser.parse_args()

    try:
        brief = load_brief(args.brief)
        errors = validate_brief(brief)
        if errors:
            raise ValueError("请先修复 brief：\n- " + "\n- ".join(errors))
        languages = LANGUAGES if args.lang == "both" else (args.lang,)
        primary = brief["meta"]["text_mode"]
        modes = (args.text_mode,) if args.text_mode else (primary, *(mode for mode in TEXT_MODES if mode != primary))
        board_lang = args.board_language or brief["meta"]["language"]
        package = package_for(brief, languages, board_lang, modes, args.adapter)
        if args.output:
            if args.output.resolve() == args.brief.resolve():
                raise ValueError("请选择不同于输入 brief 的输出路径")
            destination = write_package(args.output, package)
        elif not args.stdout and Path.cwd().resolve().is_relative_to(ROOT):
            suggested = Path("prompt-package.md")
            if suggested.resolve() == args.brief.resolve():
                raise ValueError("默认输出与输入冲突，请使用 --stdout 或 --output")
            destination = write_package(suggested, package)
        else:
            sys.stdout.write(package)
            return 0
        print(f"提示词包已写入 {destination}")
        return 0
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        print(f"提示词包生成失败：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
