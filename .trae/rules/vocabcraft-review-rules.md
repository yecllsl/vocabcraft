---
name: vocabcraft-review-rules
scope: schedule_review, generate_quiz, grade_quiz, vocabcraft-review, vocabcraft-quiz
---

# 复习规则

1. 遗忘曲线参数取自 `vocabcraft-mcp/resources/forgetting_curve.json`，默认遵循艾宾浩斯曲线
2. grade 评分标准 0-5：5完全记住/4记住略迟疑/3勉强记住/2部分记错/1几乎全忘/0完全忘记
3. grade<3 时必须重置复习周期（回到短间隔），不得递增间隔
4. 到期词汇（`next_review_date <= 今天`）必须复习，用户跳过时需记录原因且不延后日期
5. 每次评分后必须更新 SM-2 记忆状态：repetitions、easiness、next_review_date
6. 连续出题不得使用相同题型超过 2 次（除非用户指定），保证题型多样性
7. 评分客观，按既定规则给分，禁止因用户情绪或求情调整 grade
8. 选择题干扰项应来自同词性或近义词汇，避免明显错误选项
9. 填空题优先使用词汇自带 examples，无例句时降级为释义题
10. 复习结束必须汇总：题数、均分、grade<3 薄弱词列表、下次复习日期分布
