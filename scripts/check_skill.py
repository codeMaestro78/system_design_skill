#!/usr/bin/env python3
"""Check portable skill metadata, local links, and reference discoverability."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "system-design"
LINK = re.compile(r"\]\(([^)]+)\)")
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def heading_slugs(markdown: str) -> set[str]:
    counts: dict[str, int] = {}
    slugs = set()
    for line in markdown.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        base = re.sub(r"[^\w -]", "", match.group(1).lower()).replace(" ", "-")
        count = counts.get(base, 0)
        counts[base] = count + 1
        slugs.add(f"{base}-{count}" if count else base)
    return slugs


def check(skill: Path = SKILL) -> list[str]:
    errors: list[str] = []
    entry = skill / "SKILL.md"
    if not entry.is_file():
        return [f"Missing {entry}"]
    content = entry.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3 or parts[0].strip():
        return ["SKILL.md must start with YAML frontmatter delimited by ---"]
    try:
        metadata = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        return [f"Invalid YAML frontmatter: {exc}"]
    if not isinstance(metadata, dict):
        return ["Frontmatter must be a YAML mapping"]
    name = metadata.get("name")
    description = metadata.get("description")
    if not isinstance(name, str) or not (1 <= len(name) <= 64) or not NAME.fullmatch(name):
        errors.append("name must be 1-64 lowercase letters, digits, or single hyphens")
    elif name != skill.name:
        errors.append(f"name {name!r} must match directory {skill.name!r}")
    if not isinstance(description, str) or not (1 <= len(description) <= 1024):
        errors.append("description must be a nonempty string of at most 1024 characters")

    direct_references: set[Path] = set()
    for markdown in sorted(skill.rglob("*.md")):
        source = markdown.read_text(encoding="utf-8")
        for raw in LINK.findall(source):
            target = raw.strip().strip("<>").split()[0]
            if target.startswith(("https://", "http://", "mailto:")):
                continue
            path_text, _, fragment = target.partition("#")
            destination = (markdown.parent / unquote(path_text)).resolve() if path_text else markdown.resolve()
            if not destination.is_relative_to(skill.resolve()):
                errors.append(f"{markdown.relative_to(skill)}: link leaves skill package {target}")
                continue
            if not destination.is_file():
                errors.append(f"{markdown.relative_to(skill)}: missing link target {target}")
                continue
            if markdown == entry and destination.parent == (skill / "references").resolve():
                direct_references.add(destination)
            if fragment and unquote(fragment) not in heading_slugs(destination.read_text(encoding="utf-8")):
                errors.append(f"{markdown.relative_to(skill)}: missing heading in {target}")
    for reference in sorted((skill / "references").glob("*.md")):
        if reference.resolve() not in direct_references:
            errors.append(f"Reference not linked directly from SKILL.md: {reference.name}")

    interface_file = skill / "agents" / "openai.yaml"
    if interface_file.is_file():
        try:
            interface = yaml.safe_load(interface_file.read_text(encoding="utf-8"))
            icons = interface.get("interface", {}) if isinstance(interface, dict) else {}
            for key in ("icon_small", "icon_large"):
                icon = icons.get(key)
                if icon and not (skill / icon).is_file():
                    errors.append(f"agents/openai.yaml: missing {key} target {icon}")
        except yaml.YAMLError as exc:
            errors.append(f"agents/openai.yaml: invalid YAML: {exc}")
    return errors


if __name__ == "__main__":
    problems = check()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)
    print("Skill metadata, local links, and reference routing: OK")
