/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package dsp2046

import (
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCollectEntityTypes(t *testing.T) {
	t.Parallel()

	edmx := &csdl.Edmx{
		DataServices: csdl.DataServices{
			Schema: []*csdl.Schema{
				{
					Namespace: "Resource.v1_0_0",
					EntityType: []*csdl.EntityType{
						{Name: "ReferenceableMember"},
					},
				},
				{
					Namespace: "Example.v1_0_0",
					EntityType: []*csdl.EntityType{
						{Name: "DerivedDirect", BaseType: "Resource.v1_0_0.ReferenceableMember"},
						{Name: "DerivedIndirect", BaseType: "Example.v1_0_0.DerivedDirect"},
						{Name: "NormalEntity", BaseType: "Resource.v1_0_0.Resource"},
						{Name: "NormalEntityCollection", BaseType: "Resource.v1_0_0.ResourceCollection"},
						{Name: "AbstractEntity", BaseType: "Resource.v1_0_0.Resource", Abstract: true},
					},
				},
				{
					Namespace: "Example.v2_0_0",
					EntityType: []*csdl.EntityType{
						{Name: "DerivedCrossVersion", BaseType: "Example.DerivedDirect"},
					},
				},
			},
		},
	}

	assert.ElementsMatch(t,
		[]string{
			"Resource.v1_0_0.ReferenceableMember",
			"Example.v1_0_0.NormalEntity",
		},
		collectEntityTypes(edmx),
	)
}

func TestCollectEntityTypes_CyclicBaseTypesDoesNotLoop(t *testing.T) {
	t.Parallel()

	edmx := &csdl.Edmx{
		DataServices: csdl.DataServices{
			Schema: []*csdl.Schema{
				{
					Namespace: "Example.v1_0_0",
					EntityType: []*csdl.EntityType{
						{Name: "EntityA", BaseType: "Example.v1_0_0.EntityB"},
						{Name: "EntityB", BaseType: "Example.v1_0_0.EntityA"},
						{Name: "EntityC", BaseType: "Resource.v1_0_0.ReferenceableMember"},
						{Name: "EntityD", BaseType: "Resource.v1_0_0.Resource"},
					},
				},
			},
		},
	}

	assert.ElementsMatch(t,
		[]string{
			"Example.v1_0_0.EntityA",
			"Example.v1_0_0.EntityB",
			"Example.v1_0_0.EntityD",
		},
		collectEntityTypes(edmx),
	)
}

func TestCollectActions(t *testing.T) {
	t.Parallel()

	edmx := &csdl.Edmx{
		DataServices: csdl.DataServices{
			Schema: []*csdl.Schema{
				{
					Namespace: "Actions.v1_0_0",
					Action: []*csdl.Action{
						{
							Name:       "Reset",
							ReturnType: &csdl.ReturnType{Type: "Edm.String"},
							Parameter: []*csdl.Parameter{
								{Name: "target"},
								{Name: "ResetType"},
							},
						},
						{
							Name:       "Clear",
							ReturnType: nil,
							Parameter: []*csdl.Parameter{
								{Name: "target"},
							},
						},
					},
				},
			},
		},
	}

	assert.Equal(t,
		[]actionInfo{
			{Name: "Actions.v1_0_0.Reset", HasReturnType: true, NeedsRequest: true},
			{Name: "Actions.v1_0_0.Clear", HasReturnType: false, NeedsRequest: false},
		},
		collectActions(edmx),
	)
}

func TestHasEntityExample(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name       string
		entityType string
		files      []exampleFile
		expected   bool
	}{
		{
			name:       "matches versioned odata type in content",
			entityType: "ComputerSystem.v1_17_0.ComputerSystem",
			files: []exampleFile{
				newExampleFile("/tmp/example.json", `{"@odata.type":"#ComputerSystem.v1_17_0.ComputerSystem"}`),
			},
			expected: true,
		},
		{
			name:       "matches unversioned odata type in content",
			entityType: "ComputerSystem.v1_17_0.ComputerSystem",
			files: []exampleFile{
				newExampleFile("/tmp/example.json", `{"@odata.type":"#ComputerSystem.ComputerSystem"}`),
			},
			expected: true,
		},
		{
			name:       "matches unversioned filename convention",
			entityType: "ComputerSystem.v1_17_0.ComputerSystem",
			files: []exampleFile{
				newExampleFile(filepath.Join("/tmp", "computersystem-computersystem-v1-example.json"), `{}`),
			},
			expected: true,
		},
		{
			name:       "does not match unrelated example",
			entityType: "ComputerSystem.v1_17_0.ComputerSystem",
			files: []exampleFile{
				newExampleFile(
					filepath.Join("/tmp", "thermal-thermal-v1-example.json"),
					`{"@odata.type":"#Thermal.v1_0_0.Thermal"}`,
				),
			},
			expected: false,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			assert.Equal(t, tc.expected, hasEntityExample(tc.entityType, tc.files))
		})
	}
}

