/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package registry_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/registry"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

//nolint:funlen
func TestCreateTestsFromConfig(t *testing.T) {
	t.Parallel()

	t.Run("EmptyMessageRegistryDirectorySkips", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{}
		list := &testsuite.List{}

		err := registry.CreateTestsFromConfig(cfg, list)

		require.NoError(t, err)
		assert.Empty(t, list.Suites)
	})

	t.Run("MissingDirectoryReturnsError", func(t *testing.T) {
		t.Parallel()

		cfg := &config.Config{
			MessageRegistryDirectory: filepath.Join(t.TempDir(), "missing"),
		}
		list := &testsuite.List{}

		err := registry.CreateTestsFromConfig(cfg, list)

		assert.Error(t, err)
		assert.Contains(t, err.Error(), "no such file or directory")
	})

	t.Run("DirectoryCreatesSuiteAndCases", func(t *testing.T) {
		t.Parallel()

		registryDir := t.TempDir()
		require.NoError(t, os.WriteFile(filepath.Join(registryDir, "Base.1.0.0.json"), []byte(`{"RegistryPrefix":"Base","RegistryVersion":"1.0.0"}`), 0o644)) //nolint:gosec
		require.NoError(t, os.WriteFile(filepath.Join(registryDir, "Test.1.0.0.json"), []byte(`{"RegistryPrefix":"Test","RegistryVersion":"1.0.0"}`), 0o644)) //nolint:gosec

		cfg := &config.Config{MessageRegistryDirectory: registryDir}
		list := &testsuite.List{}

		err := registry.CreateTestsFromConfig(cfg, list)
		require.NoError(t, err)
		require.Len(t, list.Suites, 2)

		// Check that each suite has the correct name and tests
		for _, suite := range list.Suites {
			assert.Contains(t, suite.Name, ".json")
			require.Len(t, suite.Cases, 2)
			assert.Contains(t, suite.Cases[0].Name, "Valid UTF8 and JSON")
			assert.Contains(t, suite.Cases[1].Name, "Filename and Data match")
		}
	})

	t.Run("SkipsPrivilegeRegistryFiles", func(t *testing.T) {
		t.Parallel()

		registryDir := t.TempDir()
		require.NoError(t, os.WriteFile(filepath.Join(registryDir, "Base.1.0.0.json"), []byte(`{}`), 0o644))              //nolint:gosec
		require.NoError(t, os.WriteFile(filepath.Join(registryDir, "PrivilegeRegistry.1.0.0.json"), []byte(`{}`), 0o644)) //nolint:gosec

		cfg := &config.Config{MessageRegistryDirectory: registryDir}
		list := &testsuite.List{}

		err := registry.CreateTestsFromConfig(cfg, list)
		require.NoError(t, err)
		require.Len(t, list.Suites, 1)
		assert.Equal(t, filepath.Join(registryDir, "Base.1.0.0.json"), list.Suites[0].Name)
	})

	t.Run("SkipsNonJSONFiles", func(t *testing.T) {
		t.Parallel()

		registryDir := t.TempDir()
		require.NoError(t, os.WriteFile(filepath.Join(registryDir, "Base.1.0.0.json"), []byte(`{}`), 0o644)) //nolint:gosec
		require.NoError(t, os.WriteFile(filepath.Join(registryDir, "readme.txt"), []byte("readme"), 0o644))  //nolint:gosec
		require.NoError(t, os.Mkdir(filepath.Join(registryDir, "subdir"), 0o755))                            //nolint:gosec

		cfg := &config.Config{MessageRegistryDirectory: registryDir}
		list := &testsuite.List{}

		err := registry.CreateTestsFromConfig(cfg, list)
		require.NoError(t, err)
		require.Len(t, list.Suites, 1)
		assert.Equal(t, filepath.Join(registryDir, "Base.1.0.0.json"), list.Suites[0].Name)
	})
}

func TestCreateTestsForDirectory(t *testing.T) {
	t.Parallel()

	t.Run("ValidDirectory", func(t *testing.T) {
		t.Parallel()

		registryDir := t.TempDir()
		require.NoError(t, os.WriteFile(filepath.Join(registryDir, "Test.1.0.0.json"), []byte(`{"RegistryPrefix":"Test","RegistryVersion":"1.0.0"}`), 0o644)) //nolint:gosec

		list := &testsuite.List{}
		err := registry.CreateTestsForDirectory(registryDir, list)

		require.NoError(t, err)
		require.Len(t, list.Suites, 1)
	})

	t.Run("EmptyDirectory", func(t *testing.T) {
		t.Parallel()

		registryDir := t.TempDir()
		list := &testsuite.List{}
		err := registry.CreateTestsForDirectory(registryDir, list)

		require.NoError(t, err)
		assert.Empty(t, list.Suites)
	})

	t.Run("DirectoryReadError", func(t *testing.T) {
		t.Parallel()

		// Create a file instead of a directory to cause a read error
		file := filepath.Join(t.TempDir(), "not_a_dir")
		require.NoError(t, os.WriteFile(file, []byte("not a directory"), 0o644)) //nolint:gosec

		list := &testsuite.List{}
		err := registry.CreateTestsForDirectory(file, list)

		assert.Error(t, err)
	})
}
