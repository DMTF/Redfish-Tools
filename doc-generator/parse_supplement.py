# Copyright Notice:
# Copyright 2016, 2019 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File : parse_supplement.py

Provides parsing utilities for supplemental schema document used
with the Redfish documentation generator.

Initial author: Second Rise LLC.
"""
import re
import urllib.request
import os.path
import warnings

# TODO: move some warnings out of here and into doc_generator, accounting for the possibility
# that some values could come from either config or supplement.
def parse_file(filehandle):
    """Parse the supplemental material document. Returns a dict. """

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
        '# Excluded patternProperties', # parse out patternProperties (## headings) to exclude.
        '# Schema Supplement',     # parse out for schema-specific details (see below)
        '# Schema Documentation',  # list of search/replace patterns for links
        '# Description Overrides', # list of property name:description to substitute throughout the doc
        '# FullDescription Overrides', # list of property name:description to substitute throughout the doc
        '# Schema URI Mapping',    # map URI(s) to local repo(s)
        '# Profile URI Mapping',   # map URI(s) for profiles to local repo(s)
        '# Enum Deprecations',     # Version and description info for deprecated enums
        '# Units Translation',     # String-replace mapping for unit abbreviations
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
        parsed['wants_common_objects'] = '[insert_common_objects]' in parsed['Introduction']

    if not parsed.get('wants_common_objects') and 'Postscript' in parsed:
        parsed['wants_common_objects'] = '[insert_common_objects]' in parsed['Postscript']

    if 'Excluded Properties' in parsed:
        parsed['Excluded Properties'] = parse_excluded_properties(parsed['Excluded Properties'])

    if 'Excluded Annotations' in parsed:
        parsed['Excluded Annotations'] = parse_excluded_properties(parsed['Excluded Annotations'])

    if 'Excluded Schemas' in parsed:
        parsed['Excluded Schemas'] = parse_excluded_properties(parsed['Excluded Schemas'])

    if 'Excluded patternProperties' in parsed:
        parsed['Excluded patternProperties'] = parse_excluded_properties(parsed['Excluded patternProperties'])

    if 'Description Overrides' in parsed:
        parsed['Description Overrides'] = parse_description_overrides(parsed['Description Overrides'])

    if 'FullDescription Overrides' in parsed:
        parsed['FullDescription Overrides'] = parse_description_overrides(parsed['FullDescription Overrides'])

    if 'Schema Supplement' in parsed:
        parsed['Schema Supplement'] = parse_schema_supplement(parsed['Schema Supplement'])

        # Second pass to pull out property details
        parsed['property details'] = parse_property_details(parsed['Schema Supplement'])
        parsed['action details'] = parse_action_details(parsed['Schema Supplement'])

    if 'Schema Documentation' in parsed:
        parsed['Schema Documentation'] = parse_documentation_links(parsed['Schema Documentation'])

    if 'Schema URI Mapping' in parsed:
        parsed['local_to_uri'], parsed['uri_to_local'] = parse_uri_mapping(parsed['Schema URI Mapping'])

    if 'Profile URI Mapping' in parsed:
        parsed['profile_local_to_uri'], parsed['profile_uri_to_local'] = parse_uri_mapping(
            parsed['Profile URI Mapping'])
        if not parsed.get('profile_uri_to_local'):
            warnings.warn("Profile URI Mapping found in supplemental document didn't provide any mappings. " +
                          "Output is likely to be incomplete.\n\n")

    if 'Enum Deprecations' in parsed:
        parsed['enum_deprecations'] = parse_enum_deprecations(parsed['Enum Deprecations'])

    if 'Units Translation' in parsed:
        parsed['units_translation'] = parse_units_translation(parsed['Units Translation'])

    return parsed


def parse_configuration(markdown_blob):
    """Split this blob into bullet points with keyword: value.

    Values may be coerced as needed. So far, expected booleans are coerced.
    """
    boolean_settings = ['omit_version_in_headers', 'expand_defs_from_non_output_schemas', 'add_toc',
                        'actions_in_property_table']
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


def parse_uri_mapping(markdown_blob):
    """Parse a Schema URI mapping section, producing maps in both directions."""
    local_to_uri = {}
    uri_to_local = {}

    for line in markdown_blob.splitlines():
        if line.startswith('## Local-repo:'):
            scratch = line[14:]
            scratch = scratch.strip()
            parts = scratch.split(' ')
            if len(parts) == 2:
                uri = parts[0] # Actually a URI part -- domain and path
                local_path = parts[1]

                # Validate the local_path and normalize it:
                abs_local_path = os.path.abspath(local_path)
                if os.path.isdir(abs_local_path):
                    local_to_uri[abs_local_path] = uri
                    uri_to_local[uri] = abs_local_path
                else:
                    warnings.warn('URI mapping in Supplemental file has a bad local path "' + local_path + '"')
            else:
                warnings.warn('Could not parse URI mapping from Supplemental file: "' + line + '"')

    return local_to_uri, uri_to_local


def parse_title_from_introduction(markdown_blob):
    """If the intro contains a top-level heading, return its contents"""

    lines = markdown_blob.splitlines()
    for line in lines:
        if line.startswith('# '):
            line = line.strip('# ')
            return line


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


def parse_description_overrides(markdown_blob):
    """Create a { property_name : description } dict from markdown blob. Ignore any lines that don't parse."""

    parsed = {}

    lines = markdown_blob.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith('*'):
            line = line[1:]
            property_name, description = line.split(':', 1)
            property_name = property_name.strip()
            description = description.strip()
            if property_name and description:
                parsed[property_name] = description
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

        # Parse description overrides, if present
        if 'description overrides' in parsed[schema_name]:
            parsed[schema_name]['description overrides'] = parse_description_overrides(parsed[schema_name]['description overrides'])

        if 'fulldescription overrides' in parsed[schema_name]:
            parsed[schema_name]['fulldescription overrides'] = parse_description_overrides(parsed[schema_name]['fulldescription overrides'])

    return parsed


