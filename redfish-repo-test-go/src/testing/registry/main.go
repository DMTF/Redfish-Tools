/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package registry

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

func CreateTestsFromConfig(cfg *config.Config, list *testsuite.List) error {
	registryDir := cfg.MessageRegistryDirectory
	if registryDir == "" {
		return nil
	}
	return CreateTestsForDirectory(registryDir, list)
}

func CreateTestsForDirectory(dir string, list *testsuite.List) error {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return err
	}

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		if !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}
		if strings.Contains(entry.Name(), "PrivilegeRegistry") {
			continue
		}
		msgReg := NewMessageRegistry(filepath.Join(dir, entry.Name()))
		suite := list.AddSuite(msgReg.Filename)
		suite.AddTest("Valid UTF8 and JSON", msgReg.ValidTest)
		suite.AddTest("Filename and Data match", msgReg.FilenameMatch)
		suite.Cleanup(func(_ *testsuite.Suite) {
			msgReg.Content = nil
			msgReg.JSON = nil
		})
	}

	return nil
}
