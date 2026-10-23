/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup

import (
	"fmt"
	"math"
	"net/netip"
	"net/url"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/pboyd04/gocsdl/pkg/csdl"
)

const measuresUnit = "Measures.Unit"

const (
	odataPermissions = "OData.Permissions"
	odataDescription = "OData.Description"
	odataLongDesc    = "OData.LongDescription"
	redfishRevisions = "Redfish.Revisions"
	redfishExcerpt   = "Redfish.Excerpt"
)

//nolint:gochecknoglobals
var (
	pathsAllowedNoID = []string{
		"/redfish/v1/Registries/*",
		"/redfish/v1/TaskService/TaskMonitors/*",
		"/redfish/v1/AttributeRegistry-v1-example.json",
		"/redfish/v1/MessageRegistry-v1-example.json",
	}
	etagRegex              = regexp.MustCompile(`([wW]/)?"([^"]|\\")*"`)
	singleDigitOffsetRegex = regexp.MustCompile(`([+-])(\d):(\d{2})$`)
)

func (m *Mockup) ContentMatchesType(t *testsuite.Testing) {
	for path, file := range m.files {
		if file.Type == nil {
			// Skipping... Should have already put an error up or this file is explicitly not handled.
			continue
		}
		file.ContentMatchesType(t, path, m)
	}
}

func (f *File) ContentMatchesType(
	t *testsuite.Testing, path string, m *Mockup,
) {
	if strings.HasSuffix(path, "Capabilities") {
		// Capabilities structs are different...
		return
	}
	f.ODataIDMatchesPath(t, path, m)
	f.ODataContextSane(t, path, m)
	f.ODataEtagSane(t, path, m)
	f.DoTypeContentCheck(t, path, m)
}

func (f *File) ODataIDMatchesPath(
	t *testsuite.Testing, path string, m *Mockup,
) {
	id, ok := f.Content["@odata.id"].(string)
	if !ok {
		f.handleMissingODataID(t, path, m)
		return
	}
	if !m.InternallyConsistent {
		// This mockup is different and isn't internally consistent (i.e. not really a mockup)
		return
	}
	if strings.TrimSuffix(id, "/") != strings.TrimSuffix(path, "/") {
		f.handleMismatchedODataID(t, path, id, m)
	}
}

func (f *File) handleMissingODataID(t *testsuite.Testing, path string, m *Mockup) {
	for _, allowedPath := range pathsAllowedNoID {
		if matched, _ := filepath.Match(allowedPath, path); matched {
			return
		}
	}
	if isAutoFix(t) {
		f.applyAutoFixODataID(t, m, path, "Missing @odata.id")
		return
	}
	t.Error(NewMockupCritical(t, m, path, "@odata.id", "Missing @odata.id from mockup"))
}

func (f *File) handleMismatchedODataID(
	t *testsuite.Testing, path string, id string, m *Mockup,
) {
	if isAutoFix(t) {
		f.applyAutoFixODataID(t, m, path,
			fmt.Sprintf("Expected %s, got %s", path, id))
		return
	}
	t.Error(NewMockupCritical(t, m, path, "@odata.id",
		fmt.Sprintf("Expected %s, got %s", path, id)))
}

func isAutoFix(t *testsuite.Testing) bool {
	return t.Case != nil && t.Case.Suite != nil && t.Case.Suite.AutoFix
}

func (f *File) applyAutoFixODataID(
	t *testsuite.Testing, m *Mockup, path string, errPrefix string,
) {
	f.Content["@odata.id"] = path
	if err := f.Save(m, path); err != nil {
		t.Error(NewMockupCritical(t, m, path, "@odata.id",
			fmt.Sprintf("%s and failed to auto-fix: %v", errPrefix, err)))
	}
}

func (f *File) ODataContextSane(
	t *testsuite.Testing, path string, m *Mockup,
) {
	context, ok := f.Content["@odata.context"].(string)
	if !ok {
		// No @odata.context is fine
		return
	}
	if path == "/redfish/v1/odata" {
		if context != "/redfish/v1/$metadata" {
			t.Error(NewMockupCritical(t, m, path,
				"@odata.context",
				"Expected /redfish/v1/$metadata, got "+context))
		}
	}
	unversionedName, _, _ := strings.Cut(f.Type.Namespace, ".")
	unversionedName += "." + f.Type.Name
	expected := "/redfish/v1/$metadata#" + unversionedName
	if context != expected {
		t.Error(NewMockupWarning(t, m, path,
			"@odata.context",
			fmt.Sprintf("Expected %s, got %s",
				expected, context)))
	}
}

