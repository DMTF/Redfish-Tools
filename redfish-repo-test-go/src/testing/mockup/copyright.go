/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup

import (
	"path/filepath"
	"strings"

	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

func (m *Mockup) CopyrightTest(t *testsuite.Testing) {
	if m.Config.Copyright == "" {
		return
	}
	for path, file := range m.files {
		if strings.Contains(path, "-example.json") {
			continue
		}
		m.DoCopyrightCheck(t, path, file)
	}
}

func (m *Mockup) DoCopyrightCheck(t *testsuite.Testing, path string, file *File) {
	copyrightValue, ok := file.Content["@Redfish.Copyright"].(string)
	if !ok {
		for _, path := range m.Config.AllowLists.NoCopyrightPaths {
			if matched, _ := filepath.Match(path, path); matched {
				return
			}
		}
		t.Error(NewMockupWarning(t, m, path, "@Redfish.Copyright", "Missing @Redfish.Copyright field"))
		return
	}
	if !m.Config.GetCopyrightRegEx().MatchString(copyrightValue) {
		t.Error(NewMockupWarning(t, m, path, "@Redfish.Copyright", "Copyright mismatch"))
	}
}
