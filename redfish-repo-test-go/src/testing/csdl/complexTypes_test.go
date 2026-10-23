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
	"github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

const (
	ComplexTypesTestDefaultFile = "AnnotationsTest"
)

//nolint:funlen // The table-driven test keeps its related XML cases together.
func GetComplexTypeTestCases() []csdlTestCase {
	cfg := &config.Config{
		AllowLists: config.AllowLists{
			PluralEntityPatterns: []string{"AllowedTests"},
		},
	}
	return []csdlTestCase{
		{
			Name:       "No ComplexType",
			CSDL:       EmptyValidCSDL,
			FileName:   ComplexTypesTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Valid",
			CSDL:       makeSimpleCSDLText(AnnotationsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.Description" String="This action shall be used to test."/><Annotation Term="OData.LongDescription" String="This action shall be used to test."/></ComplexType>`),
			FileName:   AnnotationsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Plural Name",
			CSDL:       makeSimpleCSDLText(AnnotationsTestDefaultFile, `<ComplexType Name="Tests"><Annotation Term="OData.Description" String="This action shall be used to test."/><Annotation Term="OData.LongDescription" String="This action shall be used to test."/></ComplexType>`),
			FileName:   AnnotationsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:AnnotationsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='AnnotationsTest']/ComplexType[@Name='Tests']: ComplexType 'Tests' should not be plural",
			},
		},
		{
			Name:       "Plural Name - Allowed",
			CSDL:       makeSimpleCSDLText(AnnotationsTestDefaultFile, `<ComplexType Name="AllowedTests"><Annotation Term="OData.Description" String="This action shall be used to test."/><Annotation Term="OData.LongDescription" String="This action shall be used to test."/></ComplexType>`),
			FileName:   AnnotationsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Invalid",
			CSDL:       makeSimpleCSDLText(AnnotationsTestDefaultFile, `<ComplexType Name="Test" BaseType="Bad.Type"><Annotation Term="OData.Description" String="This action shall be used to test."/><Annotation Term="OData.LongDescription" String="This action shall be used to test."/></ComplexType>`),
			FileName:   AnnotationsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:AnnotationsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='AnnotationsTest']/ComplexType[@Name='Test']: ComplexType Test BaseType of 'Bad.Type' is not valid",
			},
		},
		{
			Name:       "Abstract allows no descriptions",
			CSDL:       makeSimpleCSDLText(AnnotationsTestDefaultFile, `<ComplexType Name="Test" Abstract="true"></ComplexType>`),
			FileName:   AnnotationsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "No descriptions",
			CSDL:       makeSimpleCSDLText(AnnotationsTestDefaultFile, `<ComplexType Name="TestNoDesc"></ComplexType>`),
			FileName:   AnnotationsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:AnnotationsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='AnnotationsTest']/ComplexType[@Name='TestNoDesc']: ComplexType AnnotationsTest.TestNoDesc does not contain a Description",
				"Error:AnnotationsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='AnnotationsTest']/ComplexType[@Name='TestNoDesc']: ComplexType AnnotationsTest.TestNoDesc does not contain a LongDescription",
			},
		},
		{
			Name:       "BaseType descriptions",
			CSDL:       makeSimpleCSDLText(AnnotationsTestDefaultFile, `<ComplexType Name="TestBaseType"><Annotation Term="OData.Description" String="This action shall be used to test."/><Annotation Term="OData.LongDescription" String="This action shall be used to test."/></ComplexType><ComplexType Name="TestBaseTypeChild" BaseType="AnnotationsTest.TestBaseType"></ComplexType>`),
			FileName:   AnnotationsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "BaseType not ComplexType",
			CSDL:       makeSimpleCSDLText(AnnotationsTestDefaultFile, `<EntityType Name="TestBadBaseType"><Annotation Term="OData.Description" String="This action shall be used to test."/><Annotation Term="OData.LongDescription" String="This action shall be used to test."/></EntityType><ComplexType Name="TestBadBaseTypeChild" BaseType="AnnotationsTest.TestBadBaseType"></ComplexType>`),
			FileName:   AnnotationsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:AnnotationsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='AnnotationsTest']/ComplexType[@Name='TestBadBaseTypeChild']: ComplexType TestBadBaseTypeChild has an invalid base type AnnotationsTest.TestBadBaseType",
				"Error:AnnotationsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='AnnotationsTest']/ComplexType[@Name='TestBadBaseTypeChild']: ComplexType AnnotationsTest.TestBadBaseTypeChild does not contain a Description",
				"Error:AnnotationsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='AnnotationsTest']/ComplexType[@Name='TestBadBaseTypeChild']: ComplexType AnnotationsTest.TestBadBaseTypeChild does not contain a LongDescription",
			},
		},
	}
}

func TestComplexTypeChecks(t *testing.T) {
	t.Parallel()
	//nolint:paralleltest // The TestFunc calls Parallel...
	for _, tc := range GetComplexTypeTestCases() {
		t.Run(tc.Name, tc.TestFunc("Complex types are valid", csdl.ComplexTypeChecks, nil))
	}
}

func BenchmarkComplexTypeChecks(b *testing.B) {
	for _, tc := range GetComplexTypeTestCases() {
		searcher := helperGetSearcherForText(b, tc.FileName, tc.CSDL, "")
		suiteCase := &testsuite.Case{
			Name:   "Complex types are valid",
			Func:   helperTestWrapper(nil, tc.Config, searcher, csdl.ComplexTypeChecks),
			Buffer: &bytes.Buffer{},
		}
		b.Run(tc.Name, func(b *testing.B) {
			b.ReportAllocs()
			_ = suiteCase.Run()
		})
	}
}