func (f *File) ODataEtagSane(
	t *testsuite.Testing, path string, m *Mockup,
) {
	etag, ok := f.Content["@odata.etag"]
	if !ok {
		// No @odata.etag is fine
		return
	}
	etagStr, ok := etag.(string)
	if !ok {
		t.Error(NewMockupWarning(t, m, path,
			"@odata.etag",
			"Expected string, got "+fmt.Sprintf("%T", etag)))
		return
	}
	if !etagRegex.MatchString(etagStr) {
		t.Error(NewMockupWarning(t, m, path,
			"@odata.etag",
			"Invalid @odata.etag: "+etagStr))
	}
}

func (f *File) DoTypeContentCheck(
	t *testsuite.Testing, path string, m *Mockup,
) {
	for k, v := range f.Content {
		switch {
		case k == "Members@odata.count":
			f.MembersODataCountCheck(t, path, m)
			continue
		case strings.Contains(k, "@odata.nextLink"):
			f.ODataNextLinkCheck(t, path, m, k)
			continue
		case strings.HasPrefix(k, "@odata."):
			// Already validated by the dedicated OData checks above.
			continue
		case strings.Contains(k, "@Redfish."):
			// Annotation lookup is not yet implemented.
			continue
		}
		csdlProp := GetPropertyFromCSDLType(k, f.Type, m.types)
		if csdlProp == nil {
			t.Error(NewMockupWarning(t, m, path, k,
				fmt.Sprintf("Unknown data %s %v for type %s",
					k, v, f.Type.Name)))
			continue
		}
		if csdlProp.Navigation {
			f.NavLinkIsSane(t, path, m, k, csdlProp)
			continue
		}
		f.PropValueIsSane(t, path, m, k, v, csdlProp)
	}
}

func (f *File) MembersODataCountCheck(
	t *testsuite.Testing, path string, m *Mockup,
) {
	// Make sure the type is a collection
	if !strings.HasSuffix(f.Type.Name, "Collection") {
		t.Error(NewMockupWarning(t, m, path,
			"Members@odata.count",
			fmt.Sprintf(
				"Members@odata.count is not allowed "+
					"for non-Collection type %s",
				f.Type.Name)))
		return
	}
	count, ok := f.Content["Members@odata.count"].(float64)
	memArray, memIsArray := f.Content["Members"].([]any)
	if !ok {
		if isAutoFix(t) {
			f.applyAutoFixMembersODataCount(t, path, m, memArray,
				"Members@odata.count must be a number and failed to auto-fix: %v")
			return
		}
		t.Error(NewMockupWarning(t, m, path,
			"Members@odata.count",
			fmt.Sprintf(
				"Members@odata.count must be a number, got %T",
				f.Content["Members@odata.count"])))
		return
	}
	if memIsArray && int(count) != len(memArray) {
		_, hasNextLink := f.Content["@odata.nextLink"]
		_, hasMembersNextLink := f.Content["Members@odata.nextLink"]
		if hasNextLink || hasMembersNextLink {
			return
		}
		if isAutoFix(t) {
			f.applyAutoFixMembersODataCount(t, path, m, memArray,
				"Members@odata.count does not match length of Members array and failed to auto-fix: %v")
			return
		}
		t.Error(NewMockupWarning(t, m, path,
			"Members@odata.count",
			fmt.Sprintf(
				"Members@odata.count %d does not "+
					"match length of Members "+
					"array %d",
				int(count), len(memArray))))
	}
}

func (f *File) applyAutoFixMembersODataCount(
	t *testsuite.Testing, path string, m *Mockup, memArray []any,
	errFormat string,
) {
	f.Content["Members@odata.count"] = float64(len(memArray))
	if err := f.Save(m, path); err != nil {
		t.Error(NewMockupWarning(t, m, path,
			"Members@odata.count",
			fmt.Sprintf(errFormat, err)))
	}
}

