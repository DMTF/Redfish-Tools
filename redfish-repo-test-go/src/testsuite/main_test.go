/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testsuite

import (
	"errors"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestRunIndependentListsInParallel(t *testing.T) {
	t.Parallel()

	m := NewTestMain()
	var running atomic.Int32
	var peak atomic.Int32

	for range 4 {
		list := m.AddList("independent")
		suite := list.AddSuite("s")
		suite.AddTest("t", func(t *Testing) {
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

	m.Run()

	// All 4 should have run concurrently.
	require.Greater(t, int(peak.Load()), 1, "independent lists should run in parallel")
}

func TestRunDependentListWaits(t *testing.T) {
	t.Parallel()

	m := NewTestMain()

	var mu sync.Mutex
	var order []string

	dep := m.AddList("dependency")
	depSuite := dep.AddSuite("s")
	depSuite.AddTest("slow", func(t *Testing) {
		time.Sleep(100 * time.Millisecond)
		mu.Lock()
		order = append(order, "dep")
		mu.Unlock()
	})

	child := m.AddList("child")
	child.DependsOn(dep)
	childSuite := child.AddSuite("s")
	childSuite.AddTest("fast", func(t *Testing) {
		mu.Lock()
		order = append(order, "child")
		mu.Unlock()
	})

	m.Run()

	mu.Lock()
	defer mu.Unlock()
	require.Equal(t, []string{"dep", "child"}, order)
}

func TestRunCollectsErrorsAndStatus(t *testing.T) {
	t.Parallel()

	m := NewTestMain()

	list := m.AddList("errors")
	suite := list.AddSuite("s")
	suite.AddTest("fail", func(t *Testing) {
		t.Error(errors.New("boom")) //nolint:err113 // test-only dynamic error
	})

	code := m.Run()

	// Warning status = 3 (iota position in const block)
	assert.Equal(t, int(Warning), code)
	require.Len(t, m.Errors, 1)
	assert.Contains(t, m.Errors[0].Error(), "boom")
	assert.Equal(t, Warning, m.Status)
}

func TestRunEmptyLists(t *testing.T) {
	t.Parallel()

	m := NewTestMain()
	m.AddList("empty1")
	m.AddList("empty2")

	code := m.Run()

	// Success status = 2 (iota position in const block)
	assert.Equal(t, int(Success), code)
	assert.Empty(t, m.Errors)
}

func TestRunDiamondDependency(t *testing.T) {
	t.Parallel()

	// A -> B, A -> C, B -> D, C -> D (diamond)
	m := NewTestMain()
	var mu sync.Mutex
	var order []string

	a := m.AddList("A")
	aSuite := a.AddSuite("s")
	aSuite.AddTest("t", func(t *Testing) {
		time.Sleep(50 * time.Millisecond)
		mu.Lock()
		order = append(order, "A")
		mu.Unlock()
	})

	b := m.AddList("B")
	b.DependsOn(a)
	bSuite := b.AddSuite("s")
	bSuite.AddTest("t", func(t *Testing) {
		mu.Lock()
		order = append(order, "B")
		mu.Unlock()
	})

	c := m.AddList("C")
	c.DependsOn(a)
	cSuite := c.AddSuite("s")
	cSuite.AddTest("t", func(t *Testing) {
		mu.Lock()
		order = append(order, "C")
		mu.Unlock()
	})

	d := m.AddList("D")
	d.DependsOn(b)
	d.DependsOn(c)
	dSuite := d.AddSuite("s")
	dSuite.AddTest("t", func(t *Testing) {
		mu.Lock()
		order = append(order, "D")
		mu.Unlock()
	})

	m.Run()

	mu.Lock()
	defer mu.Unlock()
	require.Len(t, order, 4)
	// A must be first
	assert.Equal(t, "A", order[0])
	// D must be last
	assert.Equal(t, "D", order[3])
}

func TestRunReturnCodeFromListOrder(t *testing.T) {
	t.Parallel()

	// Two failing lists; the return code should come from the first one in order.
	m := NewTestMain()

	l1 := m.AddList("first")
	s1 := l1.AddSuite("s")
	s1.AddTest("fail", func(t *Testing) {
		t.Error(errors.New("err1")) //nolint:err113 // test-only dynamic error
	})

	l2 := m.AddList("second")
	l2.DependsOn(l1)
	s2 := l2.AddSuite("s")
	s2.AddTest("fail", func(t *Testing) {
		t.Error(errors.New("err2")) //nolint:err113 // test-only dynamic error
	})

	code := m.Run()
	assert.Equal(t, int(Warning), code)
	require.Len(t, m.Errors, 2)
}
