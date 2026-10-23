/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testsuite

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"os"
	"runtime"
	"sync"
)

// Basically implements testing.TB, but the interface has private methods that we can't implement.
type Testing struct {
	mu       sync.Mutex
	attrs    map[string]any
	buffer   *bytes.Buffer
	cleaners []func()
	name     string
	done     chan bool
	parallel bool
	parent   *Testing
	children []*Testing
	Errors   []error
	Status   Status
	Case     *Case
}

func NewTesting(name string, out *bytes.Buffer) *Testing {
	return &Testing{
		attrs:  map[string]any{},
		buffer: out,
		name:   name,
		done:   make(chan bool, 1),
		Status: Success,
	}
}

func (t *Testing) ArtifactDir() string {
	return os.TempDir()
}

// Purposely mismatch allowing us to store arbitrary attributes on the test.
func (t *Testing) Attr(key string, value any) {
	if t.attrs == nil {
		t.attrs = make(map[string]any)
	}
	t.attrs[key] = value
}

func (t *Testing) GetAttr(key string) any {
	return t.attrs[key]
}

func (t *Testing) Cleanup(cleaner func()) {
	// Need to do the inefficient way to match golang testing behavior
	t.cleaners = append([]func(){cleaner}, t.cleaners...)
}

func (t *Testing) Error(args ...any) {
	t.mu.Lock()
	fmt.Fprint(t.buffer, args...)
	fmt.Fprintln(t.buffer)
	if len(args) == 1 {
		if err, ok := args[0].(error); ok {
			t.Errors = append(t.Errors, err)
		}
	}
	t.mu.Unlock()
	t.setStatus(Warning)
}

func (t *Testing) Errorf(format string, args ...any) {
	t.mu.Lock()
	fmt.Fprintf(t.buffer, format, args...)
	fmt.Fprintln(t.buffer)
	if len(args) == 1 {
		if err, ok := args[0].(error); ok {
			t.Errors = append(t.Errors, err)
		}
	}
	t.mu.Unlock()
	t.setStatus(Warning)
}

func (t *Testing) Fail() {
	t.setStatus(Failure)
}

func (t *Testing) FailNow() {
	t.setStatus(Failure)
	t.done <- true
	runtime.Goexit()
}

func (t *Testing) Failed() bool {
	return t.Status == Failure
}

func (t *Testing) Fatal(args ...any) {
	t.mu.Lock()
	fmt.Fprint(t.buffer, args...)
	fmt.Fprintln(t.buffer)
	if len(args) == 1 {
		if err, ok := args[0].(error); ok {
			t.Errors = append(t.Errors, err)
		}
	}
	t.mu.Unlock()
	t.FailNow()
}

func (t *Testing) Fatalf(format string, args ...any) {
	t.mu.Lock()
	fmt.Fprintf(t.buffer, format, args...)
	fmt.Fprintln(t.buffer)
	if len(args) == 1 {
		if err, ok := args[0].(error); ok {
			t.Errors = append(t.Errors, err)
		}
	}
	t.mu.Unlock()
	t.FailNow()
}

func (t *Testing) Helper() {
	// No-op for now
}

func (t *Testing) Log(args ...any) {
	t.mu.Lock()
	fmt.Fprint(t.buffer, args...)
	fmt.Fprintln(t.buffer)
	t.mu.Unlock()
}

func (t *Testing) Logf(format string, args ...any) {
	t.mu.Lock()
	fmt.Fprintf(t.buffer, format, args...)
	fmt.Fprintln(t.buffer)
	t.mu.Unlock()
}

func (t *Testing) Name() string {
	return t.name
}

func (t *Testing) Parallel() {
	if t.parallel {
		return
	}
	t.done <- false
	runtime.Goexit()
}

func (t *Testing) Run(name string, f func(t *Testing)) bool {
	tC := t.makeChild(name)
	f(tC)
	return tC.Status < Warning
}

func (t *Testing) Setenv(key, value string) {
	// No-op for now
}

func (t *Testing) Chdir(dir string) {
	// No-op for now
}

func (t *Testing) Skip(args ...any) {
	t.setSkipped()
}

func (t *Testing) SkipNow() {
	t.setSkipped()
	t.done <- true
	runtime.Goexit()
}

func (t *Testing) Skipf(format string, args ...any) {
	// No-op for now
}

func (t *Testing) Skipped() bool {
	return t.Status == Skipped
}

func (t *Testing) TempDir() string {
	return os.TempDir()
}

func (t *Testing) Context() context.Context {
	// No-op for now
	return context.Background()
}

func (t *Testing) Output() io.Writer {
	return t.buffer
}

func (t *Testing) setStatus(status Status) {
	t.mu.Lock()
	if t.Status < status {
		t.Status = status
	}
	if t.Case != nil && t.Case.Status < status {
		t.Case.Status = status
	}
	parent := t.parent
	t.mu.Unlock()
	if parent != nil {
		parent.setStatus(status)
	}
}

func (t *Testing) setSkipped() {
	t.mu.Lock()
	t.Status = Skipped
	if t.Case != nil {
		t.Case.Status = Skipped
	}
	t.mu.Unlock()
}

func (t *Testing) makeChild(name string) *Testing {
	ret := &Testing{
		name:   t.Name() + "/" + name,
		parent: t,
		done:   make(chan bool),
		buffer: &bytes.Buffer{},
	}
	t.mu.Lock()
	t.children = append(t.children, ret)
	t.mu.Unlock()
	return ret
}
