/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package jsonschema

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

var (
	errMissingSchemaDollar = errors.New("missing or non-string $schema")
	errInvalidSchemaOld    = errors.New("invalid $schema, expected old-style schema URI")
	errInvalidSchemaURI    = errors.New("invalid $schema, expected redfish-schema URI")
)

const (
	oldStyleSchema   = "http://redfish.dmtf.org/schemas/v1/redfish-schema.1.0.0.json"
	redfishSchemaURI = "http://redfish.dmtf.org/schemas/v1/redfish-schema-v1.json"
	schemaURIBase    = "http://redfish.dmtf.org/schemas/v1/"
)

//nolint:cyclop,funlen
func CreateTestsFromConfig(cfg *config.Config, list *testsuite.List) error {
	if cfg.SingleFile != "" {
		if !strings.HasSuffix(cfg.SingleFile, ".json") {
			return nil
		}
		suite := list.AddSuite(filepath.Base(cfg.SingleFile))
		schema := NewSchema(cfg.SingleFile)
		suite.AddTest("File is UTF8 and JSON", func(t *testsuite.Testing) {
			schema.ValidUTF8AndJSON(t)
		})
		suite.AddTest("File has required $schema", func(t *testsuite.Testing) {
			// Ensure the file is loaded first
			if !schema.Validated() {
				schema.ValidUTF8AndJSON(t)
			}
			validateSchemaDecls(t, []*Schema{schema})
		})
		return nil
	}

	if cfg.JSONSchemaDirectory == "" {
		return nil
	}

	entries, err := os.ReadDir(cfg.JSONSchemaDirectory)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}

	fileList := make([]string, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		if filepath.Ext(entry.Name()) != ".json" {
			continue
		}
		fileList = append(fileList, filepath.Join(cfg.JSONSchemaDirectory, entry.Name()))
	}

	if len(fileList) == 0 {
		return nil
	}

	suite := list.AddSuite("JSON Schema files")
	schemaFiles := make([]*Schema, len(fileList))
	for i, file := range fileList {
		schemaFiles[i] = NewSchema(file)
	}

	suite.AddTest("All files are UTF8 and JSON", func(t *testsuite.Testing) {
		cfg.IOWorkerPool.Run(len(schemaFiles), func(i int) {
			schemaFiles[i].ValidUTF8AndJSON(t)
		})
	})
	suite.AddTest("All files have required $schema", func(t *testsuite.Testing) {
		// Ensure all files are loaded first
		for _, schema := range schemaFiles {
			if !schema.Validated() {
				schema.ValidUTF8AndJSON(t)
			}
		}
		validateSchemaDecls(t, schemaFiles)
	})
	return nil
}

//nolint:cyclop
func validateSchemaDecls(t *testsuite.Testing, files []*Schema) {
	validSchemas := map[string]struct{}{
		redfishSchemaURI: {},
	}
	for _, file := range files {
		baseName := filepath.Base(file.Filename)
		if file.IsRedfishSchema() {
			validSchemas[schemaURIBase+baseName] = struct{}{}
		}
	}

	for _, file := range files {
		baseName := filepath.Base(file.Filename)
		if baseName == "redfish-schema.1.0.0.json" || file.IsRedfishSchema() ||
			baseName == "odata.4.0.0.json" {
			continue
		}

		schemaVal, ok := file.SchemaURI()
		if !ok {
			t.Error(fmt.Errorf("file %s: %w", file.Filename, errMissingSchemaDollar))
			continue
		}

		if strings.Contains(baseName, "1.0") {
			if !strings.EqualFold(schemaVal, oldStyleSchema) {
				t.Error(fmt.Errorf("file %s has $schema %q: %w", file.Filename, schemaVal, errInvalidSchemaOld))
			}
			continue
		}

		if _, ok := validSchemas[schemaVal]; !ok {
			t.Error(fmt.Errorf("file %s has $schema %q: %w", file.Filename, schemaVal, errInvalidSchemaURI))
		}
	}
}
