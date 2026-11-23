#!/usr/bin/env python3
"""离线核对婚礼设计 brief 的结构、文字和尺寸。"""

import argparse
import json
import re
import sys
from pathlib import Path


INPUT_TYPES = ("A", "B", "C")
FIDELITY_MODES = ("faithful", "reinterpret")
TEXT_MODES = ("full", "minimal", "none")
LANGUAGES = ("zh", "en")
LAYOUTS = {"classic": (55, 35, 10), "detail": (50, 40, 10)}
DIMENSIONS = {
    "front": ("width_mm", "height_mm"),
    "side": ("height_mm", "depth_mm"),
    "top": ("width_mm", "depth_mm"),
    "exploded": (),
}
DIMENSION_FIELDS = ("width_mm", "height_mm", "depth_mm")
FIXED_TEXT_BLOCKS = 15
MAX_TEXT_BLOCKS = 28


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"JSON 中重复定义了键 {key!r}")
        result[key] = value
    return result


def reject_non_json_number(value):
    raise ValueError(f"JSON 不接受特殊数值 {value}")


def load_brief(path):
    try:
        with path.open(encoding="utf-8-sig") as source:
            return json.load(
                source,
                object_pairs_hook=reject_duplicate_keys,
                parse_constant=reject_non_json_number,
            )
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} 第 {error.lineno} 行第 {error.colno} 列的 JSON 格式有误") from error
    except (OSError, UnicodeError, RecursionError) as error:
        raise ValueError(f"无法读取 UTF-8 JSON（{path}）：{error}") from error


