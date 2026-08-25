package models

import "time"

type Definition struct {
	Text         string   `json:"text"`
	Examples     []string `json:"examples"`
	PartOfSpeech string   `json:"part_of_speech"`
}

type StructuredVocab struct {
	Word           string       `json:"word"`
	Phonetic       string       `json:"phonetic"`
	PartOfSpeech   string       `json:"part_of_speech"`
	Definitions    []Definition `json:"definitions"`
	Language       string       `json:"language"`
	SourceImage    *string      `json:"source_image"`
	WordType       string       `json:"word_type"`
	OriginalChar   string       `json:"original_char"`
}

type ReviewState struct {
	EaseFactor    float64 `json:"ease_factor"`
	Interval      int     `json:"interval"`
	Repetitions   int     `json:"repetitions"`
	NextReview    string  `json:"next_review"`
	LastReview    *string `json:"last_review"`
	LastWordGrade *int    `json:"last_word_grade"`
}

type VocabRecord struct {
	ID          string         `json:"id"`
	Structured  StructuredVocab `json:"structured"`
	ReviewState ReviewState    `json:"review_state"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"updated_at"`
}

type Quiz struct {
	ID              string    `json:"id"`
	VocabID         string    `json:"vocab_id"`
	QuizType        string    `json:"quiz_type"`
	Question        string    `json:"question"`
	Options         []string  `json:"options"`
	Answer          string    `json:"answer"`
	GeneratedAt     time.Time `json:"generated_at"`
	Graded          bool      `json:"graded"`
	IndividualGrade *int      `json:"individual_grade"`
	DefinitionIndex *int      `json:"definition_index"`
	ExampleIndex    *int      `json:"example_index"`
}

type ReviewRecord struct {
	RecordID        string    `json:"record_id"`
	VocabID         string    `json:"vocab_id"`
	ReviewTime      time.Time `json:"review_time"`
	Grade           int       `json:"grade"`
	PrevEase        float64   `json:"prev_ease"`
	NewEase         float64   `json:"new_ease"`
	DefinitionIndex *int      `json:"definition_index"`
	ExampleIndex    *int      `json:"example_index"`
}

type ReviewSchedule struct {
	VocabID string `json:"vocab_id"`
	DueDate string `json:"due_date"`
	Status  string `json:"status"`
	QuizID  string `json:"quiz_id"`
}

var ValidQuizTypes = map[string]bool{
	"选择": true, "填空": true, "拼写": true, "释义": true,
}

var ValidScheduleStatus = map[string]bool{
	"待复习": true, "已完成": true, "已跳过": true,
}

var ValidWordTypes = map[string]bool{
	"实词": true, "虚词": true, "通假字": true,
}

var SupportedLanguages = map[string]bool{
	"en": true, "zh": true, "zh_classical": true, "de": true,
}
