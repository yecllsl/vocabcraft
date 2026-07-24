## Usage
`/quiz [vocab_id]`

## 命令用途
触发出考题流程：为指定词汇或随机词汇生成考题作练习，支持选择/填空/拼写/释义四种题型。区别于 `/review`：本命令偏"练习"语义，可对未到期词汇主动出题。

## 触发条件
- 命令：`/quiz` 或 `/quiz <vocab_id>`
- 自然语言关键词：出题、考我、测试、练一练、考题

## 调用的 Skill
`vocabcraft-quiz`（详见 `.trae/skills/vocabcraft-quiz/SKILL.md`）

## 执行流程

1. 确定出题范围：指定 `vocab_id` 或随机选取若干词汇
2. 确定题型：用户指定或按复习次数轮换
3. 调用 `generate_quiz` 生成考题
4. 展示考题，等待用户作答
5. 调用 `grade_quiz` 评分（grade 0-5）
6. 展示评分与正确答案
7. 询问是否继续下一题

## 关键 MCP Tools

| Tool | 用途 |
|------|------|
| `generate_quiz` | 生成指定题型考题 |
| `grade_quiz` | 评分并更新记忆状态 |

## 约束
- 连续出题不得使用相同题型超过 2 次（除非用户指定）
- 评分客观，按既定规则给分
- 若作为练习而非正式复习，评分仍会更新记忆状态（与 `/review` 共用 `grade_quiz`）
- 详见 `.trae/rules/vocabcraft-review-rules.md`
