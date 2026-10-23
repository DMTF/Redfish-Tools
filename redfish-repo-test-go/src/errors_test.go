/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package src_test

import (
	"errors"
	"strings"
	"testing"

	"github.com/DMTF/redfishRepoTest/src"
	"github.com/DMTF/redfishRepoTest/src/utils"
	"github.com/stretchr/testify/assert"
)

type lineNumberTest struct {
	Name           string
	File           string
	Path           string
	ExpectedLine   int
	ExpectedColumn int
}

//nolint:funlen // just a bunch of test cases.
func getLineNumberTests() []lineNumberTest {
	return []lineNumberTest{
		{
			Name:           "Non-existent",
			File:           "test1.json",
			Path:           "nonexistent",
			ExpectedLine:   0,
			ExpectedColumn: 0,
		},
		{
			Name:           "Simple Tag",
			File:           "test1.json",
			Path:           "test1",
			ExpectedLine:   2,
			ExpectedColumn: 5, // 4 leading spaces → "test1" starts at column 5
		},
		{
			Name:           "Child Tag .",
			File:           "test1.json",
			Path:           "test2.child2",
			ExpectedLine:   5,
			ExpectedColumn: 9, // 8 leading spaces → "child2" starts at column 9
		},
		{
			Name:           "Child Tag /",
			File:           "test1.json",
			Path:           "test2/child2",
			ExpectedLine:   5,
			ExpectedColumn: 9,
		},
		{
			Name:           "Array Index",
			File:           "test1.json",
			Path:           "test3[0]",
			ExpectedLine:   8,
			ExpectedColumn: 9, // 8 leading spaces → "value4" starts at column 9
		},
		{
			Name:           "Child @odata tag",
			File:           "test2.json",
			Path:           "Status.@odata.type",
			ExpectedLine:   5,
			ExpectedColumn: 9, // 8 leading spaces
		},
		{
			Name:           "Complex Array",
			File:           "test2.json",
			Path:           "ComplexCollection[1].Good",
			ExpectedLine:   14,
			ExpectedColumn: 13, // 12 leading spaces
		},
		{
			Name:           "Not in root",
			File:           "taskService.json",
			Path:           "@odata.id",
			ExpectedLine:   0,
			ExpectedColumn: 0,
		},
		{
			Name:           "Root @odata.type not confused by nested keys",
			File:           "eventDestinationCollection.json",
			Path:           "@odata.type",
			ExpectedLine:   2,
			ExpectedColumn: 5, // 4 leading spaces
		},
		// Key that exists only inside array elements, not at the root – must
		// return 0 (not found at root level).
		{
			Name:           "Nested key absent from root returns 0",
			File:           "eventDestinationCollection.json",
			Path:           "@odata.id",
			ExpectedLine:   0,
			ExpectedColumn: 0,
		},
		// Navigate into specific array elements.
		{
			Name:           "Array element 0 nested key",
			File:           "eventDestinationCollection.json",
			Path:           "Members[0].@odata.id",
			ExpectedLine:   7,
			ExpectedColumn: 13, // 12 leading spaces
		},
		{
			Name:           "Array element 1 nested key",
			File:           "eventDestinationCollection.json",
			Path:           "Members[1].@odata.id",
			ExpectedLine:   10,
			ExpectedColumn: 13,
		},
	}
}

func TestHTTPResponseErrorError(t *testing.T) {
	t.Parallel()
	err := &src.HTTPResponseError{StatusCode: 418}
	if got, want := err.Error(), "http error 418"; got != want {
		t.Fatalf("unexpected error string: got %q want %q", got, want)
	}
}

func TestSeverityString(t *testing.T) {
	t.Parallel()
	testCases := []struct {
		name     string
		severity src.Severity
		expected string
	}{
		{name: "error", severity: src.SeverityError, expected: "Error"},
		{name: "warning", severity: src.SeverityWarning, expected: "Warning"},
		{name: "info", severity: src.SeverityInfo, expected: "Info"},
		{name: "unknown", severity: src.Severity(99), expected: "Unknown"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			if got := tc.severity.String(); got != tc.expected {
				t.Fatalf("unexpected severity string: got %q want %q", got, tc.expected)
			}
		})
	}
}

