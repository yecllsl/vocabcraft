package tools

import (
	"github.com/yecllsl/vocabcraft-mcp-go/internal/prompts"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/store"
)

type ParseVocab struct {
	store *store.Store
}

func NewParseVocab(s *store.Store) *ParseVocab {
	return &ParseVocab{store: s}
}

func (p *ParseVocab) ParseVocab(imagePath, text, language string) map[string]any {
	lang := normalizeLanguage(language)

	if imagePath == "" && text == "" {
		return map[string]any{
			"structured_vocab": nil,
			"language":         lang,
			"parse_prompt":     prompts.GetMultimodalParsePrompt(lang),
			"image_path":       "",
			"mode":             "dialog",
			"message":          "请使用 parse_prompt 读取对话中的图片完成解析，结果填入 structured_vocab",
		}
	}

	if imagePath != "" {
		resolved, err := p.store.ValidateDataPath(imagePath)
		if err != nil {
			return map[string]any{
				"structured_vocab": nil,
				"language":         lang,
				"image_path":       imagePath,
				"error":            "路径越界: " + imagePath + "，仅允许读取项目 data/ 目录内的图片",
			}
		}
		_ = resolved
		return map[string]any{
			"structured_vocab": nil,
			"language":         lang,
			"parse_prompt":     prompts.GetMultimodalParsePrompt(lang),
			"image_path":       imagePath,
			"mode":             "multimodal",
			"message":          "请使用 parse_prompt 读取指定路径图片完成解析，结果填入 structured_vocab",
		}
	}

	return map[string]any{
		"structured_vocab": nil,
		"language":         lang,
		"parse_prompt":     prompts.GetParsePrompt(text, lang),
		"image_path":       "",
		"mode":             "text",
		"message":          "请使用 parse_prompt 完成解析，结果填入 structured_vocab",
	}
}

func normalizeLanguage(v string) string {
	if v == "" {
		return "en"
	}
	aliases := map[string]string{
		"en": "en", "eng": "en", "english": "en", "英语": "en", "英文": "en",
		"zh": "zh", "zhs": "zh", "chinese": "zh", "中文": "zh", "汉语": "zh", "现代汉语": "zh",
		"zh_classical": "zh_classical", "classical_chinese": "zh_classical",
		"文言": "zh_classical", "文言文": "zh_classical", "古汉语": "zh_classical", "lzh": "zh_classical",
		"de": "de", "deu": "de", "german": "de", "deutsch": "de", "德语": "de", "德文": "de",
	}
	if canonical, ok := aliases[v]; ok {
		return canonical
	}
	return v
}
