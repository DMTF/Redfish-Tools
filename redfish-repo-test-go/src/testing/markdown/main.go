/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package markdown

import (
	"bytes"
	"encoding/json"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/yuin/goldmark/ast"

	"github.com/DMTF/redfishRepoTest/src"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

func CreateTestsFromConfig(cfg *config.Config, list *testsuite.List) error {
	files, err := collectMarkdownFiles(cfg, cfg.SingleFile)
	if err != nil {
		return err
	}
	for _, file := range files {
		suite := list.AddSuite(file)
		mdFile := NewMarkdownFile(file)
		suite.AddTest("Parses as Markdown", mdFile.TestParse)
		suite.AddTest("Validate examples", mdFile.ValidateExamples)
		suite.AddTest("Validate links", mdFile.ValidateLinks)
		suite.Cleanup(func(_ *testsuite.Suite) {
			mdFile.Content = nil
			mdFile.Doc = nil
		})
	}
	return nil
}

func collectMarkdownFiles(cfg *config.Config, singleFile string) ([]string, error) {
	if singleFile != "" {
		if !strings.HasSuffix(singleFile, ".md") {
			return nil, nil
		}
		return []string{singleFile}, nil
	}
	if len(cfg.MarkdownGlobs) == 0 {
		return nil, nil
	}

	seen := make(map[string]struct{})
	files := make([]string, 0)
	for _, pattern := range cfg.MarkdownGlobs {
		matches, err := filepath.Glob(pattern)
		if err != nil {
			return nil, err
		}
		for _, match := range matches {
			if _, ok := seen[match]; ok {
				continue
			}
			seen[match] = struct{}{}
			files = append(files, match)
		}
	}
	sort.Strings(files)
	return files, nil
}

var removeEllipsisRegex = regexp.MustCompile(`\s*\.\.\.\s*(?:<[^>]+>\s*)*`)
var removeTrailingCommaBeforeCloseRegex = regexp.MustCompile(`,\s*([}\]])`)

func validateJSONExample(t *testsuite.Testing, file string, source []byte, node *ast.FencedCodeBlock) {
	content := bytes.TrimSpace(node.Lines().Value(source))
	if bytes.Contains(content, []byte("...")) {
		// Remove ellipsis placeholders. Preserve commas between object keys.
		content = removeEllipsisRegex.ReplaceAll(content, []byte(""))
		// If ellipsis was the last element, clean up the now-dangling trailing comma.
		content = removeTrailingCommaBeforeCloseRegex.ReplaceAll(content, []byte("$1"))
	}
	var parsed any
	if err := json.Unmarshal(content, &parsed); err != nil {
		line := nodeLineNumber(source, node)
		t.Error(src.NewMarkdownSourceError(file, "json-example", line, "invalid json example", src.SeverityWarning, err))
	}
}

func nodeLineNumber(source []byte, node ast.Node) int {
	line := 1
	for curr := node; curr != nil; curr = curr.Parent() {
		pos := curr.Pos()
		if pos < 0 {
			continue
		}
		if pos > len(source) {
			pos = len(source)
		}
		return byteOffsetToLine(source, pos)
	}
	return line
}

func byteOffsetToLine(source []byte, offset int) int {
	if offset <= 0 {
		return 1
	}
	if offset > len(source) {
		offset = len(source)
	}
	line := 1
	for i := range offset {
		if source[i] == '\n' {
			line++
		}
	}
	return line
}

func ParseRawHTMLTag(data []byte) (string, bool) {
	// Check if it's an anchor tag
	if !bytes.HasPrefix(data, []byte("<a ")) {
		return "", false
	}

	// This can either be href="#anchor", id="anchor", or name="anchor"
	if id, ok := getQuotedAttrValue(data, []byte(`id="`)); ok {
		return string(id), true
	}

	if name, ok := getQuotedAttrValue(data, []byte(`name="`)); ok {
		return string(name), true
	}

	href, ok := getQuotedAttrValue(data, []byte(`href="`))
	if !ok {
		return "", false
	}

	return string(bytes.TrimPrefix(href, []byte{'#'})), true
}

func getQuotedAttrValue(data, attrPrefix []byte) ([]byte, bool) {
	start := bytes.Index(data, attrPrefix)
	if start == -1 {
		return nil, false
	}
	start += len(attrPrefix)

	end := bytes.IndexByte(data[start:], '"')
	if end == -1 {
		return nil, false
	}
	return data[start : start+end], true
}
