/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup_test

import (
	"bytes"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/mockup"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func makeMockupForCopyrightTest(t *testing.T, cfg *config.Config) *mockup.Mockup {
	t.Helper()
	ret := mockup.NewMockup(t.TempDir(), cfg)
	ret.InjectFile("good.json", nil, map[string]any{"@Redfish.Copyright": "Copyright 1999 Test."})
	ret.InjectFile("alsoGood.json", nil, map[string]any{"@Redfish.Copyright": "Copyright 2002 Test."})
	ret.InjectFile("bad.json", nil, map[string]any{"@Redfish.Copyright": "Copyright 2005 Contoso."})
	ret.InjectFile("missing.json", nil, map[string]any{"somethingElse": true})
	ret.InjectFile("test-example.json", nil, map[string]any{"somethingElse": true})
	return ret
}

func TestCopyrightTest(t *testing.T) {
	t.Parallel()
	t.Run("NoCopyrightInConfig", func(t *testing.T) {
		t.Parallel()
		cfg := &config.Config{}
		mockup := makeMockupForCopyrightTest(t, cfg)
		tPrime := testsuite.NewTesting("Test", &bytes.Buffer{})
		mockup.CopyrightTest(tPrime)
		assert.Equal(t, testsuite.Success, tPrime.Status)
		assert.Empty(t, tPrime.Errors)
	})
	t.Run("CopyrightInConfig", func(t *testing.T) {
		t.Parallel()
		cfg := &config.Config{
			Copyright: `Copyright \d{4} Test.`,
		}
		mockup := makeMockupForCopyrightTest(t, cfg)
		tPrime := testsuite.NewTesting("Test", &bytes.Buffer{})
		mockup.CopyrightTest(tPrime)
		assert.Equal(t, testsuite.Warning, tPrime.Status)
		require.Len(t, tPrime.Errors, 2)
	})
	t.Run("CopyrightInConfigAllowBad", func(t *testing.T) {
		t.Parallel()
		cfg := &config.Config{
			Copyright: `Copyright \d{4} Test.`,
			AllowLists: config.AllowLists{
				NoCopyrightPaths: []string{t.TempDir() + "/bad.json"},
			},
		}
		mockup := makeMockupForCopyrightTest(t, cfg)
		tPrime := testsuite.NewTesting("Test", &bytes.Buffer{})
		mockup.CopyrightTest(tPrime)
		assert.Equal(t, testsuite.Warning, tPrime.Status)
		require.Len(t, tPrime.Errors, 1)
	})
}
