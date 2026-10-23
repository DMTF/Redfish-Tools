/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"fmt"
	"maps"
	"slices"
	"strings"

	"github.com/DMTF/redfishRepoTest/src"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
	"github.com/pboyd04/gocsdl/pkg/csdl"
)

//nolint:gochecknoglobals
var (
	validReferencePrefixes = []string{
		"http://redfish.dmtf.org/schemas/v1/",                                              // DMTF
		"http://docs.oasis-open.org/odata/odata/v4.0/errata03/csd01/complete/vocabularies", // OASIS
		"http://redfish.dmtf.org/schemas/swordfish/v1/",                                    // SNIA Swordfish
	}
	validUnusedReferences = []string{
		"Org.OData.Core.V1",
		"Org.OData.Capabilities.V1",
		"Org.OData.Measures.V1",
		"RedfishExtensions.v1_0_0",
		"Validation.v1_0_0",
	}
)

func ReferenceCheck(t *testsuite.Testing, _ units.Units, _ *config.Config, searcher *csdl.Searcher) {
	files := searcher.GetFiles()
	fileNames := slices.Sorted(maps.Keys(files))
	for _, fileName := range fileNames {
		edmx := files[fileName]
		for _, ref := range edmx.Reference {
			IsReferenceURIValid(ref, t, fileName)
			IsReferenceUsed(ref, t, edmx, fileName, validUnusedReferences)
		}
	}
}

func ReferenceCheckPedantic(t *testsuite.Testing, _ units.Units, _ *config.Config, searcher *csdl.Searcher) {
	files := searcher.GetFiles()
	fileNames := slices.Sorted(maps.Keys(files))
	for _, fileName := range fileNames {
		edmx := files[fileName]
		for _, ref := range edmx.Reference {
			IsReferenceURIValid(ref, t, fileName)
			IsReferenceUsed(ref, t, edmx, fileName, nil)
		}
	}
}

func IsReferenceURIValid(ref *csdl.Reference, t *testsuite.Testing, fileName string) {
	if ref.Uri == "" {
		t.Error(src.NewXMLSourceError(fileName+".xml",
			"/edmx:Edmx/edmx:Reference[@Uri='']", `Reference URI is empty`, src.SeverityError, nil))
		return
	}

	for _, prefix := range validReferencePrefixes {
		if strings.HasPrefix(ref.Uri, prefix) {
			return
		}
	}
	t.Error(src.NewXMLSourceError(fileName+".xml",
		fmt.Sprintf("/edmx:Edmx/edmx:Reference[@Uri='%s']", ref.Uri),
		fmt.Sprintf("Reference URI %s is not valid", ref.Uri), src.SeverityWarning, nil))
}

func IsReferenceUsed(
	ref *csdl.Reference, t *testsuite.Testing, edmx *csdl.Edmx, fileName string, allowedUnused []string,
) {
	namespaces := make(map[string]struct{})
	for _, include := range ref.Include {
		namespaces[include.Namespace] = struct{}{}
	}
	// Look through each schema in the edmx and check if the reference is used
	for _, schema := range edmx.DataServices.Schema {
		children := schema.GetChildren()
		searchChildrenForReferences(children, namespaces)
	}
	// If there are any namespaces left, they are not used
	for namespace := range namespaces {
		if slices.Contains(allowedUnused, namespace) {
			continue
		}
		t.Error(src.NewXMLSourceError(fileName+".xml",
			fmt.Sprintf("/edmx:Edmx/edmx:Reference[@Uri='%s']", ref.Uri),
			fmt.Sprintf("Reference Namespace %q of %s is not used", namespace, ref.Uri), src.SeverityWarning, nil))
	}
}

func searchChildrenForReferences(children []csdl.Searchable, referenceMap map[string]struct{}) {
	for _, child := range children {
		namespace := GetNamespaceOfChild(child)
		delete(referenceMap, namespace)
		if len(referenceMap) > 0 {
			searchChildrenForReferences(child.GetChildren(), referenceMap)
		}
	}
}

//nolint:cyclop // basically just a big switch statement.
func GetNamespaceOfChild(child csdl.Searchable) string {
	var fullName string
	switch t := child.(type) {
	case *csdl.Action, *csdl.ReturnType:
		return ""
	case *csdl.Annotation:
		fullName = t.Term
	case *csdl.ComplexType:
		fullName = t.BaseType
	case *csdl.EntityType:
		fullName = t.BaseType
	case *csdl.EnumType:
		fullName = t.UnderlyingType
	case *csdl.Member, *csdl.EntityContainer:
		return ""
	case *csdl.Parameter:
		fullName = t.Type
	case *csdl.Property:
		fullName = t.Type
	case *csdl.NavigationProperty:
		fullName = t.Type
	case *csdl.Term:
		fullName = t.Type
	case *csdl.TypeDefinition:
		fullName = t.UnderlyingType
	default:
		panic("unknown type: " + fmt.Sprintf("%T", t))
	}
	if after, ok := strings.CutPrefix(fullName, "Collection("); ok {
		fullName = after
		fullName = strings.TrimSuffix(fullName, ")")
	}
	index := strings.LastIndex(fullName, ".")
	if index == -1 {
		return fullName
	}
	return fullName[:index]
}
