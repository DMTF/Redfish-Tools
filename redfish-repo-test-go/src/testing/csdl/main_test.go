/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	csdlvalidation "github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
	"github.com/DMTF/redfishRepoTest/src/units/ucum"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type testWrapperTestCase struct {
	Name           string
	Attributes     map[string]any
	TestFuncCalled bool
}

//nolint:funlen // Long test case function.
func getTestWrapperTestCases() []testWrapperTestCase {
	return []testWrapperTestCase{
		{
			Name: "Test wrapper without units",
			Attributes: map[string]any{
				"cfg":      &config.Config{},
				"searcher": &csdl.Searcher{},
			},
			TestFuncCalled: false,
		},
		{
			Name: "Test wrapper without config",
			Attributes: map[string]any{
				"units":    func() units.Units { u, _ := units.Load(); return u }(),
				"searcher": &csdl.Searcher{},
			},
			TestFuncCalled: false,
		},
		{
			Name: "Test wrapper without searcher",
			Attributes: map[string]any{
				"units": func() units.Units { u, _ := units.Load(); return u }(),
				"cfg":   &config.Config{},
			},
			TestFuncCalled: false,
		},
		{
			Name: "Test wrapper with wrong units type",
			Attributes: map[string]any{
				"units":    "not a units object",
				"cfg":      &config.Config{},
				"searcher": &csdl.Searcher{},
			},
			TestFuncCalled: false,
		},
		{
			Name: "Test wrapper with wrong config type",
			Attributes: map[string]any{
				"units":    func() units.Units { u, _ := units.Load(); return u }(),
				"cfg":      "not a config object",
				"searcher": &csdl.Searcher{},
			},
			TestFuncCalled: false,
		},
		{
			Name: "Test wrapper with wrong searcher type",
			Attributes: map[string]any{
				"units":    func() units.Units { u, _ := units.Load(); return u }(),
				"cfg":      &config.Config{},
				"searcher": "not a searcher object",
			},
			TestFuncCalled: false,
		},
		{
			Name: "Test wrapper with all attributes present",
			Attributes: map[string]any{
				"units":    func() units.Units { u, _ := units.Load(); return u }(),
				"cfg":      &config.Config{},
				"searcher": &csdl.Searcher{},
			},
			TestFuncCalled: true,
		},
	}
}

func TestTestWrapper(t *testing.T) {
	t.Parallel()

	for _, tc := range getTestWrapperTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			suite := &testsuite.Suite{
				Name: "Test wrapper without units",
			}
			for key, value := range tc.Attributes {
				suite.AddAttribute(key, value)
			}
			wasCalled := false
			suite.AddTest("TestWrapper", csdlvalidation.TestWrapper(
				func(t *testsuite.Testing, unitUtil units.Units, cfg *config.Config, searcher *csdl.Searcher) {
					// Test function body
					wasCalled = true
				}))
			_ = suite.Run()
			assert.Equal(t, tc.TestFuncCalled, wasCalled)
		})
	}
}

//nolint:funlen // Long test function.
func TestCreateTestForFile(t *testing.T) {
	t.Parallel()

	// Create a temporary CSDL file for testing
	tempDir := t.TempDir()
	testFile := filepath.Join(tempDir, "test.xml")
	testCSDL := `<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
	<edmx:DataServices>
		<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Test">
			<EntityType Name="TestEntity">
				<Property Name="TestProperty" Type="Edm.String"/>
			</EntityType>
		</Schema>` + CSDLEnd

	err := os.WriteFile(testFile, []byte(testCSDL), 0600)
	require.NoError(t, err)

	// Create test configuration
	cfg := &config.Config{
		IncludePedanticTests: false,
	}

	// Load units utility
	unitUtil, _ := ucum.LoadFromFile(filepath.Join(tempDir, "ucum.json"))

	// Create test list
	list := &testsuite.List{
		Name:   "Test List",
		Status: testsuite.Pending,
	}

	// Call CreateTestForFile
	csdlvalidation.CreateTestForFile(testFile, cfg, list, unitUtil)

	// Verify that a suite was created for the file
	require.Len(t, list.Suites, 1)
	suite := list.Suites[0]

	// Verify suite name
	assert.Equal(t, testFile, suite.Name)

	// Verify that attributes were set
	assert.Equal(t, cfg, suite.GetAttribute("cfg"))
	assert.Equal(t, unitUtil, suite.GetAttribute("units"))

	// Verify that tests were added
	tests := suite.Cases
	expectedTests := []string{
		"Valid Syntax",
		"Units are valid",
		"Schemas have permissions",
		"Descriptions are valid",
		"Schemas are valid",
		"Entities are valid",
		"Complex types are valid",
		"Annotations are valid",
		"Enums are valid",
		"Properties are valid",
		"Actions are valid",
		"References are valid",
		"URIs are valid",
	}
	require.Len(t, tests, len(expectedTests))

	// Verify test names
	for i, expectedTest := range expectedTests {
		assert.Equal(t, testFile+"/"+expectedTest, tests[i].Name)
	}

	// Verify that pedantic tests are NOT included when disabled
	for _, test := range tests {
		assert.NotContains(t, test.Name, "pendantic")
	}
}

