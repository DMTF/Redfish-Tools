/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package main

import (
	"fmt"
	"os"

	"github.com/DMTF/redfishRepoTest/src/units/ucum"
)

func main() {
	err := ucum.MakeLocalCache()
	if err != nil {
		panic(err)
	}
	fmt.Fprintf(os.Stderr, "Cache created successfully!\n")
}
