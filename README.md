# Architecture Taste · 架构品味

**为当前上下文做可解释、可验证、可演化的架构决定。**

状态：`0.1.0 / incubating`。这是一个可直接落库的研究与实践基座，不是已经证明有效的架构顾问产品，也不是已校准的模型排行榜。

## 从哪里开始

第一次只需读三份文件：本 README、`docs/FOUNDATION.md`、`tasks/AT-001-calibrate.md`。完整计划见 [ROADMAP.md](ROADMAP.md)。

建议稳定路径：`/opt/foundry/projects/architecture-taste`。阶段、可见性等属性写入 `pyproject.toml`，不通过不断搬动目录表达。运行输出放到 `/opt/foundry/artifacts/architecture-taste/`；参与评测的 Agent **不能直接进入本题库仓库**。

## 项目做什么

日常使用面是一个可复用的 Architecture Taste Skill：先理解上下文，明确不变量，比较少量真实选项，给出当前决定、验证方式和复核条件。

研究面是一个 Architecture Judgment Lab：在固定或可询问的上下文中比较不同工作方法，记录 AI 如何处理约束、做取舍，以及在新事实出现时保留、修改或撤销旧决定。

两者共享决策协议，但**Skill 不读取题库的评分答案，评测也不因方法写进 Skill 就宣布有效**。

## 已有内容

- 三个原创合成案例，每个 T0–T2 三阶段，共九个阶段；另有三个 T0 反事实变体。
- 案例、可选结构化决策、人工评审记录的 JSON Schema。
- 实验性 Skill、普通提示、简版 ADR 三种工作指令。
- 一个 Python 手工评测辅助脚本：校验、题面导出、定额澄清、真实回答历史衔接。
- 单元测试、决策/评审模板、评估协议、路线图和可交给 Codex 的首批任务。

**尚未完成：**真实模型对照试验、人工领域校准、自动模型调用、操作系统级隔离、生产代码验证、真实项目效果评估、独立保留测试集。全部案例目前是 `synthetic / development / unreviewed`。

## 运行

需要已有 Python 3.11+ 与 `uv`。唯一运行依赖是 `jsonschema`；不需要模型 API Key、数据库、容器或 Agent framework。

本交付环境无法连接 PyPI，因此没有生成 `uv.lock`，也未完成干净环境依赖安装验证。下列首次 `uv sync` 会在可联网环境解析依赖并生成锁文件；确认测试通过后将 `uv.lock` 纳入 Git，后续改用 `uv sync --locked`。本地已有依赖环境的实际测试结果见 `docs/VERIFICATION.md`。

```bash
cd /opt/foundry/projects/architecture-taste
uv sync
uv run scripts/taste.py validate
uv run python -m unittest discover -s tests -v
uv run scripts/taste.py list
```

### 第一个练习：先做普通提示的 T0

```bash
uv run scripts/taste.py export \
  --case 001-reporting \
  --stage T0 \
  --arm baseline \
  --mode full-context \
  --trial pilot-001 \
  --model-label your-model-and-client-version \
  --output /opt/foundry/artifacts/architecture-taste/pilot-001/baseline/T0
```

把导出的 `PROMPT.md` **单独**交给一个未看过本题库的新会话。原样保存它的最终回答为同目录 `response.md`。不要把教师笔记或本仓库 AGENTS.md 给参评会话。

`run_meta.json` 的 `model_label` 只是操作者自报标签。实际模型、客户端/版本、设置、工具与记忆状态、用量等，需由操作者补录；脚本不会验证模型身份。

进入下一阶段时使用同一组别、模型标签与 trial，显式衔接实际答案：

```bash
uv run scripts/taste.py export \
  --case 001-reporting \
  --stage T1 \
  --arm baseline \
  --mode full-context \
  --trial pilot-001 \
  --model-label your-model-and-client-version \
  --previous /opt/foundry/artifacts/architecture-taste/pilot-001/baseline/T0 \
  --output /opt/foundry/artifacts/architecture-taste/pilot-001/baseline/T1
```

T2 同理。推荐每个阶段使用新会话并提供完整导出题面，以显式、相同方式恢复历史；也可用连续会话，但不可混用后当作同一实验条件。

为 `adr`、`taste` 组分别开新 trial 路径，保持模型和实验设置一致。**先完成 baseline，再让参评 Agent 看 Skill。**

### 澄清模式

将导出参数改为 `--mode clarify`。每阶段最多三次原子澄清；操作员在源案例中按问题主题找到对应 oracle ID。ID 只供操作员映射，不给参评者看答案菜单。

```bash
uv run scripts/taste.py answer \
  --packet /opt/foundry/artifacts/architecture-taste/clarify-001/baseline/T0 \
  --key O01 \
  --question '报表多久完成算达标？'
```

操作员把工具返回的答案原样交给参评者。问到不存在的事实，用 `--key UNKNOWN`；照样消耗一次预算。脚本不判断自然语言问题是否对应 ID，也不能自动拆复合问题。规则详见 `docs/PROTOCOL.md`。

在每个阶段提交 `response.md` 前完成澄清；提交后不再披露新事实。问答存入 `answers.jsonl`，后续阶段自动衔接。

### 结构校验不是质量判决

```bash
uv run scripts/taste.py check decision examples/decision.json
uv run scripts/taste.py check review templates/review.json
```

普通提示、ADR 和 Skill 都可输出自然语言，不强制它们填写复杂 JSON。`decision.schema.json` 用于实践沉淀或评审人后置规范化；原始回答必须保留，补写内容不得冒充原始回答。

## 目录职责

| 路径 | 职责 |
|---|---|
| `AGENTS.md` / `CLAUDE.md` | 维护本项目的 Agent 指令，不是参评模型指令 |
| `docs/FOUNDATION.md` | 定位、假设、方法、最小闭环 |
| `docs/PROTOCOL.md` / `docs/RUBRIC.md` | 实验协议与评分边界 |
| `skills/architecture-taste/` | 可复用方法，未完成效果验证 |
| `cases/` | 作者/操作员材料，包含隐藏事实和教师笔记 |
| `schemas/` / `templates/` | 数据契约与人工记录 |
| `scripts/` / `tests/` | 本地工具及验证 |
| `tasks/` / `docs/HANDOFF.md` | 下一步与交接状态 |

## 使用边界

本基座不自动安装全局 Skill，不修改 `~/.codex` 或 `~/.claude`，不创建 GitHub 仓库，不上传任何案例，不执行任何模型 API 调用。

`skills/architecture-taste/SKILL.md` 是可移植的方法正文；不同客户端的安装/发现目录不同，第一次可直接提供正文使用。正式集成前核对客户端实际版本与当前文档，且不要把实验 Skill 全局启用后再跑 baseline。

项目还没有选择公开发布许可证；不要把“生成了仓库”当作“已决定开源”。案例均为原创合成教学材料，不应被对外描述为真实客户事故或经过专家认可的标准答案。

参考方法与工具的原始资料见 [docs/SOURCES.md](docs/SOURCES.md)。验证实录见 [docs/VERIFICATION.md](docs/VERIFICATION.md)。
