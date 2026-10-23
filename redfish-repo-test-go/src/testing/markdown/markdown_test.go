/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package markdown_test

import (
	"os"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/testing/markdown"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type getAnchorTestCase struct {
	Name     string
	Markdown string
	Expected map[string]struct{}
}

func GetAnchorsTestCases() []getAnchorTestCase {
	return []getAnchorTestCase{
		{
			Name:     "empty",
			Markdown: "",
			Expected: map[string]struct{}{},
		},
		{
			Name: "figure",
			Markdown: `See [Figure 1](#figure_1).
			
![Figure 1: Simple schema](./images/DriveSchema.png) {id=figure_1 width="90%"}`,
			Expected: map[string]struct{}{
				"figure_1": {},
			},
		},
		{
			Name: "figure anchor",
			Markdown: `See [Figure 2](#figure_2).
			
![Figure 2: Storage Resource Schema](./images/StorageResourceSchema.png) {#figure_2 width="90%"}`,
			Expected: map[string]struct{}{
				"figure_2": {},
			},
		},
		{
			Name:     "auto index",
			Markdown: `# Appendix A: References`,
			Expected: map[string]struct{}{
				"appendix-a-references": {},
			},
		},
		{
			Name:     "auto index 2",
			Markdown: `# Redfish documentation generator`,
			Expected: map[string]struct{}{
				"redfish-documentation-generator": {},
			},
		},
		{
			Name: "explicit anchor in list",
			Markdown: `* <a id="curl"></a>curl: command line tool and library` +
				` for transferring data with URLs, [https://curl.haxx.se/]` +
				`(https://curl.haxx.se/ "https://curl.haxx.se/")`,
			Expected: map[string]struct{}{
				"curl": {},
			},
		},
	}
}

func TestMarkdownGetAnchors(t *testing.T) {
	t.Parallel()
	testCases := GetAnchorsTestCases()
	for _, tc := range testCases {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			md := &markdown.Markdown{
				Content: []byte(tc.Markdown),
			}
			err := md.Parse()
			require.NoError(t, err)
			anchors := md.GetAnchors()
			assert.Equal(t, tc.Expected, anchors)
		})
	}
}

func BenchmarkMarkdownGetAnchors(b *testing.B) {
	testCases := GetAnchorsTestCases()
	for _, tc := range testCases {
		b.Run(tc.Name, func(b *testing.B) {
			b.ReportAllocs()
			md := &markdown.Markdown{
				Content: []byte(tc.Markdown),
			}
			err := md.Parse()
			require.NoError(b, err)
			for b.Loop() {
				_ = md.GetAnchors()
			}
		})
	}
}

func TestGetIDString(t *testing.T) {
	t.Parallel()
	assert.Equal(t, "test", markdown.GetIDString("test"))
	assert.Equal(t, "test", markdown.GetIDString([]byte("test")))
	assert.Panics(t, func() {
		markdown.GetIDString(123)
	})
}

type parseTestCase struct {
	Name           string
	Filename       string
	ExpectedErrors []string
}

func getParseTestCases(tb testing.TB) []parseTestCase {
	tb.Helper()
	return []parseTestCase{
		{
			Name:     "valid markdown",
			Filename: "test.md",
		},
		{
			Name:     "non existent",
			Filename: "nothere.md",
			ExpectedErrors: []string{
				"Warning:nothere.md:: failed to read markdown file:" +
					" open nothere.md: no such file or directory",
			},
		},
	}
}

func TestMarkdownParse(t *testing.T) {
	t.Parallel()
	testCases := getParseTestCases(t)
	helperCreateFile(t, "test.md", []byte("# Test"))
	helperCreateFile(t, "bad.md", []byte{0x01, 0x02, 0x00, '&', '#', '*'})
	for _, tc := range testCases {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			md := &markdown.Markdown{
				Filename: tc.Filename,
			}
			testCase := testsuite.NewCase("test", md.TestParse, nil)
			_ = testCase.Run()
			require.Len(t, testCase.Errors, len(tc.ExpectedErrors))
			for i, err := range testCase.Errors {
				assert.Equal(t, tc.ExpectedErrors[i], err.Error())
			}
		})
	}
}

