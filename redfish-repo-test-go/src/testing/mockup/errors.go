/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup

import (
	"github.com/DMTF/redfishRepoTest/src"
)

type tHelperName interface {
	Helper()
	Name() string
}

func NewMockupError(
	t tHelperName, m *Mockup, filepath string,
	jsonPath string, severity src.Severity, message string,
) *src.JSONSourceError {
	t.Helper()
	return src.NewJSONSourceError(m.GetRealPath(filepath), jsonPath, message, severity, nil)
}

func NewMockupWarning(t tHelperName, m *Mockup, filepath string, jsonPath string, message string) *src.JSONSourceError {
	t.Helper()
	return NewMockupError(t, m, filepath, jsonPath, src.SeverityWarning, message)
}

func NewMockupCritical(
	t tHelperName, m *Mockup, filepath string,
	jsonPath string, message string,
) *src.JSONSourceError {
	t.Helper()
	return NewMockupError(t, m, filepath, jsonPath, src.SeverityError, message)
}
