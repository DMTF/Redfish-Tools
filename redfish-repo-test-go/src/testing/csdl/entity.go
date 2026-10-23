/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"fmt"
	"log"
	"slices"
	"strings"
	"sync"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
)

//nolint:gochecknoglobals
var allowedSEndingNames = []string{
	"Actions",
	"Address",
	"Attributes",
	"Bios",
	"Capabilities",
	"Chassis",
	"Links",
	"Metrics",
	"Parameters",
	"Properties",
	"Settings",
	"Status",
	"Statistics",
}

func EntityChecks(t *testsuite.Testing, _ units.Units, cfg *config.Config, searcher *csdl.Searcher) {
	entities := searcher.GetEntityTypes("")
	for _, entity := range entities {
		IsEntityNamePlural(entity.Name, t, cfg, searcher, entity)
		IsValidBaseType(entity.BaseType, t, cfg, searcher, entity)
		DoesEntityHaveActions(entity, t, cfg, searcher)
		DoesEntityHaveDescriptions(entity, t, cfg, searcher)
		if entity.BaseType == "Resource.v1_0_0.ResourceCollection" || entity.BaseType == "Resource.v1_0_0.Resource" {
			// Base enties must contain Insert, Update, and Delete restrictions
			DoesEntityHaveRestrictions(entity, t, cfg, searcher)
			// Base enties must be in the privilege registry
			IsEntityInPrivilegeRegistry(entity, t, cfg, searcher)
		}
		AddWritablePropertyCount(entity, searcher)
	}
	for _, entity := range entities {
		unversionedNamespace, _, _ := strings.Cut(entity.GetSchema().Namespace, ".")
		unversionedName := unversionedNamespace + "." + entity.GetName()
		IsEntityPropertlyUpdatable(entity, t, searcher, unversionedName)
		// Only report error once per type.
		updateableCache.Delete(unversionedName)
	}
}

func IsEntityNamePlural(name string, t *testsuite.Testing,
	cfg *config.Config, searcher *csdl.Searcher, entity csdl.Searchable) {
	if !strings.HasSuffix(name, "s") {
		return
	}
	for _, allowedName := range allowedSEndingNames {
		if strings.HasSuffix(name, allowedName) {
			return
		}
	}
	patterns := cfg.AllowLists.GetPluralEntityPatterns()
	// Allow schema names to also be allowed without duplication
	patterns = append(patterns, cfg.AllowLists.GetPluralSchemaPatterns()...)
	for _, pattern := range patterns {
		if pattern.MatchString(name) {
			return
		}
	}
	entityType := GetEntityTypeName(entity)
	t.Error(NewCSDLWarning(entity, entityType+fmt.Sprintf(` '%s' should not be plural`, name), searcher))
}

func IsValidBaseType(
	baseType string, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher, entity csdl.Searchable,
) {
	if !IsEntityBaseTypeValid(searcher, baseType) {
		entityType := GetEntityTypeName(entity)
		t.Error(NewCSDLCritical(entity,
			entityType+fmt.Sprintf(` %s BaseType of '%s' is not valid`, entity.GetName(), baseType), searcher))
	}
}

func IsEntityPropertlyUpdatable(
	entity *csdl.EntityType, t *testsuite.Testing, searcher *csdl.Searcher, unversionedName string,
) {
	updateableIntf, ok := updateableCache.Load(unversionedName)
	if !ok {
		return
	}
	//nolint:forcetypeassert // Can't happen panic if it does.
	updateable := updateableIntf.(bool)
	var writableCount []string
	writableCountIntf, ok := writablePropCount.Load(unversionedName)
	if ok {
		//nolint:forcetypeassert // Can't happen panic if it does.
		writableCount = writableCountIntf.([]string)
	}
	if updateable && len(writableCount) == 0 {
		entityType := GetEntityTypeName(entity)
		t.Error(NewCSDLWarning(entity,
			entityType+fmt.Sprintf(` %s is marked as updatable but has no writable properties`, entity.GetName()), searcher))
	}
	if !updateable && len(writableCount) > 0 {
		entityType := GetEntityTypeName(entity)
		// List only the first 5 writable properties to avoid overwhelming error messages
		const maxPropertiesToList = 5
		propList := writableCount
		if len(propList) > maxPropertiesToList {
			propList = append(propList[:maxPropertiesToList], fmt.Sprintf("and %d more", len(propList)-maxPropertiesToList))
		}
		// Point the error to the UpdateRestrictions annotation for better editor line positioning
		updateRest := GetAnnotationFromList(entity.Annotation, "Capabilities.UpdateRestrictions")
		var errorTarget csdl.Searchable = entity
		if updateRest != nil {
			errorTarget = updateRest
		}
		t.Error(NewCSDLWarning(errorTarget,
			entityType+fmt.Sprintf(` %s has writable properties '%s' but is not marked as updatable`,
				entity.GetName(), strings.Join(propList, ", ")), searcher))
	}
}

