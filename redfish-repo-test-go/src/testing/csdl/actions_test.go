/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"bytes"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

const (
	ActionTestDefaultFile = "ActionsTest"
)

//nolint:funlen // The table-driven test keeps its related XML cases together.
func GetActionTestCases() []csdlTestCase {
	return []csdlTestCase{
		{
			Name:       "No Actions",
			CSDL:       EmptyValidCSDL,
			FileName:   ActionTestDefaultFile,
			ExpectFail: false,
		},
		{
			Name:       "Actions No Short Description",
			CSDL:       makeSimpleCSDLText(ActionTestDefaultFile, `<Action Name="TestAction" IsBound="true"><Annotation Term="OData.LongDescription" String="This action shall be used to test."/><Parameter Name="Test" Type="Test.Actions"/></Action>`),
			FileName:   ActionTestDefaultFile,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:ActionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='ActionsTest']/Action[@Name='TestAction']: Action TestAction does not contain a Description",
			},
		},
		{
			Name:       "Actions No Long Description",
			CSDL:       makeSimpleCSDLText(ActionTestDefaultFile, `<Action Name="TestAction" IsBound="true"><Annotation Term="OData.Description" String="This action shall be used to test."/><Parameter Name="Test" Type="Test.Actions"/></Action>`),
			FileName:   ActionTestDefaultFile,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:ActionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='ActionsTest']/Action[@Name='TestAction']: Action TestAction does not contain a LongDescription",
			},
		},
		{
			Name:       "Simple Valid Action",
			CSDL:       makeSimpleCSDLText(ActionTestDefaultFile, `<Action Name="TestAction" IsBound="true"><Annotation Term="OData.Description" String="This action shall be used to test."/><Annotation Term="OData.LongDescription" String="This action shall be used to test."/><Parameter Name="Test" Type="Test.Actions"/></Action>`),
			FileName:   ActionTestDefaultFile,
			ExpectFail: false,
		},
		{
			Name:       "No IsBound",
			CSDL:       makeSimpleCSDLText(ActionTestDefaultFile, `<Action Name="TestAction"><Annotation Term="OData.Description" String="This action shall be used to test."/><Annotation Term="OData.LongDescription" String="This action shall be used to test."/><Parameter Name="Test" Type="Test.Actions"/></Action>`),
			FileName:   ActionTestDefaultFile,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:ActionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='ActionsTest']/Action[@Name='TestAction']: Action TestAction is not bound (IsBound should be true)",
			},
		},
		{
			Name:       "IsBound False",
			CSDL:       makeSimpleCSDLText(ActionTestDefaultFile, `<Action Name="TestAction" IsBound="false"><Annotation Term="OData.Description" String="This action shall be used to test."/><Annotation Term="OData.LongDescription" String="This action shall be used to test."/><Parameter Name="Test" Type="Test.Actions"/></Action>`),
			FileName:   ActionTestDefaultFile,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:ActionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='ActionsTest']/Action[@Name='TestAction']: Action TestAction is not bound (IsBound should be true)",
			},
		},
		{
			Name:       "No Target",
			CSDL:       makeSimpleCSDLText(ActionTestDefaultFile, `<Action Name="TestAction" IsBound="true"><Annotation Term="OData.Description" String="This action shall be used to test."/><Annotation Term="OData.LongDescription" String="This action shall be used to test."/></Action>`),
			FileName:   ActionTestDefaultFile,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:ActionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='ActionsTest']/Action[@Name='TestAction']: Action TestAction does not have a target parameter (should have a parameter with Type ending in .Actions or .OemActions)",
			},
		},
		{
			Name:       "Action Param No Descriptions",
			CSDL:       makeSimpleCSDLText(ActionTestDefaultFile, `<Action Name="TestAction" IsBound="true"><Annotation Term="OData.Description" String="This action shall be used to test."/><Annotation Term="OData.LongDescription" String="This action shall be used to test."/><Parameter Name="Test" Type="Test.Actions"/><Parameter Name="TestParam" Type="Test.Test" Nullable="false"/></Action>`),
			FileName:   ActionTestDefaultFile,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Error:ActionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='ActionsTest']/Action[@Name='TestAction']/Parameter[@Name='TestParam']: Parameter TestParam is missing a Description",
				"Error:ActionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='ActionsTest']/Action[@Name='TestAction']/Parameter[@Name='TestParam']: Parameter TestParam is missing a LongDescription",
			},
		},
	}
}

func TestActionChecks(t *testing.T) {
	t.Parallel()
	//nolint:paralleltest // The TestFunc calls Parallel...
	for _, tc := range GetActionTestCases() {
		t.Run(tc.Name, tc.TestFunc("Actions are valid", csdl.ActionChecks, nil))
	}
}

func BenchmarkActionChecks(b *testing.B) {
	for _, tc := range GetActionTestCases() {
		b.Run(tc.Name, func(b *testing.B) {
			b.ReportAllocs()
			searcher := helperGetSearcherForText(b, tc.FileName, tc.CSDL, "")
			suiteCase := &testsuite.Case{
				Name:   "Actions are valid",
				Func:   helperTestWrapper(nil, tc.Config, searcher, csdl.ActionChecks),
				Buffer: &bytes.Buffer{},
			}
			for b.Loop() {
				_ = suiteCase.Run()
			}
		})
	}
}
