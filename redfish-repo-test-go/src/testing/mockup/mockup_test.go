/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup_test

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/mockup"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

//nolint:funlen
func TestLoadRecursive(t *testing.T) {
	t.Parallel()

	t.Run("ReadDirErrorIsFatal", func(t *testing.T) {
		t.Parallel()

		m := mockup.NewMockup(filepath.Join(t.TempDir(), "missing"), &config.Config{})
		testCase := testsuite.NewCase("Load", m.Load, nil)

		testCase.Run()

		assert.Equal(t, testsuite.Failure, testCase.Status)
		require.Len(t, testCase.Errors, 1)
	})

	t.Run("ReportsInvalidUTF8File", func(t *testing.T) {
		t.Parallel()

		mockupDir := filepath.Join(t.TempDir(), "mockup")
		require.NoError(t, os.MkdirAll(filepath.Join(mockupDir, "Systems", "1"), 0o755)) //nolint:gosec
		require.NoError(t, os.WriteFile(                                                 //nolint:gosec
			filepath.Join(mockupDir, "Systems", "1", "index.json"),
			[]byte{0xff, 0xfe, 0xfd},
			0o644,
		))

		m := mockup.NewMockup(mockupDir, &config.Config{})
		tPrime := testsuite.NewTesting("Load", &bytes.Buffer{})

		m.LoadRecursive(tPrime, "")

		assert.Equal(t, testsuite.Warning, tPrime.Status)
		assert.False(t, m.PathValid("/redfish/v1/Systems/1"))
	})

	t.Run("ReportsInvalidJSONFile", func(t *testing.T) {
		t.Parallel()

		mockupDir := filepath.Join(t.TempDir(), "mockup")
		require.NoError(t, os.MkdirAll(filepath.Join(mockupDir, "Systems", "1"), 0o755)) //nolint:gosec
		require.NoError(t, os.WriteFile(                                                 //nolint:gosec
			filepath.Join(mockupDir, "Systems", "1", "index.json"),
			[]byte("{"),
			0o644,
		))

		m := mockup.NewMockup(mockupDir, &config.Config{})
		tPrime := testsuite.NewTesting("Load", &bytes.Buffer{})

		m.LoadRecursive(tPrime, "")

		assert.Equal(t, testsuite.Warning, tPrime.Status)
		assert.False(t, m.PathValid("/redfish/v1/Systems/1"))
	})

	t.Run("ReportsNonObjectJSON", func(t *testing.T) {
		t.Parallel()

		mockupDir := filepath.Join(t.TempDir(), "mockup")
		require.NoError(t, os.MkdirAll(filepath.Join(mockupDir, "Systems", "1"), 0o755)) //nolint:gosec
		require.NoError(t, os.WriteFile(                                                 //nolint:gosec
			filepath.Join(mockupDir, "Systems", "1", "index.json"),
			[]byte("[]"),
			0o644,
		))

		m := mockup.NewMockup(mockupDir, &config.Config{})
		tPrime := testsuite.NewTesting("Load", &bytes.Buffer{})

		m.LoadRecursive(tPrime, "")

		assert.Equal(t, testsuite.Warning, tPrime.Status)
		assert.False(t, m.PathValid("/redfish/v1/Systems/1"))
	})

	t.Run("LoadsRecursiveHappyPath", func(t *testing.T) {
		t.Parallel()

		mockupDir := filepath.Join(t.TempDir(), "mockup")
		require.NoError(t, os.MkdirAll(filepath.Join(mockupDir, "Systems", "1"), 0o755)) //nolint:gosec
		require.NoError(t, os.MkdirAll(filepath.Join(mockupDir, "Chassis"), 0o755))      //nolint:gosec
		require.NoError(t, os.WriteFile(                                                 //nolint:gosec
			filepath.Join(mockupDir, "Systems", "1", "index.json"),
			[]byte("{\"Id\":\"1\"}"),
			0o644,
		))
		require.NoError(t, os.WriteFile( //nolint:gosec
			filepath.Join(mockupDir, "Chassis", "1.json"),
			[]byte("{\"Id\":\"1\"}"),
			0o644,
		))

		m := mockup.NewMockup(mockupDir, &config.Config{})
		tPrime := testsuite.NewTesting("Load", &bytes.Buffer{})

		m.LoadRecursive(tPrime, "")

		assert.Equal(t, testsuite.Success, tPrime.Status)
		assert.True(t, m.PathValid("/redfish/v1/Systems/1"))
		assert.True(t, m.PathValid("/redfish/v1/Chassis/1.json"))
	})
}
