/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package jsonschema_test

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/testing/jsonschema"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestValidatedSchemaReleasesContentAndCachesURI(t *testing.T) {
	t.Parallel()

	filename := filepath.Join(t.TempDir(), "Example.json")
	content := `{"$schema":"` + testRedfishSchema + `","payload":"` + strings.Repeat("x", 1<<20) + `"}`
	require.NoError(t, os.WriteFile(filename, []byte(content), 0o600))

	schema := jsonschema.NewSchema(filename)
	testContext := testsuite.NewTesting(t.Name(), &bytes.Buffer{})
	schema.ValidUTF8AndJSON(testContext)

	assert.True(t, schema.Validated())
	assert.Empty(t, schema.Content)
	assert.Empty(t, testContext.Errors)
	uri, ok := schema.SchemaURI()
	assert.True(t, ok)
	assert.Equal(t, testRedfishSchema, uri)
}

func TestSchemaURIFallsBackToInMemoryContent(t *testing.T) {
	t.Parallel()

	schema := jsonschema.NewSchema("in-memory.json")
	schema.Content = []byte(`{"$schema":"` + testRedfishSchema + `"}`)

	uri, ok := schema.SchemaURI()
	assert.True(t, ok)
	assert.Equal(t, testRedfishSchema, uri)
}
