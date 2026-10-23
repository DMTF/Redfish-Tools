/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package workerpool

import (
	"runtime"
	"sync"
)

// DefaultMultiplier is the CPU multiplier used to size the pool.
// Adjust this value to tune overall concurrency:
//   - 1.0 = one worker per CPU (good for pure CPU-bound work)
//   - 2.0 = two workers per CPU (good default for mixed CPU + I/O work)
//   - 0.5 = half the CPUs (useful to leave headroom for other processes)
//
// Benchmarking shows a flat performance plateau from 1.0x-3.0x, with
// measurable degradation below 0.75x and diminishing returns above 4.0x.
const DefaultMultiplier = 2.0

// Pool is a semaphore-bounded worker pool that limits total concurrent
// goroutines across all call sites sharing the same Pool instance.
// A nil *Pool is safe to use; all work runs sequentially.
type Pool struct {
	sem chan struct{}
}

// New creates a Pool with the given number of workers.
func New(size int) *Pool {
	if size < 1 {
		size = 1
	}
	return &Pool{sem: make(chan struct{}, size)}
}

// NewFromMultiplier creates a Pool sized at runtime.NumCPU() * multiplier.
func NewFromMultiplier(multiplier float64) *Pool {
	size := int(float64(runtime.NumCPU()) * multiplier)
	return New(size)
}

// NumWorkers returns the pool's concurrency limit.
func (p *Pool) NumWorkers() int {
	if p == nil {
		return 1
	}
	return cap(p.sem)
}

// Run executes fn(i) for i in [0, n) concurrently, bounded by the pool size.
// It blocks until all work items complete.
// If p is nil, items are executed sequentially.
func (p *Pool) Run(n int, fn func(i int)) {
	if p == nil {
		for i := range n {
			fn(i)
		}
		return
	}
	var wg sync.WaitGroup
	for i := range n {
		p.sem <- struct{}{} // acquire slot
		wg.Add(1)
		go func(idx int) {
			defer func() {
				<-p.sem // release slot
				wg.Done()
			}()
			fn(idx)
		}(i)
	}
	wg.Wait()
}
