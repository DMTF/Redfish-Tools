/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/DMTF/redfishRepoTest/src/units/ucum"
	"github.com/stretchr/testify/require"
)

const (
	PropertiesTestDefaultFile = "PropertiesTest"
)

//nolint:funlen // The table-driven test keeps its related XML cases together.
func GetPropertiesTestCases() []csdlTestCase {
	cfg := &config.Config{
		AllowLists: config.AllowLists{
			NonPascalProperties:          []string{"Legacy.*"},
			PropertiesWithIncorrectUnits: []string{"BadUnit.*"},
			UnknownTypeReferences:        []string{"Unknown.*"},
		},
	}
	return []csdlTestCase{
		{
			Name:       "No Properties",
			CSDL:       EmptyValidCSDL,
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Valid Property",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="ValidProperty" Type="Edm.String"><Annotation Term="OData.Description" String="Test description"/><Annotation Term="OData.LongDescription" String="Test long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Invalid Property Name",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="invalidProperty" Type="Edm.String"><Annotation Term="OData.Description" String="Test description"/><Annotation Term="OData.LongDescription" String="Test long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/Property[@Name='invalidProperty']: Property name should be PascalCased: \"invalidProperty\"",
			},
		},
		{
			Name:       "Legacy Property Name Allowed",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="Legacy_Property" Type="Edm.String"><Annotation Term="OData.Description" String="Test description"/><Annotation Term="OData.LongDescription" String="Test long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property Missing Description",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="TestProperty" Type="Edm.String"><Annotation Term="OData.LongDescription" String="Test long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/Property[@Name='TestProperty']: Property 'TestProperty' does not contain a Description",
			},
		},
		{
			Name:       "Property Missing LongDescription",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="TestProperty" Type="Edm.String"><Annotation Term="OData.Description" String="Test description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/Property[@Name='TestProperty']: Property 'TestProperty' does not contain a LongDescription",
			},
		},
		{
			Name:       "Property Missing Both Descriptions",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="TestProperty" Type="Edm.String"/></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/Property[@Name='TestProperty']: Property 'TestProperty' does not contain a Description",
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/Property[@Name='TestProperty']: Property 'TestProperty' does not contain a LongDescription",
			},
		},
		{
			Name:       "Name Property No Descriptions Allowed",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="Name" Type="Edm.String"/></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Id Property No Descriptions Allowed",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="Id" Type="Edm.String"/></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Description Property No Descriptions Allowed",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="Description" Type="Edm.String"/></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property With Correct Units",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="PropertyVolts" Type="Edm.Double"><Annotation Term="OData.Description" String="Voltage property"/><Annotation Term="OData.LongDescription" String="Voltage property long description"/><Annotation Term="Measures.Unit" String="V"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property With Incorrect Units",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="WrongVoltageProperty" Type="Edm.Double"><Annotation Term="OData.Description" String="Wrong voltage property"/><Annotation Term="OData.LongDescription" String="Wrong voltage property long description"/><Annotation Term="Measures.Unit" String="V"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/Property[@Name='WrongVoltageProperty']: Property WrongVoltageProperty should have unit Volt in its name",
			},
		},
		{
			Name:       "Property With Bad Unit Allowed",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="BadUnitProperty" Type="Edm.Double"><Annotation Term="OData.Description" String="Bad unit property"/><Annotation Term="OData.LongDescription" String="Bad unit property long description"/><Annotation Term="Measures.Unit" String="V"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property With Percentage Units",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="PercentProperty" Type="Edm.Double"><Annotation Term="OData.Description" String="Percent property"/><Annotation Term="OData.LongDescription" String="Percent property long description"/><Annotation Term="Measures.Unit" String="%"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property With Alternative Unit Name",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="PropertyGbps" Type="Edm.Double"><Annotation Term="OData.Description" String="Gbps property"/><Annotation Term="OData.LongDescription" String="Gbps property long description"/><Annotation Term="Measures.Unit" String="Gbit/s"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property With No Units",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="NoUnitProperty" Type="Edm.String"><Annotation Term="OData.Description" String="No unit property"/><Annotation Term="OData.LongDescription" String="No unit property long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property With Valid Type",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="StringProperty" Type="Edm.String"><Annotation Term="OData.Description" String="String property"/><Annotation Term="OData.LongDescription" String="String property long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property With Complex Type",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<ComplexType Name="TestComplex"><Property Name="InnerProp" Type="Edm.String"><Annotation Term="OData.Description" String="Inner property"/><Annotation Term="OData.LongDescription" String="Inner property long description"/></Property></ComplexType><EntityType Name="Test"><Property Name="ComplexProperty" Type="PropertiesTest.TestComplex"><Annotation Term="OData.Description" String="Complex property"/><Annotation Term="OData.LongDescription" String="Complex property long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property With Enum Type",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EnumType Name="TestEnum"><Member Name="Member1"/></EnumType><EntityType Name="Test"><Property Name="EnumProperty" Type="PropertiesTest.TestEnum"><Annotation Term="OData.Description" String="Enum property"/><Annotation Term="OData.LongDescription" String="Enum property long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property With TypeDefinition Base Type",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<TypeDefinition Name="TestTypeDef" BaseType="Edm.String"/><EntityType Name="Test"><Property Name="TypeDefProperty" Type="PropertiesTest.TestTypeDef"><Annotation Term="OData.Description" String="TypeDef property"/><Annotation Term="OData.LongDescription" String="TypeDef property long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property With Invalid Type Not In Allow List",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="InvalidTypeProperty" Type="PropertiesTest.InvalidType"><Annotation Term="OData.Description" String="Invalid type property"/><Annotation Term="OData.LongDescription" String="Invalid type property long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/Property[@Name='InvalidTypeProperty']: Property InvalidTypeProperty does not contain a valid type has 'PropertiesTest.InvalidType'",
			},
		},
		{
			Name:       "Property With Unknown Type Allowed",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="UnknownAllowedProperty" Type="PropertiesTest.UnknownAllowedType"><Annotation Term="OData.Description" String="Unknown allowed type property"/><Annotation Term="OData.LongDescription" String="Unknown allowed type property long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Collection Property With Valid Type",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="CollectionProperty" Type="Collection(Edm.String)"><Annotation Term="OData.Description" String="Collection property"/><Annotation Term="OData.LongDescription" String="Collection property long description"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Valid Navigation Property",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><NavigationProperty Name="ValidNavProperty" Type="PropertiesTest.TargetEntity"><Annotation Term="OData.Description" String="Valid nav property"/><Annotation Term="OData.LongDescription" String="Valid nav property long description"/></NavigationProperty></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Invalid Navigation Property Name",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><NavigationProperty Name="invalidNavProperty" Type="PropertiesTest.TargetEntity"><Annotation Term="OData.Description" String="Invalid nav property"/><Annotation Term="OData.LongDescription" String="Invalid nav property long description"/></NavigationProperty></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/NavigationProperty[@Name='invalidNavProperty']: NavigationProperty name should be PascalCased: \"invalidNavProperty\"",
			},
		},
		{
			Name:       "Navigation Property Missing Description",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><NavigationProperty Name="NavProperty" Type="PropertiesTest.TargetEntity"><Annotation Term="OData.LongDescription" String="Nav property long description"/></NavigationProperty></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/NavigationProperty[@Name='NavProperty']: NavigationProperty 'NavProperty' does not contain a Description",
			},
		},
		{
			Name:       "Navigation Property Missing LongDescription",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><NavigationProperty Name="NavProperty" Type="PropertiesTest.TargetEntity"><Annotation Term="OData.Description" String="Nav property"/></NavigationProperty></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/NavigationProperty[@Name='NavProperty']: NavigationProperty 'NavProperty' does not contain a LongDescription",
			},
		},
		{
			Name:       "Navigation Property Collection Not Nullable",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><NavigationProperty Name="CollectionNavProperty" Type="Collection(PropertiesTest.TargetEntity)" Nullable="true"><Annotation Term="OData.Description" String="Collection nav property"/><Annotation Term="OData.LongDescription" String="Collection nav property long description"/></NavigationProperty></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/NavigationProperty[@Name='CollectionNavProperty']: NavigationProperty 'CollectionNavProperty' should not be nullable as it is a collection type.",
			},
		},
		{
			Name:       "Navigation Property Collection Nullable Null",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><NavigationProperty Name="CollectionNavProperty" Type="Collection(PropertiesTest.TargetEntity)"><Annotation Term="OData.Description" String="Collection nav property"/><Annotation Term="OData.LongDescription" String="Collection nav property long description"/></NavigationProperty></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Navigation Property Not Collection Nullable",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><NavigationProperty Name="SingleNavProperty" Type="PropertiesTest.TargetEntity" Nullable="true"><Annotation Term="OData.Description" String="Single nav property"/><Annotation Term="OData.LongDescription" String="Single nav property long description"/></NavigationProperty></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Multiple Properties Mixed",
			CSDL:       makeSimpleCSDLText(PropertiesTestDefaultFile, `<EntityType Name="Test"><Property Name="ValidProp" Type="Edm.String"><Annotation Term="OData.Description" String="Valid property"/><Annotation Term="OData.LongDescription" String="Valid property long description"/></Property><Property Name="invalidProp" Type="Edm.String"/><NavigationProperty Name="ValidNavProp" Type="PropertiesTest.TargetEntity"><Annotation Term="OData.Description" String="Valid nav property"/><Annotation Term="OData.LongDescription" String="Valid nav property long description"/></NavigationProperty><NavigationProperty Name="invalidNavProp" Type="PropertiesTest.TargetEntity"/></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/Property[@Name='invalidProp']: Property name should be PascalCased: \"invalidProp\"",
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/Property[@Name='invalidProp']: Property 'invalidProp' does not contain a Description",
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/Property[@Name='invalidProp']: Property 'invalidProp' does not contain a LongDescription",
				"Warning:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/NavigationProperty[@Name='invalidNavProp']: NavigationProperty name should be PascalCased: \"invalidNavProp\"",
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/NavigationProperty[@Name='invalidNavProp']: NavigationProperty 'invalidNavProp' does not contain a Description",
				"Error:PropertiesTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PropertiesTest']/EntityType[@Name='Test']/NavigationProperty[@Name='invalidNavProp']: NavigationProperty 'invalidNavProp' does not contain a LongDescription",
			},
		},
	}
}

func TestPropertyChecks(t *testing.T) {
	t.Parallel()
	unitUtil, err := ucum.LoadFromFile(filepath.Join(t.TempDir(), "ucum.json"))
	require.NoError(t, err)
	//nolint:paralleltest // The TestFunc calls Parallel...
	for _, tc := range GetPropertiesTestCases() {
		t.Run(tc.Name, tc.TestFunc("Property checks are valid", csdl.PropertyChecks, unitUtil))
	}
}

//nolint:funlen // Long test case function.
func GetPropertiesTestCasesNoUnits() []csdlTestCase {
	cfg := &config.Config{
		AllowLists: config.AllowLists{
			NonPascalProperties:          []string{"Legacy.*"},
			PropertiesWithIncorrectUnits: []string{"BadUnit.*"},
			UnknownTypeReferences:        []string{"Unknown.*"},
		},
	}
	return []csdlTestCase{
		{
			Name: "Property With Correct Units",
			CSDL: makeSimpleCSDLText(PropertiesTestDefaultFile,
				`<EntityType Name="Test"><Property Name="PropertyVolts" Type="Edm.Double">
				<Annotation Term="OData.Description" String="Voltage property"/>
				<Annotation Term="OData.LongDescription" String="Voltage property long description"/>
				<Annotation Term="Measures.Unit" String="V"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name: "Property With Incorrect Units",
			CSDL: makeSimpleCSDLText(PropertiesTestDefaultFile,
				`<EntityType Name="Test"><Property Name="WrongVoltageProperty" Type="Edm.Double">
				<Annotation Term="OData.Description" String="Wrong voltage property"/>
				<Annotation Term="OData.LongDescription" String="Wrong voltage property long description"/>
				<Annotation Term="Measures.Unit" String="V"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false, // Will fail with unit util (above)
		},
		{
			Name: "Property With Bad Unit Allowed",
			CSDL: makeSimpleCSDLText(PropertiesTestDefaultFile,
				`<EntityType Name="Test"><Property Name="BadUnitProperty" Type="Edm.Double">
				<Annotation Term="OData.Description" String="Bad unit property"/>
				<Annotation Term="OData.LongDescription" String="Bad unit property long description"/>
				<Annotation Term="Measures.Unit" String="V"/></Property></EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name: "Property With Percentage Units",
			CSDL: makeSimpleCSDLText(PropertiesTestDefaultFile, `
			<EntityType Name="Test">
				<Property Name="PercentProperty" Type="Edm.Double">
					<Annotation Term="OData.Description" String="Percent property"/>
					<Annotation Term="OData.LongDescription" String="Percent property long description"/>
					<Annotation Term="Measures.Unit" String="%"/>
				</Property>
			</EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name: "Property With Alternative Unit Name",
			CSDL: makeSimpleCSDLText(PropertiesTestDefaultFile, `
			<EntityType Name="Test">
				<Property Name="PropertyGbps" Type="Edm.Double">
					<Annotation Term="OData.Description" String="Gbps property"/>
					<Annotation Term="OData.LongDescription" String="Gbps property long description"/>
					<Annotation Term="Measures.Unit" String="Gbit/s"/>
				</Property>
			</EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name: "Property With No Units",
			CSDL: makeSimpleCSDLText(PropertiesTestDefaultFile, `
			<EntityType Name="Test">
				<Property Name="NoUnitProperty" Type="Edm.String">
					<Annotation Term="OData.Description" String="No unit property"/>
					<Annotation Term="OData.LongDescription" String="No unit property long description"/>
				</Property>
			</EntityType>`),
			FileName:   PropertiesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
	}
}

func TestPropertyChecksNoUnitUtil(t *testing.T) {
	t.Parallel()
	//nolint:paralleltest // The TestFunc calls Parallel...
	for _, tc := range GetPropertiesTestCasesNoUnits() {
		t.Run(tc.Name, tc.TestFunc("Property checks are valid", csdl.PropertyChecks, nil))
	}
}
