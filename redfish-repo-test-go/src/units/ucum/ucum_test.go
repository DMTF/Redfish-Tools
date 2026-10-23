/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package ucum_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/units/ucum"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestMakeCache(t *testing.T) {
	t.Parallel()
	tmpDir := t.TempDir()
	fileName := filepath.Join(tmpDir, "ucum.json")
	t.Cleanup(func() {
		_ = os.Remove(fileName)
	})

	err := ucum.MakeCache(fileName)
	require.NoError(t, err)

	// Verify the file was created
	_, err = os.Stat(fileName)
	require.NoError(t, err)
}

type unitTestCase struct {
	Name         string
	Unit         string
	Valid        bool
	ExpectedName string
}

//nolint:funlen // Just a list of test cases.
func getUnitTestCases() []unitTestCase {
	return []unitTestCase{
		{
			Name:         "meter",
			Unit:         "m",
			Valid:        true,
			ExpectedName: "Meter",
		},
		{
			Name:         "kilogram",
			Unit:         "kg",
			Valid:        true,
			ExpectedName: "Kilogram",
		},
		{
			Name:         "rev unit",
			Unit:         "{rev}",
			Valid:        true,
			ExpectedName: "Revolutions",
		},
		{
			Name:         "invalid unit",
			Unit:         "x",
			Valid:        false,
			ExpectedName: "",
		},
		{
			Name:         "invalid unit with prefix",
			Unit:         "kx",
			Valid:        false,
			ExpectedName: "",
		},
		{
			Name:         "valid unit with invalid prefix",
			Unit:         "xm",
			Valid:        false,
			ExpectedName: "",
		},
		{
			Name:         "valid unit with dot",
			Unit:         "m.s",
			Valid:        true,
			ExpectedName: "MeterSecond",
		},
		{
			Name:         "valid unit with multiple dots",
			Unit:         "m.g.s",
			Valid:        true,
			ExpectedName: "MeterGramSecond",
		},
		{
			Name:         "valid unit with slash",
			Unit:         "m/s",
			Valid:        true,
			ExpectedName: "MetersPerSecond",
		},
		{
			Name:         "squared units",
			Unit:         "m2",
			Valid:        true,
			ExpectedName: "SquareMeter",
		},
		{
			Name:         "cubed units",
			Unit:         "m3",
			Valid:        true,
			ExpectedName: "CubicMeter",
		},
	}
}

func TestUCUM(t *testing.T) {
	t.Parallel()

	// Create a test UCUM instance with sample data
	testUCUM := &ucum.UCUM{
		Prefixes: map[string]string{
			"k": "kilo",
			"m": "milli",
			"M": "mega",
		},
		Units: map[string]string{
			"m":     "meter",
			"g":     "gram",
			"s":     "second",
			"A":     "ampere",
			"K":     "kelvin",
			"mol":   "mole",
			"cd":    "candela",
			"{rev}": "revolutions",
		},
	}
	for _, tc := range getUnitTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()

			assert.Equal(t, tc.Valid, testUCUM.ValidMeasurement(tc.Unit), "Unit %s should be %v", tc.Unit, tc.Valid)
			if tc.ExpectedName != "" {
				assert.Equal(t, tc.ExpectedName, testUCUM.GetUnitName(tc.Unit),
					"Unit %s should have name %s", tc.Unit, tc.ExpectedName)
			}
		})
	}
}

