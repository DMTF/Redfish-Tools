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

	"github.com/DMTF/redfishRepoTest/src/workerpool"
)

type List struct {
	sync.Mutex

	Name    string
	Status  Status
	AutoFix bool
	Suites  []*Suite
	Errors  []error
	Pool    *workerpool.Pool
	setup   []func()
	deps    []*List
	done    chan struct{}
}

// DependsOn declares that this list must wait for the given list
// to finish before it starts running.
func (l *List) DependsOn(other *List) {
	l.deps = append(l.deps, other)
}

func (l *List) AddSuite(name string) *Suite {
	l.Lock()
	defer l.Unlock()
	if l.Suites == nil {
		l.Suites = make([]*Suite, 0)
	}
	suite := &Suite{
		Name:    name,
		Status:  Success,
		AutoFix: l.AutoFix,
		Cases:   make([]*Case, 0),
		attrs:   make(map[string]any),
	}
	l.Suites = append(l.Suites, suite)
	return suite
}

func (l *List) AddSetup(setup func()) {
	l.setup = append(l.setup, setup)
}

func (l *List) PrintStatus(out io.Writer, prefix string) {
	_, _ = fmt.Fprintf(out, "%s%s: %s\n", prefix, l.Name, l.Status)
	for _, suite := range l.Suites {
		suite.PrintStatus(out, prefix+"  ")
	}
}

func (l *List) Run() int {
	for _, setup := range l.setup {
		setup()
	}
	// Run all suites (parallel when Pool is set, sequential otherwise).
	l.Pool.Run(len(l.Suites), func(i int) {
		l.Suites[i].Run()
	})
	// Collect errors and status sequentially after all suites complete.
	retStatus := Success
	for _, suite := range l.Suites {
		if suite.Status > retStatus {
			retStatus = suite.Status
		}
		l.Errors = append(l.Errors, suite.Errors...)
	}
	l.Status = retStatus
	return int(retStatus)
}

// waitForDeps blocks until all dependency lists have finished.
func (l *List) waitForDeps() {
	for _, dep := range l.deps {
		<-dep.done
	}
}
