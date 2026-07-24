---
name: vocabcraft-capture-rules
scope: ocr_recognize, parse_vocab, save_vocab, vocabcraft-capture
---

# 采集规则

1. OCR 失败时降级为手动输入，禁止直接报错终止流程
2. 必填字段 word + definitions 不允许为空保存，缺失时必须补全后才保存
3. 图片文件存储在本地 `data/images/`，禁止上传到任何外部服务
4. vocab_id 格式：`vocab_YYYYMMDD_NNN`，NNN 按当日已有编号递增
5. 解析结果需用户确认后才调用 `save_vocab` 保存
6. **word（词形）和 definitions（释义）为必填字段**，不允许为 null 保存——缺失会导致后续出题与复习不可用
   - `definitions` 为 `list[Definition]`，每项 `{text, examples}` 内嵌该释义的关联例句
7. 若 AI 解析未能完成结构化，必须使用占位值填充并提示用户在确认时修改：word 标记"待确认"、definitions 标记"待确认"
8. 保存词汇时必须同时初始化 SM-2 记忆状态（repetitions=0、easiness=2.5、next_review_date=次日）
9. **多义词必须按义项关联例句**：每条例句挂在对应义项的 `definitions[i].examples` 字段下，禁止所有例句堆在某一条释义下或顶层
