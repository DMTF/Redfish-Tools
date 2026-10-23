/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"bytes"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	csdltest "github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

const (
	URITestDefaultFile = "URITest"
)

func GetURITestCases() []csdlTestCase {
	cfg := &config.Config{}
	return []csdlTestCase{
		{
			Name:       "Versioned Schema No URI Required",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   URITestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Unversioned Schema No URI Annotation",
			CSDL:       makeSimpleCSDLText("Test", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   URITestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:URITest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test']: Unversioned schemas must contain a Redfish.Uris annotation",
			},
		},
		{
			Name:       "Unversioned Schema In Allow List",
			CSDL:       makeSimpleCSDLText("AllowedSchema", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   URITestDefaultFile,
			Config:     &config.Config{AllowLists: config.AllowLists{NoURISchemas: []string{"AllowedSchema"}}},
			ExpectFail: false,
		},
		{
			Name:       "Versioned Schema With Multiple Dots",
			CSDL:       makeSimpleCSDLText("Test.v1_2_3", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   URITestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Schema With V1 But Not Versioned",
			CSDL:       makeSimpleCSDLText("V1Test", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   URITestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:URITest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='V1Test']: Unversioned schemas must contain a Redfish.Uris annotation",
			},
		},
	}
}

func TestURIChecks(t *testing.T) {
	t.Parallel()
	for _, tc := range GetURITestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			searcher := helperGetSearcherForText(t, tc.FileName, tc.CSDL, "")
			suiteCase := &testsuite.Case{
				Name:   "URI checks are valid",
				Func:   helperTestWrapper(nil, tc.Config, searcher, csdltest.URIChecks),
				Buffer: &bytes.Buffer{},
			}
			res := suiteCase.Run()
			assert.Equal(t, tc.ExpectFail, res >= testsuite.Warning)
			require.Len(t, suiteCase.Errors, len(tc.ExpectedErrors))
			for i, err := range suiteCase.Errors {
				assert.Equal(t, tc.ExpectedErrors[i], err.Error())
			}
		})
	}
}

// Test URI validation edge cases.
func TestURIChecksEdgeCases(t *testing.T) {
	t.Parallel()
	edgeCaseTests := []csdlTestCase{
		{
			Name: "Schema With Only Numbers",
			CSDL: makeSimpleCSDLText("123", `
			<EntityType Name="Test">
				<Property Name="TestProp" Type="Edm.String"/>
			</EntityType>`),
			FileName:   URITestDefaultFile,
			Config:     &config.Config{},
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:URITest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='123']: Unversioned schemas must contain a Redfish.Uris annotation",
			},
		},
		{
			Name: "All Schemas In Allow List",
			CSDL: makeSimpleCSDLText("Allowed1", `
			<EntityType Name="Test1">
				<Property Name="TestProp" Type="Edm.String"/>
			</EntityType>`) + makeSimpleCSDLText("Allowed2", `
			<EntityType Name="Test2">
				<Property Name="TestProp" Type="Edm.String"/>
			</EntityType>`),
			FileName:   URITestDefaultFile,
			Config:     &config.Config{AllowLists: config.AllowLists{NoURISchemas: []string{"Allowed1", "Allowed2"}}},
			ExpectFail: false,
		},
	}

	for _, tc := range edgeCaseTests {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			searcher := helperGetSearcherForText(t, tc.FileName, tc.CSDL, "")
			suiteCase := &testsuite.Case{
				Name:   "URI edge case checks are valid",
				Func:   helperTestWrapper(nil, tc.Config, searcher, csdltest.URIChecks),
				Buffer: &bytes.Buffer{},
			}
			res := suiteCase.Run()
			assert.Equal(t, tc.ExpectFail, res >= testsuite.Warning)
			require.Len(t, suiteCase.Errors, len(tc.ExpectedErrors))
			for i, err := range suiteCase.Errors {
				assert.Equal(t, tc.ExpectedErrors[i], err.Error())
			}
		})
	}
}

// Test configuration edge cases.
func TestURIChecksConfig(t *testing.T) {
	t.Parallel()

	configTests := []struct {
		name       string
		config     *config.Config
		expectFail bool
		errors     []string
	}{
		{
			name:       "Empty Allow List",
			config:     &config.Config{AllowLists: config.AllowLists{NoURISchemas: []string{}}},
			expectFail: true,
			errors:     []string{"Warning:URITest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test']: Unversioned schemas must contain a Redfish.Uris annotation"},
		},
		{
			name:       "Non-matching Allow List",
			config:     &config.Config{AllowLists: config.AllowLists{NoURISchemas: []string{"OtherSchema"}}},
			expectFail: true,
			errors:     []string{"Warning:URITest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test']: Unversioned schemas must contain a Redfish.Uris annotation"},
		},
	}

	baseCSDL := makeSimpleCSDLText("Test", `
	<EntityType Name="Test">
		<Property Name="TestProp" Type="Edm.String"/>
	</EntityType>`)

	for _, tc := range configTests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			searcher := helperGetSearcherForText(t, URITestDefaultFile, baseCSDL, "")
			suiteCase := &testsuite.Case{
				Name:   "URI config checks are valid",
				Func:   helperTestWrapper(nil, tc.config, searcher, csdltest.URIChecks),
				Buffer: &bytes.Buffer{},
			}
			res := suiteCase.Run()
			assert.Equal(t, tc.expectFail, res >= testsuite.Warning)
			require.Len(t, suiteCase.Errors, len(tc.errors))
			for i, err := range suiteCase.Errors {
				assert.Equal(t, tc.errors[i], err.Error())
			}
		})
	}
}
