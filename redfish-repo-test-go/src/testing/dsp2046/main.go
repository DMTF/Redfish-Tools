/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package dsp2046

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"slices"
	"strings"

	"github.com/pboyd04/gocsdl/pkg/csdl"
	"github.com/DMTF/redfishRepoTest/src"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
)

//nolint:cyclop,funlen,gocognit // Builds two related test closures from the same parsed CSDL state.
func CreateTestsFromConfig(cfg *config.Config, list *testsuite.List) error {
	// For each CSDL file, find all Entity types and ensure there is an
	// example file for them in DSP2046-examples folder
	// For each CSDL file, find all Actions and ensure there is an example
	// file for their request and response in DSP2046-examples folder
	if cfg.CSDLCache == nil {
		// Need to parse/seed CSDL cache first if DSP2046 tests are run standalone.
		log.Printf("Running only DSP2046 tests not implemented yet.\n")
		return nil
	}

	list.AddSetup(func() {
		if len(list.Suites) > 0 {
			return
		}

		searcher, err := makeSearcherFromCache(cfg.CSDLCache)
		if err != nil {
			log.Printf("Unable to create DSP2046 searcher from CSDL cache: %v", err)
			return
		}

		examplesDir := filepath.Join(cfg.MockupDirectory, "DSP2046-examples")
		exampleFiles, err := loadDSP2046ExampleFiles(examplesDir)
		if err != nil {
			log.Printf("Unable to load DSP2046 examples from %s: %v", examplesDir, err)
			return
		}

		csdlFiles := searcher.GetFiles()
		fileNames := make([]string, 0, len(csdlFiles))
		for fileName := range csdlFiles {
			if !shouldIncludeCSDLFile(cfg.SingleFile, fileName) {
				continue
			}
			fileNames = append(fileNames, fileName)
		}
		slices.Sort(fileNames)

		for _, fileName := range fileNames {
			edmx := csdlFiles[fileName]
			entityTypes := collectEntityTypes(edmx)
			actions := collectActions(edmx)

			suite := list.AddSuite(fileName)
			suite.AddTest("Entities have DSP2046 examples", func(t *testsuite.Testing) {
				for _, entityType := range entityTypes {
					if hasEntityExample(entityType, exampleFiles) {
						continue
					}
					msg := fmt.Sprintf(
						"Entity type %s does not have an example in %s",
						entityType, examplesDir,
					)
					t.Error(src.NewError(src.SeverityWarning, msg))
				}
			})
			suite.AddTest("Actions have DSP2046 request and response examples", func(t *testsuite.Testing) {
				for _, action := range actions {
					hasRequest, hasResponse := hasActionExamples(action.Name, exampleFiles)
					if action.NeedsRequest && !hasRequest {
						msg := fmt.Sprintf(
							"Action %s does not have a request example in %s",
							action.Name, examplesDir,
						)
						t.Error(src.NewError(src.SeverityWarning, msg))
					}
					if action.HasReturnType && !hasResponse {
						msg := fmt.Sprintf(
							"Action %s does not have a response example in %s",
							action.Name, examplesDir,
						)
						t.Error(src.NewError(src.SeverityWarning, msg))
					}
					if !action.HasReturnType && hasResponse {
						msg := fmt.Sprintf(
							"Action %s has response examples in %s but does not define a ReturnType",
							action.Name, examplesDir,
						)
						t.Error(src.NewError(src.SeverityWarning, msg))
					}
				}
			})
		}
	})

	return nil
}

type exampleFile struct {
	Path      string
	Content   string
	baseLower string // pre-computed strings.ToLower(filepath.Base(Path))
}

func newExampleFile(path, content string) exampleFile {
	return exampleFile{
		Path:      path,
		Content:   content,
		baseLower: strings.ToLower(filepath.Base(path)),
	}
}

type actionInfo struct {
	Name          string
	HasReturnType bool
	NeedsRequest  bool
}

func makeSearcherFromCache(cache csdl.ExternalCache) (*csdl.Searcher, error) {
	parser := csdl.NewParserFromCache(cache)
	_, err := parser.Parse(csdl.WithSkipFileRead())
	if err != nil {
		return nil, err
	}
	return csdl.NewSearcher(parser), nil
}

func shouldIncludeCSDLFile(singleFile string, fileName string) bool {
	if singleFile == "" {
		return true
	}
	if !strings.HasSuffix(singleFile, ".xml") {
		return false
	}
	target := strings.TrimSuffix(filepath.Base(singleFile), ".xml")
	current := strings.TrimSuffix(filepath.Base(fileName), ".xml")
	return current == target
}

func loadDSP2046ExampleFiles(examplesDir string) ([]exampleFile, error) {
	entries := make([]exampleFile, 0)
	err := filepath.WalkDir(examplesDir, func(path string, d os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if d.IsDir() || filepath.Ext(path) != ".json" {
			return nil
		}
		content, err := os.ReadFile(path) //nolint:gosec
		if err != nil {
			return err
		}
		entries = append(entries, newExampleFile(path, string(content)))
		return nil
	})
	if err != nil {
		return nil, err
	}
	slices.SortFunc(entries, func(a, b exampleFile) int {
		return strings.Compare(a.Path, b.Path)
	})
	return entries, nil
}