func TestErrorType(t *testing.T) {
	t.Parallel()
	err := src.NewError(src.SeverityWarning, "warning message")
	if got := err.Error(); got != "warning message" {
		t.Fatalf("unexpected Error() output: %q", got)
	}
	if got := err.GetServerity(); got != src.SeverityWarning {
		t.Fatalf("unexpected severity: %v", got)
	}
}

func TestJSONSourceErrorErrorFormatting(t *testing.T) {
	t.Parallel()
	base := src.NewJSONSourceError(
		"file.json", "root.path", "bad json", src.SeverityError,
		errors.New("decode failed"), //nolint:err113 // test-only
	)
	if got := base.Error(); got != "Error:file.json:root.path: bad json: decode failed" {
		t.Fatalf("unexpected formatted error: %q", got)
	}

	base.Message = ""
	if got := base.Error(); got != "Error:file.json:root.path: decode failed" {
		t.Fatalf("unexpected formatted error without message: %q", got)
	}

	base.Err = nil
	base.Message = "bad json"
	base.FileLine = 12
	if got := base.Error(); got != "Error:file.json:12: bad json" {
		t.Fatalf("unexpected formatted error with line: %q", got)
	}
}

func TestJSONSourceErrorAccessorsAndFormats(t *testing.T) {
	t.Parallel()

	err := src.NewJSONSourceError("file.json", "root.path", "bad value", src.SeverityWarning, nil)
	err.FileLine = 7
	assert.Equal(t, src.SeverityWarning, err.GetServerity())
	assert.Equal(t, "file.json", err.FileName())
	assert.Equal(t, 7, err.Line())
	assert.Equal(t, err.Error(), err.Format(src.StanardFormat))
	assert.Equal(t, "file.json:7:0: warning: bad value", err.Format(src.GCCFormat))
	assert.Equal(t, "file.json:7: bad value", err.Format(src.GoFormat))
	assert.Equal(t, err.Error(), err.Format(src.OutputFormat(99)))
}

func TestMarkdownSourceErrorBasics(t *testing.T) {
	t.Parallel()
	err := src.NewMarkdownSourceError("doc.md", "#bad", 21, "invalid anchor", src.SeverityWarning, nil)
	if got := err.GetServerity(); got != src.SeverityWarning {
		t.Fatalf("unexpected severity: %v", got)
	}
	if got := err.FileName(); got != "doc.md" {
		t.Fatalf("unexpected filename: %q", got)
	}
	if got := err.Line(); got != 21 {
		t.Fatalf("unexpected line: %d", got)
	}
	if got := err.Error(); got != "Warning:doc.md:21: invalid anchor" {
		t.Fatalf("unexpected formatted markdown error: %q", got)
	}
}

func TestMarkdownSourceErrorFormats(t *testing.T) {
	t.Parallel()

	err := src.NewMarkdownSourceError("doc.md", "section", 3, "bad markdown", src.SeverityError, nil)
	assert.Equal(t, err.Error(), err.Format(src.StanardFormat))
	assert.Equal(t, "doc.md:3:0: error: bad markdown", err.Format(src.GCCFormat))
	assert.Equal(t, "doc.md:3: bad markdown", err.Format(src.GoFormat))
	assert.Equal(t, err.Error(), err.Format(src.OutputFormat(99)))

	err.Level = src.SeverityWarning
	assert.Equal(t, "doc.md:3:0: warning: bad markdown", err.Format(src.GCCFormat))
}

