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

	"github.com/DMTF/redfishRepoTest/src"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

type MessageRegistry struct {
	Filename string
	Content  []byte
	JSON     map[string]any
}

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
		t.Error(src.NewJSONSourceError(m.Filename, "", "file is not valid UTF-8", src.SeverityError, nil))
		return
	}
	var result any
	if err := json.Unmarshal(content, &result); err != nil {
		t.Error(src.NewJSONSourceError(m.Filename, "", "file is not valid JSON", src.SeverityError, err))
		return
	}
	obj, ok := result.(map[string]any)
	if !ok {
		t.Error(src.NewJSONSourceError(m.Filename, "", "file is not a JSON object", src.SeverityError, nil))
		return
	}
	m.JSON = obj
}

func (m *MessageRegistry) FilenameMatch(t *testsuite.Testing) {
	prefix, ok := m.JSON["RegistryPrefix"].(string)
	if !ok {
		t.Error(src.NewJSONSourceError(m.Filename, "RegistryPrefix", "file does not have a RegistryPrefix", src.SeverityError, nil))
		return
	}
	version, ok := m.JSON["RegistryVersion"].(string)
	if !ok {
		t.Error(src.NewJSONSourceError(m.Filename, "RegistryVersion", "file does not have a RegistryVersion", src.SeverityError, nil))
		return
	}
	expectedFileName := prefix + "." + version + ".json"
	if filepath.Base(m.Filename) != expectedFileName {
		t.Error(src.NewJSONSourceError(
			m.Filename, "",
			fmt.Sprintf("filename does not match expected filename %s", expectedFileName),
			src.SeverityError, nil,
		))
		return
	}
}

func (m *MessageRegistry) CheckRequiredMessageFields(t *testsuite.Testing) {
	messages, ok := m.JSON["Messages"].(map[string]any)
	if !ok {
		t.Error(src.NewJSONSourceError(m.Filename, "Messages", "file does not have a Messages object", src.SeverityError, nil))
		return
	}
	for msgID, message := range messages {
		messageMap, ok := message.(map[string]any)
		if !ok {
			t.Error(src.NewJSONSourceError(
				m.Filename,
				fmt.Sprintf("Messages.%s", msgID),
				"file has invalid message format",
				src.SeverityError,
				nil,
			))
			return
		}
		for _, field := range RequiredMessageFields {
			if _, ok := messageMap[field]; !ok {
				t.Error(src.NewJSONSourceError(
					m.Filename,
					fmt.Sprintf("Messages.%s.%s", msgID, field),
					fmt.Sprintf("message is missing required field %s", field),
					src.SeverityError,
					nil,
				))
				return
			}
		}
	}
}

func (m *MessageRegistry) LookupErrorLines(errs []error) {
	for _, err := range errs {
		var jsonErr *src.JSONSourceError
		if errors.As(err, &jsonErr) {
			if jsonErr.FileName() != m.Filename {
				continue
			}
			if m.Content == nil {
				continue
			}
			file, err := os.Open(m.Filename)
			if err != nil {
				continue
			}
			jsonErr.LookupLineFromFile(file)
			_ = file.Close()
		}
	}
}
