package algorithms

import (
	"fmt"
	"time"
)

const (
	MinEaseFactor   = 1.3
	DefaultEaseFactor = 2.5
)

var InitialIntervalsDays = []int{1, 2, 4, 7, 15}

type ReviewResult struct {
	EaseFactor    float64
	Interval      int
	Repetitions   int
	NextReviewDate string
}

func ComputeNextReview(easeFactor float64, interval, repetitions, grade int) (*ReviewResult, error) {
	if grade < 1 || grade > 4 {
		return nil, fmt.Errorf("grade must be 1-4, got %d", grade)
	}

	var newReps, newInterval int
	if grade < 3 {
		newReps = 0
		newInterval = 1
	} else {
		newReps = repetitions + 1
		switch repetitions {
		case 0:
			newInterval = 1
		case 1:
			newInterval = 6
		default:
			newInterval = int(float64(interval)*easeFactor + 0.5)
		}
	}

	newEase := easeFactor + (0.1 - float64(5-grade)*(0.08+float64(5-grade)*0.02))
	if newEase < MinEaseFactor {
		newEase = MinEaseFactor
	}

	nextDate := time.Now().UTC().AddDate(0, 0, newInterval).Format("2006-01-02")

	return &ReviewResult{
		EaseFactor:     newEase,
		Interval:       newInterval,
		Repetitions:    newReps,
		NextReviewDate: nextDate,
	}, nil
}

type InitialSchedule struct {
	IntervalsDays []int
	DueDates      []string
	NextReview    string
}

func GetInitialSchedule(today ...time.Time) *InitialSchedule {
	base := time.Now().UTC()
	if len(today) > 0 {
		base = today[0]
	}
	dueDates := make([]string, len(InitialIntervalsDays))
	for i, d := range InitialIntervalsDays {
		dueDates[i] = base.AddDate(0, 0, d).Format("2006-01-02")
	}
	return &InitialSchedule{
		IntervalsDays: InitialIntervalsDays,
		DueDates:      dueDates,
		NextReview:    dueDates[0],
	}
}
