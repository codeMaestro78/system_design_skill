import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


evaluator = load_module("evaluate", ROOT / "evals" / "evaluate.py")


def make_case(**overrides) -> dict:
    """A case in the current schema, built inline so the tests do not depend on cases.json."""
    case = {
        "id": "unit-case",
        "mode": "greenfield",
        "prompt": "Design a service that keeps totals. The repository is at {{FIXTURE_DIR}}.",
        "criteria": [
            {
                "id": "source-of-truth",
                "critical": True,
                "expect": "Keeps the database authoritative.",
                "anchors": {
                    "2": "States the database is authoritative and names the mechanism.",
                    "1": "Mentions the database without naming the mechanism.",
                    "0": "Makes the cache authoritative or is silent.",
                },
            },
            {
                "id": "tradeoff",
                "critical": False,
                "expect": "Explains the operational cost of the change.",
                "anchors": {
                    "2": "Explains the cost with a measurable trigger.",
                    "1": "Mentions cost vaguely.",
                    "0": "Says nothing about cost.",
                },
            },
        ],
        "red_flags": [
            {
                "id": "calls-cache-authoritative",
                "text": "Asserts that a cache is strongly consistent by default",
            },
            {
                "id": "invents-throughput",
                "text": "Asserts a fabricated request rate as a requirement",
            },
        ],
    }
    case.update(overrides)
    return case


