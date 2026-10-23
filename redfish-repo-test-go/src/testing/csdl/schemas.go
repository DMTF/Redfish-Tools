/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"fmt"
	"path/filepath"
	"slices"
	"strings"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
	"github.com/DMTF/redfishRepoTest/src/utils"
)

func SchemaTest(t *testsuite.Testing, _ units.Units, cfg *config.Config, searcher *csdl.Searcher) {
	schemas := searcher.GetSchemas("")
	for _, schema := range schemas {
		empty, isTrivial := getSchemaEmptyOrTrivial(schema)
		if empty && !slices.Contains(cfg.AllowLists.AllowedBareSchemas, filepath.Base(GetFileNameFromTest(t))) {
			t.Error(NewCSDLWarning(schema, `Schema must contain at least one non-annotation child`, searcher))
		}
		IsSchemaNamePlural(schema, t, cfg, searcher)
		SchemaVersionCheck(schema, t, cfg.PublishedVersions, searcher)
		SchemaActionsCheck(schema, t, searcher)
		SchemaAnnotationChecks(schema, t, cfg, searcher)
		if !strings.Contains(schema.Namespace, ".v1") {
			// Skip unversioned namespaces since they cannot be trivial namespaces
			continue
		}
		if isTrivial {
			if len(schema.Annotation) == 0 {
				t.Error(NewCSDLWarning(schema, `Trivial namespace schema should have at least one annotation`, searcher))
				continue
			}
			found := false
			for _, annotation := range schema.Annotation {
				if annotation.Term == "OData.Description" {
					found = true
					break
				}
			}
			if !found {
				t.Error(NewCSDLWarning(schema, `Trivial namespace schema should have an OData.Description annotation`, searcher))
			}
		}
	}
}

func IsSchemaNamePlural(schema *csdl.Schema, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher) {
	// We have the metrics pattern many places, allow for that explicitly
	if strings.Contains(schema.Namespace, "Metrics.v1") {
		return
	}
	if strings.Contains(schema.Namespace, "sCollection") || strings.Contains(schema.Namespace, "s.v1") {
		patterns := cfg.AllowLists.GetPluralSchemaPatterns()
		lead, _, _ := strings.Cut(schema.Namespace, ".v1")
		for _, pattern := range patterns {
			if pattern.MatchString(lead) {
				// Allow list has an exeption for this namespace, for example Bios or Chassis
				return
			}
		}
		t.Error(NewCSDLWarning(schema, `Schema name "`+schema.Namespace+`" is plural`, searcher))
	}
}

func SchemaVersionCheck(schema *csdl.Schema, t *testsuite.Testing,
	publishedVersions map[string]*utils.RedfishNamespaceVersion, searcher *csdl.Searcher) {
	if len(publishedVersions) == 0 {
		return
	}
	schemaName, version, ok := strings.Cut(schema.Namespace, ".")
	if !ok {
		// This is an unversioned namespace, skip it.
		return
	}
	rv, err := utils.ParseVersionFromString(version)
	if err == nil {
		latestVersion, published := publishedVersions[schemaName]
		if !published {
			// Not published yet! Skip it.
			return
		}
		cmp := rv.Compare(latestVersion)
		if cmp > 1 {
			//nolint:lll
			t.Error(NewCSDLWarning(schema, `Schema version "`+schema.Namespace+`" is not in the published versions list and is more than a single version ahead`, searcher))
		}
	}
}

func SchemaActionsCheck(schema *csdl.Schema, t *testsuite.Testing, searcher *csdl.Searcher) {
	if len(schema.Action) == 0 {
		return
	}
	for _, action := range schema.Action {
		short, long := ListHasDescriptions(action.Annotation)
		if !short {
			t.Error(NewCSDLCritical(action, `Action '`+action.Name+`' does not contain a Description`, searcher))
		}
		if !long {
			t.Error(NewCSDLCritical(action, `Action '`+action.Name+`' does not contain a LongDescription`, searcher))
		}
		for _, param := range action.Parameter {
			if strings.HasSuffix(param.Type, ".Actions") {
				// Skip the binding parameter
				continue
			}
			short, long := ListHasDescriptions(param.Annotation)
			if !short {
				t.Error(NewCSDLCritical(param,
					`Parameter '`+param.Name+`' of Action '`+action.Name+`' does not contain a Description`, searcher))
			}
			if !long {
				t.Error(NewCSDLCritical(param,
					`Parameter '`+param.Name+`' of Action '`+action.Name+`' does not contain a LongDescription`, searcher))
			}
		}
	}
}

func SchemaAnnotationChecks(schema *csdl.Schema, t *testsuite.Testing, cfg *config.Config, searcher *csdl.Searcher) {
	owningEntity := SchemaHasOwningEntity(schema)
	if owningEntity == "" {
		t.Error(NewCSDLWarning(schema,
			fmt.Sprintf(`Schema '%s' must contain an owning entity`, schema.Namespace), searcher))
	}
	// Only non-errata namespaces need the release term
	//nolint:nestif
	if strings.HasSuffix(schema.Namespace, "_0") {
		annotation := GetAnnotationFromList(schema.Annotation, "Redfish.Release")
		if annotation == nil {
			found := false
			patterns := cfg.AllowLists.GetNoReleaseTermSchemas()
			for _, pattern := range patterns {
				if pattern.MatchString(schema.Namespace) {
					found = true
					break
				}
			}
			if !found {
				t.Error(NewCSDLWarning(schema,
					fmt.Sprintf(`Schema '%s' must contain a Redfish.Release annotation`, schema.Namespace), searcher))
			}
		} else if !ReleaseTermValid(annotation.String) && owningEntity == "DMTF" {
			// Some of the SNIA models that Redfish uses had odd release terms, so we allow them to skip this check
			t.Error(NewCSDLWarning(schema,
				fmt.Sprintf(`Schema '%s' must contain a valid Redfish.Release annotation. '%s' contains non-allowed characters`,
					schema.Namespace, annotation.String), searcher))
		}
	}
}

func ReleaseTermValid(releaseTerm string) bool {
	for _, char := range releaseTerm {
		if char != '.' && (char < '0' || char > '9') {
			return false
		}
	}
	return true
}

func ListHasDescriptions(annotations []*csdl.Annotation) (bool, bool) {
	long := false
	short := false
	for _, annotation := range annotations {
		if annotation.Term == "OData.Description" {
			short = true
		}
		if annotation.Term == "OData.LongDescription" {
			long = true
		}
		if long && short {
			break
		}
	}
	return short, long
}

func SchemaHasOwningEntity(schema *csdl.Schema) string {
	for _, annotation := range schema.Annotation {
		if annotation.Term == "Redfish.OwningEntity" || annotation.Term == "RedfishExtensions.v1_0_0.OwningEntity" {
			return annotation.String
		}
	}
	return ""
}

func getSchemaEmptyOrTrivial(schema *csdl.Schema) (bool, bool) {
	count := 0
	isTrivial := true
	children := schema.GetChildren()
	for _, child := range children {
		if _, ok := child.(*csdl.Annotation); ok {
			continue
		}
		count++
		for _, grandChild := range child.GetChildren() {
			switch grandChild.(type) {
			case *csdl.Annotation:
				// Skip...
			default:
				isTrivial = false
			}
			if !isTrivial {
				break
			}
		}
	}
	if count > 1 {
		isTrivial = false
	}
	return count == 0, isTrivial
}
