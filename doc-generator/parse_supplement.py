"""
File : parse_supplement.py

Provides parsing utilities for supplemental schema document used
with the Redfish documentation generator.

Initial author: Second Rise LLC.

The Distributed Management Task Force (DMTF) grants rights under copyright in
this software on the terms of the BSD 3-Clause License as set forth below; no
other rights are granted by DMTF. This software might be subject to other rights
(such as patent rights) of other parties.

Copyrights.

Copyright (c) 2016, Contributing Member(s) of Distributed Management Task Force,
Inc.. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.

    Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

    Neither the name of the Distributed Management Task Force (DMTF) nor the
    names of its contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Patents.

This software may be subject to third party patent rights, including provisional
patent rights ("patent rights"). DMTF makes no representations to users of the
standard as to the existence of such rights, and is not responsible to
recognize, disclose, or identify any or all such third party patent right,
owners or claimants, nor for any incomplete or inaccurate identification or
disclosure of such rights, owners or claimants. DMTF shall have no liability to
any party, in any manner or circumstance, under any legal theory whatsoever, for
failure to recognize, disclose, or identify any such third party patent rights,
or for such party’s reliance on the software or incorporation thereof in its
product, protocols or testing procedures. DMTF shall have no liability to any
party using such software, whether such use is foreseeable or not, nor to any
patent owner or claimant, and shall have no liability or responsibility for
costs or losses incurred if software is withdrawn or modified after publication,
and shall be indemnified and held harmless by any party using the software from
any and all claims of infringement by a patent owner for such use.

DMTF Members that contributed to this software source code might have made
patent licensing commitments in connection with their participation in the DMTF.
For details, see http://dmtf.org/sites/default/files/patent-10-18-01.pdf and
http://www.dmtf.org/about/policies/disclosures.
"""
import re
import urllib.request
import warnings

def parse_file(filehandle):
    """Parse the supplemental material document. Returns a dict."""

    # First, split into heading / text.
    parsed = {}
    current_item = None
    text = []

    # These headings have special meaning:
    section_markers = [
        '# Keyword Configuration', # list of keyword settings
        '# Introduction',          # block of markup for intro, with possible #includes
        '# Postscript',            # block of markup to include verbatim
        '# Excluded Properties',   # parse out properties (## headings) to exclude (top-level only).
        '# Excluded Annotations',  # parse out properties (## headings) to exclude.
        '# Excluded Schemas',      # parse out schemas (## headings) to exclude.
        '# Schema Supplement',     # parse out for schema-specific details (see below)
        '# Schema Documentation',   # list of search/replace patterns for links
        ]

    for line in filehandle:
        line = line.strip('\r\n') # Keep other whitespace
        if line in section_markers:
            if current_item:
                parsed[current_item] = '\n'.join(text)
            current_item = line.strip('# ')
            text = []

        else:
            text.append(line)

    if current_item and len(text):
        parsed[current_item] = '\n'.join(text)

    if 'Keyword Configuration' in parsed:
        parsed['keywords'] = parse_configuration(parsed['Keyword Configuration'])

    if 'Introduction' in parsed:
        parsed['Title'] = parse_title_from_introduction(parsed['Introduction'])

    if 'Excluded Properties' in parsed:
        parsed['Excluded Properties'] = parse_excluded_properties(parsed['Excluded Properties'])

    if 'Excluded Annotations' in parsed:
        parsed['Excluded Annotations'] = parse_excluded_properties(parsed['Excluded Annotations'])

    if 'Excluded Schemas' in parsed:
        parsed['Excluded Schemas'] = parse_excluded_properties(parsed['Excluded Schemas'])

    if 'Schema Supplement' in parsed:
        parsed['Schema Supplement'] = parse_schema_supplement(parsed['Schema Supplement'])
        # Second pass to pull out property details
        parsed['property details'] = parse_property_details(parsed['Schema Supplement'])
        parsed['action details'] = parse_action_details(parsed['Schema Supplement'])

    if 'Schema Documentation' in parsed:
        parsed['Schema Documentation'] = parse_documentation_links(parsed['Schema Documentation'])

    return parsed


