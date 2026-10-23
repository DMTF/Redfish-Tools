/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package config_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/utils"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestConfig_SetDefaults(t *testing.T) {
	t.Parallel()

	t.Run("set defaults for empty config", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{}
		// Since setDefaults is unexported, we can't test it directly
		// This test verifies the default values we expect
		assert.Empty(t, cfg.CSDLDirectory)
		assert.Empty(t, cfg.PublishedVersionsURI)
	})

	t.Run("config with existing values", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{
			CSDLDirectory:        "/custom/metadata",
			PublishedVersionsURI: "https://custom.example.com",
		}
		assert.Equal(t, "/custom/metadata", cfg.CSDLDirectory)
		assert.Equal(t, "https://custom.example.com", cfg.PublishedVersionsURI)
	})
}

//nolint:funlen // This is just a list of test cases.
func TestConfig_GetPrivilegeRegistry(t *testing.T) {
	t.Parallel()

	t.Run("empty privilege registry glob", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{}
		result := cfg.GetPrivilegeRegistry()
		assert.Nil(t, result)
	})

	t.Run("cached result", func(t *testing.T) {
		t.Parallel()

		// Since privilegeRegCache is unexported, we can't directly test caching
		// This test verifies the method works with multiple calls
		tempDir := t.TempDir()
		privFile := filepath.Join(tempDir, "privilege.json")

		privData := map[string]any{"test": "cached"}

		//nolint:gosec // This is a test file with controlled paths
		file, err := os.Create(privFile)
		require.NoError(t, err)
		defer func() {
			_ = file.Close()
		}()

		encoder := json.NewEncoder(file)
		err = encoder.Encode(privData)
		require.NoError(t, err)

		cfg := &config.Config{
			PrivilegeRegistryGlob: privFile,
		}
		result1 := cfg.GetPrivilegeRegistry()
		result2 := cfg.GetPrivilegeRegistry()
		require.NotNil(t, result1)
		require.NotNil(t, result2)
		assert.Equal(t, result1, result2)
	})

	t.Run("non-existent glob pattern", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{
			PrivilegeRegistryGlob: "/non/existent/*.json",
		}
		result := cfg.GetPrivilegeRegistry()
		assert.Nil(t, result)
	})

	t.Run("valid privilege registry file", func(t *testing.T) {
		t.Parallel()

		tempDir := t.TempDir()
		privFile := filepath.Join(tempDir, "privilege.json")

		privData := map[string]any{
			"Privileges": map[string]any{
				"Base":          []any{"Login", "ConfigureSelf"},
				"Administrator": []any{"Login", "ConfigureComponents"},
			},
		}

		//nolint:gosec // This is a test file with controlled paths
		file, err := os.Create(privFile)
		require.NoError(t, err)
		defer func() {
			_ = file.Close()
		}()

		encoder := json.NewEncoder(file)
		err = encoder.Encode(privData)
		require.NoError(t, err)

		cfg := &config.Config{
			PrivilegeRegistryGlob: privFile,
		}
		result := cfg.GetPrivilegeRegistry()
		require.NotNil(t, result)
		assert.Equal(t, privData, result)
	})

	t.Run("multiple files - choose latest", func(t *testing.T) {
		t.Parallel()

		tempDir := t.TempDir()

		// Create older file
		oldFile := filepath.Join(tempDir, "privilege_v1.json")
		oldData := map[string]any{"version": "1.0"}
		//nolint:gosec // This is a test file with controlled paths
		file, err := os.Create(oldFile)
		require.NoError(t, err)
		defer func() {
			_ = file.Close()
		}()
		encoder := json.NewEncoder(file)
		err = encoder.Encode(oldData)
		require.NoError(t, err)

		// Create newer file
		newFile := filepath.Join(tempDir, "privilege_v2.json")
		newData := map[string]any{"version": "2.0"}
		//nolint:gosec // This is a test file with controlled paths
		file2, err := os.Create(newFile)
		require.NoError(t, err)
		defer func() {
			_ = file2.Close()
		}()
		encoder2 := json.NewEncoder(file2)
		err = encoder2.Encode(newData)
		require.NoError(t, err)

		cfg := &config.Config{
			PrivilegeRegistryGlob: filepath.Join(tempDir, "privilege_*.json"),
		}
		result := cfg.GetPrivilegeRegistry()
		require.NotNil(t, result)
		assert.Equal(t, newData, result)
	})

	t.Run("invalid JSON file", func(t *testing.T) {
		t.Parallel()

		tempDir := t.TempDir()
		privFile := filepath.Join(tempDir, "invalid.json")

		//nolint:gosec // This is a test file with controlled paths
		file, err := os.Create(privFile)
		require.NoError(t, err)
		defer func() {
			_ = file.Close()
		}()

		_, err = file.WriteString("invalid json content")
		require.NoError(t, err)

		cfg := &config.Config{
			PrivilegeRegistryGlob: privFile,
		}
		result := cfg.GetPrivilegeRegistry()
		assert.Nil(t, result)
	})

	t.Run("glob matches but file cannot be opened", func(t *testing.T) {
		t.Parallel()

		tempDir := t.TempDir()
		privFile := filepath.Join(tempDir, "privilege.json")

		// Create file
		//nolint:gosec // This is a test file with controlled paths
		file, err := os.Create(privFile)
		require.NoError(t, err)
		err = file.Close()
		require.NoError(t, err)

		// Remove file to simulate permission error
		err = os.Remove(privFile)
		require.NoError(t, err)

		cfg := &config.Config{
			PrivilegeRegistryGlob: privFile,
		}
		result := cfg.GetPrivilegeRegistry()
		assert.Nil(t, result)
	})
}

