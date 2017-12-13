# Copyright Notice:
# Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/LICENSE.md

"""
File: doc_formatter.py

Brief : Contains DocFormatter class

Initial author: Second Rise LLC.
"""

import os
import copy
import re
import warnings
import sys
from doc_gen_util import DocGenUtilities

class DocFormatter:
    """Generic class for schema documentation formatter"""

    def __init__(self, property_data, traverser, config, level=0):
        """Set up the markdown generator.

        property_data: pre-processed schemas.
        traverser: SchemaTraverser object
        config: configuration dict
        """
        self.property_data = property_data
        self.traverser = traverser
        self.config = config
        self.level = level
        self.this_section = None
        self.current_version = {} # marker for latest version within property we're displaying.
        self.current_depth = 0

        # Get a list of schemas that will appear in the documentation. We need this to know
        # when to create an internal link, versus a link to a URI.
        self.documented_schemas = []
        schemas = [x for x in property_data.keys()]
        for schema_ref in schemas:
            details = self.property_data[schema_ref]
            if self.skip_schema(details['schema_name']):
                continue
            if len(details['properties']):
                self.documented_schemas.append(schema_ref)

        self.uri_match_keys = None
        if self.config.get('uri_replacements'):
            map_keys = list(self.config['uri_replacements'].keys())
            map_keys.sort(key=len, reverse=True)
            self.uri_match_keys = map_keys

        self.separators = {
            'inline': ', ',
            'linebreak': '<br>'
            }

        # Properties to carry through from parent when a ref is extended:
        self.parent_props = ['description', 'longDescription', 'readonly']


    def emit(self):
        """ Output contents thus far """
        raise NotImplementedError


    def add_section(self, text, link_id=False):
        """ Add a top-level heading """
        raise NotImplementedError


    def add_description(self, text):
        """ Add the schema description """
        raise NotImplementedError


    def add_action_details(self, action_details):
        """ Add the action details (which should already be formatted) """
        if 'action_details' not in self.this_section:
            self.this_section['action_details'] = []
        self.this_section['action_details'].append(action_details)


    def add_profile_conditional_details(self, conditional_details):
        """ Add the conditional requirements for the profile (which should already be formatted) """
        if 'profile_conditional_details' not in self.this_section:
            self.this_section['profile_conditional_details'] = []
        self.this_section['profile_conditional_details'].append(conditional_details)


    def add_json_payload(self, json_payload):
        """ Add a JSON payload for the current section """
        raise NotImplementedError


    def add_property_row(self, formatted_row):
        """Add a row (or group of rows) for an individual property in the current section/schema.

        formatted_row should be a chunk of text already formatted for output"""
        raise NotImplementedError

    def add_property_details(self, formatted_details):
        """Add a chunk of property details information for the current section/schema."""
        raise NotImplementedError


    def format_property_row(self, schema_ref, prop_name, prop_info, prop_path=[]):
        """Format information for a single property. Returns an object with 'row' and 'details'.

        'row': content for the main table being generated.
        'details': content for the Property Details section.

        This may include embedded objects with their own properties.
        """
        raise NotImplementedError


    def format_property_details(self, prop_name, prop_type, prop_description, enum, enum_details,
                                supplemental_details, meta, anchor=None):
        """Generate a formatted table of enum information for inclusion in Property Details."""
        raise NotImplementedError


    def format_list_of_object_descrs(self, schema_ref, prop_items, prop_path):
        """Format a (possibly nested) list of embedded objects.

        We expect this to amount to one definition, usually for 'items' in an array."""

        if isinstance(prop_items, dict):
            if 'properties' in prop_items:
                return self.format_object_descr(schema_ref, prop_items, prop_path)
            else:
                return self.format_non_object_descr(schema_ref, prop_items, prop_path)

        rows = []
        details = {}
        if isinstance(prop_items, list):
            for prop_item in prop_items:
                formatted = self.format_list_of_object_descrs(schema_ref, prop_item, prop_path)
                rows.extend(formatted['rows'])
                details.update(formatted['details'])
            return ({'rows': rows, 'details': details})

        return None

    def format_action_details(self, prop_name, action_details):
        """Generate a formatted Actions section from supplemental markdown."""
        raise NotImplementedError


    def format_action_parameters(self, schema_ref, prop_name, prop_descr, action_parameters):
        """Generate a formatted Actions section from parameters data"""
        raise NotImplementedError


    def format_conditional_details(self, schema_ref, prop_name, conditional_reqs):
        """Generate a formatted Conditional Details section from profile data"""
        raise NotImplementedError


    def output_document(self):
        """Return full contents of document"""
        body = self.emit()
        return body


    def generate_output(self):
        """Generate formatted from schemas and supplemental data.

        Iterates through property_data and traverses schemas for details.
        Format of output will depend on the format_* methods of the class.
        """
        property_data = self.property_data
        traverser = self.traverser
        config = self.config
        schema_supplement = config.get('schema_supplement', {})
        profile_mode = config.get('profile_mode')

        schema_keys = self.documented_schemas
        schema_keys.sort()


        for schema_ref in schema_keys:
            details = property_data[schema_ref]
            schema_name = details['schema_name']
            profile = config.get('profile_resources', {}).get(schema_ref, {})

            # Look up supplemental details for this schema/version
            version = details.get('latest_version', '1')
            major_version = version.split('.')[0]
            schema_key = schema_name + '_' + major_version
            supplemental = schema_supplement.get(schema_key,
                                                 schema_supplement.get(schema_name, {}))

            definitions = details['definitions']

            if config.get('omit_version_in_headers'):
                section_name = schema_name
            else:
                section_name = details['name_and_version']
            self.add_section(section_name, schema_name)
            self.current_version = {}

            # Normative docs prefer longDescription to description
            if config['normative'] and 'longDescription' in definitions[schema_name]:
                description = definitions[schema_name].get('longDescription')
            else:
                description = definitions[schema_name].get('description')

            # Override with supplemental schema description, if provided
            # If there is a supplemental Description or Schema-Intro, it replaces
            # the description in the schema. If both are present, the Description
            # should be output, followed by the Schema-Intro.
            if supplemental.get('description') and supplemental.get('schema-intro'):
                description = (supplemental.get('description') + '\n\n' +
                               supplemental.get('schema-intro'))
            elif supplemental.get('description'):
                description = supplemental.get('description')
            else:
                description = supplemental.get('schema-intro', description)

            # Profile purpose overrides all:
            if profile:
                description = profile.get('Purpose')

            if description:
                self.add_description(description)

            self.add_json_payload(supplemental.get('jsonpayload'))

            if 'properties' in details.keys():
                prop_details = {}
                conditional_details = {}

                properties = details['properties']
                prop_names = [x for x in properties.keys()]
                prop_names = self.organize_prop_names(prop_names, profile)

                for prop_name in prop_names:
                    prop_info = properties[prop_name]
                    prop_info = self.apply_overrides(prop_info, schema_name, prop_name)
                    meta = prop_info.get('_doc_generator_meta', {})
                    prop_infos = self.extend_property_info(schema_ref, prop_info, properties.get('_doc_generator_meta'))

                    formatted = self.format_property_row(schema_ref, prop_name, prop_infos, [])
                    if formatted:
                        self.add_property_row(formatted['row'])
                        if formatted['details']:
                            prop_details.update(formatted['details'])
                        if formatted['action_details']:
                            self.add_action_details(formatted['action_details'])
                        if formatted['profile_conditional_details']:
                            conditional_details.update(formatted['profile_conditional_details'])

                if len(prop_details):
                    detail_names = [x for x in prop_details.keys()]
                    detail_names.sort()
                    for detail_name in detail_names:
                        self.add_property_details(prop_details[detail_name])

                if len(conditional_details):
                    cond_names = [x for x in conditional_details.keys()]
                    cond_names.sort()
                    for cond_name in cond_names:
                        self.add_profile_conditional_details(conditional_details[cond_name])

        return self.output_document()


    def generate_fragment_doc(self, ref, config):
        """Given a path to a definition, generate a block of documentation.

        Used to generate documentation for schema fragments.
        """

        # If /properties is specified, expand the object and output just its contents.
        if ref.endswith('/properties'):
            ref = ref[:-len('/properties')]
            config['strip_top_object'] = True

        if not ref:
            warnings.warn("Can't generate fragment for '" + ref +
                          "': could not parse as schema URI.")
            return ''

        frag_gen = self.__class__(self.property_data, self.traverser, config, self.level)

        if "://" not in ref:
            # Try to find the file locally
            try:
                filepath = ref.split('#')[0]
                localpath = os.path.abspath(filepath)
                fragment_data = DocGenUtilities.load_as_json(localpath)
                if fragment_data:
                    traverser = self.traverser.copy()
                    traverser.add_schema(filepath, fragment_data)
                    frag_gen = self.__class__(self.property_data, traverser, config, self.level)
            except Exception as ex:
                # That's okay, it may still be a URI-style ref without the protocol
                pass

        prop_info = frag_gen.traverser.find_ref_data(ref)

        if not prop_info:
            warnings.warn("Can't generate fragment for '" + ref + "': could not find data.")
            return ''

        schema_ref = prop_info['_from_schema_ref']
        prop_name = prop_info['_prop_name']
        meta = prop_info.get('_doc_generator_meta')
        if not meta:
            meta = {}
        prop_infos = frag_gen.extend_property_info(schema_ref, prop_info)

        formatted = frag_gen.format_property_row(schema_ref, prop_name, prop_infos, [])
        if formatted:
            frag_gen.add_section('')
            frag_gen.current_version = {}

            frag_gen.add_property_row(formatted['row'])
            if len(formatted['details']):
                prop_details = {}
                prop_details.update(formatted['details'])
                detail_names = [x for x in prop_details.keys()]
                detail_names.sort()
                for detail_name in detail_names:
                    frag_gen.add_property_details(prop_details[detail_name])

            if formatted['action_details']:
                frag_gen.add_action_details(formatted['action_details'])

        return frag_gen.emit()


    def extend_property_info(self, schema_ref, prop_info, context_meta=None):
        """If prop_info contains a $ref or anyOf attribute, extend it with that information.

        Returns an array of objects. Arrays of arrays of objects are possible but not expected.
        """
        traverser = self.traverser
        prop_ref = prop_info.get('$ref', None)
        prop_anyof = prop_info.get('anyOf', None)
        if not context_meta:
            context_meta = {}

        prop_infos = []
        outside_ref = None
        schema_name = traverser.get_schema_name(schema_ref)

        # Check for anyOf with a $ref to odata.4.0.0 idRef, and replace it with that ref.
        if prop_anyof:
            for elt in prop_anyof:
                if '$ref' in elt:
                    this_ref = elt.get('$ref')
                    if this_ref.endswith('#/definitions/idRef'):
                        is_link = True
                        prop_ref = this_ref
                        prop_anyof = None
                        break

        if prop_ref:
            if prop_ref.startswith('#'):
                prop_ref = schema_ref + prop_ref
            else:
                idref_info = self.process_for_idRef(prop_ref)
                if idref_info:
                    prop_ref = None
                    # if parent_props were specified in prop_info, they take precedence:
                    for x in prop_info.keys():
                        if x in self.parent_props and prop_info[x]:
                            idref_info[x] = prop_info[x]
                    prop_info = idref_info

        if prop_ref:
            ref_info = traverser.find_ref_data(prop_ref)

            if not ref_info:
                warnings.warn("Unable to find data for " + prop_ref)

            else:
                ref_info = self.apply_overrides(ref_info)
                meta = ref_info.get('_doc_generator_meta')
                if not meta:
                    meta = {}
                node_name = traverser.get_node_from_ref(prop_ref)
                meta = self.merge_metadata(node_name, meta, context_meta)

                from_schema_ref = ref_info.get('_from_schema_ref')
                is_versioned_schema = traverser.is_versioned_schema(from_schema_ref)
                is_other_schema = from_schema_ref and (schema_ref != from_schema_ref)
                is_collection_of = traverser.is_collection_of(from_schema_ref)
                prop_name = ref_info.get('_prop_name', False)
                is_ref_to_same_schema = ((not is_other_schema) and prop_name == schema_name)

                if is_collection_of and ref_info.get('anyOf'):
                    anyof_ref = None
                    for a_of in ref_info.get('anyOf'):
                        if '$ref' in a_of:
                            anyof_ref = a_of['$ref']
                            break;
                    if anyof_ref:
                        idref_info = self.process_for_idRef(anyof_ref)
                        if idref_info:
                            ref_info = idref_info

                # If an object, include just the definition and description, and append a reference if possible:
                if ref_info.get('type') == 'object':
                    ref_description = ref_info.get('description')
                    ref_longDescription = ref_info.get('longDescription')
                    link_detail = ''
                    append_ref = ''

                    from_schema_uri, _, _ = ref_info.get('_ref_uri', '').partition('#')

                    # Links to other Redfish resources are a special case.
                    if is_other_schema or is_ref_to_same_schema:
                        if is_versioned_schema and is_collection_of:
                            append_ref = 'Contains a link to a resource.'
                            ref_schema_name = self.traverser.get_schema_name(is_collection_of)

                            if from_schema_uri.endswith('redfish.dmtf.org/schemas/v1/odata.4.0.0.json') or from_schema_uri.endswith('redfish.dmtf.org/schemas/v1/odata.v4_0_1.json'):
                                from_schema_uri = 'http://' + is_collection_of

                            link_detail = ('Link to Collection of ' + self.link_to_own_schema(is_collection_of, from_schema_uri)
                                           + '. See the ' + ref_schema_name + ' schema for details.')

                        else:
                            if is_versioned_schema:
                                link_detail = ('Link to a ' + prop_name + ' resource. See the Links section and the '
                                               + self.link_to_own_schema(from_schema_ref, from_schema_uri) +
                                               ' schema for details.')

                            if is_ref_to_same_schema:
                                # e.g., a Chassis is contained by another Chassis
                                link_detail = ('Link to another ' + prop_name + ' resource.')

                            else:
                                append_ref = ('See the ' + self.link_to_own_schema(from_schema_ref, from_schema_uri) +
                                              ' schema for details on this property.')

                        new_ref_info = {
                            'type': ref_info.get('type'),
                            'readonly': ref_info.get('readonly'),
                            'description': ref_description,
                            'longDescription': ref_longDescription,
                            'add_link_text': append_ref
                            }

                        if link_detail:
                            new_ref_info['properties'] = {'@odata.id': {'type': 'string',
                                                                        'readonly': True,
                                                                        'description': '',
                                                                        'add_link_text': link_detail}
                                                          }
                        ref_info = new_ref_info

                # if parent_props were specified in prop_info, they take precedence:
                for x in prop_info.keys():
                    if x in self.parent_props and prop_info[x]:
                        ref_info[x] = prop_info[x]
                prop_info = ref_info

                if '$ref' in ref_info or 'anyOf' in ref_info:
                    return self.extend_property_info(ref_info['_from_schema_ref'], ref_info, context_meta)

            prop_infos.append(prop_info)

        elif prop_anyof:
            skip_null = len([x for x in prop_anyof if '$ref' in x])
            sans_null = [x for x in prop_anyof if x.get('type') != 'null']

            # This is a special case for references to multiple versions of the same object.
            if len(sans_null) > 1:
                match_ref = unversioned_ref = ''
                for elt in prop_anyof:
                    this_ref = elt.get('$ref')
                    if this_ref:
                        unversioned_ref = self.make_unversioned_ref(this_ref)
                    if not unversioned_ref:
                        break

                    if not match_ref:
                        match_ref = unversioned_ref
                    else:
                        if match_ref != unversioned_ref:
                            break
                if match_ref == unversioned_ref:
                    prop_infos.append({
                        'type': '',
                        'description': '',
                        'add_link_text': ('See the ' + self.link_to_outside_schema(unversioned_ref) +
                                          ' schema for details.')
                        })
                    prop_anyof = [] # short-circuit any further processing


            for elt in prop_anyof:
                if skip_null and (elt.get('type') == 'null'):
                    continue
                if '$ref' in elt:
                    for x in prop_info.keys():
                        if x in self.parent_props:
                            elt[x] = prop_info[x]
                elt = self.extend_property_info(schema_ref, elt, context_meta)
                prop_infos.extend(elt)

        else:
            prop_infos.append(prop_info)

        return prop_infos


    def organize_prop_names(self, prop_names, profile={}):
        """ Strip out excluded property names, sorting the remainder """

        prop_names = self.filter_props_by_profile(prop_names, profile)
        prop_names = self.exclude_prop_names(prop_names, self.config['excluded_properties'],
                                       self.config['excluded_by_match'])
        prop_names.sort()
        return prop_names

    def filter_props_by_profile(self, prop_names, profile, is_action=False):

        if self.config['profile_mode'] == 'terse':
            if is_action:
                profile_props = [x for x in profile.keys()]
            else:
                profile_props = [x for x in profile.get('PropertyRequirements', {}).keys()]
            if profile.get('ActionRequirements'):
                profile_props.append('Actions')

            if is_action:
                # Action properties typically start with "#SchemaName.", which is not reflected in the profile:
                filtered = []
                for prop in profile_props:
                    if prop in prop_names:
                        filtered.append(prop)
                    else:
                        matches = [x for x in prop_names if x.endswith('.' + prop)]
                        if matches:
                            filtered.append(matches[0])
                prop_names = filtered
            else:
                prop_names = list(set(prop_names) & set(profile_props))
        prop_names.sort()
        return prop_names


    def exclude_annotations(self, prop_names):
        """ Strip out excluded annotations, sorting the remainder """

        return self.exclude_prop_names(prop_names, self.config['excluded_annotations'],
                                       self.config['excluded_annotations_by_match'])


    def exclude_prop_names(self, prop_names, props_to_exclude, props_to_exclude_by_match):
        """Strip out excluded property names, and sort the remainder."""

        # Strip out properties based on exact match:
        prop_names = [x for x in prop_names if x not in props_to_exclude]

        # Strip out properties based on partial match:
        included_prop_names = []
        for prop_name in prop_names:
            excluded = False
            for prop in props_to_exclude_by_match:
                if prop in prop_name:
                    excluded = True
                    break
            if not excluded:
                included_prop_names.append(prop_name)

        included_prop_names.sort()
        return included_prop_names


    def skip_schema(self, schema_name):
        """ True if this schema should be skipped in the output """

        if schema_name in self.config['excluded_schemas']:
            return True
        for pattern in self.config['excluded_schemas_by_match']:
            if pattern in schema_name:
                return True
        return False


    # TODO: we may not use this. Find out and either remove it or document it better:
    def always_expand_schema(self, schema_name):
        """ Optional special case for schemas that lack top-level $ref;

        If expand_defs_from_non_output_schemas is true, expand properties that are in schemas that are present
        but won't be output in the documentation."""

        if not self.config['expand_defs_from_non_output_schemas']:
            return False;

        if self.skip_schema(schema_name):
            return False
        return (self.traverser.is_known_schema(schema_name) and not
                self.traverser.is_collection_of(schema_name) and not
                self.is_documented_schema(schema_name))


    def parse_property_info(self, schema_ref, prop_name, prop_infos, prop_path, within_action=False):
        """Parse a list of one more more property info objects into strings for display.

        Returns a dict of 'prop_type', 'read_only', descr', 'prop_is_object',
        'prop_is_array', 'object_description', 'prop_details', 'item_description',
        'has_direct_prop_details', 'has_action_details', 'action_details', 'nullable',
        'profile_read_req', 'profile_write_req', 'profile_mincount', 'profile_purpose',
        'profile_conditional_req', 'profile_conditional_details'
        """

        if isinstance(prop_infos, dict):
            return self._parse_single_property_info(schema_ref, prop_name, prop_infos,
                                                    prop_path, within_action)

        if len(prop_infos) == 1:
            prop_info = prop_infos[0]
            if isinstance(prop_info, dict):
                return self._parse_single_property_info(schema_ref, prop_name, prop_info,
                                                        prop_path, within_action)
            else:
                return self.parse_property_info(schema_ref, prop_name, prop_info, prop_path, within_action)

        parsed = {'prop_type': [],
                  'prop_units': False,
                  'read_only': False,
                  'descr': [],
                  'add_link_text': '',
                  'prop_is_object': False,
                  'prop_is_array': False,
                  'nullable': False,
                  'object_description': [],
                  'item_description': [],
                  'prop_details': {},
                  'has_direct_prop_details': False,
                  'has_action_details': False,
                  'action_details': {},
                  'profile_read_req': False,
                  'profile_write_req': False,
                  'profile_mincount': False,
                  'profile_purpose': False,
                  'profile_conditional_req': False,
                  'profile_conditional_details': {}
                 }

        profile = {}
        # Skip profile data if prop_name is blank -- this is just an additional row of info and
        # the "parent" row will have the profile info.
        if self.config['profile_mode'] and prop_name:
            profile_section = 'PropertyRequirements'
            if within_action:
                profile_section = 'ActionRequirements'
            path_to_prop = prop_path.copy()
            path_to_prop.append(prop_name)
            profile = self.get_prop_profile(schema_ref, path_to_prop, profile_section)

        anyof_details = [self.parse_property_info(schema_ref, prop_name, x, prop_path, within_action)
                         for x in prop_infos]

        # Remove details for anyOf props with prop_type = 'null'.
        details = []
        has_null = False
        for det in anyof_details:
            if len(det['prop_type']) == 1 and 'null' in det['prop_type']:
                has_null = True
            else:
                details.append(det)
        # Save the null flag so we can display it later:
        parsed['nullable'] = has_null


        # Uniquify these properties and save as lists:
        props_to_combine = ['prop_type', 'descr', 'object_description', 'item_description']

        for property_name in props_to_combine:
            property_values = []
            for det in anyof_details:
                if isinstance(det[property_name], list):
                    for val in det[property_name]:
                        if val and val not in property_values:
                            property_values.append(val)
                else:
                    val = det[property_name]
                    if val and val not in property_values:
                        property_values.append(val)

            parsed[property_name] = property_values

        # read_only and units should be the same for all
        parsed['read_only'] = details[0]['read_only']
        parsed['prop_units'] = details[0]['prop_units']

        # Data from profile:
        parsed['profile_read_req'] = profile.get('ReadRequirement')
        parsed['profile_write_req'] = profile.get('WriteRequirement')
        parsed['profile_mincount'] = profile.get('MinCount')
        parsed['profile_purpose'] = profile.get('Purpose')
        parsed['profile_conditional_req'] = profile.get('ConditionalRequirements')

        for det in details:
            parsed['prop_is_object'] |= det['prop_is_object']
            parsed['prop_is_array'] |= det['prop_is_array']
            parsed['has_direct_prop_details'] |= det['has_direct_prop_details']
            parsed['prop_details'].update(det['prop_details'])
            parsed['has_action_details'] |= det['has_action_details']
            parsed['action_details'].update(det['action_details'])
            parsed['profile_conditional_details'].update(det['profile_conditional_details'])

        return parsed


    def _parse_single_property_info(self, schema_ref, prop_name, prop_info, prop_path, within_action=False):
        """Parse definition of a specific property into strings for display.

        Returns a dict of 'prop_type', 'prop_units', 'read_only', 'descr', 'add_link_text',
        'prop_is_object', 'prop_is_array', 'object_description', 'prop_details', 'item_description',
        'has_direct_prop_details', 'has_action_details', 'action_details', 'nullable',
        'profile_read_req', 'profile_write_req', 'profile_mincount', 'profile_purpose',
        'profile_conditional_req', 'profile_conditional_details'
        """
        traverser = self.traverser

        # type may be a string or a list.
        prop_details = {}
        prop_type = prop_info.get('type', [])
        prop_is_object = False
        object_description = ''
        prop_is_array = False
        item_description = ''
        item_list = '' # For lists of simple types
        array_of_objects = False
        has_prop_details = False
        has_prop_actions = False
        action_details = {}
        profile_conditional_req = False
        profile_conditional_details = {}
        schema_name = traverser.get_schema_name(schema_ref)

        # Some special treatment is required for Actions
        is_action = prop_name == 'Actions'
        if within_action:
            has_prop_actions = True

        # Only objects within Actions have parameters
        action_parameters = prop_info.get('parameters', {})

        if isinstance(prop_type, list):
            prop_is_object = 'object' in prop_type
            prop_is_array = 'array' in prop_type
        else:
            prop_is_object = prop_type == 'object'
            prop_is_array = prop_type == 'array'
            prop_type = [prop_type]

        cleaned_prop_type = []
        has_null = False
        for pt in prop_type:
            if pt == 'null':
                has_null = True
            else:
                cleaned_prop_type.append(pt)
        prop_type = cleaned_prop_type

        prop_units = prop_info.get('units')

        read_only = prop_info.get('readonly')
        if self.config['normative'] and 'longDescription' in prop_info:
            descr = prop_info.get('longDescription', '')
        else:
            descr = prop_info.get('description', '')

        if descr is None:
            descr = ''

        add_link_text = prop_info.get('add_link_text', '')

        if within_action:
            # Extend and parse parameter info
            for action_param in action_parameters.keys():
                params = action_parameters[action_param]
                params = self.extend_property_info(schema_ref, params, {})
                action_parameters[action_param] = self.extend_property_info(schema_ref, action_parameters[action_param], {})

            action_details = self.format_action_parameters(schema_ref, prop_name, descr, action_parameters)

            formatted_action_rows = []
            for param_name in action_parameters:
                formatted_action = self.format_property_row(schema_ref, param_name, action_parameters[param_name], [''])
                # Capture the enum details and merge them into the ones for the overall properties:
                if formatted_action.get('details'):
                    has_prop_details = True
                    prop_details.update(formatted_action['details'])

            self.add_action_details(action_details)


        # Items, if present, will have a definition with either an object, a list of types,
        # or a $ref:
        prop_item = prop_info.get('items')
        list_of_objects = False
        collapse_description = False
        if isinstance(prop_item, dict):
            if 'type' in prop_item and 'properties' not in prop_item:
                prop_items = [prop_item]
                collapse_description = True
            else:
                prop_items = self.extend_property_info(schema_ref, prop_item, prop_info.get('_doc_generator_meta'))
                array_of_objects = True

            list_of_objects = True

        # Enumerations go into Property Details
        prop_enum = prop_info.get('enum')
        supplemental_details = None

        if 'supplemental' in self.config and 'property details' in self.config['supplemental']:
            detconfig = self.config['supplemental']['property details']
            if schema_name in detconfig and prop_name in detconfig[schema_name]:
                supplemental_details = detconfig[schema_name][prop_name]

        if prop_enum or supplemental_details:
            has_prop_details = True

            if self.config['normative'] and 'enumLongDescriptions' in prop_info:
                prop_enum_details = prop_info.get('enumLongDescriptions')
            else:
                prop_enum_details = prop_info.get('enumDescriptions')
            anchor = schema_ref + '|details|' + prop_name
            prop_details[prop_name] = self.format_property_details(prop_name, prop_type, descr,
                                                                   prop_enum, prop_enum_details,
                                                                   supplemental_details,
                                                                   prop_info.get('_doc_generator_meta', {}),
                                                                   anchor)

        # Action details may be supplied as markdown in the supplemental doc.
        # TODO: remove this? Change it?
        supplemental_actions = None
        if 'supplemental' in self.config and 'action details' in self.config['supplemental']:
            action_config = self.config['supplemental']['action details']
            action_name = prop_name
            if '.' in action_name:
                _, _, action_name = action_name.rpartition('.')
            if action_config.get(schema_name) and action_name in action_config[schema_name].keys():
                supplemental_actions = action_config[schema_name][action_name]
                supplemental_actions['action_name'] = action_name

        if supplemental_actions:
            has_prop_actions = True
            formatted_actions = self.format_action_details(prop_name, supplemental_actions)
            action_details = supplemental_actions
            self.add_action_details(formatted_actions)

        # embedded object:
        if prop_is_object:
            new_path = prop_path.copy()
            new_path.append(prop_name)
            object_formatted = self.format_object_descr(schema_ref, prop_info, new_path, is_action)
            object_description = object_formatted['rows']
            if object_formatted['details']:
                prop_details.update(object_formatted['details'])

        # embedded items:
        if prop_is_array:
            new_path = prop_path.copy()
            new_path.append(prop_name)
            if list_of_objects:
                item_formatted = self.format_list_of_object_descrs(schema_ref, prop_items, new_path)
                if collapse_description:
                    # remember, we set collapse_description when we made prop_items a single-element list.
                    item_list = prop_items[0].get('type')

            else:
                item_formatted = self.format_non_object_descr(schema_ref, prop_item, new_path)

            item_description = item_formatted['rows']
            if item_formatted['details']:
                prop_details.update(item_formatted['details'])

        # Read/Write requirements from profile:
        # Skip profile data if prop_name is blank -- this is just an additional row of info and
        # the "parent" row will have the profile info.
        profile = {}
        if self.config['profile_mode'] and prop_name:
            prop_brief_name = prop_name
            profile_section = 'PropertyRequirements'
            if within_action:
                profile_section = 'ActionRequirements'
                if prop_name.startswith('#'): # expected
                    prop_name_parts = prop_name.split('.')
                    prop_brief_name = prop_name_parts[-1]
            path_to_prop = prop_path.copy()
            path_to_prop.append(prop_brief_name)
            profile = self.get_prop_profile(schema_ref, path_to_prop, profile_section)

            # Conditional Requirements
            profile_conditional_req = profile.get('ConditionalRequirements')
            if profile_conditional_req:
                # Add the read and write reqs, as we want to capture those as "Base Requirement":
                req = {'BaseRequirement': True}
                req['ReadRequirement'] = profile.get('ReadRequirement')
                req['WriteRequirement'] = profile.get('WriteRequirement')
                profile_conditional_req.insert(0, req)

                profile_conditional_details[prop_name] = self.format_conditional_details(schema_ref, prop_name,
                                                                                         profile_conditional_req)

        return {'prop_type': prop_type,
                'prop_units': prop_units,
                'read_only': read_only,
                'nullable': has_null,
                'descr': descr,
                'add_link_text': add_link_text,
                'prop_is_object': prop_is_object,
                'prop_is_array': prop_is_array,
                'array_of_objects': array_of_objects,
                'object_description': object_description,
                'item_description': item_description,
                'item_list': item_list,
                'prop_details': prop_details,
                'has_direct_prop_details': has_prop_details,
                'has_action_details': has_prop_actions,
                'action_details': action_details,
                'profile_read_req': profile.get('ReadRequirement'),
                'profile_write_req': profile.get('WriteRequirement'),
                'profile_mincount': profile.get('MinCount'),
                'profile_purpose': profile.get('Purpose'),
                'profile_conditional_req': profile_conditional_req,
                'profile_conditional_details': profile_conditional_details
                }


    def process_for_idRef(self, ref):
        """Convenience method to check ref for 'odata.4.0.0#/definitions/idRef' and if so, return its property info.

        We special-case this a couple of places where we treat other refs a little differently. """
        prop_info = None
        if ref.endswith('#/definitions/idRef'):
            # idRef is a special case; we just want to pull in its definition and stop.
            prop_info = self.traverser.find_ref_data(ref)
            if not prop_info:
                # We must not have the odata schema, but we know what it is.
                prop_info = {'properties':
                             {'@odata.id':
                              {'type': 'string',
                               'readonly': True,
                               "description": "The unique identifier for a resource.",
                               "longDescription": "The value of this property shall be the unique identifier for the resource and it shall be of the form defined in the Redfish specification.",
                               }
                              }
                             }
        return prop_info


    def format_object_descr(self, schema_ref, prop_info, prop_path=[], is_action=False):
        """Format the properties for an embedded object."""

        properties = prop_info.get('properties')
        output = []
        details = {}
        action_details = {}

        context_meta = prop_info.get('_doc_generator_meta')
        if not context_meta:
            context_meta = {}

        # If prop_info was extracted from a different schema, it will be present as
        # _from_schema_ref
        schema_ref = prop_info.get('_from_schema_ref', schema_ref)

        if properties:
            prop_names = [x for x in properties.keys()]
            prop_names = self.exclude_annotations(prop_names)


            # TODO: probably refactor this block:
            if self.config['profile_mode'] == 'terse':
                if len(prop_path) and prop_path[0] == 'Actions':
                    profile_section = 'ActionRequirements'
                else:
                    profile_section = 'PropertyRequirements'
                profile = self.get_prop_profile(schema_ref, prop_path, profile_section)
                prop_names = self.filter_props_by_profile(prop_names, profile, is_action)
                filtered_properties = {}
                for k in prop_names:
                    filtered_properties[k] = properties[k]
                prop_info['properties'] = properties = filtered_properties


            if is_action:
                prop_names = [x for x in prop_names if x.startswith('#')]

            for prop_name in prop_names:
                meta = {}
                base_detail_info = properties[prop_name]
                detail_info = self.extend_property_info(schema_ref, base_detail_info, context_meta)
                meta = detail_info[0].get('_doc_generator_meta', {})
                meta = self.merge_metadata(prop_name, meta, context_meta)

                if is_action:
                    # Trim out the properties; these are always Target and Title:
                    detail_info[0]['properties'] = {}

                meta['within_action'] = is_action
                detail_info[0]['_doc_generator_meta'] = meta

                new_path = prop_path.copy()

                formatted = self.format_property_row(schema_ref, prop_name, detail_info, new_path)
                if formatted:
                    output.append(formatted['row'])
                    if formatted['details']:
                        details.update(formatted['details'])
                    if formatted['action_details']:
                        action_details[prop_name] = formatted['action_details']

        return {'rows': output, 'details': details, 'action_details': action_details}


    def format_non_object_descr(self, schema_ref, prop_dict, prop_path=[]):
        """For definitions that just list simple types without a 'properties' entry"""

        output = []
        details = {}
        action_details = {}

        prop_name = prop_dict.get('_prop_name', '')
        detail_info = self.extend_property_info(schema_ref, prop_dict)

        formatted = self.format_property_row(schema_ref, prop_name, detail_info, prop_path)

        if formatted:
            output.append(formatted['row'])
            details = formatted.get('details', {})
            action_details = formatted.get('action_details', {})

        return {'rows': output, 'details': details, 'action_details': action_details}



    def link_to_own_schema(self, schema_ref, schema_full_uri):
        """ String for output. Override in HTML formatter to get actual links. """
        schema_name = self.traverser.get_schema_name(schema_ref)
        if schema_name:
            return schema_name
        return schema_ref


    def link_to_outside_schema(self, schema_full_uri):
        """ String for output. Override in HTML formatter to get actual links."""
        return schema_full_uri

    def get_documentation_uri(self, ref_uri):
        """ If ref_uri is matched in self.config['uri_replacements'], provide a reference to that """

        if not self.uri_match_keys:
            return None

        replacement = None
        for key in self.uri_match_keys:
            if key in ref_uri:
                match_list = self.config['uri_replacements'][key]
                for match_spec in match_list:
                    if match_spec.get('full_match') and match_spec['full_match'] == ref_uri:
                        replacement = match_spec.get('replace_with')
                    elif match_spec.get('wild_match'):
                        pattern = '.*' + ''.join(match_spec['wild_match']) + '.*'
                        if re.search(pattern, ref_uri):
                            replacement = match_spec.get('replace_with')

        return replacement


    # Override in HTML formatter to get actual links.
    def get_documentation_link(self, ref_uri):
        """ Provide a string referring to ref_uri. """
        target = self.get_documentation_uri(ref_uri)
        if target:
            return "See " + target
        return False

    def is_documented_schema(self, schema_name):
        """ True if the schema will appear as a section in the output documentation """
        return schema_name in self.documented_schemas


    def apply_overrides(self, prop_info, schema_name=None, prop_name=None):
        """ Apply overrides from config to prop_info. Returns a modified copy of prop_info. """

        prop_info = copy.deepcopy(prop_info)

        if not schema_name:
            schema_name = prop_info.get('_schema_name')

        if not prop_name:
            prop_name = prop_info.get('_prop_name')

        local_overrides = self.config.get('schema_supplement', {}).get(schema_name, {}).get('description overrides')
        if local_overrides:
            if prop_name in local_overrides:
                prop_info['description'] = prop_info['longDescription'] = local_overrides[prop_name]
                return prop_info
        if prop_name in self.config.get('property_description_overrides', {}):
            prop_info['description'] = prop_info['longDescription'] = self.config['property_description_overrides'][prop_name]

        units_trans = self.config['units_translation'].get(prop_info.get('units'))
        if units_trans:
            prop_info['units'] = units_trans

        return prop_info


    @staticmethod
    def truncate_version(version_string, num_parts):
        """Truncate the version string to at least the specified number of parts.

        Maintains additional part(s) if non-zero.
        """

        parts = version_string.split('.')
        keep = []
        for part in parts:
            if len(keep) < num_parts:
                keep.append(part)
            elif part != '0':
                keep.append(part)
            else:
                break

        return '.'.join(keep)


    @staticmethod
    def make_unversioned_ref(this_ref):
        """Get the un-versioned string based on a (possibly versioned) ref"""

        unversioned = None
        pattern = re.compile(r'(.+)\.([^\.]+)\.json#(.+)')
        match = pattern.fullmatch(this_ref)
        if match:
            unversioned = match.group(1) + '.json#' + match.group(3)
        return unversioned


    @staticmethod
    def text_map(text):
        """Replace string for output -- used to replace strings with nicer English text"""

        output_map = {
            'IfImplemented': 'If Implemented',
            'Conditional': 'Conditional Requirements',
            }
        return output_map.get(text, text)


    def compare_versions(self, version, context_version):
        """ Returns +1 if version is newer than context_version, -1 if version is older, 0 if equal """

        if version == context_version:
            return 0
        else:
            version_parts = version.split('.')
            context_parts = context_version.split('.')
            # versions are expected to have three parts
            for i in range(3):
                if version_parts[i] > context_parts[i]:
                    return +1
                if version_parts[i] < context_parts[i]:
                    return 1
            return 0

    def merge_metadata(self, node_name, meta, context_meta):
        """ Merge version and version_deprecated information from meta with that from context_meta

        context_meta contains version info for the parent, plus embedded version info for node_name
        (and its siblings). We want:
        * If context_meta['node_name']['version'] is newer than meta['version'], use the newer version.
          (implication is that this property was added to the parent after it was already defined elsewhere.)
        For deprecations, it's even less likely differing versions will make sense, but we generally want the
        older version.
        """
        node_meta = context_meta.get(node_name, {})

        if ('version' in meta) and ('version' in node_meta):
            compare = self.compare_versions(meta['version'], node_meta['version'])
            if compare > 0:
                # node_meta is newer; use that.
                meta['version'] = node_meta['version']
        elif 'version' in node_meta:
            meta['version'] = node_meta['version']

        if ('version_deprecated' in meta) and ('version_deprecated' in context_meta):
            compare = self.compare_versions(meta['version_deprecated'], node_meta['version_deprecated'])
            if compare < 0:
                # node_meta is older, use that:
                meta['version_deprecated'] = node_meta['version_deprecated']
        elif 'version_deprecated' in node_meta:
            meta['version_deprecated'] = node_meta['version_deprecated']
            meta['version_deprecated_explanation'] = node_meta.get('version_deprecated_explanation', '')

        return meta

    def get_prop_profile(self, schema_ref, prop_path, section):
        """Get profile data for the specified property, by schema_ref, prop name path, and section.

        Section is 'PropertyRequirements' or 'ActionRequirements'.
        Returns {} if no data is present."""

        prop_profile = {}

        if self.config['profile_resources']:
            prop_profile = self.config['profile_resources'].get(schema_ref, {})
            if section == 'ActionRequirements':
                if prop_path[0] == 'Actions':
                    prop_path = prop_path[1:]
            prop_reqs = prop_profile.get(section, {})
            prop_profile = prop_reqs

            for prop_name in prop_path:
                if not prop_name:
                    continue
                prop_profile = prop_reqs.get(prop_name, {})
                prop_reqs = prop_profile.get('PropertyRequirements', {})

        return prop_profile