def make_review(case: dict, response: Path, route: str = "automatic") -> dict:
    """A complete, passing review for the given case and response."""
    review = evaluator.template(case, response, route)
    for item in review["criteria"].values():
        item["score"] = 2
        item["evidence"] = "Quoted sentence from the response."
    for flag in review["red_flags"]:
        flag["triggered"] = False
        flag["evidence"] = "Looked in section 2 of the response; not present."
    review["run_manifest"].update(model="test-model", reviewer="tester", date_utc="2026-10-21")
    return review


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.case = make_case()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.response = Path(self.directory.name) / "response.md"
        self.response.write_text("A considered answer about totals and caches.", encoding="utf-8")

    def test_template_pins_the_run_manifest(self):
        before = evaluator.skill_digest()
        review = evaluator.template(self.case, self.response)
        after = evaluator.skill_digest()
        manifest = review["run_manifest"]
        self.assertIn(manifest["skill_sha256"], {before, after})
        self.assertEqual(evaluator.prompt_digest(self.case, "automatic"), manifest["prompt_sha256"])
        self.assertEqual("", manifest["model"])
        self.assertEqual("", manifest["reviewer"])
        self.assertEqual("", manifest["date_utc"])

    def test_template_emits_anchors_and_flag_ids(self):
        review = evaluator.template(self.case, self.response)
        criterion = review["criteria"]["source-of-truth"]
        self.assertIsNone(criterion["score"])
        self.assertEqual("", criterion["evidence"])
        self.assertEqual(self.case["criteria"][0]["anchors"], criterion["anchors"])
        self.assertEqual(["calls-cache-authoritative", "invents-throughput"], [f["id"] for f in review["red_flags"]])
        self.assertEqual(self.case["red_flags"][0]["text"], review["red_flags"][0]["text"])
        for flag in review["red_flags"]:
            self.assertIsNone(flag["triggered"])
            self.assertEqual("", flag["evidence"])

    def test_template_records_the_route(self):
        review = evaluator.template(self.case, self.response, "automatic")
        self.assertEqual("automatic", review["route"])


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.case = make_case()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.response = Path(self.directory.name) / "response.md"
        self.response.write_text("A considered answer about totals and caches.", encoding="utf-8")
        self.review = make_review(self.case, self.response)

    def score(self):
        return evaluator.score(self.case, self.review, self.response)

    def test_a_complete_review_passes(self):
        passed, errors, total, maximum = self.score()
        self.assertTrue(passed, errors)
        self.assertEqual([], errors)
        self.assertEqual(4, total)
        self.assertEqual(4, maximum)

    def test_score_rejects_a_wrong_skill_digest(self):
        self.review["run_manifest"]["skill_sha256"] = "0" * 64
        passed, errors, _, _ = self.score()
        self.assertFalse(passed)
        self.assertIn("assessment was scored against a different version of the skill", errors)

    def test_score_rejects_an_empty_model_reviewer_or_date(self):
        for field in ("model", "reviewer", "date_utc"):
            with self.subTest(field=field):
                review = make_review(self.case, self.response)
                review["run_manifest"][field] = ""
                passed, errors, _, _ = evaluator.score(self.case, review, self.response)
                self.assertFalse(passed)
                self.assertIn("run_manifest: model/reviewer/date_utc are required", errors)

    def test_score_rejects_a_missing_run_manifest(self):
        del self.review["run_manifest"]
        passed, errors, _, _ = self.score()
        self.assertFalse(passed)
        self.assertTrue(any("run_manifest" in error for error in errors))

    def test_score_rejects_a_mismatched_red_flag_id(self):
        self.review["red_flags"][0]["id"] = "some-other-flag"
        passed, errors, _, _ = self.score()
        self.assertFalse(passed)
        self.assertTrue(any("red flag id mismatch" in error for error in errors))

    def test_score_rejects_a_reversed_red_flag_order(self):
        self.review["red_flags"].reverse()
        passed, errors, _, _ = self.score()
        self.assertFalse(passed)
        self.assertTrue(any("red flag id mismatch" in error for error in errors))

    def test_score_rejects_missing_red_flag_evidence(self):
        self.review["red_flags"][0]["evidence"] = ""
        passed, errors, _, _ = self.score()
        self.assertFalse(passed)
        self.assertIn(
            "red flag calls-cache-authoritative: record where you looked, even if not triggered",
            errors,
        )

    def test_score_requires_evidence_on_every_criterion(self):
        self.review["criteria"]["tradeoff"]["evidence"] = "   "
        passed, errors, _, _ = self.score()
        self.assertFalse(passed)
        self.assertTrue(any("tradeoff" in error for error in errors))

    def test_score_rejects_an_out_of_range_score(self):
        for value in (3, "2", True, None):
            with self.subTest(value=value):
                review = make_review(self.case, self.response)
                review["criteria"]["tradeoff"]["score"] = value
                passed, errors, _, _ = evaluator.score(self.case, review, self.response)
                self.assertFalse(passed)
                self.assertTrue(any("score must be 0, 1, or 2" in error for error in errors))

    def test_score_fails_when_a_critical_criterion_scores_one(self):
        self.review["criteria"]["source-of-truth"]["score"] = 1
        passed, errors, _, _ = self.score()
        self.assertFalse(passed)
        self.assertTrue(any("critical" in error for error in errors))

    def test_score_fails_when_a_red_flag_triggers(self):
        self.review["red_flags"][0]["triggered"] = True
        passed, errors, _, _ = self.score()
        self.assertFalse(passed)
        self.assertTrue(any("triggered" in error for error in errors))

    def test_total_below_eighty_percent_still_passes_when_criteria_are_clean(self):
        self.review["criteria"]["tradeoff"]["score"] = 0
        passed, errors, total, maximum = self.score()
        self.assertTrue(passed, errors)
        self.assertEqual(2, total)
        self.assertEqual(4, maximum)
        self.assertLess(total / maximum, 0.8)

    def test_score_rejects_a_tampered_response(self):
        self.response.write_text("A different answer.", encoding="utf-8")
        passed, errors, _, _ = self.score()
        self.assertFalse(passed)
        self.assertTrue(any("Response changed" in error for error in errors))

    def test_score_rejects_a_wrong_route(self):
        self.review["route"] = "compact"
        passed, errors, _, _ = self.score()
        self.assertFalse(passed)
        self.assertIn("Assessment route is invalid for case", errors)

    def test_score_rejects_a_route_that_is_not_the_one_reviewed(self):
        case = make_case(
            reference_comparison={
                "compact": "references/data-and-storage.md",
                "detailed": "references/data-architecture.md",
            }
        )
        review = make_review(case, self.response, "compact")
        self.assertTrue(evaluator.score(case, review, self.response)[0])
        review["route"] = "detailed"
        passed, errors, _, _ = evaluator.score(case, review, self.response)
        self.assertFalse(passed)
        self.assertTrue(any("Response changed" in error for error in errors))


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "cases.json"
        self.original = evaluator.CASES

    def tearDown(self):
        evaluator.CASES = self.original

    def write(self, cases: list) -> list[str]:
        self.path.write_text(json.dumps(cases), encoding="utf-8")
        evaluator.CASES = self.path
        return evaluator.validate()

    def test_valid_case_has_no_errors(self):
        errors = self.write([make_case()])
        self.assertEqual([], errors)

    def test_duplicate_case_id_is_rejected(self):
        errors = self.write([make_case(), make_case()])
        self.assertTrue(any("Duplicate case id" in error for error in errors))

    def test_unknown_top_level_key_is_rejected(self):
        errors = self.write([make_case(unexpected="value")])
        self.assertTrue(any("unknown case keys" in error for error in errors))

    def test_missing_expectation_is_rejected(self):
        case = make_case()
        del case["criteria"][0]["expect"]
        errors = self.write([case])
        self.assertTrue(any("missing expectation" in error for error in errors))

    def test_non_boolean_critical_is_rejected(self):
        case = make_case()
        case["criteria"][0]["critical"] = "yes"
        errors = self.write([case])
        self.assertTrue(any("critical must be boolean" in error for error in errors))

    def test_missing_anchors_are_rejected(self):
        case = make_case()
        del case["criteria"][0]["anchors"]
        errors = self.write([case])
        self.assertTrue(any("anchors" in error for error in errors))

    def test_incomplete_anchors_are_rejected(self):
        case = make_case()
        del case["criteria"][0]["anchors"]["1"]
        errors = self.write([case])
        self.assertTrue(any("anchor for score 1 is missing" in error for error in errors))

    def test_red_flag_without_id_is_rejected(self):
        case = make_case()
        del case["red_flags"][0]["id"]
        errors = self.write([case])
        self.assertTrue(any("missing a nonempty id" in error for error in errors))

    def test_duplicate_red_flag_id_is_rejected(self):
        case = make_case()
        case["red_flags"][1]["id"] = case["red_flags"][0]["id"]
        errors = self.write([case])
        self.assertTrue(any("duplicate red flag id" in error for error in errors))

    def test_bare_string_red_flag_is_reported_clearly(self):
        case = make_case()
        case["red_flags"] = ["Claims the cache is authoritative"]
        errors = self.write([case])
        self.assertTrue(any("bare string" in error for error in errors))

    def test_missing_comparison_reference_is_rejected(self):
        case = make_case(
            reference_comparison={
                "compact": "references/data-and-storage.md",
                "detailed": "references/does-not-exist.md",
            }
        )
        errors = self.write([case])
        self.assertTrue(any("missing detailed comparison reference" in error for error in errors))

    def test_red_flags_may_be_absent(self):
        case = make_case()
        del case["red_flags"]
        errors = self.write([case])
        self.assertEqual([], errors)


