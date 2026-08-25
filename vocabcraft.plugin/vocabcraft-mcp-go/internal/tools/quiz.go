package tools

import (
	"fmt"
	"math/rand"
	"regexp"
	"strings"
	"time"

	"github.com/yecllsl/vocabcraft-mcp-go/internal/algorithms"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/models"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/prompts"
	"github.com/yecllsl/vocabcraft-mcp-go/internal/store"
)

var (
	objectiveTypes = map[string]bool{"选择": true, "填空": true, "拼写": true}

	posPrefixRe   = regexp.MustCompile(`^【\[(.*?)】\]\s*`)
	loanSenseRe   = regexp.MustCompile(`^同(.)[，,]`)
	phoneticSuffixRe = regexp.MustCompile(`（音[^）]*）$`)
	posSepRe      = regexp.MustCompile(`[/、,，]`)
	meaningSepRe  = regexp.MustCompile(`[，、；;,]`)

	posZhToEn = map[string]string{
		"名词": "n.", "动词": "v.", "形容词": "adj.", "副词": "adv.",
		"代词": "pron.", "数词": "num.", "量词": "量", "连词": "连",
		"介词": "介", "助词": "助", "叹词": "叹",
	}
)

type QuizTool struct {
	store *store.Store
}

func NewQuizTool(s *store.Store) *QuizTool {
	return &QuizTool{store: s}
}

func (qt *QuizTool) GenerateQuiz(vocabID, quizType string) map[string]any {
	v, err := qt.store.LoadVocab(vocabID)
	if err != nil {
		return map[string]any{"error": "词汇不存在: " + vocabID}
	}

	qtype := quizType
	if qtype == "" {
		if strings.HasPrefix(v.Structured.Language, "zh") {
			qtype = "释义"
		} else {
			qtype = "拼写"
		}
	}

	defs := v.Structured.Definitions
	wordType := v.Structured.WordType

	// zh_classical 释义题: per-definition per-example quizzes
	if qtype == "释义" && v.Structured.Language == "zh_classical" {
		return qt.generateClassicalQuizzes(v, defs, wordType, qtype)
	}

	// 虚词 + 选择题
	if qtype == "选择" && v.Structured.Language == "zh_classical" && wordType == "虚词" {
		return qt.generateVirtualSelectQuiz(v, defs, qtype)
	}

	// Non-zh_classical: single quiz
	defIndex := 0
	defsBlock := "（无）"
	if len(defs) > 0 {
		if len(defs) > 1 {
			defIndex = rand.Intn(len(defs))
		}
		selected := defs[defIndex]
		defsBlock = "1. " + selected.Text
		for _, e := range selected.Examples {
			defsBlock += "\n   - " + e
		}
	}

	prompt := prompts.GetQuizGeneratePrompt(
		v.Structured.Word, v.Structured.Phonetic, defsBlock, qtype, v.Structured.Language,
	)

	answer := ""
	if qtype == "拼写" {
		answer = v.Structured.Word
	} else if len(defs) > 0 && defIndex < len(defs) {
		answer = defs[defIndex].Text
	}

	quizID := qt.store.GenerateID("quiz")
	now := time.Now().UTC()
	quiz := &models.Quiz{
		ID:              quizID,
		VocabID:         vocabID,
		QuizType:        qtype,
		Question:        "（占位题干，请用 generate_prompt 调用 LLM 生成真实题干）",
		Answer:          answer,
		GeneratedAt:     now,
		DefinitionIndex: &defIndex,
	}
	qt.store.SaveQuiz(quiz)

	return map[string]any{
		"quiz_id":         quizID,
		"quiz":            quizToMap(quiz),
		"generate_prompt": prompt,
		"message":         "请使用 generate_prompt 调用 LLM 生成题干，结果可回写 quizzes/" + quizID + ".json",
	}
}

