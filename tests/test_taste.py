"""Local checks for structure, staged disclosure, and trace integrity."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("taste", ROOT / "scripts/taste.py")
assert spec and spec.loader
taste = importlib.util.module_from_spec(spec)
spec.loader.exec_module(taste)


class TasteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def export(self, name="packet", **kwargs):
        args = dict(case_id="001-reporting", stage_id="T0", arm="baseline",
                    mode="full-context", output=self.base / name)
        args.update(kwargs)
        taste.export_packet(**args)
        return args["output"]

    def test_all_bundled_cases(self):
        self.assertEqual(taste.validate_repo(), {"cases": 3, "stages": 9, "counterfactuals": 3})

    def test_extra_case_field_rejected(self):
        case, _ = taste.load_case("001-reporting")
        case["gold_answer"] = "Kafka"
        with self.assertRaises(ValueError): taste.validate_case(case)

    def test_duplicate_ids_rejected(self):
        case, _ = taste.load_case("001-reporting")
        case["stages"][0]["public"]["facts"][1]["id"] = "F01"
        with self.assertRaises(ValueError): taste.validate_case(case)

    def test_unknown_review_evidence_rejected(self):
        case, _ = taste.load_case("001-reporting")
        case["stages"][0]["reviewer"]["critical_requirements"][0]["supported_by"] = ["NO_SUCH_FACT"]
        with self.assertRaises(ValueError): taste.validate_case(case)

    def test_unordered_stages_rejected(self):
        case, _ = taste.load_case("001-reporting")
        case["stages"].reverse()
        with self.assertRaises(ValueError): taste.validate_case(case)

    def test_no_reviewer_or_future_text(self):
        packet = self.export()
        text = (packet / "PROMPT.md").read_text()
        case, _ = taste.load_case("001-reporting")
        self.assertNotIn(case["stages"][1]["public"]["situation"], text)
        self.assertNotIn(case["stages"][0]["reviewer"]["acceptable_families"][0], text)
        self.assertNotIn("changes_decision_because", text)
        self.assertNotIn("critical_requirements", text)

    def test_full_context_discloses_current_answers(self):
        packet = self.export()
        case, _ = taste.load_case("001-reporting")
        self.assertIn(case["stages"][0]["oracle"][0]["answer"], (packet / "PROMPT.md").read_text())

    def test_clarify_hides_answers(self):
        packet = self.export(mode="clarify")
        case, _ = taste.load_case("001-reporting")
        self.assertNotIn(case["stages"][0]["oracle"][0]["answer"], (packet / "PROMPT.md").read_text())

    def test_cannot_export_inside_author_repo(self):
        with self.assertRaises(ValueError): self.export(output=ROOT / "runs" / "unsafe")

    def test_refuses_existing_output(self):
        self.export()
        with self.assertRaises(ValueError): self.export()

    def test_stage_requires_real_history(self):
        with self.assertRaises(ValueError): self.export(stage_id="T1")

    def test_history_carries_actual_response(self):
        p0 = self.export()
        (p0 / "response.md").write_text("Keep my actual initial design.")
        p1 = self.export(name="T1", stage_id="T1", previous=p0)
        history = taste.read_json(p1 / "HISTORY.json")
        self.assertEqual(history[0]["response"], "Keep my actual initial design.")
        self.assertEqual(history[0]["response_sha256"], taste.digest(p0 / "response.md"))

    def test_three_stage_chain(self):
        prior = self.export(name="T0")
        for stage_id in ("T1", "T2"):
            (prior / "response.md").write_text(f"Actual proposal at {prior.name}")
            prior = self.export(name=stage_id, stage_id=stage_id, previous=prior)
        self.assertEqual(len(taste.read_json(prior / "HISTORY.json")), 2)

    def test_arm_cannot_change_mid_chain(self):
        p0 = self.export()
        (p0 / "response.md").write_text("A proposal")
        with self.assertRaises(ValueError): self.export(name="T1", stage_id="T1", previous=p0, arm="taste")

    def test_tampered_prompt_rejected(self):
        packet = self.export()
        (packet / "PROMPT.md").write_text("changed")
        with self.assertRaises(ValueError): taste.verify_packet(packet)

    def test_variant_uses_replacement_context(self):
        packet = self.export(variant="managed-platform")
        text = (packet / "PROMPT.md").read_text()
        self.assertIn("独立团队值守的消息平台", text)
        self.assertNotIn("reviewer_note", text)

    def test_variants_are_t0_only(self):
        with self.assertRaises(ValueError): self.export(stage_id="T1", variant="managed-platform")

    def test_unknown_case_path_rejected(self):
        with self.assertRaises(ValueError): taste.load_case("../schemas")

    def test_question_budget_includes_unknown_and_repeats(self):
        packet = self.export(mode="clarify")
        taste.answer_question(packet, "UNKNOWN", "What about an unspecified issue?")
        taste.answer_question(packet, "O01", "What is the completion target?")
        taste.answer_question(packet, "O01", "Please repeat the completion target.")
        with self.assertRaises(ValueError): taste.answer_question(packet, "O02", "What are duplicate semantics?")
        self.assertEqual(len(taste.read_answers(packet)), 3)

    def test_no_questions_after_submission(self):
        packet = self.export(mode="clarify")
        (packet / "response.md").write_text("Final proposal")
        with self.assertRaises(ValueError): taste.answer_question(packet, "O01", "Target?")

    def test_full_context_cannot_request_more_facts(self):
        packet = self.export()
        with self.assertRaises(ValueError): taste.answer_question(packet, "O01", "Target?")

    def test_question_records_enter_history(self):
        p0 = self.export(mode="clarify")
        answer = taste.answer_question(p0, "O01", "Target?")
        (p0 / "response.md").write_text("A provisional proposal")
        p1 = self.export(name="T1", stage_id="T1", previous=p0, mode="clarify")
        history = taste.read_json(p1 / "HISTORY.json")
        self.assertEqual(history[0]["clarifications"][0]["answer"], answer)

    def test_executed_check_requires_reference(self):
        decision = taste.read_json(ROOT / "examples/decision.json")
        decision["verification"][0]["evidence_status"] = "executed"
        with self.assertRaises(ValueError): taste.validate_decision(decision)

    def test_final_review_cannot_be_blank(self):
        review = taste.read_json(ROOT / "templates/review.json")
        review["status"] = "final"
        with self.assertRaises(ValueError): taste.validate_review(review)

    def test_review_dimensions_must_be_unique(self):
        review = taste.read_json(ROOT / "templates/review.json")
        review["dimensions"][1] = copy.deepcopy(review["dimensions"][0])
        with self.assertRaises(ValueError): taste.validate_review(review)

    def test_duplicate_json_keys_rejected(self):
        path = self.base / "bad.json"
        path.write_text('{"a": 1, "a": 2}')
        with self.assertRaises(ValueError): taste.read_json(path)

    def test_nonfinite_json_rejected(self):
        path = self.base / "bad.json"
        path.write_text('{"a": NaN}')
        with self.assertRaises(ValueError): taste.read_json(path)


if __name__ == "__main__":
    unittest.main()
