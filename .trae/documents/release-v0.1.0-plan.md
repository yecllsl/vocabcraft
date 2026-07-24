# VocabCraft v0.1.0 版本规划

## Context

VocabCraft 是词汇学习+制作一体工具，目标用户为需要系统化积累与复习词汇的学习者。核心闭环：拍照 → OCR 识别 → AI 结构化解析 → 保存 → 按遗忘曲线（SM-2/艾宾浩斯）排程复习 → 到期出考题 → 评分 → 更新记忆状态。

v0.1.0 为首个可用版本，聚焦"采集—复习—出题"主闭环跑通，覆盖命令、Skill、Rules、MCP Tools 全链路。本版本定位本地单机、数据本地存储、双环境（TRAEWORK CN / TRAEIDE CN）适配。

---

## 一、版本目标

1. **主闭环可用**：用户可完成"录入词汇 → 到期复习 → 出题评分 → 记忆状态演进"全流程
2. **双环境适配**：`.trae/mcp.json` 使用 `${workspaceFolder}` 变量，TRAEWORK CN 与 TRAEIDE CN 均可启动 MCP Server
3. **数据本地安全**：所有词汇、图片、记忆状态仅本地存储，不外传
4. **降级友好**：OCR、AI 解析失败均有降级方案，不阻塞主流程
5. **配置即真相**：Skills/Rules 作为流程与约束的单一真相源，MCP Server 仅提供服务能力

---

## 二、功能清单

### 1. 词汇采集（capture）

- 拍照 OCR 识别词汇（`ocr_recognize`）
- AI 结构化解析：词形/音标/词性/释义/例句（`parse_vocab`）
- 用户确认后保存，生成 `vocab_id`（`vocab_YYYYMMDD_NNN`）（`save_vocab`）
- 初始化 SM-2 记忆状态与首次复习排程
- OCR 失败降级为手动输入

### 2. 复习（review）

- 查询到期词汇（`schedule_review`，`next_review_date <= 今天`）
- 逐词出题测试（`generate_quiz`）
- 评分并按 SM-2 更新记忆状态（`grade_quiz`，grade 0-5）
- 遗忘曲线参数取自 `resources/forgetting_curve.json`
- grade<3 重置复习周期
- 复习汇总：题数、均分、薄弱词、下次复习日期

### 3. 出考题（quiz）

- 四种题型：选择（choice）/填空（fill）/拼写（spelling）/释义（definition）
- 指定词汇或随机出题
- 题型轮换，连续不超过 2 次相同题型
- 干扰项来自同词性/近义词
- 填空题无例句时降级为释义题

### 4. 统计（stats）

- 总览：总词汇数、到期数、掌握度分布
- 按掌握度/日期/复习进度多维度聚合（`get_statistics`）
- Markdown 表格输出
- 只读，不修改数据

### 5. 导出（export）

- JSON 格式（含记忆状态，用于备份/迁移回本工具）
- CSV 格式（表格核心字段，用于 Excel 查看）
- 导出前用户确认（`export_data`）
- 文件保存到本地 `data/exports/`

### 6. 数据管理（CRUD）

- 查询词汇（`query_vocab`）
- 更新词汇（`update_vocab`）
- 删除词汇（`delete_vocab`）

---

## 三、MCP Tools 清单（11 个）

| Tool | 模块 | 用途 |
|------|------|------|
| `ocr_recognize` | 采集 | 识别图片词汇 |
| `parse_vocab` | 采集 | 结构化解析词汇 |
| `save_vocab` | 采集 | 保存并初始化复习 |
| `query_vocab` | 管理 | 查询词汇 |
| `update_vocab` | 管理 | 更新词汇 |
| `delete_vocab` | 管理 | 删除词汇 |
| `schedule_review` | 复习 | 查询到期词汇 |
| `generate_quiz` | 出题 | 生成考题 |
| `grade_quiz` | 出题 | 评分并更新记忆状态 |
| `get_statistics` | 统计 | 多维度聚合统计 |
| `export_data` | 导出 | 导出 JSON/CSV |

