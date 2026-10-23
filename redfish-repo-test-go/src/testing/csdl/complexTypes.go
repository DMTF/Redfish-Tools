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

func ComplexTypeChecks(t *testsuite.Testing, _ units.Units, cfg *config.Config, searcher *csdl.Searcher) {
	complexTypes := searcher.GetComplexTypes("")
	for _, complexType := range complexTypes {
		IsEntityNamePlural(complexType.Name, t, cfg, searcher, complexType)
		IsValidBaseType(complexType.BaseType, t, cfg, searcher, complexType)
		DoesComplexTypeHaveDescriptions(complexType, t, cfg, searcher)
	}
}

func DoesComplexTypeHaveDescriptions(complexType *csdl.ComplexType, t *testsuite.Testing,
	cfg *config.Config, searcher *csdl.Searcher) {
	if complexType.Abstract {
		// We allow abstract complex types to not have descriptions
		return
	}

	unversionedNamespace, _, _ := strings.Cut(complexType.GetSchema().Namespace, ".")
	unversionedName := unversionedNamespace + "." + complexType.GetName()
	if _, exists := descriptionsDebounce.Load(unversionedName); exists {
		return
	}

	short, long := ListHasDescriptions(complexType.Annotation)
	entityType := GetEntityTypeName(complexType)
	fullName := complexType.GetSchema().Namespace + "." + complexType.GetName()

	// If missing both descriptions, check base type first
	if !short && !long && complexType.BaseType != "" {
		baseType := GetBaseComplexType(complexType, searcher)
		if baseType != nil {
			DoesComplexTypeHaveDescriptions(baseType, t, cfg, searcher)
			return
		}
		// Another type as the base is not valid!
		t.Error(NewCSDLCritical(complexType,
			entityType+fmt.Sprintf(` %s has an invalid base type %s`, complexType.GetName(), complexType.BaseType), searcher))
	}

	// Check for missing descriptions
	if !short {
		t.Error(NewCSDLCritical(complexType,
			entityType+fmt.Sprintf(` %s does not contain a Description`, fullName), searcher))
	}
	if !long {
		t.Error(NewCSDLCritical(complexType,
			entityType+fmt.Sprintf(` %s does not contain a LongDescription`, fullName), searcher))
	}

	// Cache successful validations
	StoreDescriptionInDebounce(short && long, unversionedName)
}

func StoreDescriptionInDebounce(store bool, name string) {
	if store {
		descriptionsDebounce.Store(name, struct{}{})
	}
}

func GetBaseComplexType(complexType *csdl.ComplexType, searcher *csdl.Searcher) *csdl.ComplexType {
	if baseType := searcher.GetByTypeName(complexType.BaseType); baseType != nil {
		if baseComplexType, ok := baseType.(*csdl.ComplexType); ok {
			return baseComplexType
		}
	}
	return nil
}