func TestShouldIncludeCSDLFile(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name       string
		singleFile string
		fileName   string
		expected   bool
	}{
		{name: "includes all when single file empty", singleFile: "", fileName: "ComputerSystem_v1.xml", expected: true},
		{name: "non xml single file excludes", singleFile: "README.md", fileName: "ComputerSystem_v1.xml", expected: false},
		{
			name:       "matching xml base name includes",
			singleFile: "/tmp/ComputerSystem_v1.xml",
			fileName:   "ComputerSystem_v1.xml",
			expected:   true,
		},
		{
			name:       "non matching xml base name excludes",
			singleFile: "/tmp/Chassis_v1.xml",
			fileName:   "ComputerSystem_v1.xml",
			expected:   false,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			assert.Equal(t, tc.expected, shouldIncludeCSDLFile(tc.singleFile, tc.fileName))
		})
	}
}

func TestLoadDSP2046ExampleFiles(t *testing.T) {
	t.Parallel()

	t.Run("loads json files recursively and sorts by path", func(t *testing.T) {
		t.Parallel()

		dir := t.TempDir()
		require.NoError(t, os.MkdirAll(filepath.Join(dir, "nested"), 0o755))                                    //nolint:gosec
		require.NoError(t, os.WriteFile(filepath.Join(dir, "b.json"), []byte(`{"Name":"B"}`), 0o644))           //nolint:gosec
		require.NoError(t, os.WriteFile(filepath.Join(dir, "nested", "a.json"), []byte(`{"Name":"A"}`), 0o644)) //nolint:gosec
		require.NoError(t, os.WriteFile(filepath.Join(dir, "ignore.txt"), []byte("ignored"), 0o644))            //nolint:gosec

		files, err := loadDSP2046ExampleFiles(dir)
		require.NoError(t, err)
		require.Len(t, files, 2)
		assert.LessOrEqual(t, strings.Compare(files[0].Path, files[1].Path), 0)
		assert.ElementsMatch(t,
			[]string{filepath.Join(dir, "b.json"), filepath.Join(dir, "nested", "a.json")},
			[]string{files[0].Path, files[1].Path},
		)
	})

	t.Run("missing directory returns error", func(t *testing.T) {
		t.Parallel()

		_, err := loadDSP2046ExampleFiles(filepath.Join(t.TempDir(), "missing"))
		assert.Error(t, err)
	})
}

func TestGetUnversionedEntityType(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name       string
		entityType string
		expected   string
	}{
		{name: "empty", entityType: "", expected: ""},
		{
			name:       "versioned namespace",
			entityType: "ComputerSystem.v1_17_0.ComputerSystem",
			expected:   "ComputerSystem.ComputerSystem",
		},
		{name: "already unversioned", entityType: "ComputerSystem.ComputerSystem", expected: "ComputerSystem.ComputerSystem"},
		{name: "no namespace", entityType: "ComputerSystem", expected: "ComputerSystem"},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			assert.Equal(t, tc.expected, getUnversionedEntityType(tc.entityType))
		})
	}
}

