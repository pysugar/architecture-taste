# 项目交接

日期：2026-10-02；版本：0.1.0。

## 当前目标

先验证上下文敏感的架构判断方法是否比轻量 ADR 更有价值，再决定扩题库或工程平台。

## 最近变更

- 完善 `.gitignore`：新增 Python、Golang、Web 开发（Node/前端构建产物/包管理/测试缓存等）与常见编辑器/系统临时文件的过滤配置。

## 已提供

项目基础文档、Roadmap、三个合成案例（九阶段、三个 T0 变体）、三个 Schema、实验性 Skill、两个对照提示、人工评审模板、手工题面导出工具、澄清日志与历史衔接、测试和三个后续任务包。

## 未完成

没有真实模型试验；没有独立人工领域校准；没有生产实现验证；没有操作系统隔离；没有模型自动调用；没有 holdout。案例仍是 unreviewed，示例记录仍是 proposed，空白评审模板不是结果。

## 下一任务

`tasks/AT-001-calibrate.md`：只校准 001-reporting；之后需要 James 人工确认。不要自动开始 AT-002 的模型调用或任何付费行为。

## 验证入口

```bash
uv sync
uv run scripts/taste.py validate
uv run python -m unittest discover -s tests -v
```

初始生成环境中的实际结果见 `VERIFICATION.md`。下一位维护者应重新运行，不把本文件当作在他当前环境已通过的证明。

## 注意

本仓库维护 Agent 与参评 Agent 职责不同。不要把完整仓库当参评模型工作目录。源码、case 和 prompt 的任何变化都应创建新的试验版本；不得接续已有哈希不匹配的轨迹。
