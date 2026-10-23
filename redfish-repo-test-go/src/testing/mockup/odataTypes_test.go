/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup_test

import (
	"testing"
	"time"

	"github.com/DMTF/redfishRepoTest/src/testing/mockup"
	"github.com/stretchr/testify/assert"
)

type EdmDateTimeOffsetTestCase struct {
	Name     string
	Input    string
	Expected time.Time
	Error    error
}

type EdmDurationTestCase struct {
	Name     string
	Input    string
	Expected time.Duration
	Error    error
}

type EdmGUIDTestCase struct {
	Name  string
	Input string
	Error error
}

func getNewEdmDateTimeOffsetTestCases() []EdmDateTimeOffsetTestCase {
	return []EdmDateTimeOffsetTestCase{
		{Name: "2024-01-02T03:04", Input: "2024-01-02T03:04", Expected: time.Date(2024, 1, 2, 3, 4, 0, 0, time.UTC)},
		{Name: "2024-01-02T03:04:05", Input: "2024-01-02T03:04:05", Expected: time.Date(2024, 1, 2, 3, 4, 5, 0, time.UTC)},
		{Name: "2024-01-02T03:04:05Z", Input: "2024-01-02T03:04:05Z", Expected: time.Date(2024, 1, 2, 3, 4, 5, 0, time.UTC)},
		{Name: "2024-01-02T03:04-07:00", Input: "2024-01-02T03:04-07:00", Expected: time.Date(2024, 1, 2, 3, 4, 0, 0, time.FixedZone("", -25200))},
		{Name: "2024-01-02T03:04:05-06:00", Input: "2024-01-02T03:04:05-06:30", Expected: time.Date(2024, 1, 2, 3, 4, 5, 0, time.FixedZone("", -23400))},
		{Name: "2024-01-02T03:04:05.123456789-07:00", Input: "2024-01-02T03:04:05.123456789-07:00", Expected: time.Date(2024, 1, 2, 3, 4, 5, 123456789, time.FixedZone("", -25200))},
		{Name: "empty", Input: "", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "invalid", Input: "invalid", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "no time", Input: "2024-01-02", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "invalid month", Input: "2024-13-02T03:04", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "invalid data", Input: "2024-01-02T03:60", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "invalid seconds format", Input: "2024-01-02T03:04:XX", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "invalid zulu suffix", Input: "2024-01-02T03:04:05X", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "invalid timezone hour", Input: "2024-01-02T03:04-25:00", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "invalid timezone minute", Input: "2024-01-02T03:04:05-06:99", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "no timezone", Input: "2024-01-02T03:04:05.123", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "fractional with zulu", Input: "2024-01-02T03:04:05.123Z", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "invalid fractional", Input: "2024-01-02T03:04:05.bad-07:00", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
		{Name: "invalid timezone", Input: "2024-01-02T03:04:05+0700", Expected: time.Time{}, Error: mockup.ErrInvalidDateTimeOffset},
	}
}

func TestNewEdmDateTimeOffset(t *testing.T) {
	t.Parallel()
	for _, tc := range getNewEdmDateTimeOffsetTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			result, err := mockup.NewEdmDateTimeOffset(tc.Input)
			if tc.Error != nil {
				assert.ErrorIs(t, err, tc.Error)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tc.Expected, time.Time(result))
			}
		})
	}
}

func BenchmarkNewEdmDateTimeOffset(b *testing.B) {
	testCases := getNewEdmDateTimeOffsetTestCases()
	b.ResetTimer()
	for _, tc := range testCases {
		b.Run(tc.Name, func(b *testing.B) {
			b.ReportAllocs()
			for b.Loop() {
				_, _ = mockup.NewEdmDateTimeOffset(tc.Input)
			}
		})
	}
}

func getNewEdmDurationTestCases() []EdmDurationTestCase {
	return []EdmDurationTestCase{
		{Name: "days", Input: "P2D", Expected: 48 * time.Hour},
		{Name: "hours_minutes_seconds", Input: "PT2H30M15S", Expected: 2*time.Hour + 30*time.Minute + 15*time.Second},
		{Name: "day_time", Input: "P1DT2H", Expected: 26 * time.Hour},
		{Name: "fractional_seconds_truncated", Input: "PT1.5S", Expected: time.Second},
		{Name: "empty", Input: "", Error: mockup.ErrInvalidDuration},
		{Name: "missing_prefix", Input: "1D", Error: mockup.ErrInvalidDuration},
		{Name: "invalid_designator", Input: "PX", Error: mockup.ErrInvalidDuration},
		{Name: "invalid_day_value", Input: "PXD", Error: mockup.ErrInvalidDuration},
		{Name: "missing_time_prefix_after_day", Input: "P1DX", Error: mockup.ErrInvalidDuration},
		{Name: "invalid_time_designator", Input: "PT1Q", Error: mockup.ErrInvalidDuration},
		{Name: "invalid_day_time_format", Input: "P1DTXH", Error: mockup.ErrInvalidDuration},
		{Name: "invalid_minute_value", Input: "PT1HXM", Error: mockup.ErrInvalidDuration},
		{Name: "invalid_second_value", Input: "PT1H2MXS", Error: mockup.ErrInvalidDuration},
		{Name: "trailing_garbage", Input: "PT1H2M3Sfoo", Error: mockup.ErrInvalidDuration},
	}
}