func helperCreateFile(t *testing.T, filename string, content []byte) {
	t.Helper()
	err := os.WriteFile(filename, content, 0644) //nolint:gosec
	require.NoError(t, err)
	t.Cleanup(func() {
		_ = os.Remove(filename)
	})
}

type validateExampleTestCase struct {
	Name           string
	Filename       string
	Content        []byte
	ExpectedErrors []string
}

func getValidateExampleTestCases(tb testing.TB) []validateExampleTestCase {
	tb.Helper()
	return []validateExampleTestCase{
		{
			Name:     "valid json example",
			Filename: "valid_json.md",
			Content:  []byte("# Test\n\n```json\n{\"key\": \"value\"}\n```"),
		},
		{
			Name:     "invalid json example",
			Filename: "invalid_json.md",
			Content:  []byte("# Test\n\n```json\n{\"key\": \"value\",}\n```"),
			ExpectedErrors: []string{
				"Warning:invalid_json.md:3: invalid json example: " +
					"invalid character '}' looking for beginning of object key string",
			},
		},
		{
			Name:     "json with ellipsis",
			Filename: "ellipsis_json.md",
			Content:  []byte("# Test\n\n```json\n{\"key\": \"value\", ...}\n```"),
		},
		{
			Name:     "non-json code block",
			Filename: "other_code.md",
			Content:  []byte("# Test\n\n```python\nprint(\"hello\")\n```"),
		},
		{
			Name:     "indented code block",
			Filename: "indented.md",
			Content:  []byte("# Test\n\n    some code here\n"),
		},
		{
			Name:     "multiple examples",
			Filename: "multiple.md",
			Content: []byte("# Test\n\n```json\n{\"valid\": true}\n```\n\n" +
				"```json\n{\"invalid\": }\n```\n\n```bash\necho hello\n```"),
			ExpectedErrors: []string{
				"Warning:multiple.md:7: invalid json example: " +
					"invalid character '}' looking for beginning of value",
			},
		},
		{
			Name:     "empty fenced code block",
			Filename: "empty_fenced.md",
			Content:  []byte("# Test\n\n```\nno language\n```\n"),
		},
	}
}

//nolint:dupl
func TestMarkdownValidateExamples(t *testing.T) {
	t.Parallel()
	testCases := getValidateExampleTestCases(t)

	for _, tc := range testCases {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			// Create the test file
			helperCreateFile(t, tc.Filename, tc.Content)

			// Create and parse the markdown
			md := &markdown.Markdown{
				Filename: tc.Filename,
			}
			err := md.Load()
			require.NoError(t, err)
			err = md.Parse()
			require.NoError(t, err)

			// Run ValidateExamples
			testCase := testsuite.NewCase("test", md.ValidateExamples, nil)
			_ = testCase.Run()

			// Check errors
			require.Len(t, testCase.Errors, len(tc.ExpectedErrors))
			for i, err := range testCase.Errors {
				assert.Equal(t, tc.ExpectedErrors[i], err.Error())
			}
		})
	}
}

type validateLinkTestCase struct {
	Name           string
	Filename       string
	Content        []byte
	ExpectedErrors []string
}

