/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"errors"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
)

var PascalRegex = regexp.MustCompile("^([A-Z][a-z0-9]*)+$")

func CreateTestsFromConfig(cfg *config.Config, list *testsuite.List, units units.Units) error {
	var entries []os.DirEntry
	var err error
	if cfg.SingleFile != "" {
		if !strings.HasSuffix(cfg.SingleFile, ".xml") {
			// Not a CSDL file, skip it
			return nil
		}
		CreateTestForFile(cfg.SingleFile, cfg, list, units)
	} else {
		entries, err = os.ReadDir(cfg.CSDLDirectory)
		if err != nil {
			return err
		}
	}
	if cfg.CSDLCache == nil {
		cfg.CSDLCache = &config.ExternalThreadSafeCache{}
	}
	slices.SortFunc(entries, func(a, b os.DirEntry) int {
		return strings.Compare(a.Name(), b.Name())
	})
	cfg.WorkerPool.Run(len(entries), func(i int) {
		entry := entries[i]
		if entry.IsDir() {
			return
		}
		if !strings.HasSuffix(entry.Name(), ".xml") {
			return
		}
		if slices.Contains(cfg.ExternalSchemas, filepath.Base(strings.TrimSuffix(entry.Name(), ".xml"))) {
			return
		}
		CreateTestForFile(filepath.Join(cfg.CSDLDirectory, entry.Name()), cfg, list, units)
	})
	return nil
}

func CreateTestForFile(filePath string, cfg *config.Config, list *testsuite.List, units units.Units) {
	suite := list.AddSuite(filePath)
	suite.AddAttribute("cfg", cfg)
	suite.AddAttribute("units", units)
	suite.AddTest("Valid Syntax", ParseTest)
	suite.AddTest("Units are valid", TestWrapper(ValidateUnits))
	suite.AddTest("Schemas have permissions", TestWrapper(SchemasHavePermissions))
	suite.AddTest("Descriptions are valid", TestWrapper(DescriptionChecks))
	suite.AddTest("Schemas are valid", TestWrapper(SchemaTest))
	suite.AddTest("Entities are valid", TestWrapper(EntityChecks))
	suite.AddTest("Complex types are valid", TestWrapper(ComplexTypeChecks))
	suite.AddTest("Annotations are valid", TestWrapper(AnnotationChecks))
	suite.AddTest("Enums are valid", TestWrapper(EnumChecks))
	suite.AddTest("Properties are valid", TestWrapper(PropertyChecks))
	suite.AddTest("Actions are valid", TestWrapper(ActionChecks))
	suite.AddTest("References are valid", TestWrapper(ReferenceCheck))
	suite.AddTest("URIs are valid", TestWrapper(URIChecks))
	if cfg.IncludePedanticTests {
		suite.AddTest("Descriptions are valid (pendantic)", TestWrapper(DescriptionPendantic))
		suite.AddTest("References are valid (pendantic)", TestWrapper(ReferenceCheckPedantic))
	}
	suite.Cleanup(func(suite *testsuite.Suite) {
		// Do error line look ups...
		searcher, ok := suite.GetAttribute("searcher").(*csdl.Searcher)
		if ok {
			lookupErrorLines(suite.Errors, searcher)
		}
		// The status and errors are sufficient for reporting. Release the
		// per-file parse graph once error locations have been resolved.
		suite.AddAttribute("typeMap", nil)
		suite.AddAttribute("searcher", nil)
	})
}

func lookupErrorLines(errs []error, searcher *csdl.Searcher) {
	for _, err := range errs {
		var xmlErr *src.XMLSourceError
		if !errors.As(err, &xmlErr) {
			continue
		}
		file, ok := searcher.GetParser().Files[strings.TrimSuffix(xmlErr.Filename, ".xml")]
		if !ok {
			continue
		}
		seeker, ok := file.(io.ReadSeeker)
		if !ok {
			continue
		}
		xmlErr.LookupLineFromFile(seeker)
	}
}

type CSDLTestFunc func(*testsuite.Testing, units.Units, *config.Config, *csdl.Searcher)

func TestWrapper(f CSDLTestFunc) func(*testsuite.Testing) {
	return func(t *testsuite.Testing) {
		unitUtil, ok := t.GetAttr("units").(units.Units)
		if !ok {
			t.Fatal("Units not found")
		}
		cfg, ok := t.GetAttr("cfg").(*config.Config)
		if !ok {
			t.Fatal("Config not found")
		}
		searcher, ok := t.GetAttr("searcher").(*csdl.Searcher)
		if !ok {
			t.Fatal("Searcher not found")
		}
		f(t, unitUtil, cfg, searcher)
	}
}