func collectEntityTypes(edmx *csdl.Edmx) []string {
	entityIndex := make(map[string]*csdl.EntityType)
	for _, schema := range edmx.DataServices.Schema {
		for _, entity := range schema.EntityType {
			fullName := schema.Namespace + "." + entity.Name
			entityIndex[fullName] = entity
			unversionedNamespace, _, _ := strings.Cut(schema.Namespace, ".")
			entityIndex[unversionedNamespace+"."+entity.Name] = entity
		}
	}

	derivesCache := make(map[string]bool)
	entityTypes := make([]string, 0)
	for _, schema := range edmx.DataServices.Schema {
		for _, entity := range schema.EntityType {
			if strings.HasSuffix(entity.Name, "Collection") {
				// We don't need examples of collections...
				continue
			}
			if entity.Abstract {
				// We don't need examples of abstract entities we can't produce...
				continue
			}
			fullName := schema.Namespace + "." + entity.Name
			if derivesFromReferenceableMember(fullName, entityIndex, derivesCache, map[string]struct{}{}) {
				// We don't need examples of entities deriving from Resource.v1_0_0.ReferenceableMember.
				continue
			}
			entityTypes = append(entityTypes, fullName)
		}
	}
	return entityTypes
}

func derivesFromReferenceableMember(
	entityType string,
	entityIndex map[string]*csdl.EntityType,
	cache map[string]bool,
	visiting map[string]struct{},
) bool {
	const referenceableMember = "Resource.v1_0_0.ReferenceableMember"

	if derived, ok := cache[entityType]; ok {
		return derived
	}
	if _, seen := visiting[entityType]; seen {
		cache[entityType] = false
		return false
	}
	entity, ok := entityIndex[entityType]
	if !ok {
		cache[entityType] = false
		return false
	}
	baseType := entity.BaseType
	if baseType == "" {
		cache[entityType] = false
		return false
	}
	if baseType == referenceableMember {
		cache[entityType] = true
		return true
	}

	visiting[entityType] = struct{}{}
	defer delete(visiting, entityType)

	candidates := []string{baseType}
	if unversionedBaseType := getUnversionedEntityType(baseType); unversionedBaseType != baseType {
		candidates = append(candidates, unversionedBaseType)
	}
	for _, candidate := range candidates {
		if _, ok := entityIndex[candidate]; !ok {
			continue
		}
		if derivesFromReferenceableMember(candidate, entityIndex, cache, visiting) {
			cache[entityType] = true
			return true
		}
	}

	cache[entityType] = false
	return false
}

func collectActions(edmx *csdl.Edmx) []actionInfo {
	actions := make([]actionInfo, 0)
	for _, schema := range edmx.DataServices.Schema {
		for _, action := range schema.Action {
			actions = append(actions, actionInfo{
				Name:          fmt.Sprintf("%s.%s", schema.Namespace, action.Name),
				HasReturnType: action.ReturnType != nil,
				NeedsRequest:  actionNeedsRequest(action),
			})
		}
	}
	return actions
}

func actionNeedsRequest(action *csdl.Action) bool {
	return len(action.Parameter) != 1
}

// Filename format is unversioned entityType-v1-example.json
//
//nolint:cyclop
func hasEntityExample(entityType string, files []exampleFile) bool {
	versionedNeedle := "#" + entityType
	unversionedEntityType := getUnversionedEntityType(entityType)
	unversionedNeedle := "#" + unversionedEntityType
	entityName := getEntityName(entityType)
	fileNameNeedles := []string{
		strings.ToLower(strings.ReplaceAll(entityType, ".", "-")),
		strings.ToLower(strings.ReplaceAll(unversionedEntityType, ".", "-")),
		strings.ToLower(entityName),
	}
	entityNameDash := ""
	if entityName != "" {
		entityNameDash = strings.ToLower(entityName) + "-"
	}
	for _, file := range files {
		if strings.Contains(file.Content, versionedNeedle) || strings.Contains(file.Content, unversionedNeedle) {
			return true
		}
		if !strings.Contains(file.baseLower, "example") {
			continue
		}
		for _, needle := range fileNameNeedles {
			if needle == "" {
				continue
			}
			if strings.Contains(file.baseLower, needle) {
				return true
			}
		}
		if entityNameDash != "" && strings.Contains(file.baseLower, entityNameDash) {
			return true
		}
	}
	return false
}

func getUnversionedEntityType(entityType string) string {
	if entityType == "" {
		return ""
	}
	entityName := getEntityName(entityType)
	namespace := strings.TrimSuffix(entityType, "."+entityName)
	if namespace == entityType {
		return entityType
	}
	if dot := strings.Index(namespace, "."); dot != -1 {
		namespace = namespace[:dot]
	}
	if namespace == "" || entityName == "" {
		return entityType
	}
	return namespace + "." + entityName
}

func getEntityName(entityType string) string {
	if lastDot := strings.LastIndex(entityType, "."); lastDot != -1 {
		return entityType[lastDot+1:]
	}
	return entityType
}

func hasActionExamples(action string, files []exampleFile) (bool, bool) {
	schemaName := action
	actionName := action
	if lastDot := strings.LastIndex(action, "."); lastDot != -1 {
		schemaName = action[:lastDot]
		actionName = action[lastDot+1:]
	}
	if strings.Contains(schemaName, ".") {
		schemaName, _, _ = strings.Cut(schemaName, ".")
	}
	unversionedAction := schemaName + "." + actionName
	actionNameLower := strings.ToLower(actionName)

	hasRequest := false
	hasResponse := false
	for _, file := range files {
		containsAction := strings.Contains(file.Content, action) || strings.Contains(file.Content, unversionedAction)
		if !containsAction && !strings.Contains(file.baseLower, actionNameLower) {
			continue
		}
		if strings.Contains(file.baseLower, "request") {
			hasRequest = true
		}
		if strings.Contains(file.baseLower, "response") {
			hasResponse = true
		}
	}
	return hasRequest, hasResponse
}
