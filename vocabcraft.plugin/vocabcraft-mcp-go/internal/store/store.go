package store

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	kit "github.com/yecllsl/go-sage-plugin-kit/store"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/models"
)

type Store struct {
	kit     *kit.AtomicJSON
	baseDir string
}

func New(baseDir string) (*Store, error) {
	k, err := kit.New(baseDir)
	if err != nil {
		return nil, fmt.Errorf("store: %w", err)
	}
	ensureDirs(baseDir)
	return &Store{kit: k, baseDir: baseDir}, nil
}

func ensureDirs(base string) {
	for _, sub := range []string{"vocabs", "reviews", "quizzes", "images", "exports"} {
		os.MkdirAll(filepath.Join(base, sub), 0o755)
	}
}

// ──────────────────────────────────────────
// Vocab CRUD
// ──────────────────────────────────────────

func (s *Store) SaveVocab(rec *models.VocabRecord) error {
	return s.kit.Write("vocabs/"+rec.ID+".json", rec)
}

func (s *Store) LoadVocab(vocabID string) (*models.VocabRecord, error) {
	var rec models.VocabRecord
	if err := s.kit.Read("vocabs/"+vocabID+".json", &rec); err != nil {
		return nil, err
	}
	return &rec, nil
}

func (s *Store) VocabExists(vocabID string) bool {
	return s.kit.Exists("vocabs/" + vocabID + ".json")
}

func (s *Store) DeleteVocab(vocabID string) bool {
	fp := filepath.Join(s.baseDir, "vocabs", vocabID+".json")
	if err := os.Remove(fp); err != nil {
		return false
	}
	return true
}

func (s *Store) ListVocabIDs() ([]string, error) {
	paths, err := s.kit.List("vocabs/*.json")
	if err != nil {
		return nil, err
	}
	ids := make([]string, len(paths))
	for i, p := range paths {
		ids[i] = strings.TrimSuffix(filepath.Base(p), ".json")
	}
	return ids, nil
}

func (s *Store) AllVocabs() ([]*models.VocabRecord, error) {
	ids, err := s.ListVocabIDs()
	if err != nil {
		return nil, err
	}
	var out []*models.VocabRecord
	for _, id := range ids {
		v, err := s.LoadVocab(id)
		if err != nil {
			continue
		}
		out = append(out, v)
	}
	return out, nil
}

// ──────────────────────────────────────────
// Quiz CRUD
// ──────────────────────────────────────────

func (s *Store) SaveQuiz(quiz *models.Quiz) error {
	return s.kit.Write("quizzes/"+quiz.ID+".json", quiz)
}

func (s *Store) LoadQuiz(quizID string) (*models.Quiz, error) {
	var q models.Quiz
	if err := s.kit.Read("quizzes/"+quizID+".json", &q); err != nil {
		return nil, err
	}
	return &q, nil
}

func (s *Store) ListQuizIDs() ([]string, error) {
	paths, err := s.kit.List("quizzes/*.json")
	if err != nil {
		return nil, err
	}
	ids := make([]string, len(paths))
	for i, p := range paths {
		ids[i] = strings.TrimSuffix(filepath.Base(p), ".json")
	}
	return ids, nil
}

func (s *Store) ListQuizzesForVocab(vocabID string) ([]*models.Quiz, error) {
	ids, err := s.ListQuizIDs()
	if err != nil {
		return nil, err
	}
	var out []*models.Quiz
	for _, id := range ids {
		q, err := s.LoadQuiz(id)
		if err != nil {
			continue
		}
		if q.VocabID == vocabID {
			out = append(out, q)
		}
	}
	return out, nil
}

// ──────────────────────────────────────────
// Review Record CRUD
// ──────────────────────────────────────────

func (s *Store) SaveReviewRecord(rec *models.ReviewRecord) error {
	return s.kit.Write("reviews/"+rec.RecordID+".json", rec)
}

func (s *Store) LoadAllReviewRecords() ([]*models.ReviewRecord, error) {
	paths, err := s.kit.List("reviews/*.json")
	if err != nil {
		return nil, err
	}
	var out []*models.ReviewRecord
	for _, p := range paths {
		b, err := os.ReadFile(filepath.Join(s.baseDir, p))
		if err != nil {
			continue
		}
		var rec models.ReviewRecord
		if json.Unmarshal(b, &rec) == nil {
			out = append(out, &rec)
		}
	}
	return out, nil
}

// ──────────────────────────────────────────
// ID Generation
// ──────────────────────────────────────────

func (s *Store) GenerateID(prefix string) string {
	today := time.Now().UTC().Format("20060102")
	prefix_:= prefix + "_" + today + "_"
	ids, _ := s.kit.List(prefix_ + "*.json")
	maxNNN := 0
	for _, p := range ids {
		base := strings.TrimSuffix(filepath.Base(p), ".json")
		parts := strings.Split(base, "_")
		if len(parts) >= 3 {
			n := 0
			for _, c := range parts[len(parts)-1] {
				if c >= '0' && c <= '9' {
					n = n*10 + int(c-'0')
				}
			}
			if n > maxNNN {
				maxNNN = n
			}
		}
	}
	return fmt.Sprintf("%s%03d", prefix_, maxNNN+1)
}

// ──────────────────────────────────────────
// Query
// ──────────────────────────────────────────

type QueryFilter struct {
	Language  string
	Word      string
	DateStart string
	DateEnd   string
}

func (s *Store) QueryVocabs(f QueryFilter) ([]*models.VocabRecord, error) {
	vocabs, err := s.AllVocabs()
	if err != nil {
		return nil, err
	}
	var result []*models.VocabRecord
	for _, v := range vocabs {
		if f.Language != "" && v.Structured.Language != f.Language {
			continue
		}
		if f.Word != "" && !strings.Contains(v.Structured.Word, f.Word) {
			continue
		}
		created := v.CreatedAt.Format("2006-01-02")
		if f.DateStart != "" && created < f.DateStart {
			continue
		}
		if f.DateEnd != "" && created > f.DateEnd {
			continue
		}
		result = append(result, v)
	}
	// sort by created_at descending
	sortVocabsByTime(result)
	return result, nil
}

func sortVocabsByTime(vocabs []*models.VocabRecord) {
	for i := 1; i < len(vocabs); i++ {
		for j := i; j > 0 && vocabs[j].CreatedAt.After(vocabs[j-1].CreatedAt); j-- {
			vocabs[j], vocabs[j-1] = vocabs[j-1], vocabs[j]
		}
	}
}

// ──────────────────────────────────────────
// Path Validation
// ──────────────────────────────────────────

func (s *Store) ValidateDataPath(child string) (string, error) {
	b, err := filepath.Abs(s.baseDir)
	if err != nil {
		return "", err
	}
	c, err := filepath.Abs(child)
	if err != nil {
		return "", err
	}
	rel, err := filepath.Rel(b, filepath.Dir(c))
	if err != nil || (rel != "." && strings.HasPrefix(rel, "..")) {
		return "", fmt.Errorf("path escapes data dir: %s", child)
	}
	return c, nil
}