class PromptAndDigestTests(unittest.TestCase):
    def test_prompt_replaces_the_fixture_placeholder(self):
        case = make_case()
        text = evaluator.prompt(case)
        self.assertNotIn("{{FIXTURE_DIR}}", text)
        self.assertIn(str(evaluator.FIXTURE.resolve()), text)

    def test_prompt_digest_is_machine_independent(self):
        case = make_case()
        self.assertNotIn(str(evaluator.FIXTURE.resolve()), evaluator.normalised_prompt(case))
        self.assertIn("{{FIXTURE_DIR}}", evaluator.normalised_prompt(case))

    def test_skill_digest_is_stable_and_changes_with_content(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "system-design"
            skill.mkdir()
            (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
            (skill / "references").mkdir()
            (skill / "references" / "a.md").write_text("alpha\n", encoding="utf-8")
            first = evaluator.skill_digest(skill)
            self.assertEqual(first, evaluator.skill_digest(skill))
            (skill / "references" / "a.md").write_text("beta\n", encoding="utf-8")
            self.assertNotEqual(first, evaluator.skill_digest(skill))

    def test_skill_digest_covers_every_file(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "system-design"
            skill.mkdir()
            (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
            first = evaluator.skill_digest(skill)
            (skill / "extra.md").write_text("extra\n", encoding="utf-8")
            self.assertNotEqual(first, evaluator.skill_digest(skill))

    def test_response_digest_covers_the_route(self):
        case = make_case(
            reference_comparison={
                "compact": "references/data-and-storage.md",
                "detailed": "references/data-architecture.md",
            }
        )
        automatic = evaluator.response_digest(case, "automatic", b"answer")
        compact = evaluator.response_digest(case, "compact", b"answer")
        self.assertNotEqual(automatic, compact)


if __name__ == "__main__":
    unittest.main()
