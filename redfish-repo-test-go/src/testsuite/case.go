/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testsuite

import (
	"bytes"
)

type Case struct {
	Name   string
	Func   func(t *Testing)
	Status Status
	Suite  *Suite
	Errors []error
	Buffer *bytes.Buffer
}

func NewCase(name string, test func(t *Testing), suite *Suite) *Case {
	if suite != nil {
		name = suite.Name + "/" + name
	}
	return &Case{
		Name:   name,
		Func:   test,
		Status: Success,
		Suite:  suite,
		Buffer: &bytes.Buffer{},
	}
}

func (c *Case) Run() Status {
	t := NewTesting(c.Name, c.Buffer)
	t.Case = c
	if c.Suite != nil {
		t.attrs = c.Suite.attrs
	} else {
		t.attrs = make(map[string]any)
	}
	go func() {
		defer func() {
			if r := recover(); r != nil {
				t.Error(r)
			}
			t.done <- true
		}()
		c.Func(t)
		if c.Status < Success {
			// If we got here and didn't mark an error...
			c.Status = Success
		}
	}()
	parallel := <-t.done
	if parallel {
		t.parallel = true
	}
	// Parallel test execution is not supported yet.
	c.Errors = t.Errors
	for _, child := range t.children {
		c.Errors = append(c.Errors, child.Errors...)
	}
	return c.Status
}
