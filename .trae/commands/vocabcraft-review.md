## Usage
`/review`

## 命令用途
触发复习流程：查询到期词汇，逐词出题测试，评分后按遗忘曲线（SM-2）更新记忆状态与下次复习日期。

## 触发条件
- 命令：`/review`
- 自然语言关键词：复习、复习词汇、该复习了、今天复习什么

## 调用的 Skill
`vocabcraft-review`（详见 `.trae/skills/vocabcraft-review/SKILL.md`）

## 执行流程

1. 调用 `schedule_review` 查询 `next_review_date <= 今天` 的到期词汇
2. 展示复习概览（题数、预计时长）
3. 逐词循环：
   - `generate_quiz` 生成考题（选择/填空/拼写/释义轮换）
   - 展示考题，等待用户作答
   - `grade_quiz` 评分（grade 0-5）并更新记忆状态
   - 即时反馈对错与正确答案
4. 复习汇总（题数、均分、薄弱词、下次复习日期）

## 关键 MCP Tools

| Tool | 用途 |
|------|------|
| `schedule_review` | 查询到期词汇 |
| `generate_quiz` | 生成考题 |
| `grade_quiz` | 评分并更新记忆状态 |

## 约束
- 到期词汇必须全部复习，跳过需记录原因
- grade<3 重置复习周期
- 详见 `.trae/rules/vocabcraft-review-rules.md`
