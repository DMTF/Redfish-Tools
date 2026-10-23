/*
Copyright Notice:
Copyright 2026 DMTF. All rights reserved.
License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md
*/

package ucum

import (
	"context"
	"encoding/xml"
	"errors"
	"io"
	"net/http"
	"time"

	"github.com/DMTF/redfishRepoTest/src/utils"
)

var errFailedToFetch = errors.New("failed to fetch UCUM data from any upstream source")

const (
	GithubURI         = "https://raw.githubusercontent.com/ucum-org/ucum/refs/heads/main/ucum-essence.xml"
	UnitsOfMeasureURI = "http://unitsofmeasure.org/ucum-essence.xml"
	HTTPTimeout       = 30 * time.Second
)

// Root defines the XML root structure for UCUM data.
type Root struct {
	Version      string   `xml:"version,attr"`
	Revision     string   `xml:"revision,attr"`
	RevisionDate string   `xml:"revision-date,attr"`
	Prefixes     []Prefix `xml:"prefix"`
	BaseUnits    []Unit   `xml:"base-unit"`
	Units        []Unit   `xml:"unit"`
}

// Prefix represents a UCUM prefix definition.
type Prefix struct {
	Code string `xml:"Code,attr"`
	Name string `xml:"name"`
}

// Unit represents a UCUM unit definition.
type Unit struct {
	Code string `xml:"Code,attr"`
	Name string `xml:"name"`
}

func GetUCUMDataFromUpstream() (*Root, error) {
	for _, uri := range []string{GithubURI, UnitsOfMeasureURI} {
		ctx, cancel := context.WithTimeout(context.Background(), HTTPTimeout)
		defer cancel()
		root, err := GetUCUMDataFromURI(ctx, uri)
		if err == nil {
			return root, nil
		}
	}
	return nil, errFailedToFetch
}

func GetUCUMDataFromURI(ctx context.Context, uri string) (*Root, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, uri, nil)
	if err != nil {
		return nil, err
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	//nolint:errcheck // not sure what we would do if this failed anyway.
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, &utils.HTTPResponseError{StatusCode: resp.StatusCode}
	}
	dec := xml.NewDecoder(resp.Body)
	dec.CharsetReader = func(_ string, input io.Reader) (io.Reader, error) {
		// No conversion needed...
		return input, nil
	}
	var r Root
	if err := dec.Decode(&r); err != nil {
		return nil, err
	}
	return &r, nil
}
