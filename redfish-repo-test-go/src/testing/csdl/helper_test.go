/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"bytes"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	csdlvalidation "github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

const (
	CSDLStart = `<?xml version="1.0" encoding="UTF-8"?>` +
		`<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">`
	CSDLEnd               = `</edmx:DataServices></edmx:Edmx>`
	EmptyValidCSDL        = CSDLStart + `<edmx:DataServices>` + CSDLEnd
	SimpleResourceExample = CSDLStart + `
	<edmx:DataServices>
	<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Resource">
		<EntityType Name="Resource" Abstract="true">
			<Key><PropertyRef Name="Id"/></Key>
			<Property Name="Id" Type="Edm.String" Nullable="false"/>
			<Property Name="Name" Type="Edm.String"/>
			<Property Name="Description" Type="Edm.String"/>
		</EntityType>
		<EntityType Name="ResourceCollection" Abstract="true">
			<Key><PropertyRef Name="Id"/></Key>
			<Property Name="Id" Type="Edm.String" Nullable="false"/>
			<Property Name="Name" Type="Edm.String"/>
			<Property Name="Description" Type="Edm.String"/>
		</EntityType>
	</Schema>
	<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Resource.v1_0_0">
		<EntityType Name="Resource" BaseType="Resource.Resource"></EntityType>
		<EntityType Name="ResourceCollection" BaseType="Resource.ResourceCollection"></EntityType>
	</Schema>` + CSDLEnd
)

type csdlTestCase struct {
	Name           string
	CSDL           string
	FileName       string
	ExtraFiles     map[string]string
	Config         *config.Config
	ExpectFail     bool
	ExpectedErrors []string
}

func helperTestWrapper(unitUtil units.Units, cfg *config.Config, searcher *csdl.Searcher,
	f func(*testsuite.Testing, units.Units, *config.Config, *csdl.Searcher)) func(*testsuite.Testing) {
	return func(t *testsuite.Testing) {
		f(t, unitUtil, cfg, searcher)
	}
}

func makeSimpleCSDLText(schemaName string, content string) string {
	return CSDLStart + `<edmx:DataServices>` +
		`<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="` + schemaName + `">` +
		content + `</Schema>` + CSDLEnd
}

func makeSimpleCSDLTextWithReference(
	refName string, refNamespaces []string, schemaName string, content string,
) string {
	var refBuilder strings.Builder
	refBuilder.WriteString(`<edmx:Reference Uri="http://redfish.dmtf.org/schemas/v1/`)
	refBuilder.WriteString(refName)
	refBuilder.WriteString(`.xml">`)
	for _, ns := range refNamespaces {
		refBuilder.WriteString(`<edmx:Include Namespace="`)
		refBuilder.WriteString(ns)
		refBuilder.WriteString(`"/>`)
	}
	refBuilder.WriteString(`</edmx:Reference>`)
	var csdlBuilder strings.Builder
	csdlBuilder.WriteString(CSDLStart)
	csdlBuilder.WriteString(refBuilder.String())
	csdlBuilder.WriteString(`<edmx:DataServices>`)
	csdlBuilder.WriteString(`<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="`)
	csdlBuilder.WriteString(schemaName)
	csdlBuilder.WriteString(`">`)
	csdlBuilder.WriteString(content)
	csdlBuilder.WriteString(`</Schema>`)
	csdlBuilder.WriteString(CSDLEnd)
	return csdlBuilder.String()
}

func helperGetSearcherForText(tb testing.TB, fileName string, xml string, directory string) *csdl.Searcher {
	tb.Helper()
	buffer := bytes.NewBufferString(xml)
	closer := io.NopCloser(buffer)
	parser := csdl.NewParser()
	opts := []csdl.ParseOption{}
	if directory != "" {
		opts = append(opts, csdl.WithLocalReferenceLookup(directory))
	}
	parser.AddFile(fileName, closer)
	_, err := parser.Parse(opts...)
	if err != nil {
		tb.Fatal(err)
	}
	return csdl.NewSearcher(parser)
}

func helperSetupOtherFiles(tb testing.TB, files map[string]string) string {
	tb.Helper()
	if len(files) == 0 {
		return ""
	}
	tempDir := tb.TempDir()
	for fileName, content := range files {
		err := os.WriteFile(filepath.Join(tempDir, fileName), []byte(content), 0600)
		if err != nil {
			tb.Fatal(err)
		}
	}
	tb.Cleanup(func() {
		_ = os.RemoveAll(tempDir)
	})
	return tempDir
}

// helperGetSearcherForFileContent writes content to a real temp file, opens it,
// and returns a Searcher backed by that file along with the file's path on disk.
// Unlike helperGetSearcherForText, the resulting parser file is an *os.File and
// therefore implements io.ReadSeeker, which is required for AutoFix support.
func helperGetSearcherForFileContent(tb testing.TB, fileName, content string) (*csdl.Searcher, string) {
	tb.Helper()
	dir := tb.TempDir()
	filePath := filepath.Join(dir, fileName+".xml")
	err := os.WriteFile(filePath, []byte(content), 0600) //nolint:gosec // test-only write to temp dir
	require.NoError(tb, err)

	file, err := os.Open(filePath) //nolint:gosec // test-only read from temp dir
	require.NoError(tb, err)
	tb.Cleanup(func() { _ = file.Close() })

	parser := csdl.NewParser()
	parser.AddFile(filePath, file)
	_, err = parser.Parse()
	require.NoError(tb, err)

	return csdl.NewSearcher(parser), filePath
}

func (tc *csdlTestCase) TestFunc(name string,
	testFunc csdlvalidation.CSDLTestFunc,
	units units.Units) func(*testing.T) {
	//nolint:thelper // This is the actual test function not a helper.
	return func(t *testing.T) {
		t.Parallel()
		otherDir := helperSetupOtherFiles(t, tc.ExtraFiles)
		searcher := helperGetSearcherForText(t, tc.FileName, tc.CSDL, otherDir)
		suiteCase := &testsuite.Case{
			Name:   name,
			Func:   helperTestWrapper(units, tc.Config, searcher, testFunc),
			Buffer: &bytes.Buffer{},
		}
		if tc.Config != nil {
			tc.Config.CompileRegexes()
		}
		res := suiteCase.Run()
		assert.Equal(t, tc.ExpectFail, res >= testsuite.Warning)
		require.Len(t, suiteCase.Errors, len(tc.ExpectedErrors))
		for i, err := range suiteCase.Errors {
			assert.Equal(t, tc.ExpectedErrors[i], err.Error())
		}
	}
}
