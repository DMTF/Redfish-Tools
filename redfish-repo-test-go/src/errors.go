/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package src

import (
	"bufio"
	"fmt"
	"io"
	"strconv"
	"strings"

	"github.com/antchfx/xmlquery"
)

type HTTPResponseError struct {
	StatusCode int
}

func (e *HTTPResponseError) Error() string {
	return fmt.Sprintf("http error %d", e.StatusCode)
}

type OutputFormat int

const (
	errorLabel   = "error"
	warningLabel = "warning"
)

const (
	StanardFormat OutputFormat = iota
	GCCFormat
	GoFormat
)

type Formatable interface {
	Format(format OutputFormat) string
}

type Severity int

const (
	SeverityError Severity = iota
	SeverityWarning
	SeverityInfo
)

func (s Severity) String() string {
	switch s {
	case SeverityError:
		return "Error"
	case SeverityWarning:
		return "Warning"
	case SeverityInfo:
		return "Info"
	default:
		return "Unknown"
	}
}

type ServerityError interface {
	error

	GetServerity() Severity
}

type FileLineError interface {
	error

	FileName() string
	Line() int
}

type SeverityFileLineError interface {
	ServerityError
	FileLineError
}

type XMLSourceError struct {
	Filename   string
	XPath      string
	Message    string
	FileLine   int
	FileColumn int
	Level      Severity
	Err        error
}

var _ SeverityFileLineError = (*XMLSourceError)(nil)

func NewXMLSourceError(filename string, xpath string, message string, level Severity, err error) *XMLSourceError {
	return &XMLSourceError{
		Filename: filename,
		XPath:    xpath,
		Message:  message,
		Level:    level,
		Err:      err,
	}
}

func (e *XMLSourceError) Error() string {
	prefix := e.Level.String() + ":" + e.Filename + ":"
	if e.FileLine != 0 {
		prefix += strconv.Itoa(e.FileLine)
	} else {
		prefix += e.XPath
	}
	prefix += ": "
	switch {
	case e.Message != "" && e.Err != nil:
		return prefix + e.Message + ": " + e.Err.Error()
	case e.Err != nil:
		return prefix + e.Err.Error()
	default:
		return prefix + e.Message
	}
}

func (e *XMLSourceError) GetServerity() Severity {
	return e.Level
}

func (e *XMLSourceError) FileName() string {
	return e.Filename
}

func (e *XMLSourceError) Line() int {
	return e.FileLine
}

func (e *XMLSourceError) LookupLineFromFile(file io.ReadSeeker) {
	if e.XPath == "" {
		return
	}
	// Make sure we are always at the start of the file.
	_, err := file.Seek(0, io.SeekStart)
	if err != nil {
		return
	}
	// Parse the XML file.
	doc, err := xmlquery.ParseWithOptions(file, xmlquery.ParserOptions{WithLineNumbers: true})
	if err != nil {
		return
	}
	// Find the node with the given XPath.
	node, err := xmlquery.Query(doc, e.XPath)
	if err != nil {
		return
	}
	// Get the line number of the node.
	e.FileLine = node.LineNumber
	// Get the column number (1-indexed) within that line.
	e.FileColumn = findLineColumn(file, e.FileLine)
}

func (e *XMLSourceError) Format(format OutputFormat) string {
	switch format {
	case StanardFormat:
		return e.Error()
	case GCCFormat:
		errType := errorLabel
		if e.Level >= SeverityWarning {
			errType = warningLabel
		}
		return fmt.Sprintf("%s:%d:%d: %s: %s", e.Filename, e.FileLine, e.FileColumn, errType, e.Message)
	case GoFormat:
		return fmt.Sprintf("%s:%d: %s", e.Filename, e.FileLine, e.Message)
	default:
		return e.Error()
	}
}

type JSONSourceError struct {
	Filename   string
	Path       string
	Message    string
	FileLine   int
	FileColumn int
	Level      Severity
	Err        error
}

var _ SeverityFileLineError = (*JSONSourceError)(nil)

func NewJSONSourceError(filename string, path string, message string, level Severity, err error) *JSONSourceError {
	return &JSONSourceError{
		Filename: filename,
		Path:     path,
		Message:  message,
		Level:    level,
		Err:      err,
	}
}

func (e *JSONSourceError) Error() string {
	prefix := e.Level.String() + ":" + e.Filename + ":"
	if e.FileLine != 0 {
		prefix += strconv.Itoa(e.FileLine)
	} else {
		prefix += e.Path
	}
	prefix += ": "
	switch {
	case e.Message != "" && e.Err != nil:
		return prefix + e.Message + ": " + e.Err.Error()
	case e.Err != nil:
		return prefix + e.Err.Error()
	default:
		return prefix + e.Message
	}
}

func (e *JSONSourceError) GetServerity() Severity {
	return e.Level
}

func (e *JSONSourceError) FileName() string {
	return e.Filename
}

func (e *JSONSourceError) Line() int {
	return e.FileLine
}

