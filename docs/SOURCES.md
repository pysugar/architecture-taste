# 原始资料与引用边界

核对日期：2026-09-25。这里只链接原始方法和官方工具文档，不附送原文副本。

本仓库的方法组合、合成案例、试验设计与路线图属于项目建议；下列来源不构成对 Architecture Taste 效果、商业价值或新颖性的证明。

| 编号 | 原始资料 | 本项目借鉴的范围 |
|---|---|---|
| S1 | Michael Nygard, [Documenting Architecture Decisions](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions), 2011 | 情境、决定、状态与后果；保留当时理由，避免重写历史 |
| S2 | CMU SEI, [Quality Attribute Workshop Collection](https://www.sei.cmu.edu/library/quality-attribute-workshop-collection/) | 从业务目标识别关键质量属性与需求，而不是先画技术图 |
| S3 | CMU SEI, [Architecture Tradeoff Analysis Method Collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/) | 通过场景识别风险、敏感点和取舍；本项目不是官方 ATAM 认证流程 |
| S4 | Martin Fowler, [Foreword to Building Evolutionary Architectures](https://martinfowler.com/articles/evo-arch-forward.html) | 增量变化、反馈环与架构适应度检查 |
| S5 | [Architectural Katas](https://www.architecturalkatas.com/) | 用反复设计练习培养判断；不复制其具体题目 |
| S6 | Anthropic Engineering, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | 区分代码/模型/人工评审，人工校准和轨迹检查；已有过度工程评测，不能宣称该方向无人涉足 |
| S7 | Martin Fowler, [Yagni](https://martinfowler.com/bliki/Yagni.html) | 避免为未经证实的未来需求预建复杂度；不是忽略当前必要保障 |
| S8 | Agent Skills, [Specification](https://agentskills.io/specification) | SKILL.md 的元数据与可移植组织形式；格式兼容不等于任何客户端自动安装 |
| S9 | OpenAI Codex, [Custom instructions with AGENTS.md](https://developers.openai.com/codex/agent-configuration/agents-md) | 项目级指令及作用域；用于仓库维护，不自动给参评模型 |
| S10 | Claude Code, [How Claude remembers your project](https://code.claude.com/docs/en/memory) | AGENTS.md/CLAUDE.md 的版本与加载差异；本包用 @AGENTS.md 作为共享入口兼容方式 |
| S11 | Astral, [Working on projects](https://docs.astral.sh/uv/guides/projects/) | pyproject、uv.lock、uv sync、uv run；不手工管理虚拟环境 |
| S12 | JSON Schema, [Creating your first schema](https://json-schema.org/learn/getting-started-step-by-step) | 数据结构检查；不把结构有效当成语义正确 |

## 没有被声称的事实

未证明“上下文不足是所有模型架构失败的主要原因”；没有同类项目全面竞品调查；没有证明 Skill 优于普通 ADR；没有模型排名、就业趋势数据或商业收入预测。上述内容不应从之前聊天中的推测继承为本项目事实。

## 工具文档时效

客户端指令发现、Skill 安装和配置方式会变化。首次接入真实 Codex/Claude 环境前，应查看实际版本及对应官方说明。本包不修改全局配置，不复制插件，不包含厂商 SDK，也不依赖某个特定模型版本。
