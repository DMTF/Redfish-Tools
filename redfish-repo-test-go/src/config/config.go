/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package config

import (
	"encoding/json"
	"path/filepath"
	"regexp"
	"strings"
	"sync"

	"github.com/DMTF/redfishRepoTest/src/utils"
	"github.com/DMTF/redfishRepoTest/src/workerpool"
	"github.com/pboyd04/gocsdl/pkg/csdl"
)

//nolint:lll // Just tags that repeat each other to handle serialization.
type Config struct {
	SingleFile                           string                                    `json:"-" yaml:"-"`
	CSDLDirectory                        string                                    `json:"csdlDir" yaml:"csdlDir" mapstructure:"csdldir"`
	MockupDirectory                      string                                    `json:"mockupDir" yaml:"mockupDir" mapstructure:"mockupdir"`
	JSONSchemaDirectory                  string                                    `json:"jsonSchemaDir" yaml:"jsonSchemaDir" mapstructure:"jsonschemadir"`
	MarkdownGlobs                        []string                                  `json:"markdownGlobs" yaml:"markdownGlobs" mapstructure:"markdownglobs"`
	MessageRegistryDirectory             string                                    `json:"messageRegistryDir" yaml:"messageRegistryDir" mapstructure:"messageregistrydir"`
	AllowLists                           AllowLists                                `json:"allow" yaml:"allow" mapstructure:"allow"`
	ExternalSchemas                      []string                                  `json:"externalSchemas" yaml:"externalSchemas" mapstructure:"externalschemas"`
	PrivilegeRegistryGlob                string                                    `json:"privilegeRegistryGlob" yaml:"privilegeRegistryGlob" mapstructure:"privilegeregistryglob"`
	PublishedVersionsURI                 string                                    `json:"publishedVersionsUri" yaml:"publishedVersionsUri" mapstructure:"publishedversionsuri"`
	RequireAllEntitiesToHaveDescriptions bool                                      `json:"requireAllEntitiesToHaveDescriptions" yaml:"requireAllEntitiesToHaveDescriptions" mapstructure:"requirealldescriptions"`
	IncludePedanticTests                 bool                                      `json:"includePedanticTests" yaml:"includePedanticTests" mapstructure:"includepedantictests"`
	Copyright                            string                                    `json:"copyright" yaml:"copyright" mapstructure:"copyright"`
	AutoFix                              bool                                      `json:"-" yaml:"-" mapstructure:"-"`
	PublishedVersions                    map[string]*utils.RedfishNamespaceVersion `json:"-" yaml:"-"`
	CSDLCache                            csdl.ExternalCache                        `json:"-" yaml:"-"`
	WorkerPool                           *workerpool.Pool                          `json:"-" yaml:"-"`
	IOWorkerPool                         *workerpool.Pool                          `json:"-" yaml:"-"`

	privilegeRegCache map[string]any
	copyrightRegEx    *regexp.Regexp
}

//nolint:lll // Just tags that repeat each other to handle serialization.
type AllowLists struct {
	PluralEntityPatterns         []string `json:"pluralEntity" yaml:"pluralEntity" mapstructure:"pluralentity"`
	PluralSchemaPatterns         []string `json:"pluralSchema" yaml:"pluralSchema" mapstructure:"pluralschema"`
	PropertiesWithIncorrectUnits []string `json:"propertiesWithIncorrectUnits" yaml:"propertiesWithIncorrectUnits" mapstructure:"propertieswithincorrectunits"`
	NonPascalEnums               []string `json:"nonPascalEnums" yaml:"nonPascalEnums" mapstructure:"nonpascalenums"`
	NonPascalProperties          []string `json:"nonPascalProperties" yaml:"nonPascalProperties" mapstructure:"nonpascalproperties"`
	NoActionsAllowed             []string `json:"noActions" yaml:"noActions" mapstructure:"noactions"`
	NoReleaseTermSchemas         []string `json:"noReleaseTermSchemas" yaml:"noReleaseTermSchemas" mapstructure:"noreleasetermschemas"`
	UnknownTypeReferences        []string `json:"unknownTypeReferences" yaml:"unknownTypeReferences" mapstructure:"unknowntypereferences"`
	OtherValidURIPrefixes        []string `json:"otherValidURIPrefixes" yaml:"otherValidURIPrefixes" mapstructure:"othervaliduriprefixes"`
	NoURISchemas                 []string `json:"noURISchemas" yaml:"noURISchemas" mapstructure:"nourischemas"`
	AllowedBareSchemas           []string `json:"allowedBareSchemas" yaml:"allowedBareSchemas" mapstructure:"allowedbareschemas"`
	NoCopyrightPaths             []string `json:"noCopyrightPaths" yaml:"noCopyrightPaths" mapstructure:"nocopyrightpaths"`
	AllowedNoExplorerMockups     []string `json:"allowedNoExplorerMockups" yaml:"allowedNoExplorerMockups" mapstructure:"allowednoexplorermockups"`
	pluralEntityPatterns         []*regexp.Regexp
	pluralSchemaPatterns         []*regexp.Regexp
	propertiesWithIncorrectUnits []*regexp.Regexp
	nonPascalEnums               []*regexp.Regexp
	nonPascalProperties          []*regexp.Regexp
	noReleaseTermSchemas         []*regexp.Regexp
	unknownTypeReferences        []*regexp.Regexp
	patternEditOnce              sync.Once
}

