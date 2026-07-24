---
name: vocabcraft-data-safety-rules
scope: all
---

# 数据安全规则

1. 所有数据仅存储在本地，禁止上传到任何外部服务
2. 图片文件存储在项目目录下 `data/images/`，不外传
3. 导出数据前必须经用户确认，导出文件保存到本地 `data/exports/`
4. 不记录用户姓名等个人身份信息
5. OCR 本地部署，不调用外部 OCR API
6. 导出失败不得损坏原数据（导出为只读原数据操作）
7. 记忆状态（repetitions/easiness/next_review_date）属于用户学习数据，仅本地存储与更新