func (qt *QuizTool) generateClassicalQuizzes(v *models.VocabRecord, defs []models.Definition, wordType, qtype string) map[string]any {
	if len(defs) == 0 {
		return map[string]any{"error": "词汇无释义，无法生成考题"}
	}
	if wordType == "通假字" && strings.TrimSpace(v.Structured.OriginalChar) == "" {
		return map[string]any{"error": "通假字「" + v.Structured.Word + "」缺少本字 original_char"}
	}

	type quizResult struct {
		QuizID string         `json:"quiz_id"`
		Quiz   map[string]any `json:"quiz"`
		Prompt string         `json:"generate_prompt"`
	}
	var quizzes []quizResult

	for di, d := range defs {
		pos := d.PartOfSpeech
		if pos == "" {
			pos = v.Structured.PartOfSpeech
		}
		pos = zhToEnPos(pos)
		if pos == "" {
			pos = "?"
		}
		meaning := stripPosPrefix(d.Text)
		loanChar := ""
		if wordType != "通假字" {
			loanChar = extractLoanChar(d.Text)
		}
		if loanChar != "" {
			meaning = phoneticSuffixRe.ReplaceAllString(meaning, "")
			if idx := strings.Index(meaning, "，"); idx >= 0 {
				meaning = meaning[idx+1:]
			}
		}

		var answer string
		if loanChar != "" {
			answer = loanChar + "|" + meaning
		} else if wordType == "通假字" {
			answer = v.Structured.OriginalChar + "|" + meaning
		} else {
			answer = pos + "|" + meaning
		}

		diCopy := di
		if len(d.Examples) > 0 {
			for exIdx, example := range d.Examples {
				defsBlock := "1. " + meaning + "\n   - " + example
				prompt := qt.classicalPrompt(v, wordType, defs, di, meaning, defsBlock)
				exIdxCopy := exIdx
				quizID := qt.store.GenerateID("quiz")
				now := time.Now().UTC()
				quiz := &models.Quiz{
					ID:              quizID,
					VocabID:         v.ID,
					QuizType:        qtype,
					Question:        "（占位题干，请用 generate_prompt 调用 LLM 生成真实题干）",
					Answer:          answer,
					GeneratedAt:     now,
					DefinitionIndex: &diCopy,
					ExampleIndex:    &exIdxCopy,
				}
				qt.store.SaveQuiz(quiz)
				quizzes = append(quizzes, quizResult{quizID, quizToMap(quiz), prompt})
			}
		} else {
			defsBlock := "1. " + meaning + "\n   （无例句）"
			prompt := qt.classicalPrompt(v, wordType, defs, di, meaning, defsBlock)
			quizID := qt.store.GenerateID("quiz")
			now := time.Now().UTC()
			quiz := &models.Quiz{
				ID:              quizID,
				VocabID:         v.ID,
				QuizType:        qtype,
				Question:        "（占位题干，请用 generate_prompt 调用 LLM 生成真实题干）",
				Answer:          answer,
				GeneratedAt:     now,
				DefinitionIndex: &diCopy,
			}
			qt.store.SaveQuiz(quiz)
			quizzes = append(quizzes, quizResult{quizID, quizToMap(quiz), prompt})
		}
	}

	return map[string]any{"quizzes": quizzes}
}

func (qt *QuizTool) classicalPrompt(v *models.VocabRecord, wordType string, defs []models.Definition, di int, meaning, defsBlock string) string {
	if wordType == "虚词" {
		return prompts.GetVirtualGeneratePrompt(v.Structured.Word, defsBlock)
	}
	if wordType == "通假字" || extractLoanChar(defs[di].Text) != "" {
		origChar := v.Structured.OriginalChar
		if origChar == "" {
			origChar = extractLoanChar(defs[di].Text)
		}
		return prompts.GetLoanCharGeneratePrompt(v.Structured.Word, origChar, v.Structured.Phonetic, defsBlock)
	}
	return prompts.GetClassicalGeneratePrompt(v.Structured.Word, v.Structured.PartOfSpeech, defsBlock)
}

