/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package jsonschema_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/jsonschema"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

const (
	testOldStyleSchema = "http://redfish.dmtf.org/schemas/v1/redfish-schema.1.0.0.json"
	testRedfishSchema  = "http://redfish.dmtf.org/schemas/v1/redfish-schema-v1.json"
	testSchemaURIBase  = "http://redfish.dmtf.org/schemas/v1/"
)

//nolint:funlen
func TestCreateTestsFromConfig(t *testing.T) {
	t.Parallel()

	t.Run("EmptyJSONSchemaDirectorySkips", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{}
		list := &testsuite.List{}

		err := jsonschema.CreateTestsFromConfig(cfg, list)

		require.NoError(t, err)
		assert.Empty(t, list.Suites)
	})

	t.Run("SingleFileNonJSONSkips", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{
			JSONSchemaDirectory: t.TempDir(),
			SingleFile:          filepath.Join(t.TempDir(), "README.md"),
		}
		list := &testsuite.List{}

		err := jsonschema.CreateTestsFromConfig(cfg, list)

		require.NoError(t, err)
		assert.Empty(t, list.Suites)
	})

	t.Run("SingleFileJSONCreatesSuiteAndRuns", func(t *testing.T) {
		t.Parallel()

		schemaDir := t.TempDir()
		schemaFile := filepath.Join(schemaDir, "single-file-schema.json")
		require.NoError(t, os.WriteFile(schemaFile, []byte(`{"$schema":"`+testRedfishSchema+`"}`), 0o644)) //nolint:gosec

		cfg := &config.Config{
			JSONSchemaDirectory: schemaDir,
			SingleFile:          schemaFile,
		}
		list := &testsuite.List{}

		err := jsonschema.CreateTestsFromConfig(cfg, list)
		require.NoError(t, err)
		require.Len(t, list.Suites, 1)
		assert.Len(t, list.Suites[0].Cases, 2)

		status := list.Suites[0].Run()
		assert.Equal(t, testsuite.Success, status)
	})

	t.Run("MissingDirectorySkips", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{JSONSchemaDirectory: filepath.Join(t.TempDir(), "missing")}
		list := &testsuite.List{}

		err := jsonschema.CreateTestsFromConfig(cfg, list)

		require.NoError(t, err)
		assert.Empty(t, list.Suites)
	})

	t.Run("DirectoryCreatesSuiteAndCases", func(t *testing.T) {
		t.Parallel()

		schemaDir := t.TempDir()
		require.NoError(t, os.WriteFile(filepath.Join(schemaDir, "redfish-schema-v1.json"), []byte(`{"title":"schema"}`), 0o644))               //nolint:gosec
		require.NoError(t, os.WriteFile(filepath.Join(schemaDir, "ComputerSystem.json"), []byte(`{"$schema":"`+testRedfishSchema+`"}`), 0o644)) //nolint:gosec

		cfg := &config.Config{JSONSchemaDirectory: schemaDir}
		list := &testsuite.List{}

		err := jsonschema.CreateTestsFromConfig(cfg, list)
		require.NoError(t, err)
		require.Len(t, list.Suites, 1)
		assert.Equal(t, "JSON Schema files", list.Suites[0].Name)
		assert.Len(t, list.Suites[0].Cases, 2)

		status := list.Suites[0].Run()
		assert.Equal(t, testsuite.Success, status)
	})
}

func TestCreateTestsFromConfig_LoadValidation(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name    string
		content []byte
	}{
		{name: "InvalidUTF8", content: []byte{0xff, 0xfe, 0xfd}},
		{name: "InvalidJSON", content: []byte("{")},
		{name: "NonObjectJSON", content: []byte("[]")},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			schemaDir := t.TempDir()
			require.NoError(t, os.WriteFile(filepath.Join(schemaDir, "bad.json"), tc.content, 0o644)) //nolint:gosec

			cfg := &config.Config{JSONSchemaDirectory: schemaDir}
			list := &testsuite.List{}
			require.NoError(t, jsonschema.CreateTestsFromConfig(cfg, list))
			require.Len(t, list.Suites, 1)

			loadCase := findCaseBySuffix(t, list.Suites[0], "All files are UTF8 and JSON")
			status := loadCase.Run()

			assert.Equal(t, testsuite.Warning, status)
			require.NotEmpty(t, loadCase.Errors)
		})
	}
}

//nolint:funlen
func TestCreateTestsFromConfig_SchemaValidationRules(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name          string
		files         map[string]string
		expectWarning bool
	}{
		{
			name: "Non1Dot0AllowsDiscoveredRedfishSchema",
			files: map[string]string{
				"redfish-schema.2.0.0.json": `{"title":"schema"}`,
				"Example.json":              `{"$schema":"` + testSchemaURIBase + `redfish-schema.2.0.0.json"}`,
			},
			expectWarning: false,
		},
		{
			name: "Non1Dot0RejectsUnknownSchema",
			files: map[string]string{
				"Example.json": `{"$schema":"http://example.com/unknown.json"}`,
			},
			expectWarning: true,
		},
		{
			name: "Contains1Dot0RequiresOldStyle",
			files: map[string]string{
				"Example-1.0.2.json": `{"$schema":"` + testRedfishSchema + `"}`,
			},
			expectWarning: true,
		},
		{
			name: "Contains1Dot0AcceptsOldStyle",
			files: map[string]string{
				"Example-1.0.2.json": `{"$schema":"` + testOldStyleSchema + `"}`,
			},
			expectWarning: false,
		},
		{
			name: "MissingSchemaIsWarning",
			files: map[string]string{
				"Example.json": `{"title":"no schema"}`,
			},
			expectWarning: true,
		},
		{
			name: "NonStringSchemaIsWarning",
			files: map[string]string{
				"Example.json": `{"$schema":123}`,
			},
			expectWarning: true,
		},
		{
			name: "SkipsRedfishSchemaAndOdataFiles",
			files: map[string]string{
				"redfish-schema-v1.json": `{"title":"schema"}`,
				"odata.4.0.0.json":       `{"$schema":123}`,
				"Good.json":              `{"$schema":"` + testRedfishSchema + `"}`,
			},
			expectWarning: false,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			schemaDir := t.TempDir()
			for name, content := range tc.files {
				require.NoError(t, os.WriteFile(filepath.Join(schemaDir, name), []byte(content), 0o644)) //nolint:gosec
			}

			cfg := &config.Config{JSONSchemaDirectory: schemaDir}
			list := &testsuite.List{}
			require.NoError(t, jsonschema.CreateTestsFromConfig(cfg, list))
			require.Len(t, list.Suites, 1)

			schemaCase := findCaseBySuffix(t, list.Suites[0], "All files have required $schema")
			status := schemaCase.Run()

			if tc.expectWarning {
				assert.Equal(t, testsuite.Warning, status)
				require.NotEmpty(t, schemaCase.Errors)
			} else {
				assert.Equal(t, testsuite.Success, status)
				assert.Empty(t, schemaCase.Errors)
			}
		})
	}
}

func findCaseBySuffix(t *testing.T, suite *testsuite.Suite, testName string) *testsuite.Case {
	t.Helper()

	for _, c := range suite.Cases {
		if strings.HasSuffix(c.Name, "/"+testName) {
			return c
		}
	}
	t.Fatalf("test case %q not found in suite %q", testName, suite.Name)
	return nil
}
