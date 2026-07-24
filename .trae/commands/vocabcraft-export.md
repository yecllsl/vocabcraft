## Usage
`/export [format]`

## 命令用途
导出本地词汇数据为 JSON 或 CSV 文件，便于备份或迁移。

## 触发条件
- 命令：`/export` 或 `/export <format>`
- 自然语言关键词：导出、备份数据、导出词汇、导出 csv

## 调用的 Skill
`vocabcraft-export`（详见 `.trae/skills/vocabcraft-export/SKILL.md`）

## 执行流程

1. 确定导出格式：
   - `json`（默认）：完整结构化数据，含记忆状态
   - `csv`：表格形式，便于用 Excel 查看
2. 展示导出范围与格式，请用户确认
3. 调用 `export_data`，传入 `format` 参数
4. 返回导出文件路径，提示用户位置

## 关键 MCP Tools

| Tool | 用途 |
|------|------|
| `export_data` | 导出词汇数据到文件 |

## 约束
- **导出前必须经用户确认**（数据安全规则）
- 导出文件保存到本地 `data/exports/`，不外传
- 不导出个人身份信息（本项目本就不记录）
- 详见 `.trae/rules/vocabcraft-data-safety-rules.md`