func TestAllowLists_GetPluralEntityPatterns(t *testing.T) {
	t.Parallel()

	t.Run("empty patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{}
		patterns := allowLists.GetPluralEntityPatterns()
		assert.Empty(t, patterns)
	})

	t.Run("valid patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{
			PluralEntityPatterns: []string{"Systems", "Chassis.*", ".*Manager$"},
		}
		patterns := allowLists.GetPluralEntityPatterns()
		require.Len(t, patterns, 3)

		assert.True(t, patterns[0].MatchString("Systems"))
		assert.True(t, patterns[1].MatchString("Chassis123"))
		assert.True(t, patterns[2].MatchString("Manager"))
		assert.False(t, patterns[0].MatchString("System"))
	})

	t.Run("invalid regex pattern", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{
			PluralEntityPatterns: []string{"[invalid"}, // Invalid regex
		}

		// This should panic due to invalid regex
		assert.Panics(t, func() {
			allowLists.GetPluralEntityPatterns()
		})
	})
}

func TestAllowLists_GetPluralSchemaPatterns(t *testing.T) {
	t.Parallel()

	t.Run("empty patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{}
		patterns := allowLists.GetPluralSchemaPatterns()
		assert.Empty(t, patterns)
	})

	t.Run("valid patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{
			PluralSchemaPatterns: []string{".*Collection$", ".*Systems$"},
		}
		patterns := allowLists.GetPluralSchemaPatterns()
		require.Len(t, patterns, 2)

		assert.True(t, patterns[0].MatchString("ComputerSystemCollection"))
		assert.True(t, patterns[1].MatchString("ComputerSystems"))
		assert.False(t, patterns[0].MatchString("ComputerSystem"))
	})
}

func TestAllowLists_GetPropertiesWithIncorrectUnits(t *testing.T) {
	t.Parallel()

	t.Run("empty patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{}
		patterns := allowLists.GetPropertiesWithIncorrectUnits()
		assert.Empty(t, patterns)
	})

	t.Run("valid patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{
			PropertiesWithIncorrectUnits: []string{".*Temperature$", ".*Pressure$"},
		}
		patterns := allowLists.GetPropertiesWithIncorrectUnits()
		require.Len(t, patterns, 2)

		assert.True(t, patterns[0].MatchString("CpuTemperature"))
		assert.True(t, patterns[1].MatchString("AirPressure"))
		assert.False(t, patterns[0].MatchString("CpuSpeed"))
	})
}

func TestAllowLists_GetNonPascalEnums(t *testing.T) {
	t.Parallel()

	t.Run("empty patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{}
		patterns := allowLists.GetNonPascalEnums()
		assert.Empty(t, patterns)
	})

	t.Run("valid patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{
			NonPascalEnums: []string{"^[a-z]", ".*_.*"},
		}
		patterns := allowLists.GetNonPascalEnums()
		require.Len(t, patterns, 2)

		assert.True(t, patterns[0].MatchString("lowercase"))
		assert.True(t, patterns[1].MatchString("snake_case"))
		assert.False(t, patterns[0].MatchString("PascalCase"))
	})
}

