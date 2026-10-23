/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package testing

import (
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing/csdl"
	"github.com/DMTF/redfishRepoTest/src/testing/dsp2046"
	"github.com/DMTF/redfishRepoTest/src/testing/jsonschema"
	"github.com/DMTF/redfishRepoTest/src/testing/markdown"
	"github.com/DMTF/redfishRepoTest/src/testing/mockup"
	"github.com/DMTF/redfishRepoTest/src/testing/registry"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/units"
)

func addList(main *testsuite.TestMain, name string, cfg *config.Config) *testsuite.List {
	list := main.AddList(name)
	list.Pool = cfg.WorkerPool
	list.AutoFix = cfg.AutoFix
	return list
}

func CreateTestsFromConfig(cfg *config.Config) (*testsuite.TestMain, error) {
	unitsUtil, err := units.Load()
	if err != nil {
		return nil, err
	}
	cfg.CompileRegexes()
	main := testsuite.NewTestMain()
	csdlList := addList(main, "CSDL", cfg)
	err = csdl.CreateTestsFromConfig(cfg, csdlList, unitsUtil)
	if err != nil {
		return nil, err
	}
	mockupList := addList(main, "Mockups", cfg)
	mockupList.DependsOn(csdlList)
	err = mockup.CreateTestsFromConfig(cfg, mockupList)
	if err != nil {
		return nil, err
	}
	dsp2046List := addList(main, "DSP2046", cfg)
	dsp2046List.DependsOn(csdlList)
	err = dsp2046.CreateTestsFromConfig(cfg, dsp2046List)
	if err != nil {
		return nil, err
	}
	jsonSchemaList := addList(main, "JSON Schema", cfg)
	err = jsonschema.CreateTestsFromConfig(cfg, jsonSchemaList)
	if err != nil {
		return nil, err
	}
	markdownList := addList(main, "Markdown", cfg)
	err = markdown.CreateTestsFromConfig(cfg, markdownList)
	if err != nil {
		return nil, err
	}
	registryList := addList(main, "Message Registry", cfg)
	err = registry.CreateTestsFromConfig(cfg, registryList)
	if err != nil {
		return nil, err
	}
	return main, nil
}