func (e *JSONSourceError) LookupLineFromFile(file io.ReadSeeker) {
	_, err := file.Seek(0, io.SeekStart)
	if err != nil {
		return
	}
	scanner := bufio.NewScanner(file)
	lineNumber := 0
	// depth tracks the current JSON nesting level as the scanner advances.
	// Keys in the root object are at depth 1 (inside the opening "{").
	depth := 0
	targetDepth := 1
	pathTags := splitJSONPath(e.Path)
	found := false
	for len(pathTags) > 0 {
		matchedTag, consumedTags, updatedLine, ok := lookupNextJSONPathTag(
			scanner, lineNumber, &depth, targetDepth, pathTags)
		if !ok {
			return
		}
		lineNumber = updatedLine
		pathTags = pathTags[consumedTags:]

		_, arrayIndex, hasArrayIndex := parseJSONPathTag(matchedTag)
		if hasArrayIndex {
			lineNumber, found = lookupArrayIndexLine(scanner, lineNumber, &depth, arrayIndex)
			if !found {
				return
			}
			// depth has been updated to include the element's opening token;
			// next keys to match live at that same depth level.
			targetDepth = depth
			continue
		}

		// depth was updated on the matched key's line (e.g. the "{" that opens
		// a nested object is on the same line as the key).  Next keys live at
		// the new depth.
		targetDepth = depth
		found = true
	}
	if found {
		e.FileLine = lineNumber
		// Get the column number (1-indexed) within that line.
		e.FileColumn = findLineColumn(file, e.FileLine)
	}
}

func (e *JSONSourceError) Format(format OutputFormat) string {
	switch format {
	case StanardFormat:
		return e.Error()
	case GCCFormat:
		errType := errorLabel
		if e.Level >= SeverityWarning {
			errType = warningLabel
		}
		return fmt.Sprintf("%s:%d:%d: %s: %s", e.Filename, e.FileLine, e.FileColumn, errType, e.Message)
	case GoFormat:
		return fmt.Sprintf("%s:%d: %s", e.Filename, e.FileLine, e.Message)
	default:
		return e.Error()
	}
}

type MarkdownSourceError struct {
	Filename   string
	Path       string
	Message    string
	FileLine   int
	FileColumn int
	Level      Severity
	Err        error
}

var _ SeverityFileLineError = (*MarkdownSourceError)(nil)

func NewMarkdownSourceError(
	filename string, path string, line int, message string, level Severity, err error,
) *MarkdownSourceError {
	return &MarkdownSourceError{
		Filename: filename,
		Path:     path,
		Message:  message,
		FileLine: line,
		Level:    level,
		Err:      err,
	}
}

func (e *MarkdownSourceError) Error() string {
	prefix := e.Level.String() + ":" + e.Filename + ":"
	if e.FileLine != 0 {
		prefix += strconv.Itoa(e.FileLine)
	} else {
		prefix += e.Path
	}
	prefix += ": "
	switch {
	case e.Message != "" && e.Err != nil:
		return prefix + e.Message + ": " + e.Err.Error()
	case e.Err != nil:
		return prefix + e.Err.Error()
	default:
		return prefix + e.Message
	}
}

func (e *MarkdownSourceError) GetServerity() Severity {
	return e.Level
}

func (e *MarkdownSourceError) FileName() string {
	return e.Filename
}

func (e *MarkdownSourceError) Line() int {
	return e.FileLine
}

func (e *MarkdownSourceError) LookupLineFromFile(file io.ReadSeeker) {
	if e.FileLine == 0 {
		return
	}
	// Get the column number (1-indexed) within the already-known line.
	e.FileColumn = findLineColumn(file, e.FileLine)
}

func (e *MarkdownSourceError) Format(format OutputFormat) string {
	switch format {
	case StanardFormat:
		return e.Error()
	case GCCFormat:
		errType := errorLabel
		if e.Level >= SeverityWarning {
			errType = warningLabel
		}
		return fmt.Sprintf("%s:%d:%d: %s: %s", e.Filename, e.FileLine, e.FileColumn, errType, e.Message)
	case GoFormat:
		return fmt.Sprintf("%s:%d: %s", e.Filename, e.FileLine, e.Message)
	default:
		return e.Error()
	}
}

type Error struct {
	Severity Severity
	Message  string
}

var _ ServerityError = (*Error)(nil)

func NewError(severity Severity, message string) *Error {
	return &Error{
		Severity: severity,
		Message:  message,
	}
}

func (e *Error) Error() string {
	return e.Message
}

func (e *Error) GetServerity() Severity {
	return e.Severity
}

func (e *Error) Format(format OutputFormat) string {
	switch format {
	case StanardFormat:
		return e.Error()
	case GCCFormat:
		errType := errorLabel
		if e.Severity >= SeverityWarning {
			errType = warningLabel
		}
		return fmt.Sprintf("<general>:0:0: %s: %s", errType, e.Message)
	case GoFormat:
		return "<general>: " + e.Message
	default:
		return e.Error()
	}
}

