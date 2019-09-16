# Copyright Notice:
# Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.
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

# Format user warnings simply
def simple_warning_format(message, category, filename, lineno, file=None, line=None):
    """ a basic format for warnings from this program """
    return '  Warning: %s (%s:%s)' % (message, filename, lineno) + "\n"

warnings.formatwarning = simple_warning_format


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

    def format_property_row(self, schema_ref, prop_name, prop_info, prop_path=[], in_array=False):
        """Format information for a single property.

        Returns an object with 'row', 'details', 'action_details', and 'profile_conditional_details':

        'row': content for the main table being generated.
        'details': content for the Property Details section.
        'action_details': content for the Actions section.
        'profile_conditional_details': populated only in profile_mode, formatted conditional details

        This may include embedded objects with their own properties.
        """

        traverser = self.traverser
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

        version_added = None
        version_deprecated = None
        version_deprecated_explanation = ''
        if isinstance(prop_info, list):
            version_added = prop_info[0].get('versionAdded')
            version_deprecated = prop_info[0].get('versionDeprecated')
            version_deprecated_explanation = prop_info[0].get('deprecated')
            has_enum = 'enum' in prop_info[0]
            is_excerpt = prop_info[0].get('_is_excerpt') or prop_info[0].get('excerptCopy')
        elif isinstance(prop_info, dict):
            version_added = prop_info.get('versionAdded')
            version_deprecated = prop_info.get('versionDeprecated')
            version_deprecated_explanation = prop_info.get('deprecated')
            has_enum = 'enum' in prop_info
            is_excerpt = prop_info.get('_is_excerpt')

        name_and_version = self.formatter.bold(html.escape(prop_name, False))
        deprecated_descr = None

        version = version_depr = None
        if version_added:
            version = self.format_version(version_added)
        if version_deprecated:
            version_depr = self.format_version(version_deprecated)
        self.current_version[current_depth] = version

        # Don't display version if there is a parent version and this is not newer:
        if version and self.current_version.get(parent_depth):
            if DocGenUtilities.compare_versions(version, self.current_version.get(parent_depth)) <= 0:
                version = None

        if version and version != '1.0.0':
            version_text = html.escape(version, False)
            version_display = self.truncate_version(version_text, 2) + '+'
            if version_deprecated:
                version_depr_text = html.escape(version_depr, False)
                deprecated_display = self.truncate_version(version_depr_text, 2)
                name_and_version += ' ' + self.formatter.italic('(v' + version_display +
                                                      ', deprecated v' + deprecated_display +  ')')
                deprecated_descr = html.escape("Deprecated in v" + deprecated_display + ' and later. ' +
                                                   version_deprecated_explanation, False)
            else:
                name_and_version += ' ' + self.formatter.italic('(v' + version_display + ')')
        elif version_deprecated:
            version_depr_text = html.escape(version_depr, False)
            deprecated_display = self.truncate_version(version_depr_text, 2)
            name_and_version += ' ' + self.formatter.italic('(deprecated v' + deprecated_display +  ')')
            deprecated_descr = html.escape( "Deprecated in v" + deprecated_display + ' and later. ' +
                                                version_deprecated_explanation, False)

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
                    anchor = schema_ref + '|details|' + prop_name
                    text_descr = 'For the possible property values, see <a href="#' + anchor + '">' + prop_name + '</a> in Property Details.'
                else:
                    text_descr = 'For more information about this property, see Property Details.'
                if formatted_details['descr']:
                    formatted_details['descr'] += '<br>' + self.formatter.italic(text_descr)
                else:
                    formatted_details['descr'] = self.formatter.italic(text_descr)

            # If this is an Action with details, add a note to the description:
            if formatted_details['has_action_details']:
                anchor = schema_ref + '|action_details|' + prop_name
                text_descr = 'For more information, see the <a href="#' + anchor + '">Actions</a> section below.'
                formatted_details['descr'] += '<br>' + self.formatter.italic(text_descr)

        if deprecated_descr:
            formatted_details['descr'] += ' ' + self.formatter.italic(deprecated_descr)

        prop_type = html.escape(formatted_details['prop_type'], False)
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
                    item_list = ', '.join([html.escape(x) for x in item_list])
                prop_type += '<br>(' + item_list + ')'

        prop_access = ''
        if (not formatted_details['prop_is_object']
                and not formatted_details.get('array_of_objects')):
            if formatted_details['read_only']:
                prop_access = '<nobr>read-only</nobr>'
            else:
                # Special case for subset mode; if profile indicates WriteRequirement === None (present and None),
                # emit read-only.
                if ((self.config.get('profile_mode') == 'subset')
                        and formatted_details.get('profile_write_req')
                        and (formatted_details['profile_write_req'] == 'None')):
                        prop_access = '<nobr>read-only</nobr>'
                else:
                    prop_access = '<nobr>read-write</nobr>'

        if formatted_details['prop_required'] or formatted_details.get('required_parameter'):
            prop_access += ' <nobr>required</nobr>'
        elif formatted_details['prop_required_on_create']:
            prop_access += ' <nobr>required on create</nobr>'

        if formatted_details['nullable']:
            prop_access += ' (null)'

        # If profile reqs are present, massage them:
        profile_access = self.format_base_profile_access(formatted_details)

        descr = formatted_details['descr']
        if formatted_details['profile_purpose'] and (self.config.get('profile_mode') != 'subset'):
            descr += '<br>' + self.formatter.bold("Profile Purpose: " + formatted_details['profile_purpose'])

        # Conditional Requirements
        cond_req = formatted_details['profile_conditional_req']
        if cond_req:
            anchor = schema_ref + '|conditional_reqs|' + prop_name
            cond_req_text = 'See <a href="#' + anchor + '"> Conditional Requirements</a>, below, for more information.'
            descr += ' ' + self.formatter.nobr(self.formatter.italic(cond_req_text))
            profile_access += "<br>" + self.formatter.nobr(self.formatter.italic('Conditional Requirements'))

        if not profile_access:
            profile_access = '&nbsp;' * 10

        # Comparison
        if formatted_details['profile_values']:
            comparison_descr = ('Must be ' + formatted_details['profile_comparison'] + ' ('
                                + ', '.join('"' + x + '"' for x in formatted_details['profile_values'])
                                + ')')
            profile_access += '<br>' + self.formatter.italic(comparison_descr)

        row = []
        row.append(indentation_string + name_and_version)
        if self.config.get('profile_mode') and self.config.get('profile_mode') != 'subset':
            row.append(profile_access)
        row.append(prop_type)
        if not self.config.get('profile_mode') or self.config.get('profile_mode') == 'subset':
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
                                    supplemental_details, parent_prop_info, anchor=None, profile=None):
        """Generate a formatted table of enum information for inclusion in Property Details."""

        contents = []
        contents.append(self.formatter.head_four(html.escape(prop_name, False) + ':', self.level, anchor))

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
            contents.append(self.formatter.para(prop_description))

        if isinstance(prop_type, list):
            prop_type = ', '.join([html.escape(x, False) for x in prop_type])
        else:
            prop_type = html.escape(prop_type, False)

        if supplemental_details:
            contents.append(self.formatter.markdown_to_html(supplemental_details))

        if enum_details:
            headings = [prop_type, 'Description']
            if profile_mode and profile_mode != 'subset':
                headings.append('Profile Specifies')
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
                if parent_prop_info.get('enumVersionDeprecated'):
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
                        enum_name += ' ' + self.formatter.italic('(v' + version_display + ', deprecated v' + deprecated_display + ')')
                        if deprecated_descr:
                            deprecated_descr_text = html.escape('Deprecated in v' + deprecated_display
                                                                    + ' and later. ' + deprecated_descr)
                    else:
                        enum_name += ' ' + self.formatter.italic('(v' + version_display + ')')
                elif version_depr:
                    version_depr_text = html.escape(version_depr, False)
                    deprecated_display = self.truncate_version(version_depr_text, 2)
                    enum_name += ' ' + self.formatter.italic('(deprecated v' + deprecated_display + ')')
                    if deprecated_descr:
                        deprecated_descr_text = html.escape('Deprecated in v' + deprecated_display + ' and later. ' +
                                                        deprecated_descr)

                descr = html.escape(enum_details.get(enum_item, ''), False)
                if deprecated_descr:
                    if descr:
                        descr += ' ' + self.formatter.italic(deprecated_descr)
                    else:
                        descr = self.formatter.italic(deprecated_descr)
                cells = [enum_name, descr]

                if profile_mode and profile_mode != 'subset':
                    if enum_name in profile_values:
                        cells.append('Required')
                    elif enum_name in profile_min_support_values:
                        cells.append('Required')
                    elif enum_name in profile_parameter_values:
                        cells.append('Required')
                    elif enum_name in profile_recommended_values:
                        cells.append('Recommended')
                    else:
                        cells.append('')

                table_rows.append(self.formatter.make_row(cells))
            contents.append(self.formatter.make_table(table_rows, [header_row], 'enum enum-details'))

        elif enum:
            headings = [prop_type]
            if profile_mode and profile_mode != 'subset':
                headings.append('Profile Specifies')
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
                        enum_name += ' ' + self.formatter.italic('(v' + version_display + ', deprecated v' + deprecated_display + ')')
                        if deprecated_descr:
                            enum_name += '<br>' + self.formatter.italic(html.escape(
                                'Deprecated in v' + deprecated_display
                                + ' and later. ' + deprecated_descr))
                    else:
                        enum_name += ' ' + self.formatter.italic('(v' + version_display + ')')

                elif version_depr:
                    version_depr_text = html.escape(version_depr, False)
                    deprecated_display = self.truncate_version(version_depr_text, 2)
                    enum_name += ' ' + self.formatter.italic('(deprecated v' + deprecated_display + ')')
                    if deprecated_descr:
                        enum_name += '<br>' + self.formatter.italic(html.escape(
                            'Deprecated in v' + deprecated_display + ' and later. ' +
                            deprecated_descr))


                cells = [enum_name]
                if profile_mode and profile_mode != 'subset':
                    if enum_name in profile_values:
                        cells.append('Required')
                    elif enum_name in profile_min_support_values:
                        cells.append('Required')
                    elif enum_name in profile_parameter_values:
                        cells.append('Required')
                    elif enum_name in profile_recommended_values:
                        cells.append('Recommended')
                    else:
                        cells.append('')

                table_rows.append(self.formatter.make_row(cells))
            contents.append(self.formatter.make_table(table_rows, [header_row], 'enum'))

        return '\n'.join(contents) + '\n'


    def format_action_details(self, prop_name, action_details):
        """Generate a formatted Actions section from supplemental markup."""

        contents = []
        contents.append(self.formatter.head_four(action_details.get('action_name', prop_name), self.level))
        contents.append(self.formatter.markdown_to_html(action_details.get('text', '')))
        if action_details.get('example'):
            example = '```json\n' + action_details['example'] + '\n```\n'
            contents.append(self.formatter.para('Example Action POST:'))
            contents.append(self.formatter.markdown_to_html(example))

        return '\n'.join(contents) + '\n'

    def format_action_parameters(self, schema_ref, prop_name, prop_descr, action_parameters, profile):
        """Generate a formatted Actions section from parameter data. """

        formatted = []
        anchor = schema_ref + '|action_details|' + prop_name

        action_name = prop_name
        if prop_name.startswith('#'): # expected
            # Example: from #Bios.ResetBios, we want prop_name "ResetBios" and action_name "Bios.ResetBios"
            prop_name_parts = prop_name.split('.')
            prop_name = prop_name_parts[-1]
            action_name = action_name[1:]

        formatted.append(self.formatter.head_four(prop_name, self.level, anchor))
        formatted.append(self.formatter.para(prop_descr))

        # Add the URIs for this action.
        formatted.append(self.format_uri_block_for_action(action_name, self.current_uris));

        param_names = []

        if action_parameters:
            rows = []
            # Add a "start object" row for this parameter:
            rows.append(self.formatter.make_row(['{', '','','']))

            param_names = [x for x in action_parameters.keys()]

            if self.config.get('profile_mode') == 'subset':
                if profile.get('Parameters'):
                    param_names = [x for x in profile['Parameters'].keys() if x in param_names]
                else:
                    # Pluck out just the parameters that are required by the schema
                    required_param_names = []
                    for x in param_names:
                        param_deets = action_parameters[x]
                        if isinstance(param_deets, list):
                            if param_deets[0].get('required_parameter'):
                                required_param_names.append(x)
                        else:
                            if param_deets.get('required_parameter'):
                                required_param_names.append(x)
                    param_names = required_param_names

            param_names.sort(key=str.lower)

        if len(param_names):
            for param_name in param_names:
                formatted_parameters = self.format_property_row(schema_ref, param_name, action_parameters[param_name], ['Actions', prop_name])
                rows.append(formatted_parameters.get('row'))

            # Add a closing } to the last row:
            tmp_row = rows[-1]
            tmp_row = self._add_closing_brace(tmp_row, '', '}')
            rows[-1] = tmp_row

            formatted.append(self.formatter.para('The following table shows the parameters for the action that are included in the POST body to the URI shown in the "target" property of the Action.'))

            formatted.append(self.formatter.make_table(rows))

        else:
            formatted.append(self.formatter.para("(This action takes no parameters.)"))

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
                deets.append(self.formatter.head_three('Conditional Requirements', self.level))
                deets.append(self.formatter.make_div(conditional_details, 'property-details-content'))
                contents.append(self.formatter.make_div('\n'.join(deets), 'property-details'))

            if len(section.get('action_details', [])):
                action_details = '\n'.join(section['action_details'])
                deets = []
                deets.append(self.formatter.head_three('Actions', self.level))
                deets.append(self.formatter.make_div(action_details, 'property-details-content'))
                contents.append(self.formatter.make_div('\n'.join(deets), 'property-details'))
            if section.get('property_details'):
                deets = []
                deets.append(self.formatter.head_three('Property Details', self.level))
                deets.append(self.formatter.make_div('\n'.join(section['property_details']),
                                           'property-details-content'))
                contents.append(self.formatter.make_div('\n'.join(deets), 'property-details'))

            if section.get('json_payload'):
                contents.append(self.formatter.head_three('Example Response', self.level))
                contents.append(section['json_payload'])

        self.sections = []

        # Profile output may include registry sections
        for section in self.registry_sections:
            contents.append(section.get('heading'))
            contents.append(section.get('requirement'))
            if section.get('description'):
                contents.append(self.formatter.para(section['description']))
            if section.get('messages'):
                contents.append(self.formatter.head_three('Messages', self.level))
                message_rows = [self.formatter.make_row(x) for x in section['messages']]
                header_cells = ['', 'Requirement']
                if self.config.get('profile_mode') != 'terse':
                    header_cells.append('Description')
                header_row = self.formatter.make_row(header_cells)
                contents.append(self.formatter.make_table(message_rows, [header_row], 'messages'))

        contents = '\n'.join(contents)
        return contents


    def output_document(self):
        """Return full contents of document"""

        supplemental = self.config.get('supplemental', {})
        body = ''

        intro = supplemental.get('Introduction')
        if intro:
            intro = self.process_intro(intro)
            body += intro

        body += self.emit()

        if 'Postscript' in supplemental:
            body += self.formatter.markdown_to_html(supplemental['Postscript'])

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
                warnings.warn('Supplemental file lacks "[insert_common_objects]" marker. Common object properties were found but will be omitted.')


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

        doc_title = supplemental.get('Title')
        if not doc_title:
            doc_title = ''

        headlines = ['<head>', '<meta charset="utf-8">', '<title>' + doc_title + '</title>']
        styles = self.css_content
        headlines.append(styles)
        headlines.append('</head>')
        head = '\n'.join(headlines)
        return '\n'.join(['<!doctype html>', '<html>', head, '<body>', body, '</body></html>'])


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
                intro.append(self.formatter.markdown_to_html(part['content']))
            elif part['type'] == 'fragment':
                intro.append(part['content'])
        return '\n'.join(intro)


    def add_section(self, text, link_id=False):
        """ Add a top-level heading """

        self.this_section = {
            'properties': [],
            'property_details': [],
            'head': '',
            'heading': ''
            }

        if text:
            section_text = html.escape(text, False)

            self.this_section['head'] = text
            self.this_section['heading'] = self.formatter.head_two(section_text, self.level, link_id)
            self.this_section['link_id'] = link_id

        self.sections.append(self.this_section)


    def add_description(self, text):
        """ Add the schema description """
        self.this_section['description'] = self.formatter.markdown_to_html(text)


    def add_uris(self, uris):
        """ Add the URIs (which should be a list) """
        uri_strings = []
        for uri in sorted(uris, key=str.lower):
            uri_strings.append('<li class="hanging-indent">' + self.format_uri(uri) + '</li>')

        uri_block = '<ul class="nobullet">' + '\n'.join(uri_strings) + '</ul>'
        uri_content = '<h4>URIs:</h4>' + uri_block
        self.this_section['uris'] = uri_content


    def add_conditional_requirements(self, text):
        """ Add a conditional requirements, which should already be formatted """
        self.this_section['conditional_requirements'] = '<h4>Conditional Requirements:</h4>' + text


    def format_uri_block_for_action(self, action, uris):
        """ Create a URI block for this action & the resource's URIs """
        uri_strings = []
        for uri in sorted(uris, key=str.lower):
            uri = uri + "/Actions/" + action
            uri = uri.replace('/', '/\u200b')
            uri_strings.append('<li class="hanging-indent">' + self.format_uri(uri) + '</li>')

        uri_block = '<ul class="nobullet">' + '\n'.join(uri_strings) + '</ul>'
        uri_content = '<h5>URIs:</h5>' + uri_block
        return uri_content


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
        return ('<div class="json-payload">' +
                    self.formatter.markdown_to_html(json_payload) + '</div>')


    def add_property_row(self, formatted_text):
        """Add a row (or group of rows) for an individual property in the current section/schema.

        formatted_row should be a chunk of text already formatted for output"""
        self.this_section['properties'].append(formatted_text)


    def add_property_details(self, formatted_details):
        """Add a chunk of property details information for the current section/schema."""
        self.this_section['property_details'].append(formatted_details)


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

            this_section['heading'] = self.formatter.head_two(heading, self.level)
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
        """ String for output. Override in HTML formatter to get actual links. """
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


    def get_documentation_link(self, ref_uri):
        """ Provide a link to documentation, if provided """

        target = self.get_documentation_uri(ref_uri)
        if target:
            return 'See <a href="' + target + '" target="_blank">' + target + '</a>'
        return False

    def _add_closing_brace(self, html_blob, indentation_string, brace_string):
        """ Add a closing } to the last row of this blob of rows. """
        close_str = '<br>' + indentation_string + brace_string
        tmp_rows = html_blob.rsplit('<tr>', 1)
        if (len(tmp_rows) == 2):
            tmp_rows[1] = tmp_rows[1].replace('</td>', close_str + '</td>', 1)
            html_blob = '<tr>'.join(tmp_rows)
        return html_blob
