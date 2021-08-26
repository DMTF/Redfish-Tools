#! /usr/local/bin/python3
# Copyright Notice:
# Copyright 2016-2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: doc_generator.py

Brief: Reads redfish json schema files and generates formatted documentation.

Initial author: Second Rise LLC.
"""

import os
import re
import sys
import argparse
import json
import copy
import functools
import warnings
import gettext
from doc_gen_util import DocGenUtilities
from schema_traverser import SchemaTraverser

class InfoWarning(UserWarning):
    """ A warning class for informational messages that don't need a stack trace. """
    pass


class DocGenerator:
    """Redfish Documentation Generator class. Provides 'generate_docs' method."""

    def __init__(self, import_from, outfile, config):
        self.config = config
        self.import_from = import_from
        self.outfile = outfile
        self.property_data = {} # This is an object property for ease of testing.
        self.schema_ref_to_filename = {}
        self.config['payloads'] = None

        # Localization
        languages = [config.get('locale', 'en')]
        localedir = os.path.join(os.path.dirname(__file__), 'locale')
        translations = gettext.translation('doc_generator', localedir=localedir, languages=languages)
        translations.install()
        _ = translations.gettext

        # Set up our simplified warning format.
        def simple_warning_format(message, category, filename, lineno, file=None, line=None):
            """ a basic format for warnings from this program """

            msg = str(message)
            message_skips_trace = 'MISSING JSON' in msg or 'mismatch detected in descriptions' in msg
            if category == InfoWarning or message_skips_trace:
                return '  Info: %(message)s' % {'message': message} + "\n"
            else:
                return '  Warning: %(message)s (%(filename)s: %(lineno)s)' % {'message': message, 'filename': filename, 'lineno': lineno} + "\n"
        warnings.formatwarning = simple_warning_format


        if config.get('payload_dir'):
            payload_dir = config.get('payload_dir')
            config['payloads'] = {}
            payload_filenames = [x for x in os.listdir(payload_dir) if x.endswith('.json')]
            for name in payload_filenames:
                f = open(os.path.join(payload_dir, name), 'r')
                data = f.read()
                if data:
                    config['payloads'][name] = data

        if config.get('supplement_md_dir'):
            import parse_md_supplement
            supplement_dir = config.get('supplement_md_dir')
            config['md_supplements'] = {}
            supplement_files = [x for x in os.scandir(supplement_dir) if (x.is_file() and x.name.endswith('.md')) ]
            for direntry in supplement_files:
                schema_name = direntry.name[:-3]
                f = open(direntry.path, 'r')
                try:
                    md_data = f.read()
                except Exception as ex:
                    warnings.warn('Problem with supplemental file "%(filename)s": %(ex)s' %
                                      {'filename': direntry.path, 'ex': str(ex)})
                if md_data:
                    parsed_data = parse_md_supplement.parse_markdown_supplement(md_data, direntry.name)
                    config['md_supplements'][schema_name] = parsed_data


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

            # Warn the user if a profile specifies items in selected schemas that "don't make sense":
            for schema_name in ['IPAddresses', 'Redundancy', 'Resource', 'Settings']:
                if schema_name in profile_resources:
                    warnings.warn('Profiles should not specify requirements directly on the "%(name)s" schema.' %
                                      {'name': schema_name})

            if config['profile_mode'] != 'subset':
                profile_protocol = self.merge_dicts(profile_merged.get('Protocol', {}),
                                                     self.config.get('profile', {}).get('Protocol', {}))
                self.config['profile_protocol'] = profile_protocol

            if not profile_resources:
                warnings.warn('No profile resource data found; unable to produce profile mode documentation.')
                sys.exit()

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

        # Retrieve registry data.
        # reg_repo will be a fully-qualified URI. It may be overridden by
        # uri-to-local mapping.
        base_uri = '/'.join([reg_repo, reg_name])
        if '://' in base_uri:                                  # This is expected.
            protocol, base_uri = base_uri.split('://')

        is_local_file = False
        registry_uri_to_local = self.config.get('registry_uri_to_local')
        if registry_uri_to_local:
            for partial_uri in registry_uri_to_local.keys():
                if base_uri.startswith(partial_uri):
                    local_path = registry_uri_to_local[partial_uri]
                    if partial_uri.endswith(reg_name):
                        reg_repo = local_path[0:-len(reg_name)]
                    else:
                        reg_repo = local_path
                    is_local_file = True
                    break

        reg_uri = self.get_versioned_uri(reg_name, reg_repo, reg_minversion, is_local_file)

        if not reg_uri:
            warnings.warn('Unable to find registry file for %(repo)s, %(name)s, minimum version %(minversion)s' %
                              {'repo': reg_repo, 'name': reg_name, 'minversion': reg_minversion})
            return registry_reqs

        # Generate data based on profile
        if is_local_file:
            registry_data = DocGenUtilities.load_as_json(reg_uri)
        else:
            registry_data = DocGenUtilities.http_load_as_json(reg_uri)

        if registry_data:
            registry_reqs['current_release'] = registry_data['RegistryVersion']
            registry_reqs.update(registry_data)

            for msg in registry_profile['Messages']:
                if msg in registry_reqs['Messages']:
                    registry_reqs['Messages'][msg]['profile_requirement'] = registry_profile['Messages'][msg].get(
                        'ReadRequirement', 'Mandatory')
                else:
                    warnings.warn('Profile specifies requirement for nonexistent Registry Message: %(name)s %(message)s'
                                      % {'name': reg_name, 'message': msg})

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
                else:
                    req_profile_repo = local_path
                req_profile_repo = os.path.abspath(req_profile_repo)
                is_local_file = True
                break

        req_profile_uri = self.get_versioned_uri(req_profile_name, req_profile_repo,
                                                 version_string, is_local_file)

        if not req_profile_uri:
            warnings.warn('Unable to find Profile for %(repo)s, %(name)s, minimum version: %(minversion)s'
                              % {'repo': req_profile_repo, 'name': req_profile_name, 'minversion': req_profile_minversion})
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
                    warnings.warn('Merging two items with different types would fail. Probably attempting to merge two profiles; debugging here may be required.')
            else:
                dict2[k] = v

        return dict2


    @staticmethod
    def get_files(text_input):
        """From text input (command line or parsed from file), create a list of files. """
        files_to_process = []

        for file_to_import in text_input:
            start_count = len(files_to_process)
            if os.path.isdir(file_to_import):
                for dir_entry in os.scandir(file_to_import):
                    if dir_entry.is_file():
                        if dir_entry.path[-4:] == 'json':
                            files_to_process.append(dir_entry.path)

                # NB: this is an adequate sort for file-grouping purposes. It's not guaranteed to sort versions correctly.
                files_to_process.sort(key=str.lower)
            elif os.path.isfile(file_to_import):
                files_to_process.append(os.path.abspath(file_to_import))
            if len(files_to_process) == start_count:
                warnings.warn('Oops, %(filename)s not found, or contains no .json files.' % {'filename': file_to_import} + "\n")
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
                    warnings.warn('Unable to process files for %(uri)s' % {'uri': normalized_uri})
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

            if self.config.get('locale'):
                translated_file = os.path.join(latest_info['root'], self.config.get('locale'), latest_info['filename'])
                if os.path.isfile(translated_file):
                    translated_data = DocGenUtilities.load_as_json(translated_file)
                    latest_data = self.apply_translated_data(latest_data, translated_data)

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

        if self.config['output_format'] in ['markdown', 'slate']:
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

            # Schemas listed in 'common_object_schemas' in config should not get first-class sections.
            schema_name_parts = schema_name.split('.')
            unversioned_schema_name = schema_name_parts[0]
            has_common_object_override = False
            if self.config.get('reference_disposition', {}).get(unversioned_schema_name) == 'common_object':
                has_common_object_override = True
                if 'common_object_schemas' not in self.config:
                    self.config['common_object_schemas'] = []
                self.config['common_object_schemas'].append(normalized_uri)

            data['_schema_name'] = schema_name
            all_schemas[normalized_uri] = data

            if filename in processed_files: continue

            ref = ''
            if '$ref' in data:
                ref = data['$ref'][1:] # drop initial '#'

            # This is a special case for resources like Redundancy, in which there is no $ref but we still need
            # to capture its versioned/unversioned data ... and then we want it to appear in the Common Properties
            # section if it's referred to.
            if not ref and has_common_object_override:
                ref = '/definitions/' + unversioned_schema_name
            if not ref:
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
                missing_files_list = '\n   '.join(missing_files[0:9]) + "\n   " + 'and %(number)s more.' % {'number': str(numfiles - 10)}
            warnings.warn( '%(number)s referenced files were missing: ' % {'number': str(numfiles)} + "\n   " + missing_files_list)

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

        # Check for a localized file and pull in translated text:
        if self.config.get('locale'):
            translated_file = os.path.join(ref['root'], self.config.get('locale'), ref['filename'])
            if os.path.isfile(translated_file):
                translated_data = DocGenUtilities.load_as_json(translated_file)
                data = self.apply_translated_data(data, translated_data)

        schema_name = SchemaTraverser.find_schema_name(filename, data, True)

        version = self.get_version_string(ref['filename'])

        property_data['schema_name'] = schema_name
        property_data['name_and_version'] = schema_name
        property_data['normalized_uri'] = normalized_uri
        property_data['latest_version'] = version
        release_text = data.get('release')

        if 'deprecated' in data:
            property_data['deprecated'] = data['deprecated']
            property_data['versionDeprecated'] = data.get('versionDeprecated')

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
                            property_data['name_and_version'] += ' ' + ('v%(minversion)s (current release: v%(version)s'
                                % {'minversion': min_version, 'version': version})
                        else:
                            # this is unlikely
                            property_data['name_and_version'] += ' ' + ' v%(version)s+' % {'version': min_version}
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
            warnings.warn('Check %(schema_ref)s for version problems. Are there two files with either version 1.0.0 or no version?'
                              % {'schema_ref': schema_ref})

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

            if 'deprecated' in data:
                property_data['name_and_version'] += ' ' + _('(deprecated)')
                property_data['deprecated'] = data['deprecated']
                property_data['versionDeprecated'] = data.get('versionDeprecated')

        except KeyError:
            warnings.warn('Unable to find properties in path %(ref)s from %(filename)s' % { 'ref': ref['ref'], 'filename': filename})
            return {}

        if release_text:
            release_history = property_data.get('release_history')
            if not release_history:
                property_data['release_history'] = []
                release_history = property_data.get('release_history')
            release_history.append({'version': version, 'release': release_text, 'deprecated': ('deprecated' in property_data)})


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


        # Look for a localized schema file and apply it first, if found.
        if self.config.get('locale'):
            (path_head, path_tail) = os.path.split(filename)
            translated_file = os.path.join(path_head, self.config.get('locale'), path_tail)
            if os.path.isfile(translated_file):
                translated_data = DocGenUtilities.load_as_json(translated_file)
                data = self.apply_translated_data(data, translated_data)

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


    def apply_translated_data(self, data, translated_data):
        """ Gather translated strings from translated_data and apply them to data.
        This assumes that translated_data is essentially a copy of data with translations
        and annotations applied -- this is done on a file-by-file basis.
        """

        # If there is no definitions block, there's nothing to do:
        if 'definitions' not in translated_data or 'definitions' not in data:
            return data

        definitions = translated_data['definitions']
        for prop_name, prop_info in definitions.items():
            if prop_name in data['definitions']:
                prop_data = data['definitions'].get(prop_name)
                data['definitions'][prop_name] = self.apply_translation_to_prop(prop_data, prop_info)

        return data


    def apply_translation_to_prop(self, data, translated_data):
        """ Apply translated strings and annotations on a per-property basis.
        Recurses through properties, etc. Does not follow $refs; this is intended to "overlay"
        data from a translated schema onto the original. """

        for x in ['description', 'longDescription', 'translation']:
            if translated_data.get(x):
                data[x] = translated_data.get(x)

        for x in ['enumDescriptions', 'enumLongDescriptions']:
            if x in data and x in translated_data:
                for y in data[x]:
                    data[x][y] = translated_data.get(x, {}).get(y, data[x][y])

        # enumTranslations are additional annotations we need to add during output.
        if 'enumTranslations' in translated_data:
            data['enumTranslations'] = translated_data['enumTranslations']

        for x in ['properties', 'parameters']:
            if x in translated_data and x in data:
                translated_properties = translated_data[x]
                for prop_name, prop_info in data[x].items():
                    if translated_properties.get(prop_name):
                        data[x][prop_name] = self.apply_translation_to_prop(data[x][prop_name], translated_properties[prop_name])

        return data



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
                    warnings.warn("Can't find schema file for %{ref}s", {'ref': this_ref})
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

    @staticmethod
    def parse_command_line():

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
        parser.add_argument('-n', '--normative', action='store_true', dest='normative', default=None,
                            help='Produce normative (developer-focused) output')
        parser.add_argument('--format', dest='format',
                            choices=['markdown', 'slate', 'html', 'csv'], help='Output format')
        parser.add_argument('--out', dest='outfile',
                            help=('Output file (default depends on output format: '
                                  'output.md for Markdown, index.html for HTML, output.csv for CSV'))
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
        parser.add_argument('--warn_missing_payloads', action='store_true', dest='warn_missing_payloads', default=False,
                                help='Warn on missing JSON payloads')

        parser.add_argument('--property_index', action='store_true', dest='property_index', default=None,
                            help='Produce Property Index output.')
        parser.add_argument('--property_index_config_out', dest='property_index_config_out',
                            metavar='CONFIG_FILE_OUT',
                            default=False, help='Generate updated config file, with specified filename (property_index mode only).')
        parser.add_argument('--escape', dest='escape_chars',
                            help=("Characters to escape (\\) in generated Markdown. "
                                  "For example, --escape=@#. Use --escape=@ if strings with embedded @ "
                                  "are being converted to mailto links."))

        command_line_args = vars(parser.parse_args())
        return command_line_args.copy()


    @staticmethod
    def parse_config_file(config_fn):
        """ Attempt to open and parse a config file, which should be a JSON file. Returns a dictionary. """

        config_file_read = False
        config_data = {}
        try:
            with open(config_fn, 'r', encoding="utf8") as config_file:
                config_data = json.load(config_file)
                if config_data.get('uri_mapping'):
                    # Populate the URI mappings
                    config_data['uri_to_local'] = {}
                    config_data['local_to_uri'] = {}
                    for k, v in config_data.get('uri_mapping').items():
                        vpath = os.path.abspath(v)
                        config_data['uri_to_local'][k] = vpath
                        config_data['local_to_uri'][vpath] = k
                config_file_read = True
        except (OSError) as ex:
            warnings.warn('Unable to open %(filename)s to read: %(message)s' % {'filename':  config_fn, 'message': str(ex)})
            sys.exit()
        except (json.decoder.JSONDecodeError) as ex:
            warnings.warn('%(filename)s appears to be invalid JSON. JSON decoder reports: %(message)s' %
                              {'filename': config_fn, 'message': str(ex)})
            sys.exit()

        return config_data


    @staticmethod
    def combine_configs(command_line_args=None, config_data=None, supp_config_data=None):
        """ Generate configuration based on various inputs (which should be dictionaries):
        command_line_args: command-line arguments
        config_data: read in from a config file
        supp_config_data: read in from content supplement config file

        If a parameter is specified in more than one place, config_data supersedes supplemental_data,
        and command_line_args supersedes all.
        """

        if not command_line_args:
            command_line_args = {}
        if not config_data:
            config_data = {}
        if not supp_config_data:
            supp_config_data = {}

        uri_mapping_from_config = config_data.get('uri_to_local')
        registry_uri_mapping_from_config = config_data.get('registry_uri_to_local')
        cwd = os.getcwd()

        # config will become the combined config dictionary.
        config = {
            'excluded_annotations': [],
            'excluded_annotations_by_match': [],
            'excluded_properties': [],
            'excluded_by_match': [],
            'excluded_schemas': [],
            'excluded_schemas_by_match': [],
            'excluded_pattern_props': [],
            'description_overrides': {},
            'property_description_overrides': {},
            'property_fulldescription_overrides': {},
            'wants_common_objects': False,
            'omit_version_in_headers': False,
            'schema_supplement': {},
            'normative': False,
            'escape_chars': [],
            'cwd': cwd,
            'schema_link_replacements': {},
            'local_to_uri': {},
            'uri_to_local': {},
            'registry_uri_to_local': {},
            'profile_mode': False,
            'profile_doc': None,
            'profile_resources': {},
            'profile': {},
            'profile_uri_to_local': {},
            'registry_uri_to_local': {},
            'units_translation': {},
            'combine_multiple_refs': 0,
            'with_table_numbering': False,
            'warn_missing_payloads': False,
            }

        # combined_args is an intermediate dictionary, combining command-line and config parameters.
        # Many of these parameters will need further vetting to produce config data, for
        # example, opening a file or verifying well-formedness
        combined_args = command_line_args.copy()

        if config_data:

            # boilerplate content always comes from config_data:
            for bp in ['intro_content', 'postscript_content']:
                bp_content = config_data.get(bp)
                if bp_content:
                    config[bp] = bp_content
                    if '[insert_common_objects]' in bp_content:
                        config['wants_common_objects'] = True
                    if '[add_toc]' in bp_content:
                        # We always want to set 'add_toc' if there's a placeholder for it in the boilerplate
                        config['add_toc'] = True

            if not config.get('add_toc'):
                config['add_toc'] = config_data.get('add_toc', False)

            # command-line arguments override the config file.
            config_args = [
                'format', 'outfile', 'payload_dir', 'normative',
                'profile_doc', 'subset_doc',
                'property_index', 'property_index_config_out', 'escape_chars',
                'locale', 'warn_missing_payloads'
                ]

            for x in config_args:
                if config_data.get(x) and (x not in combined_args or combined_args[x] is None):
                    combined_args[x] = config_data[x]

            # "terse" mode is a flag that can only be specified as true on the command line, and
            # otherwise will be False (not None) at this point:
            if config_data.get('profile_terse'):
                combined_args['profile_terse'] = True

            # import_from is special: command-line parsing will always produce a list, sometimes empty.
            if config_data.get('import_from') and not combined_args.get('import_from'):
                combined_args['import_from'] = config_data['import_from']

            # config_flags don't have command-line overrides; they should be added to config directly.
            config_flags = [
                'units_translation', 'suppress_version_history',
                'actions_in_property_table', 'html_title',
                'uri_to_local', 'local_to_uri', 'profile_uri_to_local', 'registry_uri_to_local',
                'combine_multiple_refs', 'omit_version_in_headers',
                'description_overrides' # this is for property_index mode only
                ]
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
                        warnings.warn('Config file entry "object_reference_disposition" contains an unrecognized key: "%(key)s", ignoring it.'
                                          % {'key': x})
                    else:
                        for ref in refs:
                            ref_disp_map[ref] = x
                config['reference_disposition'] = ref_disp_map

        # set defaults:
        arg_defaults = {
            'format' : 'slate',
            'outfile' : 'output.md',
            }
        for param, default in arg_defaults.items():
            if not combined_args.get(param):
                combined_args[param] = default

        config['output_format'] = combined_args['format']

        # Allow "with_table_numbering" to be True only for markdown formats.
        if config_data.get('with_table_numbering') and config['output_format'] in ['slate', 'markdown']:
            config['with_table_numbering'] = True

        if combined_args.get('property_index'):
            config['output_content'] = 'property_index'
            config['write_config_to'] = combined_args['property_index_config_out']

        else:
            config['output_content'] = 'full_doc'

        if 'import_from' in combined_args and len(combined_args['import_from']):
            import_from = combined_args['import_from']
        else:
            import_from = [ os.path.join(config.get('cwd'), 'json-schema') ]

        config['import_from'] = import_from

        # Determine outfile and verify that it is writeable:
        outfile_name = combined_args['outfile']
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
                if config['output_format'] in ['markdown', 'slate']:
                    outfile_name += '.md'
        config['outfile_name'] = outfile_name

        # If payload_dir was provided, verify that it is a readable directory:
        if combined_args.get('payload_dir'):
            payload_dir = combined_args.get('payload_dir')
            try:
                if os.path.isdir(combined_args['payload_dir']):
                    config['payload_dir'] = combined_args['payload_dir']
                else:
                    warnings.warn('"%(dirname)s" is not a directory. Exiting.' % {'dirname': combined_args['payload_dir']})
                    sys.exit();
            except (Exception) as ex:
                warnings.warn('Unable to read payload_dir "%(dirname)s": %(message)s' % {'dirname': combined_args['payload_dir'], 'message': str(ex)})
                sys.exit();

        # Check profile document, if specified
        if combined_args.get('profile_doc'):
            if combined_args['profile_terse']:
                config['profile_mode'] = 'terse'
            else:
                config['profile_mode'] = 'verbose'

            profile_doc = combined_args['profile_doc']
            try:
                profile = open(profile_doc, 'r', encoding="utf8")
                config['profile_doc'] = profile_doc
            except (OSError) as ex:
                warnings.warn('Unable to open %(filename)s to read: %(message)s' %  {'filename': profile_doc, 'message': str(ex)})
                sys.exit()

        if combined_args.get('subset_doc'):
            config['profile_mode'] = 'subset'
            profile_doc = combined_args['subset_doc']
            try:
                profile = open(profile_doc, 'r', encoding="utf8")
                config['profile_doc'] = profile_doc
            except (OSError) as ex:
                warnings.warn('Unable to open %(filename)s to read: %(message)s' % {'filename': profile_doc, 'message': str(ex)})
                sys.exit()

        if combined_args.get('profile_terse') and not combined_args.get('profile_doc'):
            warnings.warn('Terse output (%(arg_t)s or %(arg_terse)s) requires a profile (--%(arg_profile)s).' %
                              {'arg_t': '-t', 'arg_terse': '--terse', 'arg_profile': 'profile'},
                              InfoWarning)
            sys.exit()

        for kw in ['units_translation', 'schema_link_replacements']:
            if kw in supp_config_data:
                config[kw] = supp_config_data[kw]

        excluded_annotations = {}
        if 'excluded_annotations' in config_data:
            excluded_annotations['exact'] = [x for x in config_data['excluded_annotations'] if not x.startswith('*')]
            excluded_annotations['wildcard'] = [x[1:] for x in config_data['excluded_annotations'] if x.startswith('*')]
        if excluded_annotations.get('exact'):
            excl = excluded_annotations.get('exact')
            config['excluded_properties'].extend(excl)
            config['excluded_annotations'].extend(excl)
        if excluded_annotations.get('wildcard'):
            excl = excluded_annotations.get('wildcard')
            config['excluded_by_match'].extend(excl) # intentional?
            config['excluded_annotations_by_match'].extend(excl)

        excluded_properties = {}
        if 'excluded_properties' in config_data:
            excluded_properties['exact'] = [x for x in config_data['excluded_properties'] if not x.startswith('*')]
            excluded_properties['wildcard'] = [x[1:] for x in config_data['excluded_properties'] if x.startswith('*')]
        if excluded_properties.get('exact'):
            config['excluded_properties'].extend(excluded_properties['exact'])
        if excluded_properties.get('wildcard'):
            config['excluded_by_match'].extend(excluded_properties['wildcard'])

        excluded_schemas = {}
        if 'excluded_schemas' in config_data:
            excluded_schemas['exact'] = [x for x in config_data['excluded_schemas'] if not x.startswith('*')]
            excluded_schemas['wildcard'] = [x[1:] for x in config_data['excluded_schemas'] if x.startswith('*')]
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

        if 'property_description_overrides' in supp_config_data:
            config['property_description_overrides'] = supp_config_data['property_description_overrides']

        if 'property_fulldescription_overrides' in supp_config_data:
            config['property_fulldescription_overrides'] = supp_config_data['property_fulldescription_overrides']

        if not config['local_to_uri']:
            warnings.warn(' '.join(['Schema URI Mapping (uri_mapping) was not found or empty.',
                                        'URI mapping must be provided via config file.',
                                        'Output is likely to be incomplete.',
                                        "\n\n"]))

        if 'schema_supplement' in supp_config_data:
            config['schema_supplement'] = parse_schema_supplement(supp_config_data.get('schema_supplement'))

        config['normative'] = combined_args.get('normative', False)

        if config['combine_multiple_refs'] == 1:
            warnings.warn(' '.join(['The combine_multiple_refs setting of 1 does not make sense.',
                                        'It should be 2 or more, or 0 to prevent combining. Assuming 0 was intended.',
                                        "\n\n"]))
            config['combine_multiple_refs'] == 0

        # Apply defaults for parameters that were not explicitly set:
        if 'actions_in_property_table' not in config:
            config['actions_in_property_table'] = True

        if combined_args.get('escape_chars'):
            config['escape_chars'] = [x for x in combined_args['escape_chars']]

        if combined_args.get('locale'):
            config['locale'] = combined_args['locale']

        config['warn_missing_payloads'] = combined_args.get('warn_missing_payloads', False)

        return config