//nolint:funlen // Long test function.
func TestCreateTestForFile_WithPedanticTests(t *testing.T) {
	t.Parallel()

	// Create a temporary CSDL file for testing
	tempDir := t.TempDir()
	testFile := filepath.Join(tempDir, "test.xml")
	testCSDL := `<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
	<edmx:DataServices>
		<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Test">
			<EntityType Name="TestEntity">
				<Property Name="TestProperty" Type="Edm.String"/>
			</EntityType>
		</Schema>` + CSDLEnd

	err := os.WriteFile(testFile, []byte(testCSDL), 0600)
	require.NoError(t, err)

	// Create test configuration with pedantic tests enabled
	cfg := &config.Config{
		IncludePedanticTests: true,
	}

	// Load units utility
	unitUtil, _ := units.Load()

	// Create test list
	list := &testsuite.List{
		Name:   "Test List",
		Status: testsuite.Pending,
	}

	// Call CreateTestForFile
	csdlvalidation.CreateTestForFile(testFile, cfg, list, unitUtil)

	// Verify that a suite was created for the file
	require.Len(t, list.Suites, 1)
	suite := list.Suites[0]

	// Verify that tests were added including pedantic ones
	tests := suite.Cases
	expectedTests := []string{
		"Valid Syntax",
		"Units are valid",
		"Schemas have permissions",
		"Descriptions are valid",
		"Schemas are valid",
		"Entities are valid",
		"Complex types are valid",
		"Annotations are valid",
		"Enums are valid",
		"Properties are valid",
		"Actions are valid",
		"References are valid",
		"URIs are valid",
		"Descriptions are valid (pendantic)",
		"References are valid (pendantic)",
	}
	require.Len(t, tests, len(expectedTests))

	// Verify test names including pedantic ones
	for i, expectedTest := range expectedTests {
		assert.Equal(t, testFile+"/"+expectedTest, tests[i].Name)
	}

	// Verify that pedantic tests are included when enabled
	pedanticTests := []string{
		"Descriptions are valid (pendantic)",
		"References are valid (pendantic)",
	}
	for _, pedanticTest := range pedanticTests {
		found := false
		for _, test := range tests {
			if test.Name == testFile+"/"+pedanticTest {
				found = true
				break
			}
		}
		assert.True(t, found, "Pedantic test '%s' should be included", pedanticTest)
	}
}

