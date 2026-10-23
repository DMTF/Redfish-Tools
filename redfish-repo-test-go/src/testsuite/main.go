/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testsuite

import (
	"fmt"
	"io"
	"sync"
)

type TestMain struct {
	Lists  []*List
	Tests  []*Test
	Errors []error
	Status Status
}

func NewTestMain() *TestMain {
	return &TestMain{
		Lists:  make([]*List, 0),
		Tests:  make([]*Test, 0),
		Status: Pending,
	}
}

func (m *TestMain) AddList(name string) *List {
	list := &List{
		Name:   name,
		Status: Pending,
		done:   make(chan struct{}),
	}
	m.Lists = append(m.Lists, list)
	return list
}

func (m *TestMain) AddTest(name string, test TestFunc) {
	testObj := &Test{
		Name: name,
		Func: test,
	}
	m.Tests = append(m.Tests, testObj)
}

func (m *TestMain) PrintStatus(out io.Writer) {
	for _, list := range m.Lists {
		list.PrintStatus(out, "")
	}
	_, _ = fmt.Fprintf(out, "Overall %s\n", m.Status)
}

func (m *TestMain) Run() int {
	codes := make([]int, len(m.Lists)+len(m.Tests))

	// Run all lists in parallel, respecting declared dependencies.
	// Each list waits for its deps to close their done channel before starting.
	var wg sync.WaitGroup
	wg.Add(len(m.Lists))
	for i, list := range m.Lists {
		go func(idx int, l *List) {
			defer wg.Done()
			l.waitForDeps()
			codes[idx] = l.Run()
			close(l.done)
		}(i, list)
	}
	wg.Wait()

	// Collect errors and status from lists (sequential, after all done).
	for _, list := range m.Lists {
		m.Errors = append(m.Errors, list.Errors...)
		if list.Status > m.Status {
			m.Status = list.Status
		}
	}

	// Run tests
	for i, test := range m.Tests {
		// fmt.Printf("Running test %d\n", i)
		status, errs := test.Run()
		m.Errors = append(m.Errors, errs...)
		if status > m.Status {
			m.Status = status
			if status >= Warning {
				codes[len(m.Lists)+i] = 1
			}
		}
		// fmt.Printf("Finished test %d\n", i)
	}

	// Find the first non-zero code
	for _, code := range codes {
		if code != 0 {
			return code
		}
	}
	return 0
}