---

## 四、里程碑

| 里程碑 | 内容 | 验收 |
|--------|------|------|
| M1 配置层就绪 | `.trae/` 下 skills/rules/agents/commands 配置文件全部创建 | 文件树完整，SKILL.md 可被 Trae 识别 |
| M2 MCP Server 骨架 | `vocabcraft-mcp/` 服务层搭建，11 个 Tools 注册 | `uv run --directory ${workspaceFolder}/vocabcraft-mcp vocabcraft-mcp` 可启动 |
| M3 采集闭环 | ocr_recognize + parse_vocab + save_vocab | 可录入一条词汇并初始化复习 |
| M4 复习闭环 | schedule_review + generate_quiz + grade_quiz | 可完成到期复习并更新记忆状态 |
| M5 统计与导出 | get_statistics + export_data | 可查看统计并导出 JSON/CSV |
| M6 双环境验证 | TRAEWORK CN + TRAEIDE CN 均启动 | 两个环境 MCP Server 正常加载 Tools |
| M7 v0.1.0 发布 | 文档、安装脚本、打包 | 用户解压即可使用 |

---

## 五、验收标准

### 5.1 功能验收

- [ ] `/capture` 可录入词汇，OCR 失败时可手动输入
- [ ] `/review` 可查询到期词汇并完成复习，grade 正确更新记忆状态
- [ ] `/quiz` 可出四种题型考题并评分
- [ ] `/stats` 可展示总览与多维度统计
- [ ] `/export` 可导出 JSON 与 CSV，导出前有确认
- [ ] grade<3 时复习周期正确重置
- [ ] vocab_id 格式为 `vocab_YYYYMMDD_NNN`

### 5.2 数据安全验收

- [ ] 所有数据仅本地存储
- [ ] 图片存储于 `data/images/`，不外传
- [ ] 导出需用户确认
- [ ] OCR 本地部署，不调外部 API
- [ ] 不记录个人身份信息

### 5.3 双环境验收

- [ ] TRAEWORK CN 下 `${workspaceFolder}` 正确替换，MCP Server 启动
- [ ] TRAEIDE CN 下 `${workspaceFolder}` 正确替换，MCP Server 启动
- [ ] 两个环境均能调用全部 11 个 Tools

### 5.4 降级验收

- [ ] OCR 失败降级为手动输入，不报错
- [ ] AI 解析异常提供重试机制
- [ ] 填空题无例句降级为释义题
- [ ] 导出失败不损坏原数据

---

## 六、风险评估与回退

| 风险 | 缓解措施 |
|------|----------|
| `${workspaceFolder}` 在某些 Trae 版本不替换 | 安装脚本回退：检测未替换时写入实际路径 |
| OCR（PaddleOCR）安装失败 | OCR 为可选依赖，降级为手动输入 |
| 用户未启用项目级 MCP | 安装脚本末尾醒目提示 |
| SM-2 记忆状态计算错误 | 单元测试覆盖 grade 0-5 各档间隔演进 |
| AI 解析结构化字段缺失 | 占位值填充 + 用户确认时修改 |

---

## 七、实施步骤

1. **配置层创建** — `.trae/` 下 skills/rules/agents/commands/mcp/hooks 配置文件
2. **MCP Server 搭建** — `vocabcraft-mcp/` 服务层，注册 11 个 Tools
3. **采集闭环实现** — ocr_recognize + parse_vocab + save_vocab
4. **复习闭环实现** — schedule_review + generate_quiz + grade_quiz（含 SM-2）
5. **统计与导出实现** — get_statistics + export_data
6. **双环境验证** — TRAEWORK CN / TRAEIDE CN 实测
7. **文档与打包** — README、安装脚本、发布包

---

## 八、目标用户体验

```
4 步即可使用：
1. 下载 zip → 解压到本地
2. 运行安装脚本（等依赖安装完成）
3. Trae 打开文件夹 → 启用项目级 MCP → 重启
4. /capture 录入 → /review 复习 → /quiz 练习
```
