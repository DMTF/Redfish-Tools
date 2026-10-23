/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testsuite

type Status int

const (
	Skipped Status = -2
	Pending Status = -1
)

const (
	Success Status = iota
	Warning
	Failure
)

func (s Status) String() string {
	switch s {
	case Pending:
		return "..."
	case Skipped:
		return "\u2349"
	case Success:
		return "\u2705"
	case Failure:
		return "\u274C"
	case Warning:
		return "\u26A0"
	default:
		return "Unknown status"
	}
}
