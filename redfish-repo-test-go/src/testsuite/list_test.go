/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testsuite

import (
	"errors"
	"fmt"
	"sync/atomic"
	"testing"
	"time"

	"github.com/DMTF/redfishRepoTest/src/workerpool"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestListRunParallelSuites(t *testing.T) {
	t.Parallel()

	list := &List{
		Name:   "parallel",
		Status: Pending,
		Pool:   workerpool.New(4),
		done:   make(chan struct{}),
	}

	var running atomic.Int32
	var peak atomic.Int32

	for range 4 {
		suite := list.AddSuite("s")
		suite.AddTest("t", func(_ *Testing) {
			cur := running.Add(1)
			for {
				old := peak.Load()
				if cur <= old || peak.CompareAndSwap(old, cur) {
					break
				}
			}
			time.Sleep(50 * time.Millisecond)
			running.Add(-1)
		})
	}

	code := list.Run()

	assert.Equal(t, int(Success), code)
	require.Greater(t, int(peak.Load()), 1, "suites should run in parallel when Pool is set")
}

func TestListRunSequentialWithoutPool(t *testing.T) {
	t.Parallel()

	list := &List{
		Name:   "sequential",
		Status: Pending,
		done:   make(chan struct{}),
	}

	var running atomic.Int32
	var peak atomic.Int32

	for range 4 {
		suite := list.AddSuite("s")
		suite.AddTest("t", func(_ *Testing) {
			cur := running.Add(1)
			for {
				old := peak.Load()
				if cur <= old || peak.CompareAndSwap(old, cur) {
					break
				}
			}
			time.Sleep(20 * time.Millisecond)
			running.Add(-1)
		})
	}

	code := list.Run()

	assert.Equal(t, int(Success), code)
	assert.Equal(t, int32(1), peak.Load(), "suites should run sequentially when Pool is nil")
}

func TestListRunParallelCollectsErrors(t *testing.T) {
	t.Parallel()

	list := &List{
		Name:   "errors",
		Status: Pending,
		Pool:   workerpool.New(4),
		done:   make(chan struct{}),
	}

	for i := range 4 {
		suite := list.AddSuite(fmt.Sprintf("s%d", i))
		idx := i
		suite.AddTest("fail", func(t *Testing) {
			t.Error(fmt.Errorf("error-%d", idx)) //nolint:err113 // test-only dynamic error
		})
	}

	code := list.Run()

	assert.Equal(t, int(Warning), code)
	require.Len(t, list.Errors, 4)
	assert.Equal(t, Warning, list.Status)
}

func TestListRunParallelPreservesErrorOrder(t *testing.T) {
	t.Parallel()

	list := &List{
		Name:   "ordered-errors",
		Status: Pending,
		Pool:   workerpool.New(1), // pool of 1 forces sequential to test ordering
		done:   make(chan struct{}),
	}

	for i := range 3 {
		suite := list.AddSuite(fmt.Sprintf("s%d", i))
		idx := i
		suite.AddTest("fail", func(t *Testing) {
			t.Error(fmt.Errorf("error-%d", idx)) //nolint:err113 // test-only dynamic error
		})
	}

	list.Run()

	require.Len(t, list.Errors, 3)
	// Errors should be collected in suite order (0, 1, 2)
	for i, err := range list.Errors {
		assert.Contains(t, err.Error(), fmt.Sprintf("error-%d", i))
	}
}

func TestListRunParallelStatusIsMax(t *testing.T) {
	t.Parallel()

	list := &List{
		Name:   "max-status",
		Status: Pending,
		Pool:   workerpool.New(4),
		done:   make(chan struct{}),
	}

	// Suite 0: success
	suite0 := list.AddSuite("success")
	suite0.AddTest("ok", func(_ *Testing) {})

	// Suite 1: warning
	suite1 := list.AddSuite("warning")
	suite1.AddTest("warn", func(t *Testing) {
		t.Error(errors.New("warn")) //nolint:err113 // test-only dynamic error
	})

	// Suite 2: failure
	suite2 := list.AddSuite("failure")
	suite2.AddTest("fail", func(t *Testing) {
		t.FailNow()
	})

	code := list.Run()

	assert.Equal(t, int(Failure), code)
	assert.Equal(t, Failure, list.Status)
}

func TestListRunParallelSetupRunsFirst(t *testing.T) {
	t.Parallel()

	list := &List{
		Name:   "setup-first",
		Status: Pending,
		Pool:   workerpool.New(4),
		done:   make(chan struct{}),
	}

	setupDone := false
	list.AddSetup(func() {
		setupDone = true
	})

	suite := list.AddSuite("s")
	suite.AddTest("check", func(t *Testing) {
		if !setupDone {
			t.Fatal("setup should have run before suites")
		}
	})

	code := list.Run()
	assert.Equal(t, int(Success), code)
}
