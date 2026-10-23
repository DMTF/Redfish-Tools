/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup

import (
	"fmt"
	"slices"

	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

func (m *Mockup) ExplorerTest(t *testsuite.Testing) {
	if slices.Contains(m.Config.AllowLists.AllowedNoExplorerMockups, m.Name) {
		return
	}
	explorerFile, ok := m.files["/redfish/v1/explorer_config.json"]
	if !ok {
		t.Error(NewMockupCritical(t, m, "/redfish/v1/explorer_config.json", "", "Explorer config not found"))
		return
	}
	explorerConfig := explorerFile.Content
	_, ok = explorerConfig["name"].(string)
	if !ok {
		t.Error(NewMockupCritical(t, m, "/redfish/v1/explorer_config.json", "name", "Explorer config name field is missing or not a string"))
		return
	}
	_, ok = explorerConfig["description"].(string)
	if !ok {
		t.Error(NewMockupCritical(t, m, "/redfish/v1/explorer_config.json", "description", "Explorer config description field is missing or not a string"))
		return
	}
	// Make sure we have all the referenced navlinks...
	navLinks, ok := explorerConfig["navlinks"].([]any)
	if !ok {
		t.Error(NewMockupCritical(t, m, "/redfish/v1/explorer_config.json", "navlinks", "Explorer config navlinks field is missing or not an array"))
		return
	}
	m.CheckExplorerNavLinksRecursive(t, "", navLinks)
}

func (m *Mockup) CheckExplorerNavLinksRecursive(t *testsuite.Testing, path string, navLinks []any) {
	for i, navLink := range navLinks {
		navLinkMap, ok := navLink.(map[string]any)
		if !ok {
			jsonPath := fmt.Sprintf("navlinks[%d]", i)
			if path != "" {
				jsonPath = fmt.Sprintf("navlinks.%s[%d]", path, i)
			}
			t.Error(NewMockupWarning(t, m, "/redfish/v1/explorer_config.json", jsonPath, "has invalid navlinks"))
			continue
		}
		target, ok := navLinkMap["target"].(string)
		if !ok {
			jsonPath := fmt.Sprintf("navlinks[%d].target", i)
			if path != "" {
				jsonPath = fmt.Sprintf("navlinks.%s[%d].target", path, i)
			}
			t.Error(NewMockupWarning(t, m, "/redfish/v1/explorer_config.json", jsonPath, "has invalid navlinks target"))
			continue
		}
		if target == "main" || target == "default" {
			// This is fine this means the service root or this node so just skip this...
			continue
		}
		// Make sure the target exists in the mockup
		if !m.PathValid("/redfish/v1/" + path + target) {
			jsonPath := fmt.Sprintf("navlinks[%d].target", i)
			if path != "" {
				jsonPath = fmt.Sprintf("navlinks.%s[%d].target", path, i)
			}
			t.Error(NewMockupWarning(t, m, "/redfish/v1/explorer_config.json", jsonPath, fmt.Sprintf("has invalid navlinks target %s", target)))
		}
		childLinks, ok := navLinkMap["navlinks"].([]any)
		if ok {
			m.CheckExplorerNavLinksRecursive(t, path+target+"/", childLinks)
		}
	}
}