func TestNewEdmDuration(t *testing.T) {
	t.Parallel()
	for _, tc := range getNewEdmDurationTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			result, err := mockup.NewEdmDuration(tc.Input)
			if tc.Error != nil {
				assert.ErrorIs(t, err, tc.Error)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, mockup.EdmDuration(tc.Expected), result)
			}
		})
	}
}

func BenchmarkNewEdmDuration(b *testing.B) {
	testCases := getNewEdmDurationTestCases()
	b.ResetTimer()
	for _, tc := range testCases {
		b.Run(tc.Name, func(b *testing.B) {
			b.ReportAllocs()
			for b.Loop() {
				_, _ = mockup.NewEdmDuration(tc.Input)
			}
		})
	}
}

func getNewEdmGUIDTestCases() []EdmGUIDTestCase {
	return []EdmGUIDTestCase{
		{Name: "valid_lowercase", Input: "12345678-1234-1234-1234-1234567890ab"},
		{Name: "valid_uppercase", Input: "ABCDEF12-ABCD-ABCD-ABCD-ABCDEF123456"},
		{Name: "empty", Input: "", Error: mockup.ErrInvalidGUID},
		{Name: "empty_first_segment", Input: "-1234-1234-1234-1234567890ab", Error: mockup.ErrInvalidGUID},
		{Name: "short_first_segment", Input: "1234567-1234-1234-1234-1234567890ab", Error: mockup.ErrInvalidGUID},
		{Name: "invalid_first_segment_char", Input: "1234567_-1234-1234-1234-1234567890ab", Error: mockup.ErrInvalidGUID},
		{Name: "empty_second_segment", Input: "12345678--1234-1234-1234567890ab", Error: mockup.ErrInvalidGUID},
		{Name: "short_second_segment", Input: "12345678-123-1234-1234-1234567890ab", Error: mockup.ErrInvalidGUID},
		{Name: "invalid_second_segment_char", Input: "12345678-12_4-1234-1234-1234567890ab", Error: mockup.ErrInvalidGUID},
		{Name: "empty_third_segment", Input: "12345678-1234--1234-1234567890ab", Error: mockup.ErrInvalidGUID},
		{Name: "invalid_third_segment_char", Input: "12345678-1234-12_4-1234-1234567890ab", Error: mockup.ErrInvalidGUID},
		{Name: "empty_fourth_segment", Input: "12345678-1234-1234--1234567890ab", Error: mockup.ErrInvalidGUID},
		{Name: "invalid_fourth_segment_char", Input: "12345678-1234-1234-12_4-1234567890ab", Error: mockup.ErrInvalidGUID},
		{Name: "empty_fifth_segment", Input: "12345678-1234-1234-1234-", Error: mockup.ErrInvalidGUID},
		{Name: "short_fifth_segment", Input: "12345678-1234-1234-1234-1234567890a", Error: mockup.ErrInvalidGUID},
		{Name: "invalid_fifth_segment_char", Input: "12345678-1234-1234-1234-1234567890a_", Error: mockup.ErrInvalidGUID},
		{Name: "invalid_separator", Input: "12345678_1234-1234-1234-1234567890ab", Error: mockup.ErrInvalidGUID},
		{Name: "trailing_data", Input: "12345678-1234-1234-1234-1234567890ab-extra", Error: mockup.ErrInvalidGUID},
	}
}

func TestNewEdmGUID(t *testing.T) {
	t.Parallel()
	for _, tc := range getNewEdmGUIDTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			_, err := mockup.NewEdmGUID(tc.Input)
			if tc.Error != nil {
				assert.ErrorIs(t, err, tc.Error)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func BenchmarkNewEdmGUID(b *testing.B) {
	testCases := getNewEdmGUIDTestCases()
	b.ResetTimer()
	for _, tc := range testCases {
		b.Run(tc.Name, func(b *testing.B) {
			b.ReportAllocs()
			for b.Loop() {
				_, _ = mockup.NewEdmGUID(tc.Input)
			}
		})
	}
}

func TestAlphaNumLen(t *testing.T) {
	t.Parallel()

	cases := []struct {
		name     string
		input    string
		length   int
		expected bool
	}{
		{name: "letters_numbers", input: "A1b2", length: 4, expected: true},
		{name: "wrong_length", input: "A1b2", length: 3, expected: false},
		{name: "contains_symbol", input: "A1-b", length: 4, expected: false},
		{name: "empty", input: "", length: 0, expected: true},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			assert.Equal(t, tc.expected, mockup.AlphaNumLen(tc.input, tc.length))
		})
	}
}
