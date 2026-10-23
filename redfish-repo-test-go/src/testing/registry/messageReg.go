/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package registry

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"unicode/utf8"

	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

type MessageRegistry struct {
	Filename string
	Content  []byte
	JSON     map[string]any
}

var (
	errNotValidUTF8         = errors.New("file is not valid UTF-8")
	errNotJSONObject        = errors.New("file is not a JSON object")
	errNoRegistryPrefix     = errors.New("file does not have a RegistryPrefix")
	errNoRegistryVersion    = errors.New("file does not have a RegistryVersion")
	errFilenameNoMatch      = errors.New("filename does not match RegistryPrefix and RegistryVersion")
	errNoMessages           = errors.New("file does not have a Messages object")
	errInvalidMessageFormat = errors.New("file has invalid message format")
	errMissingRequiredField = errors.New("message is missing required field")
)

//nolint:gochecknoglobals
var RequiredMessageFields = []string{"Description", "LongDescription", "Message", "MessageSeverity"}

func NewMessageRegistry(filename string) *MessageRegistry {
	return &MessageRegistry{
		Filename: filename,
	}
}

func (m *MessageRegistry) ValidTest(t *testsuite.Testing) {
	content, err := os.ReadFile(m.Filename)
	if err != nil {
		t.Error(fmt.Errorf("failed to read file %s: %w", m.Filename, err))
		return
	}
	m.Content = content
	if !utf8.Valid(content) {
		t.Error(fmt.Errorf("file %s: %w", m.Filename, errNotValidUTF8))
		return
	}
	var result any
	if err := json.Unmarshal(content, &result); err != nil {
		t.Error(fmt.Errorf("file %s is not valid JSON: %w", m.Filename, err))
		return
	}
	obj, ok := result.(map[string]any)
	if !ok {
		t.Error(fmt.Errorf("file %s: %w", m.Filename, errNotJSONObject))
		return
	}
	m.JSON = obj
}

func (m *MessageRegistry) FilenameMatch(t *testsuite.Testing) {
	prefix, ok := m.JSON["RegistryPrefix"].(string)
	if !ok {
		t.Error(fmt.Errorf("file %s: %w", m.Filename, errNoRegistryPrefix))
		return
	}
	version, ok := m.JSON["RegistryVersion"].(string)
	if !ok {
		t.Error(fmt.Errorf("file %s: %w", m.Filename, errNoRegistryVersion))
		return
	}
	expectedFileName := prefix + "." + version + ".json"
	if filepath.Base(m.Filename) != expectedFileName {
		t.Error(fmt.Errorf(
			"file %s does not match expected filename %s: %w",
			filepath.Base(m.Filename), expectedFileName, errFilenameNoMatch,
		))
		return
	}
}

func (m *MessageRegistry) CheckRequiredMessageFields(t *testsuite.Testing) {
	messages, ok := m.JSON["Messages"].(map[string]any)
	if !ok {
		t.Error(fmt.Errorf("file %s: %w", m.Filename, errNoMessages))
		return
	}
	for _, message := range messages {
		messageMap, ok := message.(map[string]any)
		if !ok {
			t.Error(fmt.Errorf("file %s: %w", m.Filename, errInvalidMessageFormat))
			return
		}
		for _, field := range RequiredMessageFields {
			if _, ok := messageMap[field]; !ok {
				t.Error(fmt.Errorf(
					"message %s missing %s: %w",
					message, field, errMissingRequiredField,
				))
				return
			}
		}
	}
}
