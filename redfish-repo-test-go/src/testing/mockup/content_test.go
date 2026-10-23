/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup_test

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/mockup"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type contentMatchesTypeTestCase struct {
	Name           string
	MockupName     string
	Files          map[string]map[string]any
	ExpectedStatus testsuite.Status
	ExpectedErrors int
}

//nolint:funlen
func getContentMatchesTypeTestCases() []contentMatchesTypeTestCase {
	return []contentMatchesTypeTestCase{
		{
			Name: "Skips Files Without Type",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1": {
					"@odata.type": "Test.Type",
					"@odata.id":   "/redfish/v1/Systems/1",
				},
				// Excluded from type-check, so Type remains nil and should be skipped by ContentMatchesType.
				"/redfish/v1/Contoso/ignored.json": {
					"Name": "ignored",
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Reports Invalid ODataID",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1": {
					"@odata.type": "Test.Type",
					"@odata.id":   "/redfish/v1/Systems/2",
				},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name: "Reports Missing ODataID On Disallowed Path",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1": {
					"@odata.type": "Test.Type",
				},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name: "Reports Missing Navigation Link Target When Internally Consistent",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1": {
					"@odata.type": "Test.NavType",
					"@odata.id":   "/redfish/v1/Systems/1",
					"RelatedItem": map[string]any{
						"@odata.id": "/redfish/v1/Systems/999",
					},
				},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:       "Allows Missing Navigation Link Target When Not Internally Consistent",
			MockupName: "DSP2046-examples",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/1": {
					"@odata.type": "Test.NavType",
					"@odata.id":   "/redfish/v1/Systems/1",
					"RelatedItem": map[string]any{
						"@odata.id": "/redfish/v1/Systems/999",
					},
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Allows Missing ODataID For Registries Path",
			Files: map[string]map[string]any{
				"/redfish/v1/Registries/MyRegistry": {
					"@odata.type": "Test.Type",
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Allows Missing ODataID For AttributeRegistry Example",
			Files: map[string]map[string]any{
				"/redfish/v1/AttributeRegistry-v1-example.json": {
					"@odata.type": "Test.Type",
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Allows Missing ODataID For MessageRegistry Example",
			Files: map[string]map[string]any{
				"/redfish/v1/MessageRegistry-v1-example.json": {
					"@odata.type": "Test.Type",
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
	}
}

type oDataContextSaneTestCase struct {
	Name           string
	Path           string
	ContextValue   any
	ExpectedStatus testsuite.Status
	ExpectedErrors int
}

func getODataContextSaneTestCases() []oDataContextSaneTestCase {
	return []oDataContextSaneTestCase{
		{
			Name:           "Allows Missing ODataContext",
			Path:           "/redfish/v1/Systems/1",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows Matching ODataContext",
			Path:           "/redfish/v1/Systems/1",
			ContextValue:   "/redfish/v1/$metadata#Test.Type",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports Mismatched ODataContext",
			Path:           "/redfish/v1/Systems/1",
			ContextValue:   "/redfish/v1/$metadata#Test.OtherType",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Invalid ODataContext At ODataEndpoint",
			Path:           "/redfish/v1/odata",
			ContextValue:   "/redfish/v1/$metadata#Test.Type",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Two Errors For Wrong ODataEndpointContext",
			Path:           "/redfish/v1/odata",
			ContextValue:   "/redfish/v1/$metadata#Test.OtherType",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 2,
		},
	}
}

func TestODataContextSane(t *testing.T) {
	t.Parallel()

	m := mockup.NewMockup(filepath.Join(t.TempDir(), "test-mockup"), &config.Config{})
	fileType := &csdl.Type{Namespace: "Test.v1_0_0", Name: "Type"}

	for _, tc := range getODataContextSaneTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			content := map[string]any{}
			if tc.ContextValue != nil {
				content["@odata.context"] = tc.ContextValue
			}
			f := &mockup.File{Content: content, Type: fileType}

			tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
			f.ODataContextSane(tPrime, tc.Path, m)

			assert.Equal(t, tc.ExpectedStatus, tPrime.Status)
			require.Len(t, tPrime.Errors, tc.ExpectedErrors)
		})
	}
}

type oDataEtagSaneTestCase struct {
	Name           string
	EtagValue      any
	ExpectedStatus testsuite.Status
	ExpectedErrors int
}

func getODataEtagSaneTestCases() []oDataEtagSaneTestCase {
	return []oDataEtagSaneTestCase{
		{
			Name:           "Allows Missing ODataEtag",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows Valid Strong ODataEtag",
			EtagValue:      `"etag-value"`,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows Valid Weak ODataEtag",
			EtagValue:      `W/"etag-value"`,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports NonString ODataEtag",
			EtagValue:      42.0,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Invalid ODataEtag Format",
			EtagValue:      "etag-value",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
	}
}

func TestODataEtagSane(t *testing.T) {
	t.Parallel()

	m := mockup.NewMockup(filepath.Join(t.TempDir(), "test-mockup"), &config.Config{})
	path := "/redfish/v1/Systems/1"

	for _, tc := range getODataEtagSaneTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			content := map[string]any{}
			if tc.EtagValue != nil {
				content["@odata.etag"] = tc.EtagValue
			}
			f := &mockup.File{Content: content}

			tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
			f.ODataEtagSane(tPrime, path, m)

			assert.Equal(t, tc.ExpectedStatus, tPrime.Status)
			require.Len(t, tPrime.Errors, tc.ExpectedErrors)
		})
	}
}

type membersODataCountCheckTestCase struct {
	Name           string
	TypeName       string
	Content        map[string]any
	ExpectedStatus testsuite.Status
	ExpectedErrors int
}

