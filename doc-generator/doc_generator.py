#! /usr/local/bin/python3
# Copyright Notice:
# Copyright 2016, 2017, 2018, 2019 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: doc_generator.py

Brief: Reads redfish json schema files and generates a GitHub-flavored markdown document
suitable for use with the Slate documentation tool (https://github.com/tripit/slate)


Initial author: Second Rise LLC.
"""

import os
import re
import argparse
import json
import copy
import functools
import warnings
from doc_gen_util import DocGenUtilities
from schema_traverser import SchemaTraverser
import parse_supplement


# Format user warnings simply
class InfoWarning(UserWarning):
    """ A warning class for informational messages that don't need a stack trace. """
    pass

def simple_warning_format(message, category, filename, lineno, file=None, line=None):
    """ a basic format for warnings from this program """
    if category == InfoWarning:
        return '  Info: %s' % (message) + "\n"
    else:
        return '  Warning: %s (%s:%s)' % (message, filename, lineno) + "\n"


warnings.formatwarning = simple_warning_format

class DocGenerator:
    """Redfish Documentation Generator class. Provides 'generate_docs' method."""

    def __init__(self, import_from, outfile, config):
        self.config = config
        self.import_from = import_from
        self.outfile = outfile
        self.property_data = {} # This is an object property for ease of testing.
        self.schema_ref_to_filename = {}
        self.config['payloads'] = None

        if config.get('payload_dir'):
            payload_dir = config.get('payload_dir')
            config['payloads'] = {}
            payload_filenames = [x for x in os.listdir(payload_dir) if x.endswith('.json')]
            for name in payload_filenames:
                f = open(os.path.join(payload_dir, name), 'r')
                data = f.read()
                if data:
                    config['payloads'][name] = data

        if config.get('profile_mode'):
            config['profile'] = DocGenUtilities.load_as_json(config.get('profile_doc'))
            profile_merged = {}

            if 'RequiredProfiles' in config['profile']:
                for req_profile_name in config['profile']['RequiredProfiles'].keys():
                    profile_merged = self.merge_required_profile(
                        profile_merged, req_profile_name,
                        config['profile']['RequiredProfiles'][req_profile_name])

            if 'Registries' in config['profile'] and (config['profile_mode'] != 'subset'):
                config['profile']['registries_annotated'] = {}
                for registry_name in config['profile']['Registries'].keys():
                    registry_summary = self.process_registry(registry_name,
                                                             config['profile']['Registries'][registry_name])
                    config['profile']['registries_annotated'][registry_name] = registry_summary

            profile_resources = self.merge_dicts(profile_merged.get('Resources', {}),
                                                     self.config.get('profile', {}).get('Resources', {}))

            if config['profile_mode'] != 'subset':
                profile_protocol = self.merge_dicts(profile_merged.get('Protocol', {}),
                                                     self.config.get('profile', {}).get('Protocol', {}))
                self.config['profile_protocol'] = profile_protocol

            if not profile_resources:
                warnings.warn('No profile resource data found; unable to produce profile mode documentation.')
                exit()

            # Index profile_resources by Repository & schema name
            profile_resources_indexed = {}
            for schema_name in profile_resources.keys():
                profile_data = profile_resources[schema_name]
                repository = profile_data.get('Repository', 'redfish.dmtf.org/schemas/v1')
                normalized_uri = repository + '/' + schema_name + '.json'
                profile_data['Schema_Name'] = schema_name
                profile_resources_indexed[normalized_uri] = profile_data

            self.config['profile_resources'] = profile_resources_indexed


    def generate_doc(self):
        output = self.generate_docs()
        self.write_output(output, self.outfile)


    def process_registry(self, reg_name, registry_profile):
        """ Given registry requirements from a profile, retrieve the registry data and produce
        a summary based on the profile's requirements.
        """
        registry_reqs = { 'name' : reg_name }

        # Retrieve registry
        reg_repo = registry_profile.get('Repository')
        reg_minversion = registry_profile.get('MinVersion', '1.0.0')
        registry_reqs['minversion'] = reg_minversion
        registry_reqs['profile_requirement'] = registry_profile.get('ReadRequirement', 'Mandatory')
        reg_uri = self.get_versioned_uri(reg_name, reg_repo, reg_minversion)

        if not reg_uri:
            warnings.warn("Unable to find registry file for " + reg_repo + ", " + reg_name +
                          ", minimum version " + reg_minversion)
            return registry_reqs

        # Generate data based on profile
        registry_data = DocGenUtilities.http_load_as_json(reg_uri)
        if registry_data:
            registry_reqs['current_release'] = registry_data['RegistryVersion']
            registry_reqs.update(registry_data)

            for msg in registry_profile['Messages']:
                if msg in registry_reqs['Messages']:
                    registry_reqs['Messages'][msg]['profile_requirement'] = registry_profile['Messages'][msg].get('ReadRequirement', 'Mandatory')
                else:
                    warnings.warn("Profile specifies requirement for nonexistent Registry Message: " +
                                  reg_name + " " + msg)

        return registry_reqs


    def get_versioned_uri(self, base_name, repo, min_version, is_local_file=False):
        """ Get a versioned URI for the base_name schema.
        Parameters:
         base_name     -- Base name of the schema, e.g., "Resource"
         repo          -- URI of the the repo where the schema is expected to be found.
         min_version   -- Minimum acceptable version.
         is_local_file -- Find file on local system.

        If a matching URI is found among links at the repo address, it will be returned.
        If not, a URI will be composed based on repo, base_name, and version. (This
        may succeed if the repo does not provide a directory index.)

        Versions must match on the major version, with minor.errata equal to or greater than
        what is specified in min_version.
        """

        versioned_uri = None

        if is_local_file:
            repo_links = DocGenUtilities.local_get_links(repo)
        else:
            repo_links = DocGenUtilities.html_get_links(repo)

        if repo_links:
            minversion_parts = re.findall(r'(\d+)', min_version)

            candidate = None
            candidate_strength = 0
            for rl in repo_links:
                base = base_name + '.'
                if rl.startswith(repo) and base in rl and rl.endswith('.json'):
                    parts = rl[0:-5].rsplit(base, 1)
                    if len(parts) == 2:
                        suffix = parts[1]
                        version_parts = re.findall(r'(\d+)', suffix)
                        # Major version must match; minor.errata must be >=.
                        if version_parts[0] != minversion_parts[0]:
                            continue
                        if version_parts[1] > minversion_parts[1]:
                            strength = self.version_index(version_parts)
                            if strength > candidate_strength:
                                candidate_strength = strength
                                candidate = rl
                            continue
                        if version_parts[1] == minversion_parts[1]:
                            if len(version_parts) == 3 and len(minversion_parts) == 3:
                                if version_parts[2] >= minversion_parts[2]:
                                    strength = self.version_index(version_parts)
                                    if strength > candidate_strength:
                                        candidate_strength = strength
                                        candidate = rl
                            elif len(version_parts) == 2:
                                strength = self.version_index(version_parts)
                                if strength > candidate_strength:
                                    candidate_strength = strength
                                    candidate = rl
            if candidate:
                versioned_uri = candidate

        elif is_local_file:
            # Build URI from repo, name, and minversion:
            versioned_uri = '/'.join([repo, base_name]) + '.v' + min_version + '.json'

        return versioned_uri


    def merge_required_profile(self, merged_data, req_profile_name, req_profile_info):
        """ Merge a required profile into merged_data (a dict). May result in recursive calls. """

        req_profile_repo = req_profile_info.get('Repository', 'http://redfish.dmtf.org/profiles')
        req_profile_minversion = req_profile_info.get('MinVersion', '1.0.0')
        version_string = req_profile_minversion.replace('.', '_')
        req_profile_data = None

        # Retrieve profile.
        # req_profile_repo will be a fully-qualified URI. It may be overridden by
        # uri-to-local mapping.
        base_uri = '/'.join([req_profile_repo, req_profile_name])
        if '://' in base_uri:                                  # This is expected.
            protocol, base_uri = base_uri.split('://')

        is_local_file = False
        for partial_uri in self.config['profile_uri_to_local'].keys():
            if base_uri.startswith(partial_uri):
                local_path = self.config['profile_uri_to_local'][partial_uri]
                if partial_uri.endswith(req_profile_name):
                    req_profile_repo = local_path[0:-len(req_profile_name)]
                    pass
                else:
                    req_profile_repo = local_path
                is_local_file = True
                break

        req_profile_uri = self.get_versioned_uri(req_profile_name, req_profile_repo,
                                                 version_string, is_local_file)

        if not req_profile_uri:
            warnings.warn("Unable to find Profile for " + req_profile_repo + ", " +
                          req_profile_name + ", minimum version: " + req_profile_minversion)
            return merged_data


        if is_local_file:
            req_profile_data = DocGenUtilities.load_as_json(req_profile_uri)
        else:
            req_profile_data = DocGenUtilities.http_load_as_json(req_profile_uri)

        if req_profile_data:
            if 'RequiredProfiles' in req_profile_data:
                for req_profile_name in req_profile_data['RequiredProfiles'].keys():
                    merged_data = self.merge_required_profile(
                        merged_data, req_profile_name, req_profile_data['RequiredProfiles'][req_profile_name])

            merged_data = {
                'Resources': self.merge_dicts(merged_data.get('Resources', {}), req_profile_data.get('Resources', {})),
                'Protocol': self.merge_dicts(merged_data.get('Protocol', {}), req_profile_data.get('Protocol', {}))
                }

        return merged_data


    def merge_dicts(self, dict1, dict2):
        """ Merge two dictionaries recursively, with dict1 "winning." Returns the merged result. """
        return self._merge_dicts(dict1.copy(), dict2.copy())


    def _merge_dicts(self, dict1, dict2):
        """ Merge two dictionaries recursively. Modifies input. Returns the merged result.
        For this pattern and others:
           https://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
        """

        # merge elements that appear in both dictionaries:
        for k, v in dict1.items():
            if k in dict2:
                if isinstance(v, dict) and isinstance(dict2[k], dict):
                    dict2[k] = self._merge_dicts(v, dict2[k])
                elif isinstance(v, list) and isinstance(dict2[k], list):
                    for elt in v:
                        if elt not in dict2[k]:
                            dict2[k].append(elt)
                elif isinstance(v, str) and isinstance(dict2[k], str):
                    # dict1 wins
                    dict2[k] = v
                else:
                    warnings.warn("Merging two items with different types would fail. Probably attempting to merge two profiles; debugging here may be required.")
            else:
                dict2[k] = v

        return dict2


    @staticmethod
    def get_files(text_input):
        """From text input (command line or parsed from file), create a list of files. """
        files_to_process = []
        for file_to_import in text_input:
            if os.path.isdir(file_to_import):
                for root, _, files in os.walk(file_to_import):
                    # NB: this is an adequate sort for file-grouping purposes. It's not guaranteed to sort versions correctly.
                    files.sort(key=str.lower)
                    for filename in files:
                        if filename[-4:] == 'json':
                            files_to_process.append(os.path.join(root, filename))
            elif os.path.isfile(file_to_import):
                files_to_process.append(file_to_import)
            else:
                warnings.warn('Oops, ' + file_to_import + ' not found, or contains no .json files.\n')
        return files_to_process


    def generate_docs(self, level=0):
        """Given a list of files, generate a block of documentation.

        This is the main loop of the product.
        """
        files_to_process = self.get_files(self.import_from)
        grouped_files, schema_data = self.group_files(files_to_process)

        self.property_data = {}
        collection_data = {}

        # First expand the grouped files -- these are the schemas that get first-class documentation sections
        for normalized_uri in grouped_files.keys():
            data = self.process_files(normalized_uri, grouped_files[normalized_uri])
            if not data:
                # If we're in profile mode, this is probably normal.
                if not self.config['profile_mode']:
                    warnings.warn("Unable to process files for " + normalized_uri)
                continue
            data['uris'] = schema_data[normalized_uri].get('_uris', [])

            if normalized_uri.endswith('Collection.json'):
                [preamble, collection_name] = normalized_uri.rsplit('/', 1)
                collection_data[collection_name] = data['uris']

            self.property_data[normalized_uri] = data

            latest_info = grouped_files[normalized_uri][-1]
            latest_file = os.path.join(latest_info['root'], latest_info['filename'])
            latest_data = DocGenUtilities.load_as_json(latest_file)
            latest_data['_is_versioned_schema'] = latest_info.get('_is_versioned_schema')
            latest_data['_is_collection_of'] = latest_info.get('_is_collection_of')
            latest_data['_schema_name'] = latest_info.get('schema_name')

            # If we have data in the unversioned file, we need to overlay that.
            # We did this the same way for property_data. (Simplify?)
            latest_data = self.apply_unversioned_data_file(normalized_uri, latest_data)
            schema_data[normalized_uri] = latest_data

        # Also process and version definitions in any "other" files. These are files without top-level $ref objects.
        schema_data = self.process_unversioned_files(schema_data, self.config['uri_to_local'])

        traverser = SchemaTraverser(schema_data, self.config['uri_to_local'])

        # Generate output
        if self.config.get('output_content') == 'property_index':
            from doc_formatter import PropertyIndexGenerator
            self.generator = PropertyIndexGenerator(self.property_data, traverser, self.config, level)
            return self.generator.generate_output()

        if self.config['output_format'] == 'markdown':
            from doc_formatter import MarkdownGenerator
            self.generator = MarkdownGenerator(self.property_data, traverser, self.config, level)
        elif self.config['output_format'] == 'html':
            from doc_formatter import HtmlGenerator
            self.generator = HtmlGenerator(self.property_data, traverser, self.config, level)
        elif self.config['output_format'] == 'csv':
            from doc_formatter import CsvGenerator
            self.generator = CsvGenerator(self.property_data, traverser, self.config, level)

        return self.generator.generate_output()


    def group_files(self, files):
        """Traverse files, grouping any unversioned/versioned schemas together.

        Parses json to identify versioned files.
        Returns a dict of {normalized_uri : [versioned files]} where each
        versioned file is a dict of {root, filename, ref path, schema_name,
        _is_versioned_schema, _is_collection_of}.
        """

        file_list = [os.path.abspath(filename) for filename in files]
        grouped_files = {}
        all_schemas = {}
        missing_files = []
        processed_files = []

        for filename in file_list:
            # Get the (probably versioned) filename, and save the data:
            root, _, fname = filename.rpartition(os.sep)

            data = DocGenUtilities.load_as_json(filename)

            schema_name = SchemaTraverser.find_schema_name(fname, data)
            if schema_name is None: continue

            normalized_uri = self.construct_uri_for_filename(filename)
            self.schema_ref_to_filename[normalized_uri] = filename

            data['_schema_name'] = schema_name
            all_schemas[normalized_uri] = data

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
            ref_files_by_version = {}

            # is_versioned_schema will be True if there is an "anyOf" pointing to one or more versioned files.
            is_versioned_schema = False

            # is_collection_of will contain the type of objects in the collection.
            is_collection_of = None

            if 'anyOf' in data:

                for obj in data['anyOf']:
                    if '$ref' in obj:
                        refpath_uri, refpath_path = obj['$ref'].split('#')
                        if refpath_path == '/definitions/idRef':
                            continue
                        ref_fn = refpath_uri.split('/')[-1]
                        # Skip files that are not present.
                        ref_filename = os.path.abspath(os.path.join(root, ref_fn))
                        if ref_filename in file_list:
                            version_string = DocGenUtilities.get_ref_version(ref_fn)
                            file_data = {'root': root,
                                         'filename': ref_fn,
                                         'ref': refpath_path,
                                         'schema_name': schema_name,
                                         'version': version_string}
                            if version_string not in ref_files_by_version:
                                ref_files_by_version[version_string] = [ file_data ]
                            else:
                                ref_files_by_version[version_string].append(file_data) # Unexpected, but roll with it.
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
                                    is_collection_of = self.normalize_ref(member_ref)
                        ref_files = []
                        continue

                # Sort the ref_files by version.
                version_keys = sorted(ref_files_by_version.keys(), key=functools.cmp_to_key(DocGenUtilities.compare_versions))
                for vk in version_keys:
                    for file_data in ref_files_by_version[vk]:
                        ref_files.append(file_data)

            elif '$ref' in data:
                refpath_uri, refpath_path = data['$ref'].split('#')
                if refpath_path == '/definitions/idRef':
                    continue

                ref_fn = refpath_uri.split('/')[-1]
                # Skip files that are not present.
                ref_filename = os.path.abspath(os.path.join(root, ref_fn))
                if ref_filename in file_list:
                    ref_files.append({'root': root,
                                      'filename': ref_fn,
                                      'ref': refpath_path,
                                      'schema_name': schema_name})
                elif ref_filename not in missing_files:
                    missing_files.append(ref_filename)

            else:
                ref = original_ref

            if 'uris' in data:
                # Stash these in the unversioned schema_data.
                all_schemas[normalized_uri]['_uris'] = data['uris']

            if len(ref_files):
                # Add the _is_versioned_schema and  is_collection_of hints to each ref object
                is_versioned_schema = True
                [x.update({'_is_versioned_schema': is_versioned_schema, '_is_collection_of': is_collection_of})
                 for x in ref_files]
                grouped_files[normalized_uri] = ref_files

            if not normalized_uri in grouped_files:
                # this is not an unversioned schema after all.
                grouped_files[normalized_uri] = [{'root': root,
                                                  'filename': fname,
                                                  'ref': ref,
                                                  'schema_name': schema_name,
                                                  '_is_versioned_schema': is_versioned_schema,
                                                  '_is_collection_of': is_collection_of}]

            # Note these files as processed:
            processed_files.append(filename)
            for file_refs in grouped_files[normalized_uri]:
                ref_filename = os.path.join(file_refs['root'], file_refs['filename'])
                processed_files.append(ref_filename)

        if len(missing_files):
            numfiles = len(missing_files)
            if numfiles <= 10:
                missing_files_list = '\n   '.join(missing_files)
            else:
                missing_files_list = '\n   '.join(missing_files[0:9]) + "\n   and " + str(numfiles - 10) + " more."
            warnings.warn(str(numfiles) + " referenced files were missing: \n   " + missing_files_list)

        return grouped_files, all_schemas


    def process_files(self, schema_ref, refs):
        """Loop through a set of refs and process the specified files into property data.

        Returns a property_data object consisting of the properties from the last ref file.
        """
        property_data = {}
        unversioned_ref = None

        if schema_ref not in refs:
            unversioned_ref = schema_ref

        for info in refs:
            property_data = self.process_data_file(schema_ref, info, property_data)

        if unversioned_ref:
            property_data = self.apply_unversioned_data_file(unversioned_ref, property_data)
        return property_data


    def process_data_file(self, schema_ref, ref, property_data):
        """Process a single file by ref name, adding some annotations to property_data."""

        filename = os.path.join(ref['root'], ref['filename'])
        normalized_uri = self.construct_uri_for_filename(filename)

        # Get the un-versioned filename for match against profile keys
        if '.v' in filename:
            generalized_uri = self.construct_uri_for_filename(filename.split('.v')[0]) + '.json'
        else:
            generalized_uri = self.construct_uri_for_filename(filename)

        profile_mode = self.config.get('profile_mode')
        profile = self.config.get('profile_resources', {})

        data = DocGenUtilities.load_as_json(filename)
        schema_name = SchemaTraverser.find_schema_name(filename, data, True)

        version = self.get_version_string(ref['filename'])


        property_data['schema_name'] = schema_name
        property_data['name_and_version'] = schema_name
        property_data['normalized_uri'] = normalized_uri
        property_data['latest_version'] = version

        if data.get('release'):
            release_history = property_data.get('release_history')
            if not release_history:
                property_data['release_history'] = []
                release_history = property_data.get('release_history')
            release_history.append({'version': version, 'release': data.get('release')})

        min_version = False
        if profile_mode:
            schema_profile = profile.get(generalized_uri)
            if schema_profile:
                if profile_mode == 'subset':
                    property_data['name_and_version'] += ' ' + version
                else:
                    min_version = schema_profile.get('MinVersion')
                    if min_version:
                        if version:
                            property_data['name_and_version'] += ' v' + min_version + '+ (current release: v' + version + ')'
                        else:
                            # this is unlikely
                            property_data['name_and_version'] += ' v' + min_version + '+'
                    elif version:
                        property_data['name_and_version'] += ' ' + version
            else:
                # Skip schemas that aren't mentioned in the profile:
                return {}
        elif version:
            property_data['name_and_version'] += ' ' + version

        if 'properties' not in property_data:
            property_data['properties'] = {}
        if 'definitions' not in property_data:
            property_data['definitions'] = {}

        if (version == '1.0.0') and (schema_ref in property_data):
            warnings.warn('Check', schema_ref, 'for version problems.',
                          'Are there two files with either version 1.0.0 or no version?')

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
            return {}

        return property_data


    def apply_unversioned_data_file(self, ref, property_data):
        """ Overlay the unversioned data on this property_data.

        Now applying additions only, at the definitions/prop_name level. So if a property is delineated in the versioned
        file, it will not be updated here. """

        filename = self.schema_ref_to_filename[ref]
        normalized_uri = self.construct_uri_for_filename(filename)

        profile_mode = self.config.get('profile_mode')
        profile = self.config.get('profile_resources', {})

        data = DocGenUtilities.load_as_json(filename)
        schema_name = SchemaTraverser.find_schema_name(filename, data, True)

        # If there is no definitions block, there's nothing to do:
        if 'definitions' not in data:
            return property_data

        ref = data.get('$ref', '')
        element_to_skip = False

        if ref.startswith('#/definitions/'):
            # If $ref was present (and it surely was), we want to skip the element identified by it.
            # It will consist of an anyOf that led us to the versioned schemas.
            element_to_skip = ref[14:]

        if profile_mode:
            schema_profile = profile.get(normalized_uri)
            if not schema_profile:
                # Skip schemas that aren't mentioned in the profile:
                return property_data

        definitions = data.get('definitions')
        if 'definitions' not in property_data:
            property_data['definitions'] = {}

        for prop_name, prop_info in definitions.items():
            if prop_name == element_to_skip or prop_name in property_data['definitions'].keys():
                continue
            property_data['definitions'][prop_name] = prop_info

        return property_data


    def process_unversioned_files(self, schema_data, uri_to_local):
        """ Process version in individually-versioned properties in files lacking a $ref.
        That complicated rule catches some of the "referenced objects."
        """

        interim_traverser = SchemaTraverser(schema_data, uri_to_local)
        for filename, data in schema_data.items():
            if '$ref' in data:
                continue
            # Iterate definitions, then properties:
            for prop_name, prop_data in data.get('definitions', {}).items():
                schema_data[filename]['definitions'][prop_name] = self.generate_version_data(prop_name, prop_data, interim_traverser)
            for prop_name, prop_data in data.get('properties', {}).items():
                schema_data[filename]['properties'][prop_name] = self.generate_version_data(prop_name, prop_data, interim_traverser)

        return schema_data


    def generate_version_data(self, prop_name, prop_data, interim_traverser):

        if 'anyOf' in prop_data:
            prop_anyof = prop_data['anyOf']
            skip_null = len([x for x in prop_anyof if '$ref' in x])
            sans_null = [x for x in prop_anyof if x.get('type') != 'null']
            is_nullable = skip_null and [x for x in prop_anyof if x.get('type') == 'null']
            if len(sans_null) > 1:
                match_ref = unversioned_ref = ''
                latest_ref = latest_version = ''
                refs_by_version = {}
                for elt in prop_anyof:
                    this_ref = elt.get('$ref')
                    if this_ref:
                        unversioned_ref = DocGenUtilities.make_unversioned_ref(this_ref)
                        this_version = DocGenUtilities.get_ref_version(this_ref)
                        if this_version:
                            cleaned_version = this_version.replace('_', '.')
                            # WORKAROUND for CSDL-to-JSON bug that inappropriately adds properties
                            # in errata versions prior to their actual addition:
                            # version_bits = cleaned_version.split('.')
                            # if ((len(version_bits) == 3) and (version_bits[2] != '0')):
                            #     pass # continue
                            # else:
                            refs_by_version[cleaned_version] = this_ref
                        else:
                            break

                    if not match_ref:
                        match_ref = unversioned_ref
                    if not latest_ref:
                        latest_ref = this_ref
                        latest_version = cleaned_version
                    else:
                        compare = DocGenUtilities.compare_versions(latest_version, cleaned_version)
                        if compare < 0:
                            latest_version = cleaned_version
                    if match_ref != unversioned_ref: # These are not all versions of the same thing
                        break

                if match_ref == unversioned_ref:
                    # Process refs_by_version to get the version-added and deprecated strings
                    # incorporated into the properties for the latest version:
                    updated_data = self.update_versioned_properties(unversioned_ref, refs_by_version, interim_traverser)
                    if updated_data:
                        prop_data = updated_data

        return prop_data


    def update_versioned_properties(self, common_ref, refs_by_version, traverser):
        """ This is for generating versioned information for properties in supporting schemas,
        in which a property definition contains an "anyOf" linking to versioned properties.

        From a dict of version -> $ref, generate a prop_info structure with version information.
        """

        prop_info =  {}

        # Check latest version in refs_by_version against prop_info _latest_version:
        latest_version = '0.0.0'

        # Walk refs_by_version, extending prop_info
        ref_keys = [x for x in refs_by_version.keys()]
        ref_keys.sort(key=functools.cmp_to_key(DocGenUtilities.compare_versions))

        if not len(ref_keys):
            return prop_info # No changes to make
        else:
            for this_version in ref_keys:
                this_ref = refs_by_version[this_version]

                ref_info = traverser.find_ref_data(this_ref)
                if not ref_info:
                    warnings.warn("Can't find schema file for " + this_ref)
                    continue
                if 'properties' in ref_info:
                    ref_properties = ref_info['properties']

                    # Follow refs in properties, if they are local to the same schema.
                    [this_schema, rest] = this_ref.split('#')
                    for prop_name, props in ref_properties.items():
                        prop_ref = None
                        if '$ref' in props and (props['$ref'].startswith('#') or props['$ref'].startswith(this_schema)):
                            if props['$ref'].startswith('#'):
                                prop_ref = this_schema + props['$ref']
                            else:
                                prop_ref = props['$ref']
                        elif 'anyOf' in props:
                            # may be "$ref or null"
                            for elt in props['anyOf']:
                                if elt.get('type') == 'null':
                                    continue
                                if elt.get('$ref'):
                                    # Don't follow $ref if multiple are offered. Too complicated?
                                    if prop_ref:
                                        prop_ref = None
                                        break
                                    else:
                                        if elt['$ref'].startswith(this_schema):
                                            prop_ref = elt['$ref']
                                        if elt['$ref'].startswith('#'):
                                            prop_ref = this_schema + elt['$ref']

                        if prop_ref:
                            child_ref = traverser.find_ref_data(prop_ref)
                            if child_ref and 'properties' in child_ref:
                                if ref_properties[prop_name].get('anyOf'):
                                    del(ref_properties[prop_name]['anyOf']) # We're replacing this.
                                child_ref_properties = child_ref['properties']
                                ref_properties[prop_name]['properties'] = child_ref_properties
                                ref_properties[prop_name]['type'] = 'object'

                    # Update any relative refs in ref_properties with this_ref base:
                    [base_ref, rest] = this_ref.split('#')
                    [common_base_ref, rest] = common_ref.split('#')
                    if common_base_ref != base_ref:
                        ref_properties = self.absolutize_refs(base_ref, ref_properties)

            if not ref_info:
                return prop_info

            # Update saved property to latest version:
            prop_info = copy.deepcopy(ref_info)
            prop_info['properties'] = ref_properties
            prop_info['_latest_version'] = this_version
            prop_info['_ref_uri'] = common_ref

        return prop_info


    def absolutize_refs(self, base_ref, prop_data):
        """ Find any relative $ref in prop_data (recursively) and prepend base_ref """

        for key, value in prop_data.items():
            if key == '$ref':
                if value.startswith('#'):
                    value = base_ref + value
            elif isinstance(value, dict):
                value = self.absolutize_refs(base_ref, value)
            elif isinstance(value, list):
                updated = []
                for elt in value:
                    if isinstance(elt, dict):
                        updated.append(self.absolutize_refs(base_ref, elt))
                    else:
                        updated.append(elt)
                value = updated
            prop_data[key] = value

        return prop_data


    @staticmethod
    def get_version_string(filename):
        """Parse the version string from a filename. Returned format is, e.g., v1.0.1"""

        parts = filename.split('.')
        version = ''
        if parts[1][0] == 'v':
            version = parts[1][1:]
            version = version.replace('_', '.')
        return version


    @staticmethod
    def write_output(markdown, outfile):
        """Write output to a file."""

        print(markdown, file=outfile)
        outfile.close()
        print(outfile.name, "written.")


    def construct_uri_for_filename(self, fname):
        """Use the schema URI mapping to construct a URI for this file"""

        local_to_uri = self.config.get('local_to_uri')
        if local_to_uri:
            for local_path in local_to_uri.keys():
                if fname.startswith(local_path):
                    fname = fname.replace(local_path, local_to_uri[local_path])
                    return fname.replace(os.sep, '/')

        return fname

    @staticmethod
    def normalize_ref(ref):
        """Get the normalized version of ref we use to index a schema.

        Get the URL part of ref and strip off the protocol."""
        if '#' in ref:
            ref, path = ref.split('#')

        if '://' in ref:
            protocol, ref = ref.split('://')

        return ref


    @staticmethod
    def version_index(parts):
        """ Create a numeric index representing the "size" of a multipart version """

        idx = 0
        multiplier = 100
        for part in parts:
            idx = idx + (multiplier * int(part))
            multiplier = multiplier/10
        return idx


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
        'excluded_pattern_props': [],
        'omit_version_in_headers': False,
        'actions_in_property_table': True,
        'schema_supplement': None,
        'normative': False,
        'escape_chars': [],
        'cwd': os.getcwd(),
        'uri_replacements': {},
        'local_to_uri': {},
        'uri_to_local': {},
        'profile_mode': False,
        'profile_doc': None,
        'profile_resources': {},
        'profile': {},

        # These values indicate whether to override config with supplement data, and may be useful for debugging
        'uri_mapping_from_config': False
        }

    help_description = 'Generate documentation for Redfish JSON schema files.\n\n'
    help_epilog = ('Example:\n   doc_generator.py --format=html\n   doc_generator.py'
                   ' --format=html'
                   ' --out=/path/to/output/index.html /path/to/spmf/json-files')
    parser = argparse.ArgumentParser(description=help_description,
                                     epilog=help_epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--config', dest="config_file",
                        help=('Path to a config file, containing configuration '
                              ' in JSON format. '
                              ))

    parser.add_argument('import_from', metavar='import_from', nargs='*',
                        help=('Name of a file or directory to process (wild cards are acceptable). '
                              'Default: json-schema'))
    parser.add_argument('-n', '--normative', action='store_true', dest='normative', default=False,
                        help='Produce normative (developer-focused) output')
    parser.add_argument('--format', dest='format',
                        choices=['markdown', 'html', 'csv'], help='Output format')
    parser.add_argument('--out', dest='outfile',
                        help=('Output file (default depends on output format: '
                              'output.md for Markdown, index.html for HTML, output.csv for CSV'))
    parser.add_argument('--sup', dest='supfile',
                        help=('Path to the supplemental material document. '
                              'Default is usersupplement.md for user-focused documentation, '
                              'and devsupplement.md for normative documentation.'))
    parser.add_argument('--payload_dir', metavar='payload_dir',
                        help=('Directory location for JSON payload and Action examples. Optional.'
                              'Within this directory, use the following naming scheme for example files: '
                              '<schema_name>-v<major_version>-example.json for JSON payloads, '
                              '<schema_name-v<major_version>-action-<action_name>.json for action examples.'))
    parser.add_argument('--profile', dest='profile_doc',
                        help=('Path to a JSON profile document, for profile output.'))
    parser.add_argument('-t', '--terse', action='store_true', dest='profile_terse',
                        help=('Terse output (meaningful only with --profile). By default, '
                              'profile output is verbose and includes all properties regardless of '
                              'profile requirements. "Terse" output is intended for use by '
                              'Service developers, including only the subset of properties with '
                              'profile requirements.'))
    parser.add_argument('--subset', dest='subset_doc',
                        help=('Path to a JSON profile document. Generates "Schema subset" '
                              'output, with the subset defined in the JSON profile document.'))

    parser.add_argument('--property_index', action='store_true', dest='property_index', default=False,
                        help='Produce Property Index output.')
    parser.add_argument('--property_index_config_out', dest='property_index_config_out',
                        metavar='CONFIG_FILE_OUT',
                        default=False, help='Generate updated config file, with specified filename (property_index mode only).')
    parser.add_argument('--escape', dest='escape_chars',
                        help=("Characters to escape (\\) in generated Markdown. "
                              "For example, --escape=@#. Use --escape=@ if strings with embedded @ "
                              "are being converted to mailto links."))

    command_line_args = parser.parse_args()
    args = vars(command_line_args)

    # Check for a config_file. If there is one, we'll update args based on it.
    config_file_read = False
    if args['config_file']:
        try:
            with open(args['config_file'], 'r', encoding="utf8") as config_file:
                config_data = json.load(config_file)
                if config_data.get('property_index') or args['property_index']:
                    config['property_index_config'] = config_data # We will amend this on output, if requested
                if config_data.get('uri_mapping'):
                    # Populate the URI mappings
                    config['uri_to_local'] = {}
                    config['local_to_uri'] = {}
                    config['uri_mapping_from_config'] = True
                    for k, v in config_data.get('uri_mapping').items():
                        vpath = os.path.abspath(v)
                        config['uri_to_local'][k] = vpath
                        config['local_to_uri'][vpath] = k
                config_file_read = True
        except (OSError) as ex:
            warnings.warn('Unable to open ' + args['config_file'] + ' to read: ' + str(ex))
        except (json.decoder.JSONDecodeError) as ex:
            warnings.warn(args['config_file'] + " appears to be invalid JSON. JSON decoder reports: " + str(ex))
            exit()

    if config_file_read:
        config_args = ['supfile', 'format', 'import_from', 'outfile', 'payload_dir', 'normative',
                           'profile_doc', 'profile_terse', 'subset_doc',
                           'property_index', 'property_index_config_out',
                           'escape_chars'
                           ]
        for x in config_args:
            if config_data.get(x) and (x not in args or args[x] is None):
                args[x] = config_data[x]

        # config_flags don't have command-line overrides; they should be added to config directly.
        # We want to capture the fact that a flag was set, even if false, as this should override
        # the corresponding keyword in the supplemental markdown document.
        config_flags = ['add_toc', 'units_translation']
        for x in config_flags:
            if x in config_data:
                config[x] = config_data[x]

        # if config_data includes an object_reference_disposition object, vet it a bit and store it.
        if config_data.get('object_reference_disposition'):
            obj_ref_disp = config_data.get('object_reference_disposition')
            ref_disp_map = {}
            valid_keys = ['common_object', 'include']
            for x, refs in obj_ref_disp.items():
                if x not in valid_keys:
                    warnings.warn('Config file entry "object_reference_disposition" contains an unrecognized key: "'
                                      + x + '", ignoring it.')
                else:
                    for ref in refs:
                        ref_disp_map[ref] = x
            config['reference_disposition'] = ref_disp_map

    # set defaults:
    arg_defaults = {
        'format' : 'markdown',
        'outfile' : 'output.md',
        }
    for param, default in arg_defaults.items():
        if not args[param]:
            args[param] = default

    config['output_format'] = args['format']
    if args['property_index']:
        config['output_content'] = 'property_index'
        config['write_config_to'] = args['property_index_config_out']

    else:
        config['output_content'] = 'full_doc'

    if len(args['import_from']):
        import_from = args['import_from']
    else:
        import_from = [ os.path.join(config.get('cwd'), 'json-schema') ]

    # Determine outfile and verify that it is writeable:
    outfile_name = args['outfile']
    if outfile_name == 'output.md':
        if config['output_format'] == 'html':
            outfile_name = 'index.html'
        if config['output_format'] == 'csv':
            outfile_name = 'output.csv'
        if config['output_content'] == 'property_index':
            outfile_name = 'property_index'
            if config['output_format'] == 'html':
                outfile_name += '.html'
            if config['output_format'] == 'csv':
                outfile_name += '.csv'
            if config['output_format'] == 'markdown':
                outfile_name += '.md'

    try:
        outfile = open(outfile_name, 'w', encoding="utf8")
    except (OSError) as ex:
        warnings.warn('Unable to open ' + outfile_name + ' to write: ' + str(ex))
        exit();

    # If payload_dir was provided, verify that it is a readable directory:
    if args['payload_dir']:
        try:
            if os.path.isdir(args['payload_dir']):
                config['payload_dir'] = args['payload_dir']
            else:
                warnings.warn('"' + args['payload_dir'] + '" is not a directory. Exiting.')
                exit();
        except (Exception) as ex:
            warnings.warn('Unable to read payload_dir "' + payload_dir + '"; ' + str(ex))
            exit();

    if config.get('output_content') == 'property_index':
         if not config_file_read:
             # Minimal config is required; we'll be adding to this.
             config['property_index_config'] = {'DescriptionOverrides': {},
                                                'ExcludedProperties': []}
         else:
             if 'ExcludedProperties' not in config['property_index_config']:
                 config['property_index_config'] == config.get('excluded_properties', [])

         if args['supfile']:
            try:
                with open(args['supfile'], 'r', encoding="utf8") as supfile:
                    boilerplate = supfile.read()
                    if '[insert property index]' in boilerplate:
                        config['property_index_boilerplate'] = boilerplate
                    else:
                        warnings.warn("Supplemental input file lacks the '[insert property index]' marker; ignoring.")
            except (OSError) as ex:
                warnings.warn('Unable to open ' + args['supfile'] + ' to read: ' +  str(ex))
    else:
        # In any mode other than property_index, we should have a supplemental file.
        # Ensure supfile is readable (if not, warn but proceed)
        supfile_expected = False
        if args['supfile']:
            supfile = args['supfile']
            supfile_expected = True
        elif args['normative']:
            supfile = config.get('cwd') + '/devsupplement.md'
        else:
            supfile = config.get('cwd') + '/usersupplement.md'

        try:
            supfile = open(supfile, 'r', encoding="utf8")
            config['supplemental'] = parse_supplement.parse_file(supfile)
            supfile.close()
        except (OSError) as ex:
            if supfile_expected:
                warnings.warn('Unable to open ' + supfile + ' to read: ' +  str(ex))
            else:
                warnings.warn('No supplemental file specified and ' + supfile +
                              ' not found. Proceeding.')

    # Check profile document, if specified
    if args['profile_doc']:
        if args['profile_terse']:
            config['profile_mode'] = 'terse'
        else:
            config['profile_mode'] = 'verbose'

        profile_doc = args['profile_doc']
        try:
            profile = open(profile_doc, 'r', encoding="utf8")
            config['profile_doc'] = profile_doc
        except (OSError) as ex:
            warnings.warn('Unable to open ' + profile_doc + ' to read: ' +  str(ex))
            exit()

    if args['subset_doc']:
        config['profile_mode'] = 'subset'
        profile_doc = args['subset_doc']
        try:
            profile = open(profile_doc, 'r', encoding="utf8")
            config['profile_doc'] = profile_doc
        except (OSError) as ex:
            warnings.warn('Unable to open ' + profile_doc + ' to read: ' +  str(ex))
            exit()

    if args['profile_terse'] and not args['profile_doc']:
        warnings.warn('"Terse output (-t or --terse) requires a profile (--profile).', InfoWarning)
        exit()

    if 'keywords' in config['supplemental']:
        # Promote the keywords to top-level keys.
        for key, val in config['supplemental']['keywords'].items():
            if key not in config:
                config[key] = val

    if 'Schema Documentation' in config['supplemental']:
        config['uri_replacements'] = config['supplemental']['Schema Documentation']


    excluded_annotations = {}
    if 'excluded_annotations' in config_data:
        excluded_annotations['exact'] = [x for x in config_data['excluded_annotations'] if not x.startswith('*')]
        excluded_annotations['wildcard'] = [x[1:] for x in config_data['excluded_annotations'] if x.startswith('*')]
    elif 'Excluded Annotations' in config['supplemental']:
        excluded_annotations['exact'] = config['supplemental']['Excluded Annotations'].get('exact_match')
        excluded_annotations['wildcard'] = config['supplemental']['Excluded Annotations'].get('wildcard_match')
    if excluded_annotations.get('exact'):
        excl = excluded_annotations.get('exact')
        config['excluded_properties'].extend(excl)
        config['excluded_annotations'].extend(excl)
    if excluded_annotations.get('wildcard'):
        excl = excluded_annotations.get('wildcard')
        config['excluded_by_match'].extend(excl)
        config['excluded_annotations_by_match'].extend(excl)

    excluded_properties = {}
    if 'excluded_properties' in config_data:
        excluded_properties['exact'] = [x for x in config_data['excluded_properties'] if not x.startswith('*')]
        excluded_properties['wildcard'] = [x[1:] for x in config_data['excluded_properties'] if x.startswith('*')]
    elif 'Excluded Properties' in config['supplemental']:
        excluded_properties['exact'] = config['supplemental']['Excluded Properties'].get('exact_match', [])
        excluded_properties['wildcard'] = config['supplemental']['Excluded Properties'].get('wildcard_match', [])
    if excluded_properties.get('exact'):
        config['excluded_properties'].extend(excluded_properties['exact'])
    if excluded_properties.get('wildcard'):
        config['excluded_by_match'].extend(excluded_properties['wildcard'])

    excluded_schemas = {}
    if 'excluded_schemas' in config_data:
        excluded_schemas['exact'] = [x for x in config_data['excluded_schemas'] if not x.startswith('*')]
        excluded_schemas['wildcard'] = [x[1:] for x in config_data['excluded_schemas'] if x.startswith('*')]
    elif 'Excluded Schemas' in config['supplemental']:
        excluded_schemas['exact'] = config['supplemental']['Excluded Schemas'].get('exact_match')
        excluded_schemas['wildcard'] = config['supplemental']['Excluded Schemas'].get('wildcard_match')
    if excluded_schemas.get('exact'):
        config['excluded_schemas'] = excluded_schemas['exact']
    if excluded_schemas.get('wildcard'):
        config['excluded_schemas_by_match'] = excluded_schemas['wildcard']

    # We will get "exact_match" and "wildcard_match" from supplemental, but "wildcard_match" doesn't
    # make sense for patterns. On the off chance that someone starts a pattern with * and it gets scooped
    # into wildcard_match, we will pull the contents of that list back in.
    excluded_patterns = {}
    if 'excluded_pattern_properties' in config_data:
        config['excluded_pattern_props'].extend([x for x in config_data['excluded_pattern_properties']])
    elif 'Excluded patternProperties' in config['supplemental']:
        config['excluded_pattern_props'].extend(config['supplemental']['Excluded patternProperties'].get('exact_match'))
        config['excluded_pattern_props'].extend(config['supplemental']['Excluded patternProperties'].get('wildcard_match'))

    if 'Description Overrides' in config['supplemental']:
        config['property_description_overrides'] = config['supplemental']['Description Overrides']

    if 'FullDescription Overrides' in config['supplemental']:
        config['property_fulldescription_overrides'] = config['supplemental']['FullDescription Overrides']

    # URI mappings may be provided either in the config file or the supplemental document.
    # If they are in both, the version in the config file is what we use.
    # If neither is populated, issue a warning.
    if 'local_to_uri' in config['supplemental'] and 'local_to_uri' not in config:
        config['local_to_uri'] = config['supplemental']['local_to_uri']

    if not config['local_to_uri']:
        warnings.warn("Schema URI Mapping was not found or empty. " +
                          "URI mapping may be provided via config file or supplmentatl markdown. " +
                          "Output is likely to be incomplete.\n\n")

    if not config['uri_mapping_from_config']:
        if 'uri_to_local' in config['supplemental']:
            config['uri_to_local'] = config['supplemental']['uri_to_local']

        if 'profile_local_to_uri' in config['supplemental']:
            config['profile_local_to_uri'] = config['supplemental']['profile_local_to_uri']

    config['profile_uri_to_local'] = config['supplemental'].get('profile_uri_to_local', {})

    if 'enum_deprecations' in config['supplemental']:
        config['enum_deprecations'] = config['supplemental']['enum_deprecations']

    if 'units_translation' not in config:
        config['units_translation'] = config['supplemental'].get('units_translation', {})

    config['schema_supplement'] = config['supplemental'].get('Schema Supplement', {})

    config['wants_common_objects'] = config['supplemental'].get('wants_common_objects', False)

    config['normative'] = args['normative']

    if args['escape_chars']:
        config['escape_chars'] = [x for x in args['escape_chars']]

    doc_generator = DocGenerator(import_from, outfile, config)
    doc_generator.generate_doc()

if __name__ == "__main__":
    main()
