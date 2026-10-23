/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

const ParseFileName = "Parse.xml"

func TestParseTest_NoConfig(t *testing.T) {
	t.Parallel()

	// Create a test case without config
	suiteCase := &testsuite.Case{
		Name:   "Parse test without config",
		Func:   csdl.ParseTest,
		Buffer: &bytes.Buffer{},
		Suite:  &testsuite.Suite{Name: ParseFileName},
	}
	assert.NotPanics(t, func() {
		suiteCase.Run()
	})
}

func TestParseTest_FileOpenError(t *testing.T) {
	t.Parallel()

	// Create a test case with non-existent file
	suiteCase := &testsuite.Case{
		Func:   csdl.ParseTest,
		Name:   "Parse test with non-existent file",
		Suite:  &testsuite.Suite{Name: "non_existent_file.xml"},
		Buffer: &bytes.Buffer{},
	}

	// Set config attribute
	cfg := &config.Config{}
	suiteCase.Suite.AddAttribute("cfg", cfg)

	assert.NotPanics(t, func() {
		suiteCase.Run()
	})
}

func TestParseTest_MalformedXML(t *testing.T) {
	t.Parallel()

	// Create a temporary file with malformed XML
	tempDir := t.TempDir()
	malformedXMLFile := filepath.Join(tempDir, "malformed.xml")
	malformedContent := `<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
	<edmx:DataServices>
		<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Test">
			<EntityType Name="Test"
				<Property Name="TestProp" Type="Edm.String"/>
			</EntityType>
		</Schema>
	</edmx:DataServices>
</edmx:Edmx>` // Missing closing > for EntityType opening tag

	err := os.WriteFile(malformedXMLFile, []byte(malformedContent), 0600)
	require.NoError(t, err)

	// Create a test case with malformed XML file
	suiteCase := &testsuite.Case{
		Name:   "Parse test with malformed XML",
		Func:   csdl.ParseTest,
		Suite:  &testsuite.Suite{Name: malformedXMLFile},
		Buffer: &bytes.Buffer{},
	}

	// Set config attribute
	cfg := &config.Config{
		CSDLDirectory: tempDir,
	}
	suiteCase.Suite.AddAttribute("cfg", cfg)

	// This should not panic but should result in a failed test case
	assert.NotPanics(t, func() {
		suiteCase.Run()
	})

	// Check that the test case failed (has errors)
	assert.Greater(t, suiteCase.Status, testsuite.Success)
}

func TestParseTest_EmptyFile(t *testing.T) {
	t.Parallel()

	// Create a temporary empty file
	tempDir := t.TempDir()
	emptyFile := filepath.Join(tempDir, "empty.xml")
	err := os.WriteFile(emptyFile, []byte(""), 0600)
	require.NoError(t, err)

	// Create a test case with empty file
	suiteCase := &testsuite.Case{
		Name:   "Parse test with empty file",
		Func:   csdl.ParseTest,
		Suite:  &testsuite.Suite{Name: emptyFile},
		Buffer: &bytes.Buffer{},
	}

	// Set config attribute
	cfg := &config.Config{
		CSDLDirectory: tempDir,
	}
	suiteCase.Suite.AddAttribute("cfg", cfg)

	// This should not panic but should result in a failed test case
	assert.NotPanics(t, func() {
		suiteCase.Run()
	})

	// Check that the test case failed (has errors)
	assert.Greater(t, suiteCase.Status, testsuite.Success)
}

func TestParseTest_ValidCSDL(t *testing.T) {
	t.Parallel()

	// Create a temporary file with valid CSDL
	tempDir := t.TempDir()
	validCSDLFile := filepath.Join(tempDir, "valid.xml")
	validCSDLContent := `<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
	<edmx:DataServices>
		<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Test">
			<EntityType Name="Test">
				<Property Name="TestProp" Type="Edm.String"/>
			</EntityType>
		</Schema>
	</edmx:DataServices>
</edmx:Edmx>`

	err := os.WriteFile(validCSDLFile, []byte(validCSDLContent), 0600)
	require.NoError(t, err)

	// Create a test case with valid CSDL file
	suiteCase := &testsuite.Case{
		Name:   "Parse test with valid CSDL",
		Func:   csdl.ParseTest,
		Suite:  &testsuite.Suite{Name: validCSDLFile},
		Buffer: &bytes.Buffer{},
	}

	// Set config attribute
	cfg := &config.Config{
		CSDLDirectory: tempDir,
	}
	suiteCase.Suite.AddAttribute("cfg", cfg)

	// This should succeed without panicking
	assert.NotPanics(t, func() {
		suiteCase.Run()
	})

	// Check that the test case passed
	assert.Equal(t, testsuite.Success, suiteCase.Status)

	// Verify that typeMap and searcher were set
	typeMap := suiteCase.Suite.GetAttribute("typeMap")
	assert.NotNil(t, typeMap)

	searcher := suiteCase.Suite.GetAttribute("searcher")
	assert.NotNil(t, searcher)
}
