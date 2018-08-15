#! /usr/local/bin/python3
# Copyright Notice:
# Copyright 2016, 2017, 2018 Distributed Management Task Force, Inc. All rights reserved.
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
def simple_warning_format(message, category, filename, lineno, file=None, line=None):
    """ a basic format for warnings from this program """
    return '  Warning: %s (%s:%s)' % (message, filename, lineno) + "\n"

warnings.formatwarning = simple_warning_format

class DocGenerator:
    """Redfish Documentation Generator class. Provides 'generate_docs' method."""

    def __init__(self, import_from, outfile, config):
        self.config = config
        self.import_from = import_from
        self.outfile = outfile
        self.property_data = {} # This is an object property for ease of testing.

        if config.get('profile_mode'):
            config['profile'] = DocGenUtilities.load_as_json(config.get('profile_doc'))
            profile_resources = {}

            if 'RequiredProfiles' in config['profile']:
                for req_profile_name in config['profile']['RequiredProfiles'].keys():
                    profile_resources = self.merge_required_profile(
                        profile_resources, req_profile_name,
                        config['profile']['RequiredProfiles'][req_profile_name])

            if 'Registries' in config['profile']:
                config['profile']['registries_annotated'] = {}
                for registry_name in config['profile']['Registries'].keys():
                    registry_summary = self.process_registry(registry_name,
                                                             config['profile']['Registries'][registry_name])
                    config['profile']['registries_annotated'][registry_name] = registry_summary

            profile_resources = self.merge_dicts(profile_resources, self.config.get('profile', {}).get('Resources', {}))

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
            minversion_parts = re.findall('(\d+)', min_version)

            candidate = None
            candidate_strength = 0
            for rl in repo_links:
                base = base_name + '.'
                if rl.startswith(repo) and base in rl and rl.endswith('.json'):
                    parts = rl[0:-5].rsplit(base, 1)
                    if len(parts) == 2:
                        suffix = parts[1]
                        version_parts = re.findall('(\d+)', suffix)
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


    def merge_required_profile(self, profile_resources, req_profile_name, req_profile_info):
        """ Merge a required profile into profile_resources (a dict). May result in recursive calls. """

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
            return profile_resources


        if is_local_file:
            req_profile_data = DocGenUtilities.load_as_json(req_profile_uri)
        else:
            req_profile_data = DocGenUtilities.http_load_as_json(req_profile_uri)

        if req_profile_data:
            if 'RequiredProfiles' in req_profile_data:
                for req_profile_name in req_profile_data['RequiredProfiles'].keys():
                    profile_resources = self.merge_required_profile(
                        profile_resources, req_profile_name, req_profile_data['RequiredProfiles'][req_profile_name])

            profile_resources = self.merge_dicts(profile_resources, req_profile_data.get('Resources', {}))

        return profile_resources


    def merge_dicts(self, dict1, dict2):
        """ Merge two dictionaries recursively. Returns the merged result. """
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
                else:
                    dict2[k] = v

        dict2.update(dict1)
        return dict2


    @staticmethod
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


    def generate_docs(self, level=0):
        """Given a list of files, generate a block of documentation.

        This is the main loop of the product.
        """
        files_to_process = self.get_files(self.import_from)
        grouped_files, schema_data = self.group_files(files_to_process)

        self.property_data = {}
        doc_generator_meta = {}

        # First expand the grouped files -- these are the schemas that get first-class documentation sections
        for normalized_uri in grouped_files.keys():
            data = self.process_files(normalized_uri, grouped_files[normalized_uri])
            if not data:
                # If we're in profile mode, this is probably normal.
                if not self.config['profile_mode']:
                    warnings.warn("Unable to process files for " + normalized_uri)
                continue
            data['uris'] = schema_data[normalized_uri].get('_uris', [])
            self.property_data[normalized_uri] = data

            doc_generator_meta[normalized_uri] = self.property_data[normalized_uri]['doc_generator_meta']
            latest_info = grouped_files[normalized_uri][-1]
            latest_file = os.path.join(latest_info['root'], latest_info['filename'])
            latest_data = DocGenUtilities.load_as_json(latest_file)
            latest_data['_is_versioned_schema'] = latest_info.get('_is_versioned_schema')
            latest_data['_is_collection_of'] = latest_info.get('_is_collection_of')
            latest_data['_schema_name'] = latest_info.get('schema_name')
            schema_data[normalized_uri] = latest_data

        # Also process and version definitions in any "other" files. These are files without top-level $ref objects.
        schema_data = self.process_unversioned_files(schema_data, doc_generator_meta, self.config['uri_to_local'])

        traverser = SchemaTraverser(schema_data, doc_generator_meta, self.config['uri_to_local'])

        # Generate output
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
                        ref_filename = os.path.abspath(os.path.join(root, ref_fn))
                        if ref_filename in file_list:
                            ref_files.append({'root': root,
                                              'filename': ref_fn,
                                              'ref': refpath_path,
                                              'schema_name': schema_name})
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

        Returns a property_data object consisting of the properties from the last ref file,
        and metadata ('doc_generator_meta') indicating version for properties introduced after
        1.0 and version_deprecated for deprecated properties.
        """
        property_data = {}
        for info in refs:
            property_data = self.process_data_file(schema_ref, info, property_data)
        return property_data


    def process_data_file(self, schema_ref, ref, property_data):
        """Process a single file by ref name, identifying metadata and updating property_data."""

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
        property_data['latest_version'] = version
        property_data['name_and_version'] = schema_name
        property_data['normalized_uri'] = normalized_uri

        min_version = False
        if profile_mode:
            schema_profile = profile.get(generalized_uri)
            if schema_profile:
                min_version = schema_profile.get('MinVersion')
                if min_version:
                    if version:
                        property_data['name_and_version'] += ' v' + min_version + '+ (current release: v' + version + ')'
                    else:
                        # this is unlikely
                        property_data['name_and_version'] += ' v' + min_version + '+'
            else:
                # Skip schemas that aren't mentioned in the profile:
                return {}
        elif version:
            property_data['name_and_version'] += ' ' + version

        if 'properties' not in property_data:
            property_data['properties'] = {}
        meta = property_data.get('doc_generator_meta', {'schema_name': schema_name})

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

        meta = self.extend_metadata(meta, properties, version, normalized_uri + '#properties/')
        meta['definitions'] = meta.get('definitions', {})
        definitions = property_data['definitions']
        meta['definitions'] = self.extend_metadata(meta['definitions'], definitions, version, normalized_uri + '#definitions/')
        property_data['doc_generator_meta'] = meta

        return property_data


    def process_unversioned_files(self, schema_data, doc_generator_meta, uri_to_local):
        """ Process version metadata in individually-versioned properties in files lacking a $ref.
        That complicated rule catches some of the "referenced objects."
        """

        interim_traverser = SchemaTraverser(schema_data, doc_generator_meta, uri_to_local)
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
                    prop_data = self.update_versioned_properties(unversioned_ref, refs_by_version, interim_traverser)

        return prop_data


    def update_versioned_properties(self, common_ref, refs_by_version, traverser):
        """ This is for generating versioned information for properties in supporting schemas,
        in which a property definition contains an "anyOf" linking to versioned properties.

        From a dict of version -> $ref, generate a prop_info structure with version information.
        """

        prop_info =  {}
        meta = {}

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
                    meta = self.extend_metadata(meta, ref_properties, this_version, this_ref + '#properties')

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
                            child_ref_properties = child_ref['properties']
                            meta[prop_name] = self.extend_metadata(meta[prop_name], child_ref_properties, this_version,
                                                                   this_ref + '/prop_name#properties')
                            ref_properties[prop_name]['properties'] = child_ref_properties
                            ref_properties[prop_name]['type'] = 'object'
                            del(ref_properties[prop_name]['anyOf'])


                # Update any relative refs in ref_properties with this_ref base:
                [base_ref, rest] = this_ref.split('#')
                [common_base_ref, rest] = common_ref.split('#')
                if common_base_ref != base_ref:
                    ref_properties = self.absolutize_refs(base_ref, ref_properties)

            # Update saved property to latest version, with extended metadata:
            prop_info = copy.deepcopy(ref_info)
            prop_info['properties'] = ref_properties
            prop_info['_doc_generator_meta'] = meta
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


    def extend_metadata(self, meta, properties, version, normalized_uri=''):

        for prop_name in properties.keys():
            props = properties[prop_name]

            if prop_name not in meta:
                meta[prop_name] = {}
                if version: # Track version only when first seen
                    meta[prop_name]['version'] = version
            if 'deprecated' in props:
                if 'version_deprecated' not in meta[prop_name]:
                    if not version or version == '1.0.0':
                        warnings.warn('"deprecated" found in version 1.0.0: ' + prop_name )
                    else:
                        meta[prop_name]['version_deprecated'] = version
                    meta[prop_name]['version_deprecated_explanation'] = props['deprecated']

            if props.get('enum'):
                enum = props.get('enum')
                meta[prop_name]['enum'] = meta[prop_name].get('enum', {})
                # deprecated enums are not currently discernable from schema data, so look them up in config:
                prop_ref = normalized_uri + prop_name

                enum_deprecations = self.config.get('enum_deprecations', {}).get(prop_ref, {})
                for enum_name in enum:
                    if enum_name not in meta[prop_name]['enum']:
                        meta[prop_name]['enum'][enum_name] = {}
                        if version:
                            meta[prop_name]['enum'][enum_name]['version'] = version
                    # TODO: Get deprecation info from schema
                    if enum_deprecations:
                        if enum_deprecations.get(enum_name):
                            meta[prop_name]['enum'][enum_name]['version_deprecated'] = enum_deprecations[enum_name]['version']
                            meta[prop_name]['enum'][enum_name]['version_deprecated_explanation'] = enum_deprecations[enum_name]['description']

            # build out metadata for sub-properties.
            if props.get('properties'):
                child_props = props['properties']
                meta[prop_name] = self.extend_metadata(meta[prop_name], child_props, version,
                                                       normalized_uri + prop_name + '/properties/')

            properties[prop_name]['_doc_generator_meta'] = meta[prop_name]

        return meta


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
        'expand_defs_from_non_output_schemas': False,
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
        'profile': {}
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
                        choices=['markdown', 'html', 'csv'], help='Output format')
    parser.add_argument('--out', dest='outfile', default='output.md',
                        help=('Output file (default depends on output format: '
                              'output.md for markdown, index.html for html, output.csv for csv)'))
    parser.add_argument('--sup', dest='supfile',
                        help=('Path to the supplemental material document. '
                              'Default is usersupplement.md for user-focused documentation, '
                              'and devsupplement.md for normative documentation.'))
    parser.add_argument('--profile', dest='profile_doc',
                        help=('Path to a JSON profile document, for profile output'))
    parser.add_argument('-t', '--terse', action='store_true', dest='profile_terse',
                        help=('Terse output (meaningful only with --profile). By default,'
                              'profile output is verbose, including all properties regardless of'
                              'profile requirements. "Terse" output is intended for use by'
                              'Service developers, including only the subset of properties with'
                              'profile requirements.'))
    parser.add_argument('--escape', dest='escape_chars',
                        help=("Characters to escape (\\) in generated markdown; "
                              "e.g., --escape=@#. Use --escape=@ if strings with embedded @ "
                              "are being converted to mailto links."))

    args = parser.parse_args()

    config['output_format'] = args.format

    if len(args.import_from):
        import_from = args.import_from
    else:
        import_from = [ os.path.join(config.get('cwd'), 'json-schema') ]

    # Determine outfile and verify that it is writeable:
    outfile_name = args.outfile
    if outfile_name == 'output.md':
        if config['output_format'] == 'html':
            outfile_name = 'index.html'
        if config['output_format'] == 'csv':
            outfile_name = 'output.csv'

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

    # Check profile document, if specified
    if args.profile_doc:
        if args.profile_terse:
            config['profile_mode'] = 'terse'
        else:
            config['profile_mode'] = 'verbose'

        profile_doc = args.profile_doc
        try:
            profile = open(profile_doc, 'r', encoding="utf8")
            config['profile_doc'] = profile_doc
        except (OSError) as ex:
            warnings.warn('Unable to open ' + profile_doc + ' to read: ' +  str(ex))
            exit()

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

    if 'Description Overrides' in config['supplemental']:
        config['property_description_overrides'] = config['supplemental']['Description Overrides']

    if 'local_to_uri' in config['supplemental']:
        config['local_to_uri'] = config['supplemental']['local_to_uri']

    if 'uri_to_local' in config['supplemental']:
        config['uri_to_local'] = config['supplemental']['uri_to_local']

    if 'profile_local_to_uri' in config['supplemental']:
        config['profile_local_to_uri'] = config['supplemental']['profile_local_to_uri']

    config['profile_uri_to_local'] = config['supplemental'].get('profile_uri_to_local', {})

    if 'enum_deprecations' in config['supplemental']:
        config['enum_deprecations'] = config['supplemental']['enum_deprecations']

    config['units_translation'] = config['supplemental'].get('units_translation', {})

    config['schema_supplement'] = config['supplemental'].get('Schema Supplement', {})

    config['wants_common_objects'] = config['supplemental'].get('wants_common_objects', False)

    if 'keywords' in config['schema_supplement']:
        config['add_toc'] = config['supplemental']['keywords'].get('add_toc')

    config['normative'] = args.normative

    if args.escape_chars:
        config['escape_chars'] = [x for x in args.escape_chars]

    doc_generator = DocGenerator(import_from, outfile, config)
    doc_generator.generate_doc()

if __name__ == "__main__":
    main()
