/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/mockup"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

//nolint:funlen
func TestTestWrapper(t *testing.T) {
	t.Parallel()

	t.Run("NoJSON", func(t *testing.T) {
		t.Parallel()

		wrapped := mockup.TestWrapper(func(_ *testsuite.Testing, _ map[string]any, _ *config.Config, _ map[string]*csdl.Type) {
			t.Fatal("inner test should not run")
		})

		suite := &testsuite.Suite{}
		suite.AddAttribute("cfg", &config.Config{})
		suite.AddAttribute("typeMap", map[string]*csdl.Type{})

		testCase := testsuite.NewCase("Test", wrapped, suite)
		testCase.Run()

		assert.Equal(t, testsuite.Failure, testCase.Status)
	})

	t.Run("NoConfig", func(t *testing.T) {
		t.Parallel()

		wrapped := mockup.TestWrapper(func(_ *testsuite.Testing, _ map[string]any, _ *config.Config, _ map[string]*csdl.Type) {
			t.Fatal("inner test should not run")
		})

		suite := &testsuite.Suite{}
		suite.AddAttribute("json", map[string]any{})
		suite.AddAttribute("typeMap", map[string]*csdl.Type{})

		testCase := testsuite.NewCase("Test", wrapped, suite)
		testCase.Run()

		assert.Equal(t, testsuite.Failure, testCase.Status)
	})

	t.Run("NoTypeMap", func(t *testing.T) {
		t.Parallel()

		wrapped := mockup.TestWrapper(func(_ *testsuite.Testing, _ map[string]any, _ *config.Config, _ map[string]*csdl.Type) {
			t.Fatal("inner test should not run")
		})

		suite := &testsuite.Suite{}
		suite.AddAttribute("json", map[string]any{})
		suite.AddAttribute("cfg", &config.Config{})

		testCase := testsuite.NewCase("Test", wrapped, suite)
		testCase.Run()

		assert.Equal(t, testsuite.Failure, testCase.Status)
	})

	t.Run("PassesAttributesToWrappedFunction", func(t *testing.T) {
		t.Parallel()

		expectedJSON := map[string]any{"Name": "System1"}
		expectedCfg := &config.Config{}
		expectedTypeMap := map[string]*csdl.Type{"Test.Type": {}}

		called := false
		wrapped := mockup.TestWrapper(func(_ *testsuite.Testing, content map[string]any, cfg *config.Config, typeMap map[string]*csdl.Type) {
			called = true
			assert.Equal(t, expectedJSON, content)
			assert.Same(t, expectedCfg, cfg)
			assert.Equal(t, expectedTypeMap, typeMap)
		})

		suite := &testsuite.Suite{}
		suite.AddAttribute("json", expectedJSON)
		suite.AddAttribute("cfg", expectedCfg)
		suite.AddAttribute("typeMap", expectedTypeMap)

		testCase := testsuite.NewCase("Test", wrapped, suite)
		testCase.Run()

		assert.Equal(t, testsuite.Success, testCase.Status)
		assert.True(t, called)
	})
}

func TestCreateTestForDirectoryCleanupIsCalled(t *testing.T) {
	t.Parallel()

	mockupDir := filepath.Join(t.TempDir(), "cleanup-mockup")
	require.NoError(t, os.MkdirAll(filepath.Join(mockupDir, "Systems", "1"), 0o755)) //nolint:gosec
	require.NoError(t, os.WriteFile(                                                 //nolint:gosec
		filepath.Join(mockupDir, "Systems", "1", "index.json"),
		[]byte("{\n  \"Name\": \"System1\"\n}\n"),
		0o644,
	))

	list := &testsuite.List{}
	err := mockup.CreateTestForDirectory(mockupDir, &config.Config{}, list)
	require.NoError(t, err)
	require.Len(t, list.Suites, 1)

	suite := list.Suites[0]
	require.NotEmpty(t, suite.Cases)

	var injectedErr *src.JSONSourceError
	suite.AddTest("InjectedJSONError", func(t *testsuite.Testing) {
		injectedErr = src.NewJSONSourceError(
			filepath.Join(mockupDir, "Systems", "1", "index.json"),
			"Name",
			"Injected error for cleanup validation",
			src.SeverityWarning,
			nil,
		)
		t.Error(injectedErr)
	})

	injectedCase := suite.Cases[len(suite.Cases)-1]
	suite.Cases = []*testsuite.Case{suite.Cases[0], injectedCase}

	suite.Run()

	require.NotNil(t, injectedErr)
	assert.Positive(t, injectedErr.Line())
}