func (f *File) ODataNextLinkCheck(
	t *testsuite.Testing, path string,
	m *Mockup, k string,
) {
	// Make sure the type is a collection
	if !strings.HasSuffix(f.Type.Name, "Collection") {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"@odata.nextLink is not allowed "+
					"for non-Collection type %s",
				f.Type.Name)))
		return
	}
	strVal, ok := f.Content[k].(string)
	if !ok {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"@odata.nextLink must be a string, got %T",
				f.Content[k])))
		return
	}
	uri, err := url.Parse(strVal)
	if err != nil {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"@odata.nextLink must be URI. invalid URL: %s",
				err)))
		return
	}
	if strings.HasSuffix(uri.Path, "$ref") {
		return
	}
	if uri.Path != path {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"@odata.nextLink must point to the same "+
					"path as the current resource. "+
					"expected %s, got %s",
				path, uri.Path)))
		return
	}
	if uri.RawQuery == "" {
		t.Error(NewMockupWarning(t, m, path, k,
			"@odata.nextLink must include query parameters"))
		return
	}
}

func (f *File) NavLinkIsSane(
	t *testsuite.Testing, path string, m *Mockup,
	k string, csdlProp *csdl.PropType,
) {
	if strings.HasPrefix(csdlProp.Type, "Collection(") {
		f.NavLinkCollectionIsSane(t, path, m, k, csdlProp)
		return
	}
	f.NavLinkSingletonIsSane(
		t, path, m, f.Content[k], k, csdlProp)
}

//nolint:cyclop,funlen
func (f *File) NavLinkSingletonIsSane(
	t *testsuite.Testing, path string, m *Mockup,
	v any, jsonPath string, csdlProp *csdl.PropType,
) {
	// First is the navigation link an @odata.id
	navLink, ok := v.(map[string]any)
	if !ok {
		t.Error(NewMockupWarning(t, m, path, "",
			fmt.Sprintf(
				"Navigation link must be a JSON object, "+
					"got %T %s",
				v, csdlProp.Type)))
		return
	}
	if csdlProp.Excerpt {
		// Should verify that the needed bits are there...
		return
	}
	odataIDRaw, ok := navLink["@odata.id"]
	if !ok {
		t.Error(NewMockupWarning(t, m, path, jsonPath,
			"@odata.id must be present"))
		return
	}
	odataID, ok := odataIDRaw.(string)
	if !ok {
		t.Error(NewMockupWarning(t, m, path,
			jsonPath+"/@odata.id",
			"@odata.id must be a string"))
		return
	}
	if !m.InternallyConsistent {
		// We've done all we can do for this mockup...
		return
	}
	if strings.HasPrefix(odataID, "https://") ||
		strings.HasPrefix(odataID, "http://") {
		// This is an external link, we can't verify it...
		return
	}
	link, fragment, _ := strings.Cut(odataID, "#")
	link = strings.TrimSuffix(link, "/")
	otherFile, ok := m.files[link]
	if !ok {
		t.Error(NewMockupWarning(t, m, path,
			jsonPath+"/@odata.id",
			fmt.Sprintf(
				"Navigation link %s does not exist",
				odataID)))
		return
	}
	if otherFile.Type == nil {
		// This isn't a resource link... this is probably OK...
		return
	}
	csdlPropType := strings.TrimPrefix(
		csdlProp.Type, "Collection(")
	csdlPropType = strings.TrimSuffix(csdlPropType, ")")
	if csdlPropType == "Resource.Item" ||
		csdlPropType == "Resource.ItemOrCollection" {
		// This matches to anything...
		return
	}
	if fragment != "" {
		// This points to a child...
		return
	}
	if csdlPropType == "Resource.Resource" {
		// This matches everything still left...
		return
	}
	otherFileType, _, _ := strings.Cut(
		otherFile.Type.Namespace, ".")
	otherFileType = otherFileType + "." + otherFile.Type.Name
	if csdlPropType != otherFileType {
		t.Error(NewMockupWarning(t, m, path,
			jsonPath+"/@odata.id",
			fmt.Sprintf(
				"Navigation link type %s does not match "+
					"expected type %s, got type %s",
				jsonPath, csdlPropType, otherFileType)))
		return
	}
}