def parse_schema_details(markdown_blob):
    """Parse an individual schema's supplement blob.

    Captures Description, Schema-Intro, Schema-Postscript, JSONPayload, and Property Details.
    """

    markers = ['### description', '### jsonpayload', '### property details', '### action details',
               '### schema-intro', '### schema-postscript', '### mockup',
               '### description overrides', '### fulldescription overrides']
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
                                          + mockup_location + '":', "Server returned",
                                          response.status, "status")
                    except Exception as ex:
                        warnings.warn('Unable to retrieve Mockup from URL "{0}": {1}'
                                      .format(mockup_location, ex))
                else:
                    # treat it as a local file
                    try:
                        mockup_file = open(mockup_location, 'r', encoding="utf8")
                        mockup = mockup_file.read()
                    except Exception as ex:
                        warnings.warn('Unable to open Mockup file "{0}" to read: {1}'
                                      .format(mockup_location, ex))
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


def parse_enum_deprecations(markdown_blob):
    """Parse enum deprecation info.

    Creates a dict of Name: version & description, keyed by $ref.
    """

    parsed = {}

    # First, split by major heading (ref)
    ref = None
    blob = ''
    lines = markdown_blob.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith('## '):
            if ref:
                parsed[ref] = blob
                blob = ''
            line = line[3:]
            ref = line.strip()
        else:
            blob += '\n' + line

    if ref and blob:
        parsed[ref] = blob

    for ref in parsed:
        lines = parsed[ref].splitlines()
        parsed[ref] = {}
        for line in lines:
            if line.startswith('*'):
                line = line[1:]
                name, version_string, description = line.split('|', 2)
                name = name.strip()
                version_string = version_string.strip()
                description = description.strip()
                if name and version_string:
                    parsed[ref][name] = {"version": version_string, "description": description}

    return parsed


def parse_units_translation(markdown_blob):
    """Parse Unit Translations. Should contain a markdown table of Value, Replacement.

    Creates a dict of value: replacement.
    """
    parsed = {}
    heading_pattern = re.compile(r'\|\s*Value\s*\|\s*Replacement\s*\|');
    row_pattern = re.compile(r'\|\s*(\S[.*\S]*)\s*\|\s*(\S[.*\S]*)\s*\|');

    # First, find the translation table.
    in_table = False
    blob = ''
    lines = markdown_blob.splitlines()
    for line in lines:
        line = line.strip()
        if in_table:
            match = row_pattern.fullmatch(line)
            if match:
                parsed[match.group(1)] = match.group(2)
            else:
                break
        else:
            match = heading_pattern.fullmatch(line)
            if match:
                in_table = True
                continue

    return parsed