def parse_configuration(markdown_blob):
    """Split this blob into bullet points with keyword: value.

    Values may be coerced as needed. So far, expected booleans are coerced.
    """
    boolean_settings = ['omit_version_in_headers', 'expand_defs_from_non_output_schemas']
    config = {}
    pattern = re.compile(r'\s*-\s+(\S+)\s*:\s*(\S+)')

    for line in markdown_blob.splitlines():
        match = pattern.fullmatch(line)
        if match:
            name = match.group(1).lower()
            value = match.group(2)
            if name in boolean_settings:
                if value.lower() in ['false', 'no', '0']:
                    value = False
                else:
                    value = True
            config[name] = value

    return config


def parse_documentation_links(markdown_blob):
    """ Parse lines with "[link pattern]:[replacment]" into a structure for lookup and replace."""

    linkmap = {}
    pattern = re.compile(r'\#\#\s+(\S+)\s*\|\s*(\S+)')

    for line in markdown_blob.splitlines():
        match = pattern.fullmatch(line)
        if match:
            to_replace = match.group(1)
            replace_with = match.group(2)
            # Use largest non-wildcard portion of to_replace as key.
            # This may result in more than one pair being listed under the same key.
            if '*' in to_replace:
                parts = []
                largest_part = ''
                while len(to_replace):
                    i = to_replace.find('*')
                    if i > -1:
                        part = to_replace[:i]
                        to_replace = to_replace[i+1:]
                        if part:
                            parts.append(part)
                        parts.append('.*')
                        if len(part) > len(largest_part):
                            largest_part = part
                    else:
                        parts.append(to_replace)
                        if len(to_replace) > len(largest_part):
                            largest_part = to_replace
                        to_replace = ''

                if largest_part not in linkmap:
                    linkmap[largest_part] = []
                linkmap[largest_part].append({'wild_match': parts, 'replace_with': replace_with})

            else:
                if to_replace not in linkmap:
                    linkmap[to_replace] = []
                linkmap[to_replace].append({'full_match': to_replace,
                                            'replace_with':  replace_with})
    return linkmap


def parse_title_from_introduction(markdown_blob):
    """If the intro begins with a top-level heading, return its contents"""

    lines = markdown_blob.splitlines()
    for line in lines:
        if line.startswith('# '):
            line = line.strip('# ')
            return line
        # We only take the first line, so if we find a non-h1, just skip it:
        elif line.strip():
            return ''


def parse_excluded_properties(markdown_blob):
    """Find second-level headings (start with ##) in markdown_blob.

    Properties that begin with * are treated as wildcard matches."""

    parsed = {'exact_match': [], 'wildcard_match': []}

    lines = markdown_blob.splitlines()
    for line in lines:
        if line.startswith('## '):
            line = line.strip('# ')
            if line.startswith('*'):
                line = line[1:]
                parsed['wildcard_match'].append(line)
            else:
                parsed['exact_match'].append(line)

    return parsed


def parse_schema_supplement(markdown_blob):
    """Parse the schema supplement by schema, description, and payload.

    ## [schema_name].[major_version] - marks a schema

    Within this section:
    ### Description - marks a text/markdown block to replace the schema description.
    ### JSONPayload - marks a bit of markdown to treat as JSON Payload.
    ... and more! See parse_schema_details.
    """

    parsed = {}

    # Split the blob into schema sections.
    lines = markdown_blob.splitlines()
    current_schema = None
    bloblines = []

    for line in lines:
        if line.startswith('## '):
            line = line.strip('# ')
            if current_schema:
                parsed[current_schema] = '\n'.join(bloblines)
            current_schema = line
            bloblines = []
        else:
            bloblines.append(line)

    if current_schema and len(bloblines):
        parsed[current_schema] = '\n'.join(bloblines)

    # find subsections in each
    for schema_name, blob in parsed.items():
        parsed[schema_name] = parse_schema_details(blob)

    return parsed


