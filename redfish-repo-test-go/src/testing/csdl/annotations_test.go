/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"testing"

	"github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	gocsdl "github.com/pboyd04/gocsdl/pkg/csdl"
)

const (
	AnnotationsTestDefaultFile = "AnnotationsTest"
)

func GetAnnotationsTestCases() []csdlTestCase {
	return []csdlTestCase{
		{
			Name:       "No Annotations",
			CSDL:       EmptyValidCSDL,
			FileName:   AnnotationsTestDefaultFile,
			ExpectFail: false,
		},
		{
			Name:       "Valid",
			CSDL:       makeSimpleCSDLText(AnnotationsTestDefaultFile, `<Annotation Term="OData.LongDescription" String="This action shall be used to test."/>`),
			FileName:   AnnotationsTestDefaultFile,
			ExpectFail: false,
		},
		{
			Name:       "Invalid",
			CSDL:       makeSimpleCSDLText(AnnotationsTestDefaultFile, `<Annotation Term="OData.BadTerm" String="This action shall be used to test."/>`),
			FileName:   AnnotationsTestDefaultFile,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:AnnotationsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='AnnotationsTest']/Annotation[@Term='OData.BadTerm']: Unknown annotation term: \"OData.BadTerm\"",
			},
		},
		{
			Name:       "Add new Valid",
			CSDL:       makeSimpleCSDLText(AnnotationsTestDefaultFile, `<Term Name="NewTerm"/><Annotation Term="AnnotationsTest.NewTerm" String="This action shall be used to test."/>`),
			FileName:   AnnotationsTestDefaultFile,
			ExpectFail: false,
		},
	}
}

func TestAnnotationChecks(t *testing.T) {
	t.Parallel()
	//nolint:paralleltest // The TestFunc calls Parallel...
	for _, tc := range GetAnnotationsTestCases() {
		t.Run(tc.Name, tc.TestFunc("Annotations are valid", csdl.AnnotationChecks, nil))
	}
}

type annotationListTestCase struct {
	Name            string
	ListIn          []*gocsdl.Annotation
	Term            string
	ExpectedTermOut string
}

func GetAnnotationListTestCases() []annotationListTestCase {
	return []annotationListTestCase{
		{
			Name: "Present in list",
			ListIn: []*gocsdl.Annotation{
				{
					Term: "OData.LongDescription",
				},
			},
			Term:            "OData.LongDescription",
			ExpectedTermOut: "OData.LongDescription",
		},
		{
			Name: "Not present in list",
			ListIn: []*gocsdl.Annotation{
				{
					Term: "OData.LongDescription",
				},
			},
			Term:            "OData.ShortDescription",
			ExpectedTermOut: "",
		},
	}
}

func TestAnnotationListHas(t *testing.T) {
	t.Parallel()
	for _, tc := range GetAnnotationListTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			result := csdl.AnnotationListHas(tc.ListIn, tc.Term)
			assert.Equal(t, tc.ExpectedTermOut != "", result)
		})
	}
}

func TestGetAnnotationFromList(t *testing.T) {
	t.Parallel()
	for _, tc := range GetAnnotationListTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			result := csdl.GetAnnotationFromList(tc.ListIn, tc.Term)
			if tc.ExpectedTermOut == "" {
				assert.Nil(t, result)
			} else {
				require.NotNil(t, result)
				assert.Equal(t, tc.ExpectedTermOut, result.Term)
			}
		})
	}
}
