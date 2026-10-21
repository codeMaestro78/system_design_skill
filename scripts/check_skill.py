#!/usr/bin/env python3
"""Check portable skill metadata, local links, assets, and reference discoverability.

The checker is deliberately defensive: every problem is reported as a message and
the script never raises, so a malformed package produces actionable output
instead of a traceback.
"""

from __future__ import annotations

import codecs
import html
import re
import struct
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "system-design"

NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
LINK = re.compile(r"\]\(([^)]+)\)")
REFERENCE_LINK = re.compile(r"^[ \t]{0,3}\[([^\]]+)\]:[ \t]*(\S+)", re.MULTILINE)
AUTOLINK = re.compile(r"<([a-zA-Z][a-zA-Z0-9+.\-]*:[^<>\s]*)>")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")

ALLOWED_FRONTMATTER_KEYS = (
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
)
KNOWN_SCHEMES = frozenset({"http", "https", "mailto", "ftp", "ftps", "tel"})

# Budgets. The SKILL.md line limit follows the Agent Skills spec; the reference
# word budget keeps progressive disclosure working (a reference is read on
# demand, so it must stay small enough to be worth opening).
MAX_COMPATIBILITY_CHARS = 500
MAX_SHORT_DESCRIPTION_CHARS = 120
MAX_SKILL_LINES = 500
MAX_REFERENCE_WORDS = 4000

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
UNSAFE_SVG_ELEMENTS = frozenset(
    {
        "script",
        "foreignobject",
        "image",
        "use",
        "text",
        "style",
        "font",
        "audio",
        "video",
    }
)
UNSAFE_SVG_PATTERNS = ("xlink:href", "href=", "url(", "@import", "base64", "data:")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PNG_MIN_SIDE = 16
PNG_MAX_SIDE = 4096

CANONICAL_COMPANIONS = {
    "architecture-fundamentals.md": "architecture-method.md",
    "scalability-and-capacity.md": "requirements-and-capacity.md",
    "data-and-storage.md": "data-architecture.md",
    "architecture-patterns.md": "pattern-catalog.md",
    "reliability-and-operations.md": "reliability-operations.md",
    "security-and-threat-modeling.md": "security-privacy.md",
    "ai-agent-systems.md": "ai-systems.md",
    "learning-and-interview.md": "interview-learning.md",
}


# ---------------------------------------------------------------------------
# Reading files without crashing
# ---------------------------------------------------------------------------


def read_text(path: Path) -> tuple[str | None, str | None]:
    """Return ``(text, error)`` for a UTF-8 text file; never raises."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        return None, f"could not be read ({exc.strerror or exc})"
    if data.startswith(codecs.BOM_UTF8):
        return None, "starts with a UTF-8 BOM (strip the BOM before parsing)"
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, "not valid UTF-8"


def relative(path: Path, root: Path) -> str:
    """Return a package-relative path string that never raises."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Markdown parsing helpers
# ---------------------------------------------------------------------------

_FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_FENCE_CLOSE = re.compile(r"^ {0,3}(`{3,}|~{3,})[ \t]*$")
CODE_SPAN = re.compile(r"(`+)(.*?)\1", re.DOTALL)
ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
SETEXT_HEADING = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
FRONTMATTER = re.compile(r"\A---[ \t]*\n.*?\n---[ \t]*(?:\n|\Z)", re.DOTALL)

_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK_TEXT = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_REFERENCE_LINK_TEXT = re.compile(r"\[([^\]]*)\]\[[^\]]*\]")
_AUTOLINK_TEXT = re.compile(r"<([a-zA-Z][a-zA-Z0-9+.\-]*:[^<>\s]*)>")
_HTML_TAG = re.compile(r"</?[a-zA-Z][^<>]*>")
_UNDERSCORE_EMPHASIS = re.compile(r"(?<![0-9A-Za-z])_([^_]+)_(?![0-9A-Za-z])")
_PARAGRAPH_BLOCK = re.compile(r"^(?:[-*+]|\d+[.)]|>)\s|^\[[^\]]+\]:")

