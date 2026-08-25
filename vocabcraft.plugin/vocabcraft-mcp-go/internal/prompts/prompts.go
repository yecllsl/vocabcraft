package prompts

import (
	_ "embed"
	"strings"
)

//go:embed vocab_parse_multimodal.txt
var vocabParseMultimodal string

//go:embed vocab_parse_text.txt
var vocabParseText string

//go:embed quiz_generate.txt
var quizGenerate string

//go:embed quiz_generate_classical.txt
var quizGenerateClassical string

//go:embed quiz_generate_virtual.txt
var quizGenerateVirtual string

//go:embed quiz_generate_virtual_select.txt
var quizGenerateVirtualSelect string

//go:embed quiz_generate_loan_char.txt
var quizGenerateLoanChar string

//go:embed quiz_grade.txt
var quizGrade string

// Render replaces {placeholder} tokens and unescapes {{ }} to { }.
func Render(tmpl string, vars map[string]string) string {
	result := tmpl
	for k, v := range vars {
		result = strings.ReplaceAll(result, "{"+k+"}", v)
	}
	result = strings.ReplaceAll(result, "{{", "{")
	result = strings.ReplaceAll(result, "}}", "}")
	return result
}

func GetParsePrompt(rawText, language string) string {
	guide := languageGuide(language)
	return Render(vocabParseText, map[string]string{
		"raw_text":         rawText,
		"language":         language,
		"json_schema":      renderJSONSchema(language),
		"parse_requirements": parseRequirements,
		"lang_guide":       guide,
	})
}

func GetMultimodalParsePrompt(language string) string {
	guide := languageGuide(language)
	return Render(vocabParseMultimodal, map[string]string{
		"language":         language,
		"json_schema":      renderJSONSchema(language),
		"parse_requirements": parseRequirements,
		"lang_guide":       guide,
	})
}

func GetQuizGeneratePrompt(word, phonetic, defsBlock, quizType, language string) string {
	return Render(quizGenerate, map[string]string{
		"word":             word,
		"phonetic":         phonetic,
		"definitions_block": defsBlock,
		"quiz_type":        quizType,
		"language":         language,
	})
}

func GetClassicalGeneratePrompt(word, pos, defsBlock string) string {
	return Render(quizGenerateClassical, map[string]string{
		"word":              word,
		"part_of_speech":    pos,
		"definitions_block": defsBlock,
	})
}

func GetVirtualGeneratePrompt(word, defsBlock string) string {
	return Render(quizGenerateVirtual, map[string]string{
		"word":              word,
		"definitions_block": defsBlock,
	})
}

func GetVirtualSelectPrompt(word, defsBlock string) string {
	return Render(quizGenerateVirtualSelect, map[string]string{
		"word":              word,
		"definitions_block": defsBlock,
	})
}

func GetLoanCharGeneratePrompt(word, originalChar, phonetic, defsBlock string) string {
	return Render(quizGenerateLoanChar, map[string]string{
		"word":           word,
		"original_char":  originalChar,
		"phonetic":       phonetic,
		"definitions_block": defsBlock,
	})
}

func GetGradePrompt(question, referenceAnswer, userAnswer string) string {
	return Render(quizGrade, map[string]string{
		"question":        question,
		"reference_answer": referenceAnswer,
		"user_answer":     userAnswer,
	})
}

func languageGuide(lang string) string {
	switch lang {
	case "en":
		return `语言引导（英语）:
  - 词性参考: n./v./adj./adv./prep./conj./int.
  - 例句要求: 优先采用原文例句；若无则按词义构造 1-2 个，必须含中文翻译。`
	case "zh":
		return `语言引导（现代中文）:
  - 词性参考: 名词/动词/形容词/副词/代词/介词/连词/助词/量词
  - 例句要求: 优先采用原文例句；若无则按词义构造 1-2 个现代汉语例句。`
	case "zh_classical":
		return `语言引导（文言文）:
  - word_type（必填，仅文言文）: 实词/虚词/通假字
    * 实词: 名词/动词/形容词/数词/代词
    * 虚词: 之/乎/者/也/矣/焉/以/于/而/则/乃/其/为/若（代词/助词/介词/连词/副词/叹词/动词），
      每个义项即一个用法，该义项的 part_of_speech 填该用法的虚词词性，text 填用法释义
    * 通假字: 必须输出 original_char（本字），phonetic 填本字读音，
      definitions[0].text 填本字释义，part_of_speech 填本义词性。
  - 例句要求: 优先采用原文例句并标注出处；若无则构造含该字的文言短句，附现代汉语译文。
  - **多义词义项分组**: 文言文多义词必须按义项分组例句，每个义项至少 1 个原文例句并标注出处，
    例句挂在该义项 definitions[i].examples 下。`
	case "de":
		return `语言引导（德语）:
  - 词性参考: n.(der/die/das)/v./adj./adv./prep./konj.
    * 名词须标注语法性别: der(阳性)/die(阴性)/das(中性)
    * 动词标注不规则变位或完成时助动词(haben/sein)
  - 复数: 名词若有复数形式，在 phonetic 字段附 "(pl. -e/-er/-n)" 等复数标记
  - 例句要求: 优先采用原文例句；若无则构造 1-2 个德语例句，附中文翻译。`
	default:
		return languageGuide("en")
	}
}

func renderJSONSchema(lang string) string {
	return Render(`{
    "word": "词形（原形/拼写，必填）",
    "phonetic": "音标（如 /wɜːd/，无则空串）",
    "part_of_speech": "词性（见下方语言引导，无则空串）",
    "word_type": "词汇类型（仅文言文填：实词/虚词/通假字，其他语言留默认'实词'）",
    "original_char": "通假字的本字（仅 word_type=通假字 时填写，如"说"→"悦"；其他情况空串）",
    "definitions": [
        {"text": "释义1", "part_of_speech": "名词", "examples": ["例句1（出处）", "例句2（出处）"]},
        {"text": "释义2", "part_of_speech": "动词", "examples": ["例句3（出处）"]}
    ],
    "language": "{language}",
    "source_image": null
}`, map[string]string{"language": lang})
}

const parseRequirements = `解析要求：
1. word 必须从原文中提取最规范的词形；若原文含多个词，取主词
2. definitions 至少 1 条，每条简明扼要；多义词列出主要义项
3. **definitions 为 list[Definition]，每项 {"text": 释义, "part_of_speech": 词性, "examples": [例句]}**：
   - 每条释义的例句必须挂在该释义的 examples 字段下，体现"释义 ↔ 例句"的对应关系
   - 多义词必须按义项分组例句，禁止所有例句堆在某一条释义下
   - 无法确定归属的例句挂到语义最相关的释义下
4. 若原文信息不全（如无音标/词性），对应字段填空串或空列表，禁止填 null
5. 若原文完全无法识别为词汇，返回 word="" 并在 definitions 中说明原因
6. definitions 每项的 part_of_speech 填该义项的词性；多义词各义项词性不同时必须填写（如文言文"兵"：名词/动词）；各义项词性相同时留空串`
