/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"os"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/require"
)

func ParseTest(t *testsuite.Testing) {
	cfg, ok := t.GetAttr("cfg").(*config.Config)
	if !ok {
		t.Fatal("Config not found")
	}

	csdlParser := csdl.NewParser()

	fileName := GetFileNameFromTest(t)
	//nolint:gosec // This is a testsuite
	file, err := os.Open(fileName)
	if err != nil {
		t.Fatal(err)
	}
	// Don't close the file, it's needed for looking up error line numbers.
	csdlParser.AddFile(fileName, file)

	typeMap, err := csdlParser.Parse(csdl.WithLocalReferenceLookup(cfg.CSDLDirectory),
		csdl.WithExternalParseCache(cfg.CSDLCache))
	require.NoError(t, err)
	require.NotNil(t, typeMap)

	t.Attr("typeMap", typeMap)
	t.Attr("searcher", csdl.NewSearcher(csdlParser))
}

func GetFileNameFromTest(t *testsuite.Testing) string {
	if t.Case.Suite == nil {
		return ""
	}
	return t.Case.Suite.Name
}