func TestUCUM_LoadAndSave(t *testing.T) {
	t.Parallel()

	t.Run("load and save cycle", func(t *testing.T) {
		t.Parallel()

		// Create a temporary directory for test files
		tempDir := t.TempDir()
		testFile := filepath.Join(tempDir, "test_units.json")

		// Create original UCUM data
		original := &ucum.UCUM{
			Prefixes: map[string]string{
				"k": "kilo",
				"m": "milli",
			},
			Units: map[string]string{
				"m": "meter",
				"g": "gram",
			},
		}

		expectedUnits := map[string]string{
			"m":     "meter",
			"g":     "gram",
			"{rev}": "Revolutions",
		}

		// Save to file
		//nolint:gosec // this is just a test case.
		file, err := os.Create(testFile)
		require.NoError(t, err)
		//nolint:errcheck // not sure what we would do if this failed anyway.
		defer file.Close()

		enc := json.NewEncoder(file)
		err = enc.Encode(original)
		require.NoError(t, err)

		// Load from file
		loaded, err := ucum.LoadFromFile(testFile)
		require.NoError(t, err)
		require.NotNil(t, loaded)

		// Verify data integrity
		assert.Equal(t, original.Prefixes, loaded.Prefixes)
		assert.Equal(t, expectedUnits, loaded.Units)
	})

	t.Run("load invalid JSON file", func(t *testing.T) {
		t.Parallel()

		// Create a temporary directory for test files
		tempDir := t.TempDir()
		testFile := filepath.Join(tempDir, "invalid.json")

		// Create invalid JSON file
		//nolint:gosec // this is just a test case.
		file, err := os.Create(testFile)
		require.NoError(t, err)
		//nolint:errcheck // not sure what we would do if this failed anyway.
		defer file.Close()

		_, err = file.WriteString("invalid json content")
		require.NoError(t, err)

		// Try to load
		loaded, err := ucum.LoadFromFile(testFile)
		assert.Error(t, err)
		assert.Nil(t, loaded)
	})
}

// Test edge cases and error conditions.
func TestUCUM_EdgeCases(t *testing.T) {
	t.Parallel()

	t.Run("empty UCUM instance", func(t *testing.T) {
		t.Parallel()

		emptyUCUM := &ucum.UCUM{
			Prefixes: map[string]string{},
			Units:    map[string]string{},
		}

		assert.False(t, emptyUCUM.ValidMeasurement("m"))
		assert.False(t, emptyUCUM.ValidMeasurement("km"))
		assert.False(t, emptyUCUM.ValidMeasurement("m/s"))

		// GetUnitName should return the input for unknown units
		assert.Equal(t, "m", emptyUCUM.GetUnitName("m"))
		assert.Equal(t, "km", emptyUCUM.GetUnitName("km"))
	})

	t.Run("measurement validation with edge cases", func(t *testing.T) {
		t.Parallel()

		testUCUM := &ucum.UCUM{
			Prefixes: map[string]string{
				"k": "kilo",
			},
			Units: map[string]string{
				"m": "meter",
			},
		}

		// Test edge cases for measurement validation
		assert.False(t, testUCUM.ValidMeasurement(""))  // empty string
		assert.False(t, testUCUM.ValidMeasurement(".")) // just dot
		assert.False(t, testUCUM.ValidMeasurement("/")) // just slash
		assert.False(t, testUCUM.ValidMeasurement("k")) // just prefix
		assert.False(t, testUCUM.ValidMeasurement("2")) // just number
		assert.False(t, testUCUM.ValidMeasurement("3")) // just number
	})

	t.Run("unit name generation with edge cases", func(t *testing.T) {
		t.Parallel()

		testUCUM := &ucum.UCUM{
			Prefixes: map[string]string{
				"k": "kilo",
			},
			Units: map[string]string{
				"m": "meter",
			},
		}

		// Test edge cases for unit name generation
		assert.Equal(t, "k", testUCUM.GetUnitName("k"))           // just prefix
		assert.Equal(t, "2", testUCUM.GetUnitName("2"))           // just number
		assert.Equal(t, "CubicMeter", testUCUM.GetUnitName("m3")) // valid unit with cubed
		assert.Empty(t, testUCUM.GetUnitName(""))                 // empty string
	})
}