//nolint:funlen
func getMembersODataCountCheckTestCases() []membersODataCountCheckTestCase {
	return []membersODataCountCheckTestCase{
		{
			Name:     "Reports MembersCount For NonCollection Type",
			TypeName: "System",
			Content: map[string]any{
				"Members@odata.count": 1.0,
				"Members":             []any{map[string]any{"@odata.id": "/redfish/v1/Systems/1"}},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:     "Reports NonNumeric MembersCount",
			TypeName: "SystemCollection",
			Content: map[string]any{
				"Members@odata.count": "1",
				"Members":             []any{map[string]any{"@odata.id": "/redfish/v1/Systems/1"}},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:     "Allows Matching MembersCount",
			TypeName: "SystemCollection",
			Content: map[string]any{
				"Members@odata.count": 2.0,
				"Members": []any{
					map[string]any{"@odata.id": "/redfish/v1/Systems/1"},
					map[string]any{"@odata.id": "/redfish/v1/Systems/2"},
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:     "Reports Mismatched MembersCount Without NextLink",
			TypeName: "SystemCollection",
			Content: map[string]any{
				"Members@odata.count": 3.0,
				"Members": []any{
					map[string]any{"@odata.id": "/redfish/v1/Systems/1"},
				},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:     "Allows Mismatched MembersCount With ODataNextLink",
			TypeName: "SystemCollection",
			Content: map[string]any{
				"Members@odata.count": 3.0,
				"Members": []any{
					map[string]any{"@odata.id": "/redfish/v1/Systems/1"},
				},
				"@odata.nextLink": "/redfish/v1/Systems?$skip=1",
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:     "Allows Mismatched MembersCount With MembersODataNextLink",
			TypeName: "SystemCollection",
			Content: map[string]any{
				"Members@odata.count": 3.0,
				"Members": []any{
					map[string]any{"@odata.id": "/redfish/v1/Systems/1"},
				},
				"Members@odata.nextLink": "/redfish/v1/Systems?$skip=1",
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
	}
}

func TestMembersODataCountCheck(t *testing.T) {
	t.Parallel()

	m := mockup.NewMockup(filepath.Join(t.TempDir(), "test-mockup"), &config.Config{})
	path := "/redfish/v1/Systems"

	for _, tc := range getMembersODataCountCheckTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			f := &mockup.File{
				Content: tc.Content,
				Type: &csdl.Type{
					Namespace: "Test.v1_0_0",
					Name:      tc.TypeName,
				},
			}

			tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
			f.MembersODataCountCheck(tPrime, path, m)

			assert.Equal(t, tc.ExpectedStatus, tPrime.Status)
			require.Len(t, tPrime.Errors, tc.ExpectedErrors)
		})
	}
}

func TestMembersODataCountCheckAutoFix(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name          string
		count         any
		members       any
		expectedValue float64
	}{
		{name: "FixesStringCountWithMembers", count: "2", members: []any{
			map[string]any{"@odata.id": "/redfish/v1/Systems/1"},
			map[string]any{"@odata.id": "/redfish/v1/Systems/2"}}, expectedValue: 2.0},
		{name: "FixesBoolCountWithNoMembers", count: true, members: nil, expectedValue: 0.0},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			f, m, _, realPath := newMembersODataCountAutoFixFixture(t, tc.count, tc.members, "")
			tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
			tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}
			f.MembersODataCountCheck(tPrime, "/redfish/v1/Systems", m)

			assert.Equal(t, testsuite.Success, tPrime.Status)
			assert.Empty(t, tPrime.Errors)
			assert.InDelta(t, tc.expectedValue, f.Content["Members@odata.count"], 0.0)

			data, err := os.ReadFile(realPath) //nolint:gosec // test-only read of temp path
			require.NoError(t, err)
			assert.Contains(t, string(data), fmt.Sprintf(`"Members@odata.count": %d`, int(tc.expectedValue)))
		})
	}
}

// TestMembersODataCountCheckAutoFixMismatched covers the autofix path where
// Members@odata.count is numeric but does not match the Members array length.
func TestMembersODataCountCheckAutoFixMismatched(t *testing.T) {
	t.Parallel()

	t.Run("FixesCountWithoutNextLink", func(t *testing.T) {
		t.Parallel()

		members := []any{map[string]any{"@odata.id": "/redfish/v1/Systems/1"}}
		f, m, _, realPath := newMembersODataCountAutoFixFixture(t, 5.0, members, "")
		tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
		tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}
		f.MembersODataCountCheck(tPrime, "/redfish/v1/Systems", m)

		assert.Equal(t, testsuite.Success, tPrime.Status)
		assert.Empty(t, tPrime.Errors)
		assert.InDelta(t, 1.0, f.Content["Members@odata.count"], 0.0)

		data, err := os.ReadFile(realPath) //nolint:gosec // test-only read of temp path
		require.NoError(t, err)
		assert.Contains(t, string(data), `"Members@odata.count": 1`)
	})

	t.Run("DoesNotFixWhenNextLinkPresent", func(t *testing.T) {
		t.Parallel()

		members := []any{map[string]any{"@odata.id": "/redfish/v1/Systems/1"}}
		f, m, _, realPath := newMembersODataCountAutoFixFixture(t, 5.0, members,
			"/redfish/v1/Systems?$skip=1")
		tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
		tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}
		f.MembersODataCountCheck(tPrime, "/redfish/v1/Systems", m)

		assert.Equal(t, testsuite.Success, tPrime.Status)
		assert.Empty(t, tPrime.Errors)
		assert.InDelta(t, 5.0, f.Content["Members@odata.count"], 0.0)
		assert.NoFileExists(t, realPath)
	})

	t.Run("DoesNotFixWhenMembersNextLinkPresent", func(t *testing.T) {
		t.Parallel()

		members := []any{map[string]any{"@odata.id": "/redfish/v1/Systems/1"}}
		f, m, _, _ := newMembersODataCountAutoFixFixture(t, 5.0, members,
			"/redfish/v1/Systems?$skip=1")
		f.Content["Members@odata.nextLink"] = "/redfish/v1/Systems?$skip=1"
		tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
		tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}
		f.MembersODataCountCheck(tPrime, "/redfish/v1/Systems", m)

		assert.Equal(t, testsuite.Success, tPrime.Status)
		assert.Empty(t, tPrime.Errors)
		assert.InDelta(t, 5.0, f.Content["Members@odata.count"], 0.0)
	})
}

// newMembersODataCountAutoFixFixture creates a mockup, File, and target path
// for the MembersODataCountCheck autofix tests.
func newMembersODataCountAutoFixFixture(
	t *testing.T, count any, members any, nextLink string,
) (*mockup.File, *mockup.Mockup, string, string) {
	t.Helper()

	dir := t.TempDir()
	m := mockup.NewMockup(dir, &config.Config{})
	path := "/redfish/v1/Systems"
	realPath := m.GetRealPath(path)
	require.NoError(t, os.MkdirAll(filepath.Dir(realPath), 0o755)) //nolint:gosec

	content := map[string]any{
		"@odata.type":         "Test.SystemCollection",
		"Members@odata.count": count,
	}
	if members != nil {
		content["Members"] = members
	}
	if nextLink != "" {
		content["@odata.nextLink"] = nextLink
	}
	f := &mockup.File{
		Content: content,
		Type: &csdl.Type{
			Namespace: "Test.v1_0_0",
			Name:      "SystemCollection",
		},
	}
	return f, m, path, realPath
}

type oDataNextLinkCheckTestCase struct {
	Name           string
	TypeName       string
	Path           string
	Key            string
	Value          any
	ExpectedStatus testsuite.Status
	ExpectedErrors int
}

