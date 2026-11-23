#!/usr/bin/env python3
"""使用标准库自检这一版 Skill 的目录、frontmatter 和文件引用。"""

import argparse
import json
import re
import sys
from pathlib import Path


FIELDS = {"name", "description", "license", "compatibility", "metadata"}
METADATA = {"version", "author", "language"}
TRIGGERS = (
    "wedding design board", "hand-drawn concept sketch", "presentation board",
    "婚礼方案手绘图", "婚礼设计方案板", "手绘效果图", "花艺装置", "舞台/仪式区/迎宾区设计",
)
MAX_LINES = 500


def parse_scalar(raw):
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError("双引号字符串格式不正确") from error
        if isinstance(value, str):
            return value
    if re.fullmatch(r"[a-z][a-z0-9-]*|MIT", raw) and raw not in {"null", "true", "false", "yes", "no", "on", "off"}:
        return raw
    raise ValueError("使用单行双引号字符串，name 和 MIT 可不加引号")


def parse_frontmatter(lines):
    if not lines or lines[0] != "---":
        raise ValueError("SKILL.md 首行应为 ---")
    try:
        stop = lines.index("---", 1)
    except ValueError as error:
        raise ValueError("缺少 frontmatter 结束分隔线 ---") from error

    fields = {}
    active_mapping = None
    for line_number, line in enumerate(lines[1:stop], start=2):
        match = re.fullmatch(r"( {2})?([a-z][a-z-]*):(?: (.+))?", line)
        if not match:
            raise ValueError(f"第 {line_number} 行不是此包使用的单行字段或两空格缩进 metadata")
        indent, key, raw = match.groups()
        if not indent:
            active_mapping = None
        if indent:
            if active_mapping is None:
                raise ValueError(f"第 {line_number} 行的缩进仅可用于 metadata")
            target = active_mapping
        else:
            target = fields
        if key in target:
            raise ValueError(f"第 {line_number} 行重复定义 {key}")
        if not indent and key == "metadata" and raw is None:
            target[key] = {}
            active_mapping = target[key]
        else:
            if raw is None or (indent and not raw.startswith('"')):
                raise ValueError(f"第 {line_number} 行 {key} 应为字符串，metadata 的值需双引号")
            try:
                target[key] = parse_scalar(raw)
            except ValueError as error:
                raise ValueError(f"第 {line_number} 行 {key}：{error}") from error
    return fields, stop + 1


def paths_in_body(body):
    paths = set(re.findall(r"\]\((?!https?://|#)([^)\s]+)\)", body))
    paths.update(re.findall(r"(?<![\w/])(?:assets|evals|references|scripts)/[A-Za-z0-9._/-]+", body))
    return paths


def validate(directory):
    lines = (directory / "SKILL.md").read_text(encoding="utf-8").splitlines()
    fields, header_lines = parse_frontmatter(lines)
    body = "\n".join(lines[header_lines:])
    errors = []

    if fields.keys() != FIELDS:
        missing = "、".join(sorted(FIELDS - fields.keys())) or "无"
        extra = "、".join(sorted(fields.keys() - FIELDS)) or "无"
        errors.append(f"frontmatter 字段不匹配。缺少 {missing}，额外 {extra}")
    name = fields.get("name", "")
    if len(name) > 64 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or name != directory.name:
        errors.append(f"name 要与目录名 {directory.name} 一致，使用 1–64 个小写字母、数字与单个分隔连字符")
    description = fields.get("description", "")
    if not 1 <= len(description.strip()) <= 1024:
        errors.append("description 长度应为 1–1024 字符")
    absent_triggers = [term for term in TRIGGERS if term not in description.lower()]
    if absent_triggers:
        errors.append("description 缺少触发词 " + "、".join(absent_triggers))
    if fields.get("license") != "MIT":
        errors.append("license 应为 MIT")
    if not 1 <= len(fields.get("compatibility", "").strip()) <= 500:
        errors.append("compatibility 长度应为 1–500 字符")
    metadata = fields.get("metadata")
    if not isinstance(metadata, dict) or metadata.keys() != METADATA or not all(metadata.values()):
        errors.append("metadata 应包含 version、author、language 三个非空字符串")
    if not body.strip() or len(lines) > MAX_LINES:
        errors.append(f"SKILL.md 应有正文且全文最多 {MAX_LINES} 行，当前 {len(lines)} 行")

    references = paths_in_body(body)
    for path in sorted(references | {"LICENSE"}):
        target = (directory / path.split("#", 1)[0]).resolve()
        if Path(path).is_absolute() or not target.is_relative_to(directory) or not target.is_file():
            errors.append(f"引用须指向 Skill 内实际存在的文件：{path}")
    return errors, len(description), len(lines), len(lines) - header_lines, len(references)


def main():
    parser = argparse.ArgumentParser(description="核对本 Skill 的受限 YAML frontmatter、命名、行数和相对引用。")
    parser.add_argument("directory", nargs="?", type=Path, default=Path(__file__).resolve().parents[1], help="Skill 目录，默认使用脚本所在的包")
    args = parser.parse_args()
    try:
        errors, description, lines, body, references = validate(args.directory.resolve())
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        print(f"Skill 校验失败：{error}", file=sys.stderr)
        return 1
    if errors:
        print("Skill 校验失败。", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Skill 校验通过。frontmatter、命名和相对文件引用有效。")
    print(f"description {description} 字符，全文 {lines} 行（正文 {body} 行），{references} 个不同引用文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
