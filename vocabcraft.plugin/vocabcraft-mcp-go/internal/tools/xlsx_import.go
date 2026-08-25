package tools

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/xuri/excelize/v2"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/models"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/store"
)

type XLSXImport struct {
	store   *store.Store
	dataDir string
}

func NewXLSXImport(s *store.Store, dataDir string) *XLSXImport {
	return &XLSXImport{store: s, dataDir: dataDir}
}

func (xi *XLSXImport) ImportXLSX(xlsxPath, sheetName, language string) map[string]any {
	lang := normalizeLanguage(language)

	// Path validation
	resolved, err := filepath.Abs(xlsxPath)
	if err != nil {
		return xi.errResult("路径无效: " + xlsxPath)
	}
	dataRoot, _ := filepath.Abs(xi.dataDir)
	rel, err := filepath.Rel(dataRoot, filepath.Dir(resolved))
	if err != nil || (rel != "." && strings.HasPrefix(rel, "..")) {
		return xi.errResult("路径越界: " + xlsxPath)
	}

	if _, err := os.Stat(resolved); os.IsNotExist(err) {
		return xi.errResult("文件不存在: " + xlsxPath)
	}
	if strings.ToLower(filepath.Ext(resolved)) != ".xlsx" {
		return xi.errResult("文件格式错误: " + xlsxPath + "，请提供 .xlsx 文件")
	}

	f, err := excelize.OpenFile(resolved)
	if err != nil {
		return xi.errResult("读取 Excel 文件失败: " + err.Error())
	}
	defer f.Close()

	sheets := f.GetSheetList()
	if len(sheets) == 0 {
		return xi.errResult("工作簿无工作表")
	}

	sheet := sheets[0]
	if sheetName != "" {
		found := false
		for _, s := range sheets {
			if s == sheetName {
				sheet = s
				found = true
				break
			}
		}
		if !found {
			return xi.errResult("工作表 '" + sheetName + "' 不存在，可用: " + strings.Join(sheets, ", "))
		}
	}

	// Read all rows
	rows, err := f.GetRows(sheet)
	if err != nil {
		return xi.errResult("读取工作表失败: " + err.Error())
	}
	if len(rows) < 2 {
		return xi.errResult("工作表行数不足")
	}

	// Detect format: check if headers contain word/definitions
	headers := make([]string, len(rows[0]))
	for i, cell := range rows[0] {
		headers[i] = strings.TrimSpace(strings.ToLower(cell))
	}

	required := map[string]bool{"word": true, "definitions": true}
	hasRequired := true
	for k := range required {
		found := false
		for _, h := range headers {
			if h == k {
				found = true
				break
			}
		}
		if !found {
			hasRequired = false
			break
		}
	}

	if !hasRequired {
		return xi.errResult("缺少必需列 (word/definitions)")
	}

	// Group by (word, language)
	type rowMap map[string]string
	groups := map[string][]rowMap{}
	var errors []string

	for rowIdx, row := range rows[1:] {
		if len(row) == 0 {
			continue
		}
		rm := rowMap{}
		for i, h := range headers {
			if h == "" || i >= len(row) {
				continue
			}
			rm[h] = strings.TrimSpace(row[i])
		}

		word := rm["word"]
		if word == "" {
			errors = append(errors, fmt.Sprintf("行 %d: 词汇(word)为空", rowIdx+2))
			continue
		}
		defText := rm["definitions"]
		if defText == "" {
			errors = append(errors, fmt.Sprintf("行 %d: 释义(definitions)为空", rowIdx+2))
			continue
		}

		wordLang := lang
		if rl, ok := rm["language"]; ok && rl != "" {
			wordLang = normalizeLanguage(rl)
		}
		key := word + "|" + wordLang
		groups[key] = append(groups[key], rm)
	}

	successCount := 0
	errorCount := 0
	var imported []string

	for key, rows := range groups {
		parts := strings.SplitN(key, "|", 2)
		word, wordLang := parts[0], parts[1]

		phonetic := ""
		pos := ""
		wordType := ""
		originalChar := ""
		var defs []map[string]any

		for _, rm := range rows {
			if phonetic == "" && rm["phonetic"] != "" {
				phonetic = rm["phonetic"]
			}
			if pos == "" && rm["part_of_speech"] != "" {
				pos = rm["part_of_speech"]
			}
			if wordType == "" && rm["word_type"] != "" {
				wordType = rm["word_type"]
			}
			if originalChar == "" && rm["original_char"] != "" {
				originalChar = rm["original_char"]
			}

			defText := rm["definitions"]
			if defText == "" {
				continue
			}
			var examples []string
			examplesRaw := rm["examples"]
			if examplesRaw != "" {
				examplesRaw = strings.ReplaceAll(examplesRaw, "；", "\n")
				examplesRaw = strings.ReplaceAll(examplesRaw, ";", "\n")
				for _, e := range strings.Split(examplesRaw, "\n") {
					e = strings.TrimSpace(e)
					if e != "" {
						examples = append(examples, e)
					}
				}
			}
			defs = append(defs, map[string]any{
				"text":     defText,
				"examples": examples,
			})
		}

		if wordType != "" && !models.ValidWordTypes[wordType] {
			errorCount++
			errors = append(errors, fmt.Sprintf("词汇 '%s' 的词汇类型非法: %s", word, wordType))
			continue
		}

		structured := map[string]any{
			"word":         word,
			"phonetic":     phonetic,
			"part_of_speech": pos,
			"definitions":  defs,
			"language":     wordLang,
		}
		if wordType != "" {
			structured["word_type"] = wordType
		}
		if originalChar != "" {
			structured["original_char"] = originalChar
		}

		crud := NewCRUD(xi.store)
		result := crud.SaveVocab(map[string]any{"structured": structured})
		if errMsg, ok := result["error"].(string); ok {
			errorCount++
			errors = append(errors, fmt.Sprintf("词汇 '%s' 保存失败: %s", word, errMsg))
		} else {
			successCount++
			if vid, ok := result["vocab_id"].(string); ok {
				imported = append(imported, vid)
			}
		}
	}

	return map[string]any{
		"success_count":   successCount,
		"error_count":     errorCount,
		"errors":          errors,
		"imported_vocabs": imported,
	}
}

func (xi *XLSXImport) errResult(msg string) map[string]any {
	return map[string]any{
		"success_count":   0,
		"error_count":     0,
		"errors":          []string{msg},
		"imported_vocabs": []string{},
	}
}