//nolint:funlen
func getODataNextLinkCheckTestCases() []oDataNextLinkCheckTestCase {
	return []oDataNextLinkCheckTestCase{
		{
			Name:           "Reports NextLink On NonCollection Type",
			TypeName:       "System",
			Path:           "/redfish/v1/Systems",
			Key:            "@odata.nextLink",
			Value:          "/redfish/v1/Systems?$skip=1",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports NonString NextLink",
			TypeName:       "SystemCollection",
			Path:           "/redfish/v1/Systems",
			Key:            "@odata.nextLink",
			Value:          123.0,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Invalid URI NextLink",
			TypeName:       "SystemCollection",
			Path:           "/redfish/v1/Systems",
			Key:            "@odata.nextLink",
			Value:          "http://[::1",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Allows Ref NextLink",
			TypeName:       "SystemCollection",
			Path:           "/redfish/v1/Systems",
			Key:            "@odata.nextLink",
			Value:          "/redfish/v1/Systems/$ref",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports PathMismatch NextLink",
			TypeName:       "SystemCollection",
			Path:           "/redfish/v1/Systems",
			Key:            "@odata.nextLink",
			Value:          "/redfish/v1/Chassis?$skip=1",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports MissingQuery NextLink",
			TypeName:       "SystemCollection",
			Path:           "/redfish/v1/Systems",
			Key:            "@odata.nextLink",
			Value:          "/redfish/v1/Systems",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Allows Valid NextLink",
			TypeName:       "SystemCollection",
			Path:           "/redfish/v1/Systems",
			Key:            "@odata.nextLink",
			Value:          "/redfish/v1/Systems?$skip=1",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows Valid MembersNextLink",
			TypeName:       "SystemCollection",
			Path:           "/redfish/v1/Systems",
			Key:            "Members@odata.nextLink",
			Value:          "/redfish/v1/Systems?$skip=1",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
	}
}

func TestODataNextLinkCheck(t *testing.T) {
	t.Parallel()

	m := mockup.NewMockup(filepath.Join(t.TempDir(), "test-mockup"), &config.Config{})

	for _, tc := range getODataNextLinkCheckTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			f := &mockup.File{
				Content: map[string]any{tc.Key: tc.Value},
				Type: &csdl.Type{
					Namespace: "Test.v1_0_0",
					Name:      tc.TypeName,
				},
			}

			tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
			f.ODataNextLinkCheck(tPrime, tc.Path, m, tc.Key)

			assert.Equal(t, tc.ExpectedStatus, tPrime.Status)
			require.Len(t, tPrime.Errors, tc.ExpectedErrors)
		})
	}
}

type navLinkIsSaneTestCase struct {
	Name           string
	MockupName     string
	Path           string
	Key            string
	Value          any
	PropType       string
	Excerpt        bool
	Files          map[string]map[string]any
	ExpectedStatus testsuite.Status
	ExpectedErrors int
}

