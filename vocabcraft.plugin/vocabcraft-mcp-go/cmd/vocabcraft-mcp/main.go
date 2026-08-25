package main

import (
	"context"
	"log"
	"os"
	"path/filepath"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	kit "github.com/yecllsl/go-sage-plugin-kit/server"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/store"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/tools"
)

func main() {
	log.SetFlags(0)
	log.SetOutput(os.Stderr)

	// Data dir: vocabcraft-mcp/data relative to the exe
	exe, _ := os.Executable()
	dataDir := filepath.Join(filepath.Dir(exe), "..", "data")
	if envData := os.Getenv("VOCABCRAFT_DATA_DIR"); envData != "" {
		dataDir = envData
	}
	dataDir, _ = filepath.Abs(dataDir)

	s, err := store.New(dataDir)
	if err != nil {
		log.Fatal("store init failed:", err)
	}

	crud := tools.NewCRUD(s)
	review := tools.NewReview(s)
	quizTool := tools.NewQuizTool(s)
	stats := tools.NewStatistics(s)
	exportTool := tools.NewExport(s, dataDir)
	parseTool := tools.NewParseVocab(s)
	xlsxTool := tools.NewXLSXImport(s, dataDir)

	srv := kit.New(kit.Config{
		Name:         "vocabcraft-mcp",
		Version:      "0.8.0",
		Instructions: "词汇学习与制作MCP Server",
	})

	// CRUD tools
	kit.AddTool(srv, &mcp.Tool{
		Name:        "save_vocab",
		Description: "保存词汇记录到本地 JSON 文件",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input struct {
		VocabData map[string]any `json:"vocab_data"`
	}) (*mcp.CallToolResult, any, error) {
		return nil, crud.SaveVocab(input.VocabData), nil
	})

	kit.AddTool(srv, &mcp.Tool{
		Name:        "query_vocab",
		Description: "按条件查询词汇",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input struct {
		Filters map[string]any `json:"filters"`
	}) (*mcp.CallToolResult, any, error) {
		return nil, crud.QueryVocab(input.Filters), nil
	})

	kit.AddTool(srv, &mcp.Tool{
		Name:        "update_vocab",
		Description: "更新词汇记录",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input struct {
		VocabData map[string]any `json:"vocab_data"`
	}) (*mcp.CallToolResult, any, error) {
		return nil, crud.UpdateVocab(input.VocabData), nil
	})

	kit.AddTool(srv, &mcp.Tool{
		Name:        "delete_vocab",
		Description: "删除词汇记录",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input struct {
		VocabID string `json:"vocab_id"`
	}) (*mcp.CallToolResult, any, error) {
		return nil, crud.DeleteVocab(input.VocabID), nil
	})

	// Business tools
	kit.AddTool(srv, &mcp.Tool{
		Name:        "parse_vocab",
		Description: "AI 结构化解析词汇（词形/音标/词性/释义/例句）。三模式优先级：对话多模态（无参数）> 本地路径多模态（image_path）> 文本模式（text）。",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input struct {
		ImagePath string `json:"image_path"`
		Text      string `json:"text"`
		Language  string `json:"language"`
	}) (*mcp.CallToolResult, any, error) {
		return nil, parseTool.ParseVocab(input.ImagePath, input.Text, input.Language), nil
	})

	kit.AddTool(srv, &mcp.Tool{
		Name:        "schedule_review",
		Description: "基于遗忘曲线生成复习计划（language 为空则不按语种过滤）",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input struct {
		VocabID  string `json:"vocab_id"`
		Language string `json:"language"`
	}) (*mcp.CallToolResult, any, error) {
		return nil, review.ScheduleReview(input.VocabID, input.Language), nil
	})

	kit.AddTool(srv, &mcp.Tool{
		Name:        "generate_quiz",
		Description: "为指定词汇生成考题（选择/填空/拼写/释义/文言文释义）",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input struct {
		VocabID  string `json:"vocab_id"`
		QuizType string `json:"quiz_type"`
	}) (*mcp.CallToolResult, any, error) {
		return nil, quizTool.GenerateQuiz(input.VocabID, input.QuizType), nil
	})

	kit.AddTool(srv, &mcp.Tool{
		Name:        "grade_quiz",
		Description: "评分并按 SM-2 更新词汇记忆状态",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input struct {
		QuizID   string `json:"quiz_id"`
		Response string `json:"response"`
	}) (*mcp.CallToolResult, any, error) {
		return nil, quizTool.GradeQuiz(input.QuizID, input.Response), nil
	})

	kit.AddTool(srv, &mcp.Tool{
		Name:        "get_statistics",
		Description: "统计词汇量、掌握度、题型分布",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input struct {
		GroupBy string `json:"group_by"`
	}) (*mcp.CallToolResult, any, error) {
		return nil, stats.GetStatistics(input.GroupBy), nil
	})

	kit.AddTool(srv, &mcp.Tool{
		Name:        "export_data",
		Description: "导出词汇数据为 JSON/CSV",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input struct {
		Format  string         `json:"format"`
		Filters map[string]any `json:"filters"`
	}) (*mcp.CallToolResult, any, error) {
		return nil, exportTool.ExportData(input.Format, input.Filters), nil
	})

	kit.AddTool(srv, &mcp.Tool{
		Name:        "import_xlsx_vocab",
		Description: "从 .xlsx 文件批量导入词汇",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input struct {
		XLSXPath   string `json:"xlsx_path"`
		SheetName  string `json:"sheet_name"`
		Language   string `json:"language"`
	}) (*mcp.CallToolResult, any, error) {
		return nil, xlsxTool.ImportXLSX(input.XLSXPath, input.SheetName, input.Language), nil
	})

	if err := srv.Run(context.Background()); err != nil {
		log.Fatal(err)
	}
}
