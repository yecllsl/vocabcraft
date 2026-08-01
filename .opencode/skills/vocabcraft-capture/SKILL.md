---
name: vocabcraft-capture
description: Use when 用户想录入词汇、拍照识别单词、添加生词、采集词汇、保存单词
---

# 词汇采集流程

## Overview

词汇学习采集助手，负责将图片词汇转化为结构化数据并保存。
核心流程：**多模态 LLM 直接解析图片（对话上传 > 本地路径）→ OCR 降级 → 用户确认 → 保存记录 → 初始化复习排程**。

## When to Use

- 用户说"录入词汇"、"拍照录词"、"添加生词"、"采集词汇"
- 用户在对话中上传了词汇图片（首选模式）
- 用户提供词汇图片本地路径，或要求直接输入词汇文本
- 用户需要将新词保存到本地词库并开始按遗忘曲线复习

## Workflow

### 0. Excel 文件导入（新增）
- **触发条件**: 用户说"导入Excel文件"、"从表格添加词汇"、"导入词汇表"
- **执行流程**: 
  1. 获取.xlsx文件路径
  2. 调用 `import_xlsx_vocab` 工具解析文件
  3. 展示解析结果（成功数、失败数、错误详情）
  4. 用户确认后保存
- **降级方案**: 如果.xlsx文件格式错误，提示用户修正文件格式

### 1. 获取输入
- **首选**：用户直接在对话中上传词汇图片（图片成为对话上下文的一部分）
- **次选**：用户提供词汇图片的本地文件路径
- **后备**：用户直接输入词汇文本（或 OCR 识别文本）

### 2. 多模态 LLM 解析（首选 + 次选）
调用 `parse_vocab` Tool：
- **对话上传模式**（首选）：不传参数，`parse_vocab()` 返回多模态 prompt，宿主 LLM 直接读取对话上下文中的图片
- **本地路径模式**（次选）：传入 `image_path`，`parse_vocab(image_path=...)` 返回多模态 prompt，宿主 LLM 读取指定路径图片

**宿主 LLM 直接读取图片中的词汇内容**，按 prompt 格式输出结构化 JSON。

- 多模态 LLM 精度远高于传统 OCR，且无需额外安装 PaddleOCR 依赖
- 无需先调用 `ocr_recognize`，一步到位

### 3. OCR 降级（后备）
若多模态 LLM 解析失败（如宿主 LLM 不支持图片读取、图片过于模糊等），降级为 OCR 流程：
1. 调用 `ocr_recognize` Tool 识别图片文字
2. 将识别结果传入 `parse_vocab(ocr_text=...)`，使用文本模式解析
3. OCR 也失败时提示用户手动输入词汇文本，不终止流程

### 4. 展示确认
将解析结果以结构化格式展示给用户，请用户确认或修改。

### 5. 保存记录
调用 `save_vocab` Tool，生成 `vocab_id`（格式：`vocab_YYYYMMDD_NNN`），并初始化 SM-2 记忆状态（repetitions=0、easiness=2.5、首次复习次日）。

## Quick Reference

| 步骤 | 模式 | 调用方式 | 降级方案 |
|------|------|----------|----------|
| Excel导入 | 批量导入 | `import_xlsx_vocab(xlsx_path=...)` | 手动输入词汇文本 |
| 解析（首选） | 对话多模态 | `parse_vocab()`（无参数） | 降级本地路径模式 |
| 解析（次选） | 本地路径多模态 | `parse_vocab(image_path=...)` | 降级 OCR 文本模式 |
| 解析（后备） | OCR 文本 | `ocr_recognize` → `parse_vocab(ocr_text=...)` | 手动输入词汇文本 |
| 保存记录 | - | `save_vocab` | - |

## 优先级说明

1. **Excel 文件批量导入** — 用户提供.xlsx文件路径，调用 `import_xlsx_vocab` 工具
2. **对话上传多模态** — 用户在对话框中上传图片，直接调用 `parse_vocab()` 无参数模式
3. **本地路径多模态** — 用户提供本地图片路径，调用 `parse_vocab(image_path=...)`
4. **OCR 识别 + 文本解析** — 后备方案，需安装 PaddleOCR
5. **手动输入** — 最终降级，用户直接输入词汇文本

## Common Mistakes

- **跳过首选方案直接走 OCR**：应优先使用 `parse_vocab()` 多模态模式，仅在该模式失败时降级
- **对话上传后仍传 image_path**：用户已在对话中上传图片时，`parse_vocab()` 无参数即可，无需传 `image_path`
- **OCR 失败直接报错**：应提示用户手动输入，而非终止流程
- **跳过用户确认**：解析结果必须经用户确认后才保存
- **必填字段缺失仍保存**：`word` 和 `definitions` 不允许为空，缺失必须补全
- **vocab_id格式错误**：必须使用 `vocab_YYYYMMDD_NNN` 格式，NNN按当日已有编号递增
- **图片外传**：图片仅本地存储于 `data/images/`，禁止上传外部服务
- **例句未按义项分组**：多义词必须将例句挂到对应释义的 `definitions[i].examples` 下，禁止堆在某一条释义或顶层

## 约束规则

- 多模态 LLM 解析为首选，OCR 为降级后备
- 对话上传多模态优先于本地路径多模态
- OCR 失败时降级为手动输入，禁止直接报错
- 必填字段 word + definitions 不允许为空保存
- 图片文件存储在本地 `data/images/`，不外传
- vocab_id 格式：`vocab_YYYYMMDD_NNN`
- 解析结果需用户确认后才保存
- 多义词必须将例句挂到对应释义的 `definitions[i].examples` 下
- 详见 AGENTS.md「业务规则 > 采集规则」