func TestGetEntityName(t *testing.T) {
	t.Parallel()
	assert.Equal(t, "ComputerSystem", getEntityName("ComputerSystem.v1_17_0.ComputerSystem"))
	assert.Equal(t, "SimpleName", getEntityName("SimpleName"))
}

func TestHasActionExamples(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name       string
		action     string
		files      []exampleFile
		expectReq  bool
		expectResp bool
	}{
		{
			name:   "matches by action name in file path",
			action: "ComputerSystem.v1_0_0.Reset",
			files: []exampleFile{
				newExampleFile("/tmp/computersystem-reset-request-example.json", `{}`),
				newExampleFile("/tmp/computersystem-reset-response-example.json", `{}`),
			},
			expectReq:  true,
			expectResp: true,
		},
		{
			name:   "matches unversioned action in content",
			action: "ComputerSystem.v1_0_0.Reset",
			files: []exampleFile{
				newExampleFile("/tmp/request-example.json", `{"Action":"ComputerSystem.Reset"}`),
			},
			expectReq:  true,
			expectResp: false,
		},
		{
			name:   "no matches",
			action: "ComputerSystem.v1_0_0.Reset",
			files: []exampleFile{
				newExampleFile("/tmp/thermal-request-example.json", `{"Action":"Thermal.Fan"}`),
			},
			expectReq:  false,
			expectResp: false,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			hasReq, hasResp := hasActionExamples(tc.action, tc.files)
			assert.Equal(t, tc.expectReq, hasReq)
			assert.Equal(t, tc.expectResp, hasResp)
		})
	}
}

func TestActionNeedsRequest(t *testing.T) {
	t.Parallel()

	assert.True(t, actionNeedsRequest(&csdl.Action{}))
	assert.False(t, actionNeedsRequest(&csdl.Action{Parameter: []*csdl.Parameter{{Name: "target"}}}))
	assert.True(t, actionNeedsRequest(&csdl.Action{Parameter: []*csdl.Parameter{{Name: "target"}, {Name: "ResetType"}}}))
}

func TestDerivesFromReferenceableMember(t *testing.T) {
	t.Parallel()

	entityIndex := map[string]*csdl.EntityType{
		"Example.v1_0_0.Direct":   {BaseType: "Resource.v1_0_0.ReferenceableMember"},
		"Example.v1_0_0.Indirect": {BaseType: "Example.v1_0_0.Direct"},
		"Example.v1_0_0.Normal":   {BaseType: "Resource.v1_0_0.Resource"},
	}

	assert.True(t, derivesFromReferenceableMember(
		"Example.v1_0_0.Direct", entityIndex,
		map[string]bool{}, map[string]struct{}{},
	))
	assert.True(t, derivesFromReferenceableMember(
		"Example.v1_0_0.Indirect", entityIndex,
		map[string]bool{}, map[string]struct{}{},
	))
	assert.False(t, derivesFromReferenceableMember(
		"Example.v1_0_0.Normal", entityIndex,
		map[string]bool{}, map[string]struct{}{},
	))
	assert.False(t, derivesFromReferenceableMember(
		"Example.v1_0_0.Unknown", entityIndex,
		map[string]bool{}, map[string]struct{}{},
	))

	cache := map[string]bool{"Cached.True": true}
	assert.True(t, derivesFromReferenceableMember("Cached.True", entityIndex, cache, map[string]struct{}{}))
}

func TestCreateTestsFromConfig_NoCSDLCache(t *testing.T) {
	t.Parallel()

	cfg := &config.Config{}
	list := &testsuite.List{}
	err := CreateTestsFromConfig(cfg, list)
	require.NoError(t, err)
	assert.Empty(t, list.Suites)
}