func TestGeneralErrorFormats(t *testing.T) {
	t.Parallel()

	err := src.NewError(src.SeverityError, "general failure")
	assert.Equal(t, err.Error(), err.Format(src.StanardFormat))
	assert.Equal(t, "<general>:0:0: error: general failure", err.Format(src.GCCFormat))
	assert.Equal(t, "<general>: general failure", err.Format(src.GoFormat))
	assert.Equal(t, err.Error(), err.Format(src.OutputFormat(99)))

	err.Severity = src.SeverityWarning
	assert.Equal(t, "<general>:0:0: warning: general failure", err.Format(src.GCCFormat))
}

type xmlSourceErrorTestCase struct {
	Name           string
	XMLSourceError *src.XMLSourceError
	Expected       string
	Severity       src.Severity
	FileName       string
	Line           int
}

func getXMLSourceErrorTestCases() []xmlSourceErrorTestCase {
	return []xmlSourceErrorTestCase{
		{
			Name:           "basic error",
			XMLSourceError: src.NewXMLSourceError("doc.xml", "//Node", "bad node", src.SeverityError, nil),
			Expected:       "Error:doc.xml://Node: bad node",
			Severity:       src.SeverityError,
			FileName:       "doc.xml",
			Line:           0,
		},
		{
			Name: "error with line",
			XMLSourceError: &src.XMLSourceError{
				Filename: "doc.xml",
				XPath:    "//Node",
				Message:  "bad node",
				FileLine: 1,
				Level:    src.SeverityError,
				Err:      nil,
			},
			Expected: "Error:doc.xml:1: bad node",
			Severity: src.SeverityError,
			FileName: "doc.xml",
			Line:     1,
		},
		{
			Name: "error no message",
			XMLSourceError: &src.XMLSourceError{
				Filename: "doc.xml",
				XPath:    "//Node",
				Message:  "",
				FileLine: 1,
				Level:    src.SeverityError,
				Err:      errors.New("some error"), //nolint:err113 // test-only
			},
			Expected: "Error:doc.xml:1: some error",
			Severity: src.SeverityError,
			FileName: "doc.xml",
			Line:     1,
		},
		{
			Name: "error with wrapped error and message",
			XMLSourceError: &src.XMLSourceError{
				Filename: "doc.xml",
				XPath:    "//Node",
				Message:  "bad node",
				FileLine: 1,
				Level:    src.SeverityError,
				Err:      errors.New("some error"), //nolint:err113 // test-only
			},
			Expected: "Error:doc.xml:1: bad node: some error",
			Severity: src.SeverityError,
			FileName: "doc.xml",
			Line:     1,
		},
	}
}

func TestXMLSourceErrorBasics(t *testing.T) {
	t.Parallel()
	testCases := getXMLSourceErrorTestCases()
	for _, tc := range testCases {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			assert.Equal(t, tc.Severity, tc.XMLSourceError.GetServerity())
			assert.Equal(t, tc.FileName, tc.XMLSourceError.FileName())
			assert.Equal(t, tc.Line, tc.XMLSourceError.Line())
			assert.Equal(t, tc.Expected, tc.XMLSourceError.Error())
		})
	}
}

func TestXMLSourceErrorLookupAndFormat(t *testing.T) {
	t.Parallel()
	// <Node> is on line 3 with 4 leading spaces → column 5.
	xml := `<Root>
  <Child>
    <Node id="1">ok</Node>
  </Child>
</Root>`
	err := src.NewXMLSourceError("doc.xml", "//Node", "bad node", src.SeverityError, nil)
	err.LookupLineFromFile(strings.NewReader(xml))

	assert.Equal(t, 3, err.Line())
	assert.Equal(t, 5, err.FileColumn)
	assert.Equal(t, err.Error(), err.Format(src.StanardFormat))
	assert.Equal(t, "doc.xml:3:5: error: bad node", err.Format(src.GCCFormat))
	assert.Equal(t, "doc.xml:3: bad node", err.Format(src.GoFormat))
	assert.Equal(t, err.Error(), err.Format(src.OutputFormat(42)))
}

