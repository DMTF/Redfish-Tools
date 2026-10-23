/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package utils_test

import (
	"testing"

	"github.com/DMTF/redfishRepoTest/src/utils"
	"github.com/stretchr/testify/assert"
)

type parseVersionTest struct {
	Name     string
	Input    string
	Expected *utils.RedfishNamespaceVersion
	ErrorMsg string
}

//nolint:funlen // This is just a list of test cases.
func GetParseTestCases() []parseVersionTest {
	return []parseVersionTest{
		{
			Name:  "v1_0_0",
			Input: "v1_0_0",
			Expected: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  0,
				Errata: 0,
			},
			ErrorMsg: "",
		},
		{
			Name:  "v1_2_3",
			Input: "v1_2_3",
			Expected: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 3,
			},
			ErrorMsg: "",
		},
		{
			Name:  "Edge case, all 0's",
			Input: "v0_0_0",
			Expected: &utils.RedfishNamespaceVersion{
				Major:  0,
				Minor:  0,
				Errata: 0,
			},
			ErrorMsg: "",
		},
		{
			Name:  "Edge case, all 9's",
			Input: "v999_999_999",
			Expected: &utils.RedfishNamespaceVersion{
				Major:  999,
				Minor:  999,
				Errata: 999,
			},
			ErrorMsg: "",
		},
		{
			Name:     "Invalid version - missing underscores",
			Input:    "v123",
			Expected: nil,
			ErrorMsg: "Invalid version: v123",
		},
		{
			Name:     "Invalid version - one underscore",
			Input:    "v1_2",
			Expected: nil,
			ErrorMsg: "Invalid version: v1_2",
		},
		{
			Name:     "Invalid version - too many underscores",
			Input:    "v1_2_3_4",
			Expected: nil,
			ErrorMsg: "Invalid version: v1_2_3_4",
		},
		{
			Name:     "Invalid version - empty string",
			Input:    "",
			Expected: nil,
			ErrorMsg: "Invalid version: ",
		},
		{
			Name:     "Invalide version - non-numeric major",
			Input:    "va_2_3",
			Expected: nil,
			ErrorMsg: "Invalid version: va_2_3",
		},
		{
			Name:     "Invalide version - non-numeric minor",
			Input:    "v1_b_3",
			Expected: nil,
			ErrorMsg: "Invalid version: v1_b_3",
		},
		{
			Name:     "Invalide version - non-numeric errata",
			Input:    "v1_2_c",
			Expected: nil,
			ErrorMsg: "Invalid version: v1_2_c",
		},
	}
}

func TestParseVersionFromString(t *testing.T) {
	t.Parallel()

	for _, tc := range GetParseTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			result, err := utils.ParseVersionFromString(tc.Input)
			if tc.ErrorMsg == "" {
				assert.NoError(t, err)
				assert.Equal(t, tc.Expected, result)
				stringVal := result.String()
				assert.Equal(t, tc.Input, stringVal)
			} else {
				assert.Error(t, err)
				assert.Equal(t, tc.ErrorMsg, err.Error())
				assert.Nil(t, result)
			}
		})
	}
}

//nolint:funlen // This is just a list of test cases.
func TestRedfishNamespaceVersion_Compare(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name     string
		v1       *utils.RedfishNamespaceVersion
		v2       *utils.RedfishNamespaceVersion
		expected int
	}{
		{
			name: "Equal versions",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 3,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 3,
			},
			expected: 0,
		},
		{
			name: "v1 major greater",
			v1: &utils.RedfishNamespaceVersion{
				Major:  2,
				Minor:  1,
				Errata: 1,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  9,
				Errata: 9,
			},
			expected: 1,
		},
		{
			name: "v1 major less",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  9,
				Errata: 9,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  2,
				Minor:  1,
				Errata: 1,
			},
			expected: -1,
		},
		{
			name: "v1 minor greater (major equal)",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  3,
				Errata: 1,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 9,
			},
			expected: 1,
		},
		{
			name: "v1 minor less (major equal)",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 9,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  3,
				Errata: 1,
			},
			expected: -1,
		},
		{
			name: "v1 errata greater (major and minor equal)",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 4,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 3,
			},
			expected: 1,
		},
		{
			name: "v1 errata less (major and minor equal)",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 3,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 4,
			},
			expected: -1,
		},
		{
			name: "Zero versions",
			v1: &utils.RedfishNamespaceVersion{
				Major:  0,
				Minor:  0,
				Errata: 0,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  0,
				Minor:  0,
				Errata: 0,
			},
			expected: 0,
		},
		{
			name: "Large version numbers",
			v1: &utils.RedfishNamespaceVersion{
				Major:  999,
				Minor:  999,
				Errata: 999,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  1,
				Errata: 1,
			},
			expected: 998,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			result := tc.v1.Compare(tc.v2)
			assert.Equal(t, tc.expected, result)
		})
	}
}