//nolint:funlen
func getNavLinkIsSaneTestCases() []navLinkIsSaneTestCase {
	return []navLinkIsSaneTestCase{
		{
			Name:           "Reports NonObject Singleton NavLink",
			Path:           "/redfish/v1/Systems/1",
			Key:            "RelatedItem",
			Value:          "not-an-object",
			PropType:       "Resource.Item",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Missing ODataID In Singleton NavLink",
			Path:           "/redfish/v1/Systems/1",
			Key:            "RelatedItem",
			Value:          map[string]any{},
			PropType:       "Resource.Item",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name: "Reports NonString ODataID In Singleton NavLink",
			Path: "/redfish/v1/Systems/1",
			Key:  "RelatedItem",
			Value: map[string]any{
				"@odata.id": 42.0,
			},
			PropType:       "Resource.Item",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name: "Allows External Singleton NavLink",
			Path: "/redfish/v1/Systems/1",
			Key:  "RelatedItem",
			Value: map[string]any{
				"@odata.id": "https://example.com/redfish/v1/Systems/1",
			},
			PropType:       "Resource.Item",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows Excerpt Singleton NavLink",
			Path:           "/redfish/v1/Systems/1",
			Key:            "RelatedItem",
			Value:          map[string]any{},
			PropType:       "Resource.Item",
			Excerpt:        true,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:       "Allows Missing Target When Not Internally Consistent",
			MockupName: "DSP2046-examples",
			Path:       "/redfish/v1/Systems/1",
			Key:        "RelatedItem",
			Value: map[string]any{
				"@odata.id": "/redfish/v1/Systems/999",
			},
			PropType:       "Resource.Item",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Reports Missing Target When Internally Consistent",
			Path: "/redfish/v1/Systems/1",
			Key:  "RelatedItem",
			Value: map[string]any{
				"@odata.id": "/redfish/v1/Systems/999",
			},
			PropType:       "Resource.Item",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name: "Reports TypeMismatch For Existing Target",
			Path: "/redfish/v1/Systems/1",
			Key:  "RelatedItem",
			Value: map[string]any{
				"@odata.id": "/redfish/v1/Systems/2",
			},
			PropType: "Test.TargetType",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/2": {
					"@odata.type": "Test.OtherType",
				},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name: "Allows Matching Type For Existing Target",
			Path: "/redfish/v1/Systems/1",
			Key:  "RelatedItem",
			Value: map[string]any{
				"@odata.id": "/redfish/v1/Systems/2",
			},
			PropType: "Test.TargetType",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/2": {
					"@odata.type": "Test.TargetType",
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Allows Link To Existing File Without Type",
			Path: "/redfish/v1/Systems/1",
			Key:  "RelatedItem",
			Value: map[string]any{
				"@odata.id": "/redfish/v1/Errors/1",
			},
			PropType: "Test.TargetType",
			Files: map[string]map[string]any{
				"/redfish/v1/Errors/1": {
					"error": map[string]any{},
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Allows Link For ResourceItem PropType",
			Path: "/redfish/v1/Systems/1",
			Key:  "RelatedItem",
			Value: map[string]any{
				"@odata.id": "/redfish/v1/Systems/2",
			},
			PropType: "Resource.Item",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/2": {
					"@odata.type": "Test.OtherType",
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Allows Link For ResourceItemOrCollection PropType",
			Path: "/redfish/v1/Systems/1",
			Key:  "RelatedItem",
			Value: map[string]any{
				"@odata.id": "/redfish/v1/Systems/2",
			},
			PropType: "Resource.ItemOrCollection",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/2": {
					"@odata.type": "Test.OtherType",
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Allows Link For ResourceResource PropType",
			Path: "/redfish/v1/Systems/1",
			Key:  "RelatedItem",
			Value: map[string]any{
				"@odata.id": "/redfish/v1/Systems/2",
			},
			PropType: "Resource.Resource",
			Files: map[string]map[string]any{
				"/redfish/v1/Systems/2": {
					"@odata.type": "Test.OtherType",
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports NonArray Collection NavLink",
			Path:           "/redfish/v1/Systems/1",
			Key:            "Links",
			Value:          map[string]any{"@odata.id": "/redfish/v1/Systems/2"},
			PropType:       "Collection(Resource.Item)",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name: "Reports Missing Target In Collection NavLink",
			Path: "/redfish/v1/Systems/1",
			Key:  "Links",
			Value: []any{
				map[string]any{"@odata.id": "/redfish/v1/Systems/999"},
			},
			PropType:       "Collection(Resource.Item)",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
	}
}

func TestNavLinkIsSane(t *testing.T) {
	t.Parallel()

	typeMap := map[string]*csdl.Type{
		"Test.TargetType": {
			Namespace:  "Test.v1_0_0",
			Name:       "TargetType",
			Properties: map[string]csdl.PropType{},
		},
		"Test.OtherType": {
			Namespace:  "Test.v1_0_0",
			Name:       "OtherType",
			Properties: map[string]csdl.PropType{},
		},
	}

	for _, tc := range getNavLinkIsSaneTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			mockupName := "test-mockup"
			if tc.MockupName != "" {
				mockupName = tc.MockupName
			}
			m := mockup.NewMockup(filepath.Join(t.TempDir(), mockupName), &config.Config{})

			for path, content := range tc.Files {
				m.InjectFile(path, nil, content)
			}

			tSetup := testsuite.NewTesting("setup", &bytes.Buffer{})
			tSetup.Attr("typeMap", typeMap)
			tSetup.Attr("searcher", &csdl.Searcher{})
			m.FileTypesAreValid(tSetup)

			f := &mockup.File{Content: map[string]any{tc.Key: tc.Value}}
			csdlProp := &csdl.PropType{Type: tc.PropType, Navigation: true, Excerpt: tc.Excerpt}

			tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
			f.NavLinkIsSane(tPrime, tc.Path, m, tc.Key, csdlProp)

			assert.Equal(t, tc.ExpectedStatus, tPrime.Status)
			require.Len(t, tPrime.Errors, tc.ExpectedErrors)
		})
	}
}

type propValueIsSaneTestCase struct {
	Name           string
	PropType       string
	Value          any
	Annotations    []*csdl.Annotation
	ExpectedStatus testsuite.Status
	ExpectedErrors int
}

//nolint:funlen
func getPropValueIsSaneTestCases() []propValueIsSaneTestCase {
	return []propValueIsSaneTestCase{
		{
			Name:           "Allows Nil Value",
			PropType:       "Edm.String",
			Value:          nil,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows Valid Boolean",
			PropType:       "Edm.Boolean",
			Value:          true,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows PrimitiveType Boolean",
			PropType:       "Edm.PrimitiveType",
			Value:          true,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows PrimitiveType Number",
			PropType:       "Edm.PrimitiveType",
			Value:          42.0,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows PrimitiveType String",
			PropType:       "Edm.PrimitiveType",
			Value:          "primitive",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports Invalid PrimitiveType",
			PropType:       "Edm.PrimitiveType",
			Value:          map[string]any{"nested": "value"},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Invalid Boolean",
			PropType:       "Edm.Boolean",
			Value:          "true",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Invalid DateTimeOffset",
			PropType:       "Edm.DateTimeOffset",
			Value:          "not-a-date",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports DateTimeOffset Number Value",
			PropType:       "Edm.DateTimeOffset",
			Value:          42.0,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports DateTimeOffset Bool Value",
			PropType:       "Edm.DateTimeOffset",
			Value:          true,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Allows Decimal Number",
			PropType:       "Edm.Decimal",
			Value:          123.45,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows Decimal IntegerLike Number",
			PropType:       "Edm.Decimal",
			Value:          5.0,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports Decimal NonNumeric Value",
			PropType:       "Edm.Decimal",
			Value:          "123.45",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:     "Allows Decimal At Minimum",
			PropType: "Edm.Decimal",
			Value:    10.0,
			Annotations: []*csdl.Annotation{
				{Term: "Validation.Minimum", Int: 10},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:     "Reports Decimal Below Minimum",
			PropType: "Edm.Decimal",
			Value:    9.9,
			Annotations: []*csdl.Annotation{
				{Term: "Validation.Minimum", Int: 10},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:     "Allows Decimal At Maximum",
			PropType: "Edm.Decimal",
			Value:    50.0,
			Annotations: []*csdl.Annotation{
				{Term: "Validation.Maximum", Int: 50},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:     "Reports Decimal Above Maximum",
			PropType: "Edm.Decimal",
			Value:    50.1,
			Annotations: []*csdl.Annotation{
				{Term: "Validation.Maximum", Int: 50},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Allows Decimal Collection",
			PropType:       "Collection(Edm.Decimal)",
			Value:          []any{1.0, 2.5, -3.25},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows Empty Decimal Collection",
			PropType:       "Collection(Edm.Decimal)",
			Value:          []any{},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports Decimal Collection NonArray Value",
			PropType:       "Collection(Edm.Decimal)",
			Value:          "1.0",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Decimal Collection Invalid Item",
			PropType:       "Collection(Edm.Decimal)",
			Value:          []any{1.0, "bad"},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Allows Valid Duration",
			PropType:       "Edm.Duration",
			Value:          "PT1S",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports Duration Number Value",
			PropType:       "Edm.Duration",
			Value:          10.0,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Duration Bool Value",
			PropType:       "Edm.Duration",
			Value:          true,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Invalid Duration Format",
			PropType:       "Edm.Duration",
			Value:          "1H",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Invalid Duration Missing Prefix",
			PropType:       "Edm.Duration",
			Value:          "T1H",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Invalid Guid",
			PropType:       "Edm.Guid",
			Value:          "invalid-guid",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Guid Number Value",
			PropType:       "Edm.Guid",
			Value:          123.0,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports UUID Bool Value",
			PropType:       "Resource.UUID",
			Value:          false,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Int64 String Value",
			PropType:       "Edm.Int64",
			Value:          "1",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Int64 Bool Value",
			PropType:       "Edm.Int64",
			Value:          true,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports EdmString Number Value",
			PropType:       "Edm.String",
			Value:          123.0,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Allows EdmString Value",
			PropType:       "Edm.String",
			Value:          "hello",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows Empty EdmString Value",
			PropType:       "Edm.String",
			Value:          "",
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports EdmString Bool Value",
			PropType:       "Edm.String",
			Value:          false,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Allows IntegerLike Int64 Float",
			PropType:       "Edm.Int64",
			Value:          2.0,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows Negative IntegerLike Int64 Float",
			PropType:       "Edm.Int64",
			Value:          -7.0,
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports NonInteger Int64",
			PropType:       "Edm.Int64",
			Value:          1.5,
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Allows String Collection With Nil Item",
			PropType:       "Collection(Edm.String)",
			Value:          []any{"a", nil, "b"},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports String Collection NonArray Value",
			PropType:       "Collection(Edm.String)",
			Value:          "not-an-array",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports String Collection Invalid Item",
			PropType:       "Collection(Edm.String)",
			Value:          []any{"ok", 2.0},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Allows Int64 Collection",
			PropType:       "Collection(Edm.Int64)",
			Value:          []any{1.0, 0.0, -10.0},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Allows Empty Int64 Collection",
			PropType:       "Collection(Edm.Int64)",
			Value:          []any{},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports Int64 Collection NonArray Value",
			PropType:       "Collection(Edm.Int64)",
			Value:          "1",
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Int64 Collection NonInteger Item",
			PropType:       "Collection(Edm.Int64)",
			Value:          []any{1.0, 2.5},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Ignores CapacityType",
			PropType:       "Capacity.Capacity",
			Value:          map[string]any{"Bytes": 1024.0},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name:           "Reports Invalid Int64 Collection Item",
			PropType:       "Collection(Edm.Int64)",
			Value:          []any{1.0, "bad"},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name:           "Reports Unknown Type",
			PropType:       "Test.UnknownType",
			Value:          map[string]any{"Any": "Value"},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
	}
}

func TestPropValueIsSane(t *testing.T) {
	t.Parallel()

	path := "/redfish/v1/Systems/1"
	propName := "TestProp"

	for _, tc := range getPropValueIsSaneTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			m := mockup.NewMockup(filepath.Join(t.TempDir(), "test-mockup"), &config.Config{})

			f := &mockup.File{}
			csdlProp := &csdl.PropType{Type: tc.PropType, Annotations: tc.Annotations}

			tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
			f.PropValueIsSane(tPrime, path, m, propName, tc.Value, csdlProp)

			assert.Equal(t, tc.ExpectedStatus, tPrime.Status)
			require.Len(t, tPrime.Errors, tc.ExpectedErrors)
		})
	}
}

func TestGetPropertyFromCSDLType(t *testing.T) {
	t.Parallel()

	allTypes := map[string]*csdl.Type{
		"Test.v1_0_0.Base": {
			Namespace: "Test.v1_0_0",
			Name:      "Base",
			Properties: map[string]csdl.PropType{
				"BaseProp": {Type: "Edm.String"},
			},
		},
		"Test.v1_0_0.Child": {
			Namespace: "Test.v1_0_0",
			Name:      "Child",
			BaseType:  "Test.v1_0_0.Base",
			Properties: map[string]csdl.PropType{
				"ChildProp": {Type: "Edm.Int64"},
			},
		},
	}

	child := allTypes["Test.v1_0_0.Child"]

	t.Run("Finds Direct Property", func(t *testing.T) {
		t.Parallel()

		prop := mockup.GetPropertyFromCSDLType("ChildProp", child, allTypes)
		require.NotNil(t, prop)
		assert.Equal(t, "Edm.Int64", prop.Type)
	})

	t.Run("Finds Property In Base Type", func(t *testing.T) {
		t.Parallel()

		prop := mockup.GetPropertyFromCSDLType("BaseProp", child, allTypes)
		require.NotNil(t, prop)
		assert.Equal(t, "Edm.String", prop.Type)
	})

	t.Run("Returns Nil For Missing Property", func(t *testing.T) {
		t.Parallel()

		prop := mockup.GetPropertyFromCSDLType("MissingProp", child, allTypes)
		assert.Nil(t, prop)
	})
}

func TestBuildDescendantIndex(t *testing.T) {
	t.Parallel()

	allTypes := map[string]*csdl.Type{
		"Test.v1_0_0.Base": {
			Namespace:  "Test.v1_0_0",
			Name:       "Base",
			Properties: map[string]csdl.PropType{},
		},
		"Test.v1_0_0.ChildA": {
			Namespace: "Test.v1_0_0",
			Name:      "ChildA",
			BaseType:  "Test.v1_0_0.Base",
		},
		"Test.v1_0_0.ChildB": {
			Namespace: "Test.v1_0_0",
			Name:      "ChildB",
			BaseType:  "Test.v1_0_0.Base",
		},
		"Test.v1_0_0.GrandChild": {
			Namespace: "Test.v1_0_0",
			Name:      "GrandChild",
			BaseType:  "Test.v1_0_0.ChildA",
		},
	}

	idx := mockup.BuildDescendantIndex(allTypes)

	t.Run("Root has two children", func(t *testing.T) {
		t.Parallel()

		children := idx["Test.v1_0_0.Base"]
		assert.Len(t, children, 2)
	})

	t.Run("ChildA has one grandchild", func(t *testing.T) {
		t.Parallel()

		children := idx["Test.v1_0_0.ChildA"]
		require.Len(t, children, 1)
		assert.Equal(t, "GrandChild", children[0].Name)
	})

	t.Run("Leaf has no children", func(t *testing.T) {
		t.Parallel()

		children := idx["Test.v1_0_0.GrandChild"]
		assert.Empty(t, children)
	})

	t.Run("Empty map produces empty index", func(t *testing.T) {
		t.Parallel()

		emptyIdx := mockup.BuildDescendantIndex(map[string]*csdl.Type{})
		assert.Empty(t, emptyIdx)
	})
}

func TestGetPropertyFromCSDLTypeOrDescendents(t *testing.T) {
	t.Parallel()

	allTypes := map[string]*csdl.Type{
		"Test.v1_0_0.Base": {
			Namespace:  "Test.v1_0_0",
			Name:       "Base",
			Properties: map[string]csdl.PropType{},
		},
		"Test.v1_0_0.Child": {
			Namespace: "Test.v1_0_0",
			Name:      "Child",
			BaseType:  "Test.v1_0_0.Base",
			Properties: map[string]csdl.PropType{
				"ChildProp": {Type: "Edm.String"},
			},
		},
		"Test.v1_0_0.GrandChild": {
			Namespace: "Test.v1_0_0",
			Name:      "GrandChild",
			BaseType:  "Test.v1_0_0.Child",
			Properties: map[string]csdl.PropType{
				"GrandChildProp": {Type: "Edm.Boolean"},
			},
		},
	}

	idx := mockup.BuildDescendantIndex(allTypes)
	base := allTypes["Test.v1_0_0.Base"]

	t.Run("Finds Property In Descendent", func(t *testing.T) {
		t.Parallel()

		prop := mockup.GetPropertyFromCSDLTypeOrDescendents("ChildProp", base, allTypes, idx)
		require.NotNil(t, prop)
		assert.Equal(t, "Edm.String", prop.Type)
	})

	t.Run("Finds Property In Deep Descendent", func(t *testing.T) {
		t.Parallel()

		prop := mockup.GetPropertyFromCSDLTypeOrDescendents("GrandChildProp", base, allTypes, idx)
		require.NotNil(t, prop)
		assert.Equal(t, "Edm.Boolean", prop.Type)
	})

	t.Run("Returns Nil For Missing Property", func(t *testing.T) {
		t.Parallel()

		prop := mockup.GetPropertyFromCSDLTypeOrDescendents("MissingProp", base, allTypes, idx)
		assert.Nil(t, prop)
	})
}

type doTypeContentCheckTestCase struct {
	Name           string
	Path           string
	Type           *csdl.Type
	Content        map[string]any
	ExpectedStatus testsuite.Status
	ExpectedErrors int
}

//nolint:funlen
func getDoTypeContentCheckTestCases() []doTypeContentCheckTestCase {
	return []doTypeContentCheckTestCase{
		{
			Name: "Allows Valid Primitive Property",
			Path: "/redfish/v1/Systems/1",
			Type: &csdl.Type{
				Namespace: "Test.v1_0_0",
				Name:      "System",
				Properties: map[string]csdl.PropType{
					"Name": {Type: "Edm.String"},
				},
			},
			Content: map[string]any{
				"Name": "System One",
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Reports Unknown Property",
			Path: "/redfish/v1/Systems/1",
			Type: &csdl.Type{
				Namespace:  "Test.v1_0_0",
				Name:       "System",
				Properties: map[string]csdl.PropType{},
			},
			Content: map[string]any{
				"Unknown": "value",
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
		{
			Name: "Ignores Redfish Annotation Keys",
			Path: "/redfish/v1/Systems/1",
			Type: &csdl.Type{
				Namespace:  "Test.v1_0_0",
				Name:       "System",
				Properties: map[string]csdl.PropType{},
			},
			Content: map[string]any{
				"Name@Redfish.AllowableValues": []any{"A", "B"},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Allows Valid ODataNextLink On Collection",
			Path: "/redfish/v1/Systems",
			Type: &csdl.Type{
				Namespace:  "Test.v1_0_0",
				Name:       "SystemCollection",
				Properties: map[string]csdl.PropType{},
			},
			Content: map[string]any{
				"@odata.nextLink": "/redfish/v1/Systems?$skip=1",
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Allows Matching MembersODataCount On Collection",
			Path: "/redfish/v1/Systems",
			Type: &csdl.Type{
				Namespace: "Test.v1_0_0",
				Name:      "SystemCollection",
				Properties: map[string]csdl.PropType{
					"Members": {Type: "Collection(Edm.String)"},
				},
			},
			Content: map[string]any{
				"Members@odata.count": 2.0,
				"Members": []any{
					"System1",
					"System2",
				},
			},
			ExpectedStatus: testsuite.Success,
			ExpectedErrors: 0,
		},
		{
			Name: "Reports Missing ODataID In Navigation Property",
			Path: "/redfish/v1/Systems/1",
			Type: &csdl.Type{
				Namespace: "Test.v1_0_0",
				Name:      "System",
				Properties: map[string]csdl.PropType{
					"RelatedItem": {Type: "Resource.Item", Navigation: true},
				},
			},
			Content: map[string]any{
				"RelatedItem": map[string]any{},
			},
			ExpectedStatus: testsuite.Warning,
			ExpectedErrors: 1,
		},
	}
}

func TestDoTypeContentCheck(t *testing.T) {
	t.Parallel()

	for _, tc := range getDoTypeContentCheckTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			m := mockup.NewMockup(filepath.Join(t.TempDir(), "test-mockup"), &config.Config{})
			f := &mockup.File{Type: tc.Type, Content: tc.Content}

			tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
			f.DoTypeContentCheck(tPrime, tc.Path, m)

			assert.Equal(t, tc.ExpectedStatus, tPrime.Status)
			require.Len(t, tPrime.Errors, tc.ExpectedErrors)
		})
	}
}

func TestContentMatchesType(t *testing.T) {
	t.Parallel()

	typeMap := map[string]*csdl.Type{
		"Test.Type": {
			Namespace:  "Test.v1_0_0",
			Name:       "Type",
			Properties: map[string]csdl.PropType{},
		},
		"Test.NavType": {
			Namespace: "Test.v1_0_0",
			Name:      "NavType",
			Properties: map[string]csdl.PropType{
				"RelatedItem": {
					Type:       "Resource.Item",
					Navigation: true,
				},
			},
		},
	}

	for _, tc := range getContentMatchesTypeTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			mockupName := "test-mockup"
			if tc.MockupName != "" {
				mockupName = tc.MockupName
			}
			m := mockup.NewMockup(filepath.Join(t.TempDir(), mockupName), &config.Config{})
			for path, content := range tc.Files {
				m.InjectFile(path, nil, content)
			}

			tSetup := testsuite.NewTesting("setup", &bytes.Buffer{})
			tSetup.Attr("typeMap", typeMap)
			tSetup.Attr("searcher", &csdl.Searcher{})
			m.FileTypesAreValid(tSetup)
			assert.Equal(t, testsuite.Success, tSetup.Status)

			tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
			m.ContentMatchesType(tPrime)

			assert.Equal(t, tc.ExpectedStatus, tPrime.Status)
			require.Len(t, tPrime.Errors, tc.ExpectedErrors)
		})
	}
}

// TestContentMatchesTypeAutoFixPreservesAnnotations verifies that when auto-fix
// in ContentMatchesType saves the file, it does not discard @Redfish.Copyright
// or the other @odata.* annotations.
func TestContentMatchesTypeAutoFixPreservesAnnotations(t *testing.T) {
	t.Parallel()

	typeMap := map[string]*csdl.Type{
		"Test.Type": {
			Namespace:  "Test.v1_0_0",
			Name:       "Type",
			Properties: map[string]csdl.PropType{},
		},
	}

	dir := t.TempDir()
	m := mockup.NewMockup(filepath.Join(dir, "test-mockup"), &config.Config{})
	realPath := m.GetRealPath("/redfish/v1/Systems/1")
	require.NoError(t, os.MkdirAll(filepath.Dir(realPath), 0o755)) //nolint:gosec
	require.NoError(t, os.WriteFile(realPath,
		[]byte(`{"@odata.type":"Test.Type","@Redfish.Copyright":"Copyright Test."}`), 0o600))

	tSetup := testsuite.NewTesting("setup", &bytes.Buffer{})
	tSetup.Attr("typeMap", typeMap)
	tSetup.Attr("searcher", &csdl.Searcher{})
	m.Load(tSetup)
	m.FileTypesAreValid(tSetup)
	assert.Equal(t, testsuite.Success, tSetup.Status)

	tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
	tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}
	m.ContentMatchesType(tPrime)

	assert.Equal(t, testsuite.Success, tPrime.Status)
	assert.Empty(t, tPrime.Errors)

	data, err := os.ReadFile(realPath) //nolint:gosec // test-only read of temp path
	require.NoError(t, err)
	assert.Contains(t, string(data), `"@odata.id": "/redfish/v1/Systems/1"`)
	assert.Contains(t, string(data), `"@Redfish.Copyright": "Copyright Test."`)
	assert.Contains(t, string(data), `"@odata.type": "Test.Type"`)
}

// TestContentMatchesTypeAutoFixRemovesNestedODataType verifies that an
// @odata.type annotation inside a nested complex property is removed when
// auto-fix is enabled, while the root @odata.type is preserved.
func TestContentMatchesTypeAutoFixRemovesNestedODataType(t *testing.T) {
	t.Parallel()

	typeMap := map[string]*csdl.Type{
		"Test.System": {
			Namespace: "Test.v1_0_0",
			Name:      "System",
			Properties: map[string]csdl.PropType{
				"Location": {Type: "Test.Location"},
			},
		},
		"Test.Location": {
			Namespace: "Test.v1_0_0",
			Name:      "Location",
			Properties: map[string]csdl.PropType{
				"City": {Type: "Edm.String"},
			},
		},
	}

	dir := t.TempDir()
	m := mockup.NewMockup(filepath.Join(dir, "test-mockup"), &config.Config{})
	path := "/redfish/v1/Systems/1"
	realPath := m.GetRealPath(path)
	require.NoError(t, os.MkdirAll(filepath.Dir(realPath), 0o755)) //nolint:gosec

	m.InjectFile(path, nil, map[string]any{
		"@odata.type":    "#Test.System",
		"@odata.id":      path,
		"@odata.context": "/redfish/v1/$metadata#Test.System",
		"Location": map[string]any{
			"@odata.type": "#Test.Location",
			"City":        "Portland",
		},
	})

	tSetup := testsuite.NewTesting("setup", &bytes.Buffer{})
	tSetup.Attr("typeMap", typeMap)
	tSetup.Attr("searcher", &csdl.Searcher{})
	m.FileTypesAreValid(tSetup)
	assert.Equal(t, testsuite.Success, tSetup.Status)

	tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
	tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}
	m.ContentMatchesType(tPrime)

	assert.Equal(t, testsuite.Success, tPrime.Status)
	assert.Empty(t, tPrime.Errors)

	data, err := os.ReadFile(realPath) //nolint:gosec // test-only read of temp path
	require.NoError(t, err)
	assert.Contains(t, string(data), `"@odata.type": "#Test.System"`)
	assert.NotContains(t, string(data), "        \"@odata.type\"")
	assert.Contains(t, string(data), `"City": "Portland"`)
}

