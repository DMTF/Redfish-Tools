# Copyright Notice:
# Copyright 2016, 2017, 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File : markdown_generator.py

Brief : This file contains definitions for the MarkdownGenerator class.

Initial author: Second Rise LLC.
"""

import copy
import warnings
from doc_gen_util import DocGenUtilities
from . import DocFormatter
from format_utils import FormatUtils

# Format user warnings simply
def simple_warning_format(message, category, filename, lineno, file=None, line=None):
    """ a basic format for warnings from this program """
    return '  Warning: %s (%s:%s)' % (message, filename, lineno) + "\n"

warnings.formatwarning = simple_warning_format


class MarkdownGenerator(DocFormatter):
    """Provides methods for generating markdown from Redfish schemas.

    Markdown is targeted to the Slate documentation tool: https://github.com/lord/slate
    """


    def __init__(self, property_data, traverser, config, level=0):
        super(MarkdownGenerator, self).__init__(property_data, traverser, config, level)
        self.separators = {
            'inline': ', ',
            'linebreak': '\n',
            'pattern': ', '
            }
        self.formatter = FormatUtils()
        self.layout_payloads = 'top'


    def format_property_row(self, schema_ref, prop_name, prop_info, prop_path=[], in_array=False, as_action_parameters=False):
        """Format information for a single property.

        Returns an object with 'row', 'details', 'action_details', and 'profile_conditional_details':

        'row': content for the main table being generated.
        'details': content for the Property details section.
        'action_details': content for the Actions section.
        'profile_conditional_details': populated only in profile_mode, formatted conditional details

        This may include embedded objects with their own properties.
        """

        formatted = []     # The row itself

        within_action = prop_path == ['Actions']
        current_depth = len(prop_path)
        if in_array:
            current_depth = current_depth -1

        # strip_top_object is used for fragments, to allow output of just the properties
        # without the enclosing object:
        if self.config.get('strip_top_object') and current_depth > 0:
            indentation_string = '&nbsp;' * 6 * (current_depth -1)
        else:
            indentation_string = '&nbsp;' * 6 * current_depth

        # If prop_path starts with Actions and is more than 1 deep, we are outputting for an Actions
        # section and should dial back the indentation by one level.
        if len(prop_path) > 1 and prop_path[0] == 'Actions':
            indentation_string = '&nbsp;' * 6 * (current_depth -1)

        collapse_array = False # Should we collapse a list description into one row? For lists of simple types
        has_enum = False

        if current_depth < self.current_depth:
            for i in range(current_depth, self.current_depth):
                if i in self.current_version:
                    del self.current_version[i]
        self.current_depth = current_depth
        parent_depth = current_depth - 1

        if isinstance(prop_info, list):
            has_enum = 'enum' in prop_info[0]
            is_excerpt = prop_info[0].get('_is_excerpt') or prop_info[0].get('excerptCopy')
            prop_ref = prop_info[0].get('_ref_uri')
            ref_name = prop_info[0].get('_prop_name')
        elif isinstance(prop_info, dict):
            has_enum = 'enum' in prop_info
            is_excerpt = prop_info.get('_is_excerpt')
            prop_ref = prop_info.get('_ref_uri')
            ref_name = prop_info.get('_prop_name')

        version_strings = self.format_version_strings(prop_info)
        if prop_name:
            name_and_version = self.formatter.bold(self.escape_for_markdown(prop_name,
                                                                  self.config.get('escape_chars', [])))
        else:
            name_and_version = ''

        if version_strings['version_string']:
            name_and_version += ' ' + self.formatter.italic(version_strings['version_string'])
        deprecated_descr = version_strings['deprecated_descr']

        formatted_details = self.parse_property_info(schema_ref, prop_name, prop_info, prop_path)

        if formatted_details.get('promote_me'):
            return({'row': '\n'.join(formatted_details['item_description']), 'details':formatted_details['prop_details'],
                    'action_details':formatted_details.get('action_details')})

        if self.config.get('strip_top_object') and current_depth == 0:
            # In this case, we're done for this bit of documentation, and we just want the properties of this object.
            formatted.append('\n'.join(formatted_details['object_description']))
            return({'row': '\n'.join(formatted), 'details':formatted_details['prop_details'],
                    'action_details':formatted_details.get('action_details'),
                    'profile_conditional_details': formatted_details.get('profile_conditional_details')})


        # Eliminate dups in these these properties and join with a delimiter:
        props = {
            'prop_type': self.separators['inline'],
            'descr': self.separators['linebreak'],
            'object_description': self.separators['linebreak'],
            'item_description': self.separators['linebreak']
            }

        for property_name, delim in props.items():
            if isinstance(formatted_details[property_name], list):
                property_values = []
                self.append_unique_values(formatted_details[property_name], property_values)
                formatted_details[property_name] = delim.join(property_values)

        if formatted_details['prop_is_object'] and not in_array:
            if formatted_details['object_description'] == '':
                name_and_version += ' {}'
            else:
                name_and_version += ' {'

        if formatted_details['prop_is_array']:
            if formatted_details['item_description'] == '':
                if formatted_details['array_of_objects']:
                    name_and_version += ' [ {} ]'
                else:
                    name_and_version += ' [ ]'
            else:
                if formatted_details['array_of_objects']:
                    name_and_version += ' [ {'
                else:
                    collapse_array = True
                    name_and_version += ' [ ]'
        elif in_array:
            if formatted_details['prop_is_object']:
                name_and_version += ' [ { } ]'
            else:
                name_and_version += ' [ ]'

        if formatted_details['descr'] is None:
            formatted_details['descr'] = ''

        if formatted_details['profile_purpose'] and (self.config.get('profile_mode') != 'subset'):
            if formatted_details['descr']:
                formatted_details['descr'] += ' '
            formatted_details['descr'] += self.formatter.bold(formatted_details['profile_purpose'])

        if formatted_details['add_link_text']:
            if formatted_details['descr']:
                formatted_details['descr'] += ' '
            formatted_details['descr'] += formatted_details['add_link_text']

        # Append reference info to descriptions, if appropriate:
        if not formatted_details.get('fulldescription_override'):
            if formatted_details['has_direct_prop_details'] and not formatted_details['has_action_details']:
                # If there are prop_details (enum details), add a note to the description:
                if has_enum:
                    text_descr = 'For the possible property values, see ' + prop_name + ' in Property details.'
                else:
                    text_descr = 'For more information about this property, see Property details.'
                formatted_details['descr'] += ' ' + self.formatter.italic(text_descr)

            if formatted_details['has_action_details']:
                text_descr = 'For more information, see the Actions section below.'
                formatted_details['descr'] += ' ' + self.formatter.italic(text_descr)

        if deprecated_descr:
            formatted_details['descr'] += ' ' + self.formatter.italic(deprecated_descr)

        prop_type = formatted_details['prop_type']
        if has_enum:
            prop_type += '<br>(enum)'

        if formatted_details['prop_units']:
            prop_type += '<br>(' + formatted_details['prop_units'] + ')'

        if is_excerpt:
            prop_type += '<br>(excerpt)'

        if in_array:
            prop_type = 'array (' + prop_type + ')'

        if collapse_array:
            item_list = formatted_details['item_list']
            if len(item_list):
                if isinstance(item_list, list):
                    item_list = ', '.join(item_list)
                prop_type += ' (' + item_list + ')'

        prop_access = ''
        if (not formatted_details['prop_is_object']
                and not formatted_details.get('array_of_objects')
                and not as_action_parameters):
            if formatted_details['read_only']:
                prop_access = 'read-only'
            else:
                # Special case for subset mode; if profile indicates WriteRequirement === None (present and None),
                # emit read-only.
                if ((self.config.get('profile_mode') == 'subset')
                        and formatted_details.get('profile_write_req')
                        and (formatted_details['profile_write_req'] == 'None')):
                        prop_access = 'read-only'
                else:
                    prop_access = 'read-write'

        # Action parameters don't have read/write properties, but they can be required/optional.
        if as_action_parameters:
            if formatted_details['prop_required'] or formatted_details['required_parameter']:
                prop_access = 'required'
            else:
                prop_access = 'optional'
        else:
            if formatted_details['prop_required'] or formatted_details['required_parameter']:
                prop_access += ' required'
            elif formatted_details['prop_required_on_create']:
                prop_access += ' required on create'

        if formatted_details['nullable']:
            prop_access += '<br>(null)'

        # If profile reqs are present, massage them:
        profile_access = self.format_base_profile_access(formatted_details)

        if self.config.get('profile_mode') and self.config.get('profile_mode') != 'subset':
            if profile_access:
                prop_type += '<br><br>' + self.formatter.italic(profile_access)
        elif prop_access:
            prop_type += '<br><br>' + self.formatter.italic(prop_access)


        row = []
        row.append(indentation_string + name_and_version)
        row.append(prop_type)
        row.append(formatted_details['descr'])

        formatted.append('| ' + ' | '.join(row) + ' |')

        if len(formatted_details['object_description']) > 0:
            formatted.append(formatted_details['object_description'])
            formatted.append('| ' + indentation_string + '} |   |   |')

        if not collapse_array and len(formatted_details['item_description']) > 0:
            formatted.append(formatted_details['item_description'])
            if formatted_details['array_of_objects']:
                formatted.append('| ' + indentation_string + '} ] |   |   |')
            else:
                formatted.append('| ' + indentation_string + '] |   |   |')

        return({'row': '\n'.join(formatted), 'details':formatted_details['prop_details'],
                'action_details':formatted_details.get('action_details'),
                'profile_conditional_details': formatted_details.get('profile_conditional_details')})


    def format_property_details(self, prop_name, prop_type, prop_description, enum, enum_details,
                                supplemental_details, parent_prop_info, profile=None):
        """Generate a formatted table of enum information for inclusion in Property details."""

        contents = []

        parent_version = parent_prop_info.get('versionAdded')
        if parent_version:
            parent_version = self.format_version(parent_version)

        # Are we in profile mode? If so, consult the profile passed in for this property.
        # For Action Parameters, look for ParameterValues/RecommendedValues; for
        # Property enums, look for MinSupportValues/RecommendedValues.
        profile_mode = self.config.get('profile_mode')
        if profile_mode:
            if profile is None:
                profile = {}

            profile_values = profile.get('Values', [])
            profile_min_support_values = profile.get('MinSupportValues', []) # No longer a valid name?
            profile_parameter_values = profile.get('ParameterValues', [])
            profile_recommended_values = profile.get('RecommendedValues', [])

            # profile_all_values is not used. What were we going for here?
            profile_all_values = (profile_values + profile_min_support_values + profile_parameter_values
                                  + profile_recommended_values)

            # In subset mode, an action parameter with no Values (property) or ParameterValues (Action)
            # means all values are supported.
            # Otherwise, Values/ParameterValues specifies the set that should be listed.
            if profile_mode == 'subset':
                if len(profile_values):
                    enum = [x for x in enum if x in profile_values]
                elif len(profile_parameter_values):
                    enum = [x for x in enum if x in profile_parameter_values]

        if prop_description:
            contents.append(self.formatter.para(self.escape_for_markdown(prop_description, self.config.get('escape_chars', []))))

        if isinstance(prop_type, list):
            prop_type = ', '.join(prop_type)

        if supplemental_details:
            contents.append('\n' + supplemental_details + '\n')

        if enum_details:
            if profile_mode and profile_mode != 'subset':
                contents.append('| ' + prop_type + ' | Description | Profile Specifies |')
                contents.append('| --- | --- | --- |')
            else:
                contents.append('| ' + prop_type + ' | Description |')
                contents.append('| --- | --- |')
            enum.sort(key=str.lower)
            for enum_item in enum:
                enum_name = enum_item
                version = version_depr = deprecated_descr = None
                version_display = None
                if parent_prop_info.get('enumVersionAdded'):
                    version_added = parent_prop_info.get('enumVersionAdded').get(enum_name)
                    if version_added:
                        version = self.format_version(version_added)
                if parent_prop_info.get('enumVersionDeprecated'):
                    version_deprecated = parent_prop_info.get('enumVersionDeprecated').get(enum_name)
                    if version_deprecated:
                        version_depr = self.format_version(version_deprecated)
                if parent_prop_info.get('enumDeprecated'):
                    deprecated_descr = parent_prop_info.get('enumDeprecated').get(enum_name)

                if version:
                    if not parent_version or DocGenUtilities.compare_versions(version, parent_version) > 0:
                        version_display = self.truncate_version(version, 2) + '+'

                if version_display:
                    if version_depr:
                        deprecated_display = self.truncate_version(version_depr, 2)
                        enum_name += ' ' + self.formatter.italic('(v' + version_display + ', deprecated v' + deprecated_display + ')')
                        if deprecated_descr:
                            deprecated_descr = 'Deprecated in v' + deprecated_display + ' and later. ' + deprecated_descr
                    else:
                        enum_name += ' ' + self.formatter.italic('(v' + version_display + ')')
                elif version_depr:
                    deprecated_display = self.truncate_version(version_depr, 2)
                    enum_name += ' ' + self.formatter.italic('(deprecated v' + deprecated_display + ')')
                    if deprecated_descr:
                        deprecated_descr = 'Deprecated in v' + deprecated_display + ' and later. ' + deprecated_descr

                descr = enum_details.get(enum_item, '')
                if deprecated_descr:
                    if descr:
                        descr += ' ' + self.formatter.italic(deprecated_descr)
                    else:
                        descr = self.formatter.italic(deprecated_descr)

                if profile_mode and profile_mode != 'subset':
                    profile_spec = ''
                    if enum_name in profile_values:
                        profile_spec = 'Mandatory'
                    elif enum_name in profile_min_support_values:
                        profile_spec = 'Mandatory'
                    elif enum_name in profile_parameter_values:
                        profile_spec = 'Mandatory'
                    elif enum_name in profile_recommended_values:
                        profile_spec = 'Recommended'
                    contents.append('| ' + enum_name + ' | ' + descr + ' | ' + profile_spec + ' |')
                else:
                    contents.append('| ' + enum_name + ' | ' + descr + ' |')

        elif enum:
            if profile_mode and profile_mode != 'subset':
                contents.append('| ' + prop_type + ' | Profile Specifies |')
                contents.append('| --- | --- |')
            else:
                contents.append('| ' + prop_type + ' |')
                contents.append('| --- |')
            for enum_item in enum:
                enum_name = enum_item
                version = version_depr = deprecated_descr = None
                version_display = None

                if parent_prop_info.get('enumVersionAdded'):
                    version_added = parent_prop_info.get('enumVersionAdded').get(enum_name)
                    if version_added:
                        version = self.format_version(version_added)

                if parent_prop_info('enumVersionDeprecated'):
                    version_deprecated = parent_prop_info.get('enumVersionDeprecated').get(enum_name)
                    if version_deprecated:
                        version_depr = self.format_version(version_deprecated)


                if parent_prop_info.get('enumDeprecated'):
                    deprecated_descr = parent_prop_info.get('enumDeprecated').get(enum_name)

                if version:
                    if not parent_version or DocGenUtilities.compare_versions(version, parent_version) > 0:
                        version_text = html.escape(version, False)
                        version_display = self.truncate_version(version_text, 2) + '+'

                if version_display:
                    if version_depr:
                        deprecated_display = self.truncate_version(version_depr, 2)
                        if deprecated_descr:
                            enum_name += ' ' + self.formatter.italic('(v' + version_display + ', deprecated v' + deprecated_display +
                                                                         '+. ' + deprecated_descr)
                        else:
                            enum_name += ' ' + self.formatter.italic('(v' + version_display + ', deprecated v' + deprecated_display + ')')

                    else:
                        enum_name += ' ' + self.formatter.italic('(v' + version_display + ')')
                else:
                    if version_depr:
                        deprecated_display = self.truncate_version(version_depr, 2)
                        if deprecated_descr:
                            enum_name += ' ' + self.formatter.italic('Deprecated in v' + deprecated_display + ' and later. ' + deprecated_descr)
                        else:
                            enum_name += ' ' + self.formatter.italic('(deprecated in v' + deprecated_display + ' and later.)')

                if profile_mode and profile_mode != 'subset':
                    profile_spec = ''
                    if enum_name in profile_values:
                        profile_spec = 'Mandatory'
                    elif enum_name in profile_min_support_values:
                        profile_spec = 'Mandatory'
                    elif enum_name in profile_parameter_values:
                        profile_spec = 'Mandatory'
                    elif enum_name in profile_recommended_values:
                        profile_spec = 'Recommended'

                    contents.append('| ' + enum_name + ' | ' + profile_spec + ' |')
                else:
                    contents.append('| ' + enum_name + ' | ')

        return '\n'.join(contents) + '\n'


    def format_action_details(self, prop_name, action_details):
        """Generate a formatted Actions section from supplemental markup."""

        contents = []
        contents.append(self.formatter.head_three(action_details.get('action_name', prop_name), self.level))
        if action_details.get('text'):
            contents.append(action_details.get('text'))
        if action_details.get('example'):
            example = '```json\n' + action_details['example'] + '\n```\n'
            contents.append('Example Action POST:\n')
            contents.append(example)

        return '\n'.join(contents) + '\n'


    def format_action_parameters(self, schema_ref, prop_name, prop_descr, action_parameters, profile,
                                     version_strings=None):
        """Generate a formatted Actions section from parameter data. """

        formatted = []
        version_string = deprecated_descr = None
        if version_strings:
            version_string = version_strings.get('version_string')
            deprecated_descr = version_strings.get('deprecated_descr')

        action_name = prop_name
        if prop_name.startswith('#'): # expected
            # Example: from #Bios.ResetBios, we want prop_name "ResetBios" and action_name "Bios.ResetBios"
            prop_name_parts = prop_name.split('.')
            prop_name = prop_name_parts[-1]
            action_name = action_name[1:]

        name_and_version = prop_name
        if version_string:
            name_and_version += ' ' + self.formatter.italic(version_strings['version_string'])

        formatted.append(self.formatter.head_four(name_and_version, self.level))
        if deprecated_descr:
            formatted.append(self.formatter.para(italic(deprecated_descr)))
        formatted.append(self.formatter.para(prop_descr))

        # Add the URIs for this action.
        formatted.append(self.format_uri_block_for_action(action_name, self.current_uris));

        param_names = []

        if action_parameters:
            rows = []
            # Table start:
            rows.append("|     |     |     |")
            rows.append("| --- | --- | --- |")

            # Add a "start object" row for this parameter:
            rows.append('| ' + ' | '.join(['{', ' ',' ',' ']) + ' |')

            param_names = [x for x in action_parameters.keys()]

            if self.config.get('profile_mode') == 'subset':
                if profile.get('Parameters'):
                    param_names = [x for x in profile['Parameters'].keys() if x in param_names]
                # If there is no profile for this action, all parameters should be output.

            param_names.sort(key=str.lower)

        if len(param_names):
            for param_name in param_names:
                formatted_parameters = self.format_property_row(schema_ref, param_name, action_parameters[param_name], ['Actions', prop_name], False, True)
                rows.append(formatted_parameters.get('row'))

            # Add a closing } row:
            rows.append('| ' + ' | '.join(['}', ' ',' ',' ']) + ' |')

            formatted.append(self.formatter.para('The following table shows the parameters for the action which are included in the POST body to the URI shown in the "target" property of the Action.'))

            formatted.append('\n'.join(rows))

        else:
            formatted.append(self.formatter.para("(This action takes no parameters.)"))

        return "\n".join(formatted)


    def _format_profile_access(self, read_only=False, read_req=None, write_req=None, min_count=None):
        """Common formatting logic for profile_access column"""

        profile_access = ''
        if not self.config['profile_mode']:
            return profile_access

        # Each requirement  may be Mandatory, Recommended, IfImplemented, Conditional, or (None)
        if not read_req:
            read_req = 'Mandatory' # This is the default if nothing is specified.
        if read_only:
            profile_access = self.formatter.nobr(self.text_map(read_req)) + ' (Read-only)'
        elif read_req == write_req:
            profile_access = self.formatter.nobr(self.text_map(read_req)) + ' (Read/Write)'
        elif not write_req:
            profile_access = self.formatter.nobr(self.text_map(read_req)) + ' (Read)'
        else:
            # Presumably Read is Mandatory and Write is Recommended; nothing else makes sense.
            profile_access = (self.formatter.nobr(self.text_map(read_req)) + ' (Read),' +
                              self.formatter.nobr(self.text_map(write_req)) + ' (Read/Write)')

        if min_count:
            if profile_access:
                profile_access += ", "
            profile_access += self.formatter.nobr("Minimum " + str(min_count))

        return profile_access


    def format_as_prop_details(self, prop_name, prop_description, rows):
        """ Take the formatted rows and other strings from prop_info, and create a formatted block suitable for the prop_details section """
        contents = []

        if prop_description:
            contents.append(self.formatter.para(self.escape_for_markdown(prop_description, self.config.get('escape_chars', []))))

        obj_table = self.formatter.make_table(rows)
        contents.append(obj_table)

        return "\n".join(contents)


    def link_to_own_schema(self, schema_ref, schema_full_uri):
        """Format a reference to a schema."""
        result = super().link_to_own_schema(schema_ref, schema_full_uri)
        return self.formatter.italic(result)


    def link_to_outside_schema(self, schema_full_uri):
        """Format a reference to a schema_uri, which should be a valid URI"""
        return self.formatter.italic('['+ schema_full_uri + '](' + schema_full_uri + ')')


    # def format_version_strings(self, version_added, version_deprecated, version_deprecated_explanation):
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

        version = None
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
            version_display = self.truncate_version(version, 2) + '+'
            if version_deprecated:
                deprecated_display = self.truncate_version(version_depr, 2)
                version_string = '(v' + version_display + ', deprecated v' + deprecated_display +  ')'
                deprecated_descr = ("Deprecated in v" + deprecated_display + ' and later. ' +
                                    self.escape_for_markdown(version_deprecated_explanation,
                                                                 self.config.get('escape_chars', [])))
            else:
                version_string = '(v' + version_display + ')'
        elif version_deprecated:
            deprecated_display = self.truncate_version(version_depr, 2)
            version_string = '(deprecated v' + deprecated_display +  ')'
            deprecated_descr =  ("Deprecated in v" + deprecated_display + ' and later. ' +
                                 self.escape_for_markdown(version_deprecated_explanation,
                                                          self.config.get('escape_chars', [])))

        return {"version_string": version_string, "deprecated_descr": deprecated_descr}


    def emit(self):
        """ Output contents thus far """

        contents = []

        for section in self.sections:
            contents.append(section.get('heading'))
            if section.get('release_history'):
                contents.append(section['release_history'])
            if section.get('conditional_requirements'):
                contents.append(section['conditional_requirements'])
            if section.get('description'):
                contents.append(section['description'])
            if section.get('uris'):
                contents.append(section['uris'])
            if section.get('json_payload'):
                contents.append(section['json_payload'])
            # something is awry if there are no properties, but ...
            if section.get('properties'):
                contents.append('|     |     |     |')
                contents.append('| --- | --- | --- |')
                contents.append('\n'.join(section['properties']))

            if section.get('profile_conditional_details'):
                # sort them now; these can be sub-properties so may not be in alpha order.
                conditional_details = '\n'.join(sorted(section['profile_conditional_details'], key=str.lower))
                contents.append('\n' + self.formatter.head_two('Conditional Requirements', self.level))
                contents.append(conditional_details)

            if len(section.get('action_details', [])):
                contents.append('\n' + self.formatter.head_two('Actions', self.level))
                contents.append('\n\n'.join(section.get('action_details')))
            if section.get('property_details'):
                contents.append('\n' + self.formatter.head_two('Property details', self.level))
                detail_names = [x for x in section['property_details'].keys()]
                detail_names.sort(key=str.lower)
                for detail_name in detail_names:
                    contents.append(self.formatter.head_three(detail_name + ':', 0))
                    det_info = section['property_details'][detail_name]
                    if len(det_info) == 1:
                        for x in det_info.values():
                            contents.append(x['formatted_descr'])
                    else:
                        path_to_ref = {}
                        # Generate path descriptions and sort them.
                        for ref, info in det_info.items():
                            paths_as_text = [": ".join(x) for x in info['paths']]
                            paths_as_text = ', '.join(paths_as_text)
                            path_to_ref[paths_as_text] = ref
                        paths_sorted = [x for x in path_to_ref.keys()]
                        paths_sorted.sort(key=str.lower)
                        for path in paths_sorted:
                            info = det_info[path_to_ref[path]]
                            contents.append(self.formatter.para(self.formatter.bold("In " + path + ":")))
                            contents.append(info['formatted_descr'])

        self.sections = []

        # Profile output may include registry sections
        for section in self.registry_sections:
            contents.append(section.get('heading'))
            contents.append(section.get('requirement'))
            if section.get('description'):
                contents.append(self.formatter.para(section['description']))
            if section.get('messages'):
                contents.append(self.formatter.head_two('Messages', self.level))
                message_rows = [self.formatter.make_row(x) for x in section['messages']]
                header_cells = ['', 'Requirement']
                if self.config.get('profile_mode') != 'terse':
                    header_cells.append('Description')
                header_row = self.formatter.make_row(header_cells)
                contents.append(self.formatter.make_table(message_rows, [header_row], 'messages'))
                contents.append('\n')

        return '\n'.join(contents)


    def output_document(self):
        """Return full contents of document"""
        body = self.emit()
        common_properties = self.generate_common_properties_doc()

        supplemental = self.config.get('supplemental', {})

        if 'Title' in supplemental:
            doc_title = supplemental['Title']
        else:
            doc_title = 'Schema Documentation'

        prelude = "---\ntitle: " + doc_title + """