// Benchmark tests.
func BenchmarkUCUM_ValidMeasurement(b *testing.B) {
	testUCUM := &ucum.UCUM{
		Prefixes: map[string]string{
			"k": "kilo",
			"m": "milli",
			"M": "mega",
			"µ": "micro",
			"n": "nano",
		},
		Units: map[string]string{
			"m":   "meter",
			"g":   "gram",
			"s":   "second",
			"A":   "ampere",
			"K":   "kelvin",
			"mol": "mole",
			"cd":  "candela",
			"rad": "radian",
			"sr":  "steradian",
			"Hz":  "hertz",
			"N":   "newton",
			"Pa":  "pascal",
			"J":   "joule",
			"W":   "watt",
			"C":   "coulomb",
			"V":   "volt",
			"F":   "farad",
			"Ω":   "ohm",
			"S":   "siemens",
			"Wb":  "weber",
			"T":   "tesla",
			"H":   "henry",
			"lm":  "lumen",
			"lx":  "lux",
			"Bq":  "becquerel",
			"Gy":  "gray",
			"Sv":  "sievert",
			"kat": "katal",
		},
	}

	testMeasurements := []string{
		"m", "kg", "s", "A", "K", "mol", "cd",
		"km", "mm", "Mg", "µg", "ns",
		"m/s", "km/h", "m/s2", "kg.m/s2",
		"N.m", "Pa.s", "W/A", "V.s",
		"{rev}", "rad", "sr", "Hz", "N", "Pa",
	}

	b.ResetTimer()
	b.ReportAllocs()
	for b.Loop() {
		for _, measurement := range testMeasurements {
			_ = testUCUM.ValidMeasurement(measurement)
		}
	}
}

func BenchmarkUCUM_GetUnitName(b *testing.B) {
	testUCUM := &ucum.UCUM{
		Prefixes: map[string]string{
			"k": "kilo",
			"m": "milli",
			"M": "mega",
			"µ": "micro",
			"n": "nano",
		},
		Units: map[string]string{
			"m":   "meter",
			"g":   "gram",
			"s":   "second",
			"A":   "ampere",
			"K":   "kelvin",
			"mol": "mole",
			"cd":  "candela",
			"Cel": "degree Celsius",
			"F":   "degree Fahrenheit",
		},
	}

	testMeasurements := []string{
		"m", "kg", "s", "A", "K", "mol", "cd",
		"km", "mm", "Mg", "µg", "ns",
		"m/s", "km/h", "m/s2", "kg.m/s2",
		"N.m", "Pa.s", "W/A", "V.s",
		"Cel", "F",
	}

	b.ResetTimer()
	b.ReportAllocs()
	for b.Loop() {
		for _, measurement := range testMeasurements {
			_ = testUCUM.GetUnitName(measurement)
		}
	}
}

type capitalizeFirstLetterTestCase struct {
	Name     string
	Input    string
	Expected string
}

func getCapitalizeFirstLetterTestCases() []capitalizeFirstLetterTestCase {
	return []capitalizeFirstLetterTestCase{
		{
			Name:     "empty string",
			Input:    "",
			Expected: "",
		},
		{
			Name:     "single lowercase letter",
			Input:    "a",
			Expected: "A",
		},
		{
			Name:     "single uppercase letter",
			Input:    "A",
			Expected: "A",
		},
		{
			Name:     "lowercase word",
			Input:    "hello",
			Expected: "Hello",
		},
		{
			Name:     "already capitalized",
			Input:    "Hello",
			Expected: "Hello",
		},
		{
			Name:     "mixed case",
			Input:    "hELLO",
			Expected: "HELLO",
		},
		{
			Name:     "with numbers",
			Input:    "test123",
			Expected: "Test123",
		},
		{
			Name:     "with spaces",
			Input:    "hello world",
			Expected: "Hello world",
		},
		{
			Name:     "unicode character",
			Input:    "über",
			Expected: "Über",
		},
		{
			Name:     "emoji",
			Input:    "😀hello",
			Expected: "😀hello",
		},
	}
}

func TestCapitalizeFirstLetter(t *testing.T) {
	t.Parallel()
	for _, tc := range getCapitalizeFirstLetterTestCases() {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			result := ucum.CapitalizeFirstLetter(tc.Input)
			assert.Equal(t, tc.Expected, result)
		})
	}
}

func BenchmarkCapitalizeFirstLetter(b *testing.B) {
	for _, tc := range getCapitalizeFirstLetterTestCases() {
		b.Run(tc.Name, func(b *testing.B) {
			b.ReportAllocs()
			b.ResetTimer()
			for b.Loop() {
				_ = ucum.CapitalizeFirstLetter(tc.Input)
			}
		})
	}
}