func TestODataIDMatchesPathAutoFix(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name           string
		initialContent map[string]any
		initialJSON    string
	}{
		{
			name:           "CorrectsMismatch",
			initialContent: map[string]any{"@odata.id": "/redfish/v1/Systems/2"},
			initialJSON:    `{"@odata.id":"/redfish/v1/Systems/2"}`,
		},
		{
			name:           "AddsMissingODataID",
			initialContent: map[string]any{"Name": "System 1"},
			initialJSON:    `{"Name":"System 1"}`,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			dir := t.TempDir()
			m := mockup.NewMockup(dir, &config.Config{})
			realPath := m.GetRealPath("/redfish/v1/Systems/1")
			require.NoError(t, os.MkdirAll(filepath.Dir(realPath), 0o755))            //nolint:gosec
			require.NoError(t, os.WriteFile(realPath, []byte(tc.initialJSON), 0o644)) //nolint:gosec

			f := &mockup.File{Content: tc.initialContent}
			tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
			tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}

			f.ODataIDMatchesPath(tPrime, "/redfish/v1/Systems/1", m)

			assert.Equal(t, testsuite.Success, tPrime.Status)
			assert.Empty(t, tPrime.Errors)
			assert.Equal(t, "/redfish/v1/Systems/1", f.Content["@odata.id"])

			data, err := os.ReadFile(realPath) //nolint:gosec // test-only read of temp path
			require.NoError(t, err)
			assert.Contains(t, string(data), `"@odata.id": "/redfish/v1/Systems/1"`)
		})
	}
}