//nolint:funlen // This is just a list of test cases.
func TestRedfishNamespaceVersion_IsUpByOneOrEqual(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name     string
		v1       *utils.RedfishNamespaceVersion
		v2       *utils.RedfishNamespaceVersion
		expected bool
	}{
		{
			name: "Equal versions",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 3,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 3,
			},
			expected: true,
		},
		{
			name: "v1 greater by major",
			v1: &utils.RedfishNamespaceVersion{
				Major:  2,
				Minor:  1,
				Errata: 1,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  1,
				Errata: 1,
			},
			expected: true,
		},
		{
			name: "v1 less by major",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  1,
				Errata: 1,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  2,
				Minor:  1,
				Errata: 1,
			},
			expected: false,
		},
		{
			name: "v1 greater by minor",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  3,
				Errata: 1,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 1,
			},
			expected: true,
		},
		{
			name: "v1 less by minor",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 1,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  3,
				Errata: 1,
			},
			expected: false,
		},
		{
			name: "v1 greater by errata",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 4,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 3,
			},
			expected: true,
		},
		{
			name: "v1 less by errata",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 3,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  2,
				Errata: 4,
			},
			expected: false,
		},
		{
			name: "v1 much greater",
			v1: &utils.RedfishNamespaceVersion{
				Major:  5,
				Minor:  0,
				Errata: 0,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  0,
				Errata: 0,
			},
			expected: false,
		},
		{
			name: "v1 much less",
			v1: &utils.RedfishNamespaceVersion{
				Major:  1,
				Minor:  0,
				Errata: 0,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  5,
				Minor:  0,
				Errata: 0,
			},
			expected: false,
		},
		{
			name: "Zero versions equal",
			v1: &utils.RedfishNamespaceVersion{
				Major:  0,
				Minor:  0,
				Errata: 0,
			},
			v2: &utils.RedfishNamespaceVersion{
				Major:  0,
				Minor:  0,
				Errata: 0,
			},
			expected: true,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			result := tc.v1.IsUpByOneOrEqual(tc.v2)
			assert.Equal(t, tc.expected, result)
		})
	}
}

func BenchmarkParseVersionFromString(b *testing.B) {
	for _, tc := range GetParseTestCases() {
		if tc.ErrorMsg != "" {
			// Skip the error cases...
			continue
		}
		b.Run(tc.Name, func(b *testing.B) {
			b.ResetTimer()
			b.ReportAllocs()
			for b.Loop() {
				_, _ = utils.ParseVersionFromString(tc.Input)
			}
		})
	}
}

func BenchmarkRedfishNamespaceVersion_Compare(b *testing.B) {
	v1 := &utils.RedfishNamespaceVersion{Major: 1, Minor: 2, Errata: 3}
	v2 := &utils.RedfishNamespaceVersion{Major: 1, Minor: 2, Errata: 4}
	b.ResetTimer()
	for range b.N {
		_ = v1.Compare(v2)
	}
}

func BenchmarkRedfishNamespaceVersion_IsUpByOneOrEqual(b *testing.B) {
	v1 := &utils.RedfishNamespaceVersion{Major: 1, Minor: 2, Errata: 3}
	v2 := &utils.RedfishNamespaceVersion{Major: 1, Minor: 2, Errata: 2}
	b.ResetTimer()
	for range b.N {
		_ = v1.IsUpByOneOrEqual(v2)
	}
}

func BenchmarkRedfishNamespaceVersion_String(b *testing.B) {
	for _, tc := range GetParseTestCases() {
		if tc.ErrorMsg != "" {
			// Skip the error cases...
			continue
		}
		b.Run(tc.Name, func(b *testing.B) {
			b.ResetTimer()
			b.ReportAllocs()
			for b.Loop() {
				_ = tc.Expected.String()
			}
		})
	}
}
