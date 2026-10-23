/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"fmt"
	"strings"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
)

func ActionChecks(t *testsuite.Testing, _ units.Units, cfg *config.Config, searcher *csdl.Searcher) {
	actions := searcher.GetActions("")
	for _, action := range actions {
		DoesActionHaveDescriptions(action, t, cfg, searcher)
		IsActionBound(action, t, cfg, searcher)
		foundTargetParam := false
		for _, parameter := range action.Parameter {
			if DoesParameterHaveDescriptions(parameter, t, cfg, searcher) {
				foundTargetParam = true
			}
		}
		if !foundTargetParam {
			t.Error(NewCSDLCritical(action,
				fmt.Sprintf(`Action %s does not have a target parameter `+
					`(should have a parameter with Type ending in .Actions or .OemActions)`, action.Name), searcher))
		}
	}
}

func DoesActionHaveDescriptions(
	action *csdl.Action, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher,
) {
	short, long := ListHasDescriptions(action.Annotation)
	if !short {
		t.Error(NewCSDLCritical(action,
			fmt.Sprintf(`Action %s does not contain a Description`, action.Name), searcher))
	}
	if !long {
		t.Error(NewCSDLCritical(action,
			fmt.Sprintf(`Action %s does not contain a LongDescription`, action.Name), searcher))
	}
}

func IsActionBound(
	action *csdl.Action, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher,
) {
	if !action.IsBound {
		t.Error(NewCSDLWarning(action,
			fmt.Sprintf(`Action %s is not bound (IsBound should be true)`, action.Name), searcher))
	}
}

func DoesParameterHaveDescriptions(
	parameter *csdl.Parameter, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher,
) bool {
	if strings.HasSuffix(parameter.Type, ".Actions") || strings.HasSuffix(parameter.Type, ".OemActions") {
		// This is the target parameter, skip it.
		return true
	}
	short, long := ListHasDescriptions(parameter.Annotation)
	if !short {
		t.Error(NewCSDLCritical(parameter,
			fmt.Sprintf(`Parameter %s is missing a Description`, parameter.Name), searcher))
	}
	if !long {
		t.Error(NewCSDLCritical(parameter,
			fmt.Sprintf(`Parameter %s is missing a LongDescription`, parameter.Name), searcher))
	}
	return false
}
