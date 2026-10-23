/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/csdl"
)

const (
	PermissionsTestDefaultFile = "PermissionsTest"
)

//nolint:funlen // The table-driven test keeps its related XML cases together.
func GetPermissionsTestCases() []csdlTestCase {
	cfg := &config.Config{
		AllowLists: config.AllowLists{},
	}
	return []csdlTestCase{
		{
			Name:       "No Schemas",
			CSDL:       EmptyValidCSDL,
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "RedfishExtensions Skipped",
			CSDL:       makeSimpleCSDLText("RedfishExtensions", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   "RedfishExtensions",
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Valid Property with Permissions",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/Read"/></Property></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Property Missing Permissions",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Test']/Property[@Name='TestProp']: No permissions annotations",
			},
		},
		{
			Name:       "ComplexType Property Should Not Have Permissions",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<ComplexType Name="TestComplex"><Property Name="InnerProp" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/Read"/></Property></ComplexType><EntityType Name="Test"><Property Name="ComplexProp" Type="PermissionsTest.TestComplex"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/Read"/></Property></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Test']/Property[@Name='ComplexProp']: Properties that reference ComplexTypes should not have permissions annotations",
			},
		},
		{
			Name:       "ComplexType Property Without Permissions",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<ComplexType Name="TestComplex"><Property Name="InnerProp" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/Read"/></Property></ComplexType><EntityType Name="Test"><Property Name="ComplexProp" Type="PermissionsTest.TestComplex"/></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "EntityType Property Inherits Permissions",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="BaseType"><Property Name="BaseProp" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/Read"/></Property></EntityType><EntityType Name="Test" BaseType="PermissionsTest.BaseType"></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "EntityType Property Missing Base Permissions",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="BaseType"><Property Name="BaseProp" Type="Edm.String"/></EntityType><EntityType Name="Test" BaseType="PermissionsTest.BaseType"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='BaseType']/Property[@Name='BaseProp']: No permissions annotations",
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Test']/Property[@Name='TestProp']: No permissions annotations",
			},
		},
		{
			Name:       "Multiple Properties Mixed",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="Test"><Property Name="ValidProp" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/Read"/></Property><Property Name="InvalidProp" Type="Edm.String"/></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Test']/Property[@Name='InvalidProp']: No permissions annotations",
			},
		},
		{
			Name:       "Standard Edm Types",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="Test"><Property Name="StringProp" Type="Edm.String"/><Property Name="IntProp" Type="Edm.Int32"/><Property Name="BoolProp" Type="Edm.Boolean"/></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Test']/Property[@Name='StringProp']: No permissions annotations",
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Test']/Property[@Name='IntProp']: No permissions annotations",
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Test']/Property[@Name='BoolProp']: No permissions annotations",
			},
		},
		{
			Name:       "Collection Types",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="Test"><Property Name="CollectionProp" Type="Collection(Edm.String)"/></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Test']/Property[@Name='CollectionProp']: No permissions annotations",
			},
		},
		{
			Name:       "Cross Namespace Type",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="Test"><Property Name="CrossProp" Type="OtherNamespace.Type"/></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false, // Should be skipped since it's cross-namespace
		},
		{
			Name:       "Complex Inheritance Chain",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="Base"><Property Name="BaseProp" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/Read"/></Property></EntityType><EntityType Name="Middle" BaseType="PermissionsTest.Base"><Property Name="MiddleProp" Type="Edm.String"/></EntityType><EntityType Name="Test" BaseType="PermissionsTest.Middle"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Middle']/Property[@Name='MiddleProp']: No permissions annotations",
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Test']/Property[@Name='TestProp']: No permissions annotations",
			},
		},
		{
			Name:       "No Properties",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="Empty"/>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Invalid Type",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="Test"><Property Name="CollectionProp" Type="Collection(PermissionsTest.String)"/></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Test']/Property[@Name='CollectionProp']: Type not found: Collection(PermissionsTest.String)",
			},
		},
		{
			Name:       "Type Has Permissions",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="Test"><Property Name="TestChild" Type="PermissionsTest.Child"/></EntityType><EntityType Name="Child"><Property Name="ChildProp" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/Read"/></Property></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Type Does Not Have Permissions",
			CSDL:       makeSimpleCSDLText(PermissionsTestDefaultFile, `<EntityType Name="Test"><Property Name="TestChild" Type="PermissionsTest.Child"/></EntityType><EntityType Name="Child"><Property Name="ChildProp" Type="Edm.String"/></EntityType>`),
			FileName:   PermissionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Test']/Property[@Name='TestChild']: No permissions annotations",
				"Warning:PermissionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='PermissionsTest']/EntityType[@Name='Child']/Property[@Name='ChildProp']: No permissions annotations",
			},
		},
	}
}

func TestSchemasHavePermissions(t *testing.T) {
	t.Parallel()
	//nolint:paralleltest // The TestFunc calls Parallel...
	for _, tc := range GetPermissionsTestCases() {
		t.Run(tc.Name, tc.TestFunc("Permission checks are valid", csdl.SchemasHavePermissions, nil))
	}
}