func (f *File) NavLinkCollectionIsSane(
	t *testsuite.Testing, path string, m *Mockup,
	k string, csdlProp *csdl.PropType,
) {
	// First is the navigation link an @odata.id
	col, ok := f.Content[k].([]any)
	if !ok {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"Navigation link must be a JSON array, "+
					"got %T %s",
				f.Content[k], csdlProp.Type)))
		return
	}
	for i, item := range col {
		f.NavLinkSingletonIsSane(t, path, m, item,
			k+"["+strconv.Itoa(i)+"]", csdlProp)
	}
}

//nolint:cyclop,funlen
func (f *File) PropValueIsSane(
	t *testsuite.Testing, path string, m *Mockup,
	k string, v any, csdlProp *csdl.PropType,
) {
	if v == nil {
		return
	}
	switch csdlProp.Type {
	case "Edm.PrimitiveType":
		PrimitiveTypeValidation(t, path, m, k, v, csdlProp)
	case "Edm.Boolean":
		_, ok := v.(bool)
		if !ok {
			t.Error(NewMockupWarning(t, m, path, k,
				fmt.Sprintf(
					"Property %s must be a boolean, got %T",
					k, v)))
			return
		}
	case "Edm.DateTimeOffset":
		DateTimeOffsetValidation(f, t, path, m, k, v, csdlProp)
	case "Edm.Decimal":
		DecimalValidation(t, path, m, k, v, csdlProp)
	case "Edm.Duration":
		vStr, ok := v.(string)
		if !ok {
			t.Error(NewMockupWarning(t, m, path, k,
				fmt.Sprintf(
					"Property %s must be a string, got %T",
					k, v)))
			return
		}
		_, err := NewEdmDuration(vStr)
		if err != nil {
			t.Error(NewMockupWarning(t, m, path, k,
				fmt.Sprintf(
					"Property %s must be a valid duration, "+
						"P[<d>D][T[<h>H][<m>M][<s>[.<f>]S]]"+
						" got %s",
					k, vStr)))
			return
		}
	case "Edm.Guid", "Resource.UUID":
		vStr, ok := v.(string)
		if !ok {
			t.Error(NewMockupWarning(t, m, path, k,
				fmt.Sprintf(
					"Property %s must be a string, got %T",
					k, v)))
			return
		}
		_, err := NewEdmGUID(vStr)
		if err != nil {
			t.Error(NewMockupWarning(t, m, path, k,
				fmt.Sprintf(
					"Property %s must be a valid GUID, "+
						"got %s",
					k, vStr)))
			return
		}
	case "Edm.Int64":
		IntegerValidation(t, path, m, k, v, csdlProp)
	case "Edm.String", "Resource.Id", "Resource.Name",
		"Resource.Description":
		StringValidation(t, path, m, k, v, csdlProp)
	case "Collection(Edm.Decimal)":
		FloatArrayValidation(t, path, m, k, v, csdlProp)
	case "Collection(Edm.Int64)":
		IntArrayValidation(t, path, m, k, v, csdlProp)
	case "Collection(Edm.String)":
		StringArrayValidation(t, path, m, k, v, csdlProp)
	case "Capacity.Capacity":
		// Special case for SNIA owned attribute just to make
		// Redfish pass without having to parse SNIA schemas.
		// Proper validation for Capacity.Capacity is not yet
		// implemented.
		_ = v
	default:
		typeStr := csdlProp.Type
		typeStr = strings.TrimPrefix(typeStr, "Collection(")
		typeStr = strings.TrimSuffix(typeStr, ")")
		csdlTypeForProp := m.types[typeStr]
		if csdlTypeForProp != nil {
			f.DoTypeContentCheckForProperty(
				t, path, m, k, csdlTypeForProp, v)
			return
		}
		// Check for TypeDefinitions with the CSDL searcher
		if m.searcher != nil {
			searchable := m.searcher.GetByTypeName(typeStr)
			if searchable != nil {
				// TypeDefinition found
				return
			}
		}
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"Property %s has unknown type %s",
				k, csdlProp.Type)))
	}
}

