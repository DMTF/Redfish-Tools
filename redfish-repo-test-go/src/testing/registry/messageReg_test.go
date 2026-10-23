/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package registry_test

import (
	"errors"
	"os"
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src"
	"github.com/DMTF/redfishRepoTest/src/testing/registry"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewMessageRegistry(t *testing.T) {
	t.Parallel()

	filename := filepath.Join(t.TempDir(), "test.json")
	msgReg := registry.NewMessageRegistry(filename)

	assert.NotNil(t, msgReg)
	assert.Equal(t, filename, msgReg.Filename)
	assert.Nil(t, msgReg.Content)
	assert.Nil(t, msgReg.JSON)
}

//nolint:funlen
func TestMessageRegistry_ValidTest(t *testing.T) {
	t.Parallel()

	t.Run("ValidJSON", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "valid.json")
		content := []byte(`{"RegistryPrefix":"Base","RegistryVersion":"1.0.0"}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		testCase := testsuite.NewCase("test", msgReg.ValidTest, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Success, status)
		assert.Empty(t, testCase.Errors)
		assert.Equal(t, content, msgReg.Content)
		assert.NotNil(t, msgReg.JSON)
	})

	t.Run("FileReadError", func(t *testing.T) {
		t.Parallel()

		msgReg := registry.NewMessageRegistry(filepath.Join(t.TempDir(), "nonexistent.json"))
		testCase := testsuite.NewCase("test", msgReg.ValidTest, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "failed to read file")
	})

	t.Run("InvalidUTF8", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "invalid_utf8.json")
		content := []byte{0xff, 0xfe, 0xfd}                        // Invalid UTF-8
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		testCase := testsuite.NewCase("test", msgReg.ValidTest, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "not valid UTF-8")
	})

	t.Run("InvalidJSON", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "invalid_json.json")
		content := []byte(`{"invalid": json}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		testCase := testsuite.NewCase("test", msgReg.ValidTest, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "not valid JSON")
	})

	t.Run("NonObjectJSON", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "array.json")
		content := []byte(`[]`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		testCase := testsuite.NewCase("test", msgReg.ValidTest, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "not a JSON object")
	})
}

