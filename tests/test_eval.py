import base64
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]

# The fixture tree the harness expects, written out here so the test does not
# simply repeat whatever the harness believes.
EXPECTED_FIXTURE_FILES = (
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


def capture(function, *args, **kwargs):
    """Run a command, returning its exit code and what it printed."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = function(*args, **kwargs)
    return code, buffer.getvalue()


def build_fixture(root: Path) -> None:
    """A fixture tree with exactly the expected files."""
    for relative in EXPECTED_FIXTURE_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


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


class FixtureTreeTests(unittest.TestCase):
    """The partial repository fixture must be exactly the expected tree."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "partial-repository"
        build_fixture(self.root)
        self.original = evaluator.FIXTURE
        self.addCleanup(setattr, evaluator, "FIXTURE", self.original)
        evaluator.FIXTURE = self.root

    def fixture_errors(self) -> list[str]:
        return [error for error in evaluator.validate() if "fixture" in error.lower()]

    def test_the_expected_tree_is_accepted(self):
        self.assertEqual([], self.fixture_errors())

    def test_a_missing_fixture_file_is_reported(self):
        (self.root / ".env").unlink()
        self.assertIn("Partial repository fixture is missing .env", self.fixture_errors())

    def test_a_missing_nested_fixture_file_is_reported(self):
        (self.root / ".github" / "workflows" / "ci.yml").unlink()
        self.assertIn("Partial repository fixture is missing .github/workflows/ci.yml", self.fixture_errors())

    def test_an_extra_fixture_file_is_reported(self):
        (self.root / "EXTRA.md").write_text("extra\n", encoding="utf-8")
        self.assertIn("Partial repository fixture has an unexpected file: EXTRA.md", self.fixture_errors())

    def test_an_extra_nested_fixture_file_is_reported(self):
        (self.root / "docs" / "EXTRA.md").write_text("extra\n", encoding="utf-8")
        self.assertIn("Partial repository fixture has an unexpected file: docs/EXTRA.md", self.fixture_errors())

    def test_the_harness_checks_the_documented_tree(self):
        self.assertEqual(sorted(EXPECTED_FIXTURE_FILES), sorted(evaluator.FIXTURE_FILES))


class LiveFixtureTests(unittest.TestCase):
    def test_the_live_fixture_matches_the_expected_tree(self):
        present = {
            path.relative_to(evaluator.FIXTURE).as_posix() for path in evaluator.FIXTURE.rglob("*") if path.is_file()
        }
        self.assertEqual(set(EXPECTED_FIXTURE_FILES), present)


class RedFlagTextTests(unittest.TestCase):
    """A reviewer may not rewrite the claim a red flag looks for."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.case = make_case()
        self.response = Path(self.directory.name) / "response.md"
        self.response.write_text("A considered answer about totals and caches.", encoding="utf-8")

    def test_a_renamed_flag_text_is_rejected(self):
        review = make_review(self.case, self.response)
        review["red_flags"][0]["text"] = "Something else entirely"
        passed, errors, _, _ = evaluator.score(self.case, review, self.response)
        self.assertFalse(passed)
        self.assertIn(
            "red flag calls-cache-authoritative: text does not match the case definition",
            errors,
        )

    def test_a_removed_flag_text_is_rejected(self):
        review = make_review(self.case, self.response)
        del review["red_flags"][0]["text"]
        passed, errors, _, _ = evaluator.score(self.case, review, self.response)
        self.assertFalse(passed)
        self.assertTrue(any("text does not match the case definition" in error for error in errors))

    def test_surrounding_whitespace_is_allowed(self):
        review = make_review(self.case, self.response)
        review["red_flags"][0]["text"] = f"  {self.case['red_flags'][0]['text']}  "
        passed, errors, _, _ = evaluator.score(self.case, review, self.response)
        self.assertTrue(passed, errors)

    def test_the_untouched_flag_text_still_passes(self):
        review = make_review(self.case, self.response)
        passed, errors, _, _ = evaluator.score(self.case, review, self.response)
        self.assertTrue(passed, errors)


class RunManifestTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.case = make_case()
        self.response = Path(self.directory.name) / "response.md"
        self.response.write_text("A considered answer about totals and caches.", encoding="utf-8")

    def test_every_missing_manifest_field_is_reported(self):
        review = make_review(self.case, self.response)
        review["run_manifest"].update(model="", reviewer="", date_utc="")
        passed, errors, _, _ = evaluator.score(self.case, review, self.response)
        self.assertFalse(passed)
        for field in ("model", "reviewer", "date_utc"):
            self.assertIn(f"run_manifest: {field} is required", errors)

    def test_one_missing_manifest_field_is_reported_on_its_own(self):
        review = make_review(self.case, self.response)
        review["run_manifest"]["reviewer"] = ""
        passed, errors, _, _ = evaluator.score(self.case, review, self.response)
        self.assertFalse(passed)
        self.assertIn("run_manifest: reviewer is required", errors)
        self.assertNotIn("run_manifest: model is required", errors)


class StoredRunBase(unittest.TestCase):
    """baseline, archive, report and diff, all inside a temporary directory."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.results = self.base / "results"
        self.results.mkdir()
        self.original_results = evaluator.RESULTS
        self.addCleanup(setattr, evaluator, "RESULTS", self.original_results)
        evaluator.RESULTS = self.results
        self.case = make_case()
        self.catalog = {self.case["id"]: self.case}
        self.response = self.base / "response.md"
        self.response.write_text("A considered answer about totals and caches.", encoding="utf-8")
        self.review = make_review(self.case, self.response)
        self.assessment = self.base / "review.json"

    def write_review(self, review: dict | None = None) -> None:
        self.assessment.write_text(json.dumps(review or self.review, indent=2), encoding="utf-8")

    def baseline(self, date: str = "2026-10-21"):
        return capture(
            evaluator.command_baseline,
            self.assessment,
            self.response,
            self.catalog,
            date,
        )

    def archive(self, date: str = "2026-10-21", out: Path | None = None):
        return capture(
            evaluator.command_archive,
            self.assessment,
            self.response,
            self.catalog,
            date,
            out,
        )

    def stored_path(self, date: str = "2026-10-21") -> Path:
        return self.results / f"{date}-unit-case-automatic.json"


class StoredRunTests(StoredRunBase):
    def test_baseline_writes_into_the_results_directory(self):
        self.write_review()
        code, output = self.baseline()
        self.assertEqual(0, code, output)
        self.assertTrue(self.stored_path().is_file())

    def test_baseline_returns_nonzero_for_a_failing_review(self):
        self.review["criteria"]["source-of-truth"]["score"] = 1
        self.write_review()
        code, output = self.baseline()
        self.assertEqual(1, code, output)
        self.assertIn("NEEDS REVIEW", output)

    def test_archive_returns_nonzero_for_a_failing_review(self):
        self.review["red_flags"][0]["triggered"] = True
        self.write_review()
        code, output = self.archive()
        self.assertEqual(1, code, output)
        self.assertIn("NEEDS REVIEW", output)

    def test_a_traversal_route_cannot_escape_the_results_directory(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.review["route"] = "../../../outside/pwned"
        self.write_review()
        # The unsanitised name would have to exist for the write to land outside.
        (self.results / "2026-10-21-unit-case-..").mkdir(parents=True, exist_ok=True)
        code, output = self.baseline()
        self.assertEqual(1, code, output)
        self.assertFalse((outside / "pwned.json").exists())
        self.assertEqual([], list(self.base.glob("**/pwned.json")))
        for path in self.results.rglob("*"):
            self.assertTrue(path.resolve().is_relative_to(self.results.resolve()))

    def test_a_binary_response_round_trips_losslessly(self):
        raw = b"\x89PNG\r\n\x1a\n\xff\xfe\x00binary"
        self.response.write_bytes(raw)
        self.write_review(make_review(self.case, self.response))
        code, output = self.baseline()
        self.assertEqual(0, code, output)
        stored = json.loads(self.stored_path().read_text(encoding="utf-8"))
        run = stored["runs"][-1]
        self.assertEqual(raw, base64.b64decode(run["response"]["base64"]))
        code, output = capture(evaluator.command_report, [self.results], self.catalog)
        self.assertEqual(0, code, output)
        self.assertNotIn("Response changed", output)

    def test_report_honours_a_stored_verdict_when_the_skill_has_drifted(self):
        self.write_review()
        code, output = self.baseline()
        self.assertEqual(0, code, output)
        stored = json.loads(self.stored_path().read_text(encoding="utf-8"))
        run = stored["runs"][-1]
        run["manifest"]["skill_sha256"] = "0" * 64
        run["assessment"]["run_manifest"]["skill_sha256"] = "0" * 64
        self.stored_path().write_text(json.dumps(stored, indent=2), encoding="utf-8")
        code, output = capture(evaluator.command_report, [self.results], self.catalog)
        self.assertEqual(0, code, output)
        self.assertIn("scored against a different skill revision", output)
        self.assertIn("PASS", output)

    def test_report_fails_when_a_stored_run_did_not_pass(self):
        self.write_review()
        code, output = self.baseline()
        self.assertEqual(0, code, output)
        stored = json.loads(self.stored_path().read_text(encoding="utf-8"))
        run = stored["runs"][-1]
        run["manifest"]["skill_sha256"] = "0" * 64
        run["manifest"]["passed"] = False
        self.stored_path().write_text(json.dumps(stored, indent=2), encoding="utf-8")
        code, output = capture(evaluator.command_report, [self.results], self.catalog)
        self.assertEqual(1, code, output)
        self.assertIn("FAIL", output)

    def test_report_fails_on_an_unreadable_assessment_file(self):
        self.write_review()
        code, output = self.baseline()
        self.assertEqual(0, code, output)
        (self.results / "truncated.json").write_text('{"runs": [', encoding="utf-8")
        code, output = capture(evaluator.command_report, [self.results], self.catalog)
        self.assertEqual(1, code, output)
        self.assertIn("truncated.json", output)
        self.assertIn("Warning", output)

    def test_report_fails_on_a_file_that_holds_no_assessment(self):
        self.write_review()
        code, output = self.baseline()
        self.assertEqual(0, code, output)
        (self.results / "notes.json").write_text('{"note": "hello"}', encoding="utf-8")
        code, output = capture(evaluator.command_report, [self.results], self.catalog)
        self.assertEqual(1, code, output)
        self.assertIn("notes.json", output)


class ArchiveTests(StoredRunBase):
    def test_archive_rejects_a_route_the_case_does_not_define(self):
        self.review["route"] = "compact"
        self.write_review()
        code, output = self.archive()
        self.assertEqual(1, code, output)
        self.assertIn("not defined for case", output)
        self.assertNotIn("Traceback", output)
        self.assertFalse((self.results / "archive").exists())

    def test_archive_rejects_an_out_path_that_is_a_file(self):
        self.write_review()
        target = self.base / "archive"
        target.write_text("not a directory\n", encoding="utf-8")
        code, output = self.archive(out=target)
        self.assertEqual(1, code, output)
        self.assertIn("not a directory", output)
        self.assertNotIn("Traceback", output)

    def test_archive_writes_a_full_copy_of_the_run(self):
        self.write_review()
        code, output = self.archive()
        self.assertEqual(0, code, output)
        directory = self.results / "archive" / "2026-10-21-unit-case-automatic"
        for name in ("prompt.md", "response.md", "assessment.json", "manifest.json"):
            self.assertTrue((directory / name).is_file(), name)
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["passed"])


class DiffTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.response = self.base / "response.md"
        self.response.write_text("A considered answer about totals and caches.", encoding="utf-8")
        self.case = make_case()
        self.other = make_case(id="other-case")
        self.catalog = {self.case["id"]: self.case, self.other["id"]: self.other}

    def store(self, name: str, review: dict) -> Path:
        path = self.base / name
        path.write_text(json.dumps(review, indent=2), encoding="utf-8")
        return path

    def test_diff_refuses_to_compare_two_different_cases(self):
        old = self.store("old.json", make_review(self.case, self.response))
        new = self.store("new.json", make_review(self.other, self.response))
        code, output = capture(evaluator.command_diff, old, new, self.catalog)
        self.assertEqual(1, code, output)
        self.assertIn("Cannot diff two different cases", output)

    def test_a_flag_only_regression_is_not_reported_as_a_lower_score(self):
        old_review = make_review(self.case, self.response)
        new_review = make_review(self.case, self.response)
        new_review["red_flags"][0]["triggered"] = True
        old = self.store("old.json", old_review)
        new = self.store("new.json", new_review)
        code, output = capture(evaluator.command_diff, old, new, self.catalog)
        self.assertEqual(1, code, output)
        self.assertNotIn("scores lower", output)
        self.assertIn("does not pass where the old run passed", output)

    def test_a_score_drop_is_reported_as_a_lower_score(self):
        old_review = make_review(self.case, self.response)
        new_review = make_review(self.case, self.response)
        new_review["criteria"]["tradeoff"]["score"] = 0
        old = self.store("old.json", old_review)
        new = self.store("new.json", new_review)
        code, output = capture(evaluator.command_diff, old, new, self.catalog)
        self.assertEqual(1, code, output)
        self.assertIn("scores lower", output)
        self.assertNotIn("does not pass where the old run passed", output)

    def test_an_improvement_is_not_a_regression(self):
        old_review = make_review(self.case, self.response)
        old_review["criteria"]["tradeoff"]["score"] = 0
        new_review = make_review(self.case, self.response)
        old = self.store("old.json", old_review)
        new = self.store("new.json", new_review)
        code, output = capture(evaluator.command_diff, old, new, self.catalog)
        self.assertEqual(0, code, output)
        self.assertNotIn("REGRESSION", output)


class PromptOutputTests(unittest.TestCase):
    def test_the_prompt_command_prints_the_prompt_text_itself(self):
        catalog = evaluator.cases()
        case = next(iter(catalog.values()))
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            with mock.patch.object(sys, "argv", ["evaluate.py", "prompt", case["id"]]):
                code = evaluator.main()
        self.assertEqual(0, code)
        self.assertEqual(evaluator.prompt(case, "automatic"), buffer.getvalue())
        self.assertFalse(buffer.getvalue().endswith("\n"))


if __name__ == "__main__":
    unittest.main()
