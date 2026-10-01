#!/usr/bin/env python3
"""Prepare portable behavior cases and summarize evidence-backed human reviews."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases.json"
FIXTURE = HERE / "fixtures" / "partial-repository"


def cases() -> dict[str, dict]:
    raw = json.loads(CASES.read_text(encoding="utf-8"))
    return {case["id"]: case for case in raw}


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
        for field in ("mode", "prompt"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                errors.append(f"{case_id}: missing {field}")
        criteria = case.get("criteria")
        if not isinstance(criteria, list) or not criteria:
            errors.append(f"{case_id}: needs criteria")
            continue
        criterion_ids = set()
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
        if not isinstance(case.get("red_flags"), list) or not case["red_flags"]:
            errors.append(f"{case_id}: needs red flags")
        routes = case.get("reference_comparison", {})
        if routes:
            if not isinstance(routes, dict):
                errors.append(f"{case_id}: reference_comparison must be an object")
                continue
            if set(routes) != {"compact", "detailed"}:
                errors.append(f"{case_id}: comparison needs compact and detailed routes")
            for route, path in routes.items():
                if not isinstance(path, str) or not (HERE.parent / "system-design" / path).is_file():
                    errors.append(f"{case_id}: missing {route} comparison reference")
    if not FIXTURE.joinpath("src", "orders.js").is_file():
        errors.append("Partial repository fixture is missing")
    return errors


def prompt(case: dict, route: str = "automatic") -> str:
    text = case["prompt"].replace("{{FIXTURE_DIR}}", str(FIXTURE.resolve()))
    if route == "automatic":
        return text
    paths = case.get("reference_comparison", {})
    if route not in paths:
        raise ValueError(f"No {route} comparison route for {case['id']}")
    return f"For this evaluation, consult the skill's {paths[route]} reference for the data topic.\n\n{text}"


def template(case: dict, response: Path, route: str = "automatic") -> dict:
    digest = hashlib.sha256(response.read_bytes()).hexdigest()
    return {
        "case_id": case["id"],
        "route": route,
        "response_sha256": digest,
        "criteria": {item["id"]: {"score": None, "evidence": ""} for item in case["criteria"]},
        "red_flags": [{"triggered": None, "evidence": ""} for _ in case["red_flags"]],
        "reviewer_notes": "",
    }


def score(case: dict, review: dict, response: Path) -> tuple[bool, list[str], int, int]:
    errors: list[str] = []
    if review.get("case_id") != case["id"]:
        errors.append("Assessment case_id does not match case")
    if review.get("route") not in ("automatic", *case.get("reference_comparison", {})):
        errors.append("Assessment route is invalid for case")
    if review.get("response_sha256") != hashlib.sha256(response.read_bytes()).hexdigest():
        errors.append("Response changed after the assessment template was created")
    scores = review.get("criteria", {})
    if not isinstance(scores, dict):
        return False, errors + ["Assessment criteria must be an object"], 0, 2 * len(case["criteria"])
    if set(scores) != {item["id"] for item in case["criteria"]}:
        errors.append("Assessment criterion IDs differ from case definition")
    total = 0
    maximum = 2 * len(case["criteria"])
    critical_pass = True
    for criterion in case["criteria"]:
        item = scores.get(criterion["id"], {})
        if not isinstance(item, dict):
            errors.append(f"{criterion['id']}: assessment must be an object")
            continue
        value = item.get("score")
        if type(value) is not int or value not in (0, 1, 2):
            errors.append(f"{criterion['id']}: score must be 0, 1, or 2")
            continue
        if not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            errors.append(f"{criterion['id']}: explain the score with response evidence")
        total += value
        if criterion["critical"] and value != 2:
            critical_pass = False
    flags = review.get("red_flags", [])
    if not isinstance(flags, list):
        return False, errors + ["Assessment red_flags must be an array"], total, maximum
    if len(flags) != len(case["red_flags"]):
        errors.append("Assessment red flags differ from case definition")
    triggered = False
    for index, flag in enumerate(flags):
        if not isinstance(flag, dict) or type(flag.get("triggered")) is not bool:
            errors.append(f"red flag {index + 1}: triggered must be true or false")
        elif flag["triggered"]:
            triggered = True
            if not isinstance(flag.get("evidence"), str) or not flag["evidence"].strip():
                errors.append(f"red flag {index + 1}: explain what triggered it")
    passed = not errors and critical_pass and not triggered and total / maximum >= 0.8
    return passed, errors, total, maximum


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="Check case definitions and fixture")
    commands.add_parser("list", help="List scenario IDs and modes")
    for command in ("prompt", "template"):
        sub = commands.add_parser(command)
        sub.add_argument("case_id")
        sub.add_argument("--route", choices=("automatic", "compact", "detailed"), default="automatic")
        if command == "template":
            sub.add_argument("response", type=Path)
    scoring = commands.add_parser("score")
    scoring.add_argument("assessment", type=Path)
    scoring.add_argument("response", type=Path)
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
    if args.command in ("prompt", "template"):
        if args.case_id not in catalog:
            parser.error(f"Unknown case: {args.case_id}")
        case = catalog[args.case_id]
        if args.route != "automatic" and args.route not in case.get("reference_comparison", {}):
            parser.error(f"Case {args.case_id} has no {args.route} route")
        if args.command == "prompt":
            print(prompt(case, args.route))
        else:
            if not args.response.is_file():
                parser.error(f"Response file does not exist: {args.response}")
            print(json.dumps(template(case, args.response, args.route), indent=2))
        return 0
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
    print("Critical criteria require 2/2; total requires at least 80%; no red flags may trigger.")
    for error in errors:
        print(f"- {error}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
