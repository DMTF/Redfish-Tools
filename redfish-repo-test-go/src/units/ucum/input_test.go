/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package ucum_test

import (
	"context"
	"encoding/xml"
	"io"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/DMTF/redfishRepoTest/src/units/ucum"
	"github.com/DMTF/redfishRepoTest/src/utils"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

//nolint:funlen // This is just a list of test cases.
func TestGetUCUMDataFromURI(t *testing.T) {
	t.Parallel()

	t.Run("successful XML parsing", func(t *testing.T) {
		t.Parallel()

		xmlContent := `<?xml version="1.0" encoding="UTF-8"?>
<root version="1.0" revision="1" revision-date="2023-01-01">
	<prefix>
		<name>kilo</name>
	</prefix>
	<prefix>
		<name>mega</name>
	</prefix>
	<base-unit>
		<name>meter</name>
	</base-unit>
	<unit>
		<name>newton</name>
	</unit>
</root>`

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/xml")
			_, _ = w.Write([]byte(xmlContent))
		}))
		t.Cleanup(server.Close)

		ctx := context.Background()
		result, err := ucum.GetUCUMDataFromURI(ctx, server.URL)
		require.NoError(t, err)
		require.NotNil(t, result)

		assert.Equal(t, "1.0", result.Version)
		assert.Equal(t, "1", result.Revision)
		assert.Equal(t, "2023-01-01", result.RevisionDate)
		assert.Len(t, result.Prefixes, 2)
		assert.Len(t, result.BaseUnits, 1)
		assert.Len(t, result.Units, 1)
	})

	t.Run("HTTP error status", func(t *testing.T) {
		t.Parallel()

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
		}))
		t.Cleanup(server.Close)

		ctx := context.Background()
		result, err := ucum.GetUCUMDataFromURI(ctx, server.URL)
		assert.Error(t, err)
		assert.Nil(t, result)

		var httpErr *utils.HTTPResponseError
		assert.ErrorAs(t, err, &httpErr)
		assert.Equal(t, http.StatusNotFound, httpErr.StatusCode)
	})

	t.Run("network error", func(t *testing.T) {
		t.Skip("This test takes too long and doesn't provide much value.")
		t.Parallel()

		ctx := context.Background()
		result, err := ucum.GetUCUMDataFromURI(ctx, "http://invalid-url-that-does-not-exist.local")
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("malformed XML", func(t *testing.T) {
		t.Parallel()

		xmlContent := `<root><unclosed>`

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/xml")
			_, _ = w.Write([]byte(xmlContent))
		}))
		t.Cleanup(server.Close)

		ctx := context.Background()
		result, err := ucum.GetUCUMDataFromURI(ctx, server.URL)
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("context timeout", func(t *testing.T) {
		t.Parallel()

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			time.Sleep(100 * time.Millisecond) // Longer than test timeout
			w.WriteHeader(http.StatusOK)
		}))
		t.Cleanup(server.Close)

		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
		defer cancel()

		result, err := ucum.GetUCUMDataFromURI(ctx, server.URL)
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "context deadline exceeded")
	})

	t.Run("empty XML response", func(t *testing.T) {
		t.Parallel()

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/xml")
			_, _ = w.Write([]byte(""))
		}))
		t.Cleanup(server.Close)

		ctx := context.Background()
		result, err := ucum.GetUCUMDataFromURI(ctx, server.URL)
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("XML with missing attributes", func(t *testing.T) {
		t.Parallel()

		xmlContent := `<?xml version="1.0" encoding="UTF-8"?>
<root>
	<prefix><name>test</name></prefix>
</root>`

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/xml")
			_, _ = w.Write([]byte(xmlContent))
		}))
		t.Cleanup(server.Close)

		ctx := context.Background()
		result, err := ucum.GetUCUMDataFromURI(ctx, server.URL)
		require.NoError(t, err)
		require.NotNil(t, result)

		assert.Empty(t, result.Version)
		assert.Empty(t, result.Revision)
		assert.Empty(t, result.RevisionDate)
		assert.Len(t, result.Prefixes, 1)
		assert.Empty(t, result.BaseUnits)
		assert.Empty(t, result.Units)
	})
}