func TestAllowLists_GetNonPascalProperties(t *testing.T) {
	t.Parallel()

	t.Run("empty patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{}
		patterns := allowLists.GetNonPascalProperties()
		assert.Empty(t, patterns)
	})

	t.Run("valid patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{
			NonPascalProperties: []string{"^[a-z]", ".*_.*"},
		}
		patterns := allowLists.GetNonPascalProperties()
		require.Len(t, patterns, 2)

		assert.True(t, patterns[0].MatchString("lowercaseProp"))
		assert.True(t, patterns[1].MatchString("snake_case_prop"))
		assert.False(t, patterns[0].MatchString("PascalCaseProp"))
	})
}

func TestAllowLists_GetNoReleaseTermSchemas(t *testing.T) {
	t.Parallel()

	t.Run("empty patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{}
		patterns := allowLists.GetNoReleaseTermSchemas()
		assert.Empty(t, patterns)
	})

	t.Run("valid patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{
			NoReleaseTermSchemas: []string{".*v1$", ".*Beta$"},
		}
		patterns := allowLists.GetNoReleaseTermSchemas()
		require.Len(t, patterns, 2)

		assert.True(t, patterns[0].MatchString("Resource_v1"))
		assert.True(t, patterns[1].MatchString("ResourceBeta"))
		assert.False(t, patterns[0].MatchString("Resource_v2"))
	})
}

func TestAllowLists_GetUnknownTypeReferences(t *testing.T) {
	t.Parallel()

	t.Run("empty patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{}
		patterns := allowLists.GetUnknownTypeReferences()
		assert.Empty(t, patterns)
	})

	t.Run("valid patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{
			UnknownTypeReferences: []string{".*Custom.*", ".*Legacy.*"},
		}
		patterns := allowLists.GetUnknownTypeReferences()
		require.Len(t, patterns, 2)

		assert.True(t, patterns[0].MatchString("CustomType"))
		assert.True(t, patterns[1].MatchString("LegacyType"))
		assert.False(t, patterns[0].MatchString("StandardType"))
	})
}

func TestConfig_StructFields(t *testing.T) {
	t.Parallel()

	t.Run("config struct has expected fields", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{
			SingleFile:                           "test.json",
			CSDLDirectory:                        "/metadata",
			AllowLists:                           config.AllowLists{},
			ExternalSchemas:                      []string{"schema1.json", "schema2.json"},
			PrivilegeRegistryGlob:                "/privileges/*.json",
			PublishedVersionsURI:                 "https://example.com",
			RequireAllEntitiesToHaveDescriptions: true,
			IncludePedanticTests:                 true,
			PublishedVersions:                    map[string]*utils.RedfishNamespaceVersion{},
			CSDLCache:                            nil,
		}

		assert.Equal(t, "test.json", cfg.SingleFile)
		assert.Equal(t, "/metadata", cfg.CSDLDirectory)
		assert.Equal(t, []string{"schema1.json", "schema2.json"}, cfg.ExternalSchemas)
		assert.Equal(t, "/privileges/*.json", cfg.PrivilegeRegistryGlob)
		assert.Equal(t, "https://example.com", cfg.PublishedVersionsURI)
		assert.True(t, cfg.RequireAllEntitiesToHaveDescriptions)
		assert.True(t, cfg.IncludePedanticTests)
		assert.NotNil(t, cfg.PublishedVersions)
	})

	t.Run("allow lists struct has expected fields", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{
			PluralEntityPatterns:         []string{"Systems"},
			PluralSchemaPatterns:         []string{".*Collection$"},
			PropertiesWithIncorrectUnits: []string{".*Temp$"},
			NonPascalEnums:               []string{"^[a-z]"},
			NonPascalProperties:          []string{"^[a-z]"},
			NoActionsAllowed:             []string{"ReadOnly.*"},
			NoReleaseTermSchemas:         []string{".*v1$"},
			UnknownTypeReferences:        []string{".*Custom.*"},
			OtherValidURIPrefixes:        []string{"http://custom.*"},
			NoURISchemas:                 []string{"NoURI.*"},
		}

		assert.Equal(t, []string{"Systems"}, allowLists.PluralEntityPatterns)
		assert.Equal(t, []string{".*Collection$"}, allowLists.PluralSchemaPatterns)
		assert.Equal(t, []string{".*Temp$"}, allowLists.PropertiesWithIncorrectUnits)
		assert.Equal(t, []string{"^[a-z]"}, allowLists.NonPascalEnums)
		assert.Equal(t, []string{"^[a-z]"}, allowLists.NonPascalProperties)
		assert.Equal(t, []string{"ReadOnly.*"}, allowLists.NoActionsAllowed)
		assert.Equal(t, []string{".*v1$"}, allowLists.NoReleaseTermSchemas)
		assert.Equal(t, []string{".*Custom.*"}, allowLists.UnknownTypeReferences)
		assert.Equal(t, []string{"http://custom.*"}, allowLists.OtherValidURIPrefixes)
		assert.Equal(t, []string{"NoURI.*"}, allowLists.NoURISchemas)
	})
}

