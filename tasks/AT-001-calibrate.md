# AT-001 · 校准首个案例与评分边界

状态：ready；范围：只审 `001-reporting`，不调用模型 API、不扩题库。

## 给 Codex / Claude 的开场指令

```text
请先读取 AGENTS.md、README.md、docs/HANDOFF.md、docs/FOUNDATION.md、docs/PROTOCOL.md 和 docs/RUBRIC.md，再检查 Git 状态。当前只执行 tasks/AT-001-calibrate.md，不自动推进后续任务。

审阅 cases/001-reporting/case.json，重点检查：
1. 业务事实、硬约束、预算与未知有没有冲突；合成观测是否误写成已证实因果。
2. T1/T2 是否偷偷假定参评者采用了特定 T0 方案。
3. 可接受解空间能否容纳两种不同实现；有没有用技术关键词当答案。
4. managed-platform 变体是否只改变平台能力与运维归属，而不顺手改变其他轴。
5. 评分是否要求参评者知道未披露的 oracle 事实。

先形成有证据的问题列表，只做必要的最小修补；不得添加功能、模型 SDK、向量库、Dashboard 或新的业务案例。
输出 docs/CALIBRATION-001.md，列出发现、修订、保留分歧和需 James 确认的问题。运行已有 validate 和 tests，更新 HANDOFF。
不要将 review_status 改为 reviewed：本轮是 Agent 辅助审阅，仍需 James 或其他领域人员确认。
不要假称已经执行模型对照、专家复核、压测或线上验证。所有建议未获确认前保持 proposed。
```

## 允许修改

首个 case、对应测试、`docs/CALIBRATION-001.md` 与 HANDOFF。若认为 schema 或通用规则有问题，先在审阅记录中说明，不顺手重构全部资料。

## 验收

无无关变更；发现与修补可追溯；现有检查通过；剩余问题诚实列出；James 可以据此决定是否开始三份 T0 回答的流程试验。