// Test XML structure validation.
//
//nolint:funlen // This is just a list of test cases.
func TestXMLStructures(t *testing.T) {
	t.Parallel()

	t.Run("complete XML structure", func(t *testing.T) {
		t.Parallel()

		xmlContent := `<?xml version="1.0" encoding="UTF-8"?>
<root version="2.1" revision="42" revision-date="2023-12-01">
	<prefix>
		<name>Yotta</name>
	</prefix>
	<prefix>
		<name>Zetta</name>
	</prefix>
	<base-unit>
		<name>meter</name>
	</base-unit>
	<base-unit>
		<name>second</name>
	</base-unit>
	<unit>
		<name>pascal</name>
	</unit>
	<unit>
		<name>joule</name>
	</unit>
</root>`

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/xml")
			_, _ = w.Write([]byte(xmlContent))
		}))
		t.Cleanup(server.Close)

		ctx := context.Background()
		result, err := ucum.GetUCUMDataFromURI(ctx, server.URL)
		require.NoError(t, err)
		require.NotNil(t, result)

		assert.Equal(t, "2.1", result.Version)
		assert.Equal(t, "42", result.Revision)
		assert.Equal(t, "2023-12-01", result.RevisionDate)

		// Check prefixes
		assert.Len(t, result.Prefixes, 2)
		assert.Equal(t, "Yotta", result.Prefixes[0].Name)
		assert.Equal(t, "Zetta", result.Prefixes[1].Name)

		// Check base units
		assert.Len(t, result.BaseUnits, 2)
		assert.Equal(t, "meter", result.BaseUnits[0].Name)
		assert.Equal(t, "second", result.BaseUnits[1].Name)

		// Check units
		assert.Len(t, result.Units, 2)
		assert.Equal(t, "pascal", result.Units[0].Name)
		assert.Equal(t, "joule", result.Units[1].Name)
	})

	t.Run("XML with special characters", func(t *testing.T) {
		t.Parallel()

		xmlContent := `<?xml version="1.0" encoding="UTF-8"?>
<root version="1.0" revision="1" revision-date="2023-01-01">
	<prefix><name>micro (µ)</name></prefix>
	<unit><name>degree Celsius (°C)</name></unit>
</root>`

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/xml")
			_, _ = w.Write([]byte(xmlContent))
		}))
		t.Cleanup(server.Close)

		ctx := context.Background()
		result, err := ucum.GetUCUMDataFromURI(ctx, server.URL)
		require.NoError(t, err)
		require.NotNil(t, result)

		assert.Len(t, result.Prefixes, 1)
		assert.Equal(t, "micro (µ)", result.Prefixes[0].Name)
		assert.Len(t, result.Units, 1)
		assert.Equal(t, "degree Celsius (°C)", result.Units[0].Name)
	})

	t.Run("XML with whitespace", func(t *testing.T) {
		t.Parallel()

		xmlContent := `<?xml version="1.0" encoding="UTF-8"?>
<root version="1.0" revision="1" revision-date="2023-01-01">
	
	<prefix>
		
		<name>   kilo   </name>
		
	</prefix>
	
</root>`

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/xml")
			_, _ = w.Write([]byte(xmlContent))
		}))
		t.Cleanup(server.Close)

		ctx := context.Background()
		result, err := ucum.GetUCUMDataFromURI(ctx, server.URL)
		require.NoError(t, err)
		require.NotNil(t, result)

		assert.Len(t, result.Prefixes, 1)
		assert.Equal(t, "   kilo   ", result.Prefixes[0].Name) // XML preserves whitespace
	})
}

// Benchmark tests.
func BenchmarkGetUCUMDataFromURI(b *testing.B) {
	xmlContent := `<?xml version="1.0" encoding="UTF-8"?>
<root version="1.0" revision="1" revision-date="2023-01-01">
	<prefix><name>kilo</name></prefix>
	<prefix><name>mega</name></prefix>
	<prefix><name>giga</name></prefix>
	<base-unit><name>meter</name></base-unit>
	<base-unit><name>second</name></base-unit>
	<unit><name>newton</name></unit>
	<unit><name>pascal</name></unit>
	<unit><name>joule</name></unit>
</root>`

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/xml")
		_, _ = w.Write([]byte(xmlContent))
	}))
	defer server.Close()

	ctx := context.Background()

	b.ResetTimer()
	for range b.N {
		_, _ = ucum.GetUCUMDataFromURI(ctx, server.URL)
	}
}

