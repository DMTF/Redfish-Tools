/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package main

import (
	"bytes"
	_ "embed"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"runtime/pprof"
	"slices"
	"strings"

	"github.com/DMTF/redfishRepoTest/src"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testing"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/DMTF/redfishRepoTest/src/utils"
	"github.com/DMTF/redfishRepoTest/src/workerpool"
	"github.com/spf13/viper"
)

//go:embed config.yaml
var defaultConfigYAML []byte

type OutputMode int

const (
	Verbose OutputMode = iota
	GCC
	Go
)

type runtimeConfig struct {
	outputMode        OutputMode
	additionalConfigs []string
	pedantic          bool
	autoFix           bool
	workerMultiplier  float64
	onExit            func()
	rootDir           string
}

func main() {
	runtimeConfig, extraArgs := parseArgs()
	cfg := loadConfig(runtimeConfig)
	published, err := utils.GetPublishedSchemaList(cfg.PublishedVersionsURI)
	if err != nil {
		fmt.Fprintf(os.Stderr,
			"Warning: Could not get published schema list. Test will be skipped! %v", err)
	}
	cfg.PublishedVersions = published
	if len(extraArgs) > 0 {
		// This should be either a directory or a file...
		info, err := os.Stat(extraArgs[0])
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error stating file: %v\n", err)
			os.Exit(1)
		}
		if info.IsDir() {
			cfg.AddPrefixDir(extraArgs[0])
		} else {
			cfg.CSDLDirectory = filepath.Dir(extraArgs[0]) // Override the config in this case
			cfg.SingleFile = extraArgs[0]
		}
	}
	if runtimeConfig.rootDir != "" {
		// Alter the config to use the root directory
		cfg.AddPrefixDir(runtimeConfig.rootDir)
	}
	main, err := testing.CreateTestsFromConfig(cfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating tests from config: %v\n", err)
		os.Exit(1)
	}
	rc := main.Run()
	printResults(runtimeConfig, main)
	runtimeConfig.onExit()
	os.Exit(rc)
}

//nolint:cyclop,gocognit,nestif // Output modes require distinct formatting and sorting paths.
func printResults(runtimeConfig *runtimeConfig, main *testsuite.TestMain) {
	switch runtimeConfig.outputMode {
	case Verbose:
		main.PrintStatus(os.Stdout)
		if len(main.Errors) > 0 {
			_, _ = fmt.Fprintln(os.Stdout, "Errors:")
			slices.SortFunc(main.Errors, func(a, b error) int {
				var fileSevA, fileSevB src.SeverityFileLineError
				okA := errors.As(a, &fileSevA)
				okB := errors.As(b, &fileSevB)
				if okA && okB {
					ret := strings.Compare(fileSevA.FileName(), fileSevB.FileName())
					if ret != 0 {
						return ret
					}
					if fileSevA.Line() < fileSevB.Line() {
						return -1
					}
					if fileSevA.Line() > fileSevB.Line() {
						return 1
					}
					return 0
				}
				return strings.Compare(a.Error(), b.Error())
			})
			for _, err := range main.Errors {
				_, _ = fmt.Fprintln(os.Stdout, err)
			}
			_, _ = fmt.Fprintf(os.Stdout, "\nTotal errors: %d\n", len(main.Errors))
		}
	case GCC, Go:
		for _, err := range main.Errors {
			if formatter, ok := err.(src.Formatable); ok {
				_, _ = fmt.Fprintln(os.Stdout,
					formatter.Format(src.OutputFormat(runtimeConfig.outputMode)))
				continue
			}
		}
	}
}

