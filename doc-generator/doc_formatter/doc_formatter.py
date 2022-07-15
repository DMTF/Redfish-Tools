# Copyright Notice:
# Copyright 2016-2022 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

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
import functools
from doc_gen_util import DocGenUtilities
from format_utils import FormatUtils


class DocFormatter:
    """Generic class for schema documentation formatter"""

    def __init__(self, property_data, traverser, config, level=0):
        """Set up the markdown generator.

        property_data: pre-processed schemas.
        traverser: SchemaTraverser object
        config: configuration dict
        """
        self.property_data = property_data
        self.common_properties = {}
        self.common_property_details = {}
        self.traverser = traverser
        self.config = config
        self.level = level
        self.this_section = None
        self.current_version = {} # marker for latest version within property we're displaying.
        self.current_depth = 0
        self.sections = []
        self.registry_sections = []
        self.collapse_list_of_simple_type = True
        self.formatter = FormatUtils() # Non-markdown formatters will override this.
        self.layout_payloads = 'bottom' # Do payloads go at top of section or bottom?
        self.current_uris = []
        self.ref_deduplicator = {} # Tracks use of refs within a schema to assist in combining them for output.
        self.ref_counts = {}       # Summarized data from self.ref_deduplicator
        self.format_annotation_strings = { # map format annotations to desired output
                                           'uri': 'URI',
                                           'uri-reference': 'URI'
                                            }

        if self.config.get('profile_mode'):
            self.config['MinVersionLT1.6'] = False
            # Check whether Protocol MinVersion is < 1.6; we will need to add a note to URI conditions if so.
            minversion = self.config.get('profile_protocol', {}).get('MinVersion', '1.0')
            compare = DocGenUtilities.compare_versions(minversion, '1.6.0')
            if compare < 0:
                self.config['MinVersionLT1.6'] = True

        # Extend config with some defaults.
        self.config['excluded_pattern_props'] = self.config.get('excluded_pattern_props', [])

        # We need this flag to distinguish "slate" markdown from standard markdown:
        self.markdown_mode = config.get('output_format', 'markdown')

        # Get a list of schemas that will appear in the documentation. We need this to know
        # when to create an internal link, versus a link to a URI.
        self.documented_schemas = []
        schemas = [x for x in property_data.keys()]
        for schema_ref in schemas:
            details = self.property_data[schema_ref]
            if details.get('schema_name') and self.skip_schema(details['schema_name']):
                continue
            if 'common_object_schemas' in self.config and schema_ref in self.config['common_object_schemas']:
                continue
            if len(details.get('properties', {})):
                self.documented_schemas.append(schema_ref)

        self.uri_match_keys = None
        if self.config.get('schema_link_replacements'):
            map_keys = list(self.config['schema_link_replacements'].keys())
            map_keys.sort(key=len, reverse=True)
            self.uri_match_keys = map_keys

        self.separators = {
            'inline': ', ',
            'linebreak': '\n',
            'pattern': ', '
            }

        # Properties to carry through from parent when a ref is extended:
        self.parent_props = [
            'description', 'longDescription', 'verbatim_description', 'fulldescription_override', 'pattern',
            'readonly', 'prop_required', 'prop_required_on_create', 'requiredParameter', 'required_parameter',
            'versionAdded', 'versionDeprecated', 'deprecated', 'enumVersionAdded', 'enumVersionDeprecated', 'enumDeprecated',
            'translation', '_profile', '_subset'
            ]




    def format_version_strings(self, prop_info):
        """ Generate version added, version deprecated strings """

        version_string = deprecated_descr = None
        version = version_depr = deprecated_descr = None

        version_added = None
        version_deprecated = None
        version_deprecated_explanation = ''
        if isinstance(prop_info, list):
            version_added = prop_info[0].get('versionAdded')
            version_deprecated = prop_info[0].get('versionDeprecated')
            version_deprecated_explanation = prop_info[0].get('deprecated')
        elif isinstance(prop_info, dict):
            version_added = prop_info.get('versionAdded')
            version_deprecated = prop_info.get('versionDeprecated')
            version_deprecated_explanation = prop_info.get('deprecated')

        deprecated_descr = None

        if version_added:
            version = self.format_version(version_added)
        self.current_version[self.current_depth] = version

        # Don't display version if there is a parent version and this is not newer:
        parent_depth = self.current_depth - 1
        if version and self.current_version.get(parent_depth):
            if DocGenUtilities.compare_versions(version, self.current_version.get(parent_depth)) <= 0:
                version = None


        if version_added:
            version = self.format_version(version_added)
        if version_deprecated:
            version_depr = self.format_version(version_deprecated)

        if version and version != '1.0.0':
            version_text = self.escape_text(version)
            version_display = self.truncate_version(version_text, 2) + '+'
            if version_deprecated:
                version_depr_text = self.escape_text(version_depr)
                deprecated_display = self.truncate_version(version_depr_text, 2)
                version_string = _('(v%(version_number)s, deprecated v%(deprecated_version)s') % {'version_number': version_display, 'deprecated_version':  deprecated_display}
                deprecated_descr = self.escape_text(_('Deprecated in v%(deprecated_version)s and later. %(explanation)s') % {'deprecated_version': deprecated_display,
                                                                                                                                'explanation': version_deprecated_explanation})
            else:
                version_string = _('(v%(version_number)s)') % {'version_number': version_display}
        elif version_deprecated:
            version_depr_text = self.escape_text(version_depr)
            deprecated_display = self.truncate_version(version_depr_text, 2)
            version_string = _('(deprecated v%(deprecated_version)s)') % {'deprecated_version': deprecated_display}
            deprecated_descr = self.escape_text(_('Deprecated in v%(deprecated_version)s and later. %(explanation)s') %
                                                    {'deprecated_version': deprecated_display,
                                                        'explanation': version_deprecated_explanation})
        return {"version_string": version_string, "deprecated_descr": deprecated_descr}


    def emit(self):
        """ Output contents thus far """
        raise NotImplementedError


    def add_section(self, text, link_id=False, schema_ref=False):
        """ Add a container for all the information in a section """
        raise NotImplementedError


    def add_description(self, text):
        """ Add the schema description """
        raise NotImplementedError

    def add_deprecation_text(self, deprecation_text):
        """ Add deprecation text for a schema """
        raise NotImplementedError


    def add_uris(self, uris):
        """ Add the uris """
        raise NotImplementedError


    def add_conditional_requirements(self, text):
        """ Add a conditional requirements, which should already be formatted """
        raise NotImplementedError


    def add_release_history(self, release_history, versionDeprecated=False):
        """ Add the release history. """

        summarized = self.summarize_release_history(release_history, versionDeprecated)
        versions = [self.formatter.bold(_('Version'))]
        releases = [self.formatter.bold(_('Release'))]
        for elt in summarized:
            versions.append(self.formatter.italic(elt['version']))
            releases.append(elt['release'])
        heading = self.formatter.head_three(_("Revision history"), self.level);
        formatted = self.formatter.make_table([self.formatter.make_row(versions), self.formatter.make_row(releases)])
        if self.config.get('with_table_numbering'):
            caption = self.formatter.add_table_caption(_("Revision history"));
            reference = self.formatter.add_table_reference(_("The revision history is summarized in "));
            formatted = reference + "\n\n" + formatted + "\n\n" + caption
        self.this_section['release_history'] = formatted


    def format_uri_block_for_action(self, action, uris):
        """ Create a URI block for this action & the resource's URIs """
        uri_content = self.formatter.para(self.formatter.bold((_('Action URI: %(link)s') % {'link': '{' + _('Base URI of target resource') + '}/Actions/' + action})))
        return uri_content


    def format_uri(self, uri):
        """ Format a URI for output. """
        # This is highlighting for markdown. Override for other output.
        uri_parts = uri.split('/')
        uri_parts_highlighted = []
        for part in uri_parts:
            if part.startswith('{') and part.endswith('}'):
                part = self.formatter.italic(part)
            uri_parts_highlighted.append(part)
        uri_highlighted = '/&#8203;'.join(uri_parts_highlighted)
        return uri_highlighted


    def format_uris_for_table(self, uris):
        """ Format a bunch of uris to go into a table cell """
        return '<br>'.join([self.format_uri(x) for x in sorted(uris, key=str.lower)])


    def format_json_payload(self, json_payload):
        """ Format a json payload for output. """
        return json_payload


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
        if json_payload:
            self.this_section['json_payload'] = self.format_json_payload(json_payload)
        else:
            self.this_section['json_payload'] = None


    def add_property_row(self, formatted_row):
        """Add a row (or group of rows) for an individual property in the current section/schema.

        formatted_row should be a chunk of text already formatted for output"""
        raise NotImplementedError

    def add_registry_reqs(self, registry_reqs):
        """Add registry messages. registry_reqs includes profile annotations."""
        raise NotImplementedError


    def format_property_row(self, schema_ref, prop_name, prop_info, prop_path=[], in_array=False, as_action_parameters=False,
                                in_schema_ref=None):
        """Format information for a single property. Returns an object with 'row' and 'details'.

        'row': content for the main table being generated.
        'details': content for the Property Details section.

        This may include embedded objects with their own properties.
        """
        raise NotImplementedError


    def format_property_details(self, prop_name, prop_type, prop_description, enum, enum_details,
                                    supplemental_details, parent_prop_info, profile=None, subset=None):
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

    def format_action_parameters(self, schema_ref, prop_name, prop_descr, action_parameters, profile,
                                     version_strings=None, supplemental_details=None, subset=None):
        """Generate a formatted Actions section from parameters data"""
        raise NotImplementedError


    def format_action_response(self, schema_ref, action_param_name, action_response):
        """Format the data from an actionResponse"""

        formatted = []

        formatted.append(self.formatter.para(self.formatter.bold(_("Response Payload"))))

        rows = []
        # add a "start object" row:
        rows.append(self.formatter.make_row(['{', '','','']))

        formatted_rows = self.format_object_descr(schema_ref, action_response, [action_param_name], False)
        rows = rows + formatted_rows['rows']

        # Add a closing } to the last row:
        rows = self.add_object_close(rows, '', '}', 4)

        formatted.append(self.formatter.make_table(rows, last_column_wide=True))

        return "\n".join(formatted)



    def format_base_profile_access(self, formatted_details):
        """Massage profile read/write requirements for display"""

        if formatted_details.get('is_in_profile'):
            profile_access = self._format_profile_access(read_only=formatted_details.get('read_only', False),
                                                         read_req=formatted_details.get('profile_read_req'),
                                                         write_req=formatted_details.get('profile_write_req'),
                                                         min_count=formatted_details.get('profile_mincount'))
        elif self.config.get('profile_mode') == 'terse':
            if formatted_details.get('prop_required'):
                read_req = 'Mandatory'
            else:
                read_req = ''

            profile_access = self._format_profile_access(read_only=formatted_details.get('read_only', False),
                                                         read_req=read_req,
                                                         write_req=False,
                                                         min_count=False)

        else:
            profile_access = ''

        return profile_access


    def format_conditional_access(self, conditional_req):
        """Massage conditional profile read/write requirements."""

        profile_access = self._format_profile_access(read_req=conditional_req.get('ReadRequirement'),
                                                     write_req=conditional_req.get('WriteRequirement'),
                                                     min_count=conditional_req.get('MinCount'))
        return profile_access


    def _format_profile_access(self, read_only=False, read_req=None, write_req=None, min_count=None):
        """Common formatting logic for profile_access column"""

        profile_access = ''
        if not self.config.get('profile_mode'):
            return profile_access

        # Each requirement  may be Mandatory, Recommended, IfImplemented, Conditional, or (None)
        if not read_req:
            read_req = 'Mandatory' # This is the default if nothing is specified.
        if read_only:
            profile_access = _('%(access_condition)s (Read-only)') % {'access_condition': self.formatter.nobr(self.text_map(read_req))}
        elif read_req == write_req:
            profile_access = _('%(access_condition)s (Read/Write)') % {'access_condition': self.formatter.nobr(self.text_map(read_req))}
        elif not write_req:
            profile_access = _('%(access_condition)s (Read)') % {'access_condition': self.formatter.nobr(self.text_map(read_req))}
        else:
            # Presumably Read is Mandatory and Write is Recommended; nothing else makes sense.
            profile_access = (_('%(access_condition)s (Read)') % {'access_condition': self.formatter.nobr(self.text_map(read_req))}
                                  + self.formatter.br() +
                                  _('%(access_condition)s (Read/Write)') % {'access_condition': self.formatter.nobr(self.text_map(read_req))})

        if min_count:
            if profile_access:
                profile_access += self.formatter.br()

            profile_access += self.formatter.nobr(_('Minimum %(count)s') % {'count': str(min_count)})

        return profile_access


    def format_conditional_details(self, schema_ref, prop_name, conditional_reqs):
        """Generate a formatted Conditional Details section from profile data"""
        formatted = []

        if prop_name:
            anchor = schema_ref + '|conditional_reqs|' + prop_name
            if self.markdown_mode == 'slate':
                formatted.append(self.formatter.head_five(prop_name, self.level, anchor))
            else:
                formatted.append(self.formatter.head_four(prop_name, self.level, anchor))

        rows = []
        for creq in conditional_reqs:
            req_desc = ''
            purpose = creq.get('Purpose', self.formatter.nbsp()*10)
            subordinate_to = creq.get('SubordinateToResource')
            compare_property = creq.get('CompareProperty')
            comparison = creq.get('Comparison')
            values = creq.get('Values', [])
            uris = creq.get('URIs')
            uri_protocol_note = ''
            req = self.format_conditional_access(creq)

            if creq.get('BaseRequirement'):
                # Don't output the base requirement
                continue
            elif subordinate_to:
                req_desc = _('Resource instance is subordinate to %(resource_list)s') % {'resource_list':  (' ' + _('from') + ' ').join('"' + x + '"' for x in subordinate_to)}
            elif uris:
                req_desc = "Resource URI is: " + self.format_uris_for_table(uris)
                if self.config['MinVersionLT1.6']:
                    purpose = _('Applies if Protocol version is 1.6+')

            if compare_property:
                compare_to = creq.get('CompareType', '')
                if compare_to in ['Equal', 'LessThanOrEqual', 'GreaterThanOrEqual', 'NotEqual']:
                    compare_to += ' ' +  _('to')

                compare_values = creq.get('CompareValues')
                if compare_values:
                    compare_values = ', '.join(['"' + x + '"' for x in compare_values])

                if req_desc:
                    req_desc += ' ' + _('and') + ' '
                req_desc += '"' + compare_property + '" ' + _('is') + ' ' + compare_to

                if compare_values:
                    req_desc += ' ' + compare_values

                if comparison and len(values):
                    # req += ', must be ' + comparison + ' ' + ', '.join(['"' + val + '"' for val in values])
                    req += _(', must be %(comparison_word)s %(list)s') % {'comparison_word': comparison, 'list': ', '.join(['"' + val + '"' for val in values])}
            rows.append(self.formatter.make_row([req_desc, req, purpose]))

        formatted.append(self.formatter.make_table(rows))

        return "\n".join(formatted)


    def append_unique_values(self, value_list, target_list):
        """ Unwind possibly-nested list, producing a list of unique strings found. """

        for val in value_list:
            if isinstance(val, list):
                self.append_unique_values(val, target_list)
            else:
                if val and val not in target_list:
                    target_list.append(val)


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
        subset_mode = config.get('subset_mode')

        schema_keys = self.documented_schemas
        schema_keys.sort(key=str.lower)

        # Do a pass over the explicitly-called-out common properties:
        common_refs = []
        if config.get('reference_disposition'):
            for k, disp in config['reference_disposition'].items():
                if disp == 'common_object' and '#' in k:
                    cref = DocGenUtilities.make_unversioned_ref(k)
                    common_refs.append(k)

        for common_ref in common_refs:
            ref_info = traverser.find_ref_data(common_ref)
            if ref_info:
                self.common_properties[common_ref] = ref_info
            else:
                warnings.warn("Common property '%(reference)s' was not found." % {'reference': common_ref})

        for schema_ref in schema_keys:
            details = property_data[schema_ref]
            schema_name = details['schema_name']
            profile = config.get('profile_resources', {}).get(schema_ref, {})
            subset  = config.get('subset_resources', {}).get(schema_name, {})
            self.ref_deduplicator[schema_ref] = {}

            version = property_data.get('latest_version', '1')
            supplemental = self.get_supplemental_details(schema_ref)

            json_payload = None
            if self.config.get('payloads'):
                payload_key = DocGenUtilities.get_payload_name(schema_name, version)
                payload = self.config['payloads'].get(payload_key)
                if payload:
                    json_payload = payload
                else:
                    if self.config.get('warn_missing_payloads'):
                        warnings.warn("MISSING JSON PAYLOAD FOR SCHEMA '%(schema_name)s'." %{'schema_name': schema_name})
            if not json_payload and supplemental.get('jsonpayload'):
                json_payload = supplemental.get('jsonpayload')

            definitions = details['definitions']

            if config.get('omit_version_in_headers'):
                section_name = schema_name
            else:
                section_name = details['name_and_version']
            self.add_section(section_name, schema_name, schema_ref)
            self.current_version = {}

            if profile.get('URIs'):
                uris = profile['URIs']
            else:
                uris = details['uris']

            conditional_details = None
            if profile.get('ConditionalRequirements'):
                conditional_reqs = profile.get('ConditionalRequirements')
                conditional_details = self.format_conditional_details(schema_ref, None, conditional_reqs)

            # Normative docs prefer longDescription to description
            if config.get('normative') and 'longDescription' in definitions[schema_name] and definitions[schema_name].get('description') != definitions[schema_name].get('longDescription'):
                description = definitions[schema_name].get('description') + '<ul><li>' +definitions[schema_name].get('longDescription') + '</li></ul>'
            else:
                description = definitions[schema_name].get('description')

            required = definitions[schema_name].get('required', [])
            required_on_create = definitions[schema_name].get('requiredOnCreate', [])

            # Override with supplemental schema description, if provided
            # If there is a supplemental "description" or "intro", it replaces
            # the description in the schema. If both are present, the "description"
            # should be output, followed by the "intro".
            if supplemental.get('description') and supplemental.get('intro'):
                description = (supplemental.get('description') + '\n\n' +
                               supplemental.get('intro'))
            elif supplemental.get('description'):
                description = supplemental.get('description')
            else:
                description = supplemental.get('intro', description)

            # Profile purpose overrides all:
            if profile:
                description = profile.get('Purpose')

            if description:
                self.add_description(description)

            if details.get('deprecated'):
                self.add_deprecation_text(details['deprecated'])

            if len(uris):
                self.add_uris(uris)
                self.current_uris = uris
            else:
                self.current_uris = []

            if details.get('release_history') and not self.config.get('suppress_version_history'):
                self.add_release_history(details['release_history'], details.get('versionDeprecated'))

            if conditional_details:
                self.add_conditional_requirements(conditional_details)

            self.add_json_payload(json_payload)

            if 'properties' in details.keys():
                prop_details = {}
                conditional_details = {}

                properties = details['properties']
                prop_names = [x for x in properties.keys()]
                if self.config.get('profile_mode') and profile:
                    prop_names = self.filter_props_by_profile(prop_names, profile, required, False)
                if self.config.get('subset_mode') and subset:
                    prop_names = self.filter_props_by_subset(prop_names, subset)

                prop_names = self.organize_prop_names(prop_names)

                # If combining of multiple refs is requested, do a first pass, counting refs:
                if self.config.get('combine_multiple_refs', 0) > 1:
                    for prop_name in prop_names:
                        prop_info = properties[prop_name]
                        if profile:
                            prop_info['_profile'] = profile.get('PropertyRequirements', {}).get(prop_name)
                        if subset:
                            prop_info['_subset'] = subset.get('Properties', {}).get(prop_name)

                        # Note: we are calling extend_property_info here solely for the purpose of counting refs.
                        # In the next loop we call it again to generate the data to format -- we need to get the complete count
                        # of in-schema refs before generating data to format.
                        prop_infos = self.extend_property_info(schema_ref, prop_info)

                        # If we've extended an in-schema reference, capture it:
                        prop_info_ref_uri = self.count_ref_in_schema(schema_ref, prop_infos[0])

                        # Extend further so all ref counts are updated before we start formatting output:
                        self.extend_and_count_refs(schema_ref, prop_infos)

                    self.ref_counts[schema_ref] = self.summarize_duplicates(self.ref_deduplicator.get(schema_ref, {}))

                for prop_name in prop_names:
                    prop_info = properties[prop_name]
                    prop_info['prop_required'] = prop_info.get('prop_required') or prop_name in required
                    prop_info['prop_required_on_create'] = prop_info.get('prop_required_on_create') or prop_name in required_on_create
                    prop_info['parent_requires'] = required
                    prop_info['parent_requires_on_create'] = required_on_create
                    prop_info['required_parameter'] = prop_info.get('requiredParameter')
                    if profile:
                        prop_info['_profile'] = profile.get('PropertyRequirements', {}).get(prop_name)
                    if subset:
                        prop_info['_subset'] = subset.get('Properties', {}).get(prop_name)

                    prop_infos = self.extend_property_info(schema_ref, prop_info)
                    formatted = self.format_property_row(schema_ref, prop_name, prop_infos, [])
                    if formatted:
                        # Skip "Actions" if requested. Everything else is output.
                        if prop_name != 'Actions' or self.config.get('actions_in_property_table', True):
                            self.add_property_row(formatted['row'])
                        if formatted['details']:
                            self.merge_prop_details(prop_details, formatted['details'])
                        if formatted['action_details']:
                            self.add_action_details(formatted['action_details'])
                        if formatted.get('profile_conditional_details'):
                            conditional_details.update(formatted['profile_conditional_details'])

                if self.common_property_details:
                    self.merge_prop_details(prop_details, self.common_property_details)
                if len(prop_details):
                    self.merge_prop_details(self.this_section['property_details'], prop_details)

                if len(conditional_details):
                    cond_names = [x for x in conditional_details.keys()]
                    cond_names.sort(key=str.lower)
                    for cond_name in cond_names:
                        self.add_profile_conditional_details(conditional_details[cond_name])



        if self.config.get('profile_mode'):
            # Add registry messages, if in profile.
            registry_reqs = config.get('profile').get('registries_annotated', {})
            if registry_reqs:
                self.add_registry_reqs(registry_reqs)

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
            warnings.warn("Can't generate fragment for '%(reference)s': could not parse as schema URI." % {'reference': ref})
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

        # Give frag_gen our common_properties to share. This way, we get the updates.
        frag_gen.common_properties = self.common_properties

        if not prop_info:
            warnings.warn("Can't generate fragment for '%(reference)s': could not find data." % {'reference': ref})
            return ''

        schema_ref = prop_info['_from_schema_ref']
        prop_name = prop_info['_prop_name']

        prop_infos = frag_gen.extend_property_info(schema_ref, prop_info)

        formatted = frag_gen.format_property_row(schema_ref, prop_name, prop_infos, [])
        if formatted:
            frag_gen.add_section('', '', schema_ref)
            frag_gen.current_version = {}

            # Skip "Actions" if requested. Everything else is output.
            if prop_name != 'Actions' or self.config.get('actions_in_property_table', True):
                frag_gen.add_property_row(formatted['row'])
            if len(formatted['details']):
                frag_gen.merge_prop_details(frag_gen.this_section['property_details'], formatted['details'])

            if formatted['action_details']:
                frag_gen.add_action_details(formatted['action_details'])

        return frag_gen.emit()


    def generate_common_properties_doc(self):
        """ Generate output for common object properties """
        config = copy.deepcopy(self.config)
        config['strip_top_object'] = True
        schema_supplement = config.get('schema_supplement', {})

        cp_gen = self.__class__(self.property_data, self.traverser, config, self.level)

        # Sort the properties by prop_name
        def sortkey(elt):
            key = elt[1].get('_prop_name', '') + ' ' + elt[1].get('_latest_version', '') +  elt[0]
            return key.lower()
        sorted_properties = sorted(self.common_properties.items(), key=sortkey)

        for prop_tuple in sorted_properties:
            (ref, prop_info) = prop_tuple
            schema_ref = prop_info['_from_schema_ref']
            prop_name = prop_info['_prop_name']

            if self.skip_schema(prop_name):
                continue;
            version = prop_info.get('_latest_version')
            if not version:
                version = DocGenUtilities.get_ref_version(prop_info.get('_ref_uri', ''))

            prop_infos = cp_gen.extend_property_info(schema_ref, prop_info)

            # Get the supplemental details for this property/version.
            # (Probably the version information is not desired?)
            prop_key = prop_name
            if version:
                major_version = version.split('.')[0]
                prop_key = prop_name + '_' + major_version

            supplemental = schema_supplement.get(prop_key,
                                                 schema_supplement.get(prop_name, {}))

            formatted = cp_gen.format_property_row(schema_ref, prop_name, prop_infos, [])
            if formatted:
                # TODO: There is an opportunity here to refactor with code around line 319 in generate_output.
                ref_id = 'common-properties-' + prop_name
                if version:
                    ref_id += '_v' + version

                cp_gen.add_section(prop_name, ref_id, schema_ref)
                if supplemental.get('jsonpayload'):
                    payload = supplemental.get('jsonpayload')
                    cp_gen.add_json_payload(payload)

                # Override with supplemental schema description, if provided
                # If there is a supplemental "description" or "intro", it replaces
                # the description in the schema. If both are present, the "description"
                # should be output, followed by the "intro".
                description = self.get_property_description(prop_info)

                if supplemental.get('description') and supplemental.get('intro'):
                    description = (supplemental.get('description') + '\n\n' +
                                   supplemental.get('intro'))
                elif supplemental.get('description'):
                    description = supplemental.get('description')
                else:
                    description = supplemental.get('intro', description)

                if description:
                    cp_gen.add_description(description)
                cp_gen.current_version = {}

                # Skip "Actions" if requested. Everything else is output.
                if prop_name != 'Actions' or self.config.get('actions_in_property_table', True):
                    cp_gen.add_property_row(formatted['row'])
                if len(formatted['details']):
                    cp_gen.merge_prop_details(cp_gen.this_section['property_details'], formatted['details'])

                if formatted['action_details']:
                    cp_gen.add_action_details(formatted['action_details'])


        return cp_gen.emit()


    def generate_collections_doc(self):
        """ Generate output for collections. This is a table of CollectionName, URIs. """

        collections_uris = self.get_collections_uris()
        if not collections_uris:
            return ''

        doc = ""
        header = self.formatter.make_header_row([_('Collection Type'), _('URIs')])
        rows = []
        for collection_name, uris in sorted(collections_uris.items(), key=lambda x: x[0].lower()):
            item_text = self.format_uris_for_table(uris)
            rows.append(self.formatter.make_row([collection_name, item_text]))
        doc = self.formatter.make_table(rows, [header], 'uris', last_column_wide=True)

        return doc


    def get_collections_uris(self):
        """ Get just the collection names and URIs from property_data.

        Collections are identified by "Collection" in the normalized_uri. """
        data = {}
        collection_keys = sorted([x for x in self.property_data if 'Collection.' in x], key=str.lower)
        for x in collection_keys:
            [preamble, collection_file_name] = x.rsplit('/', 1)
            [collection_name, rest] = collection_file_name.split('.', 1)
            uris = sorted(self.property_data[x].get('uris', []), key=str.lower)
            data[collection_name] = uris
        return data


    def extend_property_info(self, schema_ref, prop_info):
        """If prop_info contains a $ref or anyOf attribute, extend it with that information.

        Returns an array of objects. Arrays of arrays of objects are possible but not expected.
        """
        traverser = self.traverser
        prop_ref = prop_info.get('$ref', None)
        prop_anyof = prop_info.get('anyOf', None)

        prop_infos = []
        outside_ref = None
        schema_name = traverser.get_schema_name(schema_ref)

        profile = prop_info.get('_profile', None)

        excerpt_copy_name = prop_info.get('excerptCopy')
        if excerpt_copy_name and excerpt_copy_name.endswith('Excerpt'): # It should.
            excerpt_copy_name = excerpt_copy_name[:-7]

        # Check for anyOf with a $ref to odata.4.0.0 idRef, and replace it with that ref.
        # Alternatively, if there is an excerptCopy property, use the (hopefully only) ref and expand it in place.
        if prop_anyof:
            for elt in prop_anyof:
                if '$ref' in elt:
                    this_ref = elt.get('$ref')

                    if excerpt_copy_name:
                        prop_ref = this_ref
                        break
                    elif this_ref.endswith('#/definitions/idRef'):
                        is_link = True
                        prop_ref = this_ref
                        prop_anyof = None
                        break

        if prop_ref:
            if prop_ref.startswith('#'):
                prop_ref = 'http://' + schema_ref + prop_ref
                # prop_ref = schema_ref + prop_ref
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
                warnings.warn('Unable to find data for %(reference)s' % {'reference': prop_ref})

            else:
                # Update version info from the ref, provided that it is within the same schema.
                # Make the comparison by unversioned ref, in respect of the way common_properties are keyed
                from_schema_ref = ref_info.get('_from_schema_ref')
                from_schema_uri, _discard, _discard = ref_info.get('_ref_uri', '').partition('#')
                unversioned_schema_ref = DocGenUtilities.make_unversioned_ref(from_schema_ref)
                requested_ref_uri = ref_info['_ref_uri']
                is_other_schema = from_schema_ref and not ((schema_ref == from_schema_ref)
                                                               or (schema_ref == unversioned_schema_ref))

                node_name = traverser.get_node_from_ref(prop_ref)

                is_documented_schema = self.is_documented_schema(from_schema_ref)
                is_collection_of = traverser.is_collection_of(from_schema_ref)
                prop_name = ref_info.get('_prop_name', False)
                is_ref_to_same_schema = ((not is_other_schema) and prop_name == schema_name)
                reference_disposition = self.config.get('reference_disposition') and self.config['reference_disposition'].get(prop_ref)
                include_per_profile = profile is not None

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
                ref_info = self.apply_overrides(ref_info)

                if ref_info.get('type') == 'object':
                    combine_multiple_count_met = self.config.get('combine_multiple_refs') and self.ref_counts.get(schema_ref, {}).get(requested_ref_uri, 0) >= self.config['combine_multiple_refs']
                    # If this is an excerpt, it will also be an object, and we want to expand-in-place.
                    # The same applies (or should) if config explicitly says to include:
                    if (excerpt_copy_name and not combine_multiple_count_met) or (reference_disposition == 'include') or include_per_profile:
                        if is_documented_schema:
                            excerpt_link = self.link_to_own_schema(from_schema_ref, from_schema_uri)
                        else: # This is not expected.
                            excerpt_link = self.link_to_outside_schema(from_schema_uri)
                        if excerpt_copy_name:
                            ref_info['_is_excerpt'] = True
                            ref_info['add_link_text'] = (_('This object is an excerpt of the %(link)s resource located at the URI shown in DataSourceUri.')
                                                             % {'link': excerpt_link})

                    elif combine_multiple_count_met:
                        if excerpt_copy_name:
                            if is_documented_schema:
                                excerpt_link = self.link_to_own_schema(from_schema_ref, from_schema_uri)
                            else: # This is not expected.
                                excerpt_link = self.link_to_outside_schema(from_schema_uri)
                            ref_info['_excerpt_link_text'] = (_('This object is an excerpt of the %(link)s resource located at the URI shown in DataSourceUri.')
                                                             % {'link': excerpt_link})
                        anchor = schema_ref + '|details|' + prop_name
                        ref_info['add_link_text'] = (_('For more information about this property, see %(link)s in Property Details.')
                                                         % {'link': self.link_to_anchor(prop_name, anchor)})
                        ref_info['_ref_description'] = ref_info['description']
                        ref_info['_ref_longDescription'] = ref_info['longDescription']

                    # If an object, include just the definition and description, and append a reference if possible:
                    else:
                        wants_common_objects = self.config.get('wants_common_objects')
                        ref_description = ref_info.get('description')
                        ref_longDescription = ref_info.get('longDescription')
                        ref_translation = ref_info.get('translation')
                        ref_fulldescription_override = ref_info.get('fulldescription_override')
                        ref_pattern = ref_info.get('pattern')
                        link_detail = ''
                        append_ref = ''

                        # Links to other Redfish resources are a special case.
                        if is_other_schema or is_ref_to_same_schema or reference_disposition == 'common_object':
                            if is_collection_of:
                                append_ref = _('Contains a link to a resource.')
                                ref_schema_name = self.traverser.get_schema_name(is_collection_of)

                                if 'redfish.dmtf.org/schemas/v1/odata' in from_schema_uri:
                                    from_schema_uri = 'http://' + is_collection_of

                                link_detail = (_('Link to Collection of %(schema_links)s. See the %(schema_name)s schema for details.')
                                                   % {'schema_links': self.link_to_own_schema(is_collection_of, from_schema_uri),
                                                          'schema_name': ref_schema_name})

                            else:
                                if is_ref_to_same_schema:
                                    # e.g., a Chassis is contained by another Chassis
                                    link_detail = _('Link to another %(name)s resource.') % {'name': prop_name}

                                elif is_documented_schema and reference_disposition != 'common_object':
                                    link_detail = (_('Link to a %(name)s resource. See the Links section and the %(schema_link)s schema for details.') %
                                                    {'name': prop_name,
                                                     'schema_link': self.link_to_own_schema(from_schema_ref, from_schema_uri)})
                                if not is_ref_to_same_schema and reference_disposition != 'include':
                                    if (reference_disposition != 'common_object') and (is_documented_schema or not wants_common_objects):
                                        append_ref = (_('See the %(schema_link)s schema for details on this property.')
                                                          % {'schema_link': self.link_to_own_schema(from_schema_ref, from_schema_uri)})
                                    else:
                                        # This looks like a Common Object! We should have an unversioned ref for this.
                                        ref_key = DocGenUtilities.make_unversioned_ref(ref_info['_ref_uri'])

                                        if ref_key:
                                            parent_info = traverser.find_ref_data(ref_key)
                                            if parent_info:
                                                ref_info = self.apply_overrides(parent_info)
                                        else:
                                            ref_key = ref_info['_ref_uri']

                                        if self.common_properties.get(ref_key) is None:
                                            self.common_properties[ref_key] = ref_info

                                        if not self.skip_schema(ref_info.get('_prop_name')):
                                            specific_version = DocGenUtilities.get_ref_version(requested_ref_uri)
                                            if 'type' not in ref_info:
                                                # This clause papers over a bug; somehow we never get to the bottom
                                                # of IPv6GatewayStaticAddress.
                                                ref_info['type'] = 'object'
                                            if specific_version:
                                                append_ref = (_('For property details, see %(schema_link)s v%(version_number)s).') %
                                                                 {'schema_link': self.link_to_common_property(ref_key),
                                                                      'version_number': str(specific_version)})
                                            else:
                                                append_ref = (_('For property details, see %(schema_link)s.') % {'schema_link': self.link_to_common_property(ref_key)})


                            new_ref_info = {
                                'description': ref_description,
                                'longDescription': ref_longDescription,
                                'fulldescription_override': ref_fulldescription_override,
                                'pattern': ref_pattern,
                                '_ref_description': ref_description,
                                '_ref_longDescription': ref_longDescription
                                }

                            if ref_translation: # Don't even set this parameter if it's null/empty.
                                new_ref_info['translation'] = ref_translation
                                new_ref_info['_ref_translation'] = ref_translation

                            props_to_add = ['_prop_name', '_from_schema_ref', '_schema_name', 'type', 'readonly', '_ref_description', '_ref_longDescription', '_ref_translation']
                            for x in props_to_add:
                                if ref_info.get(x):
                                    new_ref_info[x] = ref_info[x]

                            if not ref_fulldescription_override:
                                new_ref_info['add_link_text'] = append_ref

                            if link_detail:
                                link_props = {'type': 'string',
                                              'readonly': prop_info.get('readonly', True),
                                              'description': '',
                                              }
                                if not ref_fulldescription_override:
                                    link_props['add_link_text'] = link_detail
                                new_ref_info['properties'] = {'@odata.id': link_props}

                            ref_info = new_ref_info

                # if parent_props were specified in prop_info, they take precedence:
                for x in prop_info.keys():
                    if x in self.parent_props and prop_info[x]:
                        ref_info[x] = prop_info[x]

                # If we're getting prop-level version information from the $ref, use it only if the $ref
                # is in the same schema:
                if is_other_schema:
                    for x in ['versionAdded', 'versionDeprecated', 'deprecated',
                                  'enumVersionAdded', 'enumVersionDeprecated', 'enumDeprecated']:
                        if ref_info.get(x) and not prop_info.get(x):
                            del ref_info[x]

                # Pull in any "require" from parent:
                parent_requires = prop_info.get('parent_requires', [])
                parent_requires_on_create = prop_info.get('parent_requires_on_create', [])
                ref_info['prop_required'] = ref_info.get('prop_required') or prop_name in parent_requires or prop_info.get('requiredParameter')
                ref_info['prop_required_on_create'] = ref_info.get('prop_required_on_create') or prop_name in parent_requires_on_create
                ref_info['required_parameter'] = prop_info.get('requiredParameter')

                prop_info = ref_info

                # Annotate required properties.
                props = prop_info.get('properties')
                if (props):
                    required = prop_info.get('required', [])
                    required_on_create = prop_info.get('requiredOnCreate', [])
                    for x in props.keys():
                        props[x]['prop_required'] = props[x].get('prop_required') or x in required
                        props[x]['prop_required_on_create'] = props[x].get('prop_required_on_create') or x in required_on_create
                        props[x]['parent_requires'] = required
                        props[x]['parent_requires_on_create'] = required_on_create
                        props[x]['required_parameter'] = props[x].get('requiredParameter')

                if '$ref' in prop_info or 'anyOf' in prop_info:
                    return self.extend_property_info(schema_ref, prop_info)

            prop_infos.append(prop_info)

        elif prop_anyof:
            skip_null = len([x for x in prop_anyof if '$ref' in x])
            sans_null = [x for x in prop_anyof if x.get('type') != 'null']
            is_nullable = skip_null and [x for x in prop_anyof if x.get('type') == 'null']

            # This is a special case for references to multiple versions of the same object.
            # Get the most recent version, and make it the prop_ref.
            # The expected result is that these show up as referenced objects.
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
                    # Replace the anyof with a ref to the latest version:
                    prop_ref = refs_by_version[latest_version]
                    prop_anyof = [ {
                        '$ref': prop_ref
                        }]

            for elt in prop_anyof:
                if skip_null and (elt.get('type') == 'null'):
                    continue
                if '$ref' in elt:
                    for x in prop_info.keys():
                        if x in self.parent_props:
                            elt[x] = prop_info[x]
                elt = self.extend_property_info(schema_ref, elt)
                prop_infos.extend(elt)

            # If this is a nullable property (based on {type: 'null'} object AnyOf), add 'null' to the type.
            if is_nullable:
                prop_infos[0]['nullable'] = True
                if prop_infos[0].get('type'):
                    prop_infos[0]['type'] = [prop_infos[0]['type'], 'null']
                else:
                    prop_infos[0]['type'] = 'null'

        else:
            prop_infos.append(prop_info)

        return prop_infos


    def organize_prop_names(self, prop_names):
        """ Strip out excluded property names, sorting the remainder """

        prop_names = self.exclude_prop_names(prop_names, self.config['excluded_properties'],
                                       self.config['excluded_by_match'])
        prop_names.sort(key=str.lower)
        return prop_names


    def filter_props_by_subset(self, prop_names, subset):

        if subset is None:
            warnings.warn("filter_props_by_subset was called with no subset data")
            return prop_names

        # Actions have Parameters, properties have Properties.
        subsection = 'Properties'
        if 'Parameters' in subset:
            subsection = 'Parameters'

        filtered_names = []
        if subset.get('Baseline') or subset.get('Include') or subset.get('Version'):
            filtered_names = [x for x in prop_names]
            for name, instrs in subset.get(subsection, {}).items():
                if not instrs.get('Include', True):
                    if name in filtered_names:
                        filtered_names.remove(name)
        else:
            for name, instrs in subset.get(subsection, {}).items():
                if instrs.get('Include', True) and name not in filtered_names:
                    filtered_names.append(name)

        return filtered_names


    def filter_props_by_profile(self, prop_names, profile, schema_requires, is_action=False):

        if profile is None:
            warnings.warn("filter_props_by_profile was called with no profile data")
            return prop_names

        if profile.get('PropertyRequirements') is None and not is_action:
            # if a resource is specified with no PropertyRequirements, include them all...
            # but do omit "Actions" if there are no ActionRequirements (profile mode).
            if profile.get('ActionRequirements') and len(profile['ActionRequirements']):
                return prop_names
            else:
                return [x for x in prop_names if x != 'Actions']

        if self.config.get('profile_mode') == 'terse':
            if is_action:
                profile_props = [x for x in profile.keys()]
            else:
                profile_props = [x for x in profile.get('PropertyRequirements', {}).keys()]
            for x in schema_requires:
                if x not in profile_props:
                    profile_props.append(x)

            if profile.get('ActionRequirements'):
                profile_props.append('Actions')

            if is_action:
                # Action properties typically start with "#SchemaName.", which is not reflected in the profile:
                filtered = []
                for prop in profile_props:
                    if prop in prop_names or prop in schema_requires:
                        filtered.append(prop)
                    else:
                        matches = [x for x in prop_names if x.endswith('.' + prop)]
                        if matches:
                            filtered.append(matches[0])
                prop_names = filtered
            else:
                prop_names = list(set(prop_names) & set(profile_props))

        prop_names.sort(key=str.lower)
        return prop_names


    def exclude_annotations(self, prop_names):
        """ Strip out excluded annotations, sorting the remainder """

        return self.exclude_prop_names(prop_names, self.config.get('excluded_annotations', []),
                                       self.config.get('excluded_annotations_by_match', []))


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

        included_prop_names.sort(key=str.lower)
        return included_prop_names


    def skip_schema(self, schema_name):
        """ True if this schema should be skipped in the output """

        if self.config.get('profile_mode'):
            if schema_name in self.config.get('profile', {}).get('Resources', {}):
                return False

        if self.config.get('subset_mode'):
            if schema_name not in self.config.get('subset_resources').keys():
                return True

        if schema_name in self.config.get('excluded_schemas', []):
            return True
        for pattern in self.config.get('excluded_schemas_by_match', []):
            if pattern in schema_name:
                return True
        return False


    def parse_property_info(self, schema_ref, prop_name, prop_infos, prop_path):
        """Parse a list of one more more property info objects into strings for display.

        Returns a dict of 'prop_type', 'read_only', 'descr', 'prop_is_object',
        'prop_is_array', 'object_description', 'prop_details', 'item_description',
        'has_direct_prop_details', 'has_action_details', 'action_details', 'nullable',
        'is_in_profile', 'profile_read_req', 'profile_write_req', 'profile_mincount', 'profile_purpose',
        'profile_conditional_req', 'profile_conditional_details', 'profile_values', 'profile_comparison',
        'pattern', 'prop_required', 'prop_required_on_create', 'required_parameter'
        """
        within_action = prop_path == ['Actions']

        if isinstance(prop_infos, dict):
            return self._parse_single_property_info(schema_ref, prop_name, prop_infos, prop_path)

        if len(prop_infos) == 1:
            prop_info = prop_infos[0]
            if isinstance(prop_info, dict):
                return self._parse_single_property_info(schema_ref, prop_name, prop_info, prop_path)
            else:
                return self.parse_property_info(schema_ref, prop_name, prop_info, prop_path)

        parsed = {
                  'prop_type': [],
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
                  'pattern': [],
                  'prop_required': False,
                  'prop_required_on_create': False,
                  'required_parameter': False,
                  'is_in_profile': False,
                  'profile_read_req': None,
                  'profile_write_req': None,
                  'profile_mincount': None,
                  'profile_purpose': None,
                  'profile_conditional_req': None,
                  'profile_conditional_details': None,
                  'profile_values': None,
                  'profile_comparison': None
                 }

        profile = fallback_profile = None
        # Skip profile data if prop_name is blank -- this is just an additional row of info and
        # the "parent" row will have the profile info.
        if self.config.get('profile_mode') and prop_name:
            profile_section = 'PropertyRequirements'
            if within_action:
                profile_section = 'ActionRequirements'
            path_to_prop = prop_path.copy()
            path_to_prop.append(prop_name)
            fallback_profile = self.get_prop_profile(schema_ref, path_to_prop, profile_section)

        if self.config.get(subset_mode) and prop_name:
           subset_section = 'Properties'
           if within_action:
               subset_section = 'Actions'
           path_to_prop = prop_path.copy()
           path_to_prop.append(prop_name)
           schema_name = traverser.get_schema_name(schema_ref)
           fallback_subset = self.get_prop_subset(path_to_prop, subset_section)

        anyof_details = [self.parse_property_info(schema_ref, prop_name, x, prop_path)
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
        props_to_combine = ['prop_type', 'descr', 'object_description', 'item_description', 'pattern']

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

        # Restore the pattern to a single string:
        parsed['pattern'] = '\n'.join(parsed['pattern'])

        # read_only and units should be the same for all
        parsed['read_only'] = details[0]['read_only']
        parsed['prop_units'] = details[0]['prop_units']
        parsed['prop_required'] = details[0]['prop_required']
        parsed['prop_required_on_create'] = details[0]['prop_required_on_create']
        parsed['required_parameter'] = details[0].get('requiredParameter') == True

        if '_profile' in parsed:
            profile = parsed['_profile']
        else:
            profile = fallback_profile

        if '_subset' in parsed:
            subset = parsed['_subset']
        else:
            subset = fallback_subset

        if profile is not None:
            parsed['is_in_profile'] = True
            parsed['profile_read_req'] = profile.get('ReadRequirement', 'Mandatory')
            parsed['profile_write_req'] = profile.get('WriteRequirement')
            parsed['profile_mincount'] = profile.get('MinCount')
            parsed['profile_purpose'] = profile.get('Purpose')
            parsed['profile_conditional_req'] = profile.get('ConditionalRequirements')
            profile_values = profile.get('Values')
            if profile_values:
                profile_comparison = profile.get('Comparison', 'AnyOf') # Default if Comparison absent
                parsed['profile_values'] = profile_values
                parsed['profile_comparison'] = profile_comparison

            for det in details:
                parsed['prop_is_object'] |= det['prop_is_object']
                parsed['prop_is_array'] |= det['prop_is_array']
                parsed['has_direct_prop_details'] |= det['has_direct_prop_details']
                self.merge_property_details(parsed['prop_details'], det['prop_details'])
                parsed['has_action_details'] |= det['has_action_details']
                parsed['action_details'].update(det['action_details'])
                parsed['profile_conditional_details'].update(det['profile_conditional_details'])

        return parsed


    def _parse_single_property_info(self, schema_ref, prop_name, prop_info, prop_path):
        """Parse definition of a specific property into strings for display.

        Returns a dict of 'prop_type', 'prop_units', 'read_only', 'descr', 'add_link_text',
        'prop_is_object', 'prop_is_array', 'object_description', 'prop_details', 'item_description',
        'has_direct_prop_details', 'has_action_details', 'action_details', 'nullable',
        'is_in_profile', 'profile_read_req', 'profile_write_req', 'profile_mincount', 'profile_purpose',
        'profile_conditional_req', 'profile_conditional_details', 'profile_values', 'profile_comparison',
        'normative_descr', 'non_normative_descr', 'pattern', 'prop_required', 'prop_required_on_create',
        'required_parameter', 'verbatim_description'
        """
        traverser = self.traverser

        within_action = prop_path == ['Actions']

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
        profile_values = False
        profile_comparison = False
        verbatim_description = prop_info.get('verbatim_description', False)
        schema_name = traverser.get_schema_name(schema_ref)

        # Get the profile if we are in profile mode.
        # Skip profile data if prop_name is blank -- this is just an additional row of info and
        # the "parent" row will have the profile info.
        profile = None
        if '_profile' in prop_info:
            profile = prop_info['_profile']
        elif self.config.get('profile_mode') and prop_name:
            prop_brief_name = prop_name
            profile_section = 'PropertyRequirements'
            if within_action:
                profile_section = 'ActionRequirements'
                if prop_name.startswith('#'): # expected
                    prop_name_parts = prop_name.split('.')
                    prop_brief_name = prop_name_parts[-1]
            path_to_prop = prop_path.copy()
            if not prop_info.get('_in_items'):
                path_to_prop.append(prop_brief_name)
            profile = self.get_prop_profile(schema_ref, path_to_prop, profile_section)

        # Get the subset spec if we're in subset mode. Similar to above.
        subset = None
        if '_subset' in prop_info:
            subset = prop_info['_subset']
        elif self.config.get('subset_mode') and prop_name:
            subset_section = 'Properties'
            if within_action or (len(prop_path) and prop_path[0] == 'Actions'):
                subset_section = 'Actions'
            path_to_prop = prop_path.copy()
            if not prop_info.get('_in_items'):
                path_to_prop.append(prop_name)
            subset = self.get_prop_subset(path_to_prop, subset_section)

        # Some special treatment is required for Actions
        is_action = prop_name == 'Actions'
        if within_action:
            has_prop_actions = True

        # Only objects within Actions have parameters
        action_parameters = prop_info.get('parameters', {})
        has_action_parameters = len(action_parameters) > 0


        prop_info = self.apply_overrides(prop_info, schema_name, prop_name)

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
        if subset and subset.get('readonly'):
            read_only = True

        prop_required = prop_info.get('prop_required') or prop_name in prop_info.get('parent_requires', [])
        prop_required_on_create = prop_info.get('prop_required_on_create') or prop_name in prop_info.get('parent_requires_on_create', [])
        required_parameter = prop_info.get('requiredParameter')

        descr = self.get_property_description(prop_info)
        fulldescription_override = prop_info.get('fulldescription_override')

        required = prop_info.get('required', [])
        required_on_create = prop_info.get('requiredOnCreate', [])


        add_link_text = prop_info.get('add_link_text', '')

        if within_action:

            # Get the ActionName part of #SchemaName.ActionName. Example: from #Bios.ResetBios, we want "ResetBios"
            short_name = prop_name
            if prop_name.startswith('#'): # expected
                prop_name_parts = prop_name.split('.')
                short_name = prop_name_parts[-1]

            # Extend and parse parameter info
            for action_param in action_parameters.keys():
                params = action_parameters[action_param].copy()
                if subset:
                    param_subset = subset.get('Parameters', {}).get(action_param)
                    params['_subset'] = param_subset
                params = self.extend_property_info(schema_ref, params)
                action_parameters[action_param] = params

            supplemental_details = None
            supplemental = self.get_supplemental_details(schema_ref)
            if supplemental:
                supplemental_details = supplemental.get('action_details', {}).get(short_name)

            version_strings = self.format_version_strings(prop_info)
            action_details = self.format_action_parameters(schema_ref, prop_name, descr,
                                                               action_parameters, profile, version_strings,
                                                               supplemental_details, subset)

            # Provisional inserts. These need to go in a different place depending on layout.
            action_response_formatted = ''
            request_payload = ''
            response_payload = ''
            example_payload = ''
            has_action_response = False;

            if prop_info.get('actionResponse'):
                has_action_response = True;
                action_response = prop_info['actionResponse']
                action_response_extended = self.extend_property_info(schema_ref, action_response)
                action_response_formatted = self.format_action_response(schema_ref, prop_name, action_response_extended[0])
                action_details += action_response_formatted
                action_details += "\n" # Solves a problem for markdown output.

            if self.config.get('payloads'):
                version = self.get_latest_version(prop_info.get('_from_schema_ref'))

                # Insert action request payload, if present.
                payload_key = DocGenUtilities.get_payload_name(prop_info['_schema_name'], version, short_name, 'request-example')
                payload = self.config['payloads'].get(payload_key)
                if payload:
                    json_payload = payload
                    heading = self.formatter.para(self.formatter.bold(_("Request Example")))
                    request_payload = heading + self.format_json_payload(json_payload)
                else:
                    if self.config.get('warn_missing_payloads') and has_action_parameters: # has parameters
                        warnings.warn("MISSING JSON PAYLOAD FOR ACTION REQUEST for '%(schema_name)s : %(action_name)s'" %
                                          {'schema_name': schema_name, 'action_name': short_name})


                # Insert action response payload, if present.
                payload_key = DocGenUtilities.get_payload_name(prop_info['_schema_name'], version, short_name, 'response-example')
                payload = self.config['payloads'].get(payload_key)
                if payload:
                    json_payload = payload
                    heading = self.formatter.para(self.formatter.bold(_("Response Example")))
                    response_payload = heading + self.format_json_payload(json_payload)
                else:
                    if self.config.get('warn_missing_payloads') and has_action_response:
                        warnings.warn("MISSING JSON PAYLOAD FOR ACTION RESPONSE for '%(schema_name)s : %(action_name)s'" %
                                          {'schema_name': schema_name, 'action_name': short_name})

                # Old-style action payloads: this allowed for just one payload (response, presumably) per action
                payload_key = DocGenUtilities.get_payload_name(prop_info['_schema_name'], version, short_name)
                payload = self.config['payloads'].get(payload_key)
                if payload:
                    json_payload = payload
                    heading = self.formatter.para(self.formatter.bold(_("Example")))
                    example_payload = heading + self.format_json_payload(json_payload) + action_details

            if request_payload or response_payload or example_payload:
                # to put layouts at the "top," we need to slice off the heading and slip these in.
                if self.layout_payloads == 'top':
                    action_heading, action_details_body = action_details.split("\n", 1)
                    action_details = ''.join([action_heading, "\n", request_payload,
                                             response_payload, example_payload, action_details_body])
                else:
                    action_details += ''.join([request_payload, response_payload, example_payload])


            formatted_action_rows = []

            for param_name in action_parameters:
                if prop_name.startswith('#'):
                    [skip, action_name] = prop_name.rsplit('.', 1)
                else:
                    action_name = prop_name

                new_path = prop_path.copy()
                new_path.append(action_name)
                formatted_action = self.format_property_row(schema_ref, param_name, action_parameters[param_name], new_path)

                # Capture the enum details and merge them into the ones for the overall properties:
                if formatted_action and formatted_action.get('details'):
                    has_prop_details = True
                    self.merge_prop_details(prop_details, formatted_action['details'])

            self.add_action_details(action_details)


        # Items, if present, will have a definition with either an object, a list of types,
        # or a $ref:
        prop_item = prop_info.get('items')
        list_of_objects = False
        list_of_simple_type = False # For references to simple types
        collapse_description = False
        promote_me = False # Special case to replace enclosing array with combined array/simple-type

        if isinstance(prop_item, dict):

            if '_profile' in prop_info:
                prop_item['_profile'] = prop_info['_profile'] # carry through the profile, if present.

            if 'type' in prop_item and 'properties' not in prop_item:
                prop_items = [prop_item]
                collapse_description = True
            else:
                # Pass "excerptCopy" along with the prop_item, if present:
                excerpt_copy_name = prop_info.get('excerptCopy')
                excerpt_Ref_uri = None
                if excerpt_copy_name:
                    if excerpt_copy_name.endswith('Excerpt'): # It should.
                        excerpt_copy_name = excerpt_copy_name[:-7]
                    prop_item['excerptCopy'] = excerpt_copy_name

                # Pass "readonly" along with the prop_item, if present:
                if 'readonly' in prop_info:
                    prop_item['readonly'] = prop_info['readonly']

                prop_items = self.extend_property_info(schema_ref, prop_item)

                if excerpt_copy_name:
                    excerpt_ref_uri = prop_items[0].get('_ref_uri')
                    excerpt_schema_ref = prop_items[0].get('_from_schema_ref')
                    add_link_text = prop_items[0].get('add_link_text', add_link_text)

                array_of_objects = True

                # Annotate the items so we know not to add a level to the property path
                # later. There's probably a more elegant way to address this than to annotate!
                for x in prop_items:
                    x['_in_items'] = True

                if len(prop_items) == 1:
                    if 'type' in prop_items[0] and 'properties' not in prop_items[0]:
                        list_of_simple_type = True

            list_of_objects = not list_of_simple_type

        # Enumerations go into Property Details
        prop_enum = prop_info.get('enum')
        supplemental_details = None

        supplemental = self.get_supplemental_details(schema_ref)
        if supplemental:
            supplemental_details = supplemental.get('property_details', {}).get(prop_name)

        if prop_enum or supplemental_details:
            has_prop_details = True

            if self.config.get('normative') and 'enumLongDescriptions' in prop_info:
                prop_enum_details = prop_info.get('enumLongDescriptions')
                for key in prop_enum_details:
                    if prop_info.get('enumDescriptions')[key] != prop_enum_details[key]:
                        prop_enum_details[key] = prop_info.get('enumDescriptions')[key] + '<ul><li>' + prop_enum_details[key] + '</li></ul>'
            else:
                prop_enum_details = prop_info.get('enumDescriptions')

            formatted_details = self.format_property_details(prop_name, prop_type, descr,
                                                                 prop_enum, prop_enum_details,
                                                                 supplemental_details,
                                                                 prop_info,
                                                                 profile=profile, subset=subset)
            prop_detail_key = prop_info.get('_ref_uri', '_inline')
            if prop_info.get('_in_items') and len(prop_path):
                # In items, the prop_path is expected to include the prop name at this point.
                details_path = prop_path[:-1]
            else:
                details_path = prop_path[:]
            if prop_name not in prop_details:
                prop_details[prop_name] = {}
            prop_details[prop_name][prop_detail_key] = {
                'paths': [details_path],
                'formatted_descr': formatted_details
                }

        # embedded object:
        if prop_is_object:
            new_path = prop_path.copy()
            new_path.append(prop_name)

            prop_info['parent_requires'] = required
            prop_info['parent_requires_on_create'] = required_on_create

            if self.config.get('combine_multiple_refs') and self.ref_counts.get(schema_ref, {}).get(prop_info.get('_ref_uri'), 0) >= self.config['combine_multiple_refs']:
                # Details of this object are to be moved into property details.
                # Format it as if it were a top-level object, and remove the rows here.
                object_formatted = self.format_object_descr(schema_ref, prop_info, [], is_action)
                obj_prop_name = prop_info.get('_prop_name')
                ref_description = prop_info.get('_ref_description')
                if prop_info.get('_excerpt_link_text'):
                    ref_description = ref_description + ' ' + prop_info['_excerpt_link_text']
                object_as_details = self.format_as_prop_details(obj_prop_name, ref_description,
                                                                    object_formatted['rows'])
                new_details = {obj_prop_name: {
                    prop_info.get('_ref_uri', '_inline'): {
                        'paths': [new_path],
                        'formatted_descr': object_as_details
                        }
                    }}
                self.merge_prop_details(prop_details, new_details)
                object_formatted['rows'] = []
            else:
                object_formatted = self.format_object_descr(schema_ref, prop_info, new_path, is_action)
                object_description = object_formatted['rows']
            if object_formatted['details']:
                self.merge_prop_details(prop_details, object_formatted['details'])

        # embedded items:
        if prop_is_array and (list_of_objects or list_of_simple_type or prop_item):
            new_path = prop_path.copy()
            new_path.append(prop_name)
            if list_of_objects:
                item_formatted = self.format_list_of_object_descrs(schema_ref, prop_items, new_path)
                if collapse_description:
                    # remember, we set collapse_description when we made prop_items a single-element list.
                    item_list = prop_items[0].get('type')

            elif list_of_simple_type:
                if self.collapse_list_of_simple_type:
                    # We want to combine the array and its item(s) into a single row. Create a combined
                    # prop_item to make it work.
                    combined_prop_item = prop_items[0]
                    combined_prop_item['_prop_name'] = prop_name
                    combined_prop_item['readonly'] = prop_info.get('readonly', False)
                    combined_prop_item['versionAdded'] = prop_info.get('versionAdded')
                    combined_prop_item['versionDeprecated'] = prop_info.get('versionDeprecated')
                    combined_prop_item['deprecated'] = prop_info.get('deprecated')
                    combined_prop_item['enumVersionAdded'] = prop_info.get('enumVersionAdded')
                    combined_prop_item['enumVersionDeprecated'] = prop_info.get('enumVersionDeprecated')
                    combined_prop_item['enumDeprecated'] = prop_info.get('enumDeprecated')
                    if self.config.get('normative'):
                        combined_prop_item['longDescription'] = descr
                    else:
                        combined_prop_item['description'] = descr
                    if fulldescription_override:
                        combined_prop_item['fulldescription_override'] = fulldescription_override

                    item_formatted = self.format_non_object_descr(schema_ref, combined_prop_item, new_path, True)

                else:
                    item_formatted = self.format_non_object_descr(schema_ref, prop_items[0], new_path)
                    item_formatted['promote_me'] = False

            elif prop_item:
                item_formatted = self.format_non_object_descr(schema_ref, prop_item, new_path)

            promote_me = item_formatted.get('promote_me', False)
            item_description = item_formatted['rows']
            if item_formatted['details']:
                self.merge_prop_details(prop_details, item_formatted['details'])

        # Read/Write requirements from profile:
        if self.config.get('profile_mode') and prop_name and profile is not None:

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
            # Comparison
            profile_values = profile.get('Values')
            if profile_values:
                profile_comparison = profile.get('Comparison', 'AnyOf') # Default if Comparison absent


        parsed_info = {'_prop_name': prop_name,
                       'prop_type': prop_type,
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
                       'promote_me': promote_me,
                       'normative_descr': prop_info.get('longDescription', ''),
                       'non_normative_descr': prop_info.get('description', ''),
                       'fulldescription_override': prop_info.get('fulldescription_override', False),
                       'prop_required': prop_required,
                       'prop_required_on_create': prop_required_on_create,
                       'required_parameter': required_parameter,
                       'pattern': prop_info.get('pattern'),
                       'is_in_profile': False,
                       'profile_read_req': None,
                       'profile_write_req': None,
                       'profile_mincount': None,
                       'profile_purpose': None,
                       'profile_conditional_req': None,
                       'profile_conditional_details': None,
                       'profile_values': None,
                       'profile_comparison': None,
                       'verbatim_description': verbatim_description,
                       }

        if profile is not None:
            parsed_info.update({
                'is_in_profile': True,
                'profile_read_req': profile.get('ReadRequirement', 'Mandatory'),
                'profile_write_req': profile.get('WriteRequirement'),
                'profile_mincount': profile.get('MinCount'),
                'profile_purpose': profile.get('Purpose'),
                'profile_conditional_req': profile_conditional_req,
                'profile_conditional_details': profile_conditional_details,
                'profile_values': profile_values,
                'profile_comparison': profile_comparison,
                })

        return parsed_info


    def process_for_idRef(self, ref):
        """Convenience method to check ref for 'odata.4.0.0#/definitions/idRef' and if so, return its property info.

        We special-case this a couple of places where we treat other refs a little differently. """
        prop_info = None
        if ref.endswith("#/definitions/idRef"):
            # idRef is a special case; we just want to pull in its definition and stop.
            prop_info = self.traverser.find_ref_data(ref)
            if not prop_info:
                # We must not have the odata schema, but we know what it is.
                prop_info = {'properties':
                             {'@odata.id':
                              {'type': 'string',
                               'readonly': True,
                               "description": _('The unique identifier for a resource.'),
                               "longDescription": _('The value of this property shall be the unique identifier for the resource and it shall be of the form defined in the Redfish specification.'),
                               }
                              }
                             }
        return prop_info


    def get_property_description(self, prop_info):
        """ Get the right description to output, based on prop data and config """
        descr = None
        if self.config.get('profile_mode') != 'terse':
            if self.config.get('normative') and 'longDescription' in prop_info:
                descr = prop_info.get('longDescription', '')
            else:
                descr = prop_info.get('description', '')

        normative_descr = prop_info.get('longDescription', '')
        non_normative_descr = prop_info.get('description', '')
        pattern = prop_info.get('pattern')

        if self.config.get('normative') and normative_descr and non_normative_descr != normative_descr:
            descr = non_normative_descr + '<ul><li>' + normative_descr + '</li></ul>'
        else:
            descr = non_normative_descr

        if self.config.get('normative') and pattern:
            descr = _('%(descr)s Pattern: %(pattern)s') % {'descr': descr, 'pattern': pattern}

        return descr


    def format_object_descr(self, schema_ref, prop_info, prop_path=[], is_action=False):
        """Format the properties for an embedded object."""

        properties = prop_info.get('properties')
        output = []
        details = {}
        action_details = {}
        conditional_details = {}

        # If prop_info was extracted from a different schema, it will be present as _from_schema_ref
        in_schema_ref = schema_ref
        schema_ref = prop_info.get('_from_schema_ref', schema_ref)
        in_schema_name = self.traverser.get_schema_name(in_schema_ref)

        required = prop_info.get('required', [])
        required_on_create = prop_info.get('requiredOnCreate', [])

        parent_requires = prop_info.get('parent_requires', [])
        parent_requires_on_create = prop_info.get('parent_requires_on_create', [])

        prop_names = patterns = profile = False
        if len(prop_path) and prop_path[0] == 'Actions':
            profile_section = 'ActionRequirements'
            subset_section = 'Actions'
        else:
            profile_section = 'PropertyRequirements'
            subset_section = 'Properties'

        subset = None

        if properties:

            prop_names = [x for x in properties.keys()]

            if self.config.get('profile_mode') == 'terse':

                if '_profile' in prop_info:
                    profile = prop_info['_profile']
                else:
                    profile = self.get_prop_profile(schema_ref, prop_path, profile_section)

                if profile:
                    prop_names = self.filter_props_by_profile(prop_names, profile, parent_requires, is_action)
                prop_names.sort(key=str.lower)

            elif self.config.get('subset_mode'):

                if '_subset' in prop_info:
                    subset = prop_info['_subset']
                elif len(prop_path):
                    subset = self.get_prop_subset(prop_path, subset_section)

                if subset:
                    prop_names = self.filter_props_by_subset(prop_names, subset)

            else:
                prop_names = self.exclude_annotations(prop_names)

                filtered_properties = {}
                for k in prop_names:
                    filtered_properties[k] = properties[k]
                prop_info['properties'] = properties = filtered_properties


            if is_action:
                prop_names = [x for x in prop_names if x.startswith('#')]

            for prop_name in prop_names:
                base_detail_info = properties[prop_name]
                base_detail_info['prop_required'] = base_detail_info.get('prop_required') or prop_name in parent_requires
                base_detail_info['prop_required_on_create'] = (base_detail_info.get('prop_required_on_create') or
                                                                   prop_name in parent_requires_on_create)
                base_detail_info = self.apply_overrides(base_detail_info, in_schema_name, prop_name)
                if profile:
                    base_detail_info['_profile'] = profile.get(profile_section, {}).get(prop_name)
                detail_info = self.extend_property_info(schema_ref, base_detail_info)

                if is_action:
                    # Trim out the properties; these are always Target and Title:
                    detail_info[0]['properties'] = {}

                new_path = prop_path.copy()

                formatted = self.format_property_row(schema_ref, prop_name, detail_info, new_path, in_schema_ref=in_schema_ref)
                if formatted:
                    output.append(formatted['row'])
                    if formatted['details']:
                        self.merge_prop_details(details, formatted['details'])
                    if formatted['action_details']:
                        action_details[prop_name] = formatted['action_details']
                    if formatted.get('profile_conditional_details'):
                        conditional_details.update(formatted['profile_conditional_details'])

        elif prop_info.get('patternProperties') and (self.config.get('output_content') != 'property_index'):
            # If this is an action parameter, don't list the pattern here (we'll catch it in action details):
            if not ('Actions' in prop_path and len(prop_path) > prop_path.index('Actions') + 1):
                patterns = prop_info['patternProperties'].keys()
                patterns_to_include = self.exclude_prop_names(patterns, self.config['excluded_pattern_props'], [])

                for pattern in patterns_to_include:
                    prop_name = '(pattern)'
                    base_pattern_info = prop_info['patternProperties'][pattern]
                    base_pattern_info['prop_required'] = False
                    base_pattern_info['prop_required_on_create'] = False

                    base_pattern_info = self.apply_overrides(base_pattern_info, in_schema_name, None)

                    # Override the description, if any, with a line describing the pattern.
                    description = _('Property names follow regular expression pattern "%(pattern)s"') % {'pattern': self.escape_regexp(pattern)}
                    base_pattern_info['description'] = base_pattern_info['longDescription'] = description
                    base_pattern_info['verbatim_description'] = True

                    pattern_info = self.extend_property_info(schema_ref, base_pattern_info)

                    formatted = self.format_property_row(schema_ref, prop_name, pattern_info, prop_path, in_schema_ref=in_schema_ref)
                    if formatted:
                        output.append(formatted['row'])
                        if formatted['details']:
                            details.update(formatted['details'])
                        if formatted['action_details']:
                            action_details[prop_name] = formatted['action_details']
                        if formatted.get('profile_conditional_details'):
                            conditional_details.update(formatted['profile_conditional_details'])


        if len(conditional_details):
            cond_names = [x for x in conditional_details.keys()]
            cond_names.sort(key=str.lower)
            for cond_name in cond_names:
                self.add_profile_conditional_details(conditional_details[cond_name])

        return {'rows': output, 'details': details, 'action_details': action_details }


    def format_non_object_descr(self, schema_ref, prop_dict, prop_path=[], in_array=False):
        """For definitions that just list simple types without a 'properties' entry"""

        output = []
        details = {}
        action_details = {}

        prop_name = prop_dict.get('_prop_name', '')
        detail_info = self.extend_property_info(schema_ref, prop_dict)

        formatted = self.format_property_row(schema_ref, prop_name, detail_info, prop_path, in_array)

        if formatted:
            output.append(formatted['row'])
            details = formatted.get('details', {})
            action_details = formatted.get('action_details', {})

        return {'rows': output, 'details': details, 'action_details': action_details, 'promote_me': True}


    def format_as_prop_details(self, prop_name, prop_description, rows):
        """ Take the formatted rows and other strings from prop_info, and create a formatted block suitable for the prop_details section """
        raise NotImplementedError


    def link_to_own_schema(self, schema_ref, schema_full_uri):
        """ String for output. Override in HTML formatter to get actual links. """
        schema_name = self.traverser.get_schema_name(schema_ref)
        if schema_name:
            return schema_name
        return schema_ref

    def link_to_common_property(self, ref_key):
        """ String for output. Override in HTML formatter to get actual links. """
        ref_info = self.common_properties.get(ref_key)
        if ref_info and ref_info.get('_prop_name'):
            return ref_info.get('_prop_name')
        return ref_key

    def link_to_outside_schema(self, schema_full_uri):
        """ String for output. Override in HTML formatter to get actual links."""
        return schema_full_uri

    def link_to_anchor(self, text, anchor):
        """ Link to arbitrary same-page anchor. Default implementation does not link; override where links to fragments are supported. """
        return text

    def get_documentation_uri(self, ref_uri):
        """ If ref_uri is matched in self.config['schema_link_replacements'], provide a reference to that """

        if not self.uri_match_keys:
            return None

        replacement = None
        for key in self.uri_match_keys:
            if key in ref_uri:
                match_spec = self.config['schema_link_replacements'][key]
                if match_spec.get('full_match') and match_spec['full_match'] == ref_uri:
                    preplacement = match_spec.get('replace_with')
                    return replacement
                elif not match_spec.get('full_match'):
                    replacement = match_spec.get('replace_with')
                    return replacement

        return replacement

    def count_ref_in_schema(self, schema_ref, prop_info, ancestors=None):
        """ Examine prop_info for a reference and update the count in ref_deduplicator, if appropriate.
        Returns the _ref_uri from prop_info if so.
        """

        if ancestors is None:
            ancestors = []

        ref_uri = prop_info.get('_ref_uri', None)
        if not ref_uri:
            return None

        # Normalize ref_uri:
        ref_uri = 'http://' + '#'.join(self.traverser.get_schema_ref_and_path(ref_uri))

        if schema_ref not in self.ref_deduplicator:
            self.ref_deduplicator[schema_ref] = {}
        dedup = self.ref_deduplicator[schema_ref]

        for anc in ancestors:
            if anc not in dedup:
                dedup[anc] = {}
            dedup = dedup[anc]

        if ref_uri in dedup:
            dedup[ref_uri]['count'] = dedup[ref_uri].get('count') + 1
        else:
            dedup[ref_uri] = {'count': 1}

        return ref_uri


    def extend_and_count_refs(self, schema_ref, prop_infos, ancestors=None):
        """ Extend, but don't format, elements of prop_infos to update ref_deduplicator counts. """

        if ancestors is None:
            ancestors = []
        for prop_info in prop_infos:
            if isinstance(prop_info, dict):
                properties = prop_info.get('properties')
                if properties:
                    for prop_name in properties.keys():
                        if isinstance(properties.get(prop_name), dict):
                            base_detail_info = properties[prop_name]
                            detail_info = self.extend_property_info(prop_info.get('_from_schema_ref', schema_ref), base_detail_info)
                            ref_uri = self.count_ref_in_schema(schema_ref, detail_info[0], ancestors)
                            prop_ancestors = ancestors.copy()
                            if ref_uri:
                                prop_ancestors.append(ref_uri)
                            self.extend_and_count_refs(schema_ref, detail_info, prop_ancestors)

                elif prop_info.get('items') and (prop_info['items'].get('type') not in ['string', 'integer']):
                    if prop_info['items'].get('$ref') or prop_info['items'].get('anyOf'):
                        self.extend_and_count_refs(schema_ref, prop_info['items'], ancestors)


    def summarize_duplicates(self, count_data):
        """ Combine duplicate counts from self.ref_deduplicator. """

        summary = {}
        combine_threshold = self.config.get('combine_multiple_refs', 0)
        if combine_threshold < 2:
            return summary

        for (ref_uri, data) in count_data.items():
            if ref_uri == 'count':
                continue
            if data.get('count', 0) >= combine_threshold:
                summary[ref_uri] = data['count']
            else:
                summary.update(self.summarize_duplicates(data))
        return summary


    def merge_prop_details(self, prop_details, new_details):
        """ add new_details into prop_details, respecting the structure of prop_details. """
        for (key, det) in new_details.items():
            if key not in prop_details:
                prop_details[key] = det
            else:
                for ref in det:
                    if ref not in prop_details[key]:
                        prop_details[key][ref] = det[ref]
                    else:
                        if prop_details[key][ref]['formatted_descr'] != det[ref]['formatted_descr']:
                            warnings.warn('mismatch detected in descriptions for %(key)s in %(heading)s' % {'key': key, 'heading': self.this_section['head']})
                        for path in det[ref]['paths']:
                            prop_details[key][ref]['paths'].append(path)


    # Override in HTML formatter to get actual links.
    def get_documentation_link(self, ref_uri):
        """ Provide a string referring to ref_uri. """
        target = self.get_documentation_uri(ref_uri)
        if target:
            return "See " + target
        return False

    def is_documented_schema(self, schema_ref):
        """ True if the schema will appear as a section in the output documentation """
        return schema_ref in self.documented_schemas


    def get_ref_for_documented_schema_name(self, schema_name):
        """ Get the schema_ref for the schema_name, if it is a documented schema. """
        candidates = [x for x in self.documented_schemas if schema_name in x]
        for x in candidates:
            if self.property_data[x]['schema_name'] == schema_name:
                return x
        return False


    def apply_overrides(self, prop_info, schema_name=None, prop_name=None):
        """ Apply overrides from config to prop_info. Returns a modified copy of prop_info. """

        prop_info = copy.deepcopy(prop_info)

        if not schema_name:
            schema_name = prop_info.get('_schema_name')

        if not prop_name:
            prop_name = prop_info.get('_prop_name')

        local_overrides = self.config.get('schema_supplement', {}).get(schema_name, {}).get('property_description_overrides', {})
        local_full_overrides = self.config.get('schema_supplement', {}).get(schema_name, {}).get('property_fulldescription_overrides', {})
        prop_info['fulldescription_override'] = False

        if (prop_name in local_overrides) or (prop_name in local_full_overrides):
            if prop_name in local_overrides:
                prop_info['description'] = prop_info['longDescription'] = local_overrides[prop_name]
            if prop_name in local_full_overrides:
                prop_info['description'] = prop_info['longDescription'] = local_full_overrides[prop_name]
                prop_info['fulldescription_override'] = True
            return prop_info

        if prop_name in self.config.get('property_description_overrides', {}):
            prop_info['description'] = prop_info['longDescription'] = self.config['property_description_overrides'][prop_name]

        if prop_name in self.config.get('property_fulldescription_overrides', {}):
            prop_info['description'] = prop_info['longDescription'] = self.config['property_fulldescription_overrides'][prop_name]
            prop_info['fulldescription_override'] = True

        units_trans = self.config.get('units_translation', {}).get(prop_info.get('units'))
        if units_trans:
            prop_info['units'] = units_trans

        return prop_info


    def get_prop_profile(self, schema_ref, prop_path, section):
        """Get profile data for the specified property, by schema_ref, prop name path, and section.

        Section is 'PropertyRequirements' or 'ActionRequirements'.
        Returns None if no data is present ({} is a valid data-present result)."""

        prop_profile = None
        if prop_path[0] == 'Actions':
            section = 'ActionRequirements'

        if self.config.get('profile_resources'):
            prop_profile = self.config['profile_resources'].get(schema_ref, None)
            if prop_profile is None:
                return None

            if section == 'ActionRequirements':
                if prop_path[0] == 'Actions':
                    prop_path = prop_path[1:]

            prop_reqs = prop_profile.get(section, None)
            if prop_reqs == None:
                return None
            prop_profile = prop_reqs

            for prop_name in prop_path:
                if not prop_name:
                    continue
                prop_profile = prop_reqs.get(prop_name, None)
                if prop_profile is None:
                    return None
                prop_reqs = prop_profile.get('PropertyRequirements', prop_profile.get('Parameters', {}))

        return prop_profile


    def get_prop_subset(self, prop_path, section):
        """Get subset data for the specified property.
        This will be in the context of the current documented section's
        schema.

        Section is "Properties" or "Actions".
        """

        schema_name = self.this_section['schema_name']
        prop_subset = None
        subset = self.config.get('subset_resources', {}).get(schema_name)

        if subset:
            prop_subset = {}
            prop_subset['Baseline'] = subset.get('Baseline', False)
            prop_subset['Version'] = subset.get('Version', False)

            if section == 'Actions':
                subsection = 'Parameters'
                if prop_path[0] == 'Actions':
                    prop_path = prop_path[1:]
            else:
                subsection = 'Properties'

            subset = subset.get(section, {}) # 'Properties' or 'Actions'
            first = True
            for prop_name in prop_path:
                if not prop_name:
                    continue
                if not first:
                    subset = subset.get(subsection, {}) # 'Properties' or 'Parameters'
                subset = subset.get(prop_name, {})
                first = False

        if subset:
            # We generally want to return a subset that has a top-level "subsection" key,
            # except when we've drilled down to enum "SupportedValues."
            if subsection in subset or 'SupportedValues' in subset:
                subset['Baseline'] = prop_subset['Baseline']
                prop_subset = subset
            else:
                prop_subset[subsection] = subset

        return prop_subset



    def get_latest_version(self, schema_ref):
        """ Look up the latest version of the referenced schema in our property data """
        return  self.property_data.get(schema_ref, {}).get('latest_version')


    def get_supplemental_details(self, schema_ref):
        """ Look up supplemental details for this schema/version """
        supplemental = {}
        property_data = self.property_data.get(schema_ref)
        schema_supplement = self.config.get('schema_supplement')
        schema_md_supplement = self.config.get('md_supplements', {})
        if property_data:
            schema_name = property_data.get('schema_name')
            md_supp = schema_md_supplement.get(schema_name)

            if property_data and schema_supplement:
                version = property_data.get('latest_version', 1)
                major_version = version.split('.')[0]
                schema_key = schema_name + '_' + major_version
                supplemental = schema_supplement.get(schema_key,
                                                        schema_supplement.get(schema_name, {}))

            if md_supp:
                for key in ['description', 'jsonpayload', 'property_details', 'action_details']:
                    if md_supp.get(key) and key not in supplemental:
                        supplemental[key] = md_supp[key]

        return supplemental


    def add_object_close(self, rows, indentation_string, brace_string, num_cols):
        """ Modify rows with whatever we use to close an object in this format """
        row_content = [''] * num_cols
        row_content[0] = indentation_string + brace_string

        rows.append(self.formatter.make_row(row_content))
        return rows


    def escape_text(self, text, chars=None):
        """Escape text in whatever way is appropriate to this output format. Default is not to escape. """
        return text


    @staticmethod
    def format_version(version_string):
        """ version_string may be in the form "v1_5_0" or "1.5.0". We want the latter; this gives it to us. """
        if version_string.startswith('v'):
            version_string = version_string[1:]
        if '_' in version_string:
            version_string = version_string.replace('_', '.')
        return version_string


    @staticmethod
    def truncate_version(version_string, num_parts, with_prejudice=False):
        """Truncate the version string to at least the specified number of parts.

        Maintains additional part(s) if non-zero, unless with_prejudice is True
        """

        parts = version_string.split('.')
        keep = []
        for part in parts:
            if len(keep) < num_parts:
                keep.append(part)
            elif part != '0' and not with_prejudice:
                keep.append(part)
            else:
                break

        return '.'.join(keep)


    @staticmethod
    def text_map(text):
        """Replace string for output -- used to replace strings with natural language text"""

        output_map = {
            'IfImplemented': _('If Implemented'),
            'Conditional': _('Conditional Requirements'),
            'Mandatory': _('Mandatory'),
            'Recommended': _('Recommended'),
            }
        return output_map.get(text, text)

    @staticmethod
    def escape_regexp(text):
        """If escaping is necessary to protect patterns when output format is rendered, do that. """
        return text


    @staticmethod
    def summarize_release_history(release_history, versionDeprecated=False):
        """ Create a summary of the given release history, which is assumed to be ordered oldest-first:

        * last 6 entries by major/minor version
        * versions to major/minor only
        * ordered latest-to-earliest
        """
        max_entries = 10
        summarized = []
        all = copy.deepcopy(release_history)
        all.reverse()
        latest_release = ''
        num_releases = 0

        if versionDeprecated:
            versionDepr_cleaned = versionDeprecated.replace('_', '.')
            versionDepr_cleaned = versionDepr_cleaned[1:] # Remove leading 'v'

        for elt in all:
            if elt['release'] == latest_release:
                continue
            latest_release = elt['release']
            num_releases = num_releases + 1
            if len(summarized) <= max_entries:
                version = DocFormatter.truncate_version(elt['version'], 2, True)
                if versionDeprecated:
                    compare = DocGenUtilities.compare_versions(version, versionDepr_cleaned)
                    if compare >= 0:
                        version += ' ' + _('Deprecated')
                summarized.append({"version": "v" + version, "release": latest_release})
            else:
                summarized.append({"version": "...", "release": "..."})
                break

        return summarized
