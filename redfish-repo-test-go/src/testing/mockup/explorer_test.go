/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup_test

import (
	"bytes"
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/mockup"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type explorerTestCase struct {
	Name           string
	MockupName     string
	Config         *config.Config
	ExplorerConfig map[string]any
	Files          map[string]map[string]any
	ExpectedStatus testsuite.Status
	ExpectedErrors int
	ExpectedOutput string
}

//nolint:funlen
func getExplorerTestCases() []explorerTestCase {
	return []explorerTestCase{
		{
			Name:       "Allowed Missing Explorer",
			MockupName: "allowed-mockup",
			Config: &config.Config{
				AllowLists: config.AllowLists{AllowedNoExplorerMockups: []string{"allowed-mockup"}},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Missing Explorer Config",
			MockupName:     "mockup",
			Config:         &config.Config{},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 0,
			ExpectedOutput: "Explorer config not found",
		},
		{
			Name:       "Missing Name Field",
			MockupName: "mockup",
			Config:     &config.Config{},
			ExplorerConfig: map[string]any{
				"description": "desc",
				"navlinks":    []any{},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 0,
			ExpectedOutput: "Explorer config name field is missing or not a string",
		},
		{
			Name:       "Missing Description Field",
			MockupName: "mockup",
			Config:     &config.Config{},
			ExplorerConfig: map[string]any{
				"name":     "name",
				"navlinks": []any{},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 0,
			ExpectedOutput: "Explorer config description field is missing or not a string",
		},
		{
			Name:       "Missing Navlinks Field",
			MockupName: "mockup",
			Config:     &config.Config{},
			ExplorerConfig: map[string]any{
				"name":        "name",
				"description": "desc",
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 0,
			ExpectedOutput: "Explorer config navlinks field is missing or not an array",
		},
		{
			Name:       "Invalid Navlinks Entry",
			MockupName: "mockup",
			Config:     &config.Config{},
			ExplorerConfig: map[string]any{
				"name":        "name",
				"description": "desc",
				"navlinks":    []any{"bad-entry"},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 0,
			ExpectedOutput: "Path  has invalid navlinks",
		},
		{
			Name:       "Invalid Navlink Target Type",
			MockupName: "mockup",
			Config:     &config.Config{},
			ExplorerConfig: map[string]any{
				"name":        "name",
				"description": "desc",
				"navlinks": []any{
					map[string]any{"target": true},
				},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 0,
			ExpectedOutput: "Path  has invalid navlinks target",
		},
		{
			Name:       "Invalid Navlink Target Path",
			MockupName: "mockup",
			Config:     &config.Config{},
			ExplorerConfig: map[string]any{
				"name":        "name",
				"description": "desc",
				"navlinks": []any{
					map[string]any{"target": "Systems/DoesNotExist"},
				},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 0,
			ExpectedOutput: "Path  has invalid navlinks target Systems/DoesNotExist",
		},
		{
			Name:       "Valid With Main Default And Recursive Link",
			MockupName: "mockup",
			Config:     &config.Config{},
			ExplorerConfig: map[string]any{
				"name":        "name",
				"description": "desc",
				"navlinks": []any{
					map[string]any{"target": "main"},
					map[string]any{"target": "default"},
					map[string]any{
						"target": "Systems/1",
						"navlinks": []any{
							map[string]any{"target": "Processors/1"},
						},
					},
				},
			},
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1":              {},
				"/redfish/v1/Systems/1/Processors/1": {},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
	}
}

func TestExplorerTest(t *testing.T) {
	t.Parallel()

	for _, tc := range getExplorerTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			m := mockup.NewMockup(filepath.Join(t.TempDir(), tc.MockupName), tc.Config)
			if tc.ExplorerConfig != nil {
				m.InjectFile("/redfish/v1/explorer_config.json", nil, tc.ExplorerConfig)
			}
			for path, content := range tc.Files {
				m.InjectFile(path, nil, content)
			}

			out := &bytes.Buffer{}
			tPrime := testsuite.NewTesting("Test", out)
			m.ExplorerTest(tPrime)

			assert.Equal(t, tc.ExpectedStatus, tPrime.Status)
			require.Len(t, tPrime.Errors, tc.ExpectedErrors)
			if tc.ExpectedOutput != "" {
				assert.Contains(t, out.String(), tc.ExpectedOutput)
			}
		})
	}
}
