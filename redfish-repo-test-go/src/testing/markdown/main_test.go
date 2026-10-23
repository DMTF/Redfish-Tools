/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package markdown_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/markdown"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type parseRawHTMLTestCase struct {
	Name       string
	Input      string
	Expected   string
	ExpectedOK bool
}

func getParseRawHTMLTestCases() []parseRawHTMLTestCase {
	return []parseRawHTMLTestCase{
		{
			Name:       "empty",
			Input:      "",
			Expected:   "",
			ExpectedOK: false,
		},
		{
			Name: "anchor with id",
			Input: `<a id="curl"></a>curl: command line tool and library` +
				` for transferring data with URLs, [https://curl.haxx.se/]` +
				`(https://curl.haxx.se/ "https://curl.haxx.se/")`,
			Expected:   "curl",
			ExpectedOK: true,
		},
		{
			Name: "anchor with name",
			Input: `<a name="curl"></a>curl: command line tool and library` +
				` for transferring data with URLs, [https://curl.haxx.se/]` +
				`(https://curl.haxx.se/ "https://curl.haxx.se/")`,
			Expected:   "curl",
			ExpectedOK: true,
		},
		{
			Name: "anchor with href",
			Input: `<a href="#curl"></a>curl: command line tool and library` +
				` for transferring data with URLs, [https://curl.haxx.se/]` +
				`(https://curl.haxx.se/ "https://curl.haxx.se/")`,
			Expected:   "curl",
			ExpectedOK: true,
		},
		{
			Name: "anchor with bad tag",
			Input: `<a badattr="curl"></a>curl: command line tool and library` +
				` for transferring data with URLs, [https://curl.haxx.se/]` +
				`(https://curl.haxx.se/ "https://curl.haxx.se/")`,
			Expected:   "",
			ExpectedOK: false,
		},
		{
			Name: "non-anchor tag",
			Input: `<div id="curl"></div>curl: command line tool and library` +
				` for transferring data with URLs, [https://curl.haxx.se/]` +
				`(https://curl.haxx.se/ "https://curl.haxx.se/")`,
			Expected:   "",
			ExpectedOK: false,
		},
		{
			Name:       "no terminating quote",
			Input:      `<a href="curl></a>curl: command line tool and library for transferring data with URLs`,
			Expected:   "",
			ExpectedOK: false,
		},
	}
}

func TestParseRawHTMLTag(t *testing.T) {
	t.Parallel()
	testCases := getParseRawHTMLTestCases()
	for _, tc := range testCases {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			result, ok := markdown.ParseRawHTMLTag([]byte(tc.Input))
			assert.Equal(t, tc.Expected, result)
			assert.Equal(t, tc.ExpectedOK, ok)
		})
	}
}

func BenchmarkParseRawHTMLTag(b *testing.B) {
	testCases := getParseRawHTMLTestCases()
	for _, tc := range testCases {
		b.Run(tc.Name, func(b *testing.B) {
			b.ReportAllocs()
			input := []byte(tc.Input)
			for b.Loop() {
				_, _ = markdown.ParseRawHTMLTag(input)
			}
		})
	}
}

//nolint:funlen
func TestCreateTestsFromConfig(t *testing.T) {
	t.Parallel()

	t.Run("single file - valid markdown", func(t *testing.T) {
		t.Parallel()
		tmpDir := t.TempDir()
		validFile := filepath.Join(tmpDir, "test.md")
		content := []byte("# Test\n\nSome content.")
		err := os.WriteFile(validFile, content, 0644) //nolint:gosec
		require.NoError(t, err)

		cfg := &config.Config{
			SingleFile: validFile,
		}
		list := &testsuite.List{}

		err = markdown.CreateTestsFromConfig(cfg, list)
		require.NoError(t, err)

		// Should have one suite with the file name
		require.Len(t, list.Suites, 1)
		suite := list.Suites[0]
		assert.Equal(t, validFile, suite.Name)

		// Should have three tests
		require.Len(t, suite.Cases, 3)
		assert.Contains(t, suite.Cases[0].Name, "Parses as Markdown")
		assert.Contains(t, suite.Cases[1].Name, "Validate examples")
		assert.Contains(t, suite.Cases[2].Name, "Validate links")
	})

	t.Run("single file - non-markdown", func(t *testing.T) {
		t.Parallel()
		tmpDir := t.TempDir()
		nonMdFile := filepath.Join(tmpDir, "test.txt")
		content := []byte("Not markdown")
		err := os.WriteFile(nonMdFile, content, 0644) //nolint:gosec
		require.NoError(t, err)

		cfg := &config.Config{
			SingleFile: nonMdFile,
		}
		list := &testsuite.List{}

		err = markdown.CreateTestsFromConfig(cfg, list)
		require.NoError(t, err)

		// Should have no suites since it's not a markdown file
		assert.Empty(t, list.Suites)
	})

	t.Run("empty config", func(t *testing.T) {
		t.Parallel()
		cfg := &config.Config{}
		list := &testsuite.List{}

		err := markdown.CreateTestsFromConfig(cfg, list)
		require.NoError(t, err)

		// Should have no suites
		assert.Empty(t, list.Suites)
	})

	t.Run("valid globs", func(t *testing.T) {
		t.Parallel()
		tmpDir := t.TempDir()

		// Create multiple markdown files
		files := []string{"doc1.md", "doc2.md", "readme.md"}
		for _, filename := range files {
			path := filepath.Join(tmpDir, filename)
			content := []byte("# " + filename + "\n\nContent for " + filename)
			err := os.WriteFile(path, content, 0644) //nolint:gosec
			require.NoError(t, err)
		}

		// Create a non-markdown file that should be ignored
		otherFile := filepath.Join(tmpDir, "ignore.txt")
		err := os.WriteFile(otherFile, []byte("ignore me"), 0644) //nolint:gosec
		require.NoError(t, err)

		cfg := &config.Config{
			MarkdownGlobs: []string{filepath.Join(tmpDir, "*.md")},
		}
		list := &testsuite.List{}

		err = markdown.CreateTestsFromConfig(cfg, list)
		require.NoError(t, err)

		// Should have suites for all markdown files
		require.Len(t, list.Suites, 3)

		suiteNames := make([]string, 0, len(list.Suites))
		for _, suite := range list.Suites {
			suiteNames = append(suiteNames, suite.Name)
			// Each suite should have 3 tests
			require.Len(t, suite.Cases, 3)
		}

		// Should be sorted
		assert.Equal(t, []string{
			filepath.Join(tmpDir, "doc1.md"),
			filepath.Join(tmpDir, "doc2.md"),
			filepath.Join(tmpDir, "readme.md"),
		}, suiteNames)
	})
}