// (or its children) multiple times.
//
//nolint:gochecknoglobals // Use this to avoid having to check for actions on the same entity
var (
	actionsDebounce      = sync.Map{} // map[string]struct{}{}
	descriptionsDebounce = sync.Map{} // map[string]struct{}{}
	updateableCache      = sync.Map{} // map[string]bool{}
	writablePropCount    = sync.Map{} // map[string][]string{}
)

func DoesEntityHaveActions(entity *csdl.EntityType, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher) {
	// Ignore collections, trivial namespaces, service root, and action info
	if entity.BaseType == "Resource.v1_0_0.ResourceCollection" || len(entity.Property) == 0 ||
		entity.Name == "ServiceRoot" || strings.HasSuffix(entity.Name, "ActionInfo") {
		return
	}
	unversionedNamespace, _, _ := strings.Cut(entity.GetSchema().Namespace, ".")
	unversionedName := unversionedNamespace + "." + entity.GetName()
	if _, exists := actionsDebounce.Load(unversionedName); exists {
		return
	}
	for _, prop := range entity.Property {
		if prop.Name == "Actions" {
			actionsDebounce.Store(unversionedName, struct{}{})
			return
		}
	}
	// Check the allow list
	fullName := entity.GetSchema().Namespace + "." + entity.GetName()
	if slices.Contains(cfg.AllowLists.NoActionsAllowed, fullName) {
		// Do not add to debounce we want to make sure we are explicit on previous bad actors.
		return
	}
	entityType := GetEntityTypeName(entity)
	t.Error(NewCSDLWarning(entity, entityType+fmt.Sprintf(` %s does not contain an Actions property`, fullName), searcher))
}

func DoesEntityHaveDescriptions(
	entity *csdl.EntityType, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher,
) {
	unversionedNamespace, _, _ := strings.Cut(entity.GetSchema().Namespace, ".")
	if unversionedNamespace == "Resource" {
		return
	}
	unversionedName := unversionedNamespace + "." + entity.GetName()
	if _, exists := descriptionsDebounce.Load(unversionedName); exists {
		return
	}
	if entity.BaseType == "Resource.ReferenceableMember" || entity.BaseType == "Resource.v1_0_0.ReferenceableMember" {
		// we don't require descriptions on these entities for some reason.
		descriptionsDebounce.Store(unversionedName, struct{}{})
		return
	}
	short, long := ListHasDescriptions(entity.Annotation)
	if !short {
		fullName := entity.GetSchema().Namespace + "." + entity.GetName()
		entityType := GetEntityTypeName(entity)
		t.Error(NewCSDLCritical(entity, entityType+fmt.Sprintf(` %s does not contain a Description`, fullName), searcher))
	}
	if !long {
		fullName := entity.GetSchema().Namespace + "." + entity.GetName()
		entityType := GetEntityTypeName(entity)
		t.Error(NewCSDLCritical(entity, entityType+fmt.Sprintf(` %s does not contain a LongDescription`, fullName), searcher))
	}
	if long && short {
		descriptionsDebounce.Store(unversionedName, struct{}{})
	}
}