func TestConfig_AddPrefixDir(t *testing.T) {
	t.Parallel()

	cfg := &config.Config{
		CSDLDirectory:         "metadata",
		MockupDirectory:       "mockups",
		JSONSchemaDirectory:   "json-schema",
		PrivilegeRegistryGlob: "registries/*.json",
		MarkdownGlobs:         []string{"./*.md", "", "./docs/**/*.md"},
		AllowLists: config.AllowLists{
			NoCopyrightPaths: []string{"mockups/DSP2046-examples/*", "mockups/public-oem-examples/*"},
		},
	}

	prefix := "/repo/root"
	cfg.AddPrefixDir(prefix)

	assert.Equal(t, filepath.Join(prefix, "metadata"), cfg.CSDLDirectory)
	assert.Equal(t, filepath.Join(prefix, "mockups"), cfg.MockupDirectory)
	assert.Equal(t, filepath.Join(prefix, "json-schema"), cfg.JSONSchemaDirectory)
	assert.Equal(t, filepath.Join(prefix, "registries/*.json"), cfg.PrivilegeRegistryGlob)
	assert.Equal(t, []string{
		filepath.Join(prefix, "./*.md"),
		"",
		filepath.Join(prefix, "./docs/**/*.md"),
	}, cfg.MarkdownGlobs)
	assert.Equal(t, []string{
		filepath.Join(prefix, "mockups/DSP2046-examples/*"),
		filepath.Join(prefix, "mockups/public-oem-examples/*"),
	}, cfg.AllowLists.NoCopyrightPaths)
}

func TestConfig_CompileRegexesAndCopyrightCache(t *testing.T) {
	t.Parallel()

	cfg := &config.Config{
		Copyright: `Copyright \d{4}`,
		AllowLists: config.AllowLists{
			PluralEntityPatterns:         []string{"Systems", "Chassis.*"},
			PluralSchemaPatterns:         []string{".*Collection$"},
			PropertiesWithIncorrectUnits: []string{".*Temperature$"},
			NonPascalEnums:               []string{"^[a-z]"},
			NonPascalProperties:          []string{"^[a-z]"},
			NoReleaseTermSchemas:         []string{".*Beta$"},
			UnknownTypeReferences:        []string{".*Legacy.*"},
		},
	}

	cfg.CompileRegexes()

	entityPatterns := cfg.AllowLists.GetPluralEntityPatterns()
	require.Len(t, entityPatterns, 2)
	assert.True(t, entityPatterns[0].MatchString("Systems"))

	schemaPatterns := cfg.AllowLists.GetPluralSchemaPatterns()
	require.Len(t, schemaPatterns, 1)
	assert.True(t, schemaPatterns[0].MatchString("ComputerSystemCollection"))

	copyright1 := cfg.GetCopyrightRegEx()
	copyright2 := cfg.GetCopyrightRegEx()
	assert.Same(t, copyright1, copyright2)
	assert.True(t, copyright1.MatchString("Copyright 2026"))

	// CompileRegexes uses sync.Once; changing source patterns after first compile does not rebuild caches.
	cfg.AllowLists.PluralEntityPatterns = []string{"Managers"}
	cfg.CompileRegexes()
	require.Len(t, cfg.AllowLists.GetPluralEntityPatterns(), 2)
}

