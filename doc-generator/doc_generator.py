#! /usr/local/bin/python3
# Copyright Notice:
# Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/LICENSE.md

"""
File: doc_generator.py

Brief: Reads redfish json schema files and generates a GitHub-flavored markdown document
suitable for use with the Slate documentation tool (https://github.com/tripit/slate)


Initial author: Second Rise LLC.
"""

import argparse
import json
import os
from schema_traverser import SchemaTraverser
import parse_supplement

config = None

def main():
    """Parse and validate arguments, then process data and produce markdown output."""

    global config
    config = {
        'supplemental': {},
        'excluded_properties': [],
        'excluded_by_match': [],
        'excluded_schemas': [],
        'excluded_schemas_by_match': [],
        'schema_supplement': None,
        'normative': False,
        'escape_chars': [],
        }

    help_description = 'Generate documentation for Redfish JSON schema files.\n\n'
    help_epilog      = 'Example:\n   doc_generator.py --format=html --out=/path/to/output/index.html /path/to/spmf/json-files'
    parser = argparse.ArgumentParser(description=help_description,
                                     epilog=help_epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('import_from', metavar='import_from', nargs='+',
                        help='Name of a file or directory to process (wildcards are acceptable)')
    parser.add_argument('-n', '--normative', action='store_true', dest='normative', default=False, help='Produce normative (developer-focused) output')
    parser.add_argument('--format', dest='format', default='markdown', choices=['markdown', 'html'], help='Output format')
    parser.add_argument('--out', dest='outfile', default='output.md',  help='Output file (default depends on output format -- output.md for markdown, index.html for html)')
    parser.add_argument('--sup', dest='supfile', help='Path to the supplemental material document. Default is usersupplement.md for user-focused documentation, and devsupplement.md for normative documentation.')
    parser.add_argument('--escape', dest='escape_chars', help="Characters to escape (\\) in generated markdown; e.g., --escape=@#. Use --escape=@ if strings with embedded @ are being converted to mailto links.")

    usage = parser.format_usage()
    parser.usage = usage + '\n\n' + help_epilog + '\n '

    args = parser.parse_args()

    output_format = args.format

    files_to_process = []
    for file_to_import in args.import_from:
        if os.path.isdir(file_to_import):
            for root, skip, files in os.walk(file_to_import):
                files.sort(key=str.lower)
                for filename in files:
                    if filename[-4:] == 'json':
                        files_to_process.append(os.path.join(root, filename))
        elif os.path.isfile(file_to_import):
            files_to_process.append(file_to_import)
        else:
            print('Oops,', file_to_import, 'not found, or contains no .json files.\n')


    # Determine outfile and verify that it is writeable:
    outfile_name = args.outfile
    if outfile_name == 'output.md':
        if output_format == 'html':
            outfile_name = 'index.html'

    try:
        outfile = open(outfile_name, 'w')
    except (OSError) as ex:
        print('Unable to open', outfile_name, 'to write:', ex)

    # Ensure supfile is readable (if not, warn but proceed)
    if args.supfile:
        supfile = args.supfile
    elif args.normative:
        supfile = 'devsupplement.md'
    else:
        supfile = 'usersupplement.md'

    try:
        supfile = open(supfile, 'r')
    except (OSError) as ex:
        print('Unable to open', supfile, 'to read:', ex)
    config['supplemental'] = parse_supplement.parse_file(supfile)

    if 'Excluded Properties' in config['supplemental']:
        config['excluded_properties'] = config['supplemental']['Excluded Properties'].get('exact_match')
        config['excluded_by_match'] = config['supplemental']['Excluded Properties'].get('wildcard_match')

    if 'Excluded Schemas' in config['supplemental']:
        config['excluded_schemas'] = config['supplemental']['Excluded Schemas'].get('exact_match')
        config['excluded_schemas_by_match'] = config['supplemental']['Excluded Schemas'].get('wildcard_match')

    config['schema_supplement'] = config['supplemental'].get('Schema Supplement')

    config['normative'] = args.normative

    if args.escape_chars:
        config['escape_chars'] = [x for x in args.escape_chars]

    files, schema_data = group_files(files_to_process)

    property_data = {}
    for schema_name in files.keys():
        property_data[schema_name] = process_files(schema_name, files[schema_name])
        latest_info = files[schema_name][-1]
        latest_file = os.path.join(latest_info['root'], latest_info['filename'])
        latest_data = load_as_json(latest_file)
        schema_data[schema_name] = latest_data

    traverser = SchemaTraverser('http://redfish.dmtf.org/schemas/v1/', schema_data)

    # Generate output
    if output_format == 'markdown':
        from doc_formatter import MarkdownGenerator
        generator = MarkdownGenerator(property_data, traverser, config)
    elif output_format == 'html':
        from doc_formatter import HtmlGenerator
        generator = HtmlGenerator(property_data, traverser, config)

    output = generator.generate_output()

    write_output(output, outfile)


def group_files(files):
    """Traverse files, grouping any unversioned/versioned schemas together.

    Parses json to identify versioned files.
    Returns a dict of {schema_name : [versioned files]} where each
    versioned file is a dict of root, filename, ref path.
    """

    file_list = files.copy()
    grouped_files = {}
    all_schemas = {}
    missing_files = []
    processed_files = []
    for filename in file_list:
        if filename in processed_files: continue

        root, skip, fname = filename.rpartition(os.sep)
        data = load_as_json(filename)

        # Find the title, ref, and anyOf refs (skipping odata idRef)
        if 'title' not in data: continue

        title_parts = data['title'].split('.')
        if len(title_parts) > 3: continue # old file/version scheme Name.1.0.0.Name or Name.1.0.0

        schema_name = title_parts[0]
        if len(title_parts) > 1 and title_parts[1].startswith('v'):
            schema_name += '.' + title_parts[1]

        if schema_name[0] == '#': schema_name = schema_name[1:]

        all_schemas[schema_name] = data

        ref = ''
        if '$ref' in data:
            ref = data['$ref'][1:] # drop initial '#'
        else:
            continue

        if fname.count('.') > 1:
            continue

        original_ref = ref
        for pathpart in ref.split('/'):
            if not pathpart: continue
            data = data[pathpart]

        ref_files = []
        if 'anyOf' in data:
            for obj in data['anyOf']:
                if '$ref' in obj:
                    refpath_uri, refpath_path = obj['$ref'].split('#')
                    if refpath_path == '/definitions/idRef':
                        continue
                    ref_fn = refpath_uri.split('/')[-1]
                    ref_files.append({'root': root,
                                      'filename': ref_fn,
                                      'ref': refpath_path})
                else:
                    # If there is anything that's not a ref, this isn't an unversioned schema.
                    # It's probably a Collection. Zero out ref_files and skip the rest so we
                    # can save this as a single-file group.
                    ref_files = []
                    continue

        elif '$ref' in data:
            refpath_uri, refpath_path = data['$ref'].split('#')
            ref_fn = refpath_uri.split('/')[-1]
            ref_files.append({'root': root,
                              'filename': ref_fn,
                              'ref': refpath_path})
        else:
            ref = original_ref
        if len(ref_files):
            grouped_files[schema_name] = ref_files

        if not schema_name in grouped_files:
            # this is not an unversioned schema after all.
            grouped_files[schema_name] = [{'root': root,
                                           'filename': fname,
                                           'ref': ref}]

        # Note these files as processed:
        processed_files.append(filename)
        for file_refs in grouped_files[schema_name]:
            ref_filename = os.path.join(file_refs['root'], file_refs['filename'])
            processed_files.append(ref_filename)
            if ref_filename not in file_list:
                missing_files.append(ref_filename)

    if len(missing_files):
        print("Some referenced files were missing:", missing_files)

    return grouped_files, all_schemas


def process_files(schema_name, refs):
    """Loop through a set of refs and process the specified files into property data.

    Returns a property_data object consisting of the properties from the last ref file,
    and metadata ('doc_generator_meta') indicating version for properties introduced after
    1.0 and version_deprecated for deprecated properties.
    """
    property_data = {}
    for info in refs:
        process_data_file(schema_name, info, property_data)
    return property_data


def process_data_file(schema_name, ref, property_data):
    """Process a single file by ref name, identifying version metadata and updating property_data."""

    filename = os.path.join(ref['root'], ref['filename'])
    version = get_version_string(ref['filename'])
    property_data['latest_version'] = version
    property_data['name_and_version'] = schema_name
    if version:
        property_data['name_and_version'] += ' ' + version
    property_data['properties'] = {}

    if 'properties' not in property_data:
        property_data['properties'] = {}
    meta = property_data.get('doc_generator_meta', {})

    if version == '1.0.0': version = None

    if (not version) and (schema_name in property_data):
        print('Check', schema_name, 'for version problems. Are there two files with either version 1.0.0 or no version?')

    data = load_as_json(filename)

    try:
        property_data['definitions'] = data['definitions']
        for ref_part in ref['ref'].split('/'):
            if not ref_part: continue
            data = data[ref_part]

        # resolve anyOf to embedded object, if present:
        if 'anyOf' in data:
            for elt in data['anyOf']:
                if ('type' in elt) and (elt['type'] == 'object'):
                    data = elt
                    break

        properties = data['properties']
        property_data['properties'] = properties

    except KeyError:
        print('Unable to find properties in path', ref['ref'], 'from', filename)
        return

    for prop_name in properties.keys():
        props = properties[prop_name]
        if prop_name not in meta:
            meta[prop_name] = {}
            if version: # Track version only when first seen
                meta[prop_name]['version'] = version
        if 'deprecated' in props:
            if 'version_deprecated' not in meta[prop_name]:
                meta[prop_name]['version_deprecated'] = version

    property_data['doc_generator_meta'] = meta

    return


def organize_prop_names(prop_names):
    """Strip out excluded property names, and sort the remainder."""


    # Strip out properties based on exact match:
    prop_names = [x for x in prop_names if x not in config['excluded_properties']]

    # Strip out properties based on partial match:
    included_prop_names = []
    for prop_name in prop_names:
        excluded = False
        for x in config['excluded_by_match']:
            if x in prop_name:
                excluded = True
                break
        if not excluded:
            included_prop_names.append(prop_name)

    included_prop_names.sort()
    return included_prop_names


def get_version_string(filename):
    """Parse the version string from a filename. Returned format is, e.g., v1.0.1"""

    parts = filename.split('.')
    version = ''
    if parts[1][0] == 'v':
        version = parts[1][1:]
        version = version.replace('_', '.')
    return version


def truncate_version(version_string, num_parts):
    """Truncate the version string to the specified number of parts."""

    parts = version_string.split('.')
    return '.'.join(parts[0:num_parts])


def load_as_json(filename):
    """Load json data from a file, printing an error message on failure."""
    data = ''
    try:
        # Parse file as json
        jsondata = open(filename, 'r')
        data = json.load(jsondata)
        jsondata.close()
    except (OSError, json.JSONDecodeError) as ex:
        print('Unable to read', filename, ':', ex)

    return data


def write_output(markdown, outfile):
    """Write output to a file."""

    print(markdown, file=outfile)
    outfile.close()
    print(outfile.name, "written.")


main()