func (qt *QuizTool) generateVirtualSelectQuiz(v *models.VocabRecord, defs []models.Definition, qtype string) map[string]any {
	if len(defs) == 0 {
		return map[string]any{"error": "词汇无释义，无法生成考题"}
	}
	defsBlock := ""
	for i, d := range defs {
		defsBlock += fmt.Sprintf("%d. %s\n   - %s\n", i+1, stripPosPrefix(d.Text), strings.Join(d.Examples, "\n   - "))
	}
	prompt := prompts.GetVirtualSelectPrompt(v.Structured.Word, defsBlock)
	quizID := qt.store.GenerateID("quiz")
	now := time.Now().UTC()
	quiz := &models.Quiz{
		ID:              quizID,
		VocabID:         v.ID,
		QuizType:        qtype,
		Question:        "（占位题干，请用 generate_prompt 调用 LLM 生成真实题干）",
		Answer:          "",
		GeneratedAt:     now,
		DefinitionIndex: intPtr(0),
	}
	qt.store.SaveQuiz(quiz)
	return map[string]any{
		"quiz_id":         quizID,
		"quiz":            quizToMap(quiz),
		"generate_prompt": prompt,
		"message":         "请使用 generate_prompt 调用 LLM 生成题干与选项，结果可回写 quizzes/" + quizID + ".json",
	}
}

// ──────────────────────────────────────────
// Grade Quiz
// ──────────────────────────────────────────