//nolint:cyclop // parseArgs handles many CLI flags in one place.
func parseArgs() (*runtimeConfig, []string) {
	defers := []func(){}
	ret := &runtimeConfig{
		outputMode:        Verbose,
		additionalConfigs: []string{},
		onExit: func() {
			for _, d := range defers {
				d()
			}
		},
		rootDir: "",
	}
	gccMode := flag.Bool("gcc", false, "Use GCC-style error messages")
	goMode := flag.Bool("go", false, "Use Go-style error messages")
	configFiles := flag.String("config", "", "Extra config file(s) to load (comma-separated)")
	cpuProfile := flag.String("cpuprofile", "", "Write cpu profile to file")
	memProfile := flag.String("memprofile", "", "Write memory profile to file")
	pendantic := flag.Bool("pedantic", false, "Run pedantic tests")
	autoFix := flag.Bool("auto-fix", false, "Automatically fix issues where possible")
	root := flag.String("root", "", "Root directory for tests")
	workers := flag.Float64("workers", workerpool.DefaultMultiplier,
		"Worker pool CPU multiplier (e.g. 2.0 = 2x NumCPU workers)")
	flag.Parse()
	if *gccMode {
		ret.outputMode = GCC
	}
	if *goMode {
		ret.outputMode = Go
	}
	if *configFiles != "" {
		ret.additionalConfigs = strings.Split(*configFiles, ",")
	}
	if *cpuProfile != "" {
		f, err := os.Create(*cpuProfile)
		if err != nil {
			panic(err)
		}
		err = pprof.StartCPUProfile(f)
		if err != nil {
			panic(err)
		}
		defers = append(defers, func() {
			pprof.StopCPUProfile()
			_ = f.Close()
		})
	}
	if *memProfile != "" {
		defers = append(defers, func() {
			createMemProfile(*memProfile)
		})
	}
	if *configFiles != "" {
		ret.additionalConfigs = append(ret.additionalConfigs, strings.Split(*configFiles, ",")...)
	}
	if *root != "" {
		ret.rootDir = *root
	}
	ret.pedantic = *pendantic
	ret.autoFix = *autoFix
	ret.workerMultiplier = *workers
	return ret, flag.Args()
}

func findConfigFile(cfg *viper.Viper, name string) (string, error) {
	cfg.SetConfigName(name)
	err := cfg.ReadInConfig()
	if err != nil {
		return "", err
	}
	return cfg.ConfigFileUsed(), nil
}

func addConfigSearchPaths(cfg *viper.Viper) {
	cfg.AddConfigPath(".")
	cfg.AddConfigPath("./config")
	cfg.AddConfigPath("./cmd/repotest")
	if execPath, err := os.Executable(); err == nil {
		binaryDir := filepath.Dir(execPath)
		cfg.AddConfigPath(binaryDir)
		cfg.AddConfigPath(filepath.Join(binaryDir, "config"))
	}
}

func findNamedConfig(name string) (string, error) {
	tempCfg := viper.New()
	addConfigSearchPaths(tempCfg)
	return findConfigFile(tempCfg, name)
}

func loadConfig(rtc *runtimeConfig) *config.Config {
	cfg := viper.New()
	cfg.SetConfigType("yaml")
	cfg.SetDefault("publishedversionsuri", "https://redfish.dmtf.org/schemas/v1")

	mergeDefaultAndBaseConfig(cfg)
	baseConfig := unmarshalViperConfig(cfg)
	additionalConfigPaths := mergeAdditionalConfigs(cfg, rtc.additionalConfigs)
	finalConfig := unmarshalViperConfig(cfg)
	mergeAllowLists(&finalConfig.AllowLists, &baseConfig.AllowLists)
	for _, configPath := range additionalConfigPaths {
		extraAllow, err := loadAllowLists(configPath)
		if err != nil {
			panic(err)
		}
		mergeAllowLists(&finalConfig.AllowLists, extraAllow)
	}

	if rtc.pedantic {
		finalConfig.IncludePedanticTests = true
	}
	finalConfig.AutoFix = rtc.autoFix
	finalConfig.WorkerPool = workerpool.NewFromMultiplier(rtc.workerMultiplier)
	finalConfig.IOWorkerPool = workerpool.NewFromMultiplier(rtc.workerMultiplier)
	return finalConfig
}