func PrimitiveTypeValidation(
	t *testsuite.Testing, path string, m *Mockup,
	k string, v any, csdlProp *csdl.PropType,
) {
	switch v.(type) {
	case bool, float64, string:
		// These are valid primitive types
	default:
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"Property %s must be a primitive type, "+
					"got %T",
				k, v)))
	}
}

func DecimalValidation(
	t *testsuite.Testing, path string, m *Mockup,
	k string, v any, csdlProp *csdl.PropType,
) {
	vFloat, ok := v.(float64)
	if !ok {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"Property %s must be a decimal, got %T",
				k, v)))
		return
	}
	if len(csdlProp.Annotations) > 0 {
		for _, ann := range csdlProp.Annotations {
			switch ann.Term {
			case odataPermissions,
				odataDescription,
				odataLongDesc,
				measuresUnit,
				redfishRevisions,
				redfishExcerpt:
				continue
			case "Validation.Maximum":
				maxVal := ann.Int
				if vFloat > float64(maxVal) {
					t.Error(NewMockupWarning(t, m, path, k,
						fmt.Sprintf(
							"Property %s must be less "+
								"than or equal to %f, "+
								"got %f",
							k, float64(maxVal), vFloat)))
				}
			case "Validation.Minimum":
				minVal := ann.Int
				if vFloat < float64(minVal) {
					t.Error(NewMockupWarning(t, m, path, k,
						fmt.Sprintf(
							"Property %s must be greater "+
								"than or equal to %f, "+
								"got %f",
							k, float64(minVal), vFloat)))
				}
			default:
				// fmt.Printf("Annotation = %#v\n", ann)
			}
		}
	}
}

//nolint:cyclop
func IntegerValidation(
	t *testsuite.Testing, path string, m *Mockup,
	k string, v any, csdlProp *csdl.PropType,
) {
	vFloat, ok := v.(float64)
	if !ok {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"Property %s must be an number, got %T",
				k, v)))
		return
	}
	// Check if it's actually an integer
	if vFloat != math.Trunc(vFloat) {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"Property %s must be an integer, got %f",
				k, vFloat)))
		return
	}
	if len(csdlProp.Annotations) > 0 {
		for _, ann := range csdlProp.Annotations {
			switch ann.Term {
			case odataPermissions,
				odataDescription,
				odataLongDesc,
				measuresUnit,
				redfishRevisions,
				redfishExcerpt:
				continue
			case "Validation.Maximum":
				maxVal := ann.Int
				if vFloat > float64(maxVal) {
					t.Error(NewMockupWarning(t, m, path, k,
						fmt.Sprintf(
							"Property %s must be less "+
								"than or equal to %f, "+
								"got %f",
							k, float64(maxVal), vFloat)))
				}
			case "Validation.Minimum":
				minVal := ann.Int
				if vFloat < float64(minVal) {
					t.Error(NewMockupWarning(t, m, path, k,
						fmt.Sprintf(
							"Property %s must be greater "+
								"than or equal to %f, "+
								"got %f",
							k, float64(minVal), vFloat)))
				}
			default:
				// fmt.Printf("Annotation = %#v\n", ann)
			}
		}
	}
}