# ASCII punctuation GitHub strips from anchors. Hyphens and underscores survive.
_ASCII_PUNCTUATION = "!\"#$%&'()*+,./:;<=>?@[\\]^`{|}~"
_SLUG_STRIP = re.compile("[" + re.escape(_ASCII_PUNCTUATION) + "\x00-\x1f\ufeff]")


def strip_fenced_code(text: str) -> str:
    """Blank out fenced code blocks so their contents are never parsed as prose."""
    output: list[str] = []
    fence_char = ""
    fence_length = 0
    for line in text.split("\n"):
        if not fence_char:
            match = _FENCE_OPEN.match(line)
            if match:
                marker = match.group(1)
                if marker[0] == "`" and "`" in line[match.end() :]:
                    output.append(line)
                    continue
                fence_char = marker[0]
                fence_length = len(marker)
                output.append("")
                continue
            output.append(line)
            continue
        closing = _FENCE_CLOSE.match(line)
        if closing and closing.group(1)[0] == fence_char and len(closing.group(1)) >= fence_length:
            fence_char = ""
            fence_length = 0
        output.append("")
    return "\n".join(output)


def strip_inline_code(text: str) -> str:
    """Remove inline code spans so their contents are never parsed as links."""
    return "\n".join(CODE_SPAN.sub(" ", line) for line in text.split("\n"))


def strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block from a Markdown document."""
    match = FRONTMATTER.match(text)
    if not match:
        return text
    return text[match.end() :]


def visible_text(text: str) -> str:
    """Reduce inline Markdown to the text a reader actually sees."""
    text = _IMAGE.sub(r"\1", text)
    text = _LINK_TEXT.sub(r"\1", text)
    text = _REFERENCE_LINK_TEXT.sub(r"\1", text)
    text = _AUTOLINK_TEXT.sub(r"\1", text)
    text = _HTML_TAG.sub(" ", text)
    text = CODE_SPAN.sub(lambda match: match.group(2), text)
    text = text.replace("*", "")
    text = _UNDERSCORE_EMPHASIS.sub(r"\1", text)
    return html.unescape(text).strip()


def slugify(text: str) -> str:
    """Return the GitHub-style anchor slug for heading text."""
    plain = visible_text(text).lower()
    plain = _SLUG_STRIP.sub("", plain)
    return re.sub(r"\s", "-", plain)


def iter_headings(markdown: str):
    """Yield ``(level, heading_text)`` for ATX and Setext headings."""
    text = strip_fenced_code(strip_frontmatter(markdown))
    previous = ""
    for line in text.split("\n"):
        atx = ATX_HEADING.match(line)
        if atx:
            content = atx.group(2) or ""
            content = re.sub(r"[ \t]+#+[ \t]*$", "", content)
            yield len(atx.group(1)), visible_text(content)
            previous = ""
            continue
        setext = SETEXT_HEADING.match(line)
        if setext and previous and not _PARAGRAPH_BLOCK.match(previous):
            yield (1 if setext.group(1)[0] == "=" else 2), visible_text(previous)
            previous = ""
            continue
        previous = line.strip()


def heading_slugs(markdown: str) -> set[str]:
    """Return the GitHub-compatible anchor slugs of a Markdown document."""
    counts: dict[str, int] = {}
    slugs: set[str] = set()
    for _level, text in iter_headings(markdown):
        base = slugify(text)
        if not base:
            continue
        count = counts.get(base, 0)
        counts[base] = count + 1
        slugs.add(f"{base}-{count}" if count else base)
    return slugs


def link_target(raw: str) -> str:
    """Return the destination of a Markdown link target, without title text."""
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith("<"):
        end = raw.find(">")
        if end != -1:
            return raw[1:end].strip()
    parts = raw.split()
    return parts[0] if parts else ""


def extract_links(text: str) -> list[tuple[str, str]]:
    """Return ``(kind, target)`` pairs for every link in a Markdown document."""
    stripped = strip_inline_code(strip_fenced_code(text))
    links: list[tuple[str, str]] = []
    for match in LINK.finditer(stripped):
        links.append(("inline", link_target(match.group(1))))
    for match in REFERENCE_LINK.finditer(stripped):
        links.append(("reference", link_target(match.group(2))))
    for match in AUTOLINK.finditer(stripped):
        links.append(("autolink", match.group(1)))
    return links


def resolve_path(base: Path, text: str) -> tuple[Path | None, str | None]:
    """Resolve ``text`` relative to ``base`` without raising."""
    try:
        return (base / text).resolve(), None
    except (ValueError, OSError) as exc:
        return None, f"invalid path ({exc})"


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str, errors: list[str]) -> tuple[dict | None, str]:
    """Return ``(metadata, body)`` for a SKILL.md document."""
    parts = text.split("---", 2)
    if len(parts) < 3 or parts[0].strip():
        errors.append("SKILL.md must start with YAML frontmatter delimited by ---")
        return None, text
    try:
        metadata = yaml.safe_load(parts[1])
    except Exception as exc:  # yaml errors and anything a loader may raise
        errors.append(f"Invalid YAML frontmatter: {exc}")
        return None, parts[2]
    if not isinstance(metadata, dict):
        errors.append("Frontmatter must be a YAML mapping")
        return None, parts[2]
    return metadata, parts[2]


def check_license_file(skill: Path, license_value: str, errors: list[str]) -> None:
    """Cross-check a declared license against a LICENSE file shipped next to it."""
    for candidate in (skill / "LICENSE", skill.parent / "LICENSE"):
        if not candidate.is_file():
            continue
        text, read_error = read_text(candidate)
        if read_error is not None:
            errors.append(f"{candidate.name}: {read_error}")
            return
        if license_value.strip().lower() not in text.lower():
            errors.append(f"license {license_value!r} does not match the {candidate.name} file")
        return


def check_frontmatter(metadata: dict, skill: Path, body: str, errors: list[str]) -> None:
    """Validate frontmatter keys, types, and cross-file consistency."""
    name = metadata.get("name")
    description = metadata.get("description")

    if not isinstance(name, str) or not (1 <= len(name) <= 64) or not NAME.fullmatch(name):
        errors.append("name must be 1-64 lowercase letters, digits, or single hyphens")
    elif name != skill.name:
        errors.append(f"name {name!r} must match directory {skill.name!r}")

    if not isinstance(description, str) or not (1 <= len(description) <= 1024):
        errors.append("description must be a nonempty string of at most 1024 characters")

    for key in metadata:
        if key not in ALLOWED_FRONTMATTER_KEYS:
            errors.append(f"unknown frontmatter key {key!r} (allowed: {', '.join(ALLOWED_FRONTMATTER_KEYS)})")

    license_value = metadata.get("license")
    if license_value is not None:
        if not isinstance(license_value, str) or not license_value.strip():
            errors.append("license must be a nonempty string")
        else:
            check_license_file(skill, license_value, errors)

    compatibility = metadata.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str):
            errors.append("compatibility must be a string")
        elif len(compatibility) > MAX_COMPATIBILITY_CHARS:
            errors.append(
                f"compatibility must be at most {MAX_COMPATIBILITY_CHARS} characters (got {len(compatibility)})"
            )

    extra = metadata.get("metadata")
    if extra is not None:
        if not isinstance(extra, dict):
            errors.append("metadata must be a mapping")
        else:
            for key, value in extra.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    errors.append(f"metadata entries must be strings (got {key!r}: {value!r})")

    tools = metadata.get("allowed-tools")
    if tools is not None:
        if isinstance(tools, str):
            pass
        elif isinstance(tools, list):
            for item in tools:
                if not isinstance(item, str):
                    errors.append("allowed-tools entries must be strings")
                    break
        else:
            errors.append("allowed-tools must be a string or a list of strings")

    if isinstance(name, str):
        for level, heading in iter_headings(body):
            if level != 1:
                continue
            base = slugify(heading)
            if base and base != name:
                errors.append(f"SKILL.md: name {name!r} does not match the first heading {heading!r}")
            break


# ---------------------------------------------------------------------------
# Size budgets
# ---------------------------------------------------------------------------


def check_size_budgets(text: str, skill: Path, errors: list[str]) -> None:
    """Enforce the SKILL.md line budget and the reference word budget."""
    lines = text.splitlines()
    if len(lines) > MAX_SKILL_LINES:
        errors.append(f"SKILL.md must be under {MAX_SKILL_LINES} lines (got {len(lines)})")
    references = skill / "references"
    if not references.is_dir():
        return
    for reference in sorted(references.rglob("*.md")):
        source, read_error = read_text(reference)
        if read_error is not None or source is None:
            continue
        words = len(source.split())
        if words > MAX_REFERENCE_WORDS:
            errors.append(f"{relative(reference, skill)}: {words} words exceeds the {MAX_REFERENCE_WORDS} word budget")


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------


def check_links(skill: Path, entry: Path, errors: list[str]) -> tuple[dict[Path, set[Path]], set[Path]]:
    """Validate every local link and return the link graph and direct references."""
    skill_root = skill.resolve()
    references_root = (skill / "references").resolve()
    edges: dict[Path, set[Path]] = defaultdict(set)
    direct: set[Path] = set()

    for markdown in sorted(skill.rglob("*.md")):
        source, read_error = read_text(markdown)
        if read_error is not None or source is None:
            errors.append(f"{relative(markdown, skill)}: {read_error}")
            continue
        label = relative(markdown, skill)
        for kind, target in extract_links(source):
            if not target:
                errors.append(f"{label}: empty link target")
                continue
            if kind == "autolink":
                scheme = target.split(":", 1)[0].lower()
                if scheme not in KNOWN_SCHEMES:
                    errors.append(f"{label}: unsupported link scheme {scheme!r}")
                continue
            if SCHEME.match(target):
                scheme = target.split(":", 1)[0].lower()
                if scheme not in KNOWN_SCHEMES:
                    errors.append(f"{label}: unsupported link scheme {scheme!r}")
                continue

            path_text, _, fragment = target.partition("#")
            path_text = path_text.split("?", 1)[0].replace("\\", "/")
            if not path_text:
                destination = markdown.resolve()
            else:
                destination, error = resolve_path(markdown.parent, unquote(path_text))
                if destination is None:
                    errors.append(f"{label}: invalid link target {target} ({error})")
                    continue

            if not destination.is_relative_to(skill_root):
                errors.append(f"{label}: link leaves skill package {target}")
                continue
            if not destination.is_file():
                errors.append(f"{label}: missing link target {target}")
                continue

            edges[markdown.resolve()].add(destination)
            if markdown == entry and destination.is_relative_to(references_root):
                direct.add(destination)

            if fragment:
                text, read_error = read_text(destination)
                if read_error is not None or text is None:
                    errors.append(f"{label}: missing heading in {target}")
                    continue
                anchors = {anchor.lower() for anchor in heading_slugs(text)}
                if unquote(fragment).lower() not in anchors:
                    errors.append(f"{label}: missing heading in {target}")

    return edges, direct


def check_reference_links(skill: Path, direct: set[Path], errors: list[str]) -> None:
    """Every reference file must be linked directly from SKILL.md."""
    references = skill / "references"
    if not references.is_dir():
        return
    for reference in sorted(references.rglob("*.md")):
        if reference.resolve() in direct:
            continue
        if reference.parent == references:
            name = reference.name
        else:
            name = relative(reference, skill)
        errors.append(f"Reference not linked directly from SKILL.md: {name}")


def check_canonical_companions(skill: Path, edges: dict[Path, set[Path]], errors: list[str]) -> None:
    """Every compact guide must point at its canonical detailed companion."""
    references = skill / "references"
    for compact, detailed in CANONICAL_COMPANIONS.items():
        compact_path = references / compact
        detailed_path = references / detailed
        if not compact_path.is_file() or not detailed_path.is_file():
            continue
        if detailed_path.resolve() in edges.get(compact_path.resolve(), set()):
            continue
        errors.append(f"references/{compact}: does not link its canonical guide references/{detailed}")


def reachable_files(entry: Path, edges: dict[Path, set[Path]]) -> set[Path]:
    """Return every file reachable from ``entry`` by following validated links."""
    seen: set[Path] = set()
    queue = [entry]
    while queue:
        current = queue.pop()
        if current in seen:
            continue
        seen.add(current)
        for neighbour in edges.get(current, ()):  # type: ignore[arg-type]
            if neighbour not in seen:
                queue.append(neighbour)
    return seen


def check_templates(skill: Path, entry: Path, edges: dict[Path, set[Path]], errors: list[str]) -> None:
    """Every template must be reachable from SKILL.md, directly or transitively."""
    templates = skill / "templates"
    if not templates.is_dir():
        return
    reachable = reachable_files(entry.resolve(), edges)
    for template in sorted(templates.rglob("*.md")):
        if template.resolve() in reachable:
            continue
        errors.append(f"Template not reachable from SKILL.md: {relative(template, skill)}")


# ---------------------------------------------------------------------------
# agents/openai.yaml
# ---------------------------------------------------------------------------


def check_openai_yaml(skill: Path, errors: list[str]) -> None:
    """Validate the agent interface manifest and its icon references."""
    interface_file = skill / "agents" / "openai.yaml"
    if not interface_file.is_file():
        return
    text, read_error = read_text(interface_file)
    if read_error is not None or text is None:
        errors.append(f"agents/openai.yaml: {read_error}")
        return
    try:
        data = yaml.safe_load(text)
    except Exception as exc:
        errors.append(f"agents/openai.yaml: invalid YAML: {exc}")
        return
    if data is None:
        return
    if not isinstance(data, dict):
        errors.append("agents/openai.yaml: top level must be a mapping")
        return

    interface = data.get("interface")
    if interface is not None:
        if not isinstance(interface, dict):
            errors.append("agents/openai.yaml: interface must be a mapping")
        else:
            display_name = interface.get("display_name")
            if not isinstance(display_name, str) or not display_name.strip():
                errors.append("agents/openai.yaml: interface.display_name must be a nonempty string")
            short_description = interface.get("short_description")
            if not isinstance(short_description, str) or not short_description.strip():
                errors.append("agents/openai.yaml: interface.short_description must be a nonempty string")
            elif len(short_description) > MAX_SHORT_DESCRIPTION_CHARS:
                errors.append(
                    "agents/openai.yaml: interface.short_description must be at most "
                    f"{MAX_SHORT_DESCRIPTION_CHARS} characters (got {len(short_description)})"
                )
            for key in ("icon_small", "icon_large"):
                icon = interface.get(key)
                if icon is None:
                    continue
                if not isinstance(icon, str) or not icon.strip():
                    errors.append(f"agents/openai.yaml: interface.{key} must be a nonempty string")
                    continue
                destination, error = resolve_path(skill, icon)
                if destination is None:
                    errors.append(f"agents/openai.yaml: invalid {key} target {icon} ({error})")
                    continue
                if not destination.is_relative_to(skill.resolve()):
                    errors.append(f"agents/openai.yaml: {key} path leaves the skill package: {icon}")
                    continue
                if not destination.is_file():
                    errors.append(f"agents/openai.yaml: missing {key} target {icon}")

    policy = data.get("policy")
    if policy is not None:
        if not isinstance(policy, dict):
            errors.append("agents/openai.yaml: policy must be a mapping")
        else:
            allow = policy.get("allow_implicit_invocation")
            if allow is not None and not isinstance(allow, bool):
                errors.append("agents/openai.yaml: policy.allow_implicit_invocation must be a boolean")


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


def check_svg(path: Path, skill: Path, errors: list[str]) -> None:
    """Validate that an SVG asset is safe, well formed, and self contained."""
    label = relative(path, skill)
    text, read_error = read_text(path)
    if read_error is not None or text is None:
        errors.append(f"{label}: {read_error}")
        return
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        errors.append(f"{label}: invalid SVG XML: {exc}")
        return
    if not isinstance(root.tag, str) or not root.tag.endswith("svg"):
        errors.append(f"{label}: root element must be <svg>")
        return
    if not root.tag.startswith("{" + SVG_NAMESPACE + "}"):
        errors.append(f"{label}: root element must use the SVG namespace {SVG_NAMESPACE}")
    if not root.get("viewBox"):
        errors.append(f"{label}: missing viewBox")
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        local = element.tag.rsplit("}", 1)[-1].lower()
        if local in UNSAFE_SVG_ELEMENTS:
            errors.append(f"{label}: unsafe SVG element <{local}>")
        for name, value in element.attrib.items():
            key = name.rsplit("}", 1)[-1].lower()
            if key.startswith("on"):
                errors.append(f"{label}: inline event handler {name}={value!r}")
            if key == "href":
                errors.append(f"{label}: external reference attribute {name}")
    lowered = text.lower()
    for pattern in UNSAFE_SVG_PATTERNS:
        if pattern in lowered:
            errors.append(f"{label}: contains disallowed {pattern}")


def check_png(path: Path, skill: Path, errors: list[str]) -> None:
    """Validate that a PNG asset has correct magic bytes and sane dimensions."""
    label = relative(path, skill)
    try:
        data = path.read_bytes()
    except OSError as exc:
        errors.append(f"{label}: could not be read ({exc.strerror or exc})")
        return
    if not data.startswith(PNG_MAGIC):
        errors.append(f"{label}: not a PNG file (bad magic bytes)")
        return
    if len(data) < 24 or data[12:16] != b"IHDR":
        errors.append(f"{label}: missing IHDR chunk")
        return
    width, height = struct.unpack(">II", data[16:24])
    if width != height:
        errors.append(f"{label}: PNG must be square (got {width}x{height})")
    if not (PNG_MIN_SIDE <= width <= PNG_MAX_SIDE) or not (PNG_MIN_SIDE <= height <= PNG_MAX_SIDE):
        errors.append(f"{label}: PNG dimensions {width}x{height} are outside {PNG_MIN_SIDE}..{PNG_MAX_SIDE}")


def check_assets(skill: Path, errors: list[str]) -> None:
    """Validate every SVG and PNG asset shipped with the skill."""
    assets = skill / "assets"
    if not assets.is_dir():
        return
    for path in sorted(assets.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix == ".svg":
            check_svg(path, skill, errors)
        elif suffix == ".png":
            check_png(path, skill, errors)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def check(skill: Path = SKILL) -> list[str]:
    """Validate a skill package and return a list of human readable problems."""
    errors: list[str] = []
    try:
        _check(Path(skill), errors)
    except Exception as exc:  # the checker must never crash on hostile input
        errors.append(f"internal checker error: {exc!r}")
    return errors


def _check(skill: Path, errors: list[str]) -> None:
    entry = skill / "SKILL.md"
    if not entry.is_file():
        errors.append(f"Missing {entry}")
        return

    text, read_error = read_text(entry)
    if read_error is not None or text is None:
        errors.append(f"SKILL.md: {read_error}")
        return

    metadata, body = parse_frontmatter(text, errors)
    if metadata is None:
        return

    check_frontmatter(metadata, skill, body, errors)
    check_size_budgets(text, skill, errors)

    edges, direct = check_links(skill, entry, errors)
    check_reference_links(skill, direct, errors)
    check_canonical_companions(skill, edges, errors)
    check_templates(skill, entry, edges, errors)
    check_openai_yaml(skill, errors)
    check_assets(skill, errors)


if __name__ == "__main__":
    problems = check()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)
    print("Skill metadata, local links, and reference routing: OK")
