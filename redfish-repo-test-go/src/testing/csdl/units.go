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

func ValidateUnits(t *testsuite.Testing, unitUtil units.Units, _ *config.Config, searcher *csdl.Searcher) {
	measurements := searcher.GetAnnotations("Measures.Unit")
	for _, measurement := range measurements {
		measurementValue := measurement.String
		if !unitUtil.ValidMeasurement(measurementValue) {
			t.Error(NewCSDLWarning(measurement, `Invalid measurement: "`+measurementValue+`"`, searcher))
		}
	}
}
