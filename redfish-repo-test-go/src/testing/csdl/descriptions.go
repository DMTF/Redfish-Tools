/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"errors"
	"fmt"
	"io"
	"os"
	"strings"
	"sync"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"

	"github.com/golangci/misspell"
)

//nolint:gochecknoglobals // Shared misspell replacer to avoid expensive recompilation per file.
var (
	misspellOnce   sync.Once
	sharedReplacer *misspell.Replacer
)

var (
	errFileNotFound    = errors.New("file not found in parser")
	errFileNotSeekable = errors.New("file is not seekable")
	errTextNotFound    = errors.New("misspelled text not found verbatim in file")
)

func getReplacer() *misspell.Replacer {
	misspellOnce.Do(func() {
		sharedReplacer = misspell.New()
	})
	return sharedReplacer
}

func isAutoFix(t *testsuite.Testing) bool {
	return t.Case != nil && t.Case.Suite != nil && t.Case.Suite.AutoFix
}

// applySpellingFix reads the file associated with annotation via the parser's stored handle,
// replaces original with corrected, and writes the corrected content back to disk.
// All surrounding whitespace in the file is preserved exactly as-is.
func applySpellingFix(annotation csdl.Searchable, original, corrected string, searcher *csdl.Searcher) error {
	fileName, _ := searcher.GetPath(annotation)
	fileKey := strings.TrimSuffix(fileName, ".xml")
	file, ok := searcher.GetParser().Files[fileKey]
	if !ok {
		return fmt.Errorf("file not found in parser: %w", errFileNotFound)
	}
	seeker, ok := file.(io.ReadSeeker)
	if !ok {
		return fmt.Errorf("file is not seekable: %w", errFileNotSeekable)
	}
	if _, err := seeker.Seek(0, io.SeekStart); err != nil {
		return err
	}
	content, err := io.ReadAll(seeker)
	if err != nil {
		return err
	}
	// Replace the original annotation string with the corrected one.
	// All surrounding whitespace in the file is preserved as-is.
	newContent := strings.ReplaceAll(string(content), original, corrected)
	if newContent == string(content) {
		return fmt.Errorf("misspelled text not found verbatim in file: %w", errTextNotFound)
	}
	const csdlFileMode = 0644
	return os.WriteFile(
		fileName, []byte(newContent), csdlFileMode,
	)
}

func DescriptionChecks(t *testsuite.Testing, _ units.Units, _ *config.Config, searcher *csdl.Searcher) {
	replacer := getReplacer()
	descriptions := searcher.GetAnnotations("OData.Description")
	for _, description := range descriptions {
		checkDescription(t, description, false, replacer, searcher)
	}
	longDescriptions := searcher.GetAnnotations("OData.LongDescription")
	for _, longDescription := range longDescriptions {
		checkDescription(t, longDescription, true, replacer, searcher)
	}
}

func checkDescription( //nolint:cyclop
	t *testsuite.Testing, annotation *csdl.Annotation, isLong bool,
	replacer *misspell.Replacer, searcher *csdl.Searcher,
) {
	if !strings.HasSuffix(annotation.String, ".") {
		msg := "Missing period at end of description"
		if isLong {
			msg = "Missing period at end of long description"
		}
		t.Error(NewCSDLWarning(annotation, msg, searcher))
	}
	if isLong {
		if strings.Contains(strings.ToLower(annotation.String), " must ") ||
			strings.HasPrefix(annotation.String, "Must ") {
			t.Error(NewCSDLWarning(annotation,
				`Long Description should not contain ISO unallowed word "must"`, searcher))
		}
	}
	corrected, diffs := replacer.Replace(annotation.String)
	if len(diffs) == 0 {
		return
	}
	if isAutoFix(t) {
		if err := applySpellingFix(annotation, annotation.String, corrected, searcher); err == nil {
			return
		}
	}
	for _, diff := range diffs {
		prefix := "Description"
		if isLong {
			prefix = "Long description"
		}
		t.Error(NewCSDLWarning(annotation,
			fmt.Sprintf("%s contains spelling error: %s -> %s", prefix, diff.Original, diff.Corrected), searcher))
	}
}

func DescriptionPendantic(t *testsuite.Testing, _ units.Units, _ *config.Config, searcher *csdl.Searcher) {
	descriptions := searcher.GetAnnotations("OData.Description")
	for _, description := range descriptions {
		// Check for period followed by EOS or double space.
		if !AllPeriodsFollowedByDoubleSpaceOrEos(description.String) {
			t.Error(NewCSDLWarning(description, `Description does not follow period spacing rules`, searcher))
		}
	}
	longDescriptions := searcher.GetAnnotations("OData.LongDescription")
	for _, longDescription := range longDescriptions {
		if !AllPeriodsFollowedByDoubleSpaceOrEos(longDescription.String) {
			t.Error(NewCSDLWarning(longDescription, `Long description does not follow period spacing rules`, searcher))
		}
	}
}

func AllPeriodsFollowedByDoubleSpaceOrEos(s string) bool {
	rest := s
	for len(rest) > 0 {
		idx := strings.Index(rest, ".")
		if idx == -1 || len(rest) <= idx+1 {
			break
		}
		if rest[idx+1] != ' ' {
			return false
		}
		if idx+2 >= len(rest) {
			return false // Trailing space that we don't need...
		}
		if rest[idx+2] != ' ' {
			return false // Double space
		}
		rest = rest[idx+2:]
	}
	return true
}
