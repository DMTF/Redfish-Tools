/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package utils

import (
	"fmt"
	"strconv"
	"strings"
)

type InvalidVersionError struct {
	Version string
	Err     error
}

func (e *InvalidVersionError) Error() string {
	return "Invalid version: " + e.Version
}

func (e *InvalidVersionError) Unwrap() error {
	return e.Err
}

type RedfishNamespaceVersion struct {
	Major  int
	Minor  int
	Errata int
}

func ParseVersionFromString(version string) (*RedfishNamespaceVersion, error) {
	if strings.Count(version, "_") != 2 {
		return nil, &InvalidVersionError{
			Version: version,
			Err:     nil,
		}
	}
	originalVersion := version
	version = strings.TrimPrefix(version, "v")
	part, rest, _ := strings.Cut(version, "_")
	major, err := strconv.Atoi(part)
	if err != nil {
		return nil, &InvalidVersionError{
			Version: originalVersion,
			Err:     err,
		}
	}
	part, rest, _ = strings.Cut(rest, "_")
	minor, err := strconv.Atoi(part)
	if err != nil {
		return nil, &InvalidVersionError{
			Version: originalVersion,
			Err:     err,
		}
	}
	rev, err := strconv.Atoi(rest)
	if err != nil {
		return nil, &InvalidVersionError{
			Version: originalVersion,
			Err:     err,
		}
	}
	return &RedfishNamespaceVersion{
		Major:  major,
		Minor:  minor,
		Errata: rev,
	}, nil
}

func (v *RedfishNamespaceVersion) Compare(v2 *RedfishNamespaceVersion) int {
	if v.Major != v2.Major {
		return v.Major - v2.Major
	}
	if v.Minor != v2.Minor {
		return v.Minor - v2.Minor
	}
	return v.Errata - v2.Errata
}

func (v *RedfishNamespaceVersion) IsUpByOneOrEqual(v2 *RedfishNamespaceVersion) bool {
	cmp := v.Compare(v2)
	return cmp == 1 || cmp == 0
}

func (v *RedfishNamespaceVersion) String() string {
	return fmt.Sprintf("v%d_%d_%d", v.Major, v.Minor, v.Errata)
}