//nolint:funlen
func getValidateLinkTestCases(tb testing.TB) []validateLinkTestCase {
	tb.Helper()
	return []validateLinkTestCase{
		{
			Name:     "valid internal links",
			Filename: "valid_links.md",
			Content: []byte("# Test Section\n\nSome content.\n\n" +
				"## Subsection\n\nMore content.\n\n" +
				"[Link to test](#test-section)\n" +
				"[Link to subsection](#subsection)"),
		},
		{
			Name:     "missing anchor",
			Filename: "missing_anchor.md",
			Content: []byte("# Test Section\n\nSome content.\n\n" +
				"[Link to missing](#missing-section)"),
			ExpectedErrors: []string{
				"Warning:missing_anchor.md:5: invalid internal anchor link: " +
					"missing anchor \"#missing-section\"",
			},
		},
		{
			Name:     "external links ignored",
			Filename: "external_links.md",
			Content: []byte("# Test\n\n" +
				"[External link](https://example.com)\n" +
				"[Relative link](./other.md)\n" +
				"[Email](mailto:test@example.com)"),
		},
		{
			Name:     "fuzzy match suggestion",
			Filename: "fuzzy_match.md",
			Content: []byte("# Test Section\n\nSome content.\n\n" +
				"[Link with typo](#test-secton)"),
			ExpectedErrors: []string{
				"Warning:fuzzy_match.md:5: invalid internal anchor link: " +
					"missing anchor \"#test-secton\", did you mean \"test-section\"?",
			},
		},
		{
			Name:     "multiple missing anchors",
			Filename: "multiple_missing.md",
			Content: []byte("# Test Section\n\nSome content.\n\n" +
				"[Missing 1](#missing1)\n" +
				"[Missing 2](#missing2)\n" +
				"[Missing 3](#missing3)"),
			ExpectedErrors: []string{
				"Warning:multiple_missing.md:5: invalid internal anchor link: " +
					"missing anchor \"#missing1\"",
				"Warning:multiple_missing.md:6: invalid internal anchor link: " +
					"missing anchor \"#missing2\"",
				"Warning:multiple_missing.md:7: invalid internal anchor link: " +
					"missing anchor \"#missing3\"",
			},
		},
		{
			Name:     "figure anchors",
			Filename: "figure_links.md",
			Content: []byte("# Test\n\n" +
				"![Figure 1](image.png) {#fig1}\n\n" +
				"![Figure 2](image.png) {id=fig2}\n\n" +
				"[Link to figure 1](#fig1)\n" +
				"[Link to figure 2](#fig2)"),
		},
		{
			Name:     "raw html anchors",
			Filename: "html_anchors.md",
			Content: []byte("# Test\n\n" +
				"<a id=\"custom-anchor\"></a>\n\n" +
				"<a name=\"named-anchor\"></a>\n\n" +
				"[Link to custom](#custom-anchor)\n" +
				"[Link to named](#named-anchor)"),
		},
		{
			Name:     "redfish doc generator exception",
			Filename: "Input.md",
			Content: []byte("# Test\n\n" +
				"[Link to doc generator](#redfish-documentation-generator)"),
		},
		{
			Name:     "no internal links",
			Filename: "no_internal.md",
			Content: []byte("# Test Section\n\nSome content with " +
				"[external link](https://example.com) " +
				"but no internal links."),
		},
		{
			Name:     "case sensitive anchors",
			Filename: "case_sensitive.md",
			Content: []byte("# Test Section\n\nSome content.\n\n" +
				"[Wrong case](#Test-Section)\n" +
				"[Correct case](#test-section)"),
			ExpectedErrors: []string{
				"Warning:case_sensitive.md:5: invalid internal anchor link: " +
					"missing anchor \"#Test-Section\"",
			},
		},
	}
}

//nolint:dupl
func TestMarkdownValidateLinks(t *testing.T) {
	t.Parallel()
	testCases := getValidateLinkTestCases(t)

	for _, tc := range testCases {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			// Create the test file
			helperCreateFile(t, tc.Filename, tc.Content)

			// Create and parse the markdown
			md := &markdown.Markdown{
				Filename: tc.Filename,
			}
			err := md.Load()
			require.NoError(t, err)
			err = md.Parse()
			require.NoError(t, err)

			// Run ValidateLinks
			testCase := testsuite.NewCase("test", md.ValidateLinks, nil)
			_ = testCase.Run()

			// Check errors
			require.Len(t, testCase.Errors, len(tc.ExpectedErrors))
			for i, err := range testCase.Errors {
				assert.Equal(t, tc.ExpectedErrors[i], err.Error())
			}
		})
	}
}
