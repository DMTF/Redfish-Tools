/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup_test

import (
	"bytes"
	"encoding/json"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/testing/mockup"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// jsonKeys decodes the JSON object in data and returns its keys in document
// order using json.Decoder's token stream.
func jsonKeys(t *testing.T, data []byte) []string {
	t.Helper()
	dec := json.NewDecoder(bytes.NewReader(data))
	_, _ = dec.Token() // opening '{'
	var keys []string
	for dec.More() {
		tok, err := dec.Token()
		require.NoError(t, err)
		k, ok := tok.(string)
		require.True(t, ok, "expected string token, got %T", tok)
		keys = append(keys, k)
		var val json.RawMessage
		require.NoError(t, dec.Decode(&val))
	}
	return keys
}

func TestFileMarshalJSON(t *testing.T) {
	t.Parallel()

	t.Run("SerializesContent", func(t *testing.T) {
		t.Parallel()

		content := map[string]any{
			"@odata.id": "/redfish/v1/Systems/1",
			"Name":      "System 1",
			"Count":     float64(3),
		}
		f := mockup.NewFile(&stubReadSeekCloser{}, content)

		data, err := json.Marshal(f)

		require.NoError(t, err)
		assert.JSONEq(t, `{"@odata.id":"/redfish/v1/Systems/1","Name":"System 1","Count":3}`, string(data))
	})

	t.Run("EmptyContentIsEmptyObject", func(t *testing.T) {
		t.Parallel()

		f := mockup.NewFile(&stubReadSeekCloser{}, map[string]any{})

		data, err := json.Marshal(f)

		require.NoError(t, err)
		assert.JSONEq(t, `{}`, string(data))
	})
}

// TestFileMarshalJSONKeyOrdering verifies the five-group ordering rule:
//
//	@odata.* (except @odata.id) → Id/Name/Description/Status → other → @odata.id → @Redfish.*
func TestFileMarshalJSONKeyOrdering(t *testing.T) {
	t.Parallel()

	f := mockup.NewFile(&stubReadSeekCloser{}, map[string]any{
		"@Redfish.Copyright": "c",
		"@odata.type":        "T",
		"@odata.id":          "/redfish/v1/Systems/1",
		"Status":             "OK",
		"Description":        "d",
		"Name":               "n",
		"Id":                 "1",
		"Manufacturer":       "m",
		"AssetTag":           "a",
	})

	data, err := json.Marshal(f)
	require.NoError(t, err)

	assert.Equal(t, []string{
		// group 1 – @odata.* except @odata.id, alphabetically
		"@odata.type",
		// group 2 – fixed priority order (only present keys)
		"Id", "Name", "Description", "Status",
		// group 3 – other alphabetically
		"AssetTag", "Manufacturer",
		// group 4 – @odata.id just above @Redfish.*
		"@odata.id",
		// group 5 – @Redfish.* alphabetically
		"@Redfish.Copyright",
	}, jsonKeys(t, data))
}

// TestFileMarshalJSONODataCountOrdering verifies that a key of the form
// "Foo@odata.count" is emitted immediately before its corresponding "Foo" key.
func TestFileMarshalJSONODataCountOrdering(t *testing.T) {
	t.Parallel()

	f := mockup.NewFile(&stubReadSeekCloser{}, map[string]any{
		"@odata.type":         "T",
		"Members":             []any{},
		"Members@odata.count": float64(0),
		"Links":               map[string]any{},
		"Links@odata.count":   float64(0),
		"Name":                "n",
	})

	data, err := json.Marshal(f)
	require.NoError(t, err)

	assert.Equal(t, []string{
		"@odata.type",
		"Name",
		"Links@odata.count", "Links",
		"Members@odata.count", "Members",
	}, jsonKeys(t, data))
}

// TestFileMarshalJSONActionsOrdering verifies that inside an Actions action
// object the "target" property is emitted before any other properties.
func TestFileMarshalJSONActionsOrdering(t *testing.T) {
	t.Parallel()

	f := mockup.NewFile(&stubReadSeekCloser{}, map[string]any{
		"@odata.id": "/redfish/v1/Systems/1",
		"Actions": map[string]any{
			"#Computer.Reset": map[string]any{
				"title":  "Reset",
				"target": "/redfish/v1/Systems/1/Actions/Computer.Reset",
			},
		},
	})

	data, err := json.Marshal(f)
	require.NoError(t, err)

	assert.Contains(t, string(data),
		`"#Computer.Reset":{"target":"/redfish/v1/Systems/1/Actions/Computer.Reset","title":"Reset"}`)
}

// TestFileMarshalJSONPriorityKeysAbsentAreSkipped confirms that missing
// priority keys are simply omitted from the output and @odata.id still lands
// in its expected position.
func TestFileMarshalJSONPriorityKeysAbsentAreSkipped(t *testing.T) {
	t.Parallel()

	// Only Name and Status present from the priority group; @odata.id last.
	f := mockup.NewFile(&stubReadSeekCloser{}, map[string]any{
		"@odata.id": "/redfish/v1/Systems/1",
		"Status":    "OK",
		"Name":      "n",
		"Other":     "o",
	})

	data, err := json.Marshal(f)
	require.NoError(t, err)

	assert.Equal(t, []string{"Name", "Status", "Other", "@odata.id"}, jsonKeys(t, data))
}