search: true
---
"""

        intro = supplemental.get('Introduction')
        if intro:
            intro = self.process_intro(intro)
            prelude += '\n' + intro + '\n'

        contents = [prelude, body]
        if 'Postscript' in supplemental:
            contents.append('\n' + supplemental['Postscript'])

        output = '\n'.join(contents)
        if '[insert_common_objects]' in output:
            output = output.replace('[insert_common_objects]', common_properties, 1)

        if '[insert_collections]' in output:
            collections_doc = self.generate_collections_doc()
            output = output.replace('[insert_collections]', collections_doc, 1)

        # Replace pagebreak markers with HTML pagebreak markup
        output = output.replace('~pagebreak~', '<p style="page-break-before: always"></p>')

        return output


    def process_intro(self, intro_blob):
        """ Process the intro text, generating and inserting any schema fragments """
        parts = []
        intro = []
        part_text = []

        fragment_config = {
            'output_format': 'markdown',
            'normative': self.config.get('normative'),
            'cwd': self.config.get('cwd'),
            'schema_supplement': {},
            'supplemental': {},
            'excluded_annotations': [],
            'excluded_annotations_by_match': [],
            'excluded_properties': [],
            'excluded_by_match': [],
            'excluded_schemas': [],
            'excluded_schemas_by_match': [],
            'escape_chars': [],
            'uri_replacements': {},
            'units_translation': self.config.get('units_translation'),
            'profile': self.config.get('profile'),
            'profile_mode': self.config.get('profile_mode'),
            'profile_resources': self.config.get('profile_resources', {}),
            'wants_common_objects': self.config.get('wants_common_objects'),
            'actions_in_property_table': self.config.get('actions_in_property_table', True),
            }

        for line in intro_blob.splitlines():
            if line.startswith('#include_fragment'):
                if len(part_text):
                    parts.append({'type': 'markdown', 'content': '\n'.join(part_text)})
                    part_text = []
                    fragment_id = line[17:].strip()
                    fragment_content = self.generate_fragment_doc(fragment_id, fragment_config)
                    parts.append({'type': 'fragment', 'content': fragment_content})
            else:
                part_text.append(line)

        if len(part_text):
            parts.append({'type': 'markdown', 'content': '\n'.join(part_text)})

        for part in parts:
            if part['type'] == 'markdown':
                intro.append(part['content'])
            elif part['type'] == 'fragment':
                intro.append(part['content'])
        return '\n'.join(intro)


    def add_section(self, text, link_id=False, schema_ref=False):
        """ Add a top-level heading """
        self.this_section = {'head': text,
                             'heading': '\n' + self.formatter.head_one(text, self.level),
                             'properties': [],
                             'property_details': {}
                            }
        self.sections.append(self.this_section)


    def add_description(self, text):
        """ Add the schema description """
        self.this_section['description'] = text + '\n'


    def add_uris(self, uris):
        """ Add the URIs (which should be a list) """
        uri_block = "**URIs**:\n"
        for uri in sorted(uris, key=str.lower):
            uri_block += "\n" + self.format_uri(uri)
        self.this_section['uris'] = uri_block + "\n"


    def add_conditional_requirements(self, text):
        """ Add a conditional requirements, which should already be formatted """
        self.this_section['conditional_requirements'] = "\n**Conditional Requirements:**\n\n" + text + "\n"


    def format_uri_block_for_action(self, action, uris):
        """ Create a URI block for this action & the resource's URIs """
        uri_block = "**URIs**:\n"
        for uri in sorted(uris, key=str.lower):
            uri = uri + "/Actions/" + action
            uri_block += "\n" + self.format_uri(uri)

        return uri_block


    def format_json_payload(self, json_payload):
        """ Format a json payload for output. """
        return '\n' + json_payload + '\n'


    def add_property_row(self, formatted_text):
        """Add a row (or group of rows) for an individual property in the current section/schema.

        formatted_row should be a chunk of text already formatted for output"""
        self.this_section['properties'].append(formatted_text)


    def add_registry_reqs(self, registry_reqs):
        """Add registry messages. registry_reqs includes profile annotations."""

        terse_mode = self.config.get('profile_mode') == 'terse'

        reg_names = [x for x in registry_reqs.keys()]
        reg_names.sort(key=str.lower)
        for reg_name in reg_names:
            reg = registry_reqs[reg_name]
            this_section = {
                'head': reg_name,
                'description': reg.get('Description', ''),
                'messages': []
                }
            heading = reg_name + ' Registry v' + reg['minversion']  + '+'
            if reg.get('current_release', reg['minversion']) != reg['minversion']:
                heading += ' (current release: v' + reg['current_release'] + ')'

            this_section['heading'] = self.formatter.head_one(heading, self.level)
            this_section['requirement'] = 'Requirement: ' + reg.get('profile_requirement', '')

            msgs = reg.get('Messages', {})
            msg_keys = [x for x in msgs.keys()]
            msg_keys.sort(key=str.lower)

            for msg in msg_keys:
                this_msg = msgs[msg]
                if terse_mode and not this_msg.get('profile_requirement'):
                    continue
                msg_row = [msg, this_msg.get('profile_requirement', '')]
                if not terse_mode:
                    msg_row.append(this_msg.get('Description', ''))
                this_section['messages'].append(msg_row)

            self.registry_sections.append(this_section)


    @staticmethod
    def escape_for_markdown(text, chars):
        """Escape selected characters in text to prevent auto-formatting in markdown."""
        for char in chars:
            text = text.replace(char, '\\' + char)
        return text

    @staticmethod
    def escape_regexp(text):
        """If escaping is necessary to protect patterns when output format is rendered, do that."""
        chars_to_escape = r'\`*_{}[]()#+-.!|'
        escaped_text = ''
        for char in text:
            if char in chars_to_escape:
                escaped_text += '\\' + char
            else:
                escaped_text += char

        return escaped_text
