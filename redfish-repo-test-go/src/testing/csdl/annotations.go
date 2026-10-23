/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"sync"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
)

//nolint:gochecknoglobals
var validTerms = sync.Map{} // map[string]struct{}

//nolint:gochecknoinits
func init() {
	validTerms.Store("Capabilities.DeleteRestrictions", struct{}{})
	validTerms.Store("Capabilities.InsertRestrictions", struct{}{})
	validTerms.Store("Capabilities.UpdateRestrictions", struct{}{})
	validTerms.Store("Measures.Unit", struct{}{})
	validTerms.Store("OData.AdditionalProperties", struct{}{})
	validTerms.Store("OData.AutoExpand", struct{}{})
	validTerms.Store("OData.AutoExpandReferences", struct{}{})
	validTerms.Store("OData.Description", struct{}{})
	validTerms.Store("OData.IsURL", struct{}{})
	validTerms.Store("OData.LongDescription", struct{}{})
	validTerms.Store("OData.Permissions", struct{}{})
}

func AnnotationChecks(t *testsuite.Testing, _ units.Units, cfg *config.Config, searcher *csdl.Searcher) {
	annotations := searcher.GetAnnotations("")
	for _, annotation := range annotations {
		if !IsValidTerm(searcher, annotation.Term) {
			t.Error(NewCSDLCritical(annotation, `Unknown annotation term: "`+annotation.Term+`"`, searcher))
		}
	}
}

func IsValidTerm(searcher *csdl.Searcher, term string) bool {
	_, ok := validTerms.Load(term)
	if ok {
		return ok
	}
	base := searcher.GetByTypeName(term)
	if base != nil {
		validTerms.Store(term, struct{}{})
		return true
	}
	return ok
}

func AnnotationListHas(annotations []*csdl.Annotation, term string) bool {
	for _, annotation := range annotations {
		if annotation.Term == term {
			return true
		}
	}
	return false
}

func GetAnnotationFromList(nnotations []*csdl.Annotation, term string) *csdl.Annotation {
	for _, annotation := range nnotations {
		if annotation.Term == term {
			return annotation
		}
	}
	return nil
}