func TestMarkdownSourceErrorLookupLineFromFile(t *testing.T) {
	t.Parallel()

	t.Run("finds column on indented line", func(t *testing.T) {
		t.Parallel()
		// Line 3 has 4 leading spaces → column 5.
		content := "# Heading\n\n    indented content\n"
		err := src.NewMarkdownSourceError("doc.md", "#heading", 3, "msg", src.SeverityWarning, nil)
		err.LookupLineFromFile(strings.NewReader(content))
		assert.Equal(t, 5, err.FileColumn)
		assert.Equal(t, "doc.md:3:5: warning: msg", err.Format(src.GCCFormat))
	})

	t.Run("finds column on unindented line", func(t *testing.T) {
		t.Parallel()
		// Line 3 has no leading whitespace → column 1.
		content := "# Heading\n\n[link](#anchor)\n"
		err := src.NewMarkdownSourceError("doc.md", "#anchor", 3, "invalid anchor", src.SeverityWarning, nil)
		err.LookupLineFromFile(strings.NewReader(content))
		assert.Equal(t, 1, err.FileColumn)
		assert.Equal(t, "doc.md:3:1: warning: invalid anchor", err.Format(src.GCCFormat))
	})

	t.Run("skips lookup when FileLine is zero", func(t *testing.T) {
		t.Parallel()
		content := "# Heading\n"
		err := src.NewMarkdownSourceError("doc.md", "", 0, "msg", src.SeverityWarning, nil)
		err.LookupLineFromFile(strings.NewReader(content))
		assert.Equal(t, 0, err.FileColumn)
	})
}

func TestXMLSourceErrorLookupLineFromFileEdgeCases(t *testing.T) {
	t.Parallel()

	t.Run("empty xpath", func(t *testing.T) {
		t.Parallel()
		err := src.NewXMLSourceError("doc.xml", "", "msg", src.SeverityInfo, nil)
		err.LookupLineFromFile(strings.NewReader("<Root/>"))
		if err.Line() != 0 {
			t.Fatalf("expected line to remain zero for empty xpath, got %d", err.Line())
		}
	})

	t.Run("invalid xml", func(t *testing.T) {
		t.Parallel()
		err := src.NewXMLSourceError("doc.xml", "//Node", "msg", src.SeverityInfo, nil)
		err.LookupLineFromFile(strings.NewReader("<Root>"))
		if err.Line() != 0 {
			t.Fatalf("expected line to remain zero for invalid xml, got %d", err.Line())
		}
	})
}

func TestJSONSourceErrorLookupLineFromFileBadSeeker(t *testing.T) {
	t.Parallel()
	err := src.NewJSONSourceError("test.json", "test", "", src.SeverityError, nil)
	err.LookupLineFromFile(badReadSeeker{})
	if err.Line() != 0 {
		t.Fatalf("expected line to remain zero when seek fails, got %d", err.Line())
	}
}

type badReadSeeker struct{}

func (badReadSeeker) Read(_ []byte) (int, error) {
	return 0, nil
}

func (badReadSeeker) Seek(_ int64, _ int) (int64, error) {
	return 0, errors.New("seek failed") //nolint:err113 // test-only
}

func TestJSONSourceErrorLookupLineFromFile(t *testing.T) {
	t.Parallel()
	tests := getLineNumberTests()
	for _, test := range tests {
		t.Run(test.Name, func(t *testing.T) {
			t.Parallel()
			jsonErr := src.NewJSONSourceError(test.File, test.Path, "", src.SeverityError, nil)
			file, err := utils.OpenFile("./testData/" + test.File)
			if err != nil {
				t.Fatalf("Failed to open file: %v", err)
			}
			defer func() { _ = file.Close() }()
			jsonErr.LookupLineFromFile(file)
			assert.Equal(t, test.ExpectedLine, jsonErr.Line(), "line number")
			assert.Equal(t, test.ExpectedColumn, jsonErr.FileColumn, "column number")
		})
	}
}