func DoesEntityHaveRestrictions(
	entity *csdl.EntityType, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher,
) {
	insertRest := GetAnnotationFromList(entity.Annotation, "Capabilities.InsertRestrictions")
	if insertRest == nil {
		entityType := GetEntityTypeName(entity)
		t.Error(NewCSDLWarning(entity,
			entityType+fmt.Sprintf(` %s does not contain a Capabilities.InsertRestrictions annotation`,
				entity.GetName()), searcher))
	} else if insertRest.Record.PropertyValue[0].Bool && !strings.HasSuffix(entity.Name, "Collection") {
		entityType := GetEntityTypeName(entity)
		t.Error(NewCSDLWarning(entity,
			entityType+fmt.Sprintf(` %s has InsertRestrictions set to true but is not a collection`,
				entity.GetName()), searcher))
	}
	updateRest := GetAnnotationFromList(entity.Annotation, "Capabilities.UpdateRestrictions")
	if updateRest == nil {
		entityType := GetEntityTypeName(entity)
		t.Error(NewCSDLWarning(entity,
			entityType+fmt.Sprintf(` %s does not contain a Capabilities.UpdateRestrictions annotation`,
				entity.GetName()), searcher))
	} else {
		unversionedNamespace, _, _ := strings.Cut(entity.GetSchema().Namespace, ".")
		unversionedName := unversionedNamespace + "." + entity.GetName()
		updateableCache.Store(unversionedName, updateRest.Record.PropertyValue[0].Bool)
	}
	if !AnnotationListHas(entity.Annotation, "Capabilities.DeleteRestrictions") {
		entityType := GetEntityTypeName(entity)
		t.Error(NewCSDLWarning(entity,
			entityType+fmt.Sprintf(` %s does not contain a Capabilities.DeleteRestrictions annotation`,
				entity.GetName()), searcher))
	}
}

func IsEntityInPrivilegeRegistry(
	entity *csdl.EntityType, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher,
) {
	privRegistry := cfg.GetPrivilegeRegistry()
	mappings, ok := privRegistry["Mappings"].(map[string]any)
	if !ok {
		// This registry is in a bad format... this should be handled by another test
		return
	}
	found := false
	for _, mappingIntf := range mappings {
		mapping, ok := mappingIntf.(map[string]any)
		if !ok {
			continue
		}
		name, ok := mapping["Entity"].(string)
		if !ok {
			continue
		}
		if name == entity.Name {
			found = true
			break
		}
	}
	if !found {
		entityType := GetEntityTypeName(entity)
		t.Error(NewCSDLWarning(entity,
			entityType+fmt.Sprintf(` %s is not in the privilege registry`, entity.GetName()), searcher))
	}
}

func IsEntityBaseTypeValid(searcher *csdl.Searcher, baseType string) bool {
	if baseType == "" {
		return true
	}
	base := searcher.GetByTypeName(baseType)
	return base != nil
}

func GetEntityTypeName(entity csdl.Searchable) string {
	switch t := entity.(type) {
	case *csdl.EntityType:
		return "Entity"
	case csdl.ComplexType, *csdl.ComplexType:
		return "ComplexType"
	default:
		panic("unknown type: " + fmt.Sprintf("%#v", t))
	}
}

func AddWritablePropertyCount(entity *csdl.EntityType, searcher *csdl.Searcher) {
	unversionedNamespace, _, _ := strings.Cut(entity.GetSchema().Namespace, ".")
	unversionedName := unversionedNamespace + "." + entity.GetName()
	typesVisited := make(map[string]struct{})
	for _, property := range entity.Property {
		if isPropReadWriteOrContainsReadWrite(property, searcher, typesVisited) {
			var writableCount []string
			writableCountIntf, ok := writablePropCount.Load(unversionedName)
			if ok {
				//nolint:forcetypeassert // Can't happen panic if it does.
				writableCount = writableCountIntf.([]string)
			}
			writablePropCount.Store(unversionedName, append(writableCount, property.Name))
		}
	}
	for _, property := range entity.NavigationProperty {
		if isNavPropReadWriteOrContainsReadWrite(property, searcher, typesVisited) {
			var writableCount []string
			writableCountIntf, ok := writablePropCount.Load(unversionedName)
			if ok {
				//nolint:forcetypeassert // Can't happen panic if it does.
				writableCount = writableCountIntf.([]string)
			}
			writablePropCount.Store(unversionedName, append(writableCount, property.Name))
		}
	}
}

func isPropReadWriteOrContainsReadWrite(
	property *csdl.Property, searcher *csdl.Searcher, typesVisited map[string]struct{},
) bool {
	if _, ok := typesVisited[property.Type]; ok {
		return false
	}
	annotation := GetAnnotationFromList(property.Annotation, "OData.Permissions")
	if annotation != nil {
		// If the property is explicitly marked either way, believe it.
		return annotation.EnumMember == "OData.Permission/ReadWrite"
	}
	// Short cut, check if the type is already in our cache...
	_, ok := writablePropCount.Load(property.Type)
	if ok {
		return true
	}
	baseType := searcher.GetByTypeName(property.Type)
	typesVisited[property.Type] = struct{}{}
	//nolint:nestif
	if baseType != nil {
		if t, ok := baseType.(*csdl.ComplexType); ok {
			for _, prop := range t.Property {
				if isPropReadWriteOrContainsReadWrite(prop, searcher, typesVisited) {
					return true
				}
			}
			for _, prop := range t.NavigationProperty {
				if isNavPropReadWriteOrContainsReadWrite(prop, searcher, typesVisited) {
					return true
				}
			}
			return AreAnyDescendantsWritable(property.Type, searcher, typesVisited)
		}
	}
	return false
}