//nolint:funlen
func TestCreateTestsFromConfig(t *testing.T) {
	t.Parallel()

	t.Run("NilCSDLCacheReturnsWithoutSuites", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{MockupDirectory: t.TempDir()}
		list := &testsuite.List{}

		err := mockup.CreateTestsFromConfig(cfg, list)

		assert.NoError(t, err)
		assert.Empty(t, list.Suites)
	})

	t.Run("SingleFileNonJSONSkipsMockupSuiteCreation", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{
			CSDLCache:       &config.ExternalThreadSafeCache{},
			MockupDirectory: t.TempDir(),
			SingleFile:      "README.md",
		}
		list := &testsuite.List{}

		err := mockup.CreateTestsFromConfig(cfg, list)

		assert.NoError(t, err)
		assert.Empty(t, list.Suites)
	})

	t.Run("ReturnsErrorWhenMockupDirectoryMissing", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{
			CSDLCache:       &config.ExternalThreadSafeCache{},
			MockupDirectory: filepath.Join(t.TempDir(), "missing"),
		}
		list := &testsuite.List{}

		err := mockup.CreateTestsFromConfig(cfg, list)

		assert.Error(t, err)
	})

	t.Run("CreatesSuitesForMockupDirectories", func(t *testing.T) {
		t.Parallel()

		mockupRoot := t.TempDir()
		publicDir := filepath.Join(mockupRoot, "example-public-mockup")
		privateDir := filepath.Join(mockupRoot, "DSP2046-examples")
		assert.NoError(t, os.Mkdir(publicDir, 0o755))  //nolint:gosec
		assert.NoError(t, os.Mkdir(privateDir, 0o755)) //nolint:gosec

		cfg := &config.Config{
			CSDLCache:       &config.ExternalThreadSafeCache{},
			MockupDirectory: mockupRoot,
		}
		list := &testsuite.List{}

		err := mockup.CreateTestsFromConfig(cfg, list)

		assert.NoError(t, err)
		if assert.Len(t, list.Suites, 2) {
			suitesByName := map[string]*testsuite.Suite{}
			for _, suite := range list.Suites {
				suitesByName[suite.Name] = suite
			}

			if assert.Contains(t, suitesByName, "example-public-mockup") {
				assert.Len(t, suitesByName["example-public-mockup"].Cases, 5)
			}
			if assert.Contains(t, suitesByName, "DSP2046-examples") {
				assert.Len(t, suitesByName["DSP2046-examples"].Cases, 4)
			}
		}
	})

	t.Run("SetupFunctionIsCalledOnListRun", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{
			CSDLCache:       &config.ExternalThreadSafeCache{},
			MockupDirectory: t.TempDir(),
		}
		list := &testsuite.List{}
		suite := list.AddSuite("manual-suite")

		err := mockup.CreateTestsFromConfig(cfg, list)
		assert.NoError(t, err)

		assert.Nil(t, suite.GetAttribute("typeMap"))
		assert.Nil(t, suite.GetAttribute("searcher"))

		list.Run()

		_, ok := suite.GetAttribute("typeMap").(map[string]*csdl.Type)
		assert.True(t, ok)
		_, ok = suite.GetAttribute("searcher").(*csdl.Searcher)
		assert.True(t, ok)
	})
}
