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

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/mockup"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type fileTypesAreValidTestCase struct {
	Name           string
	MockupName     string
	Files          map[string]map[string]any
	TypeMap        map[string]*csdl.Type
	ExpectedStatus testsuite.Status
	ExpectedErrors int
}

//nolint:funlen
func getFileTypesAreValidTestCases() []fileTypesAreValidTestCase {
	validTypeMap := map[string]*csdl.Type{
		"Test.Type": {},
	}

	return []fileTypesAreValidTestCase{
		{
			Name:       "Valid OData Type",
			MockupName: "test-mockup",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1": {
					"@odata.type": "Test.Type",
				},
			},
			TypeMap:        validTypeMap,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:       "Valid OData Type With Hash Prefix",
			MockupName: "test-mockup",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1": {
					"@odata.type": "#Test.Type",
				},
			},
			TypeMap:        validTypeMap,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:       "Missing OData Type",
			MockupName: "test-mockup",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1": {
					"Name": "System1",
				},
			},
			TypeMap:        validTypeMap,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:       "Error Response Skips Type Check",
			MockupName: "test-mockup",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1": {
					"error": map[string]any{"code": "Base.GeneralError"},
				},
			},
			TypeMap:        validTypeMap,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:       "Invalid OData Type",
			MockupName: "test-mockup",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1": {
					"@odata.type": "Unknown.Type",
				},
			},
			TypeMap:        validTypeMap,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:       "Excluded Path Is Ignored",
			MockupName: "test-mockup",
			Files: map[string]map[string]any{
				"/redfish/v1/Contoso/BadExample": {
					"Name": "NoTypeNeeded",
				},
			},
			TypeMap:        validTypeMap,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:       "Non Resource Examples Are Skipped",
			MockupName: "non-resource-examples",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1": {
					"Name": "NoTypeNeeded",
				},
			},
			TypeMap:        validTypeMap,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
	}
}

func TestFileTypesAreValid(t *testing.T) {
	t.Parallel()

	for _, tc := range getFileTypesAreValidTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			tPrime := testsuite.NewTesting("Test", &bytes.Buffer{})
			tPrime.Attr("typeMap", tc.TypeMap)
			tPrime.Attr("searcher", &csdl.Searcher{})

			m := mockup.NewMockup(filepath.Join(t.TempDir(), tc.MockupName), &config.Config{})
			for path, content := range tc.Files {
				m.InjectFile(path, nil, content)
			}

			m.FileTypesAreValid(tPrime)

			assert.Equal(t, tc.ExpectedStatus, tPrime.Status)
			require.Len(t, tPrime.Errors, tc.ExpectedErrors)
		})
	}

	t.Run("NoTypeMap", func(t *testing.T) {
		t.Parallel()

		m := mockup.NewMockup(filepath.Join(t.TempDir(), "test-mockup"), &config.Config{})
		m.InjectFile("/redfish/v1/Systems/1", nil, map[string]any{"Name": "System1"})

		testCase := testsuite.NewCase("Test", m.FileTypesAreValid, nil)
		testCase.Run()

		assert.Equal(t, testsuite.Failure, testCase.Status)
	})

	t.Run("NoSearcher", func(t *testing.T) {
		t.Parallel()

		m := mockup.NewMockup(filepath.Join(t.TempDir(), "test-mockup"), &config.Config{})
		m.InjectFile("/redfish/v1/Systems/1", nil, map[string]any{"Name": "System1"})

		suite := &testsuite.Suite{}
		suite.AddAttribute("typeMap", map[string]*csdl.Type{})

		testCase := testsuite.NewCase("Test", m.FileTypesAreValid, suite)
		testCase.Run()

		assert.Equal(t, testsuite.Failure, testCase.Status)
	})
}