def parse_schema_details(markdown_blob):
    """Parse an individual schema's supplement blob.

    Captures Description, Schema-Intro, Schema-Postscript, JSONPayload, and Property Details.
    """

    markers = ['### description', '### jsonpayload', '### property details', '### action details',
               '### schema-intro', '### schema-postscript', '### mockup']
    parsed = {}
    current_marker = None
    bloblines = []

    # Note that we split by linebreak earlier and joined with \n, so we
    # can safely assume \n is the line separator. splitlines() omits blank lines.
    lines = markdown_blob.splitlines()
    for line in lines:
        if line.lower() in markers:
            line = line.lower().strip('# ')
            if current_marker and len(bloblines):
                parsed[current_marker] = '\n'.join(bloblines)
            current_marker = line
            bloblines = []
        else:
            bloblines.append(line)

    if current_marker and len(bloblines):
        parsed[current_marker] = '\n'.join(bloblines)

    # Combine "mockup" with "jsonpayload"
    if parsed.get('mockup'):
        mockup = None
        mockup_location = ''
        lines = parsed['mockup'].splitlines()
        for line in lines:
            if line:
                mockup_location = line.strip('# ')
                ml_lower = mockup_location.lower()
                if ml_lower.startswith('http://') or ml_lower.startswith('https://'):
                    # retrieve it via http[s]
                    try:
                        response = urllib.request.urlopen(mockup_location)
                        if 200 <= response.status < 300:
                            mockup = response.read().decode('utf-8') # JSON is UTF-8 by spec.
                        else:
                            warnings.warn('Unable to retrieve Mockup from URL "'
                                          + mockup_location + ':', "Server returned",
                                          response.status, "status")
                    except Exception as ex:
                        warnings.warn('Unable to retrieve Mockup from URL "' + mockup_location
                                      + ':', ex)
                else:
                    # treat it as a local file
                    try:
                        mockup_file = open(mockup_location, 'r', encoding="utf8")
                        mockup = mockup_file.read()
                    except Exception as ex:
                        warnings.warn('Unable to open Mockup file "' + mockup_location +
                                      '" to read:', ex)
                break

        if mockup:
            mockup = '```json\n' + mockup + '\n```\n'
            if parsed.get('jsonpayload'):
                warnings.warn('Warning: Mockup and JSONPayload both specified; using Mockup ' +
                              mockup_location)
            parsed['jsonpayload'] = mockup

    return parsed


def parse_property_details(schema_supplement):
    """Parse the property details from schema_supplement.

    second-level headings identify Schemas; third-level headings identify properties
    within the schema, following text/markdown is to be inserted as a description.
    """
    parsed = {}
    current_schema = None
    current_property = None
    bloblines = []

    for current_schema, schema_details in schema_supplement.items():
        parsed[current_schema] = {}
        if 'property details' in schema_details:
            lines = schema_details['property details'].splitlines()

            for line in lines:
                if line.startswith('#### '):
                    line = line.strip('# ')
                    if current_property and len(bloblines):
                        parsed[current_schema][current_property] = '\n'.join(bloblines)
                    current_property = line
                    bloblines = []
                else:
                    bloblines.append(line)

                if current_property and len(bloblines):
                    parsed[current_schema][current_property] = '\n'.join(bloblines)

    return parsed


def parse_action_details(schema_supplement):
    """Parse the property details from schema_supplement.

    second-level headings identify Schemas; third-level headings identify properties
    within the schema, following text/markdown is to be inserted as a description.
    """
    parsed = {}
    current_schema = None

    for current_schema, schema_details in schema_supplement.items():
        bloblines = []
        parsed[current_schema] = {}
        current_property = None
        if 'action details' in schema_details:
            lines = schema_details['action details'].splitlines()
            for line in lines:
                if line.startswith('#### '):
                    line = line.strip('# ')
                    if current_property and len(bloblines):
                        parsed[current_schema][current_property] = '\n'.join(bloblines)
                    current_property = line
                    bloblines = []
                elif current_property:
                    bloblines.append(line)

            if current_property and len(bloblines):
                parsed[current_schema][current_property] = '\n'.join(bloblines)
                bloblines = []

    for schema_name, action_details in parsed.items():
        for property, blob in action_details.items():
            lines = blob.splitlines()
            new_blob_lines = []
            new_blob = ''
            example_lines = []
            example = ''
            in_example = False
            for line in lines:
                if in_example:
                    example_lines.append(line)
                else:
                    if line.startswith('##### ') and line.strip('# ').lower() == 'example':
                        # start example
                        in_example = True
                    else:
                        new_blob_lines.append(line)

            new_blob = '\n'.join(new_blob_lines)
            example = '\n'.join(example_lines)
            parsed[schema_name][property] = {'text': new_blob, 'example': example}

    return parsed
