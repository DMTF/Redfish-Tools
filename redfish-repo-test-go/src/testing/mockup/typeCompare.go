/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup

import (
	"fmt"
	"maps"
	"os"
	"slices"
	"strings"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

//nolint:cyclop
func (m *Mockup) FileTypesAreValid(t *testsuite.Testing) {
	if m.types == nil {
		typeMap, ok := t.GetAttr("typeMap").(map[string]*csdl.Type)
		if !ok {
			t.Fatal("typeMap attribute not found")
		}
		m.types = typeMap
		descendantIdx, ok := t.GetAttr("descendantIdx").(DescendantIndex)
		if !ok {
			// Keep direct users of Mockup working even when it was not
			// created through CreateTestsFromConfig.
			descendantIdx = BuildDescendantIndex(m.types)
		}
		m.descendantIdx = descendantIdx
	}
	if m.searcher == nil {
		searcher, ok := t.GetAttr("searcher").(*csdl.Searcher)
		if !ok {
			t.Fatal("searcher attribute not found")
		}
		m.searcher = searcher
	}
	if m.Name == "non-resource-examples" {
		return
	}
	for path, file := range m.files {
		if m.isExcludedFromTypeCheck(path) {
			continue
		}
		odataType, ok := file.Content["@odata.type"].(string)
		if !ok {
			if _, ok := file.Content["error"]; ok {
				// This is an error response example, so we don't need to check the type
				continue
			}
			t.Error(NewMockupCritical(t, m, path, "@odata.type", "Missing @odata.type field"))
			continue
		}
		// Check if the type is valid
		odataType = strings.TrimPrefix(odataType, "#")
		csdlType, ok := m.types[odataType]
		if !ok {
			t.Error(NewMockupCritical(t, m, path, "@odata.type", "Invalid @odata.type field"))
			continue
		}
		file.Type = csdlType
	}
}

func (f *File) DoTypeContentCheckForProperty(
	t *testsuite.Testing, path string, m *Mockup,
	propertyName string, csdlType *csdl.Type, value any,
) {
	switch v := value.(type) {
	case map[string]any:
		// This is a complex type or entity type, so we need to check the properties
		f.DoTypeContentCheckFromComplexTypeProperty(t, path, m, propertyName, csdlType, v)
	case string:
		// This should be an enum type, so we need to make sure the value matches a member
		f.DoTypeContentCheckFromEnumTypeProperty(t, path, m, propertyName, csdlType, v)
	case []any:
		// This is a collection... now is it a collection of complex types? Enums? Something else?
		if len(v) == 0 {
			// Empty collection, nothing to check
			return
		}
		for i, item := range v {
			f.DoTypeContentCheckForProperty(t, path, m, propertyName+fmt.Sprintf("[%d]", i), csdlType, item)
		}
	default:
		_, _ = fmt.Fprintf(
			os.Stderr,
			"Validate prop %s type %s value %#v %#v\n",
			propertyName,
			csdlType.Name,
			v,
			csdlType,
		)
	}
}

//nolint:cyclop
func (f *File) DoTypeContentCheckFromComplexTypeProperty(
	t *testsuite.Testing, path string, m *Mockup,
	propertyName string, csdlType *csdl.Type,
	value map[string]any,
) {
	if csdlType.Wildcard {
		// Wildcard types allow any properties, so we don't need to check them
		return
	}
	if csdlType.Name == "Actions" {
		// Do action verification...
		return
	}
	for k, v := range value {
		if strings.Contains(k, "@Redfish") {
			// Validate that the annotation is valid
			continue
		}
		if k == "@odata.type" {
			if isAutoFix(t) {
				f.autoFixRemoveUnneededODataType(t, path, m, propertyName, value)
				continue
			}
			t.Error(NewMockupWarning(t, m, path, propertyName+"/@odata.type", "Unneeded @odata.type!"))
			continue
		}
		childPropName := propertyName + "." + k
		csdlProp := GetPropertyFromCSDLTypeOrDescendents(k, csdlType, m.types, m.descendantIdx)
		if csdlProp == nil {
			t.Error(NewMockupWarning(t, m, path, childPropName,
				fmt.Sprintf("Unknown property %s for type %s", childPropName, csdlType.Name)))
			continue
		}

		if csdlProp.Navigation {
			if strings.HasPrefix(csdlProp.Type, "Collection(") {
				collection, ok := v.([]any)
				if !ok {
					t.Error(NewMockupWarning(t, m, path, childPropName,
						fmt.Sprintf("Navigation link must be a JSON array, got %T %s", v, csdlProp.Type)))
					continue
				}
				for i, item := range collection {
					f.NavLinkSingletonIsSane(t, path, m, item, fmt.Sprintf("%s[%d]", childPropName, i), csdlProp)
				}
				continue
			}
			f.NavLinkSingletonIsSane(t, path, m, v, childPropName, csdlProp)
			continue
		}

		f.PropValueIsSane(t, path, m, childPropName, v, csdlProp)
	}
}

func (f *File) autoFixRemoveUnneededODataType(
	t *testsuite.Testing, path string, m *Mockup,
	propertyName string, value map[string]any,
) {
	delete(value, "@odata.type")
	if err := f.Save(m, path); err != nil {
		t.Error(NewMockupWarning(t, m, path, propertyName+"/@odata.type",
			"Failed to remove unneeded @odata.type: "+err.Error()))
	}
}

func (f *File) DoTypeContentCheckFromEnumTypeProperty(
	t *testsuite.Testing, path string, m *Mockup,
	propertyName string, csdlType *csdl.Type, value string,
) {
	_, ok := csdlType.Members[value]
	if !ok {
		possible := slices.Sorted(maps.Keys(csdlType.Members))
		message := "Invalid enum value: " + value + ". Possible values: " + strings.Join(possible, ", ")
		t.Error(NewMockupCritical(t, m, path, propertyName, message))
	}
}

func (m *Mockup) isExcludedFromTypeCheck(path string) bool {
	for _, exclude := range excludeFromTypeCheckStrings {
		if strings.Contains(path, exclude) {
			return true
		}
	}
	return false
}

//nolint:gochecknoglobals
var (
	excludeFromTypeCheckStrings = []string{
		"/redfish/v1/explorer_config.json",
		"/redfish/v1/odata",
		"/redfish/v1/JsonSchemas/",
		"/redfish/v1/TaskService/TaskMonitors/",
		"-request-example.json",
		"-response-example.json",
		"Contoso",
		"$ref",
		"Schema.json",
	}
)
