/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package mockup

import (
	"encoding/json"
	"io"
	"os"

	"github.com/pboyd04/gocsdl/pkg/csdl"
)

type File struct {
	Raw     io.ReadSeekCloser
	Content map[string]any
	Type    *csdl.Type
}

func NewFile(raw io.ReadSeekCloser, content map[string]any) *File {
	return &File{
		Raw:     raw,
		Content: content,
		Type:    nil,
	}
}

func (f *File) Close() error {
	return f.Raw.Close()
}

// Save writes the in-memory content back to disk and refreshes the raw reader.
func (f *File) Save(m *Mockup, path string) error {
	if f.Raw != nil {
		_ = f.Raw.Close()
	}

	realPath := m.GetRealPath(path)
	data, err := json.MarshalIndent(f, "", "    ")
	if err != nil {
		return err
	}

	//nolint:mnd,gosec // auto-fix intentionally rewrites the mockup file
	if err := os.WriteFile(realPath, data, 0o644); err != nil {
		return err
	}

	//nolint:gosec // re-opening the file just written
	file, err := os.Open(realPath)
	if err != nil {
		return err
	}
	f.Raw = file
	return nil
}
