import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_module("check_skill", ROOT / "scripts" / "check_skill.py")
evaluator = load_module("evaluate", ROOT / "evals" / "evaluate.py")


def usable_case(name: str = "payment-queue") -> dict:
    """A live case from cases.json, preferring a named one but never depending on it."""
    catalog = evaluator.cases()
    candidates = ([catalog[name]] if name in catalog else []) + [case for key, case in catalog.items() if key != name]
    for case in candidates:
        if case.get("criteria") and case.get("red_flags"):
            return case
    for case in candidates:
        if case.get("criteria"):
            return case
    raise unittest.SkipTest("cases.json defines no usable case")


def completed_review(case: dict, response: Path) -> dict:
    """A filled-in review form for the given case and response."""
    review = evaluator.template(case, response)
    for item in review["criteria"].values():
        item.update(score=2, evidence="Specific evidence in the response")
    for flag in review["red_flags"]:
        flag.update(triggered=False, evidence="Looked for this in the response; not present.")
    review["run_manifest"].update(model="test-model", reviewer="tester", date_utc="2026-10-21")
    return review


class ValidationTests(unittest.TestCase):
    def test_cases_are_valid(self):
        self.assertEqual([], evaluator.validate())

    def test_skill_package_is_valid(self):
        self.assertEqual([], checker.check())

    def test_broken_source_heading_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "system-design"
            shutil.copytree(ROOT / "system-design", skill)
            sources = skill / "references" / "sources.md"
            sources.write_text(sources.read_text().replace("## Patterns", "## Renamed patterns"))
            errors = checker.check(skill)
            self.assertTrue(any("missing heading" in error for error in errors))

    def test_unlinked_reference_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "system-design"
            shutil.copytree(ROOT / "system-design", skill)
            (skill / "references" / "new-topic.md").write_text("# New topic\n")
            errors = checker.check(skill)
            self.assertTrue(any("not linked directly" in error for error in errors))

    def test_critical_behavior_failure_cannot_pass(self):
        case = usable_case()
        critical = [item["id"] for item in case["criteria"] if item.get("critical")]
        self.assertTrue(critical, "case needs a critical criterion")
        with tempfile.TemporaryDirectory() as directory:
            response = Path(directory) / "response.md"
            response.write_text("Example answer")
            review = completed_review(case, response)
            self.assertTrue(evaluator.score(case, review, response)[0])
            review["criteria"][critical[0]]["score"] = 1
            self.assertFalse(evaluator.score(case, review, response)[0])
            review["criteria"][critical[0]]["score"] = 2
            flags = review["red_flags"]
            if flags:
                flags[0].update(triggered=True, evidence="Claims the false behaviour")
                self.assertFalse(evaluator.score(case, review, response)[0])
                flags[0].update(triggered=False, evidence="Looked; not present.")
            response.write_text("Changed answer")
            self.assertFalse(evaluator.score(case, review, response)[0])

    def test_a_review_must_name_the_skill_it_was_scored_against(self):
        case = usable_case()
        with tempfile.TemporaryDirectory() as directory:
            response = Path(directory) / "response.md"
            response.write_text("Example answer")
            review = completed_review(case, response)
            review["run_manifest"]["skill_sha256"] = "0" * 64
            passed, errors, _, _ = evaluator.score(case, review, response)
            self.assertFalse(passed)
            self.assertIn("assessment was scored against a different version of the skill", errors)

    def test_reference_comparison_routes_are_distinct(self):
        case = usable_case("cached-balance")
        routes = case.get("reference_comparison") or {}
        if len(routes) < 2:
            self.skipTest("case defines fewer than two comparison routes")
        names = sorted(routes)
        compact = evaluator.prompt(case, names[0])
        detailed = evaluator.prompt(case, names[1])
        self.assertIn(routes[names[0]], compact)
        self.assertIn(routes[names[1]], detailed)
        self.assertNotEqual(compact, detailed)


if __name__ == "__main__":
    unittest.main()