def parse_schema_supplement(supp_data):
    """ Vet and extend supp_data. Any "mockup" entries in supp_data should be file paths or URIs to be expanded. """
    for schema_name, data in supp_data.items():
        if 'mockup' in data:
            mockup_location = data.get('mockup')
            mockup = None
            ml_lower = mockup_location.lower()
            if ml_lower.startswith('http://') or ml_lower.startswith('https://'):
                # retrieve it via http[s]
                try:
                    response = urllib.request.urlopen(mockup_location)
                    if 200 <= response.status < 300:
                        mockup = response.read().decode('utf-8') # JSON is UTF-8 by spec.
                    else:
                        warnings.warn('Unable to retrieve Mockup from URL "%(uri)s": Server returned %(status_code)s status' %
                                          {'uri': mockup_location, 'status_code': response.status})
                except Exception as ex:
                    warnings.warn('Unable to retrieve Mockup from URL "%(uri)s": %(ex)s' % {'uri': mockup_location, 'ex': str(ex)})
            else:
                # treat it as a local file
                try:
                    mockup_file = open(mockup_location, 'r', encoding="utf8")
                    mockup = mockup_file.read()
                except Exception as ex:
                    warnings.warn('Unable to open Mockup file "%(uri)s" to read: %(ex)s'
                                          % {'uri': mockup_location, 'ex': str(ex)})

            if mockup:
                if data.get('jsonpayload'):
                    warnings.warn('Warning: Mockup and JSONPayload both specified; using Mockup %(uri)s'
                                      % {'uri': mockup_location})
                data['jsonpayload'] = mockup

    return supp_data


