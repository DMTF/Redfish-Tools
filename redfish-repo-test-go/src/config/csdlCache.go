/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package config

import (
	"io"
	"sync"

	"github.com/pboyd04/gocsdl/pkg/csdl"
)

var _ csdl.ExternalCache = (*ExternalThreadSafeCache)(nil)

type ExternalThreadSafeCache struct {
	cache sync.Map
}

func (e *ExternalThreadSafeCache) GetAll() map[string]*csdl.CacheEntry {
	ret := make(map[string]*csdl.CacheEntry)
	e.cache.Range(func(key, value any) bool {
		keyStr, ok := key.(string)
		valueStruct, ok2 := value.(*csdl.CacheEntry)
		if ok && ok2 {
			ret[keyStr] = valueStruct
		}
		return true
	})
	return ret
}

func (e *ExternalThreadSafeCache) Get(key string) (*csdl.Edmx, io.ReadCloser) {
	value, ok := e.cache.Load(key)
	if !ok {
		return nil, nil
	}
	valueStruct, ok := value.(*csdl.CacheEntry)
	if !ok {
		return nil, nil
	}
	return valueStruct.Edmx, valueStruct.File
}

func (e *ExternalThreadSafeCache) Set(key string, edmx *csdl.Edmx, file io.ReadCloser) {
	e.cache.Store(key, &csdl.CacheEntry{Edmx: edmx, File: file})
}
