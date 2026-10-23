/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package utils

import (
	"fmt"
	"os"
	"path/filepath"
)

// OpenFile opens a file, first trying the provided path, then trying the same path relative to the executable.
func OpenFile(filePath string) (*os.File, error) {
	//nolint:gosec // The whole point of this function is to open specified files.
	file, err := os.Open(filePath)
	if err != nil {
		var ex string
		ex, err = os.Executable()
		if err != nil {
			return nil, fmt.Errorf("could not open file %s: could not locate executable: %w", filePath, err)
		}
		dir := filepath.Dir(ex)
		//nolint:gosec // The whole point of this function is to open files relative to the executable.
		file, err = os.Open(dir + "/" + filePath)
		if err != nil {
			return nil, fmt.Errorf("could not open file %s: %w", filePath, err)
		}
	}
	return file, err
}

// DoesFileExist checks if a file exists, first trying the provided path,
// then trying the same path relative to the executable.
func DoesFileExist(filePath string) bool {
	_, err := os.Stat(filePath)
	if err != nil {
		ex, err2 := os.Executable()
		if err2 == nil {
			dir := filepath.Dir(ex)
			_, err = os.Stat(dir + "/" + filePath)
		} else {
			err = err2
		}
	}
	return err == nil
}
