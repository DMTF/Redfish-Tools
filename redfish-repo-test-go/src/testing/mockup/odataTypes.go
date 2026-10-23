/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup

import (
	"errors"
	"strconv"
	"strings"
	"time"
)

const EdmDateTimeOffsetFormat = "2006-01-02T15:04" // This is the minimum format allowed by the spec

// Named constants for datetime offset size increments.
const (
	dtOffsetSecLen     = 3
	dtOffsetSecZuluLen = 4
	dtOffsetTZLen      = 6
	dtOffsetSecTZLen   = 9
)

// Named constants for GUID segment lengths.
const (
	guidFirstSegLen  = 8
	guidMiddleSegLen = 4
	guidLastSegLen   = 12
)

type EdmDateTimeOffset time.Time
type EdmDuration time.Duration
type EdmGUID string

var ErrInvalidDateTimeOffset = errors.New("invalid datetime offset")
var ErrInvalidDuration = errors.New("invalid duration")
var ErrInvalidGUID = errors.New("invalid guid")

//nolint:cyclop
func NewEdmDateTimeOffset(str string) (EdmDateTimeOffset, error) {
	// String format is YYYY-MM-DDTHH:MM[:SS[.mmm][Z|(+/-)HH:MM]]
	switch len(str) {
	case len(EdmDateTimeOffsetFormat):
		// Basic format with just date and time
		t, err := time.Parse(EdmDateTimeOffsetFormat, str)
		if err != nil {
			return EdmDateTimeOffset{}, ErrInvalidDateTimeOffset
		}
		return EdmDateTimeOffset(t.UTC()), nil
	case len(EdmDateTimeOffsetFormat) + dtOffsetSecLen:
		// Format with seconds...
		t, err := time.Parse(EdmDateTimeOffsetFormat+":05", str)
		if err != nil {
			return EdmDateTimeOffset{}, ErrInvalidDateTimeOffset
		}
		return EdmDateTimeOffset(t.UTC()), nil
	case len(EdmDateTimeOffsetFormat) + dtOffsetSecZuluLen:
		// Format with seconds and Zulu...
		t, err := time.Parse(EdmDateTimeOffsetFormat+":05Z", str)
		if err != nil {
			return EdmDateTimeOffset{}, ErrInvalidDateTimeOffset
		}
		return EdmDateTimeOffset(t), nil
	case len(EdmDateTimeOffsetFormat) + dtOffsetTZLen:
		// Format with no seconds but timezone...
		t, err := time.Parse(EdmDateTimeOffsetFormat+"-07:00", str)
		if err != nil {
			return EdmDateTimeOffset{}, ErrInvalidDateTimeOffset
		}
		return EdmDateTimeOffset(t), nil
	case len(EdmDateTimeOffsetFormat) + dtOffsetSecTZLen:
		// Format with seconds and timezone...
		t, err := time.Parse(EdmDateTimeOffsetFormat+":05-07:00", str)
		if err != nil {
			return EdmDateTimeOffset{}, ErrInvalidDateTimeOffset
		}
		return EdmDateTimeOffset(t), nil
	default:
		if strings.Contains(str, ".") {
			// Try full with fractional seconds
			t, err := time.Parse("2006-01-02T15:04:05.999999999-07:00", str)
			if err != nil {
				return EdmDateTimeOffset{}, ErrInvalidDateTimeOffset
			}
			return EdmDateTimeOffset(t), nil
		}
		return EdmDateTimeOffset{}, ErrInvalidDateTimeOffset
	}
}

//nolint:cyclop
func NewEdmDuration(str string) (EdmDuration, error) {
	if str == "" {
		return EdmDuration(0), ErrInvalidDuration
	}
	if str[0] != 'P' {
		return EdmDuration(0), ErrInvalidDuration
	}
	str = str[1:]
	days := 0
	hours := 0
	minutes := 0
	seconds := 0.00
	var tmpStr string
	var err error
	if strings.Contains(str, "D") {
		tmpStr, str, _ = strings.Cut(str, "D")
		days, err = strconv.Atoi(tmpStr)
		if err != nil {
			return EdmDuration(0), ErrInvalidDuration
		}
	}
	//nolint:nestif
	if str != "" {
		if str[0] != 'T' {
			return EdmDuration(0), ErrInvalidDuration
		}
		str = str[1:]
		if strings.Contains(str, "H") {
			tmpStr, str, _ = strings.Cut(str, "H")
			hours, err = strconv.Atoi(tmpStr)
			if err != nil {
				return EdmDuration(0), ErrInvalidDuration
			}
		}
		if strings.Contains(str, "M") {
			tmpStr, str, _ = strings.Cut(str, "M")
			minutes, err = strconv.Atoi(tmpStr)
			if err != nil {
				return EdmDuration(0), ErrInvalidDuration
			}
		}
		if strings.Contains(str, "S") {
			tmpStr, str, _ = strings.Cut(str, "S")
			seconds, err = strconv.ParseFloat(tmpStr, 64)
			if err != nil {
				return EdmDuration(0), ErrInvalidDuration
			}
		}
	}
	if str != "" {
		return EdmDuration(0), ErrInvalidDuration
	}
	dur := time.Duration(days)*24*time.Hour +
		time.Duration(hours)*time.Hour +
		time.Duration(minutes)*time.Minute +
		time.Duration(seconds)*time.Second
	return EdmDuration(dur), nil
}

//nolint:cyclop
func NewEdmGUID(str string) (EdmGUID, error) {
	if str == "" {
		return EdmGUID(""), ErrInvalidGUID
	}
	first, str, _ := strings.Cut(str, "-")
	if first == "" {
		return EdmGUID(""), ErrInvalidGUID
	}
	if !AlphaNumLen(first, guidFirstSegLen) {
		return EdmGUID(""), ErrInvalidGUID
	}
	second, str, _ := strings.Cut(str, "-")
	if second == "" {
		return EdmGUID(""), ErrInvalidGUID
	}
	if !AlphaNumLen(second, guidMiddleSegLen) {
		return EdmGUID(""), ErrInvalidGUID
	}
	third, str, _ := strings.Cut(str, "-")
	if third == "" {
		return EdmGUID(""), ErrInvalidGUID
	}
	if !AlphaNumLen(third, guidMiddleSegLen) {
		return EdmGUID(""), ErrInvalidGUID
	}
	fourth, str, _ := strings.Cut(str, "-")
	if fourth == "" {
		return EdmGUID(""), ErrInvalidGUID
	}
	if !AlphaNumLen(fourth, guidMiddleSegLen) {
		return EdmGUID(""), ErrInvalidGUID
	}
	fifth, str, _ := strings.Cut(str, "-")
	if fifth == "" {
		return EdmGUID(""), ErrInvalidGUID
	}
	if !AlphaNumLen(fifth, guidLastSegLen) {
		return EdmGUID(""), ErrInvalidGUID
	}
	if str != "" {
		return EdmGUID(""), ErrInvalidGUID
	}
	return EdmGUID(str), nil
}

func AlphaNumLen(str string, length int) bool {
	if len(str) != length {
		return false
	}
	for _, c := range str {
		if (c < '0' || c > '9') &&
			(c < 'A' || c > 'Z') &&
			(c < 'a' || c > 'z') {
			return false
		}
	}
	return true
}
