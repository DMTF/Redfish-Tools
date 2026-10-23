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
	"github.com/DMTF/redfishRepoTest/src/utils"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

const (
	SchemaTestDefaultFile = "SchemaTest"
)

//nolint:funlen // The table-driven test keeps its related XML cases together.
func GetSchemaTestCases() []csdlTestCase {
	cfg := &config.Config{
		PublishedVersions: map[string]*utils.RedfishNamespaceVersion{
			"Test": {
				Major:  1,
				Minor:  0,
				Errata: 0,
			},
		},
		AllowLists: config.AllowLists{
			PluralSchemaPatterns: []string{"^Bios$", "^Chassis"}, // Use patterns from config.yaml
			NoReleaseTermSchemas: []string{"TestAllowed.v1_0_0"}, // Add TestAllowed for testing
		},
	}
	return []csdlTestCase{
		{
			Name:       "Valid Schema With Content",
			CSDL:       makeSimpleCSDLText("Test_0.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0"/>`) + CSDLStart + `<edmx:DataServices><Schema Namespace="Test_0.v1_0_0"></Schema></edmx:DataServices>` + CSDLEnd,
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "No Content but annotations in schema",
			CSDL:       makeSimpleCSDLText("Test", `<Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test']: Schema must contain at least one non-annotation child",
			},
		},
		{
			Name:       "Invalid Plural Schema Name",
			CSDL:       makeSimpleCSDLText("Resources.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Resources.v1_0_0']: Schema name \"Resources.v1_0_0\" is plural",
			},
		},
		{
			Name:       "Allowed Plural Schema Name (Bios)",
			CSDL:       makeSimpleCSDLText("Bios.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: false, // Bios is in the default allow list
		},
		{
			Name:       "Metrics Pattern Automatically Allowed",
			CSDL:       makeSimpleCSDLText("TestMetrics.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: false, // Metrics.v1 pattern is automatically allowed
		},
		{
			Name:       "Beyond published versions by more than 1",
			CSDL:       makeSimpleCSDLText("Test.v1_2_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				`Warning:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_2_0']: Schema version "Test.v1_2_0" is not in the published versions list and is more than a single version ahead`,
			},
		},
		{
			Name:       "Action Missing Description",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<Action Name="TestAction"><Annotation Term="OData.LongDescription" String="Long test"/></Action><EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']/Action[@Name='TestAction']: Action 'TestAction' does not contain a Description",
			},
		},
		{
			Name:       "Action Missing LongDescription",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<Action Name="TestAction"><Annotation Term="OData.Description" String="Test"/></Action><EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']/Action[@Name='TestAction']: Action 'TestAction' does not contain a LongDescription",
			},
		},
		{
			Name:       "Action Missing Both Descriptions",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<Action Name="TestAction"/><EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']/Action[@Name='TestAction']: Action 'TestAction' does not contain a Description",
				"Error:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']/Action[@Name='TestAction']: Action 'TestAction' does not contain a LongDescription",
			},
		},
		{
			Name:       "Action With Only Binding Parameter",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<Action Name="TestAction"><Annotation Term="OData.Description" String="Test"/><Annotation Term="OData.LongDescription" String="Long test"/><Parameter Name="binding" Type="Test.Actions"/></Action><EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: false, // Binding parameter doesn't need descriptions
		},
		{
			Name:       "Action Parameter Missing Description",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<Action Name="TestAction"><Annotation Term="OData.Description" String="Test"/><Annotation Term="OData.LongDescription" String="Long test"/><Parameter Name="param1" Type="Edm.String"><Annotation Term="OData.LongDescription" String="Long param desc"/></Parameter></Action><EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']/Action[@Name='TestAction']/Parameter[@Name='param1']: Parameter 'param1' of Action 'TestAction' does not contain a Description",
			},
		},
		{
			Name:       "Action Parameter Missing LongDescription",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<Action Name="TestAction"><Annotation Term="OData.Description" String="Test"/><Annotation Term="OData.LongDescription" String="Long test"/><Parameter Name="param1" Type="Edm.String"><Annotation Term="OData.Description" String="Param desc"/></Parameter></Action><EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']/Action[@Name='TestAction']/Parameter[@Name='param1']: Parameter 'param1' of Action 'TestAction' does not contain a LongDescription",
			},
		},
		{
			Name:       "Missing Owning Entity",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']: Schema 'Test.v1_0_0' must contain an owning entity",
			},
		},
		{
			Name:       "Empty Owning Entity",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String=""/><Annotation Term="Redfish.Release" String="1.0.0"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']: Schema 'Test.v1_0_0' must contain an owning entity",
			},
		},
		{
			Name:       "Missing Release Term",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']: Schema 'Test.v1_0_0' must contain a Redfish.Release annotation",
			},
		},
		{
			Name:       "Invalid Release Term",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="1.0.0-alpha"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']: Schema 'Test.v1_0_0' must contain a valid Redfish.Release annotation. '1.0.0-alpha' contains non-allowed characters",
			},
		},
		{
			Name:       "Allowed Missing Release Term",
			CSDL:       makeSimpleCSDLText("TestAllowed.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: false, // TestAllowed should be in the no release term allow list
		},
		{
			Name:       "Trivial Schema No Annotations",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<EntityType Name="Test"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']: Schema 'Test.v1_0_0' must contain an owning entity",
				"Warning:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']: Schema 'Test.v1_0_0' must contain a Redfish.Release annotation",
				"Warning:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']: Trivial namespace schema should have at least one annotation",
			},
		},
		{
			Name:       "Trivial Schema Missing Description",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="2037.1"/><EntityType Name="Test"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:SchemaTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']: Trivial namespace schema should have an OData.Description annotation",
			},
		},
		{
			Name:       "Trivial Schema With Description",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<Annotation Term="OData.Description" String="Test schema description"/><Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/><Annotation Term="Redfish.Release" String="2037.1"/><EntityType Name="Test"/>`),
			FileName:   SchemaTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
	}
}

func TestSchemaTest(t *testing.T) {
	t.Parallel()
	//nolint:paralleltest // The TestFunc calls Parallel...
	for _, tc := range GetSchemaTestCases() {
		t.Run(tc.Name, tc.TestFunc("Schema tests are valid", csdltest.SchemaTest, nil))
	}
}

func TestSchemaTestWithoutPublishedVersionsList(t *testing.T) {
	t.Parallel()
	cfg := &config.Config{
		PublishedVersions: map[string]*utils.RedfishNamespaceVersion{},
	}
	tc := csdlTestCase{
		CSDL: makeSimpleCSDLText("Test.v1_0_1", `
		<Annotation Term="OData.Description" String="Test schema description"/>
		<Annotation Term="RedfishExtensions.v1_0_0.OwningEntity" String="DMTF"/>
		<Annotation Term="Redfish.Release" String="2037.1"/>
		<EntityType Name="Test"/>
		`),
		FileName:   SchemaTestDefaultFile,
		Config:     cfg,
		ExpectFail: false,
	}
	searcher := helperGetSearcherForText(t, tc.FileName, tc.CSDL, "")
	suiteCase := &testsuite.Case{
		Name:   "Schema tests are valid",
		Func:   helperTestWrapper(nil, tc.Config, searcher, csdltest.SchemaTest),
		Buffer: &bytes.Buffer{},
	}
	res := suiteCase.Run()
	assert.Equal(t, tc.ExpectFail, res >= testsuite.Warning)
	require.Len(t, suiteCase.Errors, len(tc.ExpectedErrors))
	for i, err := range suiteCase.Errors {
		assert.Equal(t, tc.ExpectedErrors[i], err.Error())
	}
}
