/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package markdown

import (
	"errors"
	"fmt"
	"maps"
	"os"
	"slices"
	"strings"

	"github.com/lithammer/fuzzysearch/fuzzy"
	"github.com/DMTF/redfishRepoTest/src"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/yuin/goldmark"
	"github.com/yuin/goldmark/ast"
	"github.com/yuin/goldmark/parser"
	"github.com/yuin/goldmark/text"
)

var errParseFailed = errors.New("failed to parse markdown file")

type Markdown struct {
	Filename string
	Content  []byte
	Doc      ast.Node
}

func NewMarkdownFile(filename string) *Markdown {
	return &Markdown{
		Filename: filename,
	}
}

func (m *Markdown) Load() error {
	source, err := os.ReadFile(m.Filename)
	if err != nil {
		return err
	}
	m.Content = source
	return nil
}

func (m *Markdown) Parse() error {
	md := goldmark.New(goldmark.WithParserOptions(parser.WithAutoHeadingID()), goldmark.WithExtensions(Pandoc))
	doc := md.Parser().Parse(text.NewReader(m.Content))
	if doc == nil {
		return errParseFailed
	}
	m.Doc = doc
	return nil
}

func (m *Markdown) TestParse(t *testsuite.Testing) {
	err := m.Load()
	if err != nil {
		t.Error(src.NewMarkdownSourceError(m.Filename, "", 0, "failed to read markdown file", src.SeverityWarning, err))
		return
	}
	err = m.Parse()
	if err != nil {
		t.Error(src.NewMarkdownSourceError(m.Filename, "", 0, "failed to parse markdown file", src.SeverityWarning, err))
		return
	}
}

func nodeText(n ast.Node, source []byte) string {
	var buf strings.Builder
	for i := range n.Lines().Len() {
		line := n.Lines().At(i)
		buf.Write(line.Value(source))
	}
	return buf.String()
}

func (m *Markdown) ValidateExamples(t *testsuite.Testing) {
	_ = ast.Walk(m.Doc, func(node ast.Node, entering bool) (ast.WalkStatus, error) {
		if !entering {
			return ast.WalkContinue, nil
		}
		switch n := node.(type) {
		case *ast.FencedCodeBlock:
			language := strings.TrimSpace(string(n.Language(m.Content)))
			if strings.EqualFold(language, "json") {
				validateJSONExample(t, m.Filename, m.Content, n)
				return ast.WalkContinue, nil
			}
			t.Logf("example type=%s content=%q",
				language, strings.TrimSpace(nodeText(n, m.Content)))
		case *ast.CodeBlock:
			t.Logf("example type=code content=%q",
				strings.TrimSpace(nodeText(n, m.Content)))
		}
		return ast.WalkContinue, nil
	})
}

func (m *Markdown) ValidateLinks(t *testsuite.Testing) {
	anchors := m.GetAnchors()
	sortedAnchors := slices.Sorted(maps.Keys(anchors))
	_ = ast.Walk(m.Doc, func(node ast.Node, entering bool) (ast.WalkStatus, error) {
		if !entering {
			return ast.WalkContinue, nil
		}
		link, ok := node.(*ast.Link)
		if !ok {
			return ast.WalkContinue, nil
		}
		destination := string(link.Destination)
		if !strings.HasPrefix(destination, "#") {
			return ast.WalkContinue, nil
		}
		anchor := strings.TrimPrefix(destination, "#")
		if _, ok := anchors[anchor]; !ok {
			isDocGen := anchor == "redfish-documentation-generator"
			isAllowedFile := strings.HasSuffix(m.Filename, "Input.md") ||
				strings.HasSuffix(m.Filename, "IntroHTML.md") ||
				strings.HasSuffix(m.Filename, "Intro.md")
			if isDocGen && isAllowedFile {
				// These files are allowed to have missing anchors
				// referring to the documentation generator since
				// they will be run through it.
				return ast.WalkContinue, nil
			}
			line := nodeLineNumber(m.Content, node)
			matches := fuzzy.Find(anchor, sortedAnchors)
			if len(matches) > 0 {
				msg := fmt.Sprintf(
					"invalid internal anchor link: missing anchor %q, did you mean %q?",
					destination, matches[0])
				t.Error(src.NewMarkdownSourceError(
					m.Filename, destination, line, msg, src.SeverityWarning, nil))
			} else {
				msg := fmt.Sprintf(
					"invalid internal anchor link: missing anchor %q", destination)
				t.Error(src.NewMarkdownSourceError(
					m.Filename, destination, line, msg, src.SeverityWarning, nil))
			}
		}
		return ast.WalkContinue, nil
	})
}

func (m *Markdown) GetAnchors() map[string]struct{} {
	anchors := make(map[string]struct{})
	_ = ast.Walk(m.Doc, func(node ast.Node, entering bool) (ast.WalkStatus, error) {
		if !entering {
			return ast.WalkContinue, nil
		}
		switch t := node.(type) {
		case *ast.Document:
			return ast.WalkContinue, nil
		case *ast.Heading:
			id, ok := t.AttributeString("id")
			if ok {
				anchors[GetIDString(id)] = struct{}{}
			}
		case *ast.RawHTML:
			anchor, ok := ParseRawHTMLTag(t.Segments.Value(m.Content))
			if ok {
				anchors[anchor] = struct{}{}
			}
		case *ast.Text:
			// fmt.Printf("Text: %#v\n", string(t.Text(m.Content)))
		default:
			// fmt.Printf("Node: %T\n", t)
			id, ok := t.AttributeString("id")
			if ok {
				anchors[GetIDString(id)] = struct{}{}
			}
		}
		return ast.WalkContinue, nil
	})
	return anchors
}

func GetIDString(id any) string {
	switch idValue := id.(type) {
	case []byte:
		return strings.ToLower(string(idValue))
	case string:
		return strings.ToLower(idValue)
	default:
		panic(fmt.Sprintf("unexpected type for ID: %T", id))
	}
}