type dateTimeOffsetAutoFixCase struct {
	name           string
	input          string
	expectedValue  string
	expectedStatus testsuite.Status
	expectedErrors int
}

func getDateTimeOffsetAutoFixCases() []dateTimeOffsetAutoFixCase {
	return []dateTimeOffsetAutoFixCase{
		{
			name:           "FixesKnownDateTimeFormat",
			input:          "2024-01-02 03:04:05",
			expectedValue:  "2024-01-02T03:04:05Z",
			expectedStatus: testsuite.Success,
			expectedErrors: 0,
		},
		{
			name:           "FixesSingleDigitTimezoneOffset",
			input:          "2018-04-01T00:01+6:00",
			expectedValue:  "2018-04-01T00:01:00+06:00",
			expectedStatus: testsuite.Success,
			expectedErrors: 0,
		},
		{
			name:           "LogsErrorForUnparseableValue",
			input:          "not-a-date",
			expectedValue:  "not-a-date",
			expectedStatus: testsuite.Warning,
			expectedErrors: 1,
		},
		{
			name:           "FixesLeadingWhitespace",
			input:          "  2024-01-02T03:04:05Z",
			expectedValue:  "2024-01-02T03:04:05Z",
			expectedStatus: testsuite.Success,
			expectedErrors: 0,
		},
		{
			name:           "FixesTrailingWhitespace",
			input:          "2024-01-02T03:04:05Z  ",
			expectedValue:  "2024-01-02T03:04:05Z",
			expectedStatus: testsuite.Success,
			expectedErrors: 0,
		},
		{
			name:           "FixesLeadingAndTrailingWhitespace",
			input:          "  2024-01-02T03:04:05Z  ",
			expectedValue:  "2024-01-02T03:04:05Z",
			expectedStatus: testsuite.Success,
			expectedErrors: 0,
		},
		{
			name:           "FixesWhitespaceAroundNonRFC3339Format",
			input:          "  2024-01-02 03:04:05  ",
			expectedValue:  "2024-01-02T03:04:05Z",
			expectedStatus: testsuite.Success,
			expectedErrors: 0,
		},
	}
}

