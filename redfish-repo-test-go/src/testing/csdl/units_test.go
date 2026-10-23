/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"bytes"
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
	UnitsTestDefaultFile = "UnitsTest"
)

func GetUnitsTestCases() []csdlTestCase {
	cfg := &config.Config{}

	return []csdlTestCase{
		{
			Name:       "Valid Measurement Annotation",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"><Annotation Term="Measures.Unit" String="m"/></Property></EntityType>`),
			FileName:   UnitsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "No Measurement Annotations",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"/></EntityType>`),
			FileName:   UnitsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Invalid Measurement Annotation",
			CSDL:       makeSimpleCSDLText("Test.v1_0_0", `<EntityType Name="Test"><Property Name="TestProp" Type="Edm.String"><Annotation Term="Measures.Unit" String="invalid"/></Property></EntityType>`),
			FileName:   UnitsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:UnitsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='Test.v1_0_0']/EntityType[@Name='Test']/Property[@Name='TestProp']/Annotation[@Term='Measures.Unit']: Invalid measurement: \"invalid\"",
			},
		},
	}
}

func TestValidateUnits(t *testing.T) {
	t.Parallel()
	unitUtil, err := units.Load()
	require.NoError(t, err)
	for _, tc := range GetUnitsTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			searcher := helperGetSearcherForText(t, tc.FileName, tc.CSDL, "")

			// Create a custom test function that includes the unitUtil
			testFunc := func(t *testsuite.Testing, unitUtil units.Units, cfg *config.Config, searcher *csdl.Searcher) {
				csdlvalidation.ValidateUnits(t, unitUtil, cfg, searcher)
			}

			suiteCase := &testsuite.Case{
				Name:   "Units tests are valid",
				Func:   helperTestWrapper(unitUtil, tc.Config, searcher, testFunc),
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
