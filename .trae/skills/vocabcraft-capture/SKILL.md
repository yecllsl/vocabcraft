---
name: vocabcraft-capture
description: Use when 用户想录入词汇、拍照识别单词、添加生词、采集词汇、保存单词
---

# 词汇采集流程

## Overview

词汇学习采集助手，负责将纸质/图片词汇转化为结构化数据并保存。核心流程：OCR识别 → AI结构化解析 → 用户确认 → 保存记录 → 初始化复习排程。

## When to Use

- 用户说"录入词汇"、"拍照录词"、"添加生词"、"采集词汇"
- 用户提供词汇图片路径，或要求直接输入词汇文本
- 用户需要将新词保存到本地词库并开始按遗忘曲线复习

## Workflow

### 1. 获取输入
要求用户提供词汇图片路径，或允许直接输入词汇文本。

### 2. OCR识别
调用 `ocr_recognize` Tool。
- 失败时提示用户手动输入词汇文本，不终止流程

### 3. AI结构化解析
调用 `parse_vocab` Tool，获取 parse_prompt 后**智能体本身作为 LLM 直接按 prompt 输出结构化 JSON**，提取：
- word（词形，必填）
- phonetic（音标）
- pos（词性）
- definitions（释义，必填，`list[Definition]`，每项 `{text, examples}` 内嵌该释义的关联例句）

**多义词必须按义项分组例句**：每条例句挂在对应该义项的 `examples` 字段下，禁止所有例句堆在某一条释义下或顶层。

### 4. 展示确认
将解析结果以结构化格式展示给用户，请用户确认或修改。

### 5. 保存记录
调用 `save_vocab` Tool，生成 `vocab_id`（格式：`vocab_YYYYMMDD_NNN`），并初始化 SM-2 记忆状态（repetitions=0、easiness=2.5、首次复习次日）。

## Quick Reference

| 步骤 | Tool | 降级方案 |
|------|------|----------|
| OCR识别 | `ocr_recognize` | 手动输入词汇文本 |
| 结构化解析 | `parse_vocab` | 标记待确认，必填字段缺失时提示补全 |
| 保存记录 | `save_vocab` | - |

## Common Mistakes

- **OCR失败直接报错**：应提示用户手动输入，而非终止流程
- **跳过用户确认**：解析结果必须经用户确认后才保存
- **必填字段缺失仍保存**：`word` 和 `definitions` 不允许为空，缺失必须补全
- **vocab_id格式错误**：必须使用 `vocab_YYYYMMDD_NNN` 格式，NNN按当日已有编号递增
- **图片外传**：图片仅本地存储于 `data/images/`，禁止上传外部服务
- **例句未按义项分组**：多义词必须将例句挂到对应释义的 `definitions[i].examples` 下，禁止堆在某一条释义或顶层

## 约束规则

- OCR失败时降级为手动输入，禁止直接报错
- 必填字段 word + definitions 不允许为空保存
- 图片文件存储在本地 `data/images/`，不外传
- vocab_id 格式：`vocab_YYYYMMDD_NNN`
- 解析结果需用户确认后才保存
- 详见 `.trae/rules/vocabcraft-capture-rules.md`、`vocabcraft-data-safety-rules.md`