// mergeDefaultAndBaseConfig merges the embedded default config and any
// overriding "config" file into the supplied viper instance.
func mergeDefaultAndBaseConfig(cfg *viper.Viper) {
	if err := cfg.MergeConfig(bytes.NewReader(defaultConfigYAML)); err != nil {
		panic(err)
	}
	if configPath, err := findNamedConfig("config"); err == nil {
		cfg.SetConfigFile(configPath)
		if err := cfg.MergeInConfig(); err != nil {
			panic(err)
		}
	} else if !errors.As(err, &viper.ConfigFileNotFoundError{}) {
		panic(err)
	}
}

// mergeAdditionalConfigs merges each additional -config file into the viper
// instance and returns the resolved paths to those files.
func mergeAdditionalConfigs(cfg *viper.Viper, additionalConfigs []string) []string {
	paths := make([]string, 0, len(additionalConfigs))
	for _, configFile := range additionalConfigs {
		name := strings.TrimSuffix(configFile, filepath.Ext(configFile))
		configPath, err := findNamedConfig(name)
		if err != nil {
			panic(err)
		}
		paths = append(paths, configPath)

		cfg.SetConfigFile(configPath)
		if err := cfg.MergeInConfig(); err != nil {
			panic(err)
		}
	}
	return paths
}

func unmarshalViperConfig(cfg *viper.Viper) *config.Config {
	c := &config.Config{}
	if err := cfg.Unmarshal(c); err != nil {
		panic(err)
	}
	return c
}

// loadAllowLists loads only the "allow" section from a config file.
func loadAllowLists(configPath string) (*config.AllowLists, error) {
	v := viper.New()
	v.SetConfigType("yaml")
	v.SetConfigFile(configPath)
	if err := v.ReadInConfig(); err != nil {
		return nil, err
	}
	c := &config.Config{}
	if err := v.Unmarshal(c); err != nil {
		return nil, err
	}
	return &c.AllowLists, nil
}

// mergeAllowLists appends each allow list from extra onto base.
func mergeAllowLists(base, extra *config.AllowLists) {
	if extra == nil {
		return
	}
	base.PluralEntityPatterns = append(base.PluralEntityPatterns, extra.PluralEntityPatterns...)
	base.PluralSchemaPatterns = append(base.PluralSchemaPatterns, extra.PluralSchemaPatterns...)
	base.PropertiesWithIncorrectUnits = append(base.PropertiesWithIncorrectUnits, extra.PropertiesWithIncorrectUnits...)
	base.NonPascalEnums = append(base.NonPascalEnums, extra.NonPascalEnums...)
	base.NonPascalProperties = append(base.NonPascalProperties, extra.NonPascalProperties...)
	base.NoActionsAllowed = append(base.NoActionsAllowed, extra.NoActionsAllowed...)
	base.NoReleaseTermSchemas = append(base.NoReleaseTermSchemas, extra.NoReleaseTermSchemas...)
	base.UnknownTypeReferences = append(base.UnknownTypeReferences, extra.UnknownTypeReferences...)
	base.OtherValidURIPrefixes = append(base.OtherValidURIPrefixes, extra.OtherValidURIPrefixes...)
	base.NoURISchemas = append(base.NoURISchemas, extra.NoURISchemas...)
	base.AllowedBareSchemas = append(base.AllowedBareSchemas, extra.AllowedBareSchemas...)
	base.NoCopyrightPaths = append(base.NoCopyrightPaths, extra.NoCopyrightPaths...)
	base.AllowedNoExplorerMockups = append(base.AllowedNoExplorerMockups, extra.AllowedNoExplorerMockups...)
}

func (o OutputMode) WantAbsolutePath() bool {
	switch o {
	default:
		return false
	case Verbose, Go:
		return false
	case GCC:
		return true
	}
}

func createMemProfile(filename string) {
	if filename == "" {
		return
	}
	f, err := os.Create(filename) //nolint:gosec // user-supplied profiling path
	if err != nil {
		panic("could not create memory profile: " + err.Error())
	}
	defer func() { _ = f.Close() }()
	err = pprof.WriteHeapProfile(f)
	if err != nil {
		panic("could not write memory profile:" + err.Error())
	}
}
