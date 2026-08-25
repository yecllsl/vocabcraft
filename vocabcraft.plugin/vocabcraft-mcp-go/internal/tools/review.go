package tools

import (
	"time"

	"github.com/yecllsl/vocabcraft-mcp-go/internal/store"
)

type Review struct {
	store *store.Store
}

func NewReview(s *store.Store) *Review {
	return &Review{store: s}
}

func (r *Review) ScheduleReview(vocabID, language string) map[string]any {
	today := time.Now().UTC().Format("2006-01-02")

	if vocabID != "" {
		v, err := r.store.LoadVocab(vocabID)
		if err != nil {
			return map[string]any{"error": "词汇不存在: " + vocabID}
		}
		return map[string]any{
			"vocab_id": v.ID,
			"word":     v.Structured.Word,
			"review_state": map[string]any{
				"ease_factor":     v.ReviewState.EaseFactor,
				"interval":        v.ReviewState.Interval,
				"repetitions":     v.ReviewState.Repetitions,
				"next_review":     v.ReviewState.NextReview,
				"last_review":     v.ReviewState.LastReview,
				"last_word_grade": v.ReviewState.LastWordGrade,
			},
			"due_date": v.ReviewState.NextReview,
			"is_due":   v.ReviewState.NextReview != "" && v.ReviewState.NextReview <= today,
		}
	}

	vocabs, err := r.store.AllVocabs()
	if err != nil {
		return map[string]any{"error": err.Error()}
	}

	type dueItem struct {
		VocabID string `json:"vocab_id"`
		Word    string `json:"word"`
		DueDate string `json:"due_date"`
	}
	var due []dueItem
	for _, v := range vocabs {
		if v.ReviewState.NextReview == "" || v.ReviewState.NextReview > today {
			continue
		}
		if language != "" && v.Structured.Language != language {
			continue
		}
		due = append(due, dueItem{
			VocabID: v.ID,
			Word:    v.Structured.Word,
			DueDate: v.ReviewState.NextReview,
		})
	}

	// Sort by due_date, then vocab_id
	for i := 1; i < len(due); i++ {
		for j := i; j > 0; j-- {
			if due[j].DueDate < due[j-1].DueDate ||
				(due[j].DueDate == due[j-1].DueDate && due[j].VocabID < due[j-1].VocabID) {
				due[j], due[j-1] = due[j-1], due[j]
			}
		}
	}

	return map[string]any{
		"today":     today,
		"due_count": len(due),
		"due_words": due,
	}
}
