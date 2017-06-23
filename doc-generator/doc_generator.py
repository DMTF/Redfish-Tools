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
import warnings
from schema_traverser import SchemaTraverser
import parse_supplement


# Format user warnings simply
def simple_warning_format(message, category, filename, lineno, file=None, line=None):
    """ a basic format for warnings from this program """
    return '  Warning: %s (%s:%s)' % (message, filename, lineno) + "\n"

warnings.formatwarning = simple_warning_format


def main():
    """Parse and validate arguments, then process data and produce markdown output."""

    config = {
        'supplemental': {},
        'excluded_annotations': [],
        'excluded_annotations_by_match': [],
        'excluded_properties': [],
        'excluded_by_match': [],
        'excluded_schemas': [],
        'excluded_schemas_by_match': [],
        'expand_defs_from_non_output_schemas': False,
        'schema_supplement': None,
        'normative': False,
        'escape_chars': [],
        'cwd': os.getcwd(),
        'schema_root_uri': 'http://redfish.dmtf.org/schemas/v1/',
        'uri_replacements': {},
        }

    help_description = 'Generate documentation for Redfish JSON schema files.\n\n'
    help_epilog = ('Example:\n   doc_generator.py --format=html\n   doc_generator.py'
                   ' --format=html'
                   ' --out=/path/to/output/index.html /path/to/spmf/json-files')
    parser = argparse.ArgumentParser(description=help_description,
                                     epilog=help_epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('import_from', metavar='import_from', nargs='*',
                        help=('Name of a file or directory to process (wildcards are acceptable).'
                              'Default: json-schema'))
    parser.add_argument('-n', '--normative', action='store_true', dest='normative', default=False,
                        help='Produce normative (developer-focused) output')
    parser.add_argument('--format', dest='format', default='markdown',
                        choices=['markdown', 'html'], help='Output format')
    parser.add_argument('--out', dest='outfile', default='output.md',
                        help=('Output file (default depends on output format: '
                              'output.md for markdown, index.html for html)'))
    parser.add_argument('--sup', dest='supfile',
                        help=('Path to the supplemental material document. '
                              'Default is usersupplement.md for user-focused documentation, '
                              'and devsupplement.md for normative documentation.'))
    parser.add_argument('--escape', dest='escape_chars',
                        help=("Characters to escape (\\) in generated markdown; "
                              "e.g., --escape=@#. Use --escape=@ if strings with embedded @ "
                              "are being converted to mailto links."))

    args = parser.parse_args()

    config['output_format'] = args.format

    if len(args.import_from):
        import_from = args.import_from
    else:
        import_from = [config.get('cwd') + '/json-schema']

    # Determine outfile and verify that it is writeable:
    outfile_name = args.outfile
    if outfile_name == 'output.md':
        if config['output_format'] == 'html':
            outfile_name = 'index.html'

    try:
        outfile = open(outfile_name, 'w', encoding="utf8")
    except (OSError) as ex:
        warnings.warn('Unable to open ' + outfile_name + ' to write: ' + str(ex))

    # Ensure supfile is readable (if not, warn but proceed)
    supfile_expected = False
    if args.supfile:
        supfile = args.supfile
        supfile_expected = True
    elif args.normative:
        supfile = config.get('cwd') + '/devsupplement.md'
    else:
        supfile = config.get('cwd') + '/usersupplement.md'

    try:
        supfile = open(supfile, 'r', encoding="utf8")
        config['supplemental'] = parse_supplement.parse_file(supfile)
    except (OSError) as ex:
        if supfile_expected:
            warnings.warn('Unable to open ' + supfile + ' to read: ' +  str(ex))
        else:
            warnings.warn('No supplemental file specified and ' + supfile +
                          ' not found. Proceeding.')


    if 'keywords' in config['supplemental']:
        # Promote the keywords to top-level keys.
        config.update(config['supplemental']['keywords'])

    if 'Schema Documentation' in config['supplemental']:
        config['uri_replacements'] = config['supplemental']['Schema Documentation']

    if 'Excluded Annotations' in config['supplemental']:
        config['excluded_properties'].extend(
            config['supplemental']['Excluded Annotations'].get('exact_match'))
        config['excluded_annotations'].extend(
            config['supplemental']['Excluded Annotations'].get('exact_match'))
        config['excluded_by_match'].extend(
            config['supplemental']['Excluded Annotations'].get('wildcard_match'))
        config['excluded_annotations_by_match'].extend(
            config['supplemental']['Excluded Annotations'].get('wildcard_match'))

    if 'Excluded Properties' in config['supplemental']:
        config['excluded_properties'].extend(
            config['supplemental']['Excluded Properties'].get('exact_match', []))
        config['excluded_by_match'].extend(
            config['supplemental']['Excluded Properties'].get('wildcard_match', []))

    if 'Excluded Schemas' in config['supplemental']:
        config['excluded_schemas'] = config['supplemental']['Excluded Schemas'].get('exact_match')
        config['excluded_schemas_by_match'] = config['supplemental']['Excluded Schemas'].get('wildcard_match')

    config['schema_supplement'] = config['supplemental'].get('Schema Supplement', {})
    config['add_toc'] = config['supplemental']['keywords'].get('add_toc')

    config['normative'] = args.normative

    if args.escape_chars:
        config['escape_chars'] = [x for x in args.escape_chars]

    output = generate_docs(import_from, config)

    write_output(output, outfile)


def get_files(text_input):
    """From text input (command line or parsed from file), create a list of files. """

    files_to_process = []
    for file_to_import in text_input:
        if os.path.isdir(file_to_import):
            for root, _, files in os.walk(file_to_import):
                files.sort(key=str.lower)
                for filename in files:
                    if filename[-4:] == 'json':
                        files_to_process.append(os.path.join(root, filename))
        elif os.path.isfile(file_to_import):
            files_to_process.append(file_to_import)
        else:
            warnings.warn('Oops, ' + file_to_import + ' not found, or contains no .json files.\n')
    return files_to_process


def generate_docs(file_list, config, level=0):
    """Given a list of files, generate a block of documentation.

    This is the main loop of the product.
    """
    files_to_process = get_files(file_list)
    files, schema_data = group_files(files_to_process)

    property_data = {}
    doc_generator_meta = {}
    for schema_name in files.keys():
        property_data[schema_name] = process_files(schema_name, files[schema_name])
        doc_generator_meta[schema_name] = property_data[schema_name]['doc_generator_meta']
        latest_info = files[schema_name][-1]
        latest_file = os.path.join(latest_info['root'], latest_info['filename'])
        latest_data = load_as_json(latest_file)
        latest_data['_is_versioned_schema'] = latest_info.get('_is_versioned_schema')
        latest_data['_is_collection_of'] = latest_info.get('_is_collection_of')

        schema_data[schema_name] = latest_data

    traverser = SchemaTraverser(config['schema_root_uri'], schema_data, doc_generator_meta)

    # Generate output
    if config['output_format'] == 'markdown':
        from doc_formatter import MarkdownGenerator
        generator = MarkdownGenerator(property_data, traverser, config, level)
    elif config['output_format'] == 'html':
        from doc_formatter import HtmlGenerator
        generator = HtmlGenerator(property_data, traverser, config, level)

    return generator.generate_output()


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
        # Get the (probably versioned) filename, and save the data:
        root, _, fname = filename.rpartition(os.sep)
        data = load_as_json(filename)

        schema_name = get_schema_name(fname, data)
        if schema_name is None: continue

        all_schemas[schema_name] = data

        if filename in processed_files: continue

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

        # is_versioned_schema will be True if there is an "anyOf" pointing to one or more versioned files.
        is_versioned_schema = False

        # is_collection_of will contain the type of objects in the collection.
        is_collection_of = None

        if 'anyOf' in data:
            for obj in data['anyOf']:
                if '$ref' in obj:
                    refpath_uri, refpath_path = obj['$ref'].split('#')
                    if refpath_path == '/definitions/idRef':
                        is_versioned_schema = True
                        continue
                    ref_fn = refpath_uri.split('/')[-1]
                    # Skip files that are not present.
                    ref_filename = os.path.join(root, ref_fn)
                    if ref_filename in file_list:
                        ref_files.append({'root': root,
                                          'filename': ref_fn,
                                          'ref': refpath_path})
                    elif ref_filename not in missing_files:
                        missing_files.append(ref_filename)

                else:
                    # If there is anything that's not a ref, this isn't an unversioned schema.
                    # It's probably a Collection. Zero out ref_files and skip the rest so we
                    # can save this as a single-file group.
                    if 'properties' in obj:
                        if 'Members' in obj['properties']:
                            # It's a collection. What is it a collection of?
                            member_ref = obj['properties']['Members'].get('items', {}).get('$ref')
                            if member_ref:
                                is_collection_of = member_ref.split('/')[-1]
                    ref_files = []
                    continue

        elif '$ref' in data:
            refpath_uri, refpath_path = data['$ref'].split('#')
            if refpath_path == '/definitions/idRef':
                continue

            ref_fn = refpath_uri.split('/')[-1]
            # Skip files that are not present.
            ref_filename = os.path.join(root, ref_fn)
            if ref_filename in file_list:
                ref_files.append({'root': root,
                                  'filename': ref_fn,
                                  'ref': refpath_path})
            elif ref_filename not in missing_files:
                missing_files.append(ref_filename)

        else:
            ref = original_ref

        if len(ref_files):
            # Add the _is_versioned_schema and  is_collection_of hints to each ref object
            [x.update({'_is_versioned_schema': is_versioned_schema, '_is_collection_of': is_collection_of})
             for x in ref_files]
            grouped_files[schema_name] = ref_files

        if not schema_name in grouped_files:
            # this is not an unversioned schema after all.
            grouped_files[schema_name] = [{'root': root,
                                           'filename': fname,
                                           'ref': ref,
                                           '_is_versioned_schema': is_versioned_schema,
                                           '_is_collection_of': is_collection_of}]

        # Note these files as processed:
        processed_files.append(filename)
        for file_refs in grouped_files[schema_name]:
            ref_filename = os.path.join(file_refs['root'], file_refs['filename'])
            processed_files.append(ref_filename)

    if len(missing_files):
        warnings.warn("Some referenced files were missing: " + ' '.join(missing_files))

    return grouped_files, all_schemas


def process_files(schema_name, refs):
    """Loop through a set of refs and process the specified files into property data.

    Returns a property_data object consisting of the properties from the last ref file,
    and metadata ('doc_generator_meta') indicating version for properties introduced after
    1.0 and version_deprecated for deprecated properties.
    """
    property_data = {}
    for info in refs:
        property_data = process_data_file(schema_name, info, property_data)
    return property_data


def process_data_file(schema_name, ref, property_data):
    """Process a single file by ref name, identifying metadata and updating property_data."""

    filename = os.path.join(ref['root'], ref['filename'])
    version = get_version_string(ref['filename'])
    property_data['schema_name'] = schema_name
    property_data['latest_version'] = version
    property_data['name_and_version'] = schema_name
    if version:
        property_data['name_and_version'] += ' ' + version
    property_data['properties'] = {}

    if 'properties' not in property_data:
        property_data['properties'] = {}
    meta = property_data.get('doc_generator_meta', {})

    if version == '1.0.0':
        version = None

    if (not version) and (schema_name in property_data):
        warnings.warn('Check', schema_name, 'for version problems.',
                      'Are there two files with either version 1.0.0 or no version?')

    data = load_as_json(filename)

    try:
        property_data['definitions'] = data['definitions']
        for ref_part in ref['ref'].split('/'):
            if not ref_part:
                continue
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
        warnings.warn('Unable to find properties in path ' + ref['ref'] + ' from ' + filename)
        return

    meta = extend_metadata(meta, properties, version)
    meta['definitions'] = meta.get('definitions', {})
    definitions = property_data['definitions']
    # Add version metadata for sub-properties in definitions:
    # for prop_name in definitions.keys():
    #     thisprop = definitions[prop_name].get('properties')
    #     if thisprop:
    #         meta['definitions'][prop_name] = extend_metadata(meta['definitions'].get(prop_name, {}),
    #                                                          thisprop, version)
    meta['definitions'] = extend_metadata(meta['definitions'], definitions, version)
    property_data['doc_generator_meta'] = meta

    return property_data


def extend_metadata(meta, properties, version):

    for prop_name in properties.keys():
        props = properties[prop_name]
        if prop_name not in meta:
            meta[prop_name] = {}
            if version: # Track version only when first seen
                meta[prop_name]['version'] = version
        if 'deprecated' in props:
            if 'version_deprecated' not in meta[prop_name]:
                meta[prop_name]['version_deprecated'] = props['deprecated']

        properties[prop_name]['_doc_generator_meta'] = meta[prop_name]

        # build out metadata for sub-properties.
        if props.get('properties'):
            child_props = props['properties']
            meta[prop_name] = extend_metadata(meta[prop_name], child_props, version)

    return meta


def get_version_string(filename):
    """Parse the version string from a filename. Returned format is, e.g., v1.0.1"""

    parts = filename.split('.')
    version = ''
    if parts[1][0] == 'v':
        version = parts[1][1:]
        version = version.replace('_', '.')
    return version


def load_as_json(filename):
    """Load json data from a file, printing an error message on failure."""
    data = {}
    try:
        # Parse file as json
        jsondata = open(filename, 'r', encoding="utf8")
        data = json.load(jsondata)
        jsondata.close()
    except (OSError, json.JSONDecodeError) as ex:
        warnings.warn('Unable to read ' + filename + ': ' + str(ex))

    return data


def write_output(markdown, outfile):
    """Write output to a file."""

    print(markdown, file=outfile)
    outfile.close()
    print(outfile.name, "written.")


def get_schema_name(filename, data):
    """Get the schema name, preferably from a 'title' found in the data, otherwise from filename

    Returns a string or None, the latter indicating that this is an old-style schema that
    should be skipped."""

    schema_name = None

    if 'title' not in data:
        schema_name = filename[:-5]
    else:
        title_parts = data['title'].split('.')
        if len(title_parts) > 3:
            return None

        schema_name = title_parts[0]
        if len(title_parts) > 1 and title_parts[1].startswith('v'):
            schema_name += '.' + title_parts[1]

        if schema_name[0] == '#':
            schema_name = schema_name[1:]

    return schema_name


main()