func TestMakeSearcherFromCache(t *testing.T) {
	t.Parallel()

	cache := &config.ExternalThreadSafeCache{}
	cache.Set("ComputerSystem_v1.xml", &csdl.Edmx{
		DataServices: csdl.DataServices{
			Schema: []*csdl.Schema{{Namespace: "ComputerSystem.v1_0_0"}},
		},
	}, nil)

	searcher, err := makeSearcherFromCache(cache)
	require.NoError(t, err)
	require.NotNil(t, searcher)
	assert.Contains(t, searcher.GetFiles(), "ComputerSystem_v1.xml")
}

//nolint:funlen
func TestCreateTestsFromConfig_SetupExecution(t *testing.T) {
	t.Parallel()

	t.Run("creates suites and passes when examples are present", func(t *testing.T) {
		t.Parallel()

		mockupDir := t.TempDir()
		examplesDir := filepath.Join(mockupDir, "DSP2046-examples")
		require.NoError(t, os.MkdirAll(examplesDir, 0o755)) //nolint:gosec

		require.NoError(t, os.WriteFile( //nolint:gosec
			filepath.Join(examplesDir, "computersystem-example.json"),
			[]byte(`{"@odata.type":"#ComputerSystem.v1_0_0.ComputerSystem"}`),
			0o644,
		))
		require.NoError(t, os.WriteFile( //nolint:gosec
			filepath.Join(examplesDir, "reset-request-example.json"),
			[]byte(`{"Action":"ComputerSystem.v1_0_0.Reset"}`),
			0o644,
		))

		edmx := &csdl.Edmx{DataServices: csdl.DataServices{Schema: []*csdl.Schema{{
			Namespace: "ComputerSystem.v1_0_0",
			EntityType: []*csdl.EntityType{{
				Name:     "ComputerSystem",
				BaseType: "Resource.v1_0_0.Resource",
			}},
			Action: []*csdl.Action{{
				Name:       "Reset",
				Parameter:  []*csdl.Parameter{{Name: "target"}, {Name: "ResetType"}},
				ReturnType: nil,
			}},
		}}}}

		cache := &config.ExternalThreadSafeCache{}
		cache.Set("ComputerSystem_v1.xml", edmx, io.NopCloser(strings.NewReader("")))

		cfg := &config.Config{CSDLCache: cache, MockupDirectory: mockupDir}
		list := &testsuite.List{}

		require.NoError(t, CreateTestsFromConfig(cfg, list))
		assert.Empty(t, list.Suites)

		status := list.Run()
		assert.Equal(t, int(testsuite.Success), status)
		require.Len(t, list.Suites, 1)
		assert.Equal(t, "ComputerSystem_v1.xml", list.Suites[0].Name)
		assert.Len(t, list.Suites[0].Cases, 2)
	})

	t.Run("single file filter excludes non matching csdl", func(t *testing.T) {
		t.Parallel()

		mockupDir := t.TempDir()
		examplesDir := filepath.Join(mockupDir, "DSP2046-examples")
		require.NoError(t, os.MkdirAll(examplesDir, 0o755)) //nolint:gosec

		cache := &config.ExternalThreadSafeCache{}
		cache.Set("ComputerSystem_v1.xml", &csdl.Edmx{DataServices: csdl.DataServices{}}, io.NopCloser(strings.NewReader("")))

		cfg := &config.Config{CSDLCache: cache, MockupDirectory: mockupDir, SingleFile: "Chassis_v1.xml"}
		list := &testsuite.List{}

		require.NoError(t, CreateTestsFromConfig(cfg, list))
		status := list.Run()
		assert.Equal(t, int(testsuite.Success), status)
		assert.Empty(t, list.Suites)
	})

	t.Run("missing examples directory creates no suites", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		cache.Set("ComputerSystem_v1.xml", &csdl.Edmx{DataServices: csdl.DataServices{}}, io.NopCloser(strings.NewReader("")))

		cfg := &config.Config{CSDLCache: cache, MockupDirectory: t.TempDir()}
		list := &testsuite.List{}

		require.NoError(t, CreateTestsFromConfig(cfg, list))
		status := list.Run()
		assert.Equal(t, int(testsuite.Success), status)
		assert.Empty(t, list.Suites)
	})
}
