## Usage
`/stats [dimension]`

## 命令用途
查看词汇学习统计：词汇总量、掌握度分布、复习进度、到期数量等多维度统计。

## 触发条件
- 命令：`/stats` 或 `/stats <dimension>`
- 自然语言关键词：统计、词汇量、掌握度、复习进度、学习情况

## 调用的 Skill
`vocabcraft-stats`（详见 `.trae/skills/vocabcraft-stats/SKILL.md`）

## 执行流程

1. 确定统计维度（未指定则展示概览）：
   - `overview`：总览（总词汇数、到期数、掌握度分布）
   - `mastery`：按掌握度分组（新词/学习中/已掌握）
   - `date`：按录入日期分组
   - `review`：按复习进度分组（待复习/已掌握/薄弱）
2. 调用 `get_statistics`，传入 `group_by` 参数
3. 以 Markdown 表格形式展示统计结果

## 关键 MCP Tools

| Tool | 用途 |
|------|------|
| `get_statistics` | 按维度聚合统计 |

## 约束
- 统计数据只读，不修改任何词汇记录
- 输出为 Markdown，可直接在对话中展示
- 详见 `.trae/rules/vocabcraft-interaction-rules.md`
