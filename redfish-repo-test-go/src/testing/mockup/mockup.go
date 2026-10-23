/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"unicode/utf8"

	"github.com/DMTF/redfishRepoTest/src"
	"github.com/DMTF/redfishRepoTest/src/config"
	"github.com/DMTF/redfishRepoTest/src/testsuite"
	"github.com/pboyd04/gocsdl/pkg/csdl"
)

type Mockup struct {
	Name                 string
	Config               *config.Config
	Directory            string
	InternallyConsistent bool
	files                map[string]*File
	types                map[string]*csdl.Type
	descendantIdx        DescendantIndex
	searcher             *csdl.Searcher
}

func NewMockup(directory string, cfg *config.Config) *Mockup {
	return &Mockup{
		Name:                 filepath.Base(directory),
		Directory:            directory,
		Config:               cfg,
		InternallyConsistent: filepath.Base(directory) != "DSP2046-examples",
		files:                make(map[string]*File),
	}
}

func (m *Mockup) Close() error {
	for _, file := range m.files {
		if err := file.Close(); err != nil {
			return err
		}
	}
	return nil
}

// AddType adds a CSDL type to the mockup's type registry for testing purposes.
// It registers the type under both its full qualified name (Namespace.Name) and
// its simple name for lookup compatibility.
func (m *Mockup) AddType(csdlType *csdl.Type) {
	if m.types == nil {
		m.types = make(map[string]*csdl.Type)
	}
	m.types[csdlType.Namespace+"."+csdlType.Name] = csdlType
	m.types[csdlType.Name] = csdlType
}

// InjectFile is used for testing purposes to inject a file into the mockup.
func (m *Mockup) InjectFile(path string, seeker io.ReadSeekCloser, content map[string]any) {
	m.files[path] = NewFile(seeker, content)
}

func (m *Mockup) Load(t *testsuite.Testing) {
	items, err := m.collectJSONFiles("")
	if err != nil {
		t.Fatal(err)
		return
	}
	if len(items) == 0 {
		return
	}

	// Phase 1: Read all file bytes in parallel (I/O-bound).
	type readResult struct {
		file    *os.File
		content []byte
		err     error
	}

	results := make([]readResult, len(items))
	m.Config.IOWorkerPool.Run(len(items), func(idx int) {
		item := &items[idx]
		file, err := os.OpenFile(item.fullPath, os.O_RDONLY, 0)
		if err != nil {
			results[idx] = readResult{err: err}
			return
		}
		content, err := io.ReadAll(file)
		if err != nil {
			results[idx] = readResult{err: err}
			return
		}
		results[idx] = readResult{file: file, content: content}
	})

	// Phase 2: Validate and parse JSON sequentially (allocation-heavy).
	for i, res := range results {
		item := &items[i]
		if res.err != nil {
			t.Error(res.err)
			continue
		}
		if !utf8.Valid(res.content) {
			t.Errorf("File %s is not valid UTF-8", filepath.Join(item.relPath, item.fileName))
			continue
		}
		var parsed any
		if err := json.Unmarshal(res.content, &parsed); err != nil {
			t.Errorf("File %s is not valid JSON", filepath.Join(item.relPath, item.fileName))
			continue
		}
		obj, ok := parsed.(map[string]any)
		if !ok {
			t.Errorf("File %s is not a JSON object", filepath.Join(item.relPath, item.fileName))
			continue
		}
		m.files[item.key] = NewFile(res.file, obj)
	}
}

//nolint:cyclop
func (m *Mockup) LoadRecursive(t *testsuite.Testing, path string) {
	entries, err := os.ReadDir(filepath.Join(m.Directory, path))
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		if entry.IsDir() {
			m.LoadRecursive(t, filepath.Join(path, entry.Name()))
			continue
		}
		if filepath.Ext(entry.Name()) != ".json" {
			continue
		}
		file, err := os.OpenFile(filepath.Join(m.Directory, path, entry.Name()), os.O_RDONLY, 0) //nolint:gosec
		if err != nil {
			t.Error(err)
			continue
		}
		content, err := io.ReadAll(file)
		if err != nil {
			t.Error(err)
			continue
		}
		if !utf8.Valid(content) {
			t.Errorf("File %s is not valid UTF-8", filepath.Join(path, entry.Name()))
			continue
		}
		var result any
		if err := json.Unmarshal(content, &result); err != nil {
			t.Errorf("File %s is not valid JSON", filepath.Join(path, entry.Name()))
			continue
		}
		res, ok := result.(map[string]any)
		if !ok {
			t.Errorf("File %s is not a JSON object", filepath.Join(path, entry.Name()))
			continue
		}
		if entry.Name() == "index.json" {
			m.files["/redfish/v1/"+path] = NewFile(file, res)
			continue
		}
		m.files[filepath.Join("/redfish/v1/", path, entry.Name())] = NewFile(file, res)
	}
}

func (m *Mockup) LookupErrorLines(errs []error) {
	for _, err := range errs {
		var jsonErr *src.JSONSourceError
		if errors.As(err, &jsonErr) {
			file := m.GetReadSeekerFromRealPath(jsonErr.FileName())
			if file == nil {
				continue
			}
			jsonErr.LookupLineFromFile(file)
		}
	}
}

func (m *Mockup) PathValid(path string) bool {
	_, ok := m.files[path]
	return ok
}

func (m *Mockup) GetRealPath(path string) string {
	path = strings.TrimPrefix(path, "/redfish/v1/")
	ret := filepath.Join(m.Directory, path)
	if !strings.HasSuffix(ret, ".json") {
		ret += "/index.json"
	}
	return ret
}

func (m *Mockup) GetReadSeekerFromRealPath(path string) io.ReadSeeker {
	path = strings.TrimPrefix(path, m.Directory)
	path = strings.TrimPrefix(path, "/")
	path = strings.TrimSuffix(path, "/index.json")
	path = "/redfish/v1/" + path
	file, ok := m.files[path]
	if !ok {
		_, _ = fmt.Fprintf(os.Stderr, "File %q not found\n", path)
		return nil
	}
	return file.Raw
}

// loadItem represents a JSON file discovered during directory traversal.
type loadItem struct {
	relPath  string // relative path within the mockup (e.g., "Systems/1")
	fileName string // file name (e.g., "index.json")
	fullPath string // full filesystem path
	key      string // map key for m.files
}

// collectJSONFiles walks the mockup directory tree and returns all JSON file paths.
func (m *Mockup) collectJSONFiles(path string) ([]loadItem, error) {
	entries, err := os.ReadDir(filepath.Join(m.Directory, path))
	if err != nil {
		return nil, err
	}
	items := make([]loadItem, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() {
			subItems, err := m.collectJSONFiles(filepath.Join(path, entry.Name()))
			if err != nil {
				return nil, err
			}
			items = append(items, subItems...)
			continue
		}
		if filepath.Ext(entry.Name()) != ".json" {
			continue
		}
		fullPath := filepath.Join(m.Directory, path, entry.Name())
		var key string
		if entry.Name() == "index.json" {
			key = "/redfish/v1/" + path
		} else {
			key = filepath.Join("/redfish/v1/", path, entry.Name())
		}
		items = append(items, loadItem{
			relPath:  path,
			fileName: entry.Name(),
			fullPath: fullPath,
			key:      key,
		})
	}
	return items, nil
}
