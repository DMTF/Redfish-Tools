/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package utils_test

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/utils"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

//nolint:funlen // This is several test cases.
func TestGetPublishedSchemaList(t *testing.T) {
	t.Parallel()

	t.Run("successful request", func(t *testing.T) {
		t.Parallel()

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/html")
			_, _ = w.Write([]byte(`
				<html>
					<body>
						<a href="schema1.v1_0_0.json">Schema 1</a>
						<a href="schema2.v1_2_3.json">Schema 2</a>
						<a href="other.txt">Not a JSON</a>
					</body>
				</html>
			`))
		}))
		t.Cleanup(server.Close)

		result, err := utils.GetPublishedSchemaList(server.URL)
		require.NoError(t, err)
		require.NotNil(t, result)

		assert.Len(t, result, 2)
		assert.Contains(t, result, "schema1")
		assert.Contains(t, result, "schema2")

		schema1 := result["schema1"]
		assert.Equal(t, 1, schema1.Major)
		assert.Equal(t, 0, schema1.Minor)
		assert.Equal(t, 0, schema1.Errata)

		schema2 := result["schema2"]
		assert.Equal(t, 1, schema2.Major)
		assert.Equal(t, 2, schema2.Minor)
		assert.Equal(t, 3, schema2.Errata)
	})

	t.Run("HTTP error status", func(t *testing.T) {
		t.Parallel()

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
		}))
		defer server.Close()

		result, err := utils.GetPublishedSchemaList(server.URL)
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "http error 404")
	})

	t.Run("empty HTML", func(t *testing.T) {
		t.Parallel()

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/html")
			_, _ = w.Write([]byte("<html><body></body></html>"))
		}))
		defer server.Close()

		result, err := utils.GetPublishedSchemaList(server.URL)
		require.NoError(t, err)
		assert.Empty(t, result)
	})
}