// findLineColumn returns the 1-indexed column number of the first non-whitespace
// character on lineNumber of file.  It always seeks to the start of the file
// before scanning.  Returns 0 when the line is not found or on a seek error.
func findLineColumn(file io.ReadSeeker, lineNumber int) int {
	if _, err := file.Seek(0, io.SeekStart); err != nil {
		return 0
	}
	scanner := bufio.NewScanner(file)
	current := 0
	for scanner.Scan() {
		current++
		if current == lineNumber {
			line := scanner.Text()
			idx := strings.IndexFunc(line, func(r rune) bool {
				return r != ' ' && r != '\t'
			})
			if idx < 0 {
				return 1
			}
			return idx + 1 // 1-indexed
		}
	}
	return 0
}

func splitJSONPath(path string) []string {
	parts := strings.FieldsFunc(path, func(r rune) bool {
		return r == '/' || r == '.'
	})

	ret := make([]string, 0, len(parts))
	for _, part := range parts {
		if part != "" {
			ret = append(ret, part)
		}
	}

	return ret
}

// lookupNextJSONPathTag advances the scanner looking for a key that matches
// one of the pathTags, but only at targetDepth.  depth is updated on every
// line so the caller can use it to set the targetDepth for the next call.
func lookupNextJSONPathTag(
	scanner *bufio.Scanner, lineNumber int,
	depth *int, targetDepth int,
	pathTags []string,
) (string, int, int, bool) {
	for scanner.Scan() {
		lineNumber++
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		// Record depth before this line's tokens are counted.
		lineDepth := *depth
		*depth += jsonNestingDelta(line)

		if !strings.HasPrefix(line, `"`) {
			continue
		}

		// Only match object keys that sit at the expected nesting level.
		if lineDepth != targetDepth {
			continue
		}

		lineKey, ok := getJSONLineKey(line)
		if !ok {
			continue
		}

		bestConsumed := 0
		bestTag := ""
		for i := 1; i <= len(pathTags); i++ {
			candidate := strings.Join(pathTags[:i], ".")
			candidateTagName, _, _ := parseJSONPathTag(candidate)
			if lineKey == candidateTagName {
				bestConsumed = i
				bestTag = candidate
			}
		}

		if bestConsumed > 0 {
			return bestTag, bestConsumed, lineNumber, true
		}
	}

	return "", 0, lineNumber, false
}

func getJSONLineKey(line string) (string, bool) {
	line = strings.TrimSpace(line)
	if !strings.HasPrefix(line, `"`) {
		return "", false
	}
	keyPortion, _, found := strings.Cut(strings.TrimPrefix(line, `"`), `"`)
	if !found {
		return "", false
	}
	return keyPortion, true
}

func parseJSONPathTag(tag string) (string, int, bool) {
	openIdx := strings.Index(tag, "[")
	closeIdx := strings.Index(tag, "]")
	if closeIdx != len(tag)-1 {
		return tag, 0, false
	}
	if openIdx == -1 || closeIdx == -1 || closeIdx <= openIdx+1 {
		return tag, 0, false
	}
	index, err := strconv.Atoi(tag[openIdx+1 : closeIdx])
	if err != nil {
		return tag, 0, false
	}
	return tag[:openIdx], index, true
}

// lookupArrayIndexLine advances the scanner through a JSON array until it
// reaches the element at targetIndex.  depth is updated on every line so the
// caller receives the nesting depth at the returned line, which it uses to set
// the targetDepth for the next lookupNextJSONPathTag call.
func lookupArrayIndexLine(scanner *bufio.Scanner, lineNumber int, depth *int, targetIndex int) (int, bool) {
	currentIndex := -1
	// nestedDepth tracks nesting relative to the array itself so we know when
	// we're at the top level of the array vs. inside a nested element.
	nestedDepth := 0
	for scanner.Scan() {
		lineNumber++
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "[") {
			*depth += jsonNestingDelta(line)
			continue
		}

		if nestedDepth == 0 && strings.HasPrefix(line, "]") {
			*depth += jsonNestingDelta(line)
			return lineNumber, false
		}

		if nestedDepth == 0 && isJSONArrayValueStart(line) {
			currentIndex++
			if currentIndex == targetIndex {
				*depth += jsonNestingDelta(line)
				return lineNumber, true
			}
		}

		delta := jsonNestingDelta(line)
		nestedDepth += delta
		*depth += delta
		if nestedDepth < 0 {
			nestedDepth = 0
		}
	}

	return lineNumber, false
}

func isJSONArrayValueStart(line string) bool {
	return strings.HasPrefix(line, `"`) || strings.HasPrefix(line, "{") || strings.HasPrefix(line, "[") ||
		strings.HasPrefix(line, "-") || strings.HasPrefix(line, "t") || strings.HasPrefix(line, "f") ||
		strings.HasPrefix(line, "n") || (line[0] >= '0' && line[0] <= '9')
}

func jsonNestingDelta(line string) int {
	return strings.Count(line, "{") + strings.Count(line, "[") - strings.Count(line, "}") - strings.Count(line, "]")
}