func (qt *QuizTool) GradeQuiz(quizID, response string) map[string]any {
	quiz, err := qt.store.LoadQuiz(quizID)
	if err != nil {
		return map[string]any{"error": "考题不存在: " + quizID}
	}

	vocab, err := qt.store.LoadVocab(quiz.VocabID)
	if err != nil {
		return map[string]any{"error": "关联词汇不存在: " + quiz.VocabID}
	}

	if strings.TrimSpace(response) == "" {
		return map[string]any{"error": "作答为空，不允许评分", "quiz_id": quizID}
	}

	if objectiveTypes[quiz.QuizType] && strings.TrimSpace(quiz.Answer) == "" {
		return map[string]any{"error": "该考题答案为空（考题为占位题，尚未回写答案）", "quiz_id": quizID}
	}

	result := map[string]any{"quiz_id": quizID, "vocab_id": quiz.VocabID}

	var individualGrade int
	if objectiveTypes[quiz.QuizType] {
		correct := strings.TrimSpace(strings.ToLower(response)) == strings.TrimSpace(strings.ToLower(quiz.Answer))
		if correct {
			individualGrade = 4
		} else {
			individualGrade = 1
		}
		result["correct"] = correct
	} else if quiz.QuizType == "释义" && vocab.Structured.Language == "zh_classical" {
		defs := vocab.Structured.Definitions
		di := 0
		if quiz.DefinitionIndex != nil {
			di = *quiz.DefinitionIndex
		}
		senseText := ""
		if di < len(defs) {
			senseText = defs[di].Text
		}
		if vocab.Structured.WordType == "通假字" || extractLoanChar(senseText) != "" {
			individualGrade = gradeLoanChar(quiz.Answer, response)
		} else {
			individualGrade = gradeDefinition(quiz.Answer, response)
		}
		result["correct"] = individualGrade == 4
	} else {
		result["grade_prompt"] = prompts.GetGradePrompt(quiz.Question, quiz.Answer, response)
		result["correct"] = nil
		individualGrade = 3 // 骨架默认值
	}

	result["individual_grade"] = individualGrade

	// Save graded quiz
	quiz.Graded = true
	quiz.IndividualGrade = &individualGrade
	qt.store.SaveQuiz(quiz)

	// Check if all quizzes for this vocab are graded
	todayStr := time.Now().UTC().Format("2006-01-02")
	allQuizIDs, _ := qt.store.ListQuizIDs()
	var vocabQuizzes []*models.Quiz
	for _, qid := range allQuizIDs {
		q, err := qt.store.LoadQuiz(qid)
		if err != nil || q.VocabID != quiz.VocabID {
			continue
		}
		genDate := q.GeneratedAt.Format("2006-01-02")
		if genDate >= todayStr {
			timeDiff := q.GeneratedAt.Sub(quiz.GeneratedAt)
			if timeDiff < 0 {
				timeDiff = -timeDiff
			}
			if timeDiff <= 60*time.Second {
				vocabQuizzes = append(vocabQuizzes, q)
			}
		}
	}

	var ungraded, graded []*models.Quiz
	for _, q := range vocabQuizzes {
		if q.Graded {
			graded = append(graded, q)
		} else {
			ungraded = append(ungraded, q)
		}
	}

	if len(ungraded) > 0 {
		result["remaining"] = len(ungraded)
		result["message"] = "还有 " + itoa(len(ungraded)) + " 道题未答"
		return result
	}

	// All graded — compute word-level grade
	var defGrades []int
	for _, q := range graded {
		if q.IndividualGrade != nil {
			defGrades = append(defGrades, *q.IndividualGrade)
		}
	}
	wordGrade := compositeWordGrade(defGrades)
	result["word_grade"] = wordGrade

	details := make([]map[string]any, len(graded))
	for i, q := range graded {
		details[i] = map[string]any{
			"quiz_id":          q.ID,
			"definition_index": q.DefinitionIndex,
			"example_index":    q.ExampleIndex,
			"grade":            q.IndividualGrade,
		}
	}
	result["details"] = details

	// SM-2 update
	rs := vocab.ReviewState
	prevEase := rs.EaseFactor
	newState, err := algorithms.ComputeNextReview(prevEase, rs.Interval, rs.Repetitions, wordGrade)
	if err != nil {
		result["error"] = err.Error()
		return result
	}

	reviewState := vocab.ReviewState
	reviewState.EaseFactor = newState.EaseFactor
	reviewState.Interval = newState.Interval
	reviewState.Repetitions = newState.Repetitions
	reviewState.NextReview = newState.NextReviewDate
	today := time.Now().UTC().Format("2006-01-02")
	reviewState.LastReview = &today
	reviewState.LastWordGrade = &wordGrade
	vocab.ReviewState = reviewState
	qt.store.SaveVocab(vocab)

	// Save review record
	recID := qt.store.GenerateID("rec")
	now := time.Now().UTC()
	qt.store.SaveReviewRecord(&models.ReviewRecord{
		RecordID:   recID,
		VocabID:    quiz.VocabID,
		ReviewTime: now,
		Grade:      wordGrade,
		PrevEase:   prevEase,
		NewEase:    newState.EaseFactor,
	})

	result["grade"] = wordGrade
	result["remaining"] = 0
	result["review_record_id"] = recID
	return result
}

// ──────────────────────────────────────────
// Fuzzy matching for zh_classical
// ──────────────────────────────────────────

func gradeDefinition(expected, response string) int {
	expPos, expMeaning, _ := strings.Cut(expected, "|")
	actPos, actMeaning, _ := strings.Cut(response, "|")
	posOK := matchPos(expPos, actPos)
	meaningOK := matchMeaning(expMeaning, actMeaning)
	if posOK && meaningOK {
		return 4
	}
	if posOK {
		return 3
	}
	if meaningOK {
		return 2
	}
	return 1
}

func gradeLoanChar(expected, response string) int {
	expChar, expMeaning, _ := strings.Cut(expected, "|")
	actChar, actMeaning, _ := strings.Cut(response, "|")
	charOK := strings.TrimSpace(strings.ToLower(expChar)) == strings.TrimSpace(strings.ToLower(actChar))
	meaningOK := matchMeaning(expMeaning, actMeaning)
	if charOK && meaningOK {
		return 4
	}
	if charOK {
		return 3
	}
	if meaningOK {
		return 2
	}
	return 1
}

func compositeWordGrade(grades []int) int {
	if len(grades) == 0 {
		return 0
	}
	minG := grades[0]
	sum := 0
	for _, g := range grades {
		sum += g
		if g < minG {
			minG = g
		}
	}
	avg := float64(sum) / float64(len(grades))
	return int(avg*0.8 + float64(minG)*0.2 + 0.5)
}

