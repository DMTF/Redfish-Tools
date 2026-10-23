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
	EnumTestDefaultFile = "EnumTest"
)

func GetEnumTestCases() []csdlTestCase {
	cfg := &config.Config{
		AllowLists: config.AllowLists{
			NonPascalEnums: []string{"^Legacy"},
		},
	}
	return []csdlTestCase{
		{
			Name:       "No Enums",
			CSDL:       EmptyValidCSDL,
			FileName:   EnumTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Valid Enum",
			CSDL:       makeSimpleCSDLText(EnumTestDefaultFile, `<EnumType Name="TestEnum"><Member Name="ValidMember"/><Member Name="AnotherValid"/></EnumType>`),
			FileName:   EnumTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Invalid Pascal Case",
			CSDL:       makeSimpleCSDLText(EnumTestDefaultFile, `<EnumType Name="TestEnum"><Member Name="invalidMember"/><Member Name="another_invalid"/></EnumType>`),
			FileName:   EnumTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:EnumTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EnumTest']/EnumType[@Name='TestEnum']/Member[@Name='invalidMember']: Enum member name should be PascalCased: \"invalidMember\"",
				"Warning:EnumTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='EnumTest']/EnumType[@Name='TestEnum']/Member[@Name='another_invalid']: Enum member name should be PascalCased: \"another_invalid\"",
			},
		},
		{
			Name:       "Legacy Enum Allowed",
			CSDL:       makeSimpleCSDLText(EnumTestDefaultFile, `<EnumType Name="LegacyEnum"><Member Name="Legacy_Member"/></EnumType>`),
			FileName:   EnumTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
	}
}

func TestEnumChecks(t *testing.T) {
	t.Parallel()
	//nolint:paralleltest // The TestFunc calls Parallel...
	for _, tc := range GetEnumTestCases() {
		t.Run(tc.Name, tc.TestFunc("Enum checks are valid", csdl.EnumChecks, nil))
	}
}