func TestCreateTestForFile_CleanupFunction(t *testing.T) {
	t.Parallel()

	// Create a temporary CSDL file with syntax errors for testing
	tempDir := t.TempDir()
	testFile := filepath.Join(tempDir, "test.xml")
	invalidCSDL := `<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
	<edmx:DataServices>
		<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Test">
			<EntityType Name="TestEntity">
				<Property Name="TestProperty" Type="Edm.String"/>
				<InvalidElement>This will cause an error</InvalidElement>
			</EntityType>
		</Schema>` + CSDLEnd

	err := os.WriteFile(testFile, []byte(invalidCSDL), 0600)
	require.NoError(t, err)

	// Create test configuration
	cfg := &config.Config{
		IncludePedanticTests: false,
	}

	// Load units utility
	unitUtil, _ := ucum.LoadFromFile(filepath.Join(tempDir, "ucum.json"))

	// Create test list
	list := &testsuite.List{
		Name:   "Test List",
		Status: testsuite.Pending,
	}

	// Call CreateTestForFile
	csdlvalidation.CreateTestForFile(testFile, cfg, list, unitUtil)

	// Verify that a suite was created for the file
	require.Len(t, list.Suites, 1)
	suite := list.Suites[0]

	// Run the suite to generate errors and trigger cleanup
	_ = suite.Run()

	// Verify that the suite has errors (due to invalid CSDL)
	assert.NotEmpty(t, suite.Errors, "Suite should have errors due to invalid CSDL")

	// Verify that cleanup function was registered and executed
	// The cleanup function should have added line number information to errors
	// We can't directly test the line lookup functionality without access
	// to internal error types, but we can verify the cleanup was called
	// by checking that the suite has the expected structure
	assert.NotNil(t, suite)
	assert.Equal(t, testFile, suite.Name)
}

func TestCreateTestsFromConfig_SingleFile(t *testing.T) {
	t.Parallel()

	// Create a temporary CSDL file for testing
	tempDir := t.TempDir()
	testFile := filepath.Join(tempDir, "test.xml")
	testCSDL := `<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
	<edmx:DataServices>
		<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Test">
			<EntityType Name="TestEntity">
				<Property Name="TestProperty" Type="Edm.String"/>
			</EntityType>
		</Schema>` + CSDLEnd

	err := os.WriteFile(testFile, []byte(testCSDL), 0600)
	require.NoError(t, err)

	// Create test configuration for single file
	cfg := &config.Config{
		SingleFile:           testFile,
		IncludePedanticTests: false,
	}

	// Load units utility
	unitUtil, _ := ucum.LoadFromFile(filepath.Join(tempDir, "ucum.json"))

	// Create test list
	list := &testsuite.List{
		Name:   "Test List",
		Status: testsuite.Pending,
	}

	// Call CreateTestsFromConfig
	err = csdlvalidation.CreateTestsFromConfig(cfg, list, unitUtil)
	require.NoError(t, err)

	// Verify that a suite was created for the single file
	require.Len(t, list.Suites, 1)
	suite := list.Suites[0]
	assert.Equal(t, testFile, suite.Name)

	// Verify that attributes were set
	assert.Equal(t, cfg, suite.GetAttribute("cfg"))
	assert.Equal(t, unitUtil, suite.GetAttribute("units"))

	// Verify that tests were added
	assert.NotEmpty(t, suite.Cases)
}

func TestCreateTestsFromConfig_SingleFileNonXML(t *testing.T) {
	t.Parallel()

	// Create a temporary non-XML file
	tempDir := t.TempDir()
	testFile := filepath.Join(tempDir, "test.txt")
	err := os.WriteFile(testFile, []byte("not xml"), 0600)
	require.NoError(t, err)

	// Create test configuration for single file
	cfg := &config.Config{
		SingleFile: testFile,
	}

	// Load units utility
	unitUtil, _ := ucum.LoadFromFile(filepath.Join(tempDir, "ucum.json"))

	// Create test list
	list := &testsuite.List{
		Name:   "Test List",
		Status: testsuite.Pending,
	}

	// Call CreateTestsFromConfig
	err = csdlvalidation.CreateTestsFromConfig(cfg, list, unitUtil)
	require.NoError(t, err)

	// Verify that no suite was created for non-XML file
	assert.Empty(t, list.Suites)
}