//nolint:cyclop,funlen,gocognit,nestif // Validation cases mirror the supported string annotations.
func StringValidation(
	t *testsuite.Testing, path string, m *Mockup,
	k string, v any, csdlProp *csdl.PropType,
) {
	vStr, ok := v.(string)
	if !ok {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"Property %s must be a string, got %T",
				k, v)))
		return
	}
	if len(csdlProp.Annotations) > 0 {
		for _, ann := range csdlProp.Annotations {
			switch ann.Term {
			case odataPermissions,
				odataDescription,
				odataLongDesc,
				measuresUnit,
				redfishRevisions,
				redfishExcerpt,
				"Redfish.Required",
				"Redfish.RequiredOnCreate":
				continue
			case "Validation.Pattern":
				regex := regexp.MustCompile(ann.String)
				if !regex.MatchString(vStr) {
					t.Error(NewMockupWarning(t, m, path, k,
						fmt.Sprintf(
							"Property %s must match "+
								"pattern `%s`, got %s",
							k, ann.String, vStr)))
				}
			case "Redfish.IPv6Format":
				// This allows either an address or a mask...
				// Check for mask first
				if strings.Contains(vStr, "/") {
					prefix, err := netip.ParsePrefix(vStr)
					if err != nil {
						t.Error(NewMockupWarning(
							t, m, path, k,
							fmt.Sprintf(
								"Property %s must be a "+
									"valid IPv6 address "+
									"or mask, got %s",
								k, vStr)))
					}
					if !prefix.Addr().Is6() {
						t.Error(NewMockupWarning(
							t, m, path, k,
							fmt.Sprintf(
								"Property %s must be a "+
									"valid IPv6 address "+
									"or mask, got %s",
								k, vStr)))
					}
					continue
				}
				addr, err := netip.ParseAddr(vStr)
				if err != nil {
					t.Error(NewMockupWarning(
						t, m, path, k,
						fmt.Sprintf(
							"Property %s must be a "+
								"valid IPv6 address, "+
								"got %s",
							k, vStr)))
				}
				if !addr.Is6() {
					t.Error(NewMockupWarning(
						t, m, path, k,
						fmt.Sprintf(
							"Property %s must be a "+
								"valid IPv6 address, "+
								"got %s",
							k, vStr)))
				}
			case "OData.IsURL":
				// This is a URL, so we should check if it's valid
				_, err := url.Parse(vStr)
				if err != nil {
					t.Error(NewMockupWarning(
						t, m, path, k,
						fmt.Sprintf(
							"Property %s must be a "+
								"valid URL, got %s",
							k, vStr)))
				}
			default:
				// fmt.Printf("Annotation = %#v\n", ann)
			}
		}
	}
}

func DateTimeOffsetValidation(
	f *File, t *testsuite.Testing, path string, m *Mockup,
	k string, v any, csdlProp *csdl.PropType,
) {
	vStr, ok := v.(string)
	if !ok {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"Property %s must be a string, got %T",
				k, v)))
		return
	}
	_, err := NewEdmDateTimeOffset(vStr)
	if err != nil && !applyDateTimeAutoFix(f, t, path, m, k, vStr, err) {
		t.Error(NewMockupWarning(t, m, path, k, dateTimeOffsetErrorMessage(k, vStr, err)))
	}
}

func dateTimeOffsetErrorMessage(k, vStr string, err error) string {
	return fmt.Sprintf(
		"Property %s must be a valid datetime in "+
			"the format YYYY-MM-DDTHH:MM:SS"+
			"[.mmm][Z|(+/-)HH:MM], got %q: %v",
		k, vStr, err)
}

// applyDateTimeAutoFix attempts to re-parse a malformed DateTimeOffset value
// using a number of known layouts and, if successful, overwrites the content
// value with the canonical RFC3339 form.  It returns true when the error has
// been handled (fixed or logged).
func applyDateTimeAutoFix(f *File, t *testsuite.Testing, path string, m *Mockup, k, vStr string, err error) bool {
	if f == nil || !isAutoFix(t) {
		return false
	}
	parsed := tryParseKnownTimeFormats(vStr)
	if parsed == nil {
		return false
	}
	if !SetValueAtPath(f.Content, k, parsed.Format(time.RFC3339)) {
		return false
	}
	if saveErr := f.Save(m, path); saveErr == nil {
		return true
	}
	t.Error(NewMockupWarning(t, m, path, k, dateTimeOffsetErrorMessage(k, vStr, err)))
	return true
}

// SetValueAtPath sets a value in a nested map/slice structure at a JSON-path-style
// key (e.g. "Conditions[0].Timestamp").  Returns false if the path cannot be
// navigated (e.g. missing intermediate keys or invalid array indices).
func SetValueAtPath(content map[string]any, path string, value any) bool {
	parts := splitPath(path)
	return setValueAtPathParts(content, parts, value)
}

//nolint:cyclop,nestif // Splitting would increase complexity elsewhere
func setValueAtPathParts(content map[string]any, parts []string, value any) bool {
	current := any(content)
	for i, part := range parts {
		isLast := i == len(parts)-1
		key, idx, hasIndex := parseKeyWithIndex(part)
		if v, ok := current.(map[string]any); ok {
			if !hasIndex {
				if isLast {
					v[key] = value
					return true
				}
				current = v[key]
				continue
			}
			next, ok := v[key].([]any)
			if !ok || !isValidArrayIndex(next, idx) {
				return false
			}
			if isLast {
				next[idx] = value
				return true
			}
			current = next[idx]
			continue
		}
		if v, ok := current.([]any); ok {
			if !isValidArrayIndex(v, idx) {
				return false
			}
			if isLast {
				v[idx] = value
				return true
			}
			current = v[idx]
			continue
		}
		return false
	}
	return false
}

