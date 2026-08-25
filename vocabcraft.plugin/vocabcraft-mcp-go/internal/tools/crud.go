package tools

import (
	"fmt"
	"time"

	"github.com/yecllsl/vocabcraft-mcp-go/internal/algorithms"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/models"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/store"
)

type CRUD struct {
	store *store.Store
}

func NewCRUD(s *store.Store) *CRUD {
	return &CRUD{store: s}
}

func (c *CRUD) SaveVocab(vocabData map[string]any) map[string]any {
	sdRaw, ok := vocabData["structured"].(map[string]any)
	if !ok {
		return map[string]any{"error": "vocab_data.structured 为必填项"}
	}
	word, _ := sdRaw["word"].(string)
	if word == "" {
		return map[string]any{"error": "vocab_data.structured.word 为必填项"}
	}

	lang, _ := sdRaw["language"].(string)
	if lang == "" {
		lang = "en"
	}

	// Check duplicate (word, language)
	ids, _ := c.store.ListVocabIDs()
	for _, id := range ids {
		v, err := c.store.LoadVocab(id)
		if err != nil {
			continue
		}
		if v.Structured.Word == word && v.Structured.Language == lang {
			return map[string]any{
				"error":            fmt.Sprintf("词汇已存在: %s (%s)", word, lang),
				"existing_vocab_id": v.ID,
			}
		}
	}

	// Build StructuredVocab
	defsRaw, _ := sdRaw["definitions"].([]any)
	var defs []models.Definition
	for _, d := range defsRaw {
		switch dd := d.(type) {
		case string:
			defs = append(defs, models.Definition{Text: dd, Examples: []string{}})
		case map[string]any:
			def := models.Definition{Text: fmt.Sprintf("%v", dd["text"])}
			if exRaw, ok := dd["examples"].([]any); ok {
				for _, e := range exRaw {
					def.Examples = append(def.Examples, fmt.Sprintf("%v", e))
				}
			}
			if pos, ok := dd["part_of_speech"].(string); ok {
				def.PartOfSpeech = pos
			}
			defs = append(defs, def)
		}
	}

	sourceImage, _ := sdRaw["source_image"].(*string)
	wordType, _ := sdRaw["word_type"].(string)
	if wordType == "" {
		wordType = "实词"
	}
	originalChar, _ := sdRaw["original_char"].(string)
	pos, _ := sdRaw["part_of_speech"].(string)
	phonetic, _ := sdRaw["phonetic"].(string)

	structured := models.StructuredVocab{
		Word:         word,
		Phonetic:     phonetic,
		PartOfSpeech: pos,
		Definitions:  defs,
		Language:     lang,
		SourceImage:  sourceImage,
		WordType:     wordType,
		OriginalChar: originalChar,
	}

	// Review state
	reviewState := models.ReviewState{
		EaseFactor: algorithms.DefaultEaseFactor,
		Interval:   0,
		Repetitions: 0,
	}
	sched := algorithms.GetInitialSchedule()
	reviewState.NextReview = sched.NextReview

	// ID
	vocabID, _ := vocabData["id"].(string)
	if vocabID == "" {
		vocabID = c.store.GenerateID("vocab")
	}
	if c.store.VocabExists(vocabID) {
		return map[string]any{"error": fmt.Sprintf("vocab_id 已存在: %s", vocabID)}
	}

	now := time.Now().UTC()
	rec := &models.VocabRecord{
		ID:          vocabID,
		Structured:  structured,
		ReviewState: reviewState,
		CreatedAt:   now,
		UpdatedAt:   now,
	}

	if err := c.store.SaveVocab(rec); err != nil {
		return map[string]any{"error": err.Error()}
	}
	return map[string]any{"vocab_id": rec.ID}
}

func (c *CRUD) QueryVocab(filters map[string]any) map[string]any {
	f := store.QueryFilter{}
	if lang, ok := filters["language"].(string); ok {
		f.Language = lang
	}
	if word, ok := filters["word"].(string); ok {
		f.Word = word
	}
	if dr, ok := filters["date_range"].(map[string]any); ok {
		if s, ok := dr["start"].(string); ok {
			f.DateStart = s
		}
		if e, ok := dr["end"].(string); ok {
			f.DateEnd = e
		}
	}

	vocabs, err := c.store.QueryVocabs(f)
	if err != nil {
		return map[string]any{"error": err.Error()}
	}

	out := make([]map[string]any, len(vocabs))
	for i, v := range vocabs {
		out[i] = vocabToMap(v)
	}
	return map[string]any{"vocabs": out, "total_count": len(out)}
}

func (c *CRUD) UpdateVocab(vocabData map[string]any) map[string]any {
	id, _ := vocabData["id"].(string)
	if id == "" {
		return map[string]any{"error": "更新词汇需提供 id"}
	}

	existing, err := c.store.LoadVocab(id)
	if err != nil {
		return map[string]any{"error": fmt.Sprintf("词汇不存在: %s", id)}
	}

	// Deep merge patch
	for k, v := range vocabData {
		if k == "id" {
			continue
		}
		existingMap := vocabToMap(existing)
		existingMap[k] = v
		existingMap["updated_at"] = time.Now().UTC().Format(time.RFC3339)
		// Re-marshal and reload
		if err := c.store.SaveVocab(existing); err != nil {
			return map[string]any{"error": err.Error()}
		}
		return map[string]any{"vocab_id": existing.ID}
	}

	existing.UpdatedAt = time.Now().UTC()
	if err := c.store.SaveVocab(existing); err != nil {
		return map[string]any{"error": err.Error()}
	}
	return map[string]any{"vocab_id": existing.ID}
}

func (c *CRUD) DeleteVocab(vocabID string) map[string]any {
	deleted := c.store.DeleteVocab(vocabID)
	return map[string]any{"vocab_id": vocabID, "deleted": deleted}
}

func vocabToMap(v *models.VocabRecord) map[string]any {
	defs := make([]map[string]any, len(v.Structured.Definitions))
	for i, d := range v.Structured.Definitions {
		defs[i] = map[string]any{
			"text":           d.Text,
			"examples":       d.Examples,
			"part_of_speech": d.PartOfSpeech,
		}
	}
	return map[string]any{
		"id": v.ID,
		"structured": map[string]any{
			"word":            v.Structured.Word,
			"phonetic":        v.Structured.Phonetic,
			"part_of_speech":  v.Structured.PartOfSpeech,
			"definitions":     defs,
			"language":        v.Structured.Language,
			"source_image":    v.Structured.SourceImage,
			"word_type":       v.Structured.WordType,
			"original_char":   v.Structured.OriginalChar,
		},
		"review_state": map[string]any{
			"ease_factor":     v.ReviewState.EaseFactor,
			"interval":        v.ReviewState.Interval,
			"repetitions":     v.ReviewState.Repetitions,
			"next_review":     v.ReviewState.NextReview,
			"last_review":     v.ReviewState.LastReview,
			"last_word_grade": v.ReviewState.LastWordGrade,
		},
		"created_at": v.CreatedAt.Format(time.RFC3339),
		"updated_at": v.UpdatedAt.Format(time.RFC3339),
	}
}