def main():
    """Parse and validate arguments, then process data and produce markdown output."""

    cwd = os.getcwd()

    command_line_args = DocGenerator.parse_command_line()
    config_fn = command_line_args.get('config_file')
    if config_fn:
        config_data = DocGenerator.parse_config_file(config_fn)
    else:
        config_data = {}

    # path of some files will be relative to path of config file:
    config_dir = os.path.dirname(config_fn)

    # Is there a content supplement file?
    if config_data.get('content_supplement'):
        config_supp_fn = config_data['content_supplement']
        config_supp_fn = os.path.normpath(os.path.join(config_dir, config_supp_fn))
        try:
            with open(config_supp_fn, 'r', encoding="utf8") as config_supp_file:
                supp_config_data = json.load(config_supp_file)
        except (OSError) as ex:
            warnings.warn('Unable to open %(filename)s to read: %(message)s' % {'filename':  config_supp_fn, 'message': str(ex)})
            sys.exit()
        except (json.decoder.JSONDecodeError) as ex:
            warnings.warn('%(filename)s appears to be invalid JSON. JSON decoder reports: %(message)s' %
                              {'filename': config_supp_fn, 'message': str(ex)})
            sys.exit()
    else:
        supp_config_data = {}

    # If boilerplate is specified, read it in now.
    boilerplate_fns = {'boilerplate_intro': 'intro_content', 'boilerplate_postscript': 'postscript_content'}
    for fn, content_key in boilerplate_fns.items():
        if config_data.get(fn):
            boilerplate_fn = os.path.normpath(os.path.join(config_dir, config_data[fn]))
            try:
                with open(boilerplate_fn, 'r', encoding="utf8") as boilerplate_file:
                    boilerplate_lines = []
                    for line in boilerplate_file:
                        line = line.strip('\r\n') # Keep other whitespace
                        boilerplate_lines.append(line)
                    config_data[content_key] = '\n'.join(boilerplate_lines)
            except (OSError) as ex:
                warnings.warn('Unable to open %(filename)s to read: %(message)s' % {'filename':  config_supp_fn, 'message': str(ex)})
                sys.exit()

    config = DocGenerator.combine_configs(command_line_args=command_line_args, config_data=config_data,
                                              supp_config_data=supp_config_data)

    try:
        outfile = open(config['outfile_name'], 'w', encoding="utf8")
    except (OSError) as ex:
        warnings.warn('Unable to open %(filename)s to write: %(message)s' % {'filename': config['outfile_name'], 'message': str(ex)})
        sys.exit();

    doc_generator = DocGenerator(config['import_from'], outfile, config)
    doc_generator.generate_doc()


if __name__ == "__main__":
    main()
