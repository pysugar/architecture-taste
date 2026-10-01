#!/usr/bin/env python3
"""Validate cases and export manual, stage-scoped architecture exercises.

This tool never calls a model, grades architecture, or creates an OS sandbox.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
DIMENSIONS = {"context", "constraint_fit", "tradeoffs", "evolution", "verification", "uncertainty"}


def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON value: {value}")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates,
                      parse_constant=reject_constant)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def schema_check(value: Any, name: str) -> None:
    schema = read_json(ROOT / "schemas" / f"{name}.schema.json")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(list(e.path)))
    if errors:
        lines = [f"{list(e.path)}: {e.message}" for e in errors[:10]]
        raise ValueError("Schema validation failed:\n" + "\n".join(lines))


def unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {label}")


def validate_case(case: dict[str, Any]) -> None:
    schema_check(case, "case")
    stage_ids = [stage["stage_id"] for stage in case["stages"]]
    if stage_ids != [f"T{i}" for i in range(len(stage_ids))]:
        raise ValueError("Stage IDs must be contiguous and ordered from T0")
    unique([v["variant_id"] for v in case["variants"]], "variant IDs")
    if any(v["variant_id"] == "base" for v in case["variants"]):
        raise ValueError("The variant ID 'base' is reserved")
    for stage in case["stages"]:
        ids = ([f["id"] for f in stage["public"]["facts"]]
               + [c["id"] for c in stage["public"]["constraints"]]
               + [o["id"] for o in stage["oracle"]])
        unique(ids, "fact/constraint/oracle IDs within a stage")
        requirements = stage["reviewer"]["critical_requirements"]
        unique([r["id"] for r in requirements], "critical requirement IDs")
        for requirement in requirements:
            if not set(requirement["supported_by"]).issubset(ids):
                raise ValueError(f"Unknown evidence IDs in {requirement['id']}")
    for variant in case["variants"]:
        ids = ([f["id"] for f in variant["replacement_public"]["facts"]]
               + [c["id"] for c in variant["replacement_public"]["constraints"]]
               + [o["id"] for o in variant["replacement_oracle"]])
        unique(ids, "variant fact/constraint/oracle IDs")


def load_case(case_id: str) -> tuple[dict[str, Any], Path]:
    path = (ROOT / "cases" / case_id / "case.json").resolve()
    if not path.is_relative_to((ROOT / "cases").resolve()) or path.parent.name != case_id:
        raise ValueError("Invalid case ID")
    case = read_json(path)
    validate_case(case)
    if case["case_id"] != case_id:
        raise ValueError("Case ID does not match directory")
    return case, path


def select_stage(case: dict[str, Any], stage_id: str, variant_id: str) -> dict[str, Any]:
    stages = [s for s in case["stages"] if s["stage_id"] == stage_id]
    if not stages:
        raise ValueError(f"Unknown stage: {stage_id}")
    stage = copy.deepcopy(stages[0])
    if variant_id != "base":
        if stage_id != "T0":
            raise ValueError("Counterfactual variants are T0-only in v0.1")
        variants = [v for v in case["variants"] if v["variant_id"] == variant_id]
        if not variants:
            raise ValueError(f"Unknown variant: {variant_id}")
        stage["public"] = variants[0]["replacement_public"]
        stage["oracle"] = variants[0]["replacement_oracle"]
    return stage


def read_answers(packet: Path) -> list[dict[str, Any]]:
    path = packet / "answers.jsonl"
    if not path.exists():
        return []
    return [json.loads(line, object_pairs_hook=no_duplicates, parse_constant=reject_constant)
            for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_packet(packet: Path) -> dict[str, Any]:
    meta = read_json(packet / "run_meta.json")
    if meta.get("runner_version") != VERSION:
        raise ValueError("Unsupported runner version")
    expected_files = {"INPUT.md", "PROMPT.md", "HISTORY.json"}
    if set(meta.get("input_sha256", {})) != expected_files:
        raise ValueError("Invalid packet hash manifest")
    for name, expected in meta["input_sha256"].items():
        if digest(packet / name) != expected:
            raise ValueError(f"Packet input changed: {name}")
    return meta


def export_packet(case_id: str, stage_id: str, arm: str, mode: str, output: Path,
                  variant: str = "base", previous: Path | None = None,
                  trial: str = "manual-001", model_label: str = "unspecified") -> dict[str, Any]:
    if arm not in {"baseline", "adr", "taste"} or mode not in {"full-context", "clarify"}:
        raise ValueError("Invalid arm or mode")
    if not trial.strip() or not model_label.strip():
        raise ValueError("Trial and model label cannot be blank")
    output = output.resolve()
    if output.is_relative_to(ROOT) or ROOT.is_relative_to(output):
        raise ValueError("Export outside the authoring repository, not inside it or to its ancestor")
    if output.exists():
        raise ValueError(f"Refusing to overwrite an existing path: {output}")
    case, case_path = load_case(case_id)
    stage = select_stage(case, stage_id, variant)
    instruction_path = (ROOT / "skills/architecture-taste/SKILL.md" if arm == "taste"
                        else ROOT / "prompts" / f"{arm}.md")
    instruction_hash = digest(instruction_path)
    runner_hash = digest(Path(__file__))
    index = int(stage_id[1:])
    history: list[dict[str, Any]] = []
    if index == 0 and previous is not None:
        raise ValueError("T0 cannot have previous history")
    if index > 0:
        if previous is None:
            raise ValueError("T1+ requires the actual previous packet with response.md")
        prior = verify_packet(previous)
        for key, expected in {"case_id": case_id, "arm": arm, "mode": mode,
                              "variant": variant, "trial_id": trial, "model_label": model_label,
                              "stage_id": f"T{index-1}", "source_sha256": digest(case_path),
                              "instruction_sha256": instruction_hash, "runner_sha256": runner_hash}.items():
            if prior.get(key) != expected:
                raise ValueError(f"Previous packet mismatch: {key}")
        response = (previous / "response.md").read_text(encoding="utf-8")
        if not response.strip():
            raise ValueError("Previous response.md is empty")
        history = read_json(previous / "HISTORY.json")
        history.append({"stage_id": prior["stage_id"],
                        "input": (previous / "INPUT.md").read_text(encoding="utf-8"),
                        "clarifications": read_answers(previous), "response": response,
                        "response_sha256": digest(previous / "response.md")})
    instructions = instruction_path.read_text(encoding="utf-8")
    disclosed = ([{"id": o["id"], "topic": o["topic"], "answer": o["answer"]}
                  for o in stage["oracle"]] if mode == "full-context" else [])
    payload = {"case_id": case_id, "stage_id": stage_id, "synthetic": True,
               "context": stage["public"], "additional_facts": disclosed}
    mode_text = ("本阶段可公开的补充事实已全部给出。仍不确定的内容请标为假设或待确认。"
                 if mode == "full-context" else
                 "最多提出 3 个原子澄清问题，由操作员逐题回答。预算耗尽后请条件性决策或说明阻塞；不可自行查看题库。")
    current = ("# 当前阶段\n\n" + mode_text
               + "\n\n仅分析当前上下文与历史，不虚构未来、工具执行或验证结果。输出语言为中文；格式不限。\n\n"
               + "## 本组工作指令\n\n" + instructions
               + "\n\n## 案例事实\n\n```json\n"
               + json.dumps(payload, ensure_ascii=False, indent=2) + "\n```\n")
    prompt = current + "\n## 已发生的决策历史\n\n```json\n" + json.dumps(history, ensure_ascii=False, indent=2) + "\n```\n"
    output.mkdir(parents=True)
    (output / "INPUT.md").write_text(current, encoding="utf-8")
    (output / "PROMPT.md").write_text(prompt, encoding="utf-8")
    write_json(output / "HISTORY.json", history)
    (output / "answers.jsonl").write_text("", encoding="utf-8")
    meta = {"runner_version": VERSION, "created_at_utc": now(), "case_id": case_id,
            "stage_id": stage_id, "variant": variant, "arm": arm, "mode": mode,
            "trial_id": trial, "model_label": model_label, "source_sha256": digest(case_path),
            "instruction_sha256": instruction_hash, "runner_sha256": runner_hash,
            "question_budget": 3 if mode == "clarify" else 0,
            "input_sha256": {name: digest(output / name) for name in ("INPUT.md", "PROMPT.md", "HISTORY.json")},
            "model_execution": "not_performed_by_runner", "sandbox": "not_provided_by_runner",
            "model_parameters": {}, "harness_configuration": "operator_must_record_before_trial",
            "actual_usage_and_cost": None, "review_status": "not_reviewed"}
    write_json(output / "run_meta.json", meta)
    return meta


def answer_question(packet: Path, key: str, question: str) -> str:
    meta = verify_packet(packet)
    if meta["mode"] != "clarify":
        raise ValueError("Only clarify-mode packets accept questions")
    if (packet / "response.md").exists():
        raise ValueError("Cannot disclose more facts after response.md has been submitted")
    if not question.strip():
        raise ValueError("Question must not be empty")
    answers = read_answers(packet)
    if len(answers) >= meta["question_budget"]:
        raise ValueError("Question budget exhausted")
    case, path = load_case(meta["case_id"])
    if digest(path) != meta["source_sha256"]:
        raise ValueError("Case changed after export; begin a new trial")
    stage = select_stage(case, meta["stage_id"], meta["variant"])
    matches = [item for item in stage["oracle"] if item["id"] == key]
    if key != "UNKNOWN" and not matches:
        raise ValueError("Unknown oracle key; use UNKNOWN to record an unanswerable question")
    answer = matches[0]["answer"] if matches else "案例没有该事实；请保留为未知，不要自行补全。"
    record = {"turn": len(answers) + 1, "question": question, "fact_id": key,
              "answer": answer, "answered_at_utc": now(), "mapping": "human_operator"}
    with (packet / "answers.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    return answer


def validate_decision(value: dict[str, Any]) -> None:
    schema_check(value, "decision")
    for check in value["verification"]:
        if check["evidence_status"] == "executed" and not check["evidence_ref"]:
            raise ValueError("Executed verification requires an evidence reference; this does not prove its truth")
    if value["migration"]["required"] and not value["migration"]["steps"]:
        raise ValueError("A required migration needs explicit steps")


def validate_review(value: dict[str, Any]) -> None:
    schema_check(value, "review")
    names = [d["dimension"] for d in value["dimensions"]]
    if set(names) != DIMENSIONS or len(names) != 6:
        raise ValueError("Reviews require exactly the six unique dimensions")
    unique([c["requirement_id"] for c in value["critical_assessments"]], "review requirement IDs")
    if value["status"] == "final":
        for item in value["dimensions"]:
            if item["score"] is None or not item["response_evidence"] or not item["context_evidence"]:
                raise ValueError("Final scores require a score and response/context evidence")
        outcomes = [item["outcome"] for item in value["critical_assessments"]]
        if "fail" in outcomes and value["overall"] != "unsafe":
            raise ValueError("A confirmed critical violation cannot be offset by quality scores")
        if "fail" not in outcomes and "unclear" in outcomes and value["overall"] != "indeterminate":
            raise ValueError("Unresolved critical constraints require an indeterminate result")


def validate_repo() -> dict[str, int]:
    paths = sorted((ROOT / "cases").glob("*/case.json"))
    if not paths:
        raise ValueError("No cases found")
    counts = {"cases": 0, "stages": 0, "counterfactuals": 0}
    for path in paths:
        case = read_json(path)
        validate_case(case)
        counts["cases"] += 1
        counts["stages"] += len(case["stages"])
        counts["counterfactuals"] += len(case["variants"])
    validate_decision(read_json(ROOT / "examples/decision.json"))
    validate_review(read_json(ROOT / "templates/review.json"))
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="Validate case structure; not architecture quality")
    commands.add_parser("list", help="List local synthetic development cases")
    export = commands.add_parser("export", help="Export a participant prompt outside this repository")
    export.add_argument("--case", required=True)
    export.add_argument("--stage", default="T0")
    export.add_argument("--arm", choices=("baseline", "adr", "taste"), default="baseline")
    export.add_argument("--mode", choices=("full-context", "clarify"), default="full-context")
    export.add_argument("--variant", default="base")
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--previous", type=Path)
    export.add_argument("--trial", default="manual-001")
    export.add_argument("--model-label", default="unspecified")
    answer = commands.add_parser("answer", help="Operator-only fixed-fact disclosure")
    answer.add_argument("--packet", type=Path, required=True)
    answer.add_argument("--key", required=True)
    answer.add_argument("--question", required=True)
    check = commands.add_parser("check", help="Check optional decision/review record structure")
    check.add_argument("kind", choices=("decision", "review"))
    check.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            print(json.dumps(validate_repo(), ensure_ascii=False))
        elif args.command == "list":
            for path in sorted((ROOT / "cases").glob("*/case.json")):
                c = read_json(path)
                print(f"{c['case_id']}\t{c['title']}\t{c['split']} / {c['review_status']}")
        elif args.command == "export":
            export_packet(args.case, args.stage, args.arm, args.mode, args.output,
                          args.variant, args.previous, args.trial, args.model_label)
            print(f"Exported: {args.output.resolve()}\nNo model was executed. Provide PROMPT.md to the participant.")
        elif args.command == "answer":
            print(answer_question(args.packet, args.key, args.question))
        elif args.command == "check":
            value = read_json(args.file)
            (validate_decision if args.kind == "decision" else validate_review)(value)
            print("Structure valid; engineering correctness was not assessed.")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
