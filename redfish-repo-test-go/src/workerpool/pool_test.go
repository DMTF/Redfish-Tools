/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package workerpool_test

import (
	"runtime"
	"sync/atomic"
	"testing"

	"github.com/DMTF/redfishRepoTest/src/workerpool"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNew(t *testing.T) {
	t.Parallel()

	t.Run("ClampsSizeToOne", func(t *testing.T) {
		t.Parallel()
		p := workerpool.New(0)
		assert.Equal(t, 1, p.NumWorkers())

		p = workerpool.New(-5)
		assert.Equal(t, 1, p.NumWorkers())
	})

	t.Run("RespectsExplicitSize", func(t *testing.T) {
		t.Parallel()
		p := workerpool.New(8)
		assert.Equal(t, 8, p.NumWorkers())
	})
}

func TestNewFromMultiplier(t *testing.T) {
	t.Parallel()
	p := workerpool.NewFromMultiplier(1.0)
	assert.Equal(t, runtime.NumCPU(), p.NumWorkers())

	p = workerpool.NewFromMultiplier(2.0)
	assert.Equal(t, 2*runtime.NumCPU(), p.NumWorkers())
}

func TestNilPoolNumWorkers(t *testing.T) {
	t.Parallel()
	var p *workerpool.Pool
	assert.Equal(t, 1, p.NumWorkers())
}

func TestRunExecutesAllItems(t *testing.T) {
	t.Parallel()
	p := workerpool.New(4)
	n := 100
	results := make([]int, n)
	p.Run(n, func(i int) {
		results[i] = i * 2
	})
	for i := range n {
		assert.Equal(t, i*2, results[i])
	}
}

func TestRunBoundsConcurrency(t *testing.T) {
	t.Parallel()
	poolSize := 3
	p := workerpool.New(poolSize)

	var peak atomic.Int32
	var running atomic.Int32
	done := make(chan struct{})

	p.Run(20, func(i int) {
		cur := running.Add(1)
		for {
			old := peak.Load()
			if cur <= old || peak.CompareAndSwap(old, cur) {
				break
			}
		}
		// Yield to let other goroutines start if they can.
		runtime.Gosched()
		running.Add(-1)
	})
	close(done)

	require.LessOrEqual(t, int(peak.Load()), poolSize)
}

func TestNilPoolRunsSequentially(t *testing.T) {
	t.Parallel()
	var p *workerpool.Pool
	order := make([]int, 0, 5)
	p.Run(5, func(i int) {
		order = append(order, i)
	})
	assert.Equal(t, []int{0, 1, 2, 3, 4}, order)
}

func TestRunZeroItems(t *testing.T) {
	t.Parallel()
	p := workerpool.New(4)
	called := false
	p.Run(0, func(i int) {
		called = true
	})
	assert.False(t, called)
}
