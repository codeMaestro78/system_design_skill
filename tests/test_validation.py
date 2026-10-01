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


class ValidationTests(unittest.TestCase):
    def test_package_and_cases_are_valid(self):
        self.assertEqual([], checker.check())
        self.assertEqual([], evaluator.validate())

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
        case = evaluator.cases()["payment-queue"]
        with tempfile.TemporaryDirectory() as directory:
            response = Path(directory) / "response.md"
            response.write_text("Example answer")
            review = evaluator.template(case, response)
            for item in review["criteria"].values():
                item.update(score=2, evidence="Specific evidence in the response")
            for flag in review["red_flags"]:
                flag["triggered"] = False
            self.assertTrue(evaluator.score(case, review, response)[0])
            review["criteria"]["guarantee"]["score"] = 1
            self.assertFalse(evaluator.score(case, review, response)[0])
            review["criteria"]["guarantee"]["score"] = 2
            review["red_flags"][0].update(triggered=True, evidence="Claims queue guarantees exactly once")
            self.assertFalse(evaluator.score(case, review, response)[0])
            review["red_flags"][0].update(triggered=False, evidence="")
            response.write_text("Changed answer")
            self.assertFalse(evaluator.score(case, review, response)[0])

    def test_reference_comparison_routes_are_distinct(self):
        case = evaluator.cases()["cached-balance"]
        compact = evaluator.prompt(case, "compact")
        detailed = evaluator.prompt(case, "detailed")
        self.assertIn("references/data-and-storage.md", compact)
        self.assertIn("references/data-architecture.md", detailed)
        self.assertNotEqual(compact, detailed)


if __name__ == "__main__":
    unittest.main()
