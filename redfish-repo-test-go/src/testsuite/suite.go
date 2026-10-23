/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testsuite

import (
	"bytes"
	"fmt"
	"io"
)

type Suite struct {
	Name     string
	Status   Status
	AutoFix  bool
	Cases    []*Case
	attrs    map[string]any
	Errors   []error
	cleaners []func(*Suite)
}

func (s *Suite) AddTest(name string, test func(*Testing)) {
	s.Cases = append(s.Cases, &Case{
		Name:   s.Name + "/" + name,
		Func:   test,
		Status: Success,
		Suite:  s,
		Buffer: &bytes.Buffer{},
	})
}

func (s *Suite) AddAttribute(key string, value any) {
	if s.attrs == nil {
		s.attrs = make(map[string]any)
	}
	s.attrs[key] = value
}

func (s *Suite) GetAttribute(key string) any {
	return s.attrs[key]
}

func (s *Suite) Cleanup(cleaner func(*Suite)) {
	s.cleaners = append(s.cleaners, cleaner)
}

func (s *Suite) PrintStatus(out io.Writer, prefix string) {
	_, _ = fmt.Fprintf(out, "%s%s: %s\n", prefix, s.Name, s.Status)
	for _, testCase := range s.Cases {
		_, _ = fmt.Fprintf(out, "%s  %s: %s\n", prefix, testCase.Name, testCase.Status)
		if testCase.Status != Success {
			_, _ = fmt.Fprintf(out, "\n%s    %s\n", prefix, testCase.Buffer.String())
		}
	}
}

func (s *Suite) Run() Status {
	retStatus := Success
	for _, testCase := range s.Cases {
		status := testCase.Run()
		if status > retStatus {
			retStatus = status
		}
		s.Errors = append(s.Errors, testCase.Errors...)
	}
	s.Status = retStatus
	for _, cleaner := range s.cleaners {
		cleaner(s)
	}
	return s.Status
}
