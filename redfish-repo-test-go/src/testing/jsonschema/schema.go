/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package jsonschema

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"unicode/utf8"

	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

var (
	errNotValidUTF8  = errors.New("file is not valid UTF-8")
	errNotValidJSON  = errors.New("file is not valid JSON")
	errNotJSONObject = errors.New("file is not a JSON object")
)

type Schema struct {
	Filename  string
	Content   []byte
	validated bool
	schemaURI string
	schemaOK  bool
	uriCached bool
}

func NewSchema(filename string) *Schema {
	return &Schema{
		Filename: filename,
	}
}

func (s *Schema) ValidUTF8AndJSON(t *testsuite.Testing) {
	content, err := os.ReadFile(s.Filename)
	if err != nil {
		t.Error(fmt.Errorf("failed to read file %s: %w", s.Filename, err))
		return
	}
	if !utf8.Valid(content) {
		t.Error(fmt.Errorf("file %s: %w", s.Filename, errNotValidUTF8))
		return
	}
	if !json.Valid(content) {
		t.Error(fmt.Errorf("file %s: %w", s.Filename, errNotValidJSON))
		return
	}
	// json.Valid confirmed syntax; verify the top-level value is an object.
	for _, b := range content {
		switch b {
		case ' ', '\t', '\n', '\r':
			continue
		case '{':
			s.schemaURI, s.schemaOK = extractSchemaURI(content)
			s.uriCached = true
			s.validated = true
			return
		default:
			t.Error(fmt.Errorf("file %s: %w", s.Filename, errNotJSONObject))
			return
		}
	}
}

// Validated reports whether ValidUTF8AndJSON has completed successfully.
func (s *Schema) Validated() bool {
	return s.validated
}

// SchemaURI returns the cached "$schema" value, extracting it from Content
// for callers that construct an in-memory Schema directly.
func (s *Schema) SchemaURI() (string, bool) {
	if s.uriCached {
		return s.schemaURI, s.schemaOK
	}

	s.schemaURI, s.schemaOK = extractSchemaURI(s.Content)
	s.uriCached = true
	return s.schemaURI, s.schemaOK
}

func extractSchemaURI(content []byte) (string, bool) {
	dec := json.NewDecoder(bytes.NewReader(content))
	// Consume opening '{'
	tok, err := dec.Token()
	if err != nil {
		return "", false
	}
	if delim, ok := tok.(json.Delim); !ok || delim != '{' {
		return "", false
	}
	for dec.More() {
		// Read key
		tok, err = dec.Token()
		if err != nil {
			return "", false
		}
		key, ok := tok.(string)
		if !ok {
			return "", false
		}
		if key == "$schema" {
			tok, err = dec.Token()
			if err != nil {
				return "", false
			}
			val, ok := tok.(string)
			return val, ok
		}
		// Skip value we don't care about
		var skip json.RawMessage
		if err := dec.Decode(&skip); err != nil {
			return "", false
		}
	}
	return "", false
}

func (s *Schema) IsRedfishSchema() bool {
	return strings.HasPrefix(filepath.Base(s.Filename), "redfish-schema")
}