func isValidArrayIndex(arr []any, idx int) bool {
	return idx >= 0 && idx < len(arr)
}

// splitPath splits a JSON-path-style string into parts, handling keys that
// contain dots (e.g. "@odata.id") by not splitting on dots that follow an @
// or are within array index brackets.
func splitPath(path string) []string {
	// First, split on dots outside brackets
	var parts []string
	var current strings.Builder
	inBrackets := false
	for _, r := range path {
		switch {
		case r == '[':
			inBrackets = true
			current.WriteRune(r)
		case r == ']':
			inBrackets = false
			current.WriteRune(r)
		case r == '.' && !inBrackets:
			if current.Len() > 0 {
				parts = append(parts, current.String())
				current.Reset()
			}
		default:
			current.WriteRune(r)
		}
	}
	if current.Len() > 0 {
		parts = append(parts, current.String())
	}
	// Now recombine parts that start with @ with the following part
	// (e.g. ["@odata", "id"] becomes ["@odata.id"])
	return recombineAtPrefixedParts(parts)
}

func recombineAtPrefixedParts(parts []string) []string {
	var result []string
	for i := 0; i < len(parts); i++ {
		if strings.HasPrefix(parts[i], "@") && i+1 < len(parts) {
			// Combine with next part
			result = append(result, parts[i]+"."+parts[i+1])
			i++ // skip next part
		} else {
			result = append(result, parts[i])
		}
	}
	return result
}

// parseKeyWithIndex parses a key like "Conditions[0]" into ("Conditions", 0, true).
// If no index is present, returns (key, 0, false).
func parseKeyWithIndex(key string) (string, int, bool) {
	openIdx := strings.Index(key, "[")
	closeIdx := strings.Index(key, "]")
	if openIdx == -1 || closeIdx == -1 || closeIdx != len(key)-1 {
		return key, 0, false
	}
	idxStr := key[openIdx+1 : closeIdx]
	idx, err := strconv.Atoi(idxStr)
	if err != nil {
		return key, 0, false
	}
	return key[:openIdx], idx, true
}

// tryParseKnownTimeFormats attempts to parse a date/time string with a
// collection of standard Go time layouts.  It returns the parsed time, or nil
// if none of the layouts match.  Leading and trailing whitespace is stripped
// before any parsing is attempted so that values like " 2024-01-02T03:04:05Z "
// are handled correctly.
func tryParseKnownTimeFormats(vStr string) *time.Time {
	normalized := normalizeDateTimeOffset(strings.TrimSpace(vStr))
	if e, err := NewEdmDateTimeOffset(normalized); err == nil {
		t := time.Time(e)
		return &t
	}
	layouts := []string{
		time.RFC3339,
		time.RFC3339Nano,
		time.RFC1123,
		time.RFC1123Z,
		time.RFC822,
		time.RFC822Z,
		time.RFC850,
		time.ANSIC,
		time.UnixDate,
		time.RubyDate,
		time.DateTime,
	}
	for _, layout := range layouts {
		if parsed, err := time.Parse(layout, normalized); err == nil {
			return &parsed
		}
	}
	return nil
}

// normalizeDateTimeOffset pads the hour in a trailing single-digit time-zone
// offset (e.g. "+6:00" becomes "+06:00") so that Go's time layouts can parse
// it.  The input is returned unchanged if no single-digit offset is found.
func normalizeDateTimeOffset(s string) string {
	return singleDigitOffsetRegex.ReplaceAllString(s, "${1}0$2:$3")
}