def pointer_exists(root, pointer):
    if not pointer.startswith("/") or re.search(r"~(?![01])", pointer):
        return False
    value = root
    for token in pointer[1:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", key):
            if len(key) > len(str(len(value))) or int(key) >= len(value):
                return False
            value = value[int(key)]
        else:
            return False
    return True


class Audit:
    def __init__(self):
        self.errors = []

    def require(self, condition, path, message):
        if not condition:
            self.errors.append(f"{path}：{message}")
        return condition

    def object(self, value, path, required, optional=()):
        if not self.require(isinstance(value, dict), path, "应为对象"):
            return {}
        for key in required:
            self.require(key in value, f"{path.rstrip('/')}/{key}", "缺少必填字段")
        for key in sorted(value.keys() - set(required) - set(optional)):
            self.require(False, path, f"未知字段 {key!r}")
        return value

    def array(self, value, path, minimum=0, maximum=None):
        if not self.require(isinstance(value, list), path, "应为数组"):
            return []
        if maximum is None:
            self.require(len(value) >= minimum, path, f"至少需要 {minimum} 项")
        else:
            self.require(minimum <= len(value) <= maximum, path, f"需要 {minimum}–{maximum} 项")
        return value

    def choice(self, value, path, choices):
        self.require(isinstance(value, str) and value in choices, path, f"请选择 {' / '.join(choices)}")

    def line(self, value, path, limit=None):
        valid = self.require(
            isinstance(value, str) and bool(value.strip()) and value == value.strip() and value.isprintable(),
            path, "应为无换行、无首尾空格的非空文字",
        )
        if not valid:
            return ""
        if limit is not None:
            self.require(len(value) <= limit, path, f"最多 {limit} 字（含标点）")
        return value

    def pair(self, value, path, zh_limit=None):
        pair = self.object(value, path, LANGUAGES)
        return {
            "zh": self.line(pair.get("zh"), f"{path}/zh", zh_limit),
            "en": self.line(pair.get("en"), f"{path}/en"),
        }

    def pairs(self, value, path, minimum=0, maximum=None):
        return [
            self.pair(item, f"{path}/{index}")
            for index, item in enumerate(self.array(value, path, minimum, maximum))
        ]


def check_meta(audit, value):
    path = "/meta"
    meta = audit.object(value, path, ("input_type", "fidelity_mode", "aspect_ratio", "language", "text_mode"), ("layout_variant",))
    audit.choice(meta.get("input_type"), f"{path}/input_type", INPUT_TYPES)
    audit.choice(meta.get("fidelity_mode"), f"{path}/fidelity_mode", FIDELITY_MODES)
    audit.choice(meta.get("language"), f"{path}/language", LANGUAGES)
    audit.choice(meta.get("text_mode"), f"{path}/text_mode", TEXT_MODES)
    audit.choice(meta.get("layout_variant", "classic"), f"{path}/layout_variant", LAYOUTS)
    ratio = meta.get("aspect_ratio")
    if audit.require(isinstance(ratio, str) and re.fullmatch(r"[1-9][0-9]*:[1-9][0-9]*", ratio), f"{path}/aspect_ratio", "使用正整数宽:高，例如 3:4"):
        width, height = ratio.split(":")
        audit.require((len(width), width) < (len(height), height), f"{path}/aspect_ratio", "请使用宽小于高的竖版比例")
    return meta


def check_structure(audit, value):
    path = "/structure"
    structure = audit.object(value, path, ("type", "material", "components", "dimensions"))
    audit.pair(structure.get("type"), f"{path}/type")
    audit.pair(structure.get("material"), f"{path}/material")
    audit.pairs(structure.get("components"), f"{path}/components", 1)
    dimensions = audit.object(structure.get("dimensions"), f"{path}/dimensions", (*DIMENSION_FIELDS, "estimated"))
    for axis in DIMENSION_FIELDS:
        number = dimensions.get(axis)
        audit.require(type(number) is int and number > 0, f"{path}/dimensions/{axis}", "应为正整数，单位毫米")
    audit.require(type(dimensions.get("estimated")) is bool, f"{path}/dimensions/estimated", "应为布尔值 true 或 false")
    return dimensions


def check_views(audit, value, dimensions):
    views = audit.object(value, "/views", DIMENSIONS)
    for name, axes in DIMENSIONS.items():
        path = f"/views/{name}"
        view = audit.object(views.get(name), path, ("content", "dimensions"))
        audit.pair(view.get("content"), f"{path}/content")
        marks = audit.object(view.get("dimensions"), f"{path}/dimensions", axes)
        for axis in axes:
            mark = marks.get(axis)
            if audit.require(type(mark) is int and mark > 0, f"{path}/dimensions/{axis}", "应为正整数，单位毫米"):
                expected = dimensions.get(axis)
                if type(expected) is int:
                    audit.require(mark == expected, f"{path}/dimensions/{axis}", f"读到 {mark}，须与 /structure/dimensions/{axis} 的 {expected} 一致")


def check_decor(audit, root):
    floral_path = "/florals"
    flower_parts = ("main", "accent", "foliage")
    florals = audit.object(root.get("florals"), floral_path, (*flower_parts, "form", "placement", "colors"))
    parts = [audit.pairs(florals.get(key), f"{floral_path}/{key}") for key in flower_parts]
    for key in ("form", "placement"):
        part = florals.get(key)
        if any(parts) or part is not None:
            audit.pair(part, f"{floral_path}/{key}")
    audit.pairs(florals.get("colors"), f"{floral_path}/colors", minimum=int(any(parts)))

    for index, value in enumerate(audit.array(root.get("fabrics"), "/fabrics")):
        path = f"/fabrics/{index}"
        fabric = audit.object(value, path, ("type", "color", "drape", "fixing_points"))
        for key in ("type", "color", "drape"):
            audit.pair(fabric.get(key), f"{path}/{key}")
        audit.pairs(fabric.get("fixing_points"), f"{path}/fixing_points", 1)

    for key in ("focal_elements", "furniture_props"):
        audit.pairs(root.get(key), f"/{key}")


def check_board_copy(audit, root):
    unique_colors = set()
    for index, value in enumerate(audit.array(root.get("palette"), "/palette", 6, 8)):
        path = f"/palette/{index}"
        color = audit.object(value, path, ("name", "hex"))
        audit.pair(color.get("name"), f"{path}/name")
        hex_value = color.get("hex")
        if audit.require(isinstance(hex_value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", hex_value), f"{path}/hex", "使用六位 HEX 颜色值，例如 #F3E8D2"):
            audit.require(hex_value.upper() not in unique_colors, f"{path}/hex", "色板包含重复色值")
            unique_colors.add(hex_value.upper())

    legends = audit.array(root.get("materials_legend"), "/materials_legend", 1, 5)
    for index, value in enumerate(legends):
        path = f"/materials_legend/{index}"
        legend = audit.object(value, path, ("name", "phrase"))
        audit.pair(legend.get("name"), f"{path}/name", 8)
        audit.pair(legend.get("phrase"), f"{path}/phrase")

    callouts = audit.array(root.get("callouts"), "/callouts", 3, 5)
    for index, value in enumerate(callouts):
        path = f"/callouts/{index}"
        callout = audit.object(value, path, ("target", "label"), ("subtitle",))
        audit.pair(callout.get("target"), f"{path}/target")
        audit.pair(callout.get("label"), f"{path}/label", 8)
        if callout.get("subtitle") is not None:
            audit.pair(callout["subtitle"], f"{path}/subtitle", 6)

    details = audit.array(root.get("detail_zooms"), "/detail_zooms", 3, 4)
    for index, value in enumerate(details):
        path = f"/detail_zooms/{index}"
        detail = audit.object(value, path, ("subject", "title", "lines"))
        audit.pair(detail.get("subject"), f"{path}/subject")
        audit.pair(detail.get("title"), f"{path}/title", 8)
        audit.pairs(detail.get("lines"), f"{path}/lines", 1, 3)

    count = FIXED_TEXT_BLOCKS + len(callouts) + len(details) + len(legends)
    audit.require(count <= MAX_TEXT_BLOCKS, "/", f"完整模式共 {count} 个文字块，最多 {MAX_TEXT_BLOCKS} 块，请合并重复引线、细节或材质")


def check_inferences(audit, root, meta, dimensions):
    entries = audit.array(root.get("inferred_fields"), "/inferred_fields")
    seen = set()
    for index, value in enumerate(entries):
        path = f"/inferred_fields/{index}"
        item = audit.object(value, path, ("path", "reason"))
        pointer = audit.line(item.get("path"), f"{path}/path")
        if pointer:
            valid = (
                pointer_exists(root, pointer)
                and not pointer.startswith(("/inferred_fields", "/meta"))
                and pointer != "/structure/dimensions/estimated"
            )
            audit.require(valid, f"{path}/path", "应为指向实际设计字段的 JSON Pointer")
            audit.require(pointer not in seen, f"{path}/path", "该字段已记录")
            seen.add(pointer)
        audit.pair(item.get("reason"), f"{path}/reason")
    if meta.get("input_type") == "C":
        audit.require(bool(entries), "/inferred_fields", "C 类应说明补全了哪些内容及其依据")
    if dimensions.get("estimated") is True:
        accepted_paths = {"/structure/dimensions", *(f"/structure/dimensions/{key}" for key in DIMENSION_FIELDS)}
        audit.require(bool(seen & accepted_paths), "/inferred_fields", "估算尺寸应记录为 /structure/dimensions 或具体的宽、高、进深字段")


def validate_brief(value):
    audit = Audit()
    fields = (
        "meta", "title", "concept", "scene", "structure", "florals", "fabrics", "focal_elements",
        "furniture_props", "palette", "materials_legend", "callouts", "views", "detail_zooms", "inferred_fields",
    )
    root = audit.object(value, "/", fields)
    if not isinstance(value, dict):
        return audit.errors
    meta = check_meta(audit, root.get("meta"))
    audit.pair(root.get("title"), "/title")
    concept = audit.object(
        root.get("concept"), "/concept", ("style_keywords", "mood", "description"), ("reference_style",),
    )
    reference = concept.get("reference_style")
    if "reference_style" in concept or meta.get("input_type") == "B":
        path = "/concept/reference_style"
        style = audit.object(reference, path, ("medium", "layout"))
        for key in ("medium", "layout"):
            audit.pair(style.get(key), f"{path}/{key}")
    audit.pairs(concept.get("style_keywords"), "/concept/style_keywords", 1)
    audit.pair(concept.get("mood"), "/concept/mood")
    description = audit.pairs(concept.get("description"), "/concept/description", 1, 3)
    audit.require(sum(len(line["zh"]) for line in description) <= 60, "/concept/description", "中文说明合计最多 60 字（含标点）")
    scene = audit.object(root.get("scene"), "/scene", ("setting", "zone", "time_and_lighting"))
    for key in ("setting", "zone", "time_and_lighting"):
        audit.pair(scene.get(key), f"/scene/{key}")
    dimensions = check_structure(audit, root.get("structure"))
    check_decor(audit, root)
    check_views(audit, root.get("views"), dimensions)
    check_board_copy(audit, root)
    check_inferences(audit, root, meta, dimensions)
    return audit.errors


def main():
    parser = argparse.ArgumentParser(description="离线校验婚礼设计 brief 的字段、文字和正侧俯视尺寸。")
    parser.add_argument("brief", type=Path, help="UTF-8 JSON 文件")
    args = parser.parse_args()
    try:
        errors = validate_brief(load_brief(args.brief))
    except ValueError as error:
        errors = [str(error)]
    if errors:
        print("Brief 校验失败。", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Brief 校验通过。字段、文字预算和三视图尺寸一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
