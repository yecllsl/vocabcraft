package tools

import (
	"fmt"
	"time"

	"github.com/yecllsl/vocabcraft-mcp-go/internal/models"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/store"
)

type Statistics struct {
	store *store.Store
}

func NewStatistics(s *store.Store) *Statistics {
	return &Statistics{store: s}
}

func (st *Statistics) GetStatistics(groupBy string) map[string]any {
	valid := map[string]bool{"language": true, "mastery": true, "date": true, "quiz_type": true}
	if !valid[groupBy] {
		return map[string]any{"error": fmt.Sprintf("不支持的分组维度: %s", groupBy)}
	}

	vocabs, err := st.store.AllVocabs()
	if err != nil {
		return map[string]any{"error": err.Error()}
	}

	type kv struct {
		Key   string `json:"key"`
		Count int    `json:"count"`
	}

	counter := map[string]int{}
	var total int

	if groupBy == "quiz_type" {
		quizIDs, _ := st.store.ListQuizIDs()
		for _, qid := range quizIDs {
			q, err := st.store.LoadQuiz(qid)
			if err != nil {
				continue
			}
			counter[q.QuizType]++
			total++
		}
	} else {
		for _, v := range vocabs {
			var key string
			switch groupBy {
			case "language":
				key = v.Structured.Language
			case "mastery":
				key = masteryLevel(v.ReviewState.LastWordGrade)
			case "date":
				key = v.CreatedAt.Format("2006-01-02")
			}
			counter[key]++
			total++
		}
	}

	items := make([]kv, 0, len(counter))
	for k, c := range counter {
		items = append(items, kv{Key: k, Count: c})
	}
	// Sort by key
	for i := 1; i < len(items); i++ {
		for j := i; j > 0 && items[j].Key < items[j-1].Key; j-- {
			items[j], items[j-1] = items[j-1], items[j]
		}
	}

	// 30-day trends
	today := time.Now().UTC()
	type trend struct {
		Date  string `json:"date"`
		Count int    `json:"count"`
	}
	trends := make([]trend, 30)
	for i := 29; i >= 0; i-- {
		day := today.AddDate(0, 0, -i).Format("2006-01-02")
		count := 0
		for _, v := range vocabs {
			if v.CreatedAt.Format("2006-01-02") == day {
				count++
			}
		}
		trends[29-i] = trend{Date: day, Count: count}
	}

	return map[string]any{
		"group_by": groupBy,
		"items":    items,
		"total":    total,
		"trends":   trends,
	}
}

func masteryLevel(grade *int) string {
	if grade == nil || *grade <= 1 {
		return "新词"
	}
	switch *grade {
	case 2:
		return "生疏"
	case 3:
		return "熟悉"
	case 4:
		return "掌握"
	}
	return "新词"
}

// AllVocabRecords returns all vocabs as maps (for web/export use)
func (st *Statistics) AllVocabRecords() ([]*models.VocabRecord, error) {
	return st.store.AllVocabs()
}
