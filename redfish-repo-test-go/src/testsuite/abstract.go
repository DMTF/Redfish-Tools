/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testsuite

// Basically implements testing.TB, but the interface has private methods that we can't implement.
// This allows us to write a function that would work with either *testing.T or *Testing.
type T interface {
	Cleanup(f func())
	// Run(name string, f func(t T)) bool // Leaving this out since the underlying type changes.
}
