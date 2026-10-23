/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package markdown_test

import (
	"testing"

	"github.com/DMTF/redfishRepoTest/src/testing/markdown"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/yuin/goldmark"
	"github.com/yuin/goldmark/ast"
	"github.com/yuin/goldmark/parser"
	"github.com/yuin/goldmark/text"
)

type pandocDirectiveTestCase struct {
	Name          string
	Markdown      string
	ExpectedID    string
	ExpectedClass string
	ExpectedAttrs map[string]string
}

func TestPandocDirectiveParsing(t *testing.T) {
	t.Parallel()

	testCases := []pandocDirectiveTestCase{
		{
			Name:          "id only",
			Markdown:      "![Figure](./img.png) {#figure_1}",
			ExpectedID:    "figure_1",
			ExpectedClass: "",
			ExpectedAttrs: map[string]string{},
		},
		{
			Name:          "id class and attrs",
			Markdown:      "![Figure](./img.png) {#figure_2 .wide .center width=\"90%\" data-key=\"value\"}",
			ExpectedID:    "figure_2",
			ExpectedClass: "wide center",
			ExpectedAttrs: map[string]string{
				"width":    "\"90%\"",
				"data-key": "\"value\"",
			},
		},
		{
			Name:          "id equals syntax",
			Markdown:      "![Figure](./img.png) {id=figure_3}",
			ExpectedID:    "figure_3",
			ExpectedClass: "",
			ExpectedAttrs: map[string]string{
				"id": "figure_3",
			},
		},
	}

	for _, tc := range testCases {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			doc := parseWithPandoc(tc.Markdown)
			node := findNodeWithID(doc, tc.ExpectedID)
			require.NotNil(t, node)

			if tc.ExpectedClass != "" {
				classAttr, ok := node.AttributeString("class")
				require.True(t, ok)
				assert.Equal(t, tc.ExpectedClass, attrValueToString(classAttr))
			}

			for key, expected := range tc.ExpectedAttrs {
				value, ok := node.AttributeString(key)
				require.True(t, ok, "missing expected attribute %q", key)
				assert.Equal(t, expected, attrValueToString(value))
			}
		})
	}
}

func TestPandocDirectiveIgnoredInputs(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name     string
		markdown string
	}{
		{name: "empty braces", markdown: "![Figure](./img.png) {}"},
		{name: "dash braces", markdown: "![Figure](./img.png) {-}"},
		{name: "pipe content", markdown: "![Figure](./img.png) {#figure_4|x}"},
		{name: "non directive", markdown: "![Figure](./img.png) {plain}"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			doc := parseWithPandoc(tc.markdown)
			assert.Nil(t, findNodeWithID(doc, "figure_4"))
		})
	}
}

func BenchmarkPandocDirectiveParsing(b *testing.B) {
	md := goldmark.New(goldmark.WithParserOptions(parser.WithAutoHeadingID()), goldmark.WithExtensions(markdown.Pandoc))
	source := []byte("![Figure](./img.png) {#figure_1 .wide .center width=\"90%\" data-key=\"value\"}")

	b.ReportAllocs()
	for b.Loop() {
		_ = md.Parser().Parse(text.NewReader(source))
	}
}

func BenchmarkPandocDirectiveIgnoredInput(b *testing.B) {
	md := goldmark.New(goldmark.WithParserOptions(parser.WithAutoHeadingID()), goldmark.WithExtensions(markdown.Pandoc))
	source := []byte("![Figure](./img.png) {#figure_4|x}")

	b.ReportAllocs()
	for b.Loop() {
		_ = md.Parser().Parse(text.NewReader(source))
	}
}

func parseWithPandoc(markdownSource string) ast.Node {
	md := goldmark.New(goldmark.WithParserOptions(parser.WithAutoHeadingID()), goldmark.WithExtensions(markdown.Pandoc))
	return md.Parser().Parse(text.NewReader([]byte(markdownSource)))
}

func findNodeWithID(doc ast.Node, wantID string) ast.Node {
	var found ast.Node
	_ = ast.Walk(doc, func(node ast.Node, entering bool) (ast.WalkStatus, error) {
		if !entering {
			return ast.WalkContinue, nil
		}
		id, ok := node.AttributeString("id")
		if !ok {
			return ast.WalkContinue, nil
		}
		if attrValueToString(id) == wantID {
			found = node
			return ast.WalkStop, nil
		}
		return ast.WalkContinue, nil
	})
	return found
}

func attrValueToString(v any) string {
	switch value := v.(type) {
	case string:
		return value
	case []byte:
		return string(value)
	default:
		return ""
	}
}
