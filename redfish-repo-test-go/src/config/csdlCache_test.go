/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package config_test

import (
	"bytes"
	"io"
	"sync"
	"testing"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// mockReadCloser implements io.ReadCloser for testing.
type mockReadCloser struct {
	*bytes.Buffer

	closed bool
	mu     sync.Mutex
}

func newMockReadCloser(content string) *mockReadCloser {
	return &mockReadCloser{
		Buffer: bytes.NewBufferString(content),
		closed: false,
	}
}

func (m *mockReadCloser) Close() error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.closed = true
	return nil
}

func (m *mockReadCloser) IsClosed() bool {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.closed
}

func TestExternalThreadSafeCache_Get(t *testing.T) {
	t.Parallel()

	t.Run("get from empty cache", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		edmx, reader := cache.Get("nonexistent")
		assert.Nil(t, edmx)
		assert.Nil(t, reader)
	})

	t.Run("get existing entry", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		var mockEdmx *csdl.Edmx // Use nil since we can't create a real instance
		mockReader := newMockReadCloser("test content")

		// Set up cache entry
		cache.Set("test", mockEdmx, mockReader)

		// Get entry
		retrievedEdmx, retrievedReader := cache.Get("test")
		assert.Equal(t, mockEdmx, retrievedEdmx)
		assert.Same(t, mockReader, retrievedReader)
	})

	t.Run("concurrent gets", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		var mockEdmx *csdl.Edmx
		mockReader := newMockReadCloser("test content")
		cache.Set("test", mockEdmx, mockReader)

		var wg sync.WaitGroup
		results := make([]struct {
			edmx   *csdl.Edmx
			reader io.ReadCloser
		}, 10)

		for i := range 10 {
			wg.Add(1)
			go func(index int) {
				defer wg.Done()
				edmx, reader := cache.Get("test")
				results[index].edmx = edmx
				results[index].reader = reader
			}(i)
		}

		wg.Wait()

		// All results should be the same
		for i, result := range results {
			assert.Equal(t, mockEdmx, result.edmx, "iteration %d", i)
			assert.Same(t, mockReader, result.reader, "iteration %d", i)
		}
	})
}

func TestExternalThreadSafeCache_Set(t *testing.T) {
	t.Parallel()

	t.Run("set new entry", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		var mockEdmx *csdl.Edmx
		mockReader := newMockReadCloser("test content")

		cache.Set("test", mockEdmx, mockReader)

		// Verify entry was set
		edmx, reader := cache.Get("test")
		assert.Equal(t, mockEdmx, edmx)
		assert.Same(t, mockReader, reader)
	})

	t.Run("overwrite existing entry", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		var mockEdmx1 *csdl.Edmx
		mockReader1 := newMockReadCloser("content1")
		var mockEdmx2 *csdl.Edmx
		mockReader2 := newMockReadCloser("content2")

		// Set first entry
		cache.Set("key", mockEdmx1, mockReader1)
		retrievedEdmx, _ := cache.Get("key")
		assert.Equal(t, mockEdmx1, retrievedEdmx)

		// Overwrite with second entry
		cache.Set("key", mockEdmx2, mockReader2)
		retrievedEdmx, _ = cache.Get("key")
		assert.Equal(t, mockEdmx2, retrievedEdmx)
	})

	t.Run("set nil values", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		cache.Set("nil", nil, nil)

		// Should be able to set nil values
		edmx, reader := cache.Get("nil")
		assert.Nil(t, edmx)
		assert.Nil(t, reader)
	})
}

//nolint:funlen // This is just a list of test cases.
func TestExternalThreadSafeCache_GetAll(t *testing.T) {
	t.Parallel()

	t.Run("get all from empty cache", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		all := cache.GetAll()
		assert.Empty(t, all)
	})

	t.Run("get all with entries", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}

		// Add multiple entries
		entries := []struct {
			key    string
			reader *mockReadCloser
		}{
			{"key1", newMockReadCloser("content1")},
			{"key2", newMockReadCloser("content2")},
			{"key3", newMockReadCloser("content3")},
		}

		for _, entry := range entries {
			var mockEdmx *csdl.Edmx
			cache.Set(entry.key, mockEdmx, entry.reader)
		}

		all := cache.GetAll()
		assert.Len(t, all, 3)

		// Verify all entries are present
		for _, entry := range entries {
			retrieved, exists := all[entry.key]
			assert.True(t, exists, "key %s should exist", entry.key)
			assert.Same(t, entry.reader, retrieved.File)
		}
	})

	t.Run("get all is thread-safe", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		var wg sync.WaitGroup
		results := make([]map[string]*csdl.CacheEntry, 10)

		// Add some initial data
		for range 5 {
			var mockEdmx *csdl.Edmx
			mockReader := newMockReadCloser("test content")
			cache.Set("key", mockEdmx, mockReader)
		}

		// Concurrent GetAll calls
		for i := range results {
			wg.Add(1)
			go func(index int) {
				defer wg.Done()
				results[index] = cache.GetAll()
			}(i)
		}

		wg.Wait()

		// All results should be consistent
		for i, result := range results {
			assert.Len(t, result, 1, "iteration %d", i)
			assert.Contains(t, result, "key", "iteration %d", i)
		}
	})

	t.Run("get all returns copy", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		var mockEdmx *csdl.Edmx
		mockReader := newMockReadCloser("test content")
		cache.Set("test", mockEdmx, mockReader)

		all1 := cache.GetAll()
		all2 := cache.GetAll()

		// Should be equal
		assert.Len(t, all1, len(all2))
		assert.Equal(t, all1, all2)

		// Both should contain the test entry
		assert.Contains(t, all1, "test")
		assert.Contains(t, all2, "test")
	})
}

