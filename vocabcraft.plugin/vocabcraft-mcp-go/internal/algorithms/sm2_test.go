package algorithms

import (
	"testing"
)

func TestComputeNextReview_Pass(t *testing.T) {
	r, err := ComputeNextReview(2.5, 0, 0, 4)
	if err != nil {
		t.Fatal(err)
	}
	if r.Repetitions != 1 {
		t.Fatalf("expected reps=1, got %d", r.Repetitions)
	}
	if r.Interval != 1 {
		t.Fatalf("expected interval=1, got %d", r.Interval)
	}
	if r.NextReviewDate == "" {
		t.Fatal("expected non-empty next_review_date")
	}
}

func TestComputeNextReview_Fail(t *testing.T) {
	r, err := ComputeNextReview(2.5, 6, 3, 2)
	if err != nil {
		t.Fatal(err)
	}
	if r.Repetitions != 0 {
		t.Fatalf("expected reps=0 on fail, got %d", r.Repetitions)
	}
	if r.Interval != 1 {
		t.Fatalf("expected interval=1 on fail, got %d", r.Interval)
	}
}

func TestComputeNextReview_InvalidGrade(t *testing.T) {
	_, err := ComputeNextReview(2.5, 0, 0, 5)
	if err == nil {
		t.Fatal("expected error for grade=5")
	}
}

func TestGetInitialSchedule(t *testing.T) {
	s := GetInitialSchedule()
	if s.NextReview == "" {
		t.Fatal("expected non-empty next_review")
	}
	if len(s.DueDates) != 5 {
		t.Fatalf("expected 5 due dates, got %d", len(s.DueDates))
	}
	if len(s.IntervalsDays) != 5 {
		t.Fatalf("expected 5 intervals, got %d", len(s.IntervalsDays))
	}
}

func TestEaseFactorLowerBound(t *testing.T) {
	// Fail many times to push EF below min
	ef := 1.4
	for i := 0; i < 10; i++ {
		r, _ := ComputeNextReview(ef, 1, 0, 1)
		ef = r.EaseFactor
	}
	if ef < MinEaseFactor {
		t.Fatalf("EF %f below min %f", ef, MinEaseFactor)
	}
}
