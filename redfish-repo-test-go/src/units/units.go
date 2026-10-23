/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package units

import "github.com/DMTF/redfishRepoTest/src/units/ucum"

// Units is an interface for unit conversion and validation.
type Units interface {
	// ValidMeasurement checks if a measurement string is valid.
	ValidMeasurement(measurement string) bool
	// GetUnitName returns the name of a unit.
	GetUnitName(measurement string) string
}

// Load loads the units implementation.
func Load() (Units, error) {
	return ucum.Load()
}
