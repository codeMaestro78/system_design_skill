#!/usr/bin/env python3
"""Build a reproducible ZIP archive of the system-design skill package.

The archive is deterministic on purpose: entries are sorted by archive path,
timestamps are fixed, permissions are normalized, and the compression level is
pinned. Two runs over the same tree produce byte-identical archives, so the
SHA-256 of the archive is a usable build fingerprint. CI runs this script with
``--check`` to prove that property.

Usage:
    python scripts/package.py [--out DIR] [--variant full|agents]
    python scripts/package.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "system-design"
SKILL_NAME = "system-design"

#: Directories copied from the skill folder, in inclusion order.
INCLUDE_DIRS = ("references", "agents", "assets", "templates")
#: Directories copied by the "agents" variant, which omits binary assets.
AGENTS_INCLUDE_DIRS = ("references", "agents", "templates")
#: Repository files carried into the archive so the package keeps its terms.
TERMS_FILES = ("LICENSE", "NOTICE")

EXCLUDED_DIRS = {"__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"}
EXCLUDED_NAMES = {".DS_Store"}
EXCLUDED_SUFFIXES = (".pyc", ".pyo")

#: Fixed archive timestamp: 2026-01-01 00:00:00.
TIMESTAMP = (2026, 1, 1, 0, 0, 0)
#: Normalized regular-file mode (0o644) stored in the high zip attribute bits.
FILE_MODE = 0o100644
COMPRESS_LEVEL = 9

VARIANTS = ("full", "agents")


def is_excluded(path: Path) -> bool:
    """Report whether a path is build noise that never enters the archive."""
    if path.name in EXCLUDED_NAMES:
        return True
    if path.suffix in EXCLUDED_SUFFIXES:
        return True
    return any(part in EXCLUDED_DIRS for part in path.parts)


def skill_files(variant: str) -> list[Path]:
    """Return the skill files to package, sorted by path relative to the skill."""
    if variant not in VARIANTS:
        raise ValueError(f"Unknown variant: {variant}")
    entry = SKILL / "SKILL.md"
    if not entry.is_file():
        raise FileNotFoundError(f"Missing {entry}")
    files = [entry]
    directories = AGENTS_INCLUDE_DIRS if variant == "agents" else INCLUDE_DIRS
    for name in directories:
        directory = SKILL / name
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or is_excluded(path.relative_to(SKILL)):
                continue
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(SKILL).as_posix())


def entries(variant: str) -> list[tuple[str, Path]]:
    """Return (archive path, source path) pairs for the requested variant."""
    collected: list[tuple[str, Path]] = []
    for path in skill_files(variant):
        relative = path.relative_to(SKILL).as_posix()
        collected.append((f"{SKILL_NAME}/{relative}", path))
    for name in TERMS_FILES:
        source = ROOT / name
        if not source.is_file():
            continue
        collected.append((name, source))
        collected.append((f"{SKILL_NAME}/{name}", source))
    return sorted(collected, key=lambda item: item[0])


def archive_bytes(archive_path: str, source: Path, variant: str) -> bytes:
    """Return the bytes to store for one archive entry.

    The ``agents`` variant omits ``assets/`` but keeps ``agents/openai.yaml``,
    so the icon keys would point at files that are not in the archive. Strip
    them rather than ship a manifest with dangling paths.
    """
    raw = source.read_bytes()
    if variant != "agents" or not source.is_relative_to(SKILL):
        return raw
    if source.relative_to(SKILL).as_posix() != "agents/openai.yaml":
        return raw
    interface = yaml.safe_load(raw.decode("utf-8")) or {}
    icons = interface.get("interface")
    if isinstance(icons, dict):
        for key in ("icon_small", "icon_large"):
            icons.pop(key, None)
    return yaml.safe_dump(interface, sort_keys=False, allow_unicode=True).encode("utf-8")


def build(target: Path, variant: str) -> str:
    """Write the archive for `variant` to `target` and return its SHA-256."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=COMPRESS_LEVEL) as archive:
        for archive_path, source in entries(variant):
            info = zipfile.ZipInfo(archive_path, date_time=TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = FILE_MODE << 16
            info.create_system = 3
            info.create_version = 20
            info.extract_version = 20
            archive.writestr(info, archive_bytes(archive_path, source, variant))
    return digest(target)


def digest(path: Path) -> str:
    """Return the hexadecimal SHA-256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive_name(variant: str) -> str:
    """Return the file name used for a variant."""
    return "system-design.zip" if variant == "full" else "system-design-agents.zip"


def check() -> int:
    """Build every variant twice and confirm the archives are identical."""
    failures = 0
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for variant in VARIANTS:
            digests = []
            for index in (1, 2):
                target = directory / f"{variant}-{index}.zip"
                digests.append(build(target, variant))
            if digests[0] != digests[1]:
                failures += 1
                print(f"{variant}: NOT deterministic ({digests[0]} != {digests[1]})")
            else:
                print(f"{variant}: deterministic sha256={digests[0]}")
    if failures:
        print("Packaging check failed: archives differ between builds", file=sys.stderr)
        return 1
    print("Packaging check passed: repeated builds are byte-identical")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "dist",
        help="Directory that receives the archive (default: dist/)",
    )
    parser.add_argument(
        "--variant",
        choices=VARIANTS,
        default="full",
        help="full keeps every asset, agents omits assets/",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Build every variant twice and verify the archives are identical",
    )
    args = parser.parse_args()

    if args.check:
        return check()

    target = args.out / archive_name(args.variant)
    try:
        sha256 = build(target, args.variant)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Packaging failed: {exc}", file=sys.stderr)
        return 1
    print(f"{target}")
    print(f"sha256 {sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
