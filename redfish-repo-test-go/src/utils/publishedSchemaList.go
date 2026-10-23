/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package utils

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"golang.org/x/net/html"
)

const (
	httpRetryCount = 5
	httpTimeout    = 30 * time.Second
)

type HTTPResponseError struct {
	StatusCode int
}

func (e *HTTPResponseError) Error() string {
	return fmt.Sprintf("http error %d", e.StatusCode)
}

func GetPublishedSchemaList(uri string) (map[string]*RedfishNamespaceVersion, error) {
	return getListFromServer(uri)
}

func getListFromServer(uri string) (map[string]*RedfishNamespaceVersion, error) {
	var resp *http.Response
	for range httpRetryCount {
		ctx, cancel := context.WithTimeout(context.Background(), httpTimeout)
		defer cancel()
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, uri, nil)
		if err != nil {
			return nil, err
		}
		resp, err = http.DefaultClient.Do(req)
		if resp != nil {
			//nolint:errcheck // Not sure what we would do if this failed anyway.
			defer resp.Body.Close()
		}
		if err == nil && resp != nil && resp.StatusCode == http.StatusOK {
			break
		}
	}
	if resp.StatusCode != http.StatusOK {
		return nil, &HTTPResponseError{StatusCode: resp.StatusCode}
	}
	return parseList(resp.Body)
}

func parseList(body io.ReadCloser) (map[string]*RedfishNamespaceVersion, error) {
	doc, err := html.Parse(body)
	if err != nil {
		return nil, err
	}
	allJSONLinks := []string{}
	allJSONLinks = findAllJSONLinks(doc, allJSONLinks)
	ret := map[string]*RedfishNamespaceVersion{}
	for _, link := range allJSONLinks {
		link = strings.TrimSuffix(link, ".json")
		schemaName, schemaVer, ok := strings.Cut(link, ".")
		if !ok {
			continue
		}
		schemaRv, err := ParseVersionFromString(schemaVer)
		if err != nil {
			continue
		}
		oldVersion, ok := ret[schemaName]
		if !ok {
			// Easy case, the first one, just add me
			ret[schemaName] = schemaRv
		} else if schemaRv.Compare(oldVersion) > 0 {
			ret[schemaName] = schemaRv
		}
	}
	return ret, nil
}

func findAllJSONLinks(n *html.Node, ret []string) []string {
	if n.Type == html.ElementNode && n.Data == "a" {
		for _, a := range n.Attr {
			if a.Key == "href" && strings.HasSuffix(a.Val, ".json") {
				ret = append(ret, a.Val)
			}
		}
	}
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		ret = findAllJSONLinks(c, ret)
	}
	return ret
}
