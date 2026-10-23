/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"slices"
	"strings"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
)

func URIChecks(t *testsuite.Testing, _ units.Units, cfg *config.Config, searcher *csdl.Searcher) {
	schemas := searcher.GetSchemas("")
	for _, schema := range schemas {
		if strings.Contains(schema.Namespace, ".v1") {
			// Skip versioned namespaces
			continue
		}
		annotations := searcher.GetAnnotaionsUnder(schema)
		uriAnnotation := GetAnnotationFromList(annotations, "Redfish.Uris")
		if uriAnnotation == nil {
			if !slices.Contains(cfg.AllowLists.NoURISchemas, schema.Namespace) {
				t.Error(NewCSDLWarning(schema, `Unversioned schemas must contain a Redfish.Uris annotation`, searcher))
			}
		}
	}
}
