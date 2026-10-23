/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl

import (
	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src"
)

func NewCSDLError(
	csdlEntity csdl.Searchable, severity src.Severity, message string, searcher *csdl.Searcher,
) *src.XMLSourceError {
	fileName, path := searcher.GetPath(csdlEntity)
	return src.NewXMLSourceError(fileName, path, message, severity, nil)
}

func NewCSDLWarning(csdlEntity csdl.Searchable, message string, searcher *csdl.Searcher) *src.XMLSourceError {
	return NewCSDLError(csdlEntity, src.SeverityWarning, message, searcher)
}

func NewCSDLCritical(csdlEntity csdl.Searchable, message string, searcher *csdl.Searcher) *src.XMLSourceError {
	return NewCSDLError(csdlEntity, src.SeverityError, message, searcher)
}
