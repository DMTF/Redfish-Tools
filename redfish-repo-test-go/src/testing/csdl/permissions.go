/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"strings"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
)

func SchemasHavePermissions(t *testsuite.Testing, _ units.Units, _ *config.Config, searcher *csdl.Searcher) {
	schemas := searcher.GetSchemas("")
	for _, schema := range schemas {
		// Skip RedfishExtensions
		if strings.HasPrefix(schema.Namespace, "RedfishExtensions") {
			continue
		}
		CheckPermissionsInSchema(t, searcher, schema)
	}
}

//nolint:gocognit,cyclop
func CheckPermissionsInSchema(t *testsuite.Testing, searcher *csdl.Searcher, schema *csdl.Schema) {
	props := searcher.GetPropertiesUnder(schema)
	for _, prop := range props {
		found := false
		for _, annotation := range prop.Annotation {
			if annotation.Term == "OData.Permissions" {
				found = true
				break
			}
		}
		// Search for the type to see if it has permissions
		typeData, standardType, sameNamespace := TypeSearchHelper(searcher, prop.Type, schema.Namespace)
		if !sameNamespace {
			// Skip this, report it in the correct location only.
			continue
		}
		if typeData == nil && !standardType {
			t.Error(NewCSDLCritical(prop, `Type not found: `+prop.Type, searcher))
			continue
		}
		if typeData != nil {
			switch typeData.(type) {
			case *csdl.ComplexType:
				// Properties that reference ComplexTypes should not have permissions...
				if found {
					t.Error(NewCSDLWarning(prop,
						`Properties that reference ComplexTypes should not have permissions annotations`,
						searcher))
				}
				continue
			default:
				baseProps := searcher.GetPropertiesUnder(typeData)
				for _, baseProp := range baseProps {
					for _, annotation := range baseProp.Annotation {
						if annotation.Term == "OData.Permissions" {
							found = true
							break
						}
					}
				}
			}
		}
		if !found {
			t.Error(NewCSDLWarning(prop, `No permissions annotations`, searcher))
		}
	}
}

func TypeSearchHelper(searcher *csdl.Searcher, typeName string, namespace string) (csdl.Searchable, bool, bool) {
	if strings.HasPrefix(typeName, "Edm.") || strings.HasPrefix(typeName, "Collection(Edm.") {
		// Standard type!
		return nil, true, true
	}
	typeName = strings.TrimPrefix(typeName, "Collection(")
	typeName = strings.TrimSuffix(typeName, ")")
	if strings.HasPrefix(typeName, namespace) {
		return searcher.GetByTypeName(typeName), false, true
	}
	return searcher.GetByTypeName(typeName), false, false
}
