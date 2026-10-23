/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"testing"

	csdlpkg "github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/stretchr/testify/assert"
)

const (
	EntityTestDefaultFile = "EntityTest"
)

//nolint:funlen // The table-driven test keeps its related XML cases together.
func GetEntityTestCases() []csdlTestCase {
	cfg := &config.Config{
		AllowLists: config.AllowLists{
			PluralEntityPatterns: []string{"AllowedTests"},
			NoActionsAllowed:     []string{"EntityTest.NoActionsAllowed"},
		},
	}
	return []csdlTestCase{
		{
			Name:       "No Entities",
			CSDL:       EmptyValidCSDL,
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Valid Entity",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="Test"><Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/><Annotation Term="OData.Description" String="This is a test entity."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Entity With No BaseType",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="TestNoBase"><Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/><Annotation Term="OData.Description" String="This is a test entity with no base type."/><Annotation Term="OData.LongDescription" String="This is a longer test description for entity with no base type."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Plural Entity Name",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="Tests"><Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/><Annotation Term="OData.Description" String="This is a test entity."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='Tests']: Entity 'Tests' should not be plural",
			},
		},
		{
			Name:       "Plural Entity Name Allowed Implictly",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="Status"><Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/><Annotation Term="OData.Description" String="This is a test entity."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Plural Entity Name Allowed Explicitly",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="AllowedTests"><Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/><Annotation Term="OData.Description" String="This is a test entity."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Invalid BaseType",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="Test" BaseType="Invalid.Type"><Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/><Annotation Term="OData.Description" String="This is a test entity."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='Test']: Entity Test BaseType of 'Invalid.Type' is not valid",
			},
		},
		{
			Name:       "Missing Actions Property",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="TestNoAction"><Property Name="Id" Type="Edm.String"/><Annotation Term="OData.Description" String="This is a test entity."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestNoAction']: Entity EntityTest.TestNoAction does not contain an Actions property",
			},
		},
		{
			Name:       "No Actions Allowed",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="NoActionsAllowed"><Annotation Term="OData.Description" String="This is a test entity."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/><Property Name="Id" Type="Edm.String"/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Missing Description",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="TestNoDesc"><Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/><Property Name="Id" Type="Edm.String"/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestNoDesc']: Entity EntityTest.TestNoDesc does not contain a Description",
			},
		},
		{
			Name:       "Missing LongDescription",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="TestNoLongDesc"><Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/><Annotation Term="OData.Description" String="This is a test entity."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestNoLongDesc']: Entity EntityTest.TestNoLongDesc does not contain a LongDescription",
			},
		},
		{
			Name:       "Multiple Errors",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="MultipleTests" BaseType="Invalid.Type"><Annotation Term="OData.Description" String="This is a test entity."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='MultipleTests']: Entity 'MultipleTests' should not be plural",
				"Error:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='MultipleTests']: Entity MultipleTests BaseType of 'Invalid.Type' is not valid",
			},
		},
		{
			Name:       "ServiceRoot Excluded",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="ServiceRoot"><Annotation Term="OData.Description" String="This is the service root."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "ActionInfo Excluded",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="TestActionInfo"><Annotation Term="OData.Description" String="This is action info."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "ReferenceableMember Excluded",
			CSDL:       makeSimpleCSDLText(EntityTestDefaultFile, `<EntityType Name="TestMember" BaseType="Resource.ReferenceableMember"><Annotation Term="OData.Description" String="This is a referenceable member."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestMember']: Entity TestMember BaseType of 'Resource.ReferenceableMember' is not valid",
			},
		},
		{
			Name:       "Resource Namespace Excluded",
			CSDL:       makeSimpleCSDLText("Resource", `<EntityType Name="TestResource"><Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/></EntityType>`),
			FileName:   "Resource",
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "MissingRestrictions",
			CSDL:       makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile, `<EntityType Name="TestResource" BaseType="Resource.v1_0_0.Resource"><Annotation Term="OData.Description" String="This is a referenceable member."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestResource']: Entity TestResource does not contain a Capabilities.InsertRestrictions annotation",
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestResource']: Entity TestResource does not contain a Capabilities.UpdateRestrictions annotation",
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestResource']: Entity TestResource does not contain a Capabilities.DeleteRestrictions annotation",
			},
		},
		{
			Name:       "Non-Collection Insertable",
			CSDL:       makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile, `<EntityType Name="TestResource" BaseType="Resource.v1_0_0.Resource"><Annotation Term="OData.Description" String="This is a referenceable member."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/><Annotation Term="Capabilities.InsertRestrictions"><Record><PropertyValue Property="Insertable" Bool="true"/></Record></Annotation><Annotation Term="Capabilities.UpdateRestrictions"><Record><PropertyValue Property="Updatable" Bool="false"/></Record></Annotation><Annotation Term="Capabilities.DeleteRestrictions"><Record><PropertyValue Property="Deletable" Bool="true"/></Record></Annotation></EntityType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestResource']: Entity TestResource has InsertRestrictions set to true but is not a collection",
			},
		},
		{
			Name:       "Non-Updatable with RW prop",
			CSDL:       makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile, `<EntityType Name="TestResourceUpRW" BaseType="Resource.v1_0_0.Resource"><Annotation Term="OData.Description" String="This is a referenceable member."/><Annotation Term="OData.LongDescription" String="This is a longer test description."/><Annotation Term="Capabilities.InsertRestrictions"><Record><PropertyValue Property="Insertable" Bool="false"/></Record></Annotation><Annotation Term="Capabilities.UpdateRestrictions"><Record><PropertyValue Property="Updatable" Bool="false"/></Record></Annotation><Annotation Term="Capabilities.DeleteRestrictions"><Record><PropertyValue Property="Deletable" Bool="true"/></Record></Annotation><Property Name="TestProperty" Type="Edm.String" Nullable="false"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/></Property><Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/></EntityType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestResourceUpRW']/Annotation[@Term='Capabilities.UpdateRestrictions']: Entity TestResourceUpRW has writable properties 'TestProperty' but is not marked as updatable",
			},
		},
		{
			Name: "Updatable without RW prop",
			CSDL: makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile,
				`<EntityType Name="TestResourceNoRW" BaseType="Resource.v1_0_0.Resource">
				<Annotation Term="OData.Description" String="This is a referenceable member."/>
				<Annotation Term="OData.LongDescription" String="This is a longer test description."/>
				<Annotation Term="Capabilities.InsertRestrictions">
					<Record>
						<PropertyValue Property="Insertable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.UpdateRestrictions">
					<Record>
						<PropertyValue Property="Updatable" Bool="true"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.DeleteRestrictions">
					<Record>
						<PropertyValue Property="Deletable" Bool="true"/>
					</Record>
				</Annotation>
				<Property Name="TestProperty" Type="Edm.String" Nullable="false">
					<Annotation Term="OData.Permissions" EnumMember="OData.Permission/Read"/>
				</Property>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestResourceNoRW']: Entity TestResourceNoRW is marked as updatable but has no writable properties",
			},
		},
		{
			Name: "Updateable Entity Property Points to ComplexType with Writable Descendant",
			CSDL: makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile, `
			<EntityType Name="TestBaseWithWritable" BaseType="Resource.v1_0_0.Resource">
				<Annotation Term="OData.Description" String="Base type with writable property."/>
				<Annotation Term="OData.LongDescription" String="Base type with writable property longer description."/>
				<Annotation Term="Capabilities.InsertRestrictions">
					<Record>
						<PropertyValue Property="Insertable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.UpdateRestrictions">
					<Record>
						<PropertyValue Property="Updatable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.DeleteRestrictions">
					<Record>
						<PropertyValue Property="Deletable" Bool="true"/>
					</Record>
				</Annotation>
				<Property Name="WritableProp" Type="EntityTest.TestBaseComplex"/>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>
			<ComplexType Name="TestChildComplex" BaseType="EntityTest.TestBaseComplex">
				<Annotation Term="OData.Description" String="Child complex type."/>
				<Annotation Term="OData.LongDescription" String="Child complex type longer description."/>
				<Property Name="BaseProp" Type="Edm.String">
					<Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/>
				</Property>
			</ComplexType>
			<ComplexType Name="TestBaseComplex">
				<Annotation Term="OData.Description" String="Child complex type."/>
				<Annotation Term="OData.LongDescription" String="Child complex type longer description."/>
			</ComplexType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestBaseWithWritable']/Annotation[@Term='Capabilities.UpdateRestrictions']: Entity TestBaseWithWritable has writable properties 'WritableProp' but is not marked as updatable",
			},
		},
		{
			Name: "Updateable Entity Property Points to ComplexType with Multi-Layer Writable Descendant",
			CSDL: makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile,
				`<EntityType Name="TestMultiLayerWritable" BaseType="Resource.v1_0_0.Resource">
				<Annotation Term="OData.Description" String="Entity with multi-layer writable property."/>
				<Annotation Term="OData.LongDescription" String="Entity with multi-layer writable property longer description."/>
				<Annotation Term="Capabilities.InsertRestrictions">
					<Record>
						<PropertyValue Property="Insertable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.UpdateRestrictions">
					<Record>
						<PropertyValue Property="Updatable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.DeleteRestrictions">
					<Record>
						<PropertyValue Property="Deletable" Bool="true"/>
					</Record>
				</Annotation>
				<Property Name="MultiLayerProp" Type="EntityTest.TestBaseComplex"/>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>
			<ComplexType Name="TestBaseComplex">
				<Annotation Term="OData.Description" String="Base complex type."/>
				<Annotation Term="OData.LongDescription" String="Base complex type longer description."/>
			</ComplexType>
			<ComplexType Name="TestMiddleComplex" BaseType="EntityTest.TestBaseComplex">
				<Annotation Term="OData.Description" String="Middle complex type."/>
				<Annotation Term="OData.LongDescription" String="Middle complex type longer description."/>
			</ComplexType>
			<ComplexType Name="TestLeafComplex" BaseType="EntityTest.TestMiddleComplex">
				<Annotation Term="OData.Description" String="Leaf complex type with writable property."/>
				<Annotation Term="OData.LongDescription" String="Leaf complex type with writable property longer description."/>
				<Property Name="DeepWritableProp" Type="Edm.String">
					<Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/>
				</Property>
			</ComplexType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestMultiLayerWritable']/Annotation[@Term='Capabilities.UpdateRestrictions']: Entity TestMultiLayerWritable has writable properties 'MultiLayerProp' but is not marked as updatable",
			},
		},
		{
			Name: "Updateable Entity Property Points to ComplexType with Multi-Layer Writable NavProperty",
			CSDL: makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile,
				`<EntityType Name="TestMultiLayerWritableNav" BaseType="Resource.v1_0_0.Resource">
				<Annotation Term="OData.Description" String="Entity with multi-layer writable nav property."/>
				<Annotation Term="OData.LongDescription" String="Entity with multi-layer writable nav property longer description."/>
				<Annotation Term="Capabilities.InsertRestrictions">
					<Record>
						<PropertyValue Property="Insertable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.UpdateRestrictions">
					<Record>
						<PropertyValue Property="Updatable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.DeleteRestrictions">
					<Record>
						<PropertyValue Property="Deletable" Bool="true"/>
					</Record>
				</Annotation>
				<Property Name="MultiLayerNavProp" Type="EntityTest.TestBaseComplex"/>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>
			<ComplexType Name="TestBaseComplex">
				<Annotation Term="OData.Description" String="Base complex type."/>
				<Annotation Term="OData.LongDescription" String="Base complex type longer description."/>
			</ComplexType>
			<ComplexType Name="TestMiddleComplex" BaseType="EntityTest.TestBaseComplex">
				<Annotation Term="OData.Description" String="Middle complex type."/>
				<Annotation Term="OData.LongDescription" String="Middle complex type longer description."/>
			</ComplexType>
			<ComplexType Name="TestLeafNavComplex" BaseType="EntityTest.TestMiddleComplex">
				<Annotation Term="OData.Description" String="Leaf complex type with writable nav property."/>
				<Annotation Term="OData.LongDescription" String="Leaf complex type with writable nav property longer description."/>
				<NavigationProperty Name="DeepWritableNavProp" Type="EntityTest.TargetEntityType">
					<Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/>
				</NavigationProperty>
			</ComplexType>
			<EntityType Name="TargetEntityType">
				<Annotation Term="OData.Description" String="Target entity type for navigation."/>
				<Annotation Term="OData.LongDescription" String="Target entity type for navigation longer description."/>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestMultiLayerWritableNav']/Annotation[@Term='Capabilities.UpdateRestrictions']: Entity TestMultiLayerWritableNav has writable properties 'MultiLayerNavProp' but is not marked as updatable",
			},
		},
		{
			Name: "Updateable Entity Property Points to ComplexType with Multi-Layer Writable Control NavProperty",
			CSDL: makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile,
				`<EntityType Name="TestMultiLayerWritableControlNav" BaseType="Resource.v1_0_0.Resource">
				<Annotation Term="OData.Description" String="Entity with multi-layer writable control nav property."/>
				<Annotation Term="OData.LongDescription" String="Entity with multi-layer writable control nav property longer description."/>
				<Annotation Term="Capabilities.InsertRestrictions">
					<Record>
						<PropertyValue Property="Insertable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.UpdateRestrictions">
					<Record>
						<PropertyValue Property="Updatable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.DeleteRestrictions">
					<Record>
						<PropertyValue Property="Deletable" Bool="true"/>
					</Record>
				</Annotation>
				<Property Name="MultiLayerControlNavProp" Type="EntityTest.TestBaseComplex"/>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>
			<ComplexType Name="TestBaseComplex">
				<Annotation Term="OData.Description" String="Base complex type."/>
				<Annotation Term="OData.LongDescription" String="Base complex type longer description."/>
			</ComplexType>
			<ComplexType Name="TestMiddleComplex" BaseType="EntityTest.TestBaseComplex">
				<Annotation Term="OData.Description" String="Middle complex type."/>
				<Annotation Term="OData.LongDescription" String="Middle complex type longer description."/>
			</ComplexType>
			<ComplexType Name="TestLeafControlNavComplex" BaseType="EntityTest.TestMiddleComplex">
				<Annotation Term="OData.Description" String="Leaf complex type with writable control nav property."/>
				<Annotation Term="OData.LongDescription" String="Leaf complex type with writable control nav property longer description."/>
				<NavigationProperty Name="DeepWritableControlNavProp" Type="Control.Control">
					<Annotation Term="Redfish.ExcerptCopy"/>
				</NavigationProperty>
			</ComplexType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestMultiLayerWritableControlNav']/Annotation[@Term='Capabilities.UpdateRestrictions']: Entity TestMultiLayerWritableControlNav has writable properties 'MultiLayerControlNavProp' but is not marked as updatable",
			},
		},
		{
			Name: "Updateable Entity NavProperty Points to ComplexType with writable",
			CSDL: makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile,
				`<EntityType Name="TestNavWritable" BaseType="Resource.v1_0_0.Resource">
				<Annotation Term="OData.Description" String="Entity with multi-layer writable property."/>
				<Annotation Term="OData.LongDescription" String="Entity with multi-layer writable property longer description."/>
				<Annotation Term="Capabilities.InsertRestrictions">
					<Record>
						<PropertyValue Property="Insertable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.UpdateRestrictions">
					<Record>
						<PropertyValue Property="Updatable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.DeleteRestrictions">
					<Record>
						<PropertyValue Property="Deletable" Bool="true"/>
					</Record>
				</Annotation>
				<NavigationProperty Name="MultiLayerProp" Type="EntityTest.TestBaseComplex"/>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>
			<ComplexType Name="TestBaseComplex">
				<Annotation Term="OData.Description" String="Base complex type."/>
				<Annotation Term="OData.LongDescription" String="Base complex type longer description."/>
				<Property Name="DeepWritableProp" Type="Edm.String">
					<Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/>
				</Property>
			</ComplexType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestNavWritable']/Annotation[@Term='Capabilities.UpdateRestrictions']: Entity TestNavWritable has writable properties 'MultiLayerProp' but is not marked as updatable",
			},
		},
		{
			Name: "Updateable Entity NavProperty Points to ComplexType MultiLayer",
			CSDL: makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile,
				`<EntityType Name="TestNavToNavWritable" BaseType="Resource.v1_0_0.Resource">
				<Annotation Term="OData.Description" String="Entity with multi-layer writable property."/>
				<Annotation Term="OData.LongDescription" String="Entity with multi-layer writable property longer description."/>
				<Annotation Term="Capabilities.InsertRestrictions">
					<Record>
						<PropertyValue Property="Insertable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.UpdateRestrictions">
					<Record>
						<PropertyValue Property="Updatable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.DeleteRestrictions">
					<Record>
						<PropertyValue Property="Deletable" Bool="true"/>
					</Record>
				</Annotation>
				<NavigationProperty Name="MultiLayerProp" Type="EntityTest.TestBaseComplex"/>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>
			<ComplexType Name="TestBaseComplex">
				<Annotation Term="OData.Description" String="Base complex type."/>
				<Annotation Term="OData.LongDescription" String="Base complex type longer description."/>
				<NavigationProperty Name="DeepWritableProp" Type="EntityTest.TestNextComplex"/>
			</ComplexType>
			<ComplexType Name="TestNextComplex">
				<Annotation Term="OData.Description" String="Next complex type."/>
				<Annotation Term="OData.LongDescription" String="Next complex type longer description."/>
				<Property Name="DeepWritableProp" Type="Edm.String">
					<Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/>
				</Property>
			</ComplexType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestNavToNavWritable']/Annotation[@Term='Capabilities.UpdateRestrictions']: Entity TestNavToNavWritable has writable properties 'MultiLayerProp' but is not marked as updatable",
			},
		},
		{
			Name: "Updateable Entity NavProperty Points to EntityType MultiLayer",
			CSDL: makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile,
				`<EntityType Name="TestNavToNavEntityWritable" BaseType="Resource.v1_0_0.Resource">
				<Annotation Term="OData.Description" String="Entity with multi-layer writable property."/>
				<Annotation Term="OData.LongDescription" String="Entity with multi-layer writable property longer description."/>
				<Annotation Term="Capabilities.InsertRestrictions">
					<Record>
						<PropertyValue Property="Insertable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.UpdateRestrictions">
					<Record>
						<PropertyValue Property="Updatable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.DeleteRestrictions">
					<Record>
						<PropertyValue Property="Deletable" Bool="true"/>
					</Record>
				</Annotation>
				<NavigationProperty Name="MultiLayerProp" Type="EntityTest.TestBaseComplex"/>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>
			<ComplexType Name="TestBaseComplex">
				<Annotation Term="OData.Description" String="Base complex type."/>
				<Annotation Term="OData.LongDescription" String="Base complex type longer description."/>
				<NavigationProperty Name="DeepWritableProp" Type="EntityTest.TestNextEntity"/>
			</ComplexType>
			<EntityType Name="TestNextEntity">
				<Annotation Term="OData.Description" String="Next entity type."/>
				<Annotation Term="OData.LongDescription" String="Next entity type longer description."/>
				<Property Name="DeepWritableProp" Type="Edm.String">
					<Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/>
				</Property>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestNavToNavEntityWritable']/Annotation[@Term='Capabilities.UpdateRestrictions']: Entity TestNavToNavEntityWritable has writable properties 'MultiLayerProp' but is not marked as updatable",
			},
		},
		{
			Name: "Updateable Entity NavProperty Points to EntityType NacProp MultiLayer",
			CSDL: makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile,
				`<EntityType Name="TestNavToNavEntityNavWritable" BaseType="Resource.v1_0_0.Resource">
				<Annotation Term="OData.Description" String="Entity with multi-layer writable property."/>
				<Annotation Term="OData.LongDescription" String="Entity with multi-layer writable property longer description."/>
				<Annotation Term="Capabilities.InsertRestrictions">
					<Record>
						<PropertyValue Property="Insertable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.UpdateRestrictions">
					<Record>
						<PropertyValue Property="Updatable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.DeleteRestrictions">
					<Record>
						<PropertyValue Property="Deletable" Bool="true"/>
					</Record>
				</Annotation>
				<NavigationProperty Name="MultiLayerProp" Type="EntityTest.TestBaseComplex"/>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>
			<ComplexType Name="TestBaseComplex">
				<Annotation Term="OData.Description" String="Base complex type."/>
				<Annotation Term="OData.LongDescription" String="Base complex type longer description."/>
				<NavigationProperty Name="DeepWritableProp" Type="EntityTest.TestNextEntity"/>
			</ComplexType>
			<EntityType Name="TestNextEntity">
				<Annotation Term="OData.Description" String="Next entity type."/>
				<Annotation Term="OData.LongDescription" String="Next entity type longer description."/>
				<NavigationProperty Name="DeepWritableProp" Type="Edm.String">
					<Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/>
				</NavigationProperty>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestNavToNavEntityNavWritable']/Annotation[@Term='Capabilities.UpdateRestrictions']: Entity TestNavToNavEntityNavWritable has writable properties 'MultiLayerProp' but is not marked as updatable",
			},
		},
		{
			Name: "Non-Updatable with many writable properties",
			CSDL: makeSimpleCSDLTextWithReference("Resource", []string{"Resource.v1_0_0"}, EntityTestDefaultFile,
				`<EntityType Name="TestManyWritable" BaseType="Resource.v1_0_0.Resource">
				<Annotation Term="OData.Description" String="This is a referenceable member."/>
				<Annotation Term="OData.LongDescription" String="This is a longer test description."/>
				<Annotation Term="Capabilities.InsertRestrictions">
					<Record>
						<PropertyValue Property="Insertable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.UpdateRestrictions">
					<Record>
						<PropertyValue Property="Updatable" Bool="false"/>
					</Record>
				</Annotation>
				<Annotation Term="Capabilities.DeleteRestrictions">
					<Record>
						<PropertyValue Property="Deletable" Bool="true"/>
					</Record>
				</Annotation>
				<Property Name="Prop1" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/></Property>
				<Property Name="Prop2" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/></Property>
				<Property Name="Prop3" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/></Property>
				<Property Name="Prop4" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/></Property>
				<Property Name="Prop5" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/></Property>
				<Property Name="Prop6" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/></Property>
				<Property Name="Prop7" Type="Edm.String"><Annotation Term="OData.Permissions" EnumMember="OData.Permission/ReadWrite"/></Property>
				<Property Name="Actions" Type="Resource.v1_0_0.ActionCollection"/>
			</EntityType>`),
			FileName:   EntityTestDefaultFile,
			ExtraFiles: map[string]string{"Resource.xml": SimpleResourceExample},
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EntityTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EntityTest']/EntityType[@Name='TestManyWritable']/Annotation[@Term='Capabilities.UpdateRestrictions']: Entity TestManyWritable has writable properties 'Prop1, Prop2, Prop3, Prop4, Prop5, and 2 more' but is not marked as updatable",
			},
		},
	}
}

func TestEntityChecks(t *testing.T) {
	t.Parallel()
	//nolint:paralleltest // The TestFunc calls Parallel...
	for _, tc := range GetEntityTestCases() {
		t.Run(tc.Name, tc.TestFunc("Entity checks are valid", csdl.EntityChecks, nil))
	}
}

// Create a mock type that implements csdl.Searchable but is not handled.
type UnknownSearchable struct {
	// Minimal implementation to satisfy the interface
}

// Implement the required methods for csdl.Searchable interface.
func (u *UnknownSearchable) GetChildren() []csdlpkg.Searchable { return nil }
func (u *UnknownSearchable) GetName() string                   { return "Unknown" }
func (u *UnknownSearchable) GetSchema() *csdlpkg.Schema        { return nil }
func (u *UnknownSearchable) GetXPath() string                  { return "" }

func TestGetEntityTypeName_PanicOnUnknownType(t *testing.T) {
	t.Parallel()

	// Create an instance of the unknown type
	unknown := &UnknownSearchable{}

	// Verify that GetEntityTypeName panics on unknown type
	assert.Panics(t, func() {
		csdl.GetEntityTypeName(unknown)
	}, "GetEntityTypeName should panic on unknown type")

	// Verify the panic message contains expected content
	panicMessage := recover()
	if panicMessage != nil {
		//nolint:forcetypeassert
		assert.Contains(t, panicMessage.(string), "unknown type:")
	}
}