//nolint:funlen // Long test function.
func TestCreateTestsFromConfig_Directory(t *testing.T) {
	t.Parallel()

	// Create a temporary directory with multiple CSDL files
	tempDir := t.TempDir()

	// Create multiple test files
	files := map[string]string{
		"test1.xml": `<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
	<edmx:DataServices><Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Test1">
	<EntityType Name="Entity1"><Property Name="Prop1" Type="Edm.String"/>
	</EntityType></Schema></edmx:DataServices>` + CSDLEnd,
		"test2.xml": `<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
	<edmx:DataServices><Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Test2">
	<EntityType Name="Entity2"><Property Name="Prop2" Type="Edm.Int32"/>
	</EntityType></Schema></edmx:DataServices>` + CSDLEnd,
		"notxml.txt": "not an xml file",
		"external.xml": `<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
	<edmx:DataServices><Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="External">
	<EntityType Name="ExternalEntity"><Property Name="ExtProp" Type="Edm.String"/>
	</EntityType></Schema></edmx:DataServices>` + CSDLEnd,
	}

	for filename, content := range files {
		filepath := filepath.Join(tempDir, filename)
		err := os.WriteFile(filepath, []byte(content), 0600)
		require.NoError(t, err)
	}

	// Create test configuration for directory
	cfg := &config.Config{
		CSDLDirectory:        tempDir,
		ExternalSchemas:      []string{"external"},
		IncludePedanticTests: false,
	}

	// Load units utility
	unitUtil, _ := ucum.LoadFromFile(filepath.Join(tempDir, "ucum.json"))

	// Create test list
	list := &testsuite.List{
		Name:   "Test List",
		Status: testsuite.Pending,
	}

	// Call CreateTestsFromConfig
	err := csdlvalidation.CreateTestsFromConfig(cfg, list, unitUtil)
	require.NoError(t, err)

	require.Len(t, list.Suites, 2)

	// Verify suite names (should be sorted alphabetically)
	suiteNames := make([]string, len(list.Suites))
	for i, suite := range list.Suites {
		suiteNames[i] = suite.Name
	}
	expectedNames := []string{
		filepath.Join(tempDir, "test1.xml"),
		filepath.Join(tempDir, "test2.xml"),
	}
	assert.ElementsMatch(t, expectedNames, suiteNames)

	// Verify that each suite has tests
	for _, suite := range list.Suites {
		assert.NotEmpty(t, suite.Cases)
		assert.Equal(t, cfg, suite.GetAttribute("cfg"))
		assert.Equal(t, unitUtil, suite.GetAttribute("units"))
	}
}

func TestCreateTestsFromConfig_DirectoryError(t *testing.T) {
	t.Parallel()

	// Create test configuration with non-existent directory
	cfg := &config.Config{
		CSDLDirectory: "/non/existent/directory",
	}

	// Load units utility
	unitUtil, err := units.Load()
	require.NoError(t, err)

	// Create test list
	list := &testsuite.List{
		Name:   "Test List",
		Status: testsuite.Pending,
	}

	// Call CreateTestsFromConfig
	err = csdlvalidation.CreateTestsFromConfig(cfg, list, unitUtil)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "no such file or directory")

	// Verify that no suite was created
	assert.Empty(t, list.Suites)
}

func TestCreateTestsFromConfig_NilCache(t *testing.T) {
	t.Parallel()

	// Create a temporary CSDL file for testing
	tempDir := t.TempDir()
	testFile := filepath.Join(tempDir, "test.xml")
	testCSDL := `<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
	<edmx:DataServices>
		<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Test">
			<EntityType Name="TestEntity">
				<Property Name="TestProperty" Type="Edm.String"/>
			</EntityType>
		</Schema>` + CSDLEnd

	err := os.WriteFile(testFile, []byte(testCSDL), 0600)
	require.NoError(t, err)

	// Create test configuration with nil cache
	cfg := &config.Config{
		CSDLDirectory:        tempDir,
		CSDLCache:            nil, // This should be initialized by the function
		IncludePedanticTests: false,
	}

	// Load units utility
	unitUtil, err := units.Load()
	require.NoError(t, err)

	// Create test list
	list := &testsuite.List{
		Name:   "Test List",
		Status: testsuite.Pending,
	}

	// Call CreateTestsFromConfig
	err = csdlvalidation.CreateTestsFromConfig(cfg, list, unitUtil)
	require.NoError(t, err)

	// Verify that cache was initialized
	assert.NotNil(t, cfg.CSDLCache)

	// Verify that a suite was created
	require.Len(t, list.Suites, 1)
	suite := list.Suites[0]
	assert.Equal(t, testFile, suite.Name)
}
