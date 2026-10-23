/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testsuite

import "bytes"

type TestFunc func(t T)

type Test struct {
	Name string
	Func TestFunc
}

func (t *Test) Run() (Status, []error) {
	buff := &bytes.Buffer{}
	testing := NewTesting(t.Name, buff)
	go func() {
		t.Func(testing)
		testing.done <- true
	}()
	<-testing.done
	return testing.Status, testing.Errors
}
