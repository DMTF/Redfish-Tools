/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"bytes"
	"testing"

	csdl "github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	csdltest "github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

const (
	ReferencesTestDefaultFile = "ReferencesTest"
)

//nolint:funlen // The table-driven test keeps its related XML cases together.
func GetReferencesTestCases() []csdlTestCase {
	cfg := &config.Config{}
	return []csdlTestCase{
		{
			Name:       "No References",
			CSDL:       EmptyValidCSDL,
			FileName:   ReferencesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "No URI",
			CSDL:       CSDLStart + `<edmx:Reference Uri=""></edmx:Reference><edmx:DataServices><Schema Namespace="ReferencesTest"></Schema>` + CSDLEnd,
			FileName:   ReferencesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:ReferencesTest.xml:/edmx:Edmx/edmx:Reference[@Uri='']: Reference URI is empty",
			},
		},
		{
			Name:       "Bad Reference",
			CSDL:       CSDLStart + `<edmx:Reference Uri="http://example.com/badRef"></edmx:Reference><edmx:DataServices><Schema Namespace="ReferencesTest"></Schema>` + CSDLEnd,
			FileName:   ReferencesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:ReferencesTest.xml:/edmx:Edmx/edmx:Reference[@Uri='http://example.com/badRef']: Reference URI http://example.com/badRef is not valid",
			},
		},
		{
			Name:       "Valid OASIS Reference",
			CSDL:       makeSimpleCSDLTextWithReference("OData", []string{"Org.OData.Core.V1"}, ReferencesTestDefaultFile, `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   ReferencesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Reference Used In Annotation Term",
			CSDL:       makeSimpleCSDLTextWithReference("OData", []string{"Org.OData.Core.V1"}, ReferencesTestDefaultFile, `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"><Annotation Term="Org.OData.Core.V1.Description" String="Test"/></Property></EntityType>`),
			FileName:   ReferencesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Reference Not Used",
			CSDL:       makeSimpleCSDLTextWithReference("OData", []string{"Org.OData.Validation.V1"}, ReferencesTestDefaultFile, `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   ReferencesTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:ReferencesTest.xml:/edmx:Edmx/edmx:Reference[@Uri='http://redfish.dmtf.org/schemas/v1/OData.xml']: Reference Namespace \"Org.OData.Validation.V1\" of http://redfish.dmtf.org/schemas/v1/OData.xml is not used",
			},
		},
		{
			Name:       "Allowed Unused Reference",
			CSDL:       makeSimpleCSDLTextWithReference("OData", []string{"Org.OData.Core.V1"}, ReferencesTestDefaultFile, `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   ReferencesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Multiple References Mixed",
			CSDL:       makeSimpleCSDLTextWithReference("OData", []string{"Org.OData.Core.V1"}, ReferencesTestDefaultFile, `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"><Annotation Term="Org.OData.Core.V1.Description" String="Test"/></Property></EntityType>`) + makeSimpleCSDLTextWithReference("OData", []string{"Org.OData.Validation.V1"}, ReferencesTestDefaultFile, `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   ReferencesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
	}
}

func TestReferenceCheck(t *testing.T) {
	t.Parallel()
	for _, tc := range GetReferencesTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			searcher := helperGetSearcherForText(t, tc.FileName, tc.CSDL, "")
			suiteCase := &testsuite.Case{
				Name:   "Reference checks are valid",
				Func:   helperTestWrapper(nil, tc.Config, searcher, csdltest.ReferenceCheck),
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

func TestReferenceCheckPedantic(t *testing.T) {
	t.Parallel()

	// Create pedantic test cases (same as regular but with stricter unused reference checking)
	pedanticTestCases := []csdlTestCase{
		{
			Name:       "No References",
			CSDL:       EmptyValidCSDL,
			FileName:   ReferencesTestDefaultFile,
			Config:     &config.Config{},
			ExpectFail: false,
		},
		{
			Name: "Valid OASIS Reference Used",
			CSDL: makeSimpleCSDLTextWithReference("OData",
				[]string{"Org.OData.Core.V1"}, ReferencesTestDefaultFile, `
			<EntityType Name="Test">
				<Property Name="TestProp" Type="Edm.String">
					<Annotation Term="Org.OData.Core.V1.Description" String="Test"/>
				</Property>
			</EntityType>`),
			FileName:   ReferencesTestDefaultFile,
			Config:     &config.Config{},
			ExpectFail: false,
		},
		{
			Name: "Allowed Unused Reference Fails in Pedantic Mode",
			CSDL: makeSimpleCSDLTextWithReference("OData",
				[]string{"Org.OData.Core.V1"}, ReferencesTestDefaultFile, `
			<EntityType Name="Test">
				<Property Name="TestProp" Type="Edm.String"/>
			</EntityType>`),
			FileName:   ReferencesTestDefaultFile,
			Config:     &config.Config{},
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:ReferencesTest.xml:/edmx:Edmx/edmx:Reference[@Uri='http://redfish.dmtf.org/schemas/v1/OData.xml']: Reference Namespace \"Org.OData.Core.V1\" of http://redfish.dmtf.org/schemas/v1/OData.xml is not used",
			},
		},
	}

	for _, tc := range pedanticTestCases {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			searcher := helperGetSearcherForText(t, tc.FileName, tc.CSDL, "")
			suiteCase := &testsuite.Case{
				Name:   "Reference pedantic checks are valid",
				Func:   helperTestWrapper(nil, tc.Config, searcher, csdltest.ReferenceCheckPedantic),
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

//nolint:funlen // Long test function.
func TestGetNamespaceOfChild(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name     string
		child    csdl.Searchable
		expected string
	}{
		{
			name:     "Action returns empty",
			child:    &csdl.Action{Name: "TestAction"},
			expected: "",
		},
		{
			name:     "Member returns empty",
			child:    &csdl.Member{Name: "TestMember"},
			expected: "",
		},
		{
			name:     "Property with simple type",
			child:    &csdl.Property{Name: "TestProp", Type: "Edm.String"},
			expected: "Edm",
		},
		{
			name:     "Property with namespaced type",
			child:    &csdl.Property{Name: "TestProp", Type: "Redfish.v1_0_0.TestType"},
			expected: "Redfish.v1_0_0",
		},
		{
			name:     "Property with collection type",
			child:    &csdl.Property{Name: "TestProp", Type: "Collection(Redfish.v1_0_0.TestType)"},
			expected: "Redfish.v1_0_0",
		},
		{
			name:     "NavigationProperty with namespaced type",
			child:    &csdl.NavigationProperty{Name: "TestNav", Type: "Redfish.v1_0_0.TestType"},
			expected: "Redfish.v1_0_0",
		},
		{
			name:     "EntityType with base type",
			child:    &csdl.EntityType{Name: "TestEntity", BaseType: "Redfish.v1_0_0.BaseType"},
			expected: "Redfish.v1_0_0",
		},
		{
			name:     "ComplexType with base type",
			child:    &csdl.ComplexType{Name: "TestComplex", BaseType: "Redfish.v1_0_0.BaseType"},
			expected: "Redfish.v1_0_0",
		},
		{
			name:     "EnumType with underlying type",
			child:    &csdl.EnumType{Name: "TestEnum", UnderlyingType: "Edm.Int64"},
			expected: "Edm",
		},
		{
			name:     "TypeDefinition with underlying type",
			child:    &csdl.TypeDefinition{Name: "TestTypeDef", UnderlyingType: "Edm.String"},
			expected: "Edm",
		},
		{
			name:     "Annotation with term",
			child:    &csdl.Annotation{Term: "Redfish.v1_0_0.TestTerm"},
			expected: "Redfish.v1_0_0",
		},
		{
			name:     "Parameter with type",
			child:    &csdl.Parameter{Name: "TestParam", Type: "Redfish.v1_0_0.TestType"},
			expected: "Redfish.v1_0_0",
		},
		{
			name:     "Term with type",
			child:    &csdl.Term{Name: "TestTerm", Type: "Redfish.v1_0_0.TestType"},
			expected: "Redfish.v1_0_0",
		},
		{
			name:     "Type without namespace",
			child:    &csdl.Property{Name: "TestProp", Type: "StringType"},
			expected: "StringType",
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			result := csdltest.GetNamespaceOfChild(tc.child)
			assert.Equal(t, tc.expected, result)
		})
	}
}

func TestGetNamespaceOfChildPanic(t *testing.T) {
	t.Parallel()
	t.Run("panic", func(t *testing.T) {
		t.Parallel()
		assert.Panics(t, func() {
			csdltest.GetNamespaceOfChild(csdl.Searchable(nil))
		})
	})
}
