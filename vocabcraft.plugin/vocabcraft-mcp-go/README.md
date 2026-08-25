# vocabcraft-mcp-go

VocabCraft MCP Server 的 Go 实现，基于 [go-sage-plugin-kit](https://github.com/yecllsl/go-sage-plugin-kit)。

## 构建

```bash
go build -o vocabcraft-mcp.exe ./cmd/vocabcraft-mcp
```

## 运行

```bash
# 设置数据目录（默认为 exe 同级 ../data）
set VOCABCRAFT_DATA_DIR=D:\data\vocabcraft
vocabcraft-mcp.exe
```

## MCP 配置

```json
{
  "mcpServers": {
    "vocabcraft-mcp": {
      "type": "stdio",
      "command": "path/to/vocabcraft-mcp.exe"
    }
  }
}
```

## 工具列表

| Tool | 用途 |
|------|------|
| `save_vocab` | 保存词汇记录到本地 JSON 文件 |
| `query_vocab` | 按条件查询词汇 |
| `update_vocab` | 更新词汇记录（patch 语义） |
| `delete_vocab` | 删除词汇记录 |
| `parse_vocab` | AI 结构化解析词汇（三模式） |
| `schedule_review` | 基于遗忘曲线生成复习计划 |
| `generate_quiz` | 为指定词汇生成考题 |
| `grade_quiz` | 评分并按 SM-2 更新记忆状态 |
| `get_statistics` | 统计词汇量、掌握度、题型分布 |
| `export_data` | 导出词汇数据为 JSON/CSV |
| `import_xlsx_vocab` | 从 .xlsx 文件批量导入词汇 |

## 依赖

- Go 1.27+
- [go-sage-plugin-kit](https://github.com/yecllsl/go-sage-plugin-kit)（MCP 引导 + 原子存储）
- [go-sdk](https://github.com/modelcontextprotocol/go-sdk) v1.7.0（MCP 协议）
- [excelize](https://github.com/xuri/excelize) v2.11（Excel 读取）
