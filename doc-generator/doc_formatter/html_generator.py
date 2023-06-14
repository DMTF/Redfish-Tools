# Copyright Notice:
# Copyright 2016-2022 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File : html_generator.py

Brief : Defines HtmlGenerator class.

Initial author: Second Rise LLC.
"""

import copy
import html
import markdown
import warnings
from doc_gen_util import DocGenUtilities
from format_utils import HtmlUtils
from . import DocFormatter
from . import ToCParser

class HtmlGenerator(DocFormatter):
    """Provides methods for generating markdown from Redfish schemas. """


    def __init__(self, property_data, traverser, config, level=0):
        super(HtmlGenerator, self).__init__(property_data, traverser, config, level)
        self.separators = {
            'inline': ', ',
            'linebreak': '<br>',
            'pattern': '\n\n' # This separator is applied prior to applying markdown_to_html
            }
        self.formatter = HtmlUtils()
        self.table_of_contents = ''
        self.css_content = """
<style>
 * {margin: 0; padding: 0;}
 body {font: 0.8125em Helvetica, sans-serif; color: #222; background: #FFF; width: 90%; margin: 2em auto;}
 h1, h3, h4{margin:1em 0 .5em;}
 h2 {margin: 2em 0 .5em;}
 h3 {
    border-bottom: 1px solid #000000
 }
 h4 {
    text-decoration: underline #000000
 }
 ul, ol {margin-left: 2em;}
 li {margin: 0 0 0.5em;
     word-break: break-all;}
 .hanging-indent {
      padding-left: 1em;
      text-indent: -1em;
 }
 p {margin: 0 0 0.5em;}
 div.toc {margin: 0 0 2em 0;}
 .toc ul {list-style-type: none;}
 ul.nobullet { list-style-type: none }
 table{
    max-width: 100%;
    background-color: transparent;
    border-collapse: separate;
    border-spacing: 0;
    margin-bottom: 1.25em;
    border: 1px solid #999999;
    border-width: 0 1px 1px 0;
 }
 td, th{
    padding: .5em;
    text-align: left;
    vertical-align: top;
    border: 1px solid #999999;
    border-width: 1px 0 0 1px;
}
table.properties{
    width: 100%;
}
table.uris tr td:nth-child(2) {
    word-break: break-all;
}
.property-details-content {
    margin-left: 5em;
}
pre.code{
    font-size: 1em;
    margin-left: 5em;
    color: #0000FF
}

.codehilite .hll { background-color: #ffffcc }
.codehilite  { background: #f8f8f8; }
.codehilite .c { color: #408080; font-style: italic } /* Comment */
.codehilite .err { border: 1px solid #FF0000 } /* Error */
.codehilite .k { color: #008000; font-weight: bold } /* Keyword */
.codehilite .o { color: #666666 } /* Operator */
.codehilite .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
.codehilite .cm { color: #408080; font-style: italic } /* Comment.Multiline */
.codehilite .cp { color: #BC7A00 } /* Comment.Preproc */
.codehilite .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
.codehilite .c1 { color: #408080; font-style: italic } /* Comment.Single */
.codehilite .cs { color: #408080; font-style: italic } /* Comment.Special */
.codehilite .gd { color: #A00000 } /* Generic.Deleted */
.codehilite .ge { font-style: italic } /* Generic.Emph */
.codehilite .gr { color: #FF0000 } /* Generic.Error */
.codehilite .gh { color: #000080; font-weight: bold } /* Generic.Heading */
.codehilite .gi { color: #00A000 } /* Generic.Inserted */
.codehilite .go { color: #888888 } /* Generic.Output */
.codehilite .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
.codehilite .gs { font-weight: bold } /* Generic.Strong */
.codehilite .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
.codehilite .gt { color: #0044DD } /* Generic.Traceback */
.codehilite .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
.codehilite .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
.codehilite .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
.codehilite .kp { color: #008000 } /* Keyword.Pseudo */
.codehilite .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
.codehilite .kt { color: #B00040 } /* Keyword.Type */
.codehilite .m { color: #666666 } /* Literal.Number */
.codehilite .s { color: #BA2121 } /* Literal.String */
.codehilite .na { color: #7D9029 } /* Name.Attribute */
.codehilite .nb { color: #008000 } /* Name.Builtin */
.codehilite .nc { color: #0000FF; font-weight: bold } /* Name.Class */
.codehilite .no { color: #880000 } /* Name.Constant */
.codehilite .nd { color: #AA22FF } /* Name.Decorator */
.codehilite .ni { color: #999999; font-weight: bold } /* Name.Entity */
.codehilite .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
.codehilite .nf { color: #0000FF } /* Name.Function */
.codehilite .nl { color: #A0A000 } /* Name.Label */
.codehilite .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
.codehilite .nt { color: #008000; font-weight: bold } /* Name.Tag */
.codehilite .nv { color: #19177C } /* Name.Variable */
.codehilite .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
.codehilite .w { color: #bbbbbb } /* Text.Whitespace */
.codehilite .mb { color: #666666 } /* Literal.Number.Bin */
.codehilite .mf { color: #666666 } /* Literal.Number.Float */
.codehilite .mh { color: #666666 } /* Literal.Number.Hex */
.codehilite .mi { color: #666666 } /* Literal.Number.Integer */
.codehilite .mo { color: #666666 } /* Literal.Number.Oct */
.codehilite .sa { color: #BA2121 } /* Literal.String.Affix */
.codehilite .sb { color: #BA2121 } /* Literal.String.Backtick */
.codehilite .sc { color: #BA2121 } /* Literal.String.Char */
.codehilite .dl { color: #BA2121 } /* Literal.String.Delimiter */
.codehilite .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
.codehilite .s2 { color: #BA2121 } /* Literal.String.Double */
.codehilite .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
.codehilite .sh { color: #BA2121 } /* Literal.String.Heredoc */
.codehilite .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
.codehilite .sx { color: #008000 } /* Literal.String.Other */
.codehilite .sr { color: #BB6688 } /* Literal.String.Regex */
.codehilite .s1 { color: #BA2121 } /* Literal.String.Single */
.codehilite .ss { color: #19177C } /* Literal.String.Symbol */
.codehilite .bp { color: #008000 } /* Name.Builtin.Pseudo */
.codehilite .fm { color: #0000FF } /* Name.Function.Magic */
.codehilite .vc { color: #19177C } /* Name.Variable.Class */
.codehilite .vg { color: #19177C } /* Name.Variable.Global */
.codehilite .vi { color: #19177C } /* Name.Variable.Instance */
.codehilite .vm { color: #19177C } /* Name.Variable.Magic */
.codehilite .il { color: #666666 } /* Literal.Number.Integer.Long */
</style>
"""

    def format_property_row(self, schema_ref, prop_name, prop_info, prop_path=[], in_array=False, as_action_parameters=False,
                                in_schema_ref=None):
        """Format information for a single property.

        Returns an object with 'row', 'details', 'action_details', and 'profile_conditional_details':

        'row': content for the main table being generated.
        'details': content for the Property Details section.
        'action_details': content for the Actions section.
        'profile_conditional_details': populated only in profile_mode, formatted conditional details

        This may include embedded objects with their own properties.
        """

        if not in_schema_ref:
            in_schema_ref = schema_ref

        traverser = self.traverser
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

        # If prop_path starts with Actions and is more than 1 deep, we are outputting for an Actions
        # section and should dial back the indentation by one level.
        if self.config.get('remove_blanks') != True:
            if len(prop_path) > 1 and prop_path[0] == 'Actions':
                indentation_string = '&nbsp;' * 6 * (current_depth -1)

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
        name_and_version = self.formatter.bold(html.escape(prop_name, False))

        if translated_name:
            name_and_version += ' ' + self.formatter.italic('(' + translated_name + ')')

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
                    'profile_conditional_details':formatted_details.get('profile_conditional_details')})

        # Eliminate dups in these these properties and join with a delimiter:
        props = {
            'prop_type': self.separators['inline'],
            'descr': self.separators['linebreak'],
            'object_description': '\n',
            'item_description': '\n'
            }

        for property_name, delim in props.items():
            if isinstance(formatted_details[property_name], list):
                property_values = []
                self.append_unique_values(formatted_details[property_name], property_values)
                formatted_details[property_name] = delim.join(property_values)

        if formatted_details['prop_is_object'] and not in_array:
            if formatted_details['object_description'] == '':
                name_and_version += ' { }'
            else:
                name_and_version += ' {'

        if formatted_details['prop_is_array']:
            if formatted_details['item_description'] == '':
                if formatted_details['array_of_objects']:
                    name_and_version += ' [ { } ]'
                else:
                    name_and_version += ' [ ] '
            else:
                if formatted_details['array_of_objects']:
                    name_and_version += ' [ {'
                else:
                    collapse_array = True
                    name_and_version += ' [ ] '
        elif in_array:
            if formatted_details['prop_is_object']:
                name_and_version += ' [ { } ]'
            else:
                name_and_version += ' [ ] '

        name_and_version = '<nobr>' + name_and_version  + '</nobr>'

        if formatted_details['descr'] is None:
            formatted_details['descr'] = ''

        if not formatted_details.get('verbatim_description', False):
            formatted_details['descr'] = self.formatter.markdown_to_html(html.escape(formatted_details['descr'], False), no_para=True)

        if formatted_details['add_link_text']:
            if formatted_details['descr']:
                formatted_details['descr'] += self.formatter.br()
            formatted_details['descr'] += self.formatter.italic(formatted_details['add_link_text'])

        # Append reference info to descriptions, if appropriate:
        if not formatted_details.get('fulldescription_override'):
            # If there are prop_details (enum details), add a note to the description:
            if formatted_details['has_direct_prop_details'] and not formatted_details['has_action_details']:
                if has_enum:
                    anchor = in_schema_ref + '|details|' + prop_name
                    text_descr = (_('For the possible property values, see %(link)s in Property details.') %
                                      {'link': '<a href="#' + anchor + '">' + prop_name + '</a>'})
                else:
                    text_descr = _('For more information about this property, see Property details.')
                if formatted_details['descr']:
                    formatted_details['descr'] += '<br>' + self.formatter.italic(text_descr)
                else:
                    formatted_details['descr'] = self.formatter.italic(text_descr)

            # If this is an Action with details, add a note to the description:
            if formatted_details['has_action_details']:
                anchor = in_schema_ref + '|action_details|' + prop_name
                text_descr = (_('For more information, see the %(link)s section below.') %
                                  {'link': '<a href="#' + anchor + '">' + _('Actions') + '</a>'})
                formatted_details['descr'] += '<br>' + self.formatter.italic(text_descr)

        if deprecated_descr:
            formatted_details['descr'] += ' ' + self.formatter.italic(deprecated_descr)

        prop_type = html.escape(formatted_details['prop_type'], False)
        if has_enum:
            prop_type += '<br>(enum)'
        if format_annotation:
            prop_type += '<br>(' + format_annotation + ')'
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
                    item_list = ', '.join([html.escape(x) for x in item_list])
                prop_type += '<br>(' + item_list + ')'

        prop_access = ''
        if (not formatted_details['prop_is_object']
                and not formatted_details.get('array_of_objects')
                and not as_action_parameters):
            if formatted_details['read_only']:
                prop_access = '<nobr>' + _('read-only') + '</nobr>'
            else:
                prop_access = '<nobr>' + _('read-write') + '</nobr>'

        if formatted_details['prop_required'] or formatted_details.get('required_parameter'):
            prop_access += ' <nobr>' + _('required') + '</nobr>'
        elif formatted_details['prop_required_on_create']:
            prop_access += ' <nobr>' + _('required on create') + '</nobr>'
        elif as_action_parameters:
            prop_access += ' ' + _('optional')

        if formatted_details['nullable']:
            prop_access += ' ' + _('(null)')

        # If profile reqs are present, massage them:
        profile_access = self.format_base_profile_access(formatted_details)

        descr = formatted_details['descr']
        if formatted_details['profile_purpose'] and self.config.get('profile_mode'):
            descr += '<br>' + self.formatter.bold(_('Profile Purpose: %(purpose)s') % {'purpose': formatted_details['profile_purpose']})

        # Conditional Requirements
        cond_req = formatted_details['profile_conditional_req']
        if cond_req:
            anchor = in_schema_ref + '|conditional_reqs|' + prop_name
            cond_req_text = (_('See %(link)s, below, for more information.') %
                                 {'link': '<a href="#' + anchor + '">' + _('Conditional Requirements') + '</a>'})
            descr += ' ' + self.formatter.nobr(self.formatter.italic(cond_req_text))
            profile_access += "<br>" + self.formatter.nobr(self.formatter.italic(_('Conditional Requirements')))

        if not profile_access:
            profile_access = '&nbsp;' * 10

        # Comparison
        if formatted_details['profile_values']:
            comparison_descr = (_('Must be %(comparison_word)s (%(values)s)') %
                                    {'comparison_word': formatted_details['profile_comparison'],
                                     'values': ', '.join('"' + x + '"' for x in formatted_details['profile_values'])})
            profile_access += '<br>' + self.formatter.italic(comparison_descr)

        row = []
        row.append(indentation_string + name_and_version)
        if self.config.get('profile_mode'):
            row.append(profile_access)
        row.append(prop_type)
        if not self.config.get('profile_mode'):
            row.append(prop_access)
        row.append(descr)

        formatted.append(self.formatter.make_row(row))

        if len(formatted_details['object_description']) > 0:
            formatted_object = formatted_details['object_description']
            # Add a closing } to the last row of this object.
            formatted_object = self._add_closing_brace(formatted_object, indentation_string, '}')
            formatted.append(formatted_object)

        if not collapse_array and len(formatted_details['item_description']) > 0:
            formatted_array = formatted_details['item_description']
            # Add closing }] or ] to the last row of this array:
            if formatted_details['array_of_objects']:
                formatted_array = self._add_closing_brace(formatted_array, indentation_string, '} ]')
            else:
                formatted_array = self._add_closing_brace(formatted_array, indentation_string, ']')
            formatted.append(formatted_array)

        return({'row': '\n'.join(formatted), 'details':formatted_details['prop_details'],
                'action_details':formatted_details.get('action_details'),
                'profile_conditional_details':formatted_details.get('profile_conditional_details')})


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

        if subset_mode and subset:
            supported_values = subset.get('SupportedValues')
            if supported_values:
                enum = [x for x in enum if x in supported_values]

        if prop_description:
            contents.append(self.formatter.para(prop_description))

        if isinstance(prop_type, list):
            prop_type = ', '.join([html.escape(x, False) for x in prop_type])
        else:
            prop_type = html.escape(prop_type, False)

        if supplemental_details:
            contents.append(self.formatter.markdown_to_html(supplemental_details))

        enum_translations = parent_prop_info.get('enumTranslations', {})

        if enum_details:
            headings = [prop_type, _('Description')]
            if profile_mode:
                headings.append(_('Profile Specifies'))
            header_row = self.formatter.make_header_row(headings)
            table_rows = []
            enum.sort(key=str.lower)

            for enum_item in enum:
                enum_name = html.escape(enum_item, False)
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
                        version_text = html.escape(version, False)
                        version_display = self.truncate_version(version_text, 2) + '+'

                if version_display:
                    if version_depr:
                        version_depr_text = html.escape(version_depr, False)
                        deprecated_display = self.truncate_version(version_depr_text, 2)
                        enum_name += ' ' + self.formatter.italic(_('(v%(version_number)s, deprecated v%(deprecated_version)s)') %
                                                                     {'version_number': version_display,
                                                                          'deprecated_version': deprecated_display})
                        if deprecated_descr:
                            deprecated_descr_text = html.escape(_('Deprecated in v%(version_number)s and later. %(explanation)s') %
                                                                    {'version_number': deprecated_display,
                                                                         'explanation': deprecated_descr})
                    else:
                        enum_name += ' ' + self.formatter.italic(_('(v%(version_number)s)') % {'version_number': version_display})
                elif version_depr:
                    version_depr_text = html.escape(version_depr, False)
                    deprecated_display = self.truncate_version(version_depr_text, 2)
                    enum_name += ' ' + self.formatter.italic(_('(deprecated v%(version_number)s)') % {'version_number': deprecated_display})
                    if deprecated_descr:
                        deprecated_descr_text = html.escape(_('Deprecated in v%(version_number)s and later. %(explanation)s') %
                                                                {'version_number': deprecated_display,
                                                                     'explanation': deprecated_descr})

                descr = html.escape(enum_details.get(enum_item, ''), False)
                if deprecated_descr:
                    if descr:
                        descr += ' ' + self.formatter.italic(deprecated_descr)
                    else:
                        descr = self.formatter.italic(deprecated_descr)
                cells = [enum_name, descr]

                if profile_mode:
                    if enum_item in profile_values:
                        cells.append(self.text_map('Mandatory'))
                    elif enum_item in profile_min_support_values:
                        cells.append(self.text_map('Mandatory'))
                    elif enum_item in profile_parameter_values:
                        cells.append(self.text_map('Mandatory'))
                    elif enum_item in profile_recommended_values:
                        cells.append(self.text_map('Recommended'))
                    else:
                        cells.append('')

                table_rows.append(self.formatter.make_row(cells))
            contents.append(self.formatter.make_table(table_rows, [header_row], 'enum enum-details'))

        elif enum:
            headings = [prop_type]
            if profile_mode:
                headings.append(_('Profile Specifies'))
            header_row = self.formatter.make_header_row(headings)
            table_rows = []
            enum.sort(key=str.lower)
            for enum_item in enum:
                enum_name = html.escape(enum_item, False)
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
                        version_depr_text = html.escape(version_depr, False)
                        deprecated_display = self.truncate_version(version_depr_text, 2)
                        enum_name += ' ' + self.formatter.italic(_('(v%(version_number)s, deprecated v%(deprecated_version)s)') %
                                                                     {'version_number': version_display,
                                                                          'explanation': deprecated_display})
                        if deprecated_descr:
                            enum_name += '<br>' + self.formatter.italic(html.escape(
                                _('Deprecated in v%(version_number)s and later. %(explanation)s') %
                                {'version_number': deprecated_display,
                                     'explanation': deprecated_descr}))
                    else:
                        enum_name += ' ' + self.formatter.italic(_('(v%(version_number)s)') % {'version_number': version_display})

                elif version_depr:
                    version_depr_text = html.escape(version_depr, False)
                    deprecated_display = self.truncate_version(version_depr_text, 2)
                    enum_name += ' ' + self.formatter.italic(_('(deprecated v%(version_number)s)') % {'version_number': deprecated_display})
                    if deprecated_descr:
                        enum_name += '<br>' + self.formatter.italic(html.escape(
                            _('Deprecated in v%(version_number)s and later. %(explanation)s') %
                            {'version_number': deprecated_display,
                                 'explanation': deprecated_descr}))


                cells = [enum_name]
                if profile_mode:
                    if enum_name in profile_values:
                        cells.append(self.text_map('Mandatory'))
                    elif enum_name in profile_min_support_values:
                        cells.append(self.text_map('Mandatory'))
                    elif enum_name in profile_parameter_values:
                        cells.append(self.text_map('Mandatory'))
                    elif enum_name in profile_recommended_values:
                        cells.append(self.text_map('Recommended'))
                    else:
                        cells.append('')

                table_rows.append(self.formatter.make_row(cells))
            contents.append(self.formatter.make_table(table_rows, [header_row], _('enum')))

        return '\n'.join(contents) + '\n'


    def format_action_parameters(self, schema_ref, prop_name, prop_descr, action_parameters, profile,
                                     version_strings=None, supplemental_details=None, subset=None):
        """Generate a formatted Actions section from parameter data. """

        formatted = []
        anchor = schema_ref + '|action_details|' + prop_name
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

        formatted.append(self.formatter.head_four(name_and_version, self.level, anchor))
        if deprecated_descr:
            formatted.append(self.formatter.para(italic(deprecated_descr)))
        formatted.append(self.formatter.para(prop_descr))

        if supplemental_details:
            formatted.append(self.formatter.markdown_to_html(supplemental_details))

        # Add the URIs for this action.
        formatted.append(self.format_uri_block_for_action(action_name, self.current_uris));

        param_names = []

        if action_parameters:
            rows = []
            # Add a "start object" row for this parameter:
            rows.append(self.formatter.make_row(['{', '','','']))

            param_names = [x for x in action_parameters.keys()]

            if self.config.get('subset_mode') and subset:
                supported_values = subset.get('SupportedValues')
                if supported_values:
                    param_names = [x for x in param_names if x in supported_values]

            param_names.sort(key=str.lower)

        if len(param_names):
            for param_name in param_names:
                formatted_parameters = self.format_property_row(schema_ref, param_name, action_parameters[param_name], ['Actions', prop_name], False, True)
                rows.append(formatted_parameters.get('row'))

            # Add a closing } to the last row:
            tmp_row = rows[-1]
            tmp_row = self._add_closing_brace(tmp_row, '', '}')
            rows[-1] = tmp_row

            formatted.append(self.formatter.para(_('Perform the action using a POST to the specific Action URI for this resource. Parameters for the action are passed in a JSON body and are defined as follows:')))

            formatted.append(self.formatter.make_table(rows))

        else:
            formatted.append(self.formatter.para(_('Perform the action using a POST to the specific Action URI for this resource. This action takes no parameters.')))

        return "\n".join(formatted)


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

            # something is awry if there are no properties
            if section.get('properties'):
                contents.append(self.formatter.make_table(section['properties'], None, 'properties'))

            if section.get('profile_conditional_details'):
                # sort them now; these can be sub-properties so may not be in alpha order.
                conditional_details = '\n'.join(sorted(section['profile_conditional_details'], key=str.lower))
                deets = []
                deets.append(self.formatter.head_three(_('Conditional Requirements'), self.level))
                deets.append(self.formatter.make_div(conditional_details, 'property-details-content'))
                contents.append(self.formatter.make_div('\n'.join(deets), 'property-details'))

            if len(section.get('action_details', [])):
                action_details = '\n'.join(section['action_details'])
                deets = []
                deets.append(self.formatter.head_three(_('Actions'), self.level))
                deets.append(self.formatter.make_div(action_details, 'property-details-content'))
                contents.append(self.formatter.make_div('\n'.join(deets), 'property-details'))
            if section.get('property_details'):
                deets = []
                deets.append(self.formatter.head_three(_('Property details'), self.level))
                # Sort and output property details
                detail_names = [x for x in section['property_details'].keys()]
                detail_names.sort(key=str.lower)
                deets_content = []
                for detail_name in detail_names:
                    det_info = section['property_details'][detail_name]
                    anchor = section['schema_ref'] + '|details|' + detail_name
                    deets_content.append(self.formatter.head_four(html.escape(detail_name, False), 0, anchor))

                    if len(det_info) == 1:
                        for x in det_info.values():
                            deets_content.append(x['formatted_descr'])
                    else:
                        path_to_ref = {}
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
                            deets_content.append(self.formatter.head_five(path_text, 0))
                            deets_content.append(info['formatted_descr'])

                deets.append(self.formatter.make_div('\n'.join(deets_content),
                                           'property-details-content'))
                contents.append(self.formatter.make_div('\n'.join(deets), 'property-details'))

            if section.get('json_payload'):
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
                contents.append(self.formatter.head_three(_('Messages'), self.level))
                message_rows = [self.formatter.make_row(x) for x in section['messages']]
                header_cells = ['', _('Requirement')]
                if self.config.get('profile_mode') != 'terse':
                    header_cells.append(_('Description'))
                header_row = self.formatter.make_row(header_cells)
                contents.append(self.formatter.make_table(message_rows, [header_row], 'messages'))

        contents = '\n'.join(contents)
        return contents


    def output_document(self):
        """Return full contents of document"""

        body = ''

        intro = self.config.get('intro_content')
        if intro:
            intro = self.process_intro(intro)
            body += intro

        body += self.emit()

        postscript = self.config.get('postscript_content')
        if postscript:
            body += self.formatter.markdown_to_html(postscript)

        common_properties = self.generate_common_properties_doc()
        marker = False
        if '<p>[insert_common_objects]</p>' in body:
            marker = '<p>[insert_common_objects]</p>'
        elif '[insert_common_objects]' in body:
            marker = '[insert_common_objects]'
        if marker:
            body = body.replace(marker, common_properties, 1)
        else:
            if common_properties:
                warnings.warn('Boilerplate lacks "[insert_common_objects]" marker. Common object properties were found but will be omitted.')


        marker = False
        if '<p>[insert_collections]</p>' in body:
            marker = '<p>[insert_collections]</p>'
        elif '[insert_collections]' in body:
            marker = '[insert_collections]'
        if marker:
            collections_doc = self.generate_collections_doc()
            body = body.replace(marker, collections_doc, 1)

        if self.config.get('add_toc'):
            toc = self.generate_toc(body)
            if '[add_toc]' in body:
                body = body.replace('[add_toc]', toc, 1)
            else:
                body = toc + body

        # Replace pagebreak markers with pagebreak markup
        body = body.replace('~pagebreak~', '<p style="page-break-before: always"></p>')

        doc_title = self.config.get('html_title', '')

        headlines = ['<head>', '<meta charset="utf-8"/>', '<title>' + doc_title + '</title>']
        styles = self.css_content
        headlines.append(styles)
        headlines.append('</head>')
        head = '\n'.join(headlines)
        return '\n'.join(['<!DOCTYPE html>', '<html>', head, '<body>', body, '</body></html>'])


    def generate_toc(self, html_blob):
        """ Generate a TOC for an HTML blob (probably the body of this document) """

        toc = ''
        levels = ['h1', 'h2']
        parser = ToCParser(levels)
        parser.feed(html_blob)
        toc_data = parser.close()

        current_level = 0
        for entry in toc_data:
            level = levels.index(entry['level'])
            if level > current_level:
                toc += "<ul>\n"
            if level < current_level:
                toc += "</ul>\n"
            current_level = level

            toc += "<li>" + '<a href="#' + entry['link_id'] +'">' + entry['text'] + "</a></li>\n"

        while current_level > 0:
            current_level = current_level - 1
            toc += "</ul>\n"

        toc = '<div class="toc">' + "<ul>\n" + toc + "</ul>\n</div>\n"

        return toc


    def process_intro(self, intro_blob):
        """ Process the Intro markdown, pulling in any schema fragments """

        parts = []
        intro = []
        part_text = []

        fragment_config = {
            'output_format': 'html',
            'normative': self.config.get('normative'),
            'cwd': self.config.get('cwd'),
            'schema_supplement': {},
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
                intro.append(self.formatter.markdown_to_html(part['content']))
            elif part['type'] == 'fragment':
                intro.append(part['content'])
        return '\n'.join(intro)


    def add_section(self, text, link_id=False, schema_ref=False):
        """ Add a container for all the information in a section """

        self.this_section = {
            'properties': [],
            'property_details': {},
            'head': '',
            'heading': '',
            'schema_ref': '',
            'schema_name': '',
            }

        if text:
            section_text = html.escape(text, False)
            self.this_section['head'] = text
            self.this_section['heading'] = self.formatter.head_two(section_text, self.level, link_id)
            self.this_section['link_id'] = link_id
        if schema_ref:
            self.this_section['schema_ref'] = schema_ref
            self.this_section['schema_name'] = self.traverser.get_schema_name(self.this_section['schema_ref'])
        elif text:
            self.this_section['schema_ref'] = section_text
        self.sections.append(self.this_section)


    def add_description(self, text):
        """ Add the schema description """
        self.this_section['description'] = self.formatter.markdown_to_html(text)


    def add_deprecation_text(self, deprecation_text):
        """ Add deprecation text for a schema """
        depr_text = self.formatter.markdown_to_html(deprecation_text, no_para=True)
        depr_text = self.formatter.italic(_('This schema has been deprecated and use in new implementations is discouraged except to retain compatibility with existing products.')) + ' ' + depr_text
        self.this_section['deprecation_text'] = depr_text


    def add_uris(self, uris, urisDeprecated):
        """ Add the URIs (which should be a list) """
        uri_strings = []
        
        for i in range(len(uris)):
            if uris[i] in urisDeprecated:
                uris[i] += _(" (deprecated)")
        
        # if resource block-related URIs are in the list, omit them for brevity
        has_resource_block_uris = False
        for uri in sorted(uris, key=str.lower):
            if '{ResourceBlockId}/' in uri:
                has_resource_block_uris = True
            else:
                uri_strings.append('<li class="hanging-indent">' + self.format_uri(uri) + '</li>')

        # if resource block-related URIs have been trimmed, add a note 
        if has_resource_block_uris:
            uri_strings.append('<li class="hanging-indent">' + "* " +
                _("Note: Resource block-related URIs have been omitted from this list") + '\n</li>')

        uri_block = '<ul class="nobullet">' + '\n'.join(uri_strings) + '</ul>'
        uri_content = '<h4>' + _('URIs:') + '</h4>' + uri_block
        self.this_section['uris'] = uri_content


    def add_conditional_requirements(self, text):
        """ Add a conditional requirements, which should already be formatted """
        self.this_section['conditional_requirements'] = '<h4>' + _('Conditional Requirements:') + '</h4>' + text


    def format_uri(self, uri):
        """ Format a URI for output. Includes creating links to Id'd schemas """

        uri_parts = uri.split('/')
        uri_parts_highlighted = []
        for part in uri_parts:
            if part.startswith('{') and part.endswith('}'):
                # Look up the schema and create a link, if documented.
                if part.endswith('Id}'):
                    schema_name = part[1:-3]
                    if self.get_ref_for_documented_schema_name(schema_name):
                        part = '<a href="#' + schema_name + '">' + part + '</a>'

                # and italicize it
                part = self.formatter.italic(part)
            uri_parts_highlighted.append(part)
        uri_highlighted = '/\u200b'.join(uri_parts_highlighted)
        return uri_highlighted


    def format_uris_for_table(self, uris):
        """ Format a bunch of uris to go into a table cell """
        return ''.join(['<div class="hanging-indent">' + self.format_uri(x) + '</div>'
                            for x in sorted(uris, key=str.lower)])


    def format_json_payload(self, json_payload):
        """ Format a json payload for output. """
        # Add markdown for formatting. Conditional because some inputs may provide it.
        if '```json' not in json_payload:
            json_payload = '```json\n' + json_payload.strip() + '\n```\n'
        return ('<div class="json-payload">' +
                    self.formatter.markdown_to_html(json_payload) + '</div>')


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
            heading = reg_name + ' ' + (_('Registry v%(version_number)s+') % {'version_number': reg['minversion']})
            if reg.get('current_release', reg['minversion']) != reg['minversion']:
                heading += ' ' + (_('(current release: v%(version_number)s)') % {'version_number': reg['current_release']})

            this_section['heading'] = self.formatter.head_two(heading, self.level)
            this_section['requirement'] = _('Requirement: %(req)s') % {'req': reg.get('profile_requirement', '')}

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


    def format_as_prop_details(self, prop_name, prop_description, rows):
        """ Take the formatted rows and other strings from prop_info, and create a formatted block suitable for the prop_details section """
        contents = []

        if prop_description:
            contents.append(self.formatter.para(prop_description))

        obj_table = self.formatter.make_table(rows)
        contents.append(obj_table)

        return "\n".join(contents)


    def link_to_own_schema(self, schema_ref, schema_uri):
        """ Provide a link to schema_ref, preferring an in-document link to the schema_uri. """
        schema_name = self.traverser.get_schema_name(schema_ref)
        if not schema_name:
            schema_name = schema_ref

        if self.is_documented_schema(schema_ref):
            return '<a href="#' + schema_name + '">' + schema_name + '</a>'
        else:
            return '<a href="' + schema_uri + '" target="_blank">' + schema_name + '</a>'

        return schema_name


    def link_to_common_property(self, ref_key):
        """ String for output, with actual links. """
        ref_info = self.common_properties.get(ref_key)
        if ref_info and ref_info.get('_prop_name'):
            ref_id = 'common-properties-' + ref_info.get('_prop_name')
            # Get the version as well.
            version = ref_info.get('_latest_version')
            if not version:
                version = DocGenUtilities.get_ref_version(ref_info.get('_ref_uri', ''))
            if version:
                ref_id += '_v' + version
            return '<a href="#' + ref_id + '">' + ref_info.get('_prop_name') + '</a>'
        return ref_key


    def link_to_outside_schema(self, uri):
        """ Provide a link to a scheme in another namespace """
        return '<a href="' + uri + '" target="_blank">' + uri + '</a>'


    def link_to_anchor(self, text, anchor):
        """ Link to arbitrary same-page anchor """
        return '<a href="#' + anchor + '">' + text + '</a>'


    def get_documentation_link(self, ref_uri):
        """ Provide a link to documentation, if provided """

        target = self.get_documentation_uri(ref_uri)
        if target:
            return _('See %(link)s') % {'link': '<a href="' + target + '" target="_blank">' + target + '</a>'}
        return False


    def add_object_close(self, rows, indentation_string, brace_string, num_cols):
        """ Modify rows with whatever we use to close an object in this format """
        tmp_row = rows[-1]
        tmp_row = self._add_closing_brace(tmp_row, '', '}')
        rows[-1] = tmp_row
        return rows


    def _add_closing_brace(self, html_blob, indentation_string, brace_string):
        """ Add a closing } to the last row of this blob of rows. """
        close_str = '<br>' + indentation_string + brace_string
        tmp_rows = html_blob.rsplit('<tr>', 1)
        if (len(tmp_rows) == 2):
            tmp_rows[1] = tmp_rows[1].replace('</td>', close_str + '</td>', 1)
            html_blob = '<tr>'.join(tmp_rows)
        return html_blob


    def escape_text(self, text, chars=None):
        """Escape text in whatever way is appropriate to this output format. """
        return html.escape(text, False)