func TestExternalThreadSafeCache_InterfaceCompliance(t *testing.T) {
	t.Parallel()

	t.Run("implements csdl.ExternalCache interface", func(t *testing.T) {
		t.Parallel()

		var _ csdl.ExternalCache = &config.ExternalThreadSafeCache{}
		cache := &config.ExternalThreadSafeCache{}

		// Test all interface methods exist and work
		assert.NotNil(t, cache.GetAll())
		edmx, reader := cache.Get("test")
		assert.Nil(t, edmx)
		assert.Nil(t, reader)

		var mockEdmx *csdl.Edmx
		mockReader := newMockReadCloser("test content")
		cache.Set("test", mockEdmx, mockReader)

		retrievedEdmx, retrievedReader := cache.Get("test")
		assert.Equal(t, mockEdmx, retrievedEdmx)
		assert.Same(t, mockReader, retrievedReader)

		all := cache.GetAll()
		assert.Contains(t, all, "test")
	})
}

func TestExternalThreadSafeCache_EdgeCases(t *testing.T) {
	t.Parallel()

	t.Run("empty string keys", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		var mockEdmx *csdl.Edmx
		mockReader := newMockReadCloser("test content")

		cache.Set("", mockEdmx, mockReader)
		retrievedEdmx, retrievedReader := cache.Get("")
		assert.Equal(t, mockEdmx, retrievedEdmx)
		assert.Same(t, mockReader, retrievedReader)

		all := cache.GetAll()
		assert.Contains(t, all, "")
	})

	t.Run("nil cache operations", func(t *testing.T) {
		t.Parallel()

		var cache *config.ExternalThreadSafeCache

		assert.Panics(t, func() {
			cache.Get("test")
		})

		assert.Panics(t, func() {
			cache.Set("test", nil, nil)
		})

		assert.Panics(t, func() {
			cache.GetAll()
		})
	})

	t.Run("reader lifecycle", func(t *testing.T) {
		t.Parallel()

		cache := &config.ExternalThreadSafeCache{}
		var mockEdmx *csdl.Edmx
		mockReader := newMockReadCloser("test content")

		cache.Set("test", mockEdmx, mockReader)

		// Retrieve the reader
		_, retrievedReader := cache.Get("test")
		assert.NotNil(t, retrievedReader)
		mockRetrievedReader, ok := retrievedReader.(*mockReadCloser)
		require.True(t, ok)
		assert.False(t, mockRetrievedReader.IsClosed())

		// Close the reader
		err := retrievedReader.Close()
		assert.NoError(t, err)
		assert.True(t, mockRetrievedReader.IsClosed())

		// Read from closed reader should work since we're using bytes.Buffer
		content, err := io.ReadAll(retrievedReader)
		assert.NoError(t, err)
		assert.Equal(t, "test content", string(content))
	})
}

// Benchmark tests.
func BenchmarkExternalThreadSafeCache_Get(b *testing.B) {
	cache := &config.ExternalThreadSafeCache{}
	var mockEdmx *csdl.Edmx
	mockReader := newMockReadCloser("test content")
	cache.Set("test", mockEdmx, mockReader)

	b.ResetTimer()
	b.ReportAllocs()
	for b.Loop() {
		_, _ = cache.Get("test")
	}
}

func BenchmarkExternalThreadSafeCache_Get_NotFound(b *testing.B) {
	cache := &config.ExternalThreadSafeCache{}

	b.ResetTimer()
	b.ReportAllocs()
	for b.Loop() {
		_, _ = cache.Get("nonexistent")
	}
}

func BenchmarkExternalThreadSafeCache_Set(b *testing.B) {
	cache := &config.ExternalThreadSafeCache{}

	b.ResetTimer()
	b.ReportAllocs()
	for b.Loop() {
		var mockEdmx *csdl.Edmx
		mockReader := newMockReadCloser("test content")
		cache.Set("key", mockEdmx, mockReader)
	}
}

func BenchmarkExternalThreadSafeCache_GetAll(b *testing.B) {
	cache := &config.ExternalThreadSafeCache{}

	// Pre-populate cache
	for i := range 100 {
		var mockEdmx *csdl.Edmx
		mockReader := newMockReadCloser("test content")
		cache.Set("key"+string(rune(i)), mockEdmx, mockReader)
	}

	b.ResetTimer()
	b.ReportAllocs()
	for b.Loop() {
		_ = cache.GetAll()
	}
}

func BenchmarkExternalThreadSafeCache_GetAll_Empty(b *testing.B) {
	cache := &config.ExternalThreadSafeCache{}

	b.ResetTimer()
	b.ReportAllocs()
	for b.Loop() {
		_ = cache.GetAll()
	}
}

func BenchmarkExternalThreadSafeCache_ConcurrentOperations(b *testing.B) {
	cache := &config.ExternalThreadSafeCache{}
	var mockEdmx *csdl.Edmx
	mockReader := newMockReadCloser("test content")
	cache.Set("test", mockEdmx, mockReader)

	b.ResetTimer()
	b.ReportAllocs()

	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			// Mix of get and set operations
			_, _ = cache.Get("test")
			var newEdmx *csdl.Edmx
			newReader := newMockReadCloser("updated content")
			cache.Set("test", newEdmx, newReader)
		}
	})
}
