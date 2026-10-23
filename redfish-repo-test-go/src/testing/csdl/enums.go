/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
)

func EnumChecks(t *testsuite.Testing, _ units.Units, cfg *config.Config, searcher *csdl.Searcher) {
	enums := searcher.GetEnumTypes("")
	for _, enum := range enums {
		for _, member := range enum.Member {
			if !IsValidPascalCasedEnumMember(member.Name, cfg) {
				t.Error(NewCSDLWarning(member, `Enum member name should be PascalCased: "`+member.Name+`"`, searcher))
			}
		}
	}
}

func IsValidPascalCasedEnumMember(memberName string, cfg *config.Config) bool {
	if PascalRegex.MatchString(memberName) {
		return true
	}
	patterns := cfg.AllowLists.GetNonPascalEnums()
	for _, pattern := range patterns {
		if pattern.MatchString(memberName) {
			return true
		}
	}
	return false
}
