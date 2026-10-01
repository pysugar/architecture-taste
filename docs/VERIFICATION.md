# 本地验证实录

交付日期：2026-09-25。环境：Linux，Python 3.13.5，jsonschema 4.26.0（预装依赖）。

## 实际执行

```bash
uv run --active --no-project python scripts/taste.py validate
uv run --active --no-project python -m unittest discover -s tests -v
uv run --active --no-project python scripts/taste.py check decision examples/decision.json
uv run --active --no-project python scripts/taste.py check review templates/review.json
```

`--active --no-project` 用于交付环境的已有依赖，不是用户项目的推荐长期运行方式。用户首次在项目目录运行 `uv sync`，生成并提交 uv.lock 后再使用锁定依赖。

结构校验输出：

```json
{"cases": 3, "stages": 9, "counterfactuals": 3}
```

单元测试结果：**27 项通过**。覆盖 Schema、重复 ID/JSON key、阶段顺序、导出路径/覆盖保护、当前与隐藏事实边界、实际历史、跨组拒绝串接、题面变更、澄清预算、反事实范围、评审与证据字段检查。

另执行两次 CLI 题面导出：001-reporting/T0 的 taste/full-context；003-platform/T0 的 no-platform 变体 baseline/clarify。成功生成题面；没有把任何题面交给真实模型。导出产生的临时 packet 不打进本交付包，避免被误认为评测结果。

## 未通过或未验证的部分

尝试 `uv lock` 时，交付容器无法解析 pypi.org，安装链路失败。因此**没有生成 uv.lock，也没有完成隔离的干净环境依赖安装验证**。包内只声明 jsonschema 版本范围，不伪造锁文件。需要在可联网环境执行首次 uv sync，再重跑测试。

未在用户 macOS 上运行；没有真实模型对照、领域专家校准、OS 文件访问隔离、生产故障实验或性能评测。这里的“通过”仅限上述本地工具测试，不代表案例语义或 Skill 有效性已经验证。

## 单元测试原始输出

```text
test_all_bundled_cases (test_taste.TasteTests.test_all_bundled_cases) ... ok
test_arm_cannot_change_mid_chain (test_taste.TasteTests.test_arm_cannot_change_mid_chain) ... ok
test_cannot_export_inside_author_repo (test_taste.TasteTests.test_cannot_export_inside_author_repo) ... ok
test_clarify_hides_answers (test_taste.TasteTests.test_clarify_hides_answers) ... ok
test_duplicate_ids_rejected (test_taste.TasteTests.test_duplicate_ids_rejected) ... ok
test_duplicate_json_keys_rejected (test_taste.TasteTests.test_duplicate_json_keys_rejected) ... ok
test_executed_check_requires_reference (test_taste.TasteTests.test_executed_check_requires_reference) ... ok
test_extra_case_field_rejected (test_taste.TasteTests.test_extra_case_field_rejected) ... ok
test_final_review_cannot_be_blank (test_taste.TasteTests.test_final_review_cannot_be_blank) ... ok
test_full_context_cannot_request_more_facts (test_taste.TasteTests.test_full_context_cannot_request_more_facts) ... ok
test_full_context_discloses_current_answers (test_taste.TasteTests.test_full_context_discloses_current_answers) ... ok
test_history_carries_actual_response (test_taste.TasteTests.test_history_carries_actual_response) ... ok
test_no_questions_after_submission (test_taste.TasteTests.test_no_questions_after_submission) ... ok
test_no_reviewer_or_future_text (test_taste.TasteTests.test_no_reviewer_or_future_text) ... ok
test_nonfinite_json_rejected (test_taste.TasteTests.test_nonfinite_json_rejected) ... ok
test_question_budget_includes_unknown_and_repeats (test_taste.TasteTests.test_question_budget_includes_unknown_and_repeats) ... ok
test_question_records_enter_history (test_taste.TasteTests.test_question_records_enter_history) ... ok
test_refuses_existing_output (test_taste.TasteTests.test_refuses_existing_output) ... ok
test_review_dimensions_must_be_unique (test_taste.TasteTests.test_review_dimensions_must_be_unique) ... ok
test_stage_requires_real_history (test_taste.TasteTests.test_stage_requires_real_history) ... ok
test_tampered_prompt_rejected (test_taste.TasteTests.test_tampered_prompt_rejected) ... ok
test_three_stage_chain (test_taste.TasteTests.test_three_stage_chain) ... ok
test_unknown_case_path_rejected (test_taste.TasteTests.test_unknown_case_path_rejected) ... ok
test_unknown_review_evidence_rejected (test_taste.TasteTests.test_unknown_review_evidence_rejected) ... ok
test_unordered_stages_rejected (test_taste.TasteTests.test_unordered_stages_rejected) ... ok
test_variant_uses_replacement_context (test_taste.TasteTests.test_variant_uses_replacement_context) ... ok
test_variants_are_t0_only (test_taste.TasteTests.test_variants_are_t0_only) ... ok

----------------------------------------------------------------------
Ran 27 tests in 0.638s

OK
```
