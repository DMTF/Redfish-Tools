/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package csdl_test

import (
	"bytes"
	"os"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

const (
	DescriptionsTestDefaultFile = "DescriptionsTest"
)

//nolint:funlen // The table-driven test keeps its related XML cases together.
func GetDescriptionTestCases() []csdlTestCase {
	cfg := &config.Config{
		AllowLists: config.AllowLists{},
	}
	//nolint:misspell // Test cases test misspelling detection.
	return []csdlTestCase{
		{
			Name:       "No Descriptions",
			CSDL:       EmptyValidCSDL,
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Valid Descriptions",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.Description" String="This is a test."/><Annotation Term="OData.LongDescription" String="This is a longer test.  It has proper spacing."/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Missing Period in Description",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.Description" String="This is a test without period"/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.Description']: Missing period at end of description",
			},
		},
		{
			Name:       "Missing Period in LongDescription",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.LongDescription" String="This is a long description without period"/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.LongDescription']: Missing period at end of long description",
			},
		},
		{
			Name:       "Contains Must in LongDescription",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.LongDescription" String="This must not be used.  It has proper spacing."/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.LongDescription']: Long Description should not contain ISO unallowed word \"must\"",
			},
		},
		{
			Name:       "Must at Start of LongDescription",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.LongDescription" String="Must not be used.  It has proper spacing."/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.LongDescription']: Long Description should not contain ISO unallowed word \"must\"",
			},
		},
		{
			Name:       "Spelling Error in Description",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.Description" String="This is a test with a spelling error in abbout."/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.Description']: Description contains spelling error: abbout -> about",
			},
		},
		{
			Name:       "Spelling Error in LongDescription",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.LongDescription" String="This is a long description with a spelling error.  Check that abilty."/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.LongDescription']: Long description contains spelling error: abilty -> ability",
			},
		},
		{
			Name:       "Multiple Errors",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.Description" String="This is a test with teh spelling error"/><Annotation Term="OData.LongDescription" String="This must not be used and has no period"/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.Description']: Missing period at end of description",
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.Description']: Description contains spelling error: teh -> the",
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.LongDescription']: Missing period at end of long description",
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.LongDescription']: Long Description should not contain ISO unallowed word \"must\"",
			},
		},
	}
}

//nolint:funlen // The table-driven test keeps its related XML cases together.
func GetDescriptionPendanticTestCases() []csdlTestCase {
	cfg := &config.Config{
		AllowLists: config.AllowLists{},
	}
	return []csdlTestCase{
		{
			Name:       "No Descriptions",
			CSDL:       EmptyValidCSDL,
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Valid Double Space After Period",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.Description" String="This is a test.  It has double space."/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Valid Period at End",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.Description" String="This is a test."/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Invalid Single Space After Period",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.Description" String="This is a test. It has single space."/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.Description']: Description does not follow period spacing rules",
			},
		},
		{
			Name:       "Invalid LongDescription Single Space",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.LongDescription" String="This is a test. It has single space."/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.LongDescription']: Long description does not follow period spacing rules",
			},
		},
		{
			Name:       "Multiple Periods with Mixed Spacing",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.Description" String="First sentence.  Second sentence. Third sentence."/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.Description']: Description does not follow period spacing rules",
			},
		},
		{
			Name:       "Valid Multiple Periods with Double Space",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.Description" String="First sentence.  Second sentence.  Third sentence."/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: false,
		},
		{
			Name:       "Both Description and LongDescription Invalid",
			CSDL:       makeSimpleCSDLText(DescriptionsTestDefaultFile, `<ComplexType Name="Test"><Annotation Term="OData.Description" String="Bad spacing. Here"/><Annotation Term="OData.LongDescription" String="Also bad. Here"/></ComplexType>`),
			FileName:   DescriptionsTestDefaultFile,
			Config:     cfg,
			ExpectFail: true,
			ExpectedErrors: []string{
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.Description']: Description does not follow period spacing rules",
				"Warning:DescriptionsTest.xml:/edmx:Edmx/edmx:DataServices/Schema[@Namespace='DescriptionsTest']/ComplexType[@Name='Test']/Annotation[@Term='OData.LongDescription']: Long description does not follow period spacing rules",
			},
		},
	}
}

func TestDescriptionChecks(t *testing.T) {
	t.Parallel()
	//nolint:paralleltest // The TestFunc calls Parallel...
	for _, tc := range GetDescriptionTestCases() {
		t.Run(tc.Name, tc.TestFunc("Description checks are valid", csdl.DescriptionChecks, nil))
	}
}

func BenchmarkDescriptionChecks(b *testing.B) {
	for _, tc := range GetDescriptionTestCases() {
		searcher := helperGetSearcherForText(b, tc.FileName, tc.CSDL, "")
		suiteCase := &testsuite.Case{
			Name:   "Description checks are valid",
			Func:   helperTestWrapper(nil, tc.Config, searcher, csdl.DescriptionChecks),
			Buffer: &bytes.Buffer{},
		}
		for b.Loop() {
			_ = suiteCase.Run()
		}
	}
}

func TestDescriptionPendantic(t *testing.T) {
	t.Parallel()
	//nolint:paralleltest // The TestFunc calls Parallel...
	for _, tc := range GetDescriptionPendanticTestCases() {
		t.Run(tc.Name, tc.TestFunc("Description pendantic checks are valid", csdl.DescriptionPendantic, nil))
	}
}

