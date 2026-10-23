/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package markdown

import (
	"bytes"
	"strings"

	"github.com/yuin/goldmark"
	"github.com/yuin/goldmark/ast"
	"github.com/yuin/goldmark/parser"
	"github.com/yuin/goldmark/text"
	"github.com/yuin/goldmark/util"
)

//nolint:gochecknoglobals
var Pandoc = &pandoc{}

type pandoc struct{}

func (p *pandoc) Extend(md goldmark.Markdown) {
	md.Parser().AddOptions(
		parser.WithInlineParsers(util.Prioritized(&pandocInlineParser{}, 0)),
	)
}

type pandocInlineParser struct{}

func (p *pandocInlineParser) Trigger() []byte {
	return []byte{'{'}
}

//nolint:cyclop
func (p *pandocInlineParser) Parse(parent ast.Node, block text.Reader, pc parser.Context) ast.Node {
	child := parent.FirstChild()
	if child == nil {
		return nil
	}
	line, _ := block.PeekLine()
	index := strings.Index(string(line), "}")
	if index == -1 {
		// This is not a pandoc directive, skip it
		return nil
	}
	if strings.HasPrefix(string(line), "{}") || strings.Contains(string(line), "|") {
		// Don't process this...
		return nil
	}
	if string(line) == "{-}" {
		// This is an empty pandoc directive, skip it
		block.Advance(len(line))
		return nil
	}
	line = bytes.TrimSpace(line[1:index])
	// There are a few formats acceptable here...
	// {#id}
	// {id=value}
	// {#id .class}
	// {#id class="class"}
	// {#id class="class" style="style"}
	// {#id class="class" style="style" data-key="value"}
	// etc.
	lineStr := string(line)
	if !strings.Contains(lineStr, "=") &&
		!strings.Contains(lineStr, ".") &&
		!strings.Contains(lineStr, "#") {
		// This is not a pandoc directive, skip it
		return nil
	}
	var data []byte
	for {
		data, line, _ = bytes.Cut(line, []byte{' '})
		if len(data) == 0 {
			break
		}
		switch {
		case data[0] == '#':
			parent.SetAttribute([]byte("id"), data[1:])
		case data[0] == '.':
			// Class directive
			class, _ := parent.Attribute([]byte("class"))
			if class == nil {
				parent.SetAttribute([]byte("class"), data[1:])
			} else {
				classBytes, ok := class.([]byte)
				if ok {
					parent.SetAttribute([]byte("class"), append(classBytes, []byte(" "+string(data[1:]))...))
				}
			}
		case bytes.Contains(data, []byte{'='}):
			// Attribute directive
			key, value, _ := bytes.Cut(data, []byte{'='})
			parent.SetAttribute(key, value)
		default:
			// Unknown directive
			// fmt.Printf("Data = %q\n", data)
		}
	}
	block.Advance(index + 1)
	return nil
}