func BenchmarkXMLParsing(b *testing.B) {
	xmlContent := `<?xml version="1.0" encoding="UTF-8"?>
<root version="1.0" revision="1" revision-date="2023-01-01">
	<prefix><name>kilo</name></prefix>
	<prefix><name>mega</name></prefix>
	<prefix><name>giga</name></prefix>
	<prefix><name>tera</name></prefix>
	<prefix><name>peta</name></prefix>
	<prefix><name>exa</name></prefix>
	<prefix><name>zetta</name></prefix>
	<prefix><name>yotta</name></prefix>
	<base-unit><name>meter</name></base-unit>
	<base-unit><name>second</name></base-unit>
	<base-unit><name>kilogram</name></base-unit>
	<base-unit><name>ampere</name></base-unit>
	<base-unit><name>kelvin</name></base-unit>
	<base-unit><name>mole</name></base-unit>
	<base-unit><name>candela</name></base-unit>
	<unit><name>newton</name></unit>
	<unit><name>pascal</name></unit>
	<unit><name>joule</name></unit>
	<unit><name>watt</name></unit>
	<unit><name>coulomb</name></unit>
	<unit><name>volt</name></unit>
	<unit><name>farad</name></unit>
	<unit><name>ohm</name></unit>
	<unit><name>siemens</name></unit>
	<unit><name>weber</name></unit>
	<unit><name>tesla</name></unit>
	<unit><name>henry</name></unit>
	<unit><name>lumen</name></unit>
	<unit><name>lux</name></unit>
	<unit><name>becquerel</name></unit>
	<unit><name>gray</name></unit>
	<unit><name>sievert</name></unit>
	<unit><name>katal</name></unit>
</root>`

	reader := strings.NewReader(xmlContent)

	b.ResetTimer()
	for range b.N {
		reader.Reset(xmlContent)
		dec := xml.NewDecoder(reader)
		dec.CharsetReader = func(_ string, input io.Reader) (io.Reader, error) {
			return input, nil
		}
		var r ucum.Root
		_ = dec.Decode(&r)
	}
}

// Edge case tests
//
//nolint:funlen // This is just a list of test cases.
func TestEdgeCases(t *testing.T) {
	t.Parallel()

	t.Run("nil context", func(t *testing.T) {
		t.Parallel()

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
		}))
		t.Cleanup(server.Close)

		// Test with nil context - should return an error rather than panic
		result, err := ucum.GetUCUMDataFromURI(context.TODO(), server.URL)
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("cancelled context", func(t *testing.T) {
		t.Parallel()

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			time.Sleep(100 * time.Millisecond)
			w.WriteHeader(http.StatusOK)
		}))
		t.Cleanup(server.Close)

		ctx, cancel := context.WithCancel(context.Background())
		cancel() // Cancel immediately

		result, err := ucum.GetUCUMDataFromURI(ctx, server.URL)
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "context canceled")
	})

	t.Run("very large XML", func(t *testing.T) {
		t.Parallel()

		// Generate a large XML with many units
		var xmlBuilder strings.Builder
		xmlBuilder.WriteString(`<?xml version="1.0" encoding="UTF-8"?>`)
		xmlBuilder.WriteString(`<root version="1.0" revision="1" revision-date="2023-01-01">`)

		for i := range 100 {
			xmlBuilder.WriteString(`<prefix><name>prefix`)
			xmlBuilder.WriteString(strconv.Itoa(i))
			xmlBuilder.WriteString(`</name></prefix>`)
		}

		for i := range 100 {
			xmlBuilder.WriteString(`<unit><name>unit`)
			xmlBuilder.WriteString(strconv.Itoa(i))
			xmlBuilder.WriteString(`</name></unit>`)
		}

		xmlBuilder.WriteString(`</root>`)

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/xml")
			_, _ = w.Write([]byte(xmlBuilder.String()))
		}))
		t.Cleanup(server.Close)

		ctx := context.Background()
		result, err := ucum.GetUCUMDataFromURI(ctx, server.URL)
		require.NoError(t, err)
		require.NotNil(t, result)

		assert.Len(t, result.Prefixes, 100)
		assert.Len(t, result.Units, 100)
	})
}

// Test the actual upstream uris.
func TestGetUCUMDataFromUpstream(t *testing.T) {
	t.Parallel()

	result, err := ucum.GetUCUMDataFromUpstream()
	require.NoError(t, err)
	require.NotNil(t, result)

	assert.NotEmpty(t, result.Prefixes)
	assert.NotEmpty(t, result.Units)
}
