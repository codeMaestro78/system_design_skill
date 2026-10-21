"""Unit tests for scripts/check_skill.py.

Every test builds a throwaway copy of a minimal skill package in a temporary
directory so the suite never depends on the live repository contents.
"""

from __future__ import annotations

import importlib.util
import os
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts" / "check_skill.py"


def load_module(name: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_module("check_skill", CHECKER_PATH)
CHECKER_SOURCE = CHECKER_PATH.read_text(encoding="utf-8")


def mutated_checker(*patches: tuple[str, str]) -> types.ModuleType:
    """Return an in-memory copy of the checker with ``patches`` applied."""
    source = CHECKER_SOURCE
    for old, new in patches:
        if old not in source:
            raise AssertionError(f"mutation target not found in checker: {old!r}")
        source = source.replace(old, new, 1)
    module = types.ModuleType("check_skill_mutated")
    module.__file__ = str(CHECKER_PATH)
    exec(compile(source, str(CHECKER_PATH), "exec"), module.__dict__)
    return module


BASE_SKILL = """---
name: system-design
description: A small fixture package used to exercise the skill package checker.
---

# System design

Fixture body.

- [Guide](references/guide.md)
- [Other](references/other.md)
"""

BASE_GUIDE = """# Guide

## Section One

Guide text.
"""

BASE_OTHER = """# Other

## Section Two

Other text.
"""

BASE_OPENAI = """interface:
  display_name: System Design
  short_description: Design and review complex software systems
  icon_small: assets/icon.svg
  icon_large: assets/icon.svg
policy:
  products:
  - chatgpt
  allow_implicit_invocation: true
"""

BASE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
    '<path d="M0 0h24v24H0z" fill="#FFD400"/></svg>\n'
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def png_bytes(width: int = 64, height: int = 64) -> bytes:
    """Build a tiny but structurally valid PNG."""
    import struct
    import zlib

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00\x00\x00\x00" * width for _ in range(height))
    return PNG_MAGIC + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


class PackageTestCase(unittest.TestCase):
    """Base class that builds a minimal, valid skill package per test."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.skill = self.root / "system-design"
        self.build()

    def build(self) -> None:
        skill = self.skill
        (skill / "references").mkdir(parents=True, exist_ok=True)
        (skill / "agents").mkdir(parents=True, exist_ok=True)
        (skill / "assets").mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(BASE_SKILL, encoding="utf-8")
        (skill / "references" / "guide.md").write_text(BASE_GUIDE, encoding="utf-8")
        (skill / "references" / "other.md").write_text(BASE_OTHER, encoding="utf-8")
        (skill / "agents" / "openai.yaml").write_text(BASE_OPENAI, encoding="utf-8")
        (skill / "assets" / "icon.svg").write_text(BASE_SVG, encoding="utf-8")

    def write(self, relpath: str, text: str, encoding: str = "utf-8") -> Path:
        path = self.skill / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding=encoding)
        return path

    def write_bytes(self, relpath: str, payload: bytes) -> Path:
        path = self.skill / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return path

    def append_skill(self, text: str) -> None:
        entry = self.skill / "SKILL.md"
        entry.write_text(entry.read_text(encoding="utf-8") + text, encoding="utf-8")

    def skill_text(self) -> str:
        return (self.skill / "SKILL.md").read_text(encoding="utf-8")

    def set_skill(self, text: str) -> None:
        (self.skill / "SKILL.md").write_text(text, encoding="utf-8")

    def errors(self, skill: Path | None = None) -> list[str]:
        return checker.check(skill or self.skill)


class BasePackageTests(PackageTestCase):
    def test_fixture_package_is_clean(self):
        self.assertEqual([], self.errors())

    def test_missing_skill_file_is_reported(self):
        (self.skill / "SKILL.md").unlink()
        errors = self.errors()
        self.assertEqual(1, len(errors))
        self.assertIn("SKILL.md", errors[0])

    def test_package_without_agents_or_assets_is_supported(self):
        (self.skill / "agents" / "openai.yaml").unlink()
        (self.skill / "assets" / "icon.svg").unlink()
        self.assertEqual([], self.errors())

    def test_name_must_match_directory(self):
        other = self.root / "other-name"
        other.mkdir()
        for item in self.skill.iterdir():
            item.rename(other / item.name)
        errors = self.errors(other)
        self.assertTrue(any("must match directory" in error for error in errors), errors)
        self.assertFalse(any("does not match the first heading" in error for error in errors))


class CrashSafetyTests(PackageTestCase):
    def test_non_utf8_file_is_reported(self):
        self.write_bytes("references/guide.md", b"# Guide\n\n\xff\xfe\x00broken\n")
        errors = self.errors()
        self.assertTrue(
            any(error.startswith("references/guide.md:") and "not valid UTF-8" in error for error in errors),
            errors,
        )

    def test_utf8_bom_is_reported_clearly(self):
        self.write_bytes(
            "SKILL.md",
            b"\xef\xbb\xbf" + BASE_SKILL.encode("utf-8"),
        )
        errors = self.errors()
        self.assertTrue(any("BOM" in error for error in errors), errors)
        self.assertFalse(
            any("must start with YAML frontmatter" in error for error in errors),
            errors,
        )

    def test_openai_yaml_invalid_interface_type_is_reported(self):
        self.write("agents/openai.yaml", "interface: oops\n")
        errors = self.errors()
        self.assertIn("agents/openai.yaml: interface must be a mapping", errors)

    def test_openai_yaml_icon_path_outside_skill_is_rejected(self):
        self.write(
            "agents/openai.yaml",
            BASE_OPENAI.replace("assets/icon.svg", "../../etc/x.svg", 1),
        )
        errors = self.errors()
        self.assertTrue(
            any("icon_small" in error and "leaves the skill package" in error for error in errors),
            errors,
        )

    def test_openai_yaml_missing_display_name_is_reported(self):
        self.write(
            "agents/openai.yaml",
            BASE_OPENAI.replace("  display_name: System Design\n", ""),
        )
        errors = self.errors()
        self.assertTrue(any("display_name" in error for error in errors), errors)

    def test_openai_yaml_missing_short_description_is_reported(self):
        self.write(
            "agents/openai.yaml",
            BASE_OPENAI.replace("  short_description: Design and review complex software systems\n", ""),
        )
        errors = self.errors()
        self.assertTrue(any("short_description" in error for error in errors), errors)

    def test_openai_yaml_non_boolean_policy_is_reported(self):
        self.write(
            "agents/openai.yaml",
            BASE_OPENAI.replace("allow_implicit_invocation: true", "allow_implicit_invocation: maybe"),
        )
        errors = self.errors()
        self.assertTrue(any("allow_implicit_invocation" in error for error in errors), errors)

    def test_empty_whitespace_link_is_reported(self):
        self.append_skill("\nBroken [bad]( ) link.\n")
        errors = self.errors()
        self.assertTrue(any("empty link target" in error for error in errors), errors)

    def test_check_never_raises_on_random_bytes(self):
        payloads = [
            b"\xff\xfe\x00\x01",
            b"\x80\x81\x82",
            bytes(range(256)),
            os.urandom(64),
            "é中文".encode("utf-16"),
        ]
        for index, payload in enumerate(payloads):
            with self.subTest(payload=index):
                self.build()
                self.write_bytes("SKILL.md", payload)
                self.write_bytes("references/guide.md", payload)
                self.write_bytes("references/other.md", payload)
                self.write_bytes("agents/openai.yaml", payload)
                self.write_bytes("assets/icon.svg", payload)
                errors = self.errors()
                self.assertIsInstance(errors, list)
                self.assertTrue(errors)


class LinkTests(PackageTestCase):
    def test_link_inside_code_block_is_ignored(self):
        self.append_skill("\n```markdown\nExample: [x](./missing.md) and [y](missing.md)\n```\n")
        errors = self.errors()
        self.assertFalse(any("missing link target" in error for error in errors), errors)

    def test_inline_code_link_is_ignored(self):
        self.append_skill("\nInline `[x](./missing.md)` stays untouched.\n")
        errors = self.errors()
        self.assertFalse(any("missing link target" in error for error in errors), errors)

    def test_link_with_query_string_resolves(self):
        self.append_skill("\n- [Guide](references/guide.md?v=2)\n")
        errors = self.errors()
        self.assertFalse(any("missing link target" in error for error in errors), errors)

    def test_fragment_match_is_case_insensitive(self):
        self.append_skill("\n- [Guide](references/guide.md#SECTION-ONE)\n")
        errors = self.errors()
        self.assertFalse(any("missing heading" in error for error in errors), errors)

    def test_reference_style_link_is_validated(self):
        self.append_skill("\n[ref]: ./nowhere.md\n")
        errors = self.errors()
        self.assertTrue(
            any("missing link target" in error and "nowhere.md" in error for error in errors),
            errors,
        )

    def test_reference_style_link_that_exists_is_accepted(self):
        self.append_skill("\n[ref]: ./references/guide.md\n")
        errors = self.errors()
        self.assertFalse(any("missing link target" in error for error in errors), errors)

    def test_autolink_with_unknown_scheme_is_reported(self):
        self.append_skill("\nSee <gopher://example.com/x> for details.\n")
        errors = self.errors()
        self.assertTrue(any("scheme" in error for error in errors), errors)

    def test_autolink_with_known_scheme_is_accepted(self):
        self.append_skill("\nSee <https://example.com/x> for details.\n")
        errors = self.errors()
        self.assertFalse(any("scheme" in error for error in errors), errors)
        self.assertFalse(any("missing link target" in error for error in errors), errors)

    def test_backslash_separator_is_normalised(self):
        self.append_skill("\n- [Guide](references\\guide.md)\n")
        errors = self.errors()
        self.assertFalse(any("missing link target" in error for error in errors), errors)

    def test_link_target_must_exist(self):
        self.append_skill("\n- [Nope](./missing.md)\n")
        errors = self.errors()
        self.assertTrue(any("missing link target" in error for error in errors), errors)

    def test_package_escape_is_detected(self):
        self.append_skill("\n- [Escape](../../etc/passwd)\n")
        errors = self.errors()
        self.assertTrue(any("link leaves skill package" in error for error in errors), errors)

    def test_heading_slug_matches_github_for_linked_heading(self):
        self.write(
            "references/guide.md",
            "# Guide\n\n## [Linked](http://x)\n\nText.\n",
        )
        self.append_skill("\n- [Guide](references/guide.md#linked)\n")
        errors = self.errors()
        self.assertFalse(any("missing heading" in error for error in errors), errors)
        self.assertIn("linked", checker.heading_slugs("# Guide\n\n## [Linked](http://x)\n"))

    def test_heading_slug_ignores_fenced_code(self):
        self.write(
            "references/guide.md",
            "# Guide\n\n```\n# patterns\n```\n\n## Section One\n",
        )
        self.append_skill("\n- [Guide](references/guide.md#patterns)\n")
        errors = self.errors()
        self.assertTrue(any("missing heading" in error for error in errors), errors)
        self.assertNotIn("patterns", checker.heading_slugs("# Guide\n\n```\n# patterns\n```\n"))

    def test_setext_heading_is_resolved(self):
        self.write("references/guide.md", "Guide Title\n============\n\nText.\n")
        self.append_skill("\n- [Guide](references/guide.md#guide-title)\n")
        errors = self.errors()
        self.assertFalse(any("missing heading" in error for error in errors), errors)
        self.assertIn("guide-title", checker.heading_slugs("Guide Title\n============\n"))

    def test_duplicate_headings_get_indexed_slugs(self):
        self.write(
            "references/guide.md",
            "# Guide\n\n## Dup\n\nText.\n\n## Dup\n\nText.\n\n## Dup\n",
        )
        slugs = checker.heading_slugs("# Guide\n\n## Dup\n\nText.\n\n## Dup\n\nText.\n\n## Dup\n")
        self.assertIn("dup", slugs)
        self.assertIn("dup-1", slugs)
        self.assertIn("dup-2", slugs)
        self.append_skill("\n- [First](references/guide.md#dup-1)\n")
        errors = self.errors()
        self.assertFalse(any("missing heading" in error for error in errors), errors)

    def test_emoji_headings_keep_their_emoji(self):
        slugs = checker.heading_slugs("# Guide\n\n## \U0001f680 Launch\n")
        self.assertIn("\U0001f680-launch", slugs)


class FrontmatterTests(PackageTestCase):
    def test_unknown_frontmatter_key_is_rejected(self):
        self.set_skill(BASE_SKILL.replace("name: system-design\n", "name: system-design\nauthor: Someone\n"))
        errors = self.errors()
        self.assertTrue(
            any("unknown frontmatter key" in error and "author" in error for error in errors),
            errors,
        )

    def test_licence_typo_is_rejected(self):
        self.set_skill(BASE_SKILL.replace("name: system-design\n", "name: system-design\nlicence: MIT\n"))
        errors = self.errors()
        self.assertTrue(
            any("unknown frontmatter key" in error and "licence" in error for error in errors),
            errors,
        )

    def test_metadata_must_be_string_map(self):
        self.set_skill(
            BASE_SKILL.replace(
                "name: system-design\n",
                "name: system-design\nmetadata:\n  owner: 42\n",
            )
        )
        errors = self.errors()
        self.assertTrue(any("metadata entries must be strings" in error for error in errors), errors)

    def test_metadata_must_be_a_mapping(self):
        self.set_skill(BASE_SKILL.replace("name: system-design\n", "name: system-design\nmetadata: nope\n"))
        errors = self.errors()
        self.assertTrue(any("metadata must be a mapping" in error for error in errors), errors)

    def test_compatibility_length_limit(self):
        self.set_skill(
            BASE_SKILL.replace("name: system-design\n", "name: system-design\ncompatibility: " + "x" * 501 + "\n")
        )
        errors = self.errors()
        self.assertTrue(any("compatibility" in error for error in errors), errors)

    def test_compatibility_within_limit_is_accepted(self):
        self.set_skill(
            BASE_SKILL.replace("name: system-design\n", "name: system-design\ncompatibility: " + "x" * 500 + "\n")
        )
        errors = self.errors()
        self.assertFalse(any("compatibility" in error for error in errors), errors)

    def test_allowed_tools_must_be_string_or_list(self):
        self.set_skill(BASE_SKILL.replace("name: system-design\n", "name: system-design\nallowed-tools: 5\n"))
        errors = self.errors()
        self.assertTrue(any("allowed-tools" in error for error in errors), errors)

    def test_allowed_tools_list_of_strings_is_accepted(self):
        self.set_skill(
            BASE_SKILL.replace(
                "name: system-design\n",
                "name: system-design\nallowed-tools:\n- Read\n- Write\n",
            )
        )
        errors = self.errors()
        self.assertFalse(any("allowed-tools" in error for error in errors), errors)

    def test_license_must_be_a_string(self):
        self.set_skill(BASE_SKILL.replace("name: system-design\n", "name: system-design\nlicense: 5\n"))
        errors = self.errors()
        self.assertTrue(any("license must be a nonempty string" in error for error in errors), errors)

    def test_license_is_cross_checked_with_the_license_file(self):
        (self.root / "LICENSE").write_text("MIT License\n\nCopyright (c) 2026\n", encoding="utf-8")
        self.set_skill(BASE_SKILL.replace("name: system-design\n", "name: system-design\nlicense: Apache-2.0\n"))
        errors = self.errors()
        self.assertTrue(any("does not match the LICENSE file" in error for error in errors), errors)

    def test_matching_license_is_accepted(self):
        (self.root / "LICENSE").write_text("MIT License\n\nCopyright (c) 2026\n", encoding="utf-8")
        self.set_skill(BASE_SKILL.replace("name: system-design\n", "name: system-design\nlicense: MIT\n"))
        errors = self.errors()
        self.assertFalse(any("LICENSE" in error for error in errors), errors)

    def test_name_must_match_first_heading(self):
        self.set_skill(BASE_SKILL.replace("# System design", "# Something else"))
        errors = self.errors()
        self.assertTrue(any("does not match the first heading" in error for error in errors), errors)


class BudgetTests(PackageTestCase):
    def test_skill_line_budget(self):
        self.append_skill("\n" + ("filler line\n" * 600))
        errors = self.errors()
        self.assertTrue(any("SKILL.md must be under 500 lines" in error for error in errors), errors)

    def test_reference_word_budget(self):
        filler = checker.MAX_REFERENCE_WORDS + 200
        self.write("references/guide.md", "# Guide\n\n" + ("word " * filler))
        errors = self.errors()
        self.assertTrue(
            any("word budget" in error and "references/guide.md" in error for error in errors),
            errors,
        )

    def test_reference_within_the_word_budget_is_accepted(self):
        self.write("references/guide.md", "# Guide\n\n" + ("word " * 100))
        errors = self.errors()
        self.assertFalse(any("word budget" in error for error in errors), errors)


class ReferenceTests(PackageTestCase):
    def test_nested_reference_must_be_linked(self):
        self.write("references/deep/nested.md", "# Nested\n\nText.\n")
        errors = self.errors()
        self.assertTrue(
            any("not linked directly" in error and "nested.md" in error for error in errors),
            errors,
        )

    def test_nested_reference_linked_from_skill_is_accepted(self):
        self.write("references/deep/nested.md", "# Nested\n\nText.\n")
        self.append_skill("\n- [Nested](references/deep/nested.md)\n")
        errors = self.errors()
        self.assertFalse(any("not linked directly" in error for error in errors), errors)

    def test_unlinked_reference_is_detected(self):
        self.write("references/new-topic.md", "# New topic\n")
        errors = self.errors()
        self.assertTrue(any("not linked directly" in error for error in errors), errors)

    def test_canonical_companion_rule(self):
        self.write("references/architecture-fundamentals.md", "# Architecture foundations\n\nShort.\n")
        self.write("references/architecture-method.md", "# Architecture method\n\nDeep.\n")
        self.append_skill(
            "\n- [Fundamentals](references/architecture-fundamentals.md)\n"
            "- [Method](references/architecture-method.md)\n"
        )
        expected = (
            "references/architecture-fundamentals.md: does not link its canonical "
            "guide references/architecture-method.md"
        )
        errors = self.errors()
        self.assertIn(expected, errors)

        self.write(
            "references/architecture-fundamentals.md",
            "# Architecture foundations\n\nSee the [method](architecture-method.md).\n",
        )
        errors = self.errors()
        self.assertNotIn(expected, errors)


class TemplateTests(PackageTestCase):
    def test_template_not_reachable_is_reported(self):
        self.write("templates/index.md", "# Templates\n\n- [Design doc](design-doc.md)\n")
        self.write("templates/design-doc.md", "# Design doc\n\nText.\n")
        self.write("templates/orphan.md", "# Orphan\n\nText.\n")
        self.append_skill("\n- [Templates](templates/index.md)\n")
        errors = self.errors()
        self.assertTrue(
            any("Template not reachable from SKILL.md" in error and "orphan.md" in error for error in errors),
            errors,
        )

    def test_transitively_reachable_templates_are_accepted(self):
        self.write("templates/index.md", "# Templates\n\n- [Design doc](design-doc.md)\n")
        self.write("templates/design-doc.md", "# Design doc\n\nText.\n")
        self.append_skill("\n- [Templates](templates/index.md)\n")
        errors = self.errors()
        self.assertFalse(any("Template not reachable" in error for error in errors), errors)

    def test_template_check_is_skipped_without_a_templates_directory(self):
        errors = self.errors()
        self.assertFalse(any("Template not reachable" in error for error in errors), errors)


class AssetTests(PackageTestCase):
    def test_svg_with_script_element_is_rejected(self):
        self.write(
            "assets/icon.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><script>alert(1)</script></svg>',
        )
        errors = self.errors()
        self.assertTrue(any("unsafe SVG element" in error for error in errors), errors)

    def test_svg_with_external_reference_is_rejected(self):
        self.write(
            "assets/icon.svg",
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use href="https://example.com/x.svg"/></svg>',
        )
        errors = self.errors()
        self.assertTrue(any("external reference" in error for error in errors), errors)

    def test_svg_missing_viewbox_is_rejected(self):
        self.write(
            "assets/icon.svg",
            '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>',
        )
        errors = self.errors()
        self.assertTrue(any("viewBox" in error for error in errors), errors)

    def test_svg_without_namespace_is_rejected(self):
        self.write("assets/icon.svg", '<svg viewBox="0 0 24 24"><path d="M0 0"/></svg>')
        errors = self.errors()
        self.assertTrue(any("namespace" in error for error in errors), errors)

    def test_svg_with_invalid_xml_is_rejected(self):
        self.write("assets/icon.svg", "<svg><path></svg>")
        errors = self.errors()
        self.assertTrue(any("invalid SVG XML" in error for error in errors), errors)

    def test_png_with_bad_magic_is_rejected(self):
        self.write_bytes("assets/logo.png", b"NOTAPNG" + b"\x00" * 32)
        errors = self.errors()
        self.assertTrue(any("bad magic bytes" in error for error in errors), errors)

    def test_png_without_ihdr_is_rejected(self):
        self.write_bytes("assets/logo.png", PNG_MAGIC + b"\x00" * 32)
        errors = self.errors()
        self.assertTrue(any("IHDR" in error for error in errors), errors)

    def test_non_square_png_is_rejected(self):
        self.write_bytes("assets/logo.png", png_bytes(64, 32))
        errors = self.errors()
        self.assertTrue(any("square" in error for error in errors), errors)

    def test_png_outside_the_size_range_is_rejected(self):
        self.write_bytes("assets/logo.png", png_bytes(8, 8))
        errors = self.errors()
        self.assertTrue(any("outside" in error for error in errors), errors)

    def test_valid_png_is_accepted(self):
        self.write_bytes("assets/logo.png", png_bytes(64, 64))
        errors = self.errors()
        self.assertFalse(any("PNG" in error for error in errors), errors)


class MutationSensitivityTests(PackageTestCase):
    """Disable individual checks and prove the matching scenario stops being reported."""

    def test_package_escape_check_is_load_bearing(self):
        self.append_skill("\n- [Escape](../../etc/passwd)\n")
        self.assertTrue(any("link leaves skill package" in error for error in self.errors()))
        mutated = mutated_checker(
            (
                """            if not destination.is_relative_to(skill_root):
                errors.append(f"{label}: link leaves skill package {target}")
                continue""",
                """            if False:
                errors.append(f"{label}: link leaves skill package {target}")
                continue""",
            )
        )
        errors = mutated.check(self.skill)
        self.assertFalse(any("link leaves skill package" in error for error in errors), errors)

    def test_name_versus_directory_check_is_load_bearing(self):
        other = self.root / "other-name"
        other.mkdir()
        for item in self.skill.iterdir():
            item.rename(other / item.name)
        self.assertTrue(any("must match directory" in error for error in self.errors(other)))
        mutated = mutated_checker(
            (
                """    elif name != skill.name:
        errors.append(f"name {name!r} must match directory {skill.name!r}")""",
                """    elif False:
        pass""",
            )
        )
        errors = mutated.check(other)
        self.assertFalse(any("must match directory" in error for error in errors), errors)

    def test_icon_check_is_load_bearing(self):
        self.write(
            "agents/openai.yaml",
            BASE_OPENAI.replace("icon_small: assets/icon.svg", "icon_small: assets/gone.svg"),
        )
        self.assertTrue(any("missing icon_small" in error for error in self.errors()))
        mutated = mutated_checker(
            (
                """                if not destination.is_file():
                    errors.append(f"agents/openai.yaml: missing {key} target {icon}")""",
                """                if False:
                    pass""",
            )
        )
        errors = mutated.check(self.skill)
        self.assertFalse(any("missing icon_small" in error for error in errors), errors)

    def test_description_length_check_is_load_bearing(self):
        self.set_skill(
            BASE_SKILL.replace(
                "description: A small fixture package used to exercise the skill package checker.",
                "description: " + "x" * 1100,
            )
        )
        self.assertTrue(any("description" in error for error in self.errors()))
        mutated = mutated_checker(
            (
                """    if not isinstance(description, str) or not (1 <= len(description) <= 1024):
        errors.append("description must be a nonempty string of at most 1024 characters")""",
                """    if False:
        pass""",
            )
        )
        errors = mutated.check(self.skill)
        self.assertFalse(any("description" in error for error in errors), errors)

    def test_link_target_existence_check_is_load_bearing(self):
        self.append_skill("\n- [Nope](./missing.md)\n")
        self.assertTrue(any("missing link target" in error for error in self.errors()))
        mutated = mutated_checker(
            (
                """            if not destination.is_file():
                errors.append(f"{label}: missing link target {target}")
                continue""",
                """            if False:
                pass""",
            )
        )
        errors = mutated.check(self.skill)
        self.assertFalse(any("missing link target" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
