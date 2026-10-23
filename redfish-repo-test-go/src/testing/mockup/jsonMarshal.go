/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup

import (
	"bytes"
	"encoding/json"
	"slices"
	"strings"
)

// priorityKeys are emitted in this fixed order after the leading @odata.*
// keys, giving the most human-relevant fields prominent placement.
//
//nolint:gochecknoglobals // immutable ordering configuration
var priorityKeys = []string{"Id", "Name", "Description", "Status"}

// MarshalJSON implements json.Marshaler.  Keys are emitted in this order:
//  1. @odata.* keys except @odata.id (alphabetically sorted)
//  2. Id, Name, Description, and Status in that fixed order
//  3. All other keys (alphabetically sorted)
//  4. @odata.id
//  5. @Redfish.* keys (alphabetically sorted)
//
// This keeps the most-important identity fields at the top, places the
// self-link (@odata.id) just before the copyright boilerplate, and matches
// Redfish mockup conventions.
func (f *File) MarshalJSON() ([]byte, error) {
	cat := categorizeContentKeys(f.Content)
	ordered := make([]string, 0, len(f.Content))
	ordered = append(ordered, cat.odata...)
	ordered = append(ordered, cat.priority...)
	ordered = append(ordered, cat.other...)
	if cat.odataIDPresent {
		ordered = append(ordered, "@odata.id")
	}
	ordered = append(ordered, cat.redfish...)
	return encodeOrderedContent(f.Content, ordered)
}

// categorizedKeys holds the five groups produced by categorizeContentKeys.
type categorizedKeys struct {
	odata          []string // @odata.* except @odata.id, alphabetically sorted
	priority       []string // Id/Name/Description/Status (present ones, in fixed order)
	other          []string // everything else, alphabetically sorted
	odataIDPresent bool
	redfish        []string // @Redfish.*, alphabetically sorted
}

func categorizeContentKeys(content map[string]any) categorizedKeys {
	prioritySet := make(map[string]struct{}, len(priorityKeys))
	for _, k := range priorityKeys {
		prioritySet[k] = struct{}{}
	}

	var cat categorizedKeys
	for k := range content {
		switch {
		case k == "@odata.id":
			cat.odataIDPresent = true
		case strings.HasPrefix(k, "@odata."):
			cat.odata = append(cat.odata, k)
		case strings.HasPrefix(k, "@Redfish."):
			cat.redfish = append(cat.redfish, k)
		default:
			if _, isPriority := prioritySet[k]; !isPriority {
				cat.other = append(cat.other, k)
			}
		}
	}
	slices.Sort(cat.odata)
	slices.Sort(cat.redfish)
	slices.SortFunc(cat.other, odataCountAwareLess)

	for _, k := range priorityKeys {
		if _, ok := content[k]; ok {
			cat.priority = append(cat.priority, k)
		}
	}
	return cat
}

// odataCountAwareLess sorts keys so that a "Foo@odata.count" key always
// immediately precedes its corresponding "Foo" key.  All other keys are
// ordered alphabetically by their base name.
func odataCountAwareLess(a, b string) int {
	const suffix = "@odata.count"
	aBase, aHasSuffix := strings.CutSuffix(a, suffix)
	bBase, bHasSuffix := strings.CutSuffix(b, suffix)
	if aBase != bBase {
		return strings.Compare(aBase, bBase)
	}
	// Same base: @odata.count variant sorts first.
	if aHasSuffix == bHasSuffix {
		return 0
	}
	if aHasSuffix {
		return -1
	}
	return 1
}

func encodeOrderedContent(content map[string]any, ordered []string) ([]byte, error) {
	var buf bytes.Buffer
	buf.WriteByte('{')
	for i, k := range ordered {
		if i > 0 {
			buf.WriteByte(',')
		}
		keyBytes, err := json.Marshal(k)
		if err != nil {
			return nil, err
		}
		buf.Write(keyBytes)
		buf.WriteByte(':')
		valBytes, err := json.Marshal(marshalValueForKey(k, content[k]))
		if err != nil {
			return nil, err
		}
		buf.Write(valBytes)
	}
	buf.WriteByte('}')
	return buf.Bytes(), nil
}

// marshalValueForKey returns the value to marshal for a given top-level key.
// For "Actions" it wraps the map so that each action object emits "target"
// as its first property.
func marshalValueForKey(key string, v any) any {
	if key != "Actions" {
		return v
	}
	actions, ok := v.(map[string]any)
	if !ok {
		return v
	}
	return orderedActions(actions)
}

// orderedActions is a map of action-name to action object.  It marshals with
// action names sorted alphabetically and each action object's "target" key
// emitted before all others.
type orderedActions map[string]any

func (oa orderedActions) MarshalJSON() ([]byte, error) {
	var buf bytes.Buffer
	buf.WriteByte('{')
	keys := make([]string, 0, len(oa))
	for k := range oa {
		keys = append(keys, k)
	}
	slices.Sort(keys)
	first := true
	writePair := func(k string, v any) error {
		if !first {
			buf.WriteByte(',')
		}
		first = false
		keyBytes, err := json.Marshal(k)
		if err != nil {
			return err
		}
		buf.Write(keyBytes)
		buf.WriteByte(':')
		valBytes, err := json.Marshal(v)
		if err != nil {
			return err
		}
		buf.Write(valBytes)
		return nil
	}
	for _, k := range keys {
		action, ok := oa[k].(map[string]any)
		if !ok {
			if err := writePair(k, oa[k]); err != nil {
				return nil, err
			}
			continue
		}
		if err := writePair(k, orderedAction(action)); err != nil {
			return nil, err
		}
	}
	buf.WriteByte('}')
	return buf.Bytes(), nil
}

// orderedAction marshals a Redfish action object with "target" first and the
// remaining keys sorted alphabetically.
type orderedAction map[string]any

func (oa orderedAction) MarshalJSON() ([]byte, error) {
	var buf bytes.Buffer
	buf.WriteByte('{')
	first := true
	writePair := func(k string, v any) error {
		if !first {
			buf.WriteByte(',')
		}
		first = false
		keyBytes, err := json.Marshal(k)
		if err != nil {
			return err
		}
		buf.Write(keyBytes)
		buf.WriteByte(':')
		valBytes, err := json.Marshal(v)
		if err != nil {
			return err
		}
		buf.Write(valBytes)
		return nil
	}
	if target, ok := oa["target"]; ok {
		if err := writePair("target", target); err != nil {
			return nil, err
		}
	}
	keys := make([]string, 0, len(oa))
	for k := range oa {
		if k != "target" {
			keys = append(keys, k)
		}
	}
	slices.Sort(keys)
	for _, k := range keys {
		if err := writePair(k, oa[k]); err != nil {
			return nil, err
		}
	}
	buf.WriteByte('}')
	return buf.Bytes(), nil
}
