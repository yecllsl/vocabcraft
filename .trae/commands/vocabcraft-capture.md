## Usage
`/capture`

## 命令用途
触发词汇采集流程：通过拍照 OCR 或手动输入，将新词汇结构化解析并保存到本地，同时初始化复习排程。

## 触发条件
- 命令：`/capture`
- 自然语言关键词：录词、录入词汇、添加词汇、拍照录词、采集词汇

## 调用的 Skill
`vocabcraft-capture`（详见 `.trae/skills/vocabcraft-capture/SKILL.md`）

## 执行流程

1. 获取词汇输入（图片路径优先，或直接文本）
2. OCR 识别 → 失则降级为手动输入
3. 调用 `parse_vocab` 结构化解析（词形/音标/释义/例句）
4. 展示解析结果，请用户确认或修改
5. 调用 `save_vocab` 保存，生成 `vocab_id`（`vocab_YYYYMMDD_NNN`）
6. 初始化 SM-2 记忆状态与首次复习排程

## 关键 MCP Tools

| Tool | 用途 |
|------|------|
| `ocr_recognize` | 识别图片词汇 |
| `parse_vocab` | 结构化解析 |
| `save_vocab` | 保存并初始化复习 |

## 约束
- 解析结果必须经用户确认后才保存
- OCR 失败时降级为手动输入，不报错终止
- 详见 `.trae/rules/vocabcraft-capture-rules.md`