func matchPos(expected, actual string) bool {
	return posSetEqual(normalizePosSet(expected), normalizePosSet(actual))
}

func posSetEqual(a, b map[string]bool) bool {
	if len(a) != len(b) {
		return false
	}
	for k := range a {
		if !b[k] {
			return false
		}
	}
	return true
}

func normalizePosSet(posStr string) map[string]bool {
	parts := posSepRe.Split(strings.TrimSpace(strings.ToLower(posStr)), -1)
	result := map[string]bool{}
	modifiers := map[string]bool{"使动": true, "意动": true, "为动": true, "被动": true, "主动": true, "及物": true, "不及物": true}
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		en := posZhToEn[p]
		if en == "" {
			en = p
		}
		for mod := range modifiers {
			if strings.HasPrefix(en, mod) {
				en = strings.TrimPrefix(en, mod)
				break
			}
		}
		en = strings.TrimSpace(en)
		if en != "" {
			result[en] = true
		}
	}
	return result
}

func matchMeaning(expected, actual string) bool {
	particles := "也矣乎哉之者"
	rawParts := meaningSepRe.Split(strings.TrimSpace(expected), -1)
	var parts []string
	for _, p := range rawParts {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		// Strip particles
		for _, r := range particles {
			p = strings.TrimRight(p, string(r))
		}
		p = strings.TrimSpace(p)
		if p != "" {
			parts = append(parts, p)
		}
	}
	actualText := strings.TrimSpace(actual)
	if len(parts) == 0 || actualText == "" {
		return false
	}
	noWS := func(s string) string { return strings.ReplaceAll(s, " ", "") }
	actualClean := noWS(actualText)

	if len(parts) > 1 {
		for _, ep := range parts {
			epClean := noWS(ep)
			if strings.Contains(actualClean, epClean) {
				return true
			}
			if strings.Contains(epClean, actualClean) && len(actualClean) >= 2 && len(actualClean) >= len(epClean)/2 {
				return true
			}
		}
		return false
	}

	epClean := noWS(parts[0])
	if strings.Contains(actualClean, epClean) {
		return true
	}
	return strings.Contains(epClean, actualClean) && len(actualClean) >= len(epClean)/2
}

// ──────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────

func stripPosPrefix(text string) string {
	return posPrefixRe.ReplaceAllString(text, "")
}

func extractLoanChar(text string) string {
	m := loanSenseRe.FindStringSubmatch(strings.TrimSpace(text))
	if len(m) > 1 {
		return m[1]
	}
	return ""
}

func zhToEnPos(zh string) string {
	parts := posSepRe.Split(zh, -1)
	var mapped []string
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		if en, ok := posZhToEn[p]; ok {
			mapped = append(mapped, en)
		} else {
			mapped = append(mapped, p)
		}
	}
	return strings.Join(mapped, "/")
}

func quizToMap(q *models.Quiz) map[string]any {
	m := map[string]any{
		"id":           q.ID,
		"vocab_id":     q.VocabID,
		"quiz_type":    q.QuizType,
		"question":     q.Question,
		"answer":       q.Answer,
		"generated_at": q.GeneratedAt.Format(time.RFC3339),
		"graded":       q.Graded,
	}
	if q.Options != nil {
		m["options"] = q.Options
	}
	if q.IndividualGrade != nil {
		m["individual_grade"] = *q.IndividualGrade
	}
	if q.DefinitionIndex != nil {
		m["definition_index"] = *q.DefinitionIndex
	}
	if q.ExampleIndex != nil {
		m["example_index"] = *q.ExampleIndex
	}
	return m
}

func intPtr(i int) *int { return &i }

func itoa(i int) string {
	if i == 0 {
		return "0"
	}
	s := ""
	for i > 0 {
		s = string(rune('0'+i%10)) + s
		i /= 10
	}
	return s
}
