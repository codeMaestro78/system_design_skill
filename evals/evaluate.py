#!/usr/bin/env python3
"""Prepare portable behavior cases and summarize evidence-backed human reviews.

The harness is deliberately small: it prepares a prompt, freezes a review form
that pins the exact skill revision, prompt, and response bytes, and then checks
a human review against that form. It never judges architecture quality itself.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CASES = HERE / "cases.json"
FIXTURE = HERE / "fixtures" / "partial-repository"
SKILL = ROOT / "system-design"
RESULTS = HERE / "results"

CASE_KEYS = frozenset({"id", "mode", "prompt", "criteria", "red_flags", "reference_comparison"})
ANCHOR_LEVELS = ("2", "1", "0")
FIXTURE_PLACEHOLDER = "{{FIXTURE_DIR}}"

# The fixture is a partial repository: it must stay exactly this tree, because
# a case that claims to review a repository only means something when the
# repository is the same everywhere. A missing file changes what the reviewer
# can see; an extra file lets a case quietly rely on something that is not
# part of the fixture.
FIXTURE_FILES = (
    ".env",
    ".github/workflows/ci.yml",
    ".gitignore",
    "Dockerfile",
    "README.md",
    "docker-compose.yml",
    "docs/ARCHITECTURE.md",
    "migrations/001_init.sql",
    "openapi.yaml",
    "package.json",
    "src/orders.js",
    "test/orders.test.js",
)

# Characters that are safe in a single path component of a result file name.
UNSAFE_NAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")
NAME_LIMIT = 64


# --------------------------------------------------------------------------- #
# paths
# --------------------------------------------------------------------------- #
def _relative(path: Path) -> str:
    """A path relative to the repository root when it is inside it."""
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _safe_name(value: str, limit: int = NAME_LIMIT) -> str:
    """A single path component that cannot escape its directory.

    Every character outside ``[A-Za-z0-9._-]`` becomes ``-`` and the result is
    truncated, so a value taken from an untrusted assessment can never add a
    directory separator. A name that is only dots is replaced as well, so the
    result is never the parent directory itself.
    """
    cleaned = UNSAFE_NAME_CHARS.sub("-", str(value))[:limit]
    if not cleaned.strip("."):
        cleaned = "-"
    return cleaned


def _within(directory: Path, target: Path) -> bool:
    """True when ``target`` resolves inside ``directory``."""
    try:
        return target.resolve().is_relative_to(directory.resolve())
    except (OSError, ValueError):
        return False


# --------------------------------------------------------------------------- #
# case catalogue
# --------------------------------------------------------------------------- #
def cases() -> dict[str, dict]:
    raw = json.loads(CASES.read_text(encoding="utf-8"))
    return {case["id"]: case for case in raw}


def flag_ids(case: dict) -> list[str]:
    """Identifiers for the case's red flags, in definition order.

    Bare-string red flags (the legacy shape) fall back to positional ids so an
    in-flight case file can still be scored; `validate()` reports the legacy
    shape as an error because the scoring path needs real ids.
    """
    identifiers: list[str] = []
    for index, flag in enumerate(case.get("red_flags") or [], start=1):
        if isinstance(flag, dict):
            candidate = flag.get("id")
            if isinstance(candidate, str) and candidate.strip():
                identifiers.append(candidate)
                continue
        identifiers.append(f"flag-{index}")
    return identifiers


def flag_texts(case: dict) -> list[str]:
    texts: list[str] = []
    for flag in case.get("red_flags") or []:
        if isinstance(flag, dict):
            texts.append(str(flag.get("text") or ""))
        else:
            texts.append(str(flag))
    return texts


def _anchors(criterion: dict) -> dict[str, str]:
    anchors = criterion.get("anchors")
    if not isinstance(anchors, dict):
        return {level: "" for level in ANCHOR_LEVELS}
    return {level: str(anchors.get(level) or "") for level in ANCHOR_LEVELS}


def allowed_routes(case: dict) -> set[str]:
    routes = case.get("reference_comparison") or {}
    if not isinstance(routes, dict):
        return {"automatic"}
    return {"automatic", *routes.keys()}


def _filled(value) -> bool:
    """True when a manifest field holds a non-empty string."""
    return isinstance(value, str) and bool(value.strip())


# --------------------------------------------------------------------------- #
# digests
# --------------------------------------------------------------------------- #
def skill_digest(root: Path = SKILL) -> str:
    """Hash the whole skill tree so a review pins the exact skill revision.

    Files are sorted by relative POSIX path and hashed as
    ``path\\0sha256(content)\\n`` so the result is stable across machines.
    """
    if not root.is_dir():
        return ""
    entries: list[str] = []
    files = [path for path in root.rglob("*") if path.is_file()]
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        entries.append(f"{relative}\0{hashlib.sha256(path.read_bytes()).hexdigest()}\n")
    return hashlib.sha256("".join(entries).encode("utf-8")).hexdigest()


def normalised_prompt(case: dict, route: str = "automatic") -> str:
    """The prompt as sent, with the machine-specific fixture path folded back."""
    text = prompt(case, route)
    return text.replace(str(FIXTURE.resolve()), FIXTURE_PLACEHOLDER)


def prompt_digest(case: dict, route: str = "automatic") -> str:
    """Hash of the exact prompt text sent to the agent (machine independent)."""
    return hashlib.sha256(normalised_prompt(case, route).encode("utf-8")).hexdigest()


def response_digest(case: dict, route: str, response: bytes) -> str:
    """Hash the route, the prompt, and the response bytes together.

    Folding the route and prompt into the digest means a response scored under
    the wrong route can no longer pass.
    """
    digest = hashlib.sha256()
    digest.update(route.encode("utf-8"))
    digest.update(b"\0")
    digest.update(prompt_digest(case, route).encode("utf-8"))
    digest.update(b"\0")
    digest.update(response)
    return digest.hexdigest()


# --------------------------------------------------------------------------- #
# validation
# --------------------------------------------------------------------------- #
def validate() -> list[str]:
    errors: list[str] = []
    try:
        raw = json.loads(CASES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Cannot read cases: {exc}"]
    if not isinstance(raw, list) or not raw:
        return ["cases.json must contain a nonempty array"]
    seen: set[str] = set()
    for case in raw:
        if not isinstance(case, dict):
            errors.append("Each case must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append("Every case needs a nonempty id")
            continue
        if case_id in seen:
            errors.append(f"Duplicate case id: {case_id}")
        seen.add(case_id)
        unknown = sorted(set(case) - CASE_KEYS)
        if unknown:
            errors.append(f"{case_id}: unknown case keys: {', '.join(unknown)}")
        for field in ("mode", "prompt"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                errors.append(f"{case_id}: missing {field}")
        errors.extend(_validate_criteria(case))
        errors.extend(_validate_red_flags(case))
        errors.extend(_validate_routes(case))
    errors.extend(_validate_fixture())
    return errors


def _validate_fixture() -> list[str]:
    """Check the partial repository fixture against its expected file tree.

    The tree is walked with ``rglob`` so nested files are included, and every
    file is compared with the expected set in both directions: a missing file
    and an unexpected file are both errors.
    """
    errors: list[str] = []
    if not FIXTURE.is_dir():
        errors.append(f"Partial repository fixture is missing {_relative(FIXTURE)}")
        return errors
    present = {path.relative_to(FIXTURE).as_posix() for path in FIXTURE.rglob("*") if path.is_file()}
    expected = set(FIXTURE_FILES)
    for relative in sorted(expected - present):
        errors.append(f"Partial repository fixture is missing {relative}")
    for relative in sorted(present - expected):
        errors.append(f"Partial repository fixture has an unexpected file: {relative}")
    return errors


def _validate_criteria(case: dict) -> list[str]:
    errors: list[str] = []
    case_id = case["id"]
    criteria = case.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        errors.append(f"{case_id}: needs criteria")
        return errors
    criterion_ids: set[str] = set()
    for criterion in criteria:
        if not isinstance(criterion, dict):
            errors.append(f"{case_id}: invalid criterion")
            continue
        cid = criterion.get("id")
        if not isinstance(cid, str) or not cid or cid in criterion_ids:
            errors.append(f"{case_id}: missing or duplicate criterion id {cid!r}")
        criterion_ids.add(cid)
        if not isinstance(criterion.get("expect"), str) or not criterion["expect"].strip():
            errors.append(f"{case_id}/{cid}: missing expectation")
        if not isinstance(criterion.get("critical"), bool):
            errors.append(f"{case_id}/{cid}: critical must be boolean")
        anchors = criterion.get("anchors")
        if not isinstance(anchors, dict):
            errors.append(f"{case_id}/{cid}: needs anchors for scores 2, 1 and 0")
            continue
        for level in ANCHOR_LEVELS:
            text = anchors.get(level)
            if not isinstance(text, str) or not text.strip():
                errors.append(f"{case_id}/{cid}: anchor for score {level} is missing")
    return errors


def _validate_red_flags(case: dict) -> list[str]:
    errors: list[str] = []
    case_id = case["id"]
    if "red_flags" not in case:
        return errors
    flags = case["red_flags"]
    if not isinstance(flags, list):
        errors.append(f"{case_id}: red_flags must be an array")
        return errors
    seen: set[str] = set()
    for index, flag in enumerate(flags, start=1):
        if isinstance(flag, str):
            errors.append(
                f'{case_id}: red flag {index} is a bare string; the scoring path needs an object with "id" and "text"'
            )
            continue
        if not isinstance(flag, dict):
            errors.append(f"{case_id}: invalid red flag {index}")
            continue
        identifier = flag.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"{case_id}: red flag {index} is missing a nonempty id")
        elif identifier in seen:
            errors.append(f"{case_id}: duplicate red flag id {identifier}")
        else:
            seen.add(identifier)
        text = flag.get("text")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{case_id}/{identifier or index}: red flag is missing text")
    return errors


def _validate_routes(case: dict) -> list[str]:
    errors: list[str] = []
    case_id = case["id"]
    routes = case.get("reference_comparison")
    if routes is None:
        return errors
    if not isinstance(routes, dict):
        errors.append(f"{case_id}: reference_comparison must be an object")
        return errors
    if not routes:
        return errors
    if set(routes) != {"compact", "detailed"}:
        errors.append(f"{case_id}: comparison needs compact and detailed routes")
    for route, path in routes.items():
        if not isinstance(path, str) or not (SKILL / path).is_file():
            errors.append(f"{case_id}: missing {route} comparison reference")
    return errors


# --------------------------------------------------------------------------- #
# prompt and review template
# --------------------------------------------------------------------------- #
def prompt(case: dict, route: str = "automatic") -> str:
    text = case["prompt"].replace(FIXTURE_PLACEHOLDER, str(FIXTURE.resolve()))
    if route == "automatic":
        return text
    paths = case.get("reference_comparison") or {}
    if route not in paths:
        raise ValueError(f"No {route} comparison route for {case['id']}")
    return f"For this evaluation, consult the skill's {paths[route]} reference for the data topic.\n\n{text}"


def template(case: dict, response: Path, route: str = "automatic") -> dict:
    """Freeze a review form that pins the skill, the prompt, and the response."""
    return {
        "case_id": case["id"],
        "route": route,
        "response_sha256": response_digest(case, route, response.read_bytes()),
        "run_manifest": {
            "skill_sha256": skill_digest(),
            "prompt_sha256": prompt_digest(case, route),
            "model": "",
            "reviewer": "",
            "date_utc": "",
        },
        "criteria": {
            item["id"]: {
                "score": None,
                "evidence": "",
                "anchors": _anchors(item),
            }
            for item in case.get("criteria") or []
        },
        "red_flags": [
            {"id": identifier, "text": text, "triggered": None, "evidence": ""}
            for identifier, text in zip(flag_ids(case), flag_texts(case))
        ],
        "reviewer_notes": "",
    }


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #
def run_manifest_errors(case: dict, review: dict, route: str | None) -> list[str]:
    """Check that a review names the exact skill, prompt, model, reviewer, and date."""
    errors: list[str] = []
    manifest = review.get("run_manifest")
    if not isinstance(manifest, dict):
        return ["run_manifest: missing (expected skill_sha256, prompt_sha256, model, reviewer, date_utc)"]
    skill = manifest.get("skill_sha256")
    if not isinstance(skill, str) or not skill.strip():
        errors.append("run_manifest: skill_sha256 is required")
        errors.append("assessment was scored against a different version of the skill")
    elif skill != skill_digest():
        errors.append("assessment was scored against a different version of the skill")
    if route is not None:
        recorded = manifest.get("prompt_sha256")
        if not isinstance(recorded, str) or not recorded.strip():
            errors.append("run_manifest: prompt_sha256 is required")
        elif recorded != prompt_digest(case, route):
            errors.append("run_manifest: prompt_sha256 does not match the prompt for this case and route")
    missing = [field for field in ("model", "reviewer", "date_utc") if not _filled(manifest.get(field))]
    if missing:
        errors.append("run_manifest: model/reviewer/date_utc are required")
        for field in missing:
            errors.append(f"run_manifest: {field} is required")
    return errors


def evaluate_review(case: dict, review: dict, response: bytes | None) -> tuple[bool, list[str], int, int]:
    """Score a review against a case.

    ``response`` is the exact response bytes, or ``None`` when the response is
    not available (for example when aggregating stored history).
    """
    errors: list[str] = []
    criteria = case.get("criteria") or []
    maximum = 2 * len(criteria)
    if review.get("case_id") != case["id"]:
        errors.append("Assessment case_id does not match case")
    route = review.get("route")
    if route not in allowed_routes(case):
        errors.append("Assessment route is invalid for case")
        route = None
    if route is not None and response is not None:
        if review.get("response_sha256") != response_digest(case, route, response):
            errors.append("Response changed after the assessment template was created")
    errors.extend(run_manifest_errors(case, review, route))

    scores = review.get("criteria", {})
    if not isinstance(scores, dict):
        errors.append("Assessment criteria must be an object")
        return False, errors, 0, maximum
    if set(scores) != {item["id"] for item in criteria}:
        errors.append("Assessment criterion IDs differ from case definition")
    total = 0
    critical_pass = True
    for criterion in criteria:
        cid = criterion["id"]
        item = scores.get(cid, {})
        if not isinstance(item, dict):
            errors.append(f"{cid}: assessment must be an object")
            continue
        value = item.get("score")
        if type(value) is not int or value not in (0, 1, 2):
            errors.append(f"{cid}: score must be 0, 1, or 2")
            continue
        if not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            errors.append(f"{cid}: explain the score with response evidence")
        total += value
        if criterion["critical"] and value != 2:
            critical_pass = False
            errors.append(f"{cid}: critical criterion must score 2")

    flags = review.get("red_flags", [])
    if not isinstance(flags, list):
        errors.append("Assessment red_flags must be an array")
        return False, errors, total, maximum
    expected_ids = flag_ids(case)
    expected_texts = flag_texts(case)
    if len(flags) != len(expected_ids):
        errors.append("Assessment red flags differ from case definition")
    submitted_ids: list[str | None] = []
    for index, flag in enumerate(flags, start=1):
        if not isinstance(flag, dict):
            errors.append(f"red flag {index}: assessment must be an object")
            submitted_ids.append(None)
            continue
        identifier = flag.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"red flag {index}: missing id")
            submitted_ids.append(None)
            continue
        submitted_ids.append(identifier)
    for index, identifier in enumerate(submitted_ids):
        if identifier is None:
            continue
        expected = expected_ids[index] if index < len(expected_ids) else None
        if expected is None:
            errors.append(f"red flag id mismatch: {identifier}")
        elif identifier != expected:
            errors.append(f"red flag id mismatch: {expected} (submitted {identifier})")

    triggered = False
    for index, flag in enumerate(flags):
        if not isinstance(flag, dict):
            continue
        identifier = flag.get("id")
        expected_id = expected_ids[index] if index < len(expected_ids) else None
        label = expected_id or (identifier if isinstance(identifier, str) and identifier.strip() else str(index + 1))
        if index < len(expected_texts):
            expected_text = expected_texts[index]
            submitted_text = flag.get("text")
            if not isinstance(submitted_text, str) or submitted_text.strip() != expected_text.strip():
                errors.append(f"red flag {label}: text does not match the case definition")
        value = flag.get("triggered")
        if type(value) is not bool:
            errors.append(f"red flag {label}: triggered must be true or false")
        elif value:
            triggered = True
            errors.append(f"red flag {label}: triggered")
        if not isinstance(flag.get("evidence"), str) or not flag["evidence"].strip():
            errors.append(f"red flag {label}: record where you looked, even if not triggered")

    passed = not errors and critical_pass and not triggered
    return passed, errors, total, maximum


def score(case: dict, review: dict, response: Path) -> tuple[bool, list[str], int, int]:
    """Score a review against the response file it was written for."""
    return evaluate_review(case, review, response.read_bytes())


# --------------------------------------------------------------------------- #
# stored runs
# --------------------------------------------------------------------------- #
def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _decode_response(stored) -> bytes | None:
    """Recover the exact response bytes from a stored run.

    New runs keep the raw bytes base64 encoded, so a response that is not
    valid UTF-8 still round-trips byte for byte. The plain ``response`` string
    is the older, lossy shape and is still read for history.
    """
    if isinstance(stored, str) and stored:
        return stored.encode("utf-8")
    if isinstance(stored, dict):
        encoded = stored.get("base64")
        if isinstance(encoded, str):
            try:
                return base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError):
                return None
    return None


def _encode_response(raw: bytes) -> dict:
    """Store response bytes losslessly."""
    return {"encoding": "base64", "base64": base64.b64encode(raw).decode("ascii")}


def _entry_from_assessment(data: dict, response: bytes | None, source: Path) -> dict:
    return {"assessment": data, "response": response, "source": source, "manifest": None}


def _entries_from_json(path: Path, problems: list[str] | None = None) -> list[dict]:
    problems = problems if problems is not None else []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        problems.append(f"could not read {_relative(path)}: {exc}")
        return []
    except json.JSONDecodeError as exc:
        problems.append(f"could not read {_relative(path)} as an assessment: invalid JSON ({exc})")
        return []
    if not isinstance(data, dict):
        problems.append(f"could not read {_relative(path)} as an assessment: it is not a JSON object")
        return []
    runs = data.get("runs")
    if isinstance(runs, list):
        entries = []
        for run in runs:
            if not isinstance(run, dict) or not isinstance(run.get("assessment"), dict):
                problems.append(f"could not read {_relative(path)} as an assessment: a stored run has no assessment")
                continue
            entries.append(
                {
                    "assessment": run["assessment"],
                    "response": _decode_response(run.get("response")),
                    "source": path,
                    "manifest": run.get("manifest"),
                }
            )
        return entries
    if isinstance(data.get("assessment"), dict):
        return [
            {
                "assessment": data["assessment"],
                "response": _decode_response(data.get("response")),
                "source": path,
                "manifest": data.get("manifest"),
            }
        ]
    if isinstance(data.get("criteria"), dict) and "case_id" in data:
        return [_entry_from_assessment(data, None, path)]
    problems.append(f"could not read {_relative(path)} as an assessment: it holds no assessment")
    return []


def _entries_in_dir(path: Path, problems: list[str] | None = None) -> list[dict]:
    problems = problems if problems is not None else []
    assessment = path / "assessment.json"
    if assessment.is_file():
        try:
            data = json.loads(assessment.read_text(encoding="utf-8"))
        except OSError as exc:
            problems.append(f"could not read {_relative(assessment)}: {exc}")
            return []
        except json.JSONDecodeError as exc:
            problems.append(f"could not read {_relative(assessment)} as an assessment: invalid JSON ({exc})")
            return []
        if not isinstance(data, dict):
            problems.append(f"could not read {_relative(assessment)} as an assessment: it is not a JSON object")
            return []
        response_file = path / "response.md"
        response = response_file.read_bytes() if response_file.is_file() else None
        return [
            {
                "assessment": data,
                "response": response,
                "source": path,
                "manifest": _load_json(path / "manifest.json"),
            }
        ]
    entries: list[dict] = []
    for child in sorted(path.iterdir()):
        if child.is_dir():
            entries.extend(_entries_in_dir(child, problems))
        elif child.suffix == ".json":
            entries.extend(_entries_from_json(child, problems))
    return entries


def entries_at(path: Path) -> list[dict]:
    """Assessments stored at a path, ignoring files that cannot be read."""
    return _entries_at(path, [])


def _entries_at(path: Path, problems: list[str]) -> list[dict]:
    if path.is_dir():
        return _entries_in_dir(path, problems)
    return _entries_from_json(path, problems)


def triggered_flags(review: dict) -> list[str]:
    flags = review.get("red_flags")
    if not isinstance(flags, list):
        return []
    names = []
    for index, flag in enumerate(flags, start=1):
        if isinstance(flag, dict) and flag.get("triggered") is True:
            identifier = flag.get("id")
            names.append(identifier if isinstance(identifier, str) and identifier.strip() else str(index))
    return names


def build_manifest(review: dict, total: int, maximum: int, passed: bool, date: str) -> dict:
    manifest = review.get("run_manifest")
    manifest = manifest if isinstance(manifest, dict) else {}
    return {
        "case_id": review.get("case_id"),
        "route": review.get("route"),
        "date_utc": date,
        "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": manifest.get("model", ""),
        "reviewer": manifest.get("reviewer", ""),
        "skill_sha256": manifest.get("skill_sha256", ""),
        "prompt_sha256": manifest.get("prompt_sha256", ""),
        "response_sha256": review.get("response_sha256", ""),
        "total": total,
        "maximum": maximum,
        "passed": passed,
        "triggered_flags": triggered_flags(review),
    }


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def command_report(paths: list[Path], catalog: dict[str, dict]) -> int:
    entries: list[dict] = []
    unreadable: list[str] = []
    for path in paths:
        entries.extend(_entries_at(path, unreadable))
    if not entries:
        print("No assessments found")
        for problem in unreadable:
            print(f"Warning: {problem}")
        return 1
    rows: list[tuple[str, str, str, str, str]] = []
    problems: list[str] = []
    failures = 0
    unverified = 0
    drifted = 0
    current_skill = skill_digest()
    for entry in entries:
        review = entry["assessment"]
        case_id = review.get("case_id")
        case = catalog.get(case_id)
        if case is None:
            failures += 1
            problems.append(f"{case_id}: unknown case")
            rows.append((str(case_id), str(review.get("route")), "-", "FAIL", "-"))
            continue
        manifest = entry.get("manifest")
        manifest = manifest if isinstance(manifest, dict) else {}
        stored = _stored_verdict(manifest, review, current_skill)
        if stored is not None:
            # The run was scored against a different skill revision, so it is
            # reported with the verdict it was given. Re-scoring it against
            # today's skill would only report the skill edit, not the run.
            drifted += 1
            passed, total, maximum = stored
            if not passed:
                failures += 1
            rows.append(
                (
                    str(case_id),
                    str(review.get("route")),
                    f"{total}/{maximum}",
                    "PASS" if passed else "FAIL",
                    ", ".join(triggered_flags(review)) or "none",
                )
            )
            continue
        if entry.get("response") is None:
            unverified += 1
        passed, errors, total, maximum = evaluate_review(case, review, entry.get("response"))
        if not passed:
            failures += 1
        rows.append(
            (
                str(case_id),
                str(review.get("route")),
                f"{total}/{maximum}",
                "PASS" if passed else "FAIL",
                ", ".join(triggered_flags(review)) or "none",
            )
        )
        for error in errors:
            problems.append(f"{case_id} ({review.get('route')}): {error}")
    print("| case | route | total/max | result | triggered flags |")
    print("| --- | --- | --- | --- | --- |")
    for row in rows:
        print("| " + " | ".join(row) + " |")
    if unverified:
        print()
        print(f"Note: {unverified} assessment(s) had no response copy, so the response hash was not re-verified.")
    if drifted:
        print()
        print(f"Note: {drifted} assessment(s) were scored against a different skill revision.")
    if problems:
        print()
        print("Problems:")
        for problem in problems:
            print(f"- {problem}")
    if unreadable:
        print()
        print("Warnings:")
        for problem in unreadable:
            print(f"- {problem}")
        print("A file that cannot be read as an assessment fails the gate: a truncated")
        print("baseline must never pass silently.")
    return 1 if failures or unreadable else 0


def _stored_verdict(manifest: dict, review: dict, current_skill: str) -> tuple[bool, int, int] | None:
    """The verdict a stored run was given, when it cannot be re-scored.

    A run stores the skill revision it was scored against. When that revision
    is no longer the one in the working tree, the run cannot be re-scored
    without reporting the skill edit rather than the run, so the stored
    ``passed``, ``total`` and ``maximum`` are used instead. ``None`` means the
    run must be scored against the current skill.
    """
    skill = manifest.get("skill_sha256")
    if not isinstance(skill, str) or not skill.strip():
        skill = (review.get("run_manifest") or {}).get("skill_sha256")
    if not isinstance(skill, str) or not skill.strip() or skill == current_skill:
        return None
    passed = manifest.get("passed")
    total = manifest.get("total")
    maximum = manifest.get("maximum")
    if not isinstance(passed, bool) or not isinstance(total, int) or not isinstance(maximum, int):
        return None
    return passed, total, maximum


def _load_review_for_case(path: Path, catalog: dict[str, dict]) -> tuple[dict | None, dict | None]:
    """Load an assessment and the case it claims to review."""
    review = _load_json(path)
    if not isinstance(review, dict):
        print(f"Invalid assessment JSON: {path}")
        return None, None
    case = catalog.get(review.get("case_id"))
    if case is None:
        print(f"Unknown case in assessment: {review.get('case_id')}")
        return None, None
    return review, case


def _result_file(date: str, case_id: str, route: str) -> tuple[Path, str | None]:
    """The results file that holds a run, with every name component sanitised.

    ``date``, ``case_id`` and ``route`` come from an assessment a reviewer
    wrote, so they are untrusted: each one is reduced to a single safe path
    component and the resolved file is checked to be inside the results
    directory before anything is written.
    """
    parts = {"date": date, "case": case_id, "route": route}
    safe = {name: _safe_name(value) for name, value in parts.items()}
    for name, value in parts.items():
        if safe[name] != value:
            print(f"note: {name} {value!r} was sanitised to {safe[name]!r} in the result file name")
    target = RESULTS / f"{safe['date']}-{safe['case']}-{safe['route']}.json"
    if not _within(RESULTS, target):
        return target, f"error: refusing to write outside the results directory: {target}"
    return target, None


def command_baseline(
    assessment: Path,
    response: Path,
    catalog: dict[str, dict],
    date: str,
    allow_fail: bool = False,
) -> int:
    review, case = _load_review_for_case(assessment, catalog)
    if review is None or case is None:
        return 1
    case_id = review.get("case_id")
    route = review.get("route")
    route_name = route if isinstance(route, str) and route else "automatic"
    raw = response.read_bytes()
    passed, errors, total, maximum = evaluate_review(case, review, raw)
    manifest = build_manifest(review, total, maximum, passed, date)
    entry = {
        "manifest": manifest,
        "assessment": review,
        "response": _encode_response(raw),
    }
    target, problem = _result_file(date, str(case_id), route_name)
    if problem:
        print(problem)
        return 1
    stored = _load_json(target)
    runs: list = []
    if isinstance(stored, dict) and isinstance(stored.get("runs"), list):
        runs = [run for run in stored["runs"] if isinstance(run, dict)]
    runs.append(entry)
    _write_text(target, json.dumps({"case_id": case_id, "route": route_name, "runs": runs}, indent=2) + "\n")
    print(f"{case_id}: {'PASS' if passed else 'NEEDS REVIEW'} ({total}/{maximum})")
    for error in errors:
        print(f"- {error}")
    print(f"baseline written to {_display_path(target)}")
    return 0 if passed or allow_fail else 1


def command_archive(
    assessment: Path,
    response: Path,
    catalog: dict[str, dict],
    date: str,
    out: Path | None,
    allow_fail: bool = False,
) -> int:
    review, case = _load_review_for_case(assessment, catalog)
    if review is None or case is None:
        return 1
    case_id = review.get("case_id")
    route = review.get("route")
    raw = response.read_bytes()
    passed, errors, total, maximum = evaluate_review(case, review, raw)
    if not isinstance(route, str) or route not in allowed_routes(case):
        print(f"error: assessment route {route!r} is not defined for case {case_id}")
        print(f"{case_id}: {'PASS' if passed else 'NEEDS REVIEW'} ({total}/{maximum})")
        for error in errors:
            print(f"- {error}")
        return 1
    manifest = build_manifest(review, total, maximum, passed, date)
    if out is not None:
        if out.exists() and not out.is_dir():
            print(f"error: archive destination exists and is not a directory: {out}")
            return 1
        directory = out
    else:
        name = f"{_safe_name(date)}-{_safe_name(str(case_id))}-{_safe_name(route)}"
        directory = RESULTS / "archive" / name
        if not _within(RESULTS, directory):
            print(f"error: refusing to write outside the results directory: {directory}")
            return 1
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"error: cannot create the archive directory {directory}: {exc}")
        return 1
    try:
        _write_text(directory / "prompt.md", normalised_prompt(case, route))
        (directory / "response.md").write_bytes(raw)
        _write_text(directory / "assessment.json", json.dumps(review, indent=2) + "\n")
        _write_text(directory / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    except OSError as exc:
        print(f"error: cannot write the archive to {directory}: {exc}")
        return 1
    print(f"{case_id}: {'PASS' if passed else 'NEEDS REVIEW'} ({total}/{maximum})")
    for error in errors:
        print(f"- {error}")
    print(f"archive written to {directory}")
    return 0 if passed or allow_fail else 1


def _select_entry(path: Path) -> dict | None:
    """The most recent run stored in a file or directory."""
    if path.is_dir():
        entries = _entries_in_dir(path)
        return entries[-1] if entries else None
    entries = _entries_from_json(path)
    return entries[-1] if entries else None


def command_diff(old: Path, new: Path, catalog: dict[str, dict]) -> int:
    old_entry = _select_entry(old)
    new_entry = _select_entry(new)
    if old_entry is None or new_entry is None:
        print("Both runs must be readable assessments or stored runs")
        return 1
    old_review = old_entry["assessment"]
    new_review = new_entry["assessment"]
    old_case_id = old_review.get("case_id")
    new_case_id = new_review.get("case_id")
    if old_case_id and new_case_id and old_case_id != new_case_id:
        print(f"Cannot diff two different cases: {old_case_id} and {new_case_id}")
        return 1
    case = catalog.get(old_case_id) or catalog.get(new_case_id)
    print(f"case: {old_case_id}  route: {old_review.get('route')}")
    old_manifest = old_entry.get("manifest") or {}
    new_manifest = new_entry.get("manifest") or {}
    old_skill = old_manifest.get("skill_sha256") or (old_review.get("run_manifest") or {}).get("skill_sha256")
    new_skill = new_manifest.get("skill_sha256") or (new_review.get("run_manifest") or {}).get("skill_sha256")
    if old_skill != new_skill:
        print(f"skill:   {old_skill} -> {new_skill} (changed)")
    old_total, old_maximum = _totals(case, old_entry)
    new_total, new_maximum = _totals(case, new_entry)
    if isinstance(old_total, int) and isinstance(new_total, int):
        delta = new_total - old_total
        print(f"total:   {old_total}/{old_maximum} -> {new_total}/{new_maximum} ({delta:+d})")
    old_criteria = old_review.get("criteria") if isinstance(old_review.get("criteria"), dict) else {}
    new_criteria = new_review.get("criteria") if isinstance(new_review.get("criteria"), dict) else {}
    identifiers: list[str] = []
    if case is not None:
        identifiers = [item["id"] for item in case["criteria"]]
    for identifier in list(identifiers) + [key for key in new_criteria if key not in identifiers]:
        old_value = _criterion_score(old_criteria.get(identifier))
        new_value = _criterion_score(new_criteria.get(identifier))
        if old_value is None and new_value is None:
            continue
        change = "" if old_value is None or new_value is None else f" ({new_value - old_value:+d})"
        print(f"  {identifier:<20} {old_value} -> {new_value}{change}")
    old_flags = old_review.get("red_flags") if isinstance(old_review.get("red_flags"), list) else []
    new_flags = new_review.get("red_flags") if isinstance(new_review.get("red_flags"), list) else []
    for index in range(max(len(old_flags), len(new_flags))):
        old_flag = old_flags[index] if index < len(old_flags) else {}
        new_flag = new_flags[index] if index < len(new_flags) else {}
        old_state = _flag_state(old_flag)
        new_state = _flag_state(new_flag)
        if old_state != new_state:
            label = new_flag.get("id") or old_flag.get("id") or str(index + 1)
            print(f"  flag {label:<15} {old_state} -> {new_state}")
    regressions: list[str] = []
    if isinstance(old_total, int) and isinstance(new_total, int) and new_total < old_total:
        regressions.append("REGRESSION: the new run scores lower than the old run")
    if _passed(case, old_entry) is True and _passed(case, new_entry) is False:
        regressions.append("REGRESSION: the new run does not pass where the old run passed")
    for regression in regressions:
        print(regression)
    return 1 if regressions else 0


def _totals(case: dict | None, entry: dict) -> tuple[int | None, int | None]:
    manifest = entry.get("manifest") or {}
    total = manifest.get("total")
    maximum = manifest.get("maximum")
    if isinstance(total, int) and isinstance(maximum, int):
        return total, maximum
    if case is not None:
        _, _, total, maximum = evaluate_review(case, entry["assessment"], entry.get("response"))
        return total, maximum
    return None, None


def _passed(case: dict | None, entry: dict) -> bool | None:
    manifest = entry.get("manifest") or {}
    value = manifest.get("passed")
    if isinstance(value, bool):
        return value
    if case is not None:
        return evaluate_review(case, entry["assessment"], entry.get("response"))[0]
    return None


def _criterion_score(item) -> int | None:
    if not isinstance(item, dict):
        return None
    value = item.get("score")
    return value if type(value) is int and value in (0, 1, 2) else None


def _flag_state(flag) -> str:
    if not isinstance(flag, dict):
        return "missing"
    value = flag.get("triggered")
    if value is True:
        return "triggered"
    if value is False:
        return "not triggered"
    return "unset"


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="Check case definitions and fixture")
    commands.add_parser("list", help="List scenario IDs and modes")
    commands.add_parser("digest", help="Print the current skill digest")
    for command in ("prompt", "template"):
        sub = commands.add_parser(command)
        sub.add_argument("case_id")
        sub.add_argument("--route", choices=("automatic", "compact", "detailed"), default="automatic")
        if command == "template":
            sub.add_argument("response", type=Path)
    scoring = commands.add_parser("score")
    scoring.add_argument("assessment", type=Path)
    scoring.add_argument("response", type=Path)
    reporting = commands.add_parser("report")
    reporting.add_argument("paths", nargs="+", type=Path)
    for command in ("baseline", "archive"):
        sub = commands.add_parser(command)
        sub.add_argument("assessment", type=Path)
        sub.add_argument("response", type=Path)
        sub.add_argument("--date", default=datetime.now(timezone.utc).date().isoformat())
        sub.add_argument(
            "--allow-fail",
            action="store_true",
            help="Store the run and exit 0 even when the review did not pass",
        )
        if command == "archive":
            sub.add_argument("--out", type=Path, default=None)
    comparison = commands.add_parser("diff")
    comparison.add_argument("old", type=Path)
    comparison.add_argument("new", type=Path)
    args = parser.parse_args()

    problems = validate()
    if problems:
        print("\n".join(problems))
        return 1
    catalog = cases()
    if args.command == "validate":
        print(f"{len(catalog)} behavior cases and fixture: OK")
        return 0
    if args.command == "list":
        for case in catalog.values():
            print(f"{case['id']:<24} {case['mode']}")
        return 0
    if args.command == "digest":
        print(skill_digest())
        return 0
    if args.command in ("prompt", "template"):
        if args.case_id not in catalog:
            parser.error(f"Unknown case: {args.case_id}")
        case = catalog[args.case_id]
        if args.route != "automatic" and args.route not in (case.get("reference_comparison") or {}):
            parser.error(f"Case {args.case_id} has no {args.route} route")
        if args.command == "prompt":
            # The prompt is printed without a trailing newline so the bytes on
            # screen are the bytes the prompt digest covers.
            print(prompt(case, args.route), end="")
        else:
            if not args.response.is_file():
                parser.error(f"Response file does not exist: {args.response}")
            print(json.dumps(template(case, args.response, args.route), indent=2))
        return 0
    if args.command == "report":
        for path in args.paths:
            if not path.exists():
                parser.error(f"Path does not exist: {path}")
        return command_report(args.paths, catalog)
    if args.command in ("baseline", "archive"):
        if not args.assessment.is_file() or not args.response.is_file():
            parser.error("Assessment and response files must both exist")
        if args.command == "baseline":
            return command_baseline(args.assessment, args.response, catalog, args.date, args.allow_fail)
        return command_archive(args.assessment, args.response, catalog, args.date, args.out, args.allow_fail)
    if args.command == "diff":
        if not args.old.exists() or not args.new.exists():
            parser.error("Both runs must exist")
        return command_diff(args.old, args.new, catalog)
    if not args.assessment.is_file() or not args.response.is_file():
        parser.error("Assessment and response files must both exist")
    try:
        review = json.loads(args.assessment.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        parser.error(f"Invalid assessment JSON: {exc}")
    if not isinstance(review, dict):
        parser.error("Assessment must be a JSON object")
    case_id = review.get("case_id")
    if case_id not in catalog:
        parser.error(f"Unknown case in assessment: {case_id}")
    passed, errors, total, maximum = score(catalog[case_id], review, args.response)
    print(f"{case_id}: {'PASS' if passed else 'NEEDS REVIEW'} ({total}/{maximum})")
    print(
        "Critical criteria must score 2/2 and no red flag may trigger. "
        "The total is reported as a diagnostic, not as a pass condition."
    )
    for error in errors:
        print(f"- {error}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