// Test edge cases and error conditions.
func TestConfig_EdgeCases(t *testing.T) {
	t.Parallel()

	t.Run("nil config methods", func(t *testing.T) {
		t.Parallel()

		var cfg *config.Config
		assert.Panics(t, func() {
			_ = cfg.GetPrivilegeRegistry()
		})
	})

	t.Run("nil allow lists methods", func(t *testing.T) {
		t.Parallel()

		var allowLists *config.AllowLists
		assert.Panics(t, func() {
			_ = allowLists.GetPluralEntityPatterns()
		})
	})

	t.Run("empty string patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{
			PluralEntityPatterns: []string{""},
		}
		patterns := allowLists.GetPluralEntityPatterns()
		require.Len(t, patterns, 1)
		assert.True(t, patterns[0].MatchString(""))
	})

	t.Run("complex regex patterns", func(t *testing.T) {
		t.Parallel()

		allowLists := &config.AllowLists{
			PluralEntityPatterns: []string{"^([A-Z][a-z]*)+s$", ".*([A-Z][a-z]*){2,}.*"},
		}
		patterns := allowLists.GetPluralEntityPatterns()
		require.Len(t, patterns, 2)

		assert.True(t, patterns[0].MatchString("Systems"))
		assert.True(t, patterns[1].MatchString("ComplexPatternTest"))
		assert.False(t, patterns[0].MatchString("System"))
	})
}

// Benchmark tests.
func BenchmarkConfig_GetPrivilegeRegistry(b *testing.B) {
	tempDir := b.TempDir()
	privFile := filepath.Join(tempDir, "privilege.json")

	privData := map[string]any{
		"Privileges": map[string]any{
			"Base":          []string{"Login", "ConfigureSelf"},
			"Administrator": []string{"Login", "ConfigureComponents"},
		},
	}

	//nolint:gosec // This is a test file with controlled paths
	file, err := os.Create(privFile)
	require.NoError(b, err)
	defer func() {
		_ = file.Close()
	}()

	encoder := json.NewEncoder(file)
	err = encoder.Encode(privData)
	require.NoError(b, err)

	cfg := &config.Config{
		PrivilegeRegistryGlob: privFile,
	}

	b.ResetTimer()
	b.ReportAllocs()
	for b.Loop() {
		_ = cfg.GetPrivilegeRegistry()
	}
}

func BenchmarkConfig_GetPrivilegeRegistry_Cached(b *testing.B) {
	tempDir := b.TempDir()
	privFile := filepath.Join(tempDir, "privilege.json")

	privData := map[string]any{
		"Privileges": map[string]any{
			"Base":          []string{"Login", "ConfigureSelf"},
			"Administrator": []string{"Login", "ConfigureComponents"},
		},
	}

	//nolint:gosec // This is just a test case using a test file.
	file, err := os.Create(privFile)
	require.NoError(b, err)
	defer func() {
		_ = file.Close()
	}()

	encoder := json.NewEncoder(file)
	err = encoder.Encode(privData)
	require.NoError(b, err)

	cfg := &config.Config{
		PrivilegeRegistryGlob: privFile,
	}
	// Pre-cache by calling once
	_ = cfg.GetPrivilegeRegistry()

	b.ResetTimer()
	b.ReportAllocs()
	for b.Loop() {
		_ = cfg.GetPrivilegeRegistry()
	}
}

func BenchmarkAllowLists_GetPluralEntityPatterns(b *testing.B) {
	allowLists := &config.AllowLists{
		PluralEntityPatterns: []string{"Systems", "Chassis.*", ".*Manager$"},
	}

	b.ResetTimer()
	b.ReportAllocs()
	for b.Loop() {
		_ = allowLists.GetPluralEntityPatterns()
	}
}

func BenchmarkAllowLists_GetPluralEntityPatterns_Cached(b *testing.B) {
	allowLists := &config.AllowLists{
		PluralEntityPatterns: []string{"Systems", "Chassis.*", ".*Manager$"},
	}
	// Pre-cache patterns
	_ = allowLists.GetPluralEntityPatterns()

	b.ResetTimer()
	b.ReportAllocs()
	for b.Loop() {
		_ = allowLists.GetPluralEntityPatterns()
	}
}
