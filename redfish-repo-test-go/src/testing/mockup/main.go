/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup

import (
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/pboyd04/gocsdl/pkg/csdl"
)

func CreateTestsFromConfig(cfg *config.Config, list *testsuite.List) error {
	if cfg.CSDLCache == nil {
		// Need to go and parse the CSDL if we are running just the mockup tests.
		log.Printf("Running only mockup tests not implemented yet.\n")
		return nil
	}
	list.AddSetup(func() {
		typeMap, searcher := MakeSearcherFromCache(cfg.CSDLCache)
		descendantIdx := BuildDescendantIndex(typeMap)
		for _, suite := range list.Suites {
			suite.AddAttribute("typeMap", typeMap)
			suite.AddAttribute("searcher", searcher)
			suite.AddAttribute("descendantIdx", descendantIdx)
		}
	})
	if cfg.SingleFile != "" {
		if !strings.HasSuffix(cfg.SingleFile, ".json") {
			// Not a Mockup file, skip it
			return nil
		}
		// Need to test the whole mockup for consistency...
		log.Printf("Running only mockup test for single file %s not implemented yet.\n", cfg.SingleFile)
		return nil
	}
	entries, err := os.ReadDir(cfg.MockupDirectory)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		if entry.IsDir() {
			err := CreateTestForDirectory(filepath.Join(cfg.MockupDirectory, entry.Name()), cfg, list)
			if err != nil {
				return err
			}
		}
	}
	return nil
}

func CreateTestForDirectory(directory string, cfg *config.Config, list *testsuite.List) error {
	mockup := NewMockup(directory, cfg)
	suite := list.AddSuite(mockup.Name)
	suite.AddTest("All files are UTF8 and JSON", mockup.Load)
	suite.AddTest("Copyrights are valid", mockup.CopyrightTest)
	suite.AddTest("File Root Types are valid", mockup.FileTypesAreValid)
	suite.AddTest("File Content matches type", mockup.ContentMatchesType)
	if strings.Contains(mockup.Name, "public") {
		suite.AddTest("Explorer config is present and sane", mockup.ExplorerTest)
	}
	suite.Cleanup(func(suite *testsuite.Suite) {
		// Do error line look ups...
		mockup.LookupErrorLines(suite.Errors)
		_ = mockup.Close()
		mockup.files = nil
		mockup.types = nil
		mockup.descendantIdx = nil
		mockup.searcher = nil
	})
	return nil
}

func MakeSearcherFromCache(cache csdl.ExternalCache) (map[string]*csdl.Type, *csdl.Searcher) {
	parsers := csdl.NewParserFromCache(cache)
	types, err := parsers.Parse(csdl.WithSkipFileRead())
	if err != nil {
		log.Printf("Failed to parse CSDL: %v", err)
	}
	searcher := csdl.NewSearcher(parsers)
	return types, searcher
}

type testFunction func(*testsuite.Testing, map[string]any, *config.Config, map[string]*csdl.Type)

func TestWrapper(f testFunction) func(*testsuite.Testing) {
	return func(t *testsuite.Testing) {
		content, ok := t.GetAttr("json").(map[string]any)
		if !ok {
			t.Fatal("Units not found")
		}
		cfg, ok := t.GetAttr("cfg").(*config.Config)
		if !ok {
			t.Fatal("Config not found")
		}
		typeMap, ok := t.GetAttr("typeMap").(map[string]*csdl.Type)
		if !ok {
			t.Fatal("Type map not found")
		}
		f(t, content, cfg, typeMap)
	}
}