func TestDescriptionChecksAutoFixPreservesWhitespace(t *testing.T) {
	t.Parallel()

	cfg := &config.Config{}

	inputData, err := os.ReadFile("./testData/testSpellFix.xml")
	require.NoError(t, err)

	searcher, filePath := helperGetSearcherForFileContent(t, "testSpellFix", string(inputData))

	tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
	tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}

	cfg.CompileRegexes()
	csdl.DescriptionChecks(tPrime, nil, cfg, searcher)

	assert.Equal(t, testsuite.Success, tPrime.Status)
	assert.Empty(t, tPrime.Errors)

	result, err := os.ReadFile(filePath) //nolint:gosec // test-only read of temp path
	require.NoError(t, err)

	expected, err := os.ReadFile("./testData/testSpellFix_out.xml")
	require.NoError(t, err)

	assert.Equal(t, string(expected), string(result))
}

func TestDescriptionChecksAutoFixDescription(t *testing.T) {
	t.Parallel()

	cfg := &config.Config{}
	//nolint:misspell // Test case intentionally contains a misspelling to verify auto-fix.
	csdlContent := makeSimpleCSDLText(DescriptionsTestDefaultFile,
		`<ComplexType Name="Test"><Annotation Term="OData.Description" String="This is a test with a spelling error in abbout."/></ComplexType>`)

	searcher, filePath := helperGetSearcherForFileContent(t, DescriptionsTestDefaultFile, csdlContent)

	tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
	tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}

	cfg.CompileRegexes()
	csdl.DescriptionChecks(tPrime, nil, cfg, searcher)

	assert.Equal(t, testsuite.Success, tPrime.Status)
	assert.Empty(t, tPrime.Errors)

	data, err := os.ReadFile(filePath) //nolint:gosec // test-only read of temp path
	require.NoError(t, err)
	//nolint:misspell // Confirming the misspelling was corrected in the file.
	assert.NotContains(t, string(data), "abbout")
	assert.Contains(t, string(data), "about")
}

func TestDescriptionChecksAutoFixLongDescription(t *testing.T) {
	t.Parallel()

	cfg := &config.Config{}
	//nolint:misspell // Test case intentionally contains a misspelling to verify auto-fix.
	csdlContent := makeSimpleCSDLText(DescriptionsTestDefaultFile,
		`<ComplexType Name="Test"><Annotation Term="OData.LongDescription" String="This is a long description with a spelling error.  Check that abilty."/></ComplexType>`)

	searcher, filePath := helperGetSearcherForFileContent(t, DescriptionsTestDefaultFile, csdlContent)

	tPrime := testsuite.NewTesting("test", &bytes.Buffer{})
	tPrime.Case = &testsuite.Case{Suite: &testsuite.Suite{AutoFix: true}}

	cfg.CompileRegexes()
	csdl.DescriptionChecks(tPrime, nil, cfg, searcher)

	assert.Equal(t, testsuite.Success, tPrime.Status)
	assert.Empty(t, tPrime.Errors)

	data, err := os.ReadFile(filePath) //nolint:gosec // test-only read of temp path
	require.NoError(t, err)
	//nolint:misspell // Confirming the misspelling was corrected in the file.
	assert.NotContains(t, string(data), "abilty")
	assert.Contains(t, string(data), "ability")
}

type doubleSpaceTestCase struct {
	Name     string
	Input    string
	Expected bool
}

func GetDoubleSpaceTestCases() []doubleSpaceTestCase {
	return []doubleSpaceTestCase{
		{
			Name:     "Empty string",
			Input:    "",
			Expected: true,
		},
		{
			Name:     "Single period at end",
			Input:    "Hello.",
			Expected: true,
		},
		{
			Name:     "Single period not at end",
			Input:    "Hello. World",
			Expected: false,
		},
		{
			Name:     "Double space after period",
			Input:    "Hello.  World",
			Expected: true,
		},
		{
			Name:     "Multiple periods with double spaces",
			Input:    "Hello.  World.  Test.",
			Expected: true,
		},
		{
			Name:     "Multiple periods with single spaces",
			Input:    "Hello. World. Test.",
			Expected: false,
		},
		{
			Name:     "Trailing space after period",
			Input:    "Hello. ",
			Expected: false,
		},
		{
			Name:     "No periods",
			Input:    "Hello World Test",
			Expected: true,
		},
		{
			Name:     "Only periods",
			Input:    "...",
			Expected: false,
		},
	}
}

func TestAllPeriodsFollowedByDoubleSpaceOrEos(t *testing.T) {
	t.Parallel()
	testCases := GetDoubleSpaceTestCases()
	for _, tc := range testCases {
		t.Run(tc.Name, func(t *testing.T) {
			t.Parallel()
			result := csdl.AllPeriodsFollowedByDoubleSpaceOrEos(tc.Input)
			assert.Equal(t, tc.Expected, result, "Input: %q", tc.Input)
		})
	}
}

func BenchmarkAllPeriodsFollowedByDoubleSpaceOrEos(b *testing.B) {
	testCases := GetDoubleSpaceTestCases()
	for _, tc := range testCases {
		b.Run(tc.Name, func(b *testing.B) {
			b.ReportAllocs()
			for b.Loop() {
				_ = csdl.AllPeriodsFollowedByDoubleSpaceOrEos(tc.Input)
			}
		})
	}
}
