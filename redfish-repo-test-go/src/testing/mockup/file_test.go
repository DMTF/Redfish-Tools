/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup_test

import (
	"errors"
	"io"
	"os"
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/mockup"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

var errCloseFailed = errors.New("close failed")

type stubReadSeekCloser struct {
	closed   bool
	closeErr error
}

func (s *stubReadSeekCloser) Read(_ []byte) (int, error) {
	return 0, io.EOF
}

func (s *stubReadSeekCloser) Seek(_ int64, _ int) (int64, error) {
	return 0, nil
}

func (s *stubReadSeekCloser) Close() error {
	s.closed = true
	return s.closeErr
}

func TestNewFile(t *testing.T) {
	t.Parallel()

	raw := &stubReadSeekCloser{}
	content := map[string]any{"name": "value"}

	file := mockup.NewFile(raw, content)

	assert.Same(t, raw, file.Raw)
	assert.Equal(t, content, file.Content)
	assert.Nil(t, file.Type)
}

func TestFileClose(t *testing.T) {
	t.Parallel()

	t.Run("Success", func(t *testing.T) {
		t.Parallel()

		raw := &stubReadSeekCloser{}
		file := mockup.NewFile(raw, map[string]any{})

		err := file.Close()

		assert.NoError(t, err)
		assert.True(t, raw.closed)
	})

	t.Run("ReturnsUnderlyingError", func(t *testing.T) {
		t.Parallel()

		expectedErr := errCloseFailed
		raw := &stubReadSeekCloser{closeErr: expectedErr}
		file := mockup.NewFile(raw, map[string]any{})

		err := file.Close()

		assert.ErrorIs(t, err, expectedErr)
		assert.True(t, raw.closed)
	})
}

func TestFileSave(t *testing.T) {
	t.Parallel()

	dir := t.TempDir()
	m := mockup.NewMockup(dir, &config.Config{})
	realPath := m.GetRealPath("/redfish/v1/Systems/1")
	require.NoError(t, os.MkdirAll(filepath.Dir(realPath), 0o755))        //nolint:gosec
	require.NoError(t, os.WriteFile(realPath, []byte("original"), 0o644)) //nolint:gosec

	f := &mockup.File{
		Content: map[string]any{
			"@odata.id": "/redfish/v1/Systems/1",
			"Id":        "1",
		},
	}

	require.NoError(t, f.Save(m, "/redfish/v1/Systems/1"))
	require.NotNil(t, f.Raw)

	data, err := os.ReadFile(realPath) //nolint:gosec // test-only read of temp path
	require.NoError(t, err)
	assert.Contains(t, string(data), `"@odata.id": "/redfish/v1/Systems/1"`)
	assert.Contains(t, string(data), `"Id": "1"`)
}
