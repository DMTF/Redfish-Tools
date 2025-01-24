# Copyright Notice:
# Copyright 2016-2022 Distributed Management Task Force, Inc. All rights reserved.
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

class MarkdownGenerator(DocFormatter):
    """Provides methods for generating markdown from Redfish schemas.

    "slate" mode markdown is targeted to the Slate documentation tool: https://github.com/lord/slate
    """


    def __init__(self, property_data, traverser, config, level=0):
        super(MarkdownGenerator, self).__init__(property_data, traverser, config, level)
        self.separators = {
            'inline': ', ',
            'linebreak': '\n',
            'pattern': ', '
            }
        self.formatter = FormatUtils()
        self.table_formats = self.config.get('table_formats')
        self.table_xref_formats = self.config.get('table_xref_formats')
        if self.markdown_mode == 'slate':
            self.layout_payloads = 'top'
        else:
            self.layout_payloads = 'bottom'

        # Add some functions we'll use to selectively promote headings when the output mode is slate.
        self.format_head_two = self.formatter.head_two
        if self.markdown_mode == 'slate':
            self.format_head_two = self.formatter.head_one

        self.format_head_three = self.formatter.head_three
        if self.markdown_mode == 'slate':
            self.format_head_three = self.formatter.head_two

        self.format_head_four = self.formatter.head_four
        if self.markdown_mode == 'slate':
            self.format_head_four = self.formatter.head_three


    def format_property_row(self, schema_ref, prop_name, prop_info, prop_path=[], in_array=False, as_action_parameters=False,
                                in_schema_ref=None):
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
        if self.config.get('remove_blanks') != True:
            if self.config.get('strip_top_object') and current_depth > 0:
                indentation_string = '&nbsp;' * 6 * (current_depth -1)
            else:
                indentation_string = '&nbsp;' * 6 * current_depth
        else:
            indentation_string = ""

        # If prop_path starts with Actions and is more than 1 deep, we are outputting for an Actions
        # section and should dial back the indentation by one level.
        if self.config.get('remove_blanks') != True:
            if len(prop_path) > 1 and prop_path[0] == 'Actions':
                indentation_string = '&nbsp;' * 6 * (current_depth -1)
        else:
            indentation_string = ""

        collapse_array = False # Should we collapse a list description into one row? For lists of simple types
        has_enum = False
        format_annotation = None

        if current_depth < self.current_depth:
            for i in range(current_depth, self.current_depth):
                if i in self.current_version:
                    del self.current_version[i]
        self.current_depth = current_depth
        parent_depth = current_depth - 1

        if isinstance(prop_info, list):
            has_enum = 'enum' in prop_info[0]
            is_excerpt = prop_info[0].get('_is_excerpt') or prop_info[0].get('excerptCopy')
            translated_name = prop_info[0].get('translation')
            if 'format' in prop_info[0]:
                format_annotation = prop_info[0]['format']
            if 'pattern' in prop_info[0]:
                if (prop_info[0].get('pattern') == '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$') or (prop_info[0].get('pattern') == '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})'):
                    format_annotation = 'uuid'
                if (prop_info[0].get('pattern') == '^P(\\d+D)?(T(\\d+H)?(\\d+M)?(\\d+(.\\d+)?S)?)?$') or (prop_info[0].get('pattern') == '-?P(\d+D)?(T(\d+H)?(\d+M)?(\d+(.\d+)?S)?)?'):
                    format_annotation = 'duration'
        elif isinstance(prop_info, dict):
            has_enum = 'enum' in prop_info
            is_excerpt = prop_info.get('_is_excerpt')
            translated_name = prop_info.get('translation')
            if 'format' in prop_info:
                format_annotation = prop_info['format']
            if 'pattern' in prop_info:
                if prop_info.get('pattern') == '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})':
                    format_annotation = 'uuid'
                if prop_info.get('pattern') == '-?P(\d+D)?(T(\d+H)?(\d+M)?(\d+(.\d+)?S)?)?':
                    format_annotation = 'duration'

        format_annotation = self.format_annotation_strings.get(format_annotation, format_annotation)


        version_strings = self.format_version_strings(prop_info)
        if prop_name:
            name_and_version = self.formatter.bold(self.escape_for_markdown(prop_name,
                                                                  self.config.get('escape_chars', [])))
            if translated_name:
                name_and_version += ' ' + self.formatter.italic(self.escape_for_markdown('(' + translated_name + ')',
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

        if formatted_details['profile_purpose'] and self.config.get('profile_mode'):
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
                    text_descr = _('For the possible property values, see %(link)s in Property details.') % {'link': prop_name}
                else:
                    text_descr = _('For more information about this property, see Property details.')
                formatted_details['descr'] += ' ' + self.formatter.italic(text_descr)

            if formatted_details['has_action_details']:
                text_descr = _('For more information, see the Actions section below.')
                formatted_details['descr'] += ' ' + self.formatter.italic(text_descr)

        if deprecated_descr:
            formatted_details['descr'] += ' ' + self.formatter.italic(deprecated_descr)

        prop_type = formatted_details['prop_type']
        if has_enum:
            prop_type += '<br>(' + _('enum') + ')'

        if format_annotation:
            prop_type += '<br>(' + format_annotation + ')'

        if formatted_details['prop_units']:
            prop_type += '<br>(' + formatted_details['prop_units'] + ')'

        if is_excerpt:
            prop_type += '<br>(' + _('excerpt') + ')'

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
                prop_access = _('read-only')
            else:
                prop_access = _('read-write')

        # Action parameters don't have read/write properties, but they can be required/optional.
        if as_action_parameters:
            if formatted_details['prop_required'] or formatted_details['required_parameter']:
                prop_access = _('required')
            else:
                prop_access = _('optional')
        else:
            if formatted_details['prop_required'] or formatted_details['required_parameter']:
                prop_access += ' ' + _('required')
            elif formatted_details['prop_required_on_create']:
                prop_access += ' ' + _('required on create')

        if formatted_details['nullable']:
            prop_access += '<br>' + _('(null)')

        # If profile reqs are present, massage them:
        profile_access = self.format_base_profile_access(formatted_details)

        if self.markdown_mode == 'slate':
            if self.config.get('profile_mode'):
                if profile_access:
                    prop_type += '<br><br>' + self.formatter.italic(profile_access)
            elif prop_access:
                prop_type += '<br><br>' + self.formatter.italic(prop_access)


        row = []
        row.append(indentation_string + name_and_version)
        row.append(prop_type)
        if self.markdown_mode != 'slate':
            if self.config.get('profile_mode'):
                if profile_access:
                    row.append(self.formatter.italic(profile_access))
                else:
                    row.append('')
            else:
                if prop_access:
                    row.append(self.formatter.italic(prop_access))
                else:
                    row.append('')

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
                                supplemental_details, parent_prop_info, profile=None, subset=None):
        """Generate a formatted table of enum information for inclusion in Property details."""

        contents = []

        parent_version = parent_prop_info.get('versionAdded')
        if parent_version:
            parent_version = self.format_version(parent_version)

        # Are we in profile mode? If so, consult the profile passed in for this property.
        # For Action Parameters, look for ParameterValues/RecommendedValues; for
        # Property enums, look for MinSupportValues/RecommendedValues.
        profile_mode = self.config.get('profile_mode')
        subset_mode = self.config.get('subset_mode')
        if profile_mode or subset_mode: # TODO: split these up
            if profile is None:
                profile = {}

            profile_values = profile.get('Values', [])
            profile_min_support_values = profile.get('MinSupportValues', []) # No longer a valid name?
            profile_parameter_values = profile.get('ParameterValues', [])
            profile_recommended_values = profile.get('RecommendedValues', [])

            # profile_all_values is not used. What were we going for here?
            profile_all_values = (profile_values + profile_min_support_values + profile_parameter_values
                                  + profile_recommended_values)

            if subset_mode and subset:
                supported_values = subset.get('SupportedValues')
                if supported_values:
                    enum = [x for x in enum if x in supported_values]

        if prop_description:
            contents.append(self.escape_for_markdown(prop_description, self.config.get('escape_chars', [])))
            contents.append('') # for a newline after. (self.formatter.para would also add one before, excessively)

        if isinstance(prop_type, list):
            prop_type = ', '.join(prop_type)

        if supplemental_details:
            contents.append('\n' + supplemental_details + '\n')

        enum_translations = parent_prop_info.get('enumTranslations', {})

        if enum_details:
            if profile_mode:
                contents.append('| ' + prop_type + ' | ' + _('Description') + ' | ' + _('Profile Specifies') + ' |')
                if self.config.get('table_formats', {}).get("enum_details"):
                    contents.append(self.config.get('table_formats', {}).get("enum_details"))
                else:
                    contents.append('| :--- | :------ | :--- |')
            else:
                contents.append('| ' + prop_type + ' | ' + _('Description') + ' |')
                if self.config.get('table_formats', {}).get("enum_subset"):
                    contents.append(self.config.get('table_formats', {}).get("enum_subset"))
                else:
                    contents.append('| :--- | :------------ |')
            enum.sort(key=str.lower)
            for enum_item in enum:
                enum_name = enum_item
                enum_translation = enum_translations.get(enum_item)
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

                if enum_translation:
                    enum_name += ' (' + enum_translation + ')'

                if version:
                    if not parent_version or DocGenUtilities.compare_versions(version, parent_version) > 0:
                        version_display = self.truncate_version(version, 2) + '+'

                if version_display:
                    if version_depr:
                        deprecated_display = self.truncate_version(version_depr, 2)
                        enum_name += ' ' + self.formatter.italic(_('(v%(version_number)s, deprecated v%(deprecated_version)s)') %
                                                                     {'version_number': version_display, 'deprecated_version': deprecated_display})
                        if deprecated_descr:
                            deprecated_descr = (_('Deprecated in v%(version_number)s and later. %(explanation)s') %
                                                    {'version_number': deprecated_display, 'explanation': deprecated_descr})
                    else:
                        enum_name += ' ' + self.formatter.italic(_('(v%(version_number)s)') % {'version_number': version_display})
                elif version_depr:
                    deprecated_display = self.truncate_version(version_depr, 2)
                    enum_name += ' ' + self.formatter.italic(_('(deprecated v%(version_number)s)') % {'version_number': deprecated_display})
                    if deprecated_descr:
                        deprecated_descr = (_('Deprecated in v%(version_number)s and later. %(explanation)s') %
                                                {'version_number': deprecated_display, 'explanation': deprecated_descr})

                descr = enum_details.get(enum_item, '')
                if deprecated_descr:
                    if descr:
                        descr += ' ' + self.formatter.italic(deprecated_descr)
                    else:
                        descr = self.formatter.italic(deprecated_descr)

                if profile_mode:
                    profile_spec = ''
                    # Note: don't wrap the following strings for trnaslation; self.text_map handles that.
                    if enum_item in profile_values:
                        profile_spec = 'Mandatory'
                    elif enum_item in profile_min_support_values:
                        profile_spec = 'Mandatory'
                    elif enum_item in profile_parameter_values:
                        profile_spec = 'Mandatory'
                    elif enum_item in profile_recommended_values:
                        profile_spec = 'Recommended'
                    contents.append('| ' + enum_name + ' | ' + descr + ' | ' + self.text_map(profile_spec) + ' |')
                else:
                    contents.append('| ' + enum_name + ' | ' + descr + ' |')

        elif enum:
            if profile_mode:
                contents.append('| ' + prop_type + ' | '+ _('Profile Specifies') + ' |')
                if self.config.get('table_formats', {}).get("profile_details"):
                    contents.append(self.config.get('table_formats', {}).get("profile_details"))
                else:
                    contents.append('| :--- | :--- |')
            else:
                contents.append('| ' + prop_type + ' |')
                if self.config.get('table_formats', {}).get("profile_subset"):
                    contents.append(self.config.get('table_formats', {}).get("profile_subset"))
                else:
                    contents.append('| :--- |')
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
                            enum_name += ' ' + self.formatter.italic(_('(v%(version_number)s, deprecated v%(deprecated_version)s. %(explanation)s') %
                                                                         { 'version_number': version_display, 'deprecated_version': deprecated_display,
                                                                               'explanation': deprecated_descr})
                        else:
                            enum_name += ' ' + self.formatter.italic(_('(v%(version_number)s, deprecated v%(deprecated_version)s)') %
                                                                         {'version_number': version_display, 'deprecated_version': deprecated_display})

                    else:
                        enum_name += ' ' + self.formatter.italic(_('(v%(version_number)s)') % {'version_number': version_display})
                else:
                    if version_depr:
                        deprecated_display = self.truncate_version(version_depr, 2)
                        if deprecated_descr:
                            enum_name += ' ' + self.formatter.italic(_('Deprecated in v%(deprecated_version)s and later. %(explanation)s') %
                                                                         {'deprecated_version': deprecated_display, 'explanation': deprecated_descr})
                        else:
                            enum_name += ' ' + self.formatter.italic(_('(deprecated in v%(deprecated_version)s and later.)') % {'deprecated_version': deprecated_display})

                if profile_mode:
                    profile_spec = ''
                    # Note: don't wrap the following strings for trnaslation; self.text_map handles that.
                    if enum_name in profile_values:
                        profile_spec = 'Mandatory'
                    elif enum_name in profile_min_support_values:
                        profile_spec = 'Mandatory'
                    elif enum_name in profile_parameter_values:
                        profile_spec = 'Mandatory'
                    elif enum_name in profile_recommended_values:
                        profile_spec = 'Recommended'

                    contents.append('| ' + enum_name + ' | ' + self.text_map(profile_spec) + ' |')
                else:
                    contents.append('| ' + enum_name + ' | ')

        formatted = '\n'.join(contents) + '\n'
        if self.config.get('with_table_numbering'):
            if self.table_xref_formats:
                caption = self.formatter.add_table_caption(_("%(prop_name)s property values") % {'prop_name': prop_name}, self.table_xref_formats['caption'])
                preamble = self.formatter.add_table_reference(_("The defined property values are listed in "), self.table_xref_formats['reference'])
            formatted = preamble + '\n' + formatted + caption

        return formatted


    def format_action_parameters(self, schema_ref, prop_name, prop_descr, action_parameters, profile,
                                     version_strings=None, supplemental_details=None, subset=None):
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

        if self.markdown_mode == 'slate':
            formatted.append(self.formatter.head_five(name_and_version, self.level))
        else:
            formatted.append(self.formatter.head_four(name_and_version, self.level))

        if deprecated_descr:
            formatted.append(self.formatter.para(italic(deprecated_descr)))
        formatted.append(self.formatter.para(self.formatter.bold(_("Description"))))
        formatted.append(self.formatter.para(prop_descr))

        if supplemental_details:
            formatted.append("\n" + supplemental_details)

        # Add the URIs for this action.
        formatted.append(self.format_uri_block_for_action(action_name, self.current_uris));

        param_names = []

        if action_parameters:
            rows = []
            # Table start:

            if self.markdown_mode == 'slate':
                rows.append("| " + _('Parameter Name') + "     | " + _('Type') + "     | " + _('Notes') + "     |")
                rows.append("| :--- | :--- | :--- |")
            else:
                rows.append("| " + _('Parameter Name') + "     | " + _('Type') + "     | " + _('Attributes') + '   | ' + _('Notes') + "     |")
                if self.table_formats:
                    if self.table_formats.get("properties"):
                        rows.append(self.table_formats.get('action_parameters'))
                else:
                    rows.append("| :--- | :--- | :--- | :--------------------- |")

            param_names = [x for x in action_parameters.keys()]

            if self.config.get('subset_mode') and subset:
                supported_values = subset.get('SupportedValues')
                if supported_values:
                    param_names = [x for x in param_names if x in supported_values]

            param_names.sort(key=str.lower)

        heading = self.formatter.para(self.formatter.bold(_("Action parameters")))
        if len(param_names):
            for param_name in param_names:
                formatted_parameters = self.format_property_row(schema_ref, param_name, action_parameters[param_name], ['Actions', prop_name], False, True)
                rows.append(formatted_parameters.get('row'))

            formatted_rows = '\n'.join(rows) + "\n"
            if self.config.get('with_table_numbering'):
                if self.table_xref_formats:
                    caption = self.formatter.add_table_caption(_("%(prop_name)s action parameters") % {'prop_name': prop_name}, self.table_xref_formats['caption'])
                    preamble = "\n" + heading + "\n\n" +  self.formatter.add_table_reference(_("The parameters for the action which are included in the POST body to the URI shown in the 'target' property of the Action are summarized in "), self.table_xref_formats['reference']) + "\n\n"
                    formatted_rows = preamble +  formatted_rows + caption
            else:
                formatted.append(heading)
            formatted.append(formatted_rows)

        else:
            formatted.append(heading)
            formatted.append(self.formatter.para(_("This action takes no parameters.")))

        return "\n".join(formatted)


    def _format_profile_access(self, read_only=False, read_req=None, write_req=None, min_count=None):
        """Common formatting logic for profile_access column"""

        profile_access = ''
        if not self.config.get('profile_mode'):
            return profile_access

        # Each requirement  may be Mandatory, Recommended, IfImplemented, Conditional, or (None)
        if not read_req:
            read_req = 'Mandatory' # This is the default if nothing is specified.
        if read_only:
            profile_access = self.formatter.nobr(self.text_map(read_req)) + ' ' + _('(Read-only)')
        elif read_req == write_req:
            profile_access = self.formatter.nobr(self.text_map(read_req)) + ' ' + _('(Read/Write)')
        elif not write_req:
            profile_access = self.formatter.nobr(self.text_map(read_req)) + ' ' + _('(Read)')
        else:
            # Presumably Read is Mandatory and Write is Recommended; nothing else makes sense.
            profile_access = (self.formatter.nobr(self.text_map(read_req)) + ' ' + _('(Read)') + ',' +
                              self.formatter.nobr(self.text_map(write_req)) + ' ' + _('(Read/Write)'))

        if min_count:
            if profile_access:
                profile_access += ", "
            profile_access += self.formatter.nobr(_('Minimum %(min_count)s') % {'min_count':  str(min_count)})

        return profile_access


    def format_as_prop_details(self, prop_name, prop_description, rows):
        """ Take the formatted rows and other strings from prop_info, and create a formatted block suitable for the prop_details section """
        contents = []

        if prop_description:
            contents.append(self.formatter.para(self.escape_for_markdown(prop_description, self.config.get('escape_chars', []))))

        obj_table = self.formatter.make_table(rows, last_column_wide=True)
        contents.append(obj_table)

        return "\n".join(contents)


    def link_to_own_schema(self, schema_ref, schema_full_uri):
        """Format a reference to a schema."""
        result = super().link_to_own_schema(schema_ref, schema_full_uri)
        return self.formatter.italic(result)


    def link_to_outside_schema(self, schema_full_uri):
        """Format a reference to a schema_uri, which should be a valid URI"""
        return self.formatter.italic('['+ schema_full_uri + '](' + schema_full_uri + ')')


    def emit(self):
        """ Output contents thus far """

        contents = []

        for section in self.sections:
            contents.append(section.get('heading'))
            if section.get('release_history'):
                contents.append(section['release_history'])
            if section.get('conditional_requirements'):
                contents.append(section['conditional_requirements'])
            if section.get('deprecation_text'):
                contents.append(section['deprecation_text'])
            if section.get('description'):
                contents.append(section['description'])
            if section.get('uris'):
                contents.append(section['uris'])
            if section.get('json_payload') and (self.markdown_mode == 'slate'): # If not slate, it goes at the end.:
                contents.append(section['json_payload'])

            # something is awry if there are no properties, but ...
            if section.get('properties'):

                if self.config.get('with_table_numbering'):
                    if self.table_xref_formats:
                        caption = self.formatter.add_table_caption(section["head"] + " properties", self.table_xref_formats['caption'])
                        preamble = self.formatter.add_table_reference("The properties defined for the " + section["head"] + " schema are summarized in ", self.table_xref_formats['reference']) + "\n"
                else:
                    caption = preamble = ''

                # properties are a peer of URIs, if they exist
                # TODO: this should use make_table()
                contents.append('\n' + self.format_head_three(_('Properties'), self.level))

                if preamble:
                    contents.append(preamble)

                if self.markdown_mode == 'slate':
                    contents.append('|' + _('Property') + '     |' + _('Type') + '     |' + _('Notes') + '     |')
                    contents.append('| :--- | :--- | :--- |')
                else:
                    contents.append('|' + _('Property') + '     |' + _('Type') + '     |' + _('Attributes') + '   |' + _('Notes') + '     |')
                    if self.table_formats:
                        if self.table_formats.get("properties"):
                            contents.append(self.table_formats.get('properties'))
                    else:
                        contents.append('| :--- | :--- | :--- | :--------------------- |')

                contents.append('\n'.join(section['properties']))

                if caption:
                    contents.append(caption + '\n')

            if section.get('profile_conditional_details'):
                # sort them now; these can be sub-properties so may not be in alpha order.
                conditional_details = '\n'.join(sorted(section['profile_conditional_details'], key=str.lower))
                contents.append('\n' + self.format_head_three(_('Conditional Requirements'), self.level))
                contents.append(conditional_details)

            if len(section.get('action_details', [])):
                contents.append('\n' + self.format_head_three('Actions', self.level))
                contents.append('\n\n'.join(section.get('action_details')))
            if section.get('property_details'):
                contents.append('\n' + self.format_head_three(_('Property details'), self.level))
                detail_names = [x for x in section['property_details'].keys()]
                detail_names.sort(key=str.lower)
                for detail_name in detail_names:
                    contents.append(self.format_head_four(detail_name, 0))
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
                            if path:
                                path_text = _("In %(path)s:") % {'path': path}
                            else:
                                path_text = _("In top level:")
                            if self.markdown_mode == 'slate':
                                contents.append(self.formatter.para(self.formatter.bold(path_text)))
                            else:
                                contents.append(self.formatter.head_five(path_text, self.level))
                            contents.append(info['formatted_descr'])

            if section.get('json_payload') and (self.markdown_mode != 'slate'): # Otherwise, this was inserted above.
                contents.append(self.formatter.head_three(_('Example response'), self.level))
                contents.append(section['json_payload'])

        self.sections = []

        # Profile output may include registry sections
        for section in self.registry_sections:
            contents.append(section.get('heading'))
            contents.append(section.get('requirement'))
            if section.get('description'):
                contents.append(self.formatter.para(section['description']))
            if section.get('messages'):
                contents.append(self.format_head_three(_('Messages'), self.level))
                message_rows = [self.formatter.make_row(x) for x in section['messages']]
                header_cells = ['', _('Requirement')]
                if self.config.get('profile_mode') != 'terse':
                    header_cells.append(_('Description'))
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
            doc_title = _('Schema Documentation')

        prelude = ""

        intro = self.config.get('intro_content')
        if intro:
            intro = self.process_intro(intro)
            prelude += '\n' + intro + '\n'

        contents = [prelude, body]
        postscript = self.config.get('postscript_content')
        if postscript:
            contents.append('\n' + postscript)

        output = '\n'.join(contents)
        if '[insert_common_objects]' in output:
            output = output.replace('[insert_common_objects]', common_properties, 1)

        if '[insert_collections]' in output:
            collections_doc = self.generate_collections_doc()
            output = output.replace('[insert_collections]', collections_doc, 1)

        if self.config.get('add_toc'):
            output = self.generate_toc_and_add_anchors(output)

        # Replace pagebreak markers with HTML pagebreak markup
        output = output.replace('~pagebreak~', '<p style="page-break-before: always"></p>')

        return output


    def generate_toc_and_add_anchors(self, markdown_blob):
        """ Generate a TOC for a blob of markdown, add anchors to markdown, and insert TOC """

        import urllib

        toc = ''
        output_blob = ''
        anchors_seen = []
        for line in markdown_blob.splitlines():
            heading = None
            if line.startswith('# '):
                prefix = '# '
                heading = line[2:]
                indent = 0
            if line.startswith('## '):
                prefix = '## '
                heading = line[3:]
                indent = 1
            if heading:
                anchor = urllib.parse.quote(heading.lower().replace(' ', '-'))
                if anchor in anchors_seen:
                    initial_anchor = anchor
                    num = 0
                    while anchor in anchors_seen:
                        num = num + 1
                        anchor = initial_anchor + '-' + str(num)
                anchors_seen.append(anchor)

                toc += self.formatter.para(('   ' * indent) + '- [' + heading + '](#' + anchor + ')')
                line = prefix + '<a name="' + anchor + '"></a>' + heading

            output_blob = output_blob + '\n' + line

        if '[add_toc]' in output_blob:
            output_blob = output_blob.replace('[add_toc]', toc, 1)
        else:
            output_blob = toc + "\n" + output_blob

        return output_blob


    def process_intro(self, intro_blob):
        """ Process the intro text, generating and inserting any schema fragments """
        parts = []
        intro = []
        part_text = []

        fragment_config = {
            'output_format': 'slate',
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
            'schema_link_replacements': {},
            'units_translation': self.config.get('units_translation'),
            'profile': self.config.get('profile'),
            'profile_mode': self.config.get('profile_mode'),
            'profile_resources': self.config.get('profile_resources', {}),
            'wants_common_objects': self.config.get('wants_common_objects'),
            'actions_in_property_table': self.config.get('actions_in_property_table', True),
            'output_format': self.config.get('output_format')
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

        self.this_section = {
            'properties': [],
            'property_details': {},
            'head': '',
            'heading': '',
            'schema_ref': '',
            'schema_name': '',
            }

        if text:
            self.this_section['head'] = text
            self.this_section['heading'] = '\n' + self.format_head_two(text, self.level)

        if schema_ref:
            self.this_section['schema_ref'] = schema_ref
            self.this_section['schema_name'] = self.traverser.get_schema_name(self.this_section['schema_ref'])

        self.sections.append(self.this_section)


    def add_description(self, text):
        """ Add the schema description """
        self.this_section['description'] = self.format_head_three(_('Description'), self.level) + self.formatter.para(text)


    def add_deprecation_text(self, deprecation_text):
        """ Add deprecation text for a schema """
        depr_text = self.formatter.italic(_('This schema has been deprecated and use in new implementations is discouraged except to retain compatibility with existing products.')) + ' ' + deprecation_text
        self.this_section['deprecation_text'] = depr_text + '\n'


    def add_uris(self, uris):
        """ Add the URIs (which should be a list) """
        uri_block = self.format_head_three(_('URIs'), self.level)
        for uri in sorted(uris, key=str.lower):
            uri_block += "\n" + self.format_uri(uri) + "<br>"
        self.this_section['uris'] = uri_block + "\n"


    def add_conditional_requirements(self, text):
        """ Add a conditional requirements, which should already be formatted """
        self.this_section['conditional_requirements'] = "\n**" + _('Conditional Requirements') + ":**\n\n" + text + "\n"


    def format_json_payload(self, json_payload):
        """ Format a json payload for output. """
        # Add markdown for formatting. Conditional because some inputs may provide it.
        if '```json' not in json_payload:
            json_payload = '```json\n' + json_payload.strip() + '\n```\n'
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
            heading = _('%(Name)s Registry v%(version_number)s+') % {'Name': reg_name, 'version_number': reg['minversion']}
            if reg.get('current_release', reg['minversion']) != reg['minversion']:
                heading += ' ' + (_('(current release: v%(version_number)s)') % {'version_number': reg['current_release']})

            this_section['heading'] = self.format_head_two(heading, self.level)
            this_section['requirement'] = _('Requirement: %(req)s') % {'req': reg.get('profile_requirement')}

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


    def escape_text(self, text, chars=None):
        """Escape text in whatever way is appropriate to this output format. """
        if chars is None:
            chars = []
        return self.escape_for_markdown(text, chars)


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