func (c *Config) AddPrefixDir(prefix string) {
	c.CSDLDirectory = filepath.Join(prefix, c.CSDLDirectory)
	c.PrivilegeRegistryGlob = filepath.Join(prefix, c.PrivilegeRegistryGlob)
	c.MockupDirectory = filepath.Join(prefix, c.MockupDirectory)
	c.JSONSchemaDirectory = filepath.Join(prefix, c.JSONSchemaDirectory)
	c.MessageRegistryDirectory = filepath.Join(prefix, c.MessageRegistryDirectory)
	for i, pattern := range c.MarkdownGlobs {
		if pattern == "" {
			continue
		}
		c.MarkdownGlobs[i] = filepath.Join(prefix, pattern)
	}
	for i, path := range c.AllowLists.NoCopyrightPaths {
		c.AllowLists.NoCopyrightPaths[i] = filepath.Join(prefix, path)
	}
}

func (c *Config) GetPrivilegeRegistry() map[string]any {
	if c.privilegeRegCache != nil {
		return c.privilegeRegCache
	}
	if c.PrivilegeRegistryGlob == "" {
		return nil
	}
	matches, err := filepath.Glob(c.PrivilegeRegistryGlob)
	if err != nil || len(matches) == 0 {
		return nil
	}
	fileName := matches[0]
	for _, match := range matches[1:] {
		if strings.Compare(match, fileName) > 0 {
			fileName = match
		}
	}
	if fileName == "" {
		return nil
	}
	file, err := utils.OpenFile(fileName)
	if err != nil {
		return nil
	}
	defer func() {
		_ = file.Close()
	}()
	var privs map[string]any
	dec := json.NewDecoder(file)
	err = dec.Decode(&privs)
	if err != nil {
		return nil
	}
	c.privilegeRegCache = privs
	return privs
}

func (c *Config) CompileRegexes() {
	c.AllowLists.patternEditOnce.Do(func() {
		c.GetCopyrightRegEx()
		c.AllowLists.CompileRegexes()
	})
}

func (c *Config) GetCopyrightRegEx() *regexp.Regexp {
	if c.copyrightRegEx != nil {
		return c.copyrightRegEx
	}
	c.copyrightRegEx = regexp.MustCompile(c.Copyright)
	return c.copyrightRegEx
}

func (a *AllowLists) CompileRegexes() {
	a.pluralEntityPatterns = make([]*regexp.Regexp, len(a.PluralEntityPatterns))
	a.pluralSchemaPatterns = make([]*regexp.Regexp, len(a.PluralSchemaPatterns))
	a.propertiesWithIncorrectUnits = make([]*regexp.Regexp, len(a.PropertiesWithIncorrectUnits))
	a.nonPascalEnums = make([]*regexp.Regexp, len(a.NonPascalEnums))
	a.nonPascalProperties = make([]*regexp.Regexp, len(a.NonPascalProperties))
	a.noReleaseTermSchemas = make([]*regexp.Regexp, len(a.NoReleaseTermSchemas))
	a.unknownTypeReferences = make([]*regexp.Regexp, len(a.UnknownTypeReferences))

	for i, pattern := range a.PluralEntityPatterns {
		a.pluralEntityPatterns[i] = regexp.MustCompile(pattern)
	}
	for i, pattern := range a.PluralSchemaPatterns {
		a.pluralSchemaPatterns[i] = regexp.MustCompile(pattern)
	}
	for i, pattern := range a.PropertiesWithIncorrectUnits {
		a.propertiesWithIncorrectUnits[i] = regexp.MustCompile(pattern)
	}
	for i, pattern := range a.NonPascalEnums {
		a.nonPascalEnums[i] = regexp.MustCompile(pattern)
	}
	for i, pattern := range a.NonPascalProperties {
		a.nonPascalProperties[i] = regexp.MustCompile(pattern)
	}
	for i, pattern := range a.NoReleaseTermSchemas {
		a.noReleaseTermSchemas[i] = regexp.MustCompile(pattern)
	}
	for i, pattern := range a.UnknownTypeReferences {
		a.unknownTypeReferences[i] = regexp.MustCompile(pattern)
	}
}

func (a *AllowLists) GetPluralEntityPatterns() []*regexp.Regexp {
	a.patternEditOnce.Do(func() {
		a.CompileRegexes()
	})
	return a.pluralEntityPatterns
}

func (a *AllowLists) GetPluralSchemaPatterns() []*regexp.Regexp {
	a.patternEditOnce.Do(func() {
		a.CompileRegexes()
	})
	return a.pluralSchemaPatterns
}

func (a *AllowLists) GetPropertiesWithIncorrectUnits() []*regexp.Regexp {
	a.patternEditOnce.Do(func() {
		a.CompileRegexes()
	})
	return a.propertiesWithIncorrectUnits
}

func (a *AllowLists) GetNonPascalEnums() []*regexp.Regexp {
	a.patternEditOnce.Do(func() {
		a.CompileRegexes()
	})
	return a.nonPascalEnums
}

func (a *AllowLists) GetNonPascalProperties() []*regexp.Regexp {
	a.patternEditOnce.Do(func() {
		a.CompileRegexes()
	})
	return a.nonPascalProperties
}

func (a *AllowLists) GetNoReleaseTermSchemas() []*regexp.Regexp {
	a.patternEditOnce.Do(func() {
		a.CompileRegexes()
	})
	return a.noReleaseTermSchemas
}

func (a *AllowLists) GetUnknownTypeReferences() []*regexp.Regexp {
	a.patternEditOnce.Do(func() {
		a.CompileRegexes()
	})
	return a.unknownTypeReferences
}
