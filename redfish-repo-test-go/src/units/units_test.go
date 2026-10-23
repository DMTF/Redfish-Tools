/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package units_test

import (
	"testing"

	"github.com/DMTF/redfishRepoTest/src/units"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestLoad(t *testing.T) { //nolint:paralleltest // Changes process working directory.
	t.Chdir("../..")

	unitData, err := units.Load()
	require.NoError(t, err)
	require.NotNil(t, unitData)
	assert.True(t, unitData.ValidMeasurement("m"))
	assert.Equal(t, "Meter", unitData.GetUnitName("m"))
}
