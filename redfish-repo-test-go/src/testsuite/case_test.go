/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testsuite

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCaseRun_PanicDoesNotDeadlock(t *testing.T) {
	t.Parallel()

	c := NewCase("panic-case", func(_ *Testing) {
		panic("boom")
	}, nil)

	done := make(chan Status, 1)
	go func() {
		done <- c.Run()
	}()

	select {
	case status := <-done:
		assert.Equal(t, Warning, status)
		require.Contains(t, c.Buffer.String(), "boom")
	case <-time.After(2 * time.Second):
		t.Fatal("Case.Run hung after panic")
	}
}
