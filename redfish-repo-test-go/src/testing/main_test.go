/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testing_test

import (
	"path/filepath"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/config"
	testfactory "github.com/DMTF/redfishRepoTest/src/testing"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCreateTestsFromConfigWithUnrelatedSingleFile(t *testing.T) { //nolint:paralleltest // Changes process working directory.
	t.Chdir("../..")

	cfg := &config.Config{
		SingleFile: filepath.Join(t.TempDir(), "unrelated.txt"),
		Copyright:  "Copyright",
	}

	testMain, err := testfactory.CreateTestsFromConfig(cfg)
	require.NoError(t, err)
	require.NotNil(t, testMain)
	require.Len(t, testMain.Lists, 6)
	assert.Equal(t, "CSDL", testMain.Lists[0].Name)
	assert.Equal(t, "Mockups", testMain.Lists[1].Name)
	assert.Equal(t, "DSP2046", testMain.Lists[2].Name)
	assert.Equal(t, "JSON Schema", testMain.Lists[3].Name)
	assert.Equal(t, "Markdown", testMain.Lists[4].Name)
	assert.Equal(t, "Message Registry", testMain.Lists[5].Name)
}
