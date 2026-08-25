package tools

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/yecllsl/vocabcraft-mcp-go/internal/store"
)

type Export struct {
	store   *store.Store
	dataDir string
}

func NewExport(s *store.Store, dataDir string) *Export {
	return &Export{store: s, dataDir: dataDir}
}

func (e *Export) ExportData(format string, filters map[string]any) map[string]any {
	if format != "json" && format != "csv" {
		return map[string]any{"error": "不支持的格式: " + format}
	}

	f := store.QueryFilter{}
	if lang, ok := filters["language"].(string); ok {
		f.Language = lang
	}
	if word, ok := filters["word"].(string); ok {
		f.Word = word
	}

	vocabs, err := e.store.QueryVocabs(f)
	if err != nil {
		return map[string]any{"error": err.Error()}
	}

	exportsDir := filepath.Join(e.dataDir, "exports")
	os.MkdirAll(exportsDir, 0o755)
	timestamp := time.Now().UTC().Format("20060102_150405")

	if format == "json" {
		fp := filepath.Join(exportsDir, "vocabs_"+timestamp+".json")
		data := make([]map[string]any, len(vocabs))
		for i, v := range vocabs {
			data[i] = vocabToMap(v)
		}
		b, _ := json.MarshalIndent(data, "", "  ")
		os.WriteFile(fp, b, 0o644)
		return map[string]any{"file_path": fp, "total_exported": len(vocabs)}
	}

	// CSV
	fp := filepath.Join(exportsDir, "vocabs_"+timestamp+".csv")
	f2, err := os.Create(fp)
	if err != nil {
		return map[string]any{"error": err.Error()}
	}
	defer f2.Close()
	// UTF-8 BOM
	f2.Write([]byte{0xEF, 0xBB, 0xBF})

	w := csv.NewWriter(f2)
	defer w.Flush()

	header := []string{"id", "word", "phonetic", "part_of_speech", "definitions", "language", "ease_factor", "interval", "repetitions", "next_review", "created_at", "updated_at"}
	w.Write(header)

	for _, v := range vocabs {
		defTexts := ""
		for i, d := range v.Structured.Definitions {
			if i > 0 {
				defTexts += "; "
			}
			defTexts += d.Text
		}
		row := []string{
			v.ID, v.Structured.Word, v.Structured.Phonetic, v.Structured.PartOfSpeech,
			defTexts, v.Structured.Language,
			fmt.Sprintf("%.2f", v.ReviewState.EaseFactor),
			itoa(v.ReviewState.Interval),
			itoa(v.ReviewState.Repetitions),
			v.ReviewState.NextReview,
			v.CreatedAt.Format(time.RFC3339),
			v.UpdatedAt.Format(time.RFC3339),
		}
		w.Write(row)
	}

	return map[string]any{"file_path": fp, "total_exported": len(vocabs)}
}