func TestDateTimeOffsetValidationAutoFix(t *testing.T) {
	t.Parallel()

	for _, tc := range getDateTimeOffsetAutoFixCases() {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			dir := t.TempDir()
			m := mockup.NewMockup(dir, &config.Config{})
			path := "/redfish/v1/Systems/1"
			realPath := m.GetRealPath(path)
			require.NoError(t, os.MkdirAll(filepath.Dir(realPath), 0o755)) //nolint:gosec

			f := &mockup.File{
				Content: map[string]any{
					"@odata.id": path,
					"BootTime":  tc.input,
				},
				Type: &csdl.Type{
					Namespace: "Test.v1_0_0",
					Name:      "System",
					Properties: map[string]csdl.PropType{
						"BootTime": {Type: "Edm.DateTimeOffset"},
					},
				},
			}

			tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
			tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}
			f.DoTypeContentCheck(tPrime, path, m)

			assert.Equal(t, tc.expectedStatus, tPrime.Status)
			require.Len(t, tPrime.Errors, tc.expectedErrors)
			if tc.expectedStatus == testsuite.Success {
				data, err := os.ReadFile(realPath) //nolint:gosec // test-only read of temp path
				require.NoError(t, err)
				assert.Contains(t, string(data), `"BootTime": "`+tc.expectedValue+`"`)
			}
		})
	}
}

func TestSetValueAtPath(t *testing.T) {
	t.Parallel()

	tests := getSetValueAtPathTestCases()
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			// Make a copy of content for modification
			contentCopy := make(map[string]any, len(tc.content))
			for k, v := range tc.content {
				contentCopy[k] = v
			}
			result := mockup.SetValueAtPath(contentCopy, tc.path, tc.value)
			assert.Equal(t, tc.ok, result)
			assert.Equal(t, tc.expected, contentCopy)
		})
	}
}