func AreAnyDescendantsWritable(typeName string, searcher *csdl.Searcher, typesVisited map[string]struct{}) bool {
	typeName = strings.TrimPrefix(typeName, "Collection(")
	typeName = strings.TrimSuffix(typeName, ")")
	writable := AreAnyDecdendentEntityTypesWritable(typeName, searcher, typesVisited)
	if writable {
		return true
	}
	return AreAnyDecdendentComplexTypesWritable(typeName, searcher, typesVisited)
}

func AreAnyDecdendentEntityTypesWritable(
	typeName string, searcher *csdl.Searcher, typesVisited map[string]struct{},
) bool {
	entities := searcher.GetEntityTypes("*")
	for _, entity := range entities {
		if entity.BaseType == typeName {
			for _, property := range entity.Property {
				if isPropReadWriteOrContainsReadWrite(property, searcher, typesVisited) {
					return true
				}
			}
			for _, navProp := range entity.NavigationProperty {
				if isNavPropReadWriteOrContainsReadWrite(navProp, searcher, typesVisited) {
					return true
				}
			}
			if AreAnyDescendantsWritable(entity.GetSchema().Namespace+"."+entity.Name, searcher, typesVisited) {
				return true
			}
		}
	}
	return false
}

func AreAnyDecdendentComplexTypesWritable(
	typeName string, searcher *csdl.Searcher, typesVisited map[string]struct{},
) bool {
	complexTypes := searcher.GetComplexTypes("*")
	for _, complexType := range complexTypes {
		if complexType.BaseType == typeName {
			for _, property := range complexType.Property {
				if isPropReadWriteOrContainsReadWrite(property, searcher, typesVisited) {
					return true
				}
			}
			for _, navProp := range complexType.NavigationProperty {
				if isNavPropReadWriteOrContainsReadWrite(navProp, searcher, typesVisited) {
					return true
				}
			}
			if AreAnyDescendantsWritable(complexType.GetSchema().Namespace+"."+complexType.Name, searcher, typesVisited) {
				return true
			}
		}
	}
	return false
}

//nolint:gocognit,cyclop
func isNavPropReadWriteOrContainsReadWrite(
	property *csdl.NavigationProperty, searcher *csdl.Searcher, typesVisited map[string]struct{},
) bool {
	if _, ok := typesVisited[property.Type]; ok {
		return false
	}
	annotation := GetAnnotationFromList(property.Annotation, "OData.Permissions")
	if annotation != nil {
		// If the property is explicitly marked either way, believe it.
		return annotation.EnumMember == "OData.Permission/ReadWrite"
	}
	annotation = GetAnnotationFromList(property.Annotation, "Redfish.ExcerptCopy")
	if annotation != nil && property.Type == "Control.Control" {
		return true
	}
	baseType := searcher.GetByTypeName(property.Type)
	typesVisited[property.Type] = struct{}{}
	if baseType != nil {
		switch t := baseType.(type) {
		case *csdl.ComplexType:
			for _, prop := range t.Property {
				if isPropReadWriteOrContainsReadWrite(prop, searcher, typesVisited) {
					return true
				}
			}
			for _, prop := range t.NavigationProperty {
				if isNavPropReadWriteOrContainsReadWrite(prop, searcher, typesVisited) {
					return true
				}
			}
			// This is only valid for nav properties not regular properties
		case *csdl.EntityType:
			for _, prop := range t.Property {
				if isPropReadWriteOrContainsReadWrite(prop, searcher, typesVisited) {
					return true
				}
			}
			for _, prop := range t.NavigationProperty {
				if isNavPropReadWriteOrContainsReadWrite(prop, searcher, typesVisited) {
					return true
				}
			}
		default:
			log.Printf("Got unknown type %s %T\n", property.Type, t)
		}
	}
	return false
}
