/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"fmt"
	"slices"
	"strings"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
)

//nolint:gochecknoglobals
var (
	propsWithNoDescriptionsAllowed = []string{"Name", "Id", "Description"}
	primativeTypes                 = []string{
		"Edm.Boolean", "Edm.DateTimeOffset", "Edm.Decimal", "Edm.Double",
		"Edm.Guid", "Edm.Int64", "Edm.String", "Edm.Duration", "Edm.PrimitiveType",
	}
	// These are names that Redfish allows outside of the UCUM standard.
	alternativeUnitNames = map[string]string{
		"%":         "Percentage",
		"{rev}/min": "RPM",
		"A":         "Amps",            // UCUM results in Ampère
		"A.h":       "AmpHours",        // UCUM results in AmpèreHour
		"Gbit/s":    "Gbps",            // Allow the Gbps abbreviation
		"GiBy":      "GiB",             // Allow the GiB abbreviation
		"Hz":        "Hz",              // Allow the Hz abbreviation
		"kg":        "Kg",              // Allow the Kg abbreviation
		"kg/m3":     "KgPerCubicMeter", // UCUM results in KilogramsPerCubicMeter
		"KiBy":      "KiBytes",         // Allow the KiBytes abbreviation
		"kJ/kg/K":   "kJoulesPerKgK",   // UCUM results in KilojoulesPerKilogramsPerKelvin
		"kPa":       "kPa",             // Allow the kPa abbreviation
		"kV.A.h":    "kVAh",            // UCUM results in KiloVoltsPerAmpèreHour
		"Mbit/s":    "Mbps",            // Allow the Mbps abbreviation
		"MiBy":      "MiB",             // Allow the MiB abbreviation
		"min":       "Min",             // Allow the Min abbreviation
		"MHz":       "MHz",             // Allow the MHz abbreviation
		"mA":        "MilliAmps",       // UCUM results in Milliampère
		"mm":        "Mm",              // Allow the Mm abbreviation
		"mW":        "MilliWatts",      // Not sure why we pascal case this one...
		"ms":        "Ms",              // Allow the Ms abbreviation
		"W":         "Wattage",         // UCUM results in Watt
		"V":         "Voltage",
		"V.A":       "VA",
	}
)

func PropertyChecks(t *testsuite.Testing, unitUtil units.Units, cfg *config.Config, searcher *csdl.Searcher) {
	for _, property := range searcher.GetProperties("") {
		if !IsValidPascalCasedPropertyName(property.Name, cfg) {
			t.Error(NewCSDLWarning(property, `Property name should be PascalCased: "`+property.Name+`"`, searcher))
		}
		PropertyHasDescriptions(property, t, cfg, searcher)
		PropertyHasCorrectUnits(property, t, unitUtil, cfg, searcher)
		PropertyHasKnownType(property, t, cfg, searcher)
	}
	for _, property := range searcher.GetNavigationProperties("") {
		if !IsValidPascalCasedPropertyName(property.Name, cfg) {
			t.Error(NewCSDLWarning(property, `NavigationProperty name should be PascalCased: "`+property.Name+`"`, searcher))
		}
		NavPropertyIsNotCollectionAndNullable(property, t, searcher)
		NavPropertyHasDescriptions(property, t, cfg, searcher)
	}
}

func IsValidPascalCasedPropertyName(propName string, cfg *config.Config) bool {
	if PascalRegex.MatchString(propName) {
		return true
	}
	patterns := cfg.AllowLists.GetNonPascalProperties()
	for _, pattern := range patterns {
		if pattern.MatchString(propName) {
			return true
		}
	}
	return false
}

func PropertyHasDescriptions(
	property *csdl.Property, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher,
) {
	if slices.Contains(propsWithNoDescriptionsAllowed, property.Name) {
		return
	}
	short, long := ListHasDescriptions(property.Annotation)
	if !short {
		t.Error(NewCSDLCritical(property, `Property '`+property.Name+`' does not contain a Description`, searcher))
	}
	if !long {
		t.Error(NewCSDLCritical(property, `Property '`+property.Name+`' does not contain a LongDescription`, searcher))
	}
}

func PropertyHasCorrectUnits(property *csdl.Property, t *testsuite.Testing,
	unitUtil units.Units, cfg *config.Config, searcher *csdl.Searcher) {
	annotation := GetAnnotationFromList(property.Annotation, "Measures.Unit")
	if annotation == nil {
		// No units skip this.
		return
	}
	if unitUtil == nil {
		// No unit util, skip this check.
		return
	}
	if annotation.String == "%" {
		// Special case for %, sometimes it is in the front of the name
		if strings.HasPrefix(property.Name, "Percent") || strings.HasPrefix(property.Name, "Percentage") {
			return
		}
	}
	alternate, ok := alternativeUnitNames[annotation.String]
	if ok && strings.HasSuffix(property.Name, alternate) {
		return
	}
	unitName := unitUtil.GetUnitName(annotation.String)
	if !IsPropNameAllowedWithUnit(property.Name, unitName, cfg) {
		t.Error(NewCSDLWarning(property,
			fmt.Sprintf(`Property %s should have unit %s in its name`, property.Name, unitName), searcher))
	}
}

func IsPropNameAllowedWithUnit(propertyName, unitName string, cfg *config.Config) bool {
	// Check if the property name already has the unit in it
	if strings.HasSuffix(propertyName, unitName) || strings.HasSuffix(propertyName, unitName+"s") {
		return true
	}

	// Check if the property name is in the allowlist
	patterns := cfg.AllowLists.GetPropertiesWithIncorrectUnits()
	for _, pattern := range patterns {
		if pattern.MatchString(propertyName) {
			return true
		}
	}

	return false
}

func PropertyHasKnownType(property *csdl.Property, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher) {
	typeName := strings.TrimPrefix(property.Type, "Collection(")
	typeName = strings.TrimSuffix(typeName, ")")
	if slices.Contains(primativeTypes, typeName) {
		return
	}
	csdlType := searcher.GetByTypeName(typeName)
	if csdlType != nil {
		switch csdlType.(type) {
		case csdl.EnumType, *csdl.EnumType:
			return
		case csdl.ComplexType, *csdl.ComplexType:
			return
		case csdl.TypeDefinition, *csdl.TypeDefinition:
			return
		}
	}
	patterns := cfg.AllowLists.GetUnknownTypeReferences()
	for _, pattern := range patterns {
		if pattern.MatchString(typeName) {
			return
		}
	}
	t.Error(NewCSDLCritical(property,
		fmt.Sprintf(`Property %s does not contain a valid type has '%s'`, property.Name, property.Type), searcher))
}

func NavPropertyIsNotCollectionAndNullable(
	property *csdl.NavigationProperty, t *testsuite.Testing, searcher *csdl.Searcher,
) {
	if !strings.HasPrefix(property.Type, "Collection(") {
		return
	}
	if property.Nullable == nil {
		return
	}
	if *property.Nullable {
		t.Error(NewCSDLCritical(property,
			`NavigationProperty '`+property.Name+`' should not be nullable as it is a collection type.`, searcher))
	}
}

func NavPropertyHasDescriptions(
	property *csdl.NavigationProperty, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher,
) {
	short, long := ListHasDescriptions(property.Annotation)
	if !short {
		t.Error(NewCSDLCritical(property,
			`NavigationProperty '`+property.Name+`' does not contain a Description`, searcher))
	}
	if !long {
		t.Error(NewCSDLCritical(property,
			`NavigationProperty '`+property.Name+`' does not contain a LongDescription`, searcher))
	}
}