//nolint:funlen // Test data helper function
func getSetValueAtPathTestCases() []struct {
	name     string
	content  map[string]any
	path     string
	value    any
	expected map[string]any
	ok       bool
} {
	return []struct {
		name     string
		content  map[string]any
		path     string
		value    any
		expected map[string]any
		ok       bool
	}{
		{
			name: "simple key",
			content: map[string]any{
				"BootTime": "2024-01-02T03:04:05Z",
			},
			path:  "BootTime",
			value: "2024-01-02T03:04:06Z",
			expected: map[string]any{
				"BootTime": "2024-01-02T03:04:06Z",
			},
			ok: true,
		},
		{
			name: "nested key",
			content: map[string]any{
				"Conditions": []any{
					map[string]any{
						"Timestamp": "2020-11-08T12:25:00-05:00 ",
					},
				},
			},
			path:  "Conditions[0].Timestamp",
			value: "2020-11-08T12:25:00-05:00",
			expected: map[string]any{
				"Conditions": []any{
					map[string]any{
						"Timestamp": "2020-11-08T12:25:00-05:00",
					},
				},
			},
			ok: true,
		},
		{
			name: "deeply nested",
			content: map[string]any{
				"Conditions": []any{
					map[string]any{
						"OriginOfCondition": map[string]any{
							"@odata.id": "/redfish/v1/Chassis/1/Power",
						},
					},
				},
			},
			path:  "Conditions[0].OriginOfCondition.@odata.id",
			value: "/redfish/v1/Chassis/2/Power",
			expected: map[string]any{
				"Conditions": []any{
					map[string]any{
						"OriginOfCondition": map[string]any{
							"@odata.id": "/redfish/v1/Chassis/2/Power",
						},
					},
				},
			},
			ok: true,
		},
		{
			name: "invalid array index",
			content: map[string]any{
				"Conditions": []any{
					map[string]any{},
				},
			},
			path:  "Conditions[5].Timestamp",
			value: "2020-11-08T12:25:00-05:00",
			expected: map[string]any{
				"Conditions": []any{
					map[string]any{},
				},
			},
			ok: false,
		},
		{
			name: "missing intermediate key",
			content: map[string]any{
				"Conditions": []any{},
			},
			path:  "Conditions[0].Timestamp",
			value: "2020-11-08T12:25:00-05:00",
			expected: map[string]any{
				"Conditions": []any{},
			},
			ok: false,
		},
	}
}

func TestDateTimeOffsetValidationAutoFixNestedProperty(t *testing.T) {
	t.Parallel()

	dir := t.TempDir()
	m := mockup.NewMockup(dir, &config.Config{})
	path := "/redfish/v1/ServiceConditions"
	realPath := m.GetRealPath(path)
	require.NoError(t, os.MkdirAll(filepath.Dir(realPath), 0o755)) //nolint:gosec

	setupServiceConditionsTypes(m)

	// Copy the test file to the temp directory
	data, err := os.ReadFile("./testData/serviceConditions.json")
	require.NoError(t, err)
	require.NoError(t, os.WriteFile(realPath, data, 0o644)) //nolint:gosec

	// Read the file into a File struct
	var content map[string]any
	require.NoError(t, json.Unmarshal(data, &content))
	f := &mockup.File{
		Content: content,
		Type:    getServiceConditionsType(),
	}

	tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
	tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}
	f.DoTypeContentCheck(tPrime, path, m)

	// We expect some warnings about other properties (OriginOfCondition, LogEntry),
	// but the Timestamp should have been fixed
	assert.NotEmpty(t, tPrime.Errors)

	// Read the fixed file and verify the Timestamp was trimmed
	fixedData, err := os.ReadFile(realPath) //nolint:gosec // test-only read of temp path
	require.NoError(t, err)
	var fixedContent map[string]any
	require.NoError(t, json.Unmarshal(fixedData, &fixedContent))

	// Navigate to Conditions[0].Timestamp
	conditions, ok := fixedContent["Conditions"].([]any)
	require.True(t, ok)
	require.Len(t, conditions, 2)
	condition0, ok := conditions[0].(map[string]any)
	require.True(t, ok)
	timestamp, ok := condition0["Timestamp"].(string)
	require.True(t, ok)
	assert.Equal(t, "2020-11-08T12:25:00-05:00", timestamp, "Timestamp should be trimmed and fixed")
}

func setupServiceConditionsTypes(m *mockup.Mockup) {
	conditionType := &csdl.Type{
		Namespace: "Condition.v1_0_0",
		Name:      "Condition",
		Properties: map[string]csdl.PropType{
			"Timestamp":         {Type: "Edm.DateTimeOffset"},
			"MessageId":         {Type: "Edm.String"},
			"Message":           {Type: "Edm.String"},
			"Severity":          {Type: "Edm.String"},
			"MessageArgs":       {Type: "Collection(Edm.String)"},
			"OriginOfCondition": {Type: "Edm.String"},
			"LogEntry":          {Type: "Edm.String"},
		},
	}
	m.AddType(conditionType)
	m.AddType(getServiceConditionsType())
}

func getServiceConditionsType() *csdl.Type {
	return &csdl.Type{
		Namespace: "ServiceConditions.v1_0_1",
		Name:      "ServiceConditions",
		Properties: map[string]csdl.PropType{
			"Name":         {Type: "Edm.String"},
			"HealthRollup": {Type: "Edm.String"},
			"Conditions":   {Type: "Collection(Condition)"},
		},
	}
}

func TestODataIDMatchesPathAutoFixWhitespace(t *testing.T) {
	t.Parallel()

	dir := t.TempDir()
	m := mockup.NewMockup(dir, &config.Config{})
	realPath := m.GetRealPath("/redfish/v1/EventService/Subscriptions")
	require.NoError(t, os.MkdirAll(filepath.Dir(realPath), 0o755)) //nolint:gosec
	// Read ./testData/eventDestinationCollection.json and write it to realPath
	data, err := os.ReadFile("./testData/eventDestinationCollection.json")
	require.NoError(t, err)
	require.NoError(t, os.WriteFile(realPath, data, 0o644)) //nolint:gosec

	var initalContent map[string]any
	require.NoError(t, json.Unmarshal(data, &initalContent))

	// Now read it back and verify that the @odata.id is correct
	f := &mockup.File{Content: initalContent}
	tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
	tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}

	f.ODataIDMatchesPath(tPrime, "/redfish/v1/EventService/Subscriptions", m)

	assert.Equal(t, testsuite.Success, tPrime.Status)
	assert.Empty(t, tPrime.Errors)
	assert.Equal(t, "/redfish/v1/EventService/Subscriptions", f.Content["@odata.id"])

	data, err = os.ReadFile(realPath) //nolint:gosec // test-only read of temp path
	require.NoError(t, err)
	// Verify that the @odata.id is present and that the json whitespace has not been significantly altered.
	assert.Contains(t, string(data), `"@odata.id": "/redfish/v1/EventService/Subscriptions"`)

	// Read the fixed file and verify that it has the correct @odata.id
	fixedData, err := os.ReadFile("./testData/eventDestinationCollection_fixed.json")
	require.NoError(t, err)
	assert.Equal(t, string(data), string(fixedData))
}
