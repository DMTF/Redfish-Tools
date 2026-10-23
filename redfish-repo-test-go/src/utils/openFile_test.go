/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package utils_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/utils"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type openFileTestCase struct {
	Name           string
	PathToTest     string
	PathToCreate   string
	ExpectedExists bool
}

func getOpenFileTestCases(tb testing.TB) []openFileTestCase {
	tb.Helper()
	tmpDir := tb.TempDir()
	return []openFileTestCase{
		{
			Name:           "Absolute Path Success",
			PathToTest:     filepath.Join(tmpDir, "test.txt"),
			PathToCreate:   filepath.Join(tmpDir, "test.txt"),
			ExpectedExists: true,
		},
		{
			Name:           "File Not Found",
			PathToTest:     "/non/existent/file.txt",
			PathToCreate:   "",
			ExpectedExists: false,
		},
		{
			Name:           "Relative Path Success",
			PathToTest:     "test.txt",
			PathToCreate:   "test.txt",
			ExpectedExists: true,
		},
		{
			Name:           "Relative Path Subdir Success",
			PathToTest:     "subdir/test.txt",
			PathToCreate:   "subdir/test.txt",
			ExpectedExists: true,
		},
	}
}

func (tc *openFileTestCase) setup(tb testing.TB) {
	tb.Helper()
	if tc.PathToCreate != "" {
		err := os.MkdirAll(filepath.Dir(tc.PathToCreate), 0750)
		if err != nil {
			tb.Fatalf("Failed to create directory: %v", err)
		}
		err = os.WriteFile(tc.PathToCreate, []byte("test content"), 0600)
		if err != nil {
			tb.Fatalf("Failed to create test file: %v", err)
		}
		tb.Cleanup(func() {
			_ = os.Remove(tc.PathToCreate)
			_ = os.RemoveAll(filepath.Dir(tc.PathToCreate))
		})
	}
}

//nolint:paralleltest // These manipulate the filesystem.
func TestOpenFile(t *testing.T) {
	for _, tc := range getOpenFileTestCases(t) {
		t.Run(tc.Name, func(t *testing.T) {
			tc.setup(t)
			file, err := utils.OpenFile(tc.PathToTest)
			if !tc.ExpectedExists {
				assert.Error(t, err)
				return
			}
			require.NoError(t, err)
			require.NotNil(t, file)
			_ = file.Close()
		})
	}
}

//nolint:paralleltest // These manipulate the filesystem.
func TestDoesFileExist(t *testing.T) {
	for _, tc := range getOpenFileTestCases(t) {
		t.Run(tc.Name, func(t *testing.T) {
			tc.setup(t)
			exists := utils.DoesFileExist(tc.PathToTest)
			assert.Equal(t, tc.ExpectedExists, exists)
		})
	}
}