func IntArrayValidation(
	t *testsuite.Testing, path string, m *Mockup,
	k string, v any, csdlProp *csdl.PropType,
) {
	vArr, ok := v.([]any)
	if !ok {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"Property %s must be an array, got %T",
				k, v)))
		return
	}
	for i, item := range vArr {
		idx := "[" + strconv.Itoa(i) + "]"
		vFloat, ok := item.(float64)
		if !ok {
			t.Error(NewMockupWarning(t, m, path, k+idx,
				fmt.Sprintf(
					"Property %s[%d] must be a number, "+
						"got %T",
					k, i, item)))
			return
		}
		// Check if it's actually an integer
		if vFloat != math.Trunc(vFloat) {
			t.Error(NewMockupWarning(t, m, path, k+idx,
				fmt.Sprintf(
					"Property %s[%d] must be an integer, "+
						"got %f",
					k, i, vFloat)))
			return
		}
		// Float validation is not yet implemented.
		_ = vFloat
	}
}

func FloatArrayValidation(
	t *testsuite.Testing, path string, m *Mockup,
	k string, v any, csdlProp *csdl.PropType,
) {
	vArr, ok := v.([]any)
	if !ok {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"Property %s must be an array, got %T",
				k, v)))
		return
	}
	for i, item := range vArr {
		idx := "[" + strconv.Itoa(i) + "]"
		vFloat, ok := item.(float64)
		if !ok {
			t.Error(NewMockupWarning(t, m, path, k+idx,
				fmt.Sprintf(
					"Property %s[%d] must be a number, "+
						"got %T",
					k, i, item)))
			return
		}
		// Float validation is not yet implemented.
		_ = vFloat
	}
}

func StringArrayValidation(
	t *testsuite.Testing, path string, m *Mockup,
	k string, v any, csdlProp *csdl.PropType,
) {
	vArr, ok := v.([]any)
	if !ok {
		t.Error(NewMockupWarning(t, m, path, k,
			fmt.Sprintf(
				"Property %s must be an array, got %T",
				k, v)))
		return
	}
	for i, item := range vArr {
		if item == nil {
			continue // Yes this is valid...
		}
		idx := "[" + strconv.Itoa(i) + "]"
		vStr, ok := item.(string)
		if !ok {
			t.Error(NewMockupWarning(t, m, path, k+idx,
				fmt.Sprintf(
					"Property %s[%d] must be a string, "+
						"got %T",
					k, i, item)))
			return
		}
		// String validation is not yet implemented.
		_ = vStr
	}
}

func GetPropertyFromCSDLType(
	propertyName string, csdlType *csdl.Type,
	allTypes map[string]*csdl.Type,
) *csdl.PropType {
	prop, ok := csdlType.Properties[propertyName]
	if ok {
		return &prop
	}
	if csdlType.BaseType != "" {
		baseType, ok := allTypes[csdlType.BaseType]
		if ok {
			return GetPropertyFromCSDLType(
				propertyName, baseType, allTypes)
		}
	}
	return nil
}

// DescendantIndex maps a type's full name (Namespace.Name) to
// its direct children. Build once with BuildDescendantIndex and
// pass to GetPropertyFromCSDLTypeOrDescendents to avoid O(n)
// scans of the type map on every call.
type DescendantIndex map[string][]*csdl.Type

// BuildDescendantIndex creates an index of
// parent type -> direct child types.
func BuildDescendantIndex(
	allTypes map[string]*csdl.Type,
) DescendantIndex {
	// Most types have no children, so sizing this map for every type wastes
	// substantially more memory than allowing it to grow for base types only.
	idx := make(DescendantIndex)
	for _, t := range allTypes {
		if t.BaseType != "" {
			idx[t.BaseType] = append(idx[t.BaseType], t)
		}
	}
	return idx
}

// Redfish allows us to also go forward in time to find
// properties in descendents of the type.
func GetPropertyFromCSDLTypeOrDescendents(
	propertyName string, csdlType *csdl.Type,
	allTypes map[string]*csdl.Type, idx DescendantIndex,
) *csdl.PropType {
	prop := GetPropertyFromCSDLType(
		propertyName, csdlType, allTypes)
	if prop != nil {
		return prop
	}
	// Look through direct children from the pre-built index
	fullName := csdlType.Namespace + "." + csdlType.Name
	for _, child := range idx[fullName] {
		prop := GetPropertyFromCSDLTypeOrDescendents(
			propertyName, child, allTypes, idx)
		if prop != nil {
			return prop
		}
	}
	return nil
}