//nolint:funlen
func TestMessageRegistry_FilenameMatch(t *testing.T) {
	t.Parallel()

	t.Run("MatchingFilename", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{"RegistryPrefix":"Base","RegistryVersion":"1.0.0"}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Test filename matching
		testCase = testsuite.NewCase("test", msgReg.FilenameMatch, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Success, status)
		assert.Empty(t, testCase.Errors)
	})

	t.Run("MissingRegistryPrefix", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{"RegistryVersion":"1.0.0"}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Test filename matching
		testCase = testsuite.NewCase("test", msgReg.FilenameMatch, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "does not have a RegistryPrefix")
	})

	t.Run("MissingRegistryVersion", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{"RegistryPrefix":"Base"}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Test filename matching
		testCase = testsuite.NewCase("test", msgReg.FilenameMatch, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "does not have a RegistryVersion")
	})

	t.Run("NonStringRegistryPrefix", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{"RegistryPrefix":123,"RegistryVersion":"1.0.0"}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Test filename matching
		testCase = testsuite.NewCase("test", msgReg.FilenameMatch, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "does not have a RegistryPrefix")
	})

	t.Run("NonStringRegistryVersion", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{"RegistryPrefix":"Base","RegistryVersion":123}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Test filename matching
		testCase = testsuite.NewCase("test", msgReg.FilenameMatch, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "does not have a RegistryVersion")
	})

	t.Run("MismatchedFilename", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Wrong.1.0.0.json")
		content := []byte(`{"RegistryPrefix":"Base","RegistryVersion":"1.0.0"}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Test filename matching
		testCase = testsuite.NewCase("test", msgReg.FilenameMatch, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "does not match expected filename")
	})
}

//nolint:funlen
func TestMessageRegistry_CheckRequiredMessageFields(t *testing.T) {
	t.Parallel()

	t.Run("ValidMessages", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{
			"RegistryPrefix": "Base",
			"RegistryVersion": "1.0.0",
			"Messages": {
				"TestMessage": {
					"Description": "Test description",
					"LongDescription": "Test long description",
					"Message": "Test message",
					"MessageSeverity": "Warning"
				}
			}
		}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Test required fields
		testCase = testsuite.NewCase("test", msgReg.CheckRequiredMessageFields, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Success, status)
		assert.Empty(t, testCase.Errors)
	})

	t.Run("MissingMessagesObject", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{"RegistryPrefix":"Base","RegistryVersion":"1.0.0"}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Test required fields
		testCase = testsuite.NewCase("test", msgReg.CheckRequiredMessageFields, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "does not have a Messages object")
	})

	t.Run("InvalidMessageFormat", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{
			"RegistryPrefix": "Base",
			"RegistryVersion": "1.0.0",
			"Messages": {
				"TestMessage": "invalid format"
			}
		}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Test required fields
		testCase = testsuite.NewCase("test", msgReg.CheckRequiredMessageFields, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "invalid message format")
	})

	t.Run("MissingRequiredField", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{
			"RegistryPrefix": "Base",
			"RegistryVersion": "1.0.0",
			"Messages": {
				"TestMessage": {
					"Description": "Test description",
					"LongDescription": "Test long description",
					"Message": "Test message"
				}
			}
		}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		loadStatus := testCase.Run()
		assert.Equal(t, testsuite.Success, loadStatus)
		assert.NotNil(t, msgReg.JSON)

		// Test required fields
		testCase = testsuite.NewCase("test", msgReg.CheckRequiredMessageFields, nil)
		status := testCase.Run()

		assert.Equal(t, testsuite.Warning, status)
		require.NotEmpty(t, testCase.Errors)
		assert.Contains(t, testCase.Errors[0].Error(), "MessageSeverity")
		assert.Contains(t, testCase.Errors[0].Error(), "missing required field")
	})
}

func TestMessageRegistry_LookupErrorLines(t *testing.T) {
	t.Parallel()

	t.Run("LookupLineFromFile", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{
			"RegistryPrefix": "Base",
			"RegistryVersion": "1.0.0"
		}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Create a JSONSourceError with a path
		jsonErr := src.NewJSONSourceError(jsonFile, "RegistryPrefix", "test error", src.SeverityError, nil)
		msgReg.LookupErrorLines([]error{jsonErr})

		// Verify that the line number was looked up
		assert.Greater(t, jsonErr.Line(), 0)
	})

	t.Run("SkipNonJSONSourceError", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{"RegistryPrefix":"Base","RegistryVersion":"1.0.0"}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Create a regular error
		regularErr := errors.New("regular error")
		msgReg.LookupErrorLines([]error{regularErr})

		// Should not panic
		assert.Equal(t, "regular error", regularErr.Error())
	})

	t.Run("SkipWrongFilename", func(t *testing.T) {
		t.Parallel()

		jsonFile := filepath.Join(t.TempDir(), "Base.1.0.0.json")
		content := []byte(`{"RegistryPrefix":"Base","RegistryVersion":"1.0.0"}`)
		require.NoError(t, os.WriteFile(jsonFile, content, 0o644)) //nolint:gosec

		msgReg := registry.NewMessageRegistry(jsonFile)
		// Load the JSON first
		testCase := testsuite.NewCase("load", msgReg.ValidTest, nil)
		_ = testCase.Run()

		// Create a JSONSourceError with a different filename
		jsonErr := src.NewJSONSourceError("other.json", "RegistryPrefix", "test error", src.SeverityError, nil)
		msgReg.LookupErrorLines([]error{jsonErr})

		// Line should remain 0 since it's a different file
		assert.Equal(t, 0, jsonErr.Line())
	})
}
