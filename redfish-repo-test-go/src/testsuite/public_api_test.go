/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testsuite_test

import (
	"bytes"
	"errors"
	"os"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

var errTestFailure = errors.New("test failure")

func TestTestingPublicAPI(t *testing.T) {
	t.Parallel()

	var output bytes.Buffer
	testContext := testsuite.NewTesting("parent", &output)

	assert.Equal(t, "parent", testContext.Name())
	assert.Equal(t, os.TempDir(), testContext.ArtifactDir())
	assert.Equal(t, os.TempDir(), testContext.TempDir())
	assert.NotNil(t, testContext.Context())
	assert.Same(t, &output, testContext.Output())

	testContext.Attr("key", "value")
	assert.Equal(t, "value", testContext.GetAttr("key"))

	testContext.Cleanup(func() {})
	testContext.Helper()
	testContext.Setenv("KEY", "value")
	testContext.Chdir(t.TempDir())
	testContext.Skipf("unused %s", "message")

	testContext.Log("log message")
	testContext.Logf("formatted %s", "message")
	testContext.Error(errTestFailure)
	testContext.Errorf("wrapped: %v", errTestFailure)

	assert.False(t, testContext.Failed())
	assert.Equal(t, testsuite.Warning, testContext.Status)
	assert.Equal(t, []error{errTestFailure, errTestFailure}, testContext.Errors)
	assert.Contains(t, output.String(), "log message")
	assert.Contains(t, output.String(), "formatted message")
	assert.Contains(t, output.String(), "test failure")

	testContext.Fail()
	assert.True(t, testContext.Failed())

	skipped := testsuite.NewTesting("skipped", &bytes.Buffer{})
	skipped.Skip("reason")
	assert.True(t, skipped.Skipped())
}

func TestTestingRunPropagatesChildStatus(t *testing.T) {
	t.Parallel()

	parent := testsuite.NewTesting("parent", &bytes.Buffer{})
	assert.True(t, parent.Run("success", func(child *testsuite.Testing) {
		assert.Equal(t, "parent/success", child.Name())
	}))
	assert.False(t, parent.Run("warning", func(child *testsuite.Testing) {
		child.Error(errTestFailure)
	}))
	assert.Equal(t, testsuite.Warning, parent.Status)
}

func TestTestingTerminatingMethods(t *testing.T) {
	t.Parallel()

	testCases := []struct {
		name     string
		test     func(*testsuite.Testing)
		expected testsuite.Status
		message  string
	}{
		{
			name: "fail now",
			test: func(testContext *testsuite.Testing) {
				testContext.FailNow()
			},
			expected: testsuite.Failure,
		},
		{
			name: "fatal",
			test: func(testContext *testsuite.Testing) {
				testContext.Fatal(errTestFailure)
			},
			expected: testsuite.Failure,
			message:  "test failure",
		},
		{
			name: "fatalf",
			test: func(testContext *testsuite.Testing) {
				testContext.Fatalf("fatal: %v", errTestFailure)
			},
			expected: testsuite.Failure,
			message:  "fatal: test failure",
		},
		{
			name: "skip now",
			test: func(testContext *testsuite.Testing) {
				testContext.SkipNow()
			},
			expected: testsuite.Skipped,
		},
		{
			name: "parallel",
			test: func(testContext *testsuite.Testing) {
				testContext.Parallel()
			},
			expected: testsuite.Success,
		},
	}

	for _, testCase := range testCases {
		t.Run(testCase.name, func(t *testing.T) {
			t.Parallel()
			caseInstance := testsuite.NewCase(testCase.name, testCase.test, nil)
			assert.Equal(t, testCase.expected, caseInstance.Run())
			if testCase.message != "" {
				assert.Contains(t, caseInstance.Buffer.String(), testCase.message)
			}
		})
	}
}

func TestSuiteAttributesCleanupAndStatusOutput(t *testing.T) {
	t.Parallel()

	list := &testsuite.List{Name: "list", Status: testsuite.Pending}
	suite := list.AddSuite("suite")
	suite.AddAttribute("key", 42)
	assert.Equal(t, 42, suite.GetAttribute("key"))

	cleaned := false
	suite.Cleanup(func(cleanedSuite *testsuite.Suite) {
		cleaned = true
		assert.Same(t, suite, cleanedSuite)
	})
	suite.AddTest("success", func(testContext *testsuite.Testing) {
		assert.Equal(t, 42, testContext.GetAttr("key"))
	})
	suite.AddTest("warning", func(testContext *testsuite.Testing) {
		testContext.Error(errTestFailure)
	})

	assert.Equal(t, testsuite.Warning, suite.Run())
	assert.True(t, cleaned)
	require.Len(t, suite.Errors, 1)

	var output bytes.Buffer
	suite.PrintStatus(&output, "  ")
	assert.Contains(t, output.String(), "  suite: ")
	assert.Contains(t, output.String(), "suite/warning")
	assert.Contains(t, output.String(), "test failure")
}

func TestTestMainDirectTestsAndStatusOutput(t *testing.T) {
	t.Parallel()

	main := testsuite.NewTestMain()
	main.AddTest("success", func(testContext testsuite.T) {
		testContext.Cleanup(func() {})
	})
	list := main.AddList("list")
	setupCalled := false
	list.AddSetup(func() { setupCalled = true })
	list.AddSuite("suite").AddTest("success", func(_ *testsuite.Testing) {})

	assert.Zero(t, main.Run())
	assert.True(t, setupCalled)

	var output bytes.Buffer
	main.PrintStatus(&output)
	assert.Contains(t, output.String(), "list:")
	assert.Contains(t, output.String(), "Overall")
}

func TestStatusString(t *testing.T) {
	t.Parallel()

	testCases := map[testsuite.Status]string{
		testsuite.Pending: "...",
		testsuite.Skipped: "⍉",
		testsuite.Success: "✅",
		testsuite.Warning: "⚠",
		testsuite.Failure: "❌",
		99:                "Unknown status",
	}
	for status, expected := range testCases {
		assert.Equal(t, expected, status.String())
	}
}
