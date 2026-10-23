/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package ucum

import (
	"encoding/json"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"

	"github.com/DMTF/redfishRepoTest/src/utils"
)

const (
	LocalCacheFileName = "units.json"
)

type UCUM struct {
	Prefixes map[string]string `json:"prefixes"`
	Units    map[string]string `json:"units"`
}

// Load will use a well known file to get the UCUM measurements.
func Load() (*UCUM, error) {
	return LoadFromFile(LocalCacheFileName)
}

// MakeLocalCache will create a local cache of the UCUM measurements.
func MakeLocalCache() error {
	return MakeCache(LocalCacheFileName)
}

// MakeCache will create a cache of the UCUM measurements.
func MakeCache(filename string) error {
	r, err := GetUCUMDataFromUpstream()
	if err != nil {
		return err
	}
	res := UCUM{
		Prefixes: map[string]string{},
		Units:    map[string]string{},
	}
	for _, prefix := range r.Prefixes {
		res.Prefixes[prefix.Code] = prefix.Name
	}
	for _, unit := range r.BaseUnits {
		res.Units[unit.Code] = unit.Name
	}
	for _, unit := range r.Units {
		res.Units[unit.Code] = unit.Name
	}
	//nolint:gosec // this is controlled by the runner of the utility.
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	//nolint:errcheck // not sure what we would do if this failed anyway.
	defer file.Close()
	enc := json.NewEncoder(file)
	return enc.Encode(res)
}

// LoadFromFile will load the UCUM measurements from a file.
func LoadFromFile(filename string) (*UCUM, error) {
	if !utils.DoesFileExist(filename) {
		// Make the local cache...
		if err := MakeCache(filename); err != nil {
			return nil, err
		}
	}
	file, err := utils.OpenFile(filename)
	if err != nil {
		return nil, err
	}
	//nolint:errcheck // Not sure what we would do if this failed anyway.
	defer file.Close()
	dec := json.NewDecoder(file)
	var tmp UCUM
	if err := dec.Decode(&tmp); err != nil {
		return nil, err
	}
	tmp.Units["{rev}"] = "Revolutions"
	return &tmp, nil
}

//nolint:gochecknoglobals // These are basically constants, but golang doesn't let us mark them that way.
var (
	seperators = map[string]string{
		".": "",
		"/": "sPer",
	}
	suffixes = map[string]string{
		"2": "Square",
		"3": "Cubic",
	}
)

// ValidMeasurement checks if a measurement string is valid.
func (ucum *UCUM) ValidMeasurement(measurement string) bool {
	_, ok := ucum.Units[measurement]
	if ok {
		return true
	}
	for sep := range seperators {
		if strings.Contains(measurement, sep) {
			m1, m2, _ := strings.Cut(measurement, sep)
			return ucum.ValidMeasurement(m1) && ucum.ValidMeasurement(m2)
		}
	}
	for prefix := range ucum.Prefixes {
		if after, ok0 := strings.CutPrefix(measurement, prefix); ok0 {
			tmp := after
			_, ok := ucum.Units[tmp]
			if ok {
				return true
			}
		}
	}
	for suffix := range suffixes {
		if strings.HasSuffix(measurement, suffix) {
			return ucum.ValidMeasurement(measurement[:len(measurement)-len(suffix)])
		}
	}
	return ok
}

// GetUnitName returns the name of a unit.
func (ucum *UCUM) GetUnitName(measurement string) string {
	if len(measurement) > 1 {
		for suffix, name := range suffixes {
			if strings.HasSuffix(measurement, suffix) {
				return name + ucum.GetUnitName(measurement[:len(measurement)-len(suffix)])
			}
		}
	}
	value, ok := ucum.Units[measurement]
	if ok {
		value = strings.TrimPrefix(value, "degree ") // Remove degree prefix from temps
		return CapitalizeFirstLetter(value)
	}
	for sep, insert := range seperators {
		if strings.Contains(measurement, sep) {
			m1, m2, _ := strings.Cut(measurement, sep)
			return ucum.GetUnitName(m1) + insert + ucum.GetUnitName(m2)
		}
	}
	for prefix, prefixName := range ucum.Prefixes {
		if after, ok0 := strings.CutPrefix(measurement, prefix); ok0 {
			tmp := after
			unitName, ok := ucum.Units[tmp]
			if ok {
				return CapitalizeFirstLetter(prefixName) + unitName
			}
		}
	}
	return measurement
}

// CapitalizeFirstLetter capitalizes the first letter of a string.
func CapitalizeFirstLetter(s string) string {
	if s == "" {
		return ""
	}

	r, size := utf8.DecodeRuneInString(s)
	if r == utf8.RuneError { // Handle potential decoding errors
		return s // Return original string if there's an error
	}
	if unicode.IsUpper(r) {
		return s
	}

	return string(unicode.ToUpper(r)) + s[size:]
}
