"""
File : html_generator.py

Brief : Defines HtmlGenerator class.

Initial author: Second Rise LLC.


The Distributed Management Task Force (DMTF) grants rights under copyright in
this software on the terms of the BSD 3-Clause License as set forth below; no
other rights are granted by DMTF. This software might be subject to other rights
(such as patent rights) of other parties.

Copyrights.

Copyright (c) 2016, Contributing Member(s) of Distributed Management Task Force,
Inc.. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.

    Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

    Neither the name of the Distributed Management Task Force (DMTF) nor the
    names of its contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Patents.

This software may be subject to third party patent rights, including provisional
patent rights ("patent rights"). DMTF makes no representations to users of the
standard as to the existence of such rights, and is not responsible to
recognize, disclose, or identify any or all such third party patent right,
owners or claimants, nor for any incomplete or inaccurate identification or
disclosure of such rights, owners or claimants. DMTF shall have no liability to
any party, in any manner or circumstance, under any legal theory whatsoever, for
failure to recognize, disclose, or identify any such third party patent rights,
or for such party’s reliance on the software or incorporation thereof in its
product, protocols or testing procedures. DMTF shall have no liability to any
party using such software, whether such use is foreseeable or not, nor to any
patent owner or claimant, and shall have no liability or responsibility for
costs or losses incurred if software is withdrawn or modified after publication,
and shall be indemnified and held harmless by any party using the software from
any and all claims of infringement by a patent owner for such use.

DMTF Members that contributed to this software source code might have made
patent licensing commitments in connection with their participation in the DMTF.
For details, see http://dmtf.org/sites/default/files/patent-10-18-01.pdf and
http://www.dmtf.org/about/policies/disclosures.
"""
import html
import markdown
from . import DocFormatter

class HtmlGenerator(DocFormatter):
    """Provides methods for generating markdown from Redfish schemas. """


    def __init__(self, property_data, traverser, config, level=0):
        super(HtmlGenerator, self).__init__(property_data, traverser, config, level)
        self.sections = []
        self.separators = {
            'inline': ', ',
            'linebreak': '<br>'
            }
        self.css_content = """
<style>
 * {margin: 0; padding: 0;}
 body {font: 0.8125em Helvetica, sans-serif; color: #222; background: #FFF; width: 90%; margin: 2em auto;}
 h1, h2, h3, h4{margin:1em 0 .5em;}
 h3 {
    border-bottom: 1px solid #000000
 }
 h4 {
    text-decoration: underline #000000
 }
 ul, ol {margin-left: 2em;}
 li {margin: 0 0 0.5em;}
 p {margin: 0 0 0.5em;}
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


    def format_property_row(self, schema_name, prop_name, prop_info, meta=None, current_depth=0):
        """Format information for a single property.

        Returns an object with 'row', 'details', and 'action_details':

        'row': content for the main table being generated.
        'details': content for the Property Details section.
        'action_details': content for the Actions section.

        This may include embedded objects with their own properties.
        """

        traverser = self.traverser
        formatted = []     # The row itself
        indentation_string = '&nbsp;' * 6 * current_depth

        if not meta:
            meta = {}

        name_and_version = self.bold(html.escape(prop_name, False))
        if 'version' in meta:
            version_text = html.escape(meta['version'], False)
            version_display = self.truncate_version(version_text, 2) + '+'
            if 'version_deprecated' in meta:
                version_depr = html.escape(meta['version_deprecated'], False)
                deprecated_display = self.truncate_version(version_depr, 2)
                name_and_version += ' ' + self.italic('(v' + version_display +
                                                      ', deprecated v' + deprecated_display +  ')')
            else:
                name_and_version += ' ' + self.italic('(v' + version_display + ')')
        elif 'version_deprecated' in meta:
            version_depr = html.escape(meta['version_deprecated'], False)
            deprecated_display = self.truncate_version(version_depr, 2)
            name_and_version += ' ' + self.italic('(deprecated v' + deprecated_display +  ')')

        formatted_details = self.parse_property_info(schema_name, prop_name, traverser,
                                                     prop_info, current_depth)

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
                for val in formatted_details[property_name]:
                    if val and val not in property_values:
                        property_values.append(val)
                formatted_details[property_name] = delim.join(property_values)

        if formatted_details['prop_is_object']:
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
                    name_and_version += ' [ '

        formatted_details['descr'] = html.escape(formatted_details['descr'], False)
        if formatted_details['add_link_text']:
            if formatted_details['descr']:
                formatted_details['descr'] += ' '
            formatted_details['descr'] += formatted_details['add_link_text']

        # If there are prop_details (enum details), add a note to the description:
        if formatted_details['has_direct_prop_details']:
            text_descr = 'See Property Details, below, for more information about this property.'
            formatted_details['descr'] += '<br>' + self.italic(text_descr)

        # If this is an Action with details, add a note to the description:
        if formatted_details['has_action_details']:
            text_descr = 'For more information, see the Action Details section below.'
            formatted_details['descr'] += '<br>' + self.italic(text_descr)

        prop_type = html.escape(formatted_details['prop_type'], False)
        if formatted_details['prop_units']:
            prop_type += '<br>(' + formatted_details['prop_units'] + ')'

        if formatted_details['read_only']:
            prop_access = 'read-only'
        else:
            prop_access = 'read-write'

        row = []
        row.append(indentation_string + name_and_version)
        row.append(prop_type)
        row.append(prop_access)
        row.append(formatted_details['descr'])

        formatted.append(self.make_row(row))

        if len(formatted_details['object_description']) > 0:
            formatted.append(formatted_details['object_description'])
            desc_row = [''] * len(row)
            desc_row[0] = indentation_string + '}'
            formatted.append(self.make_row(desc_row))

        if len(formatted_details['item_description']) > 0:
            formatted.append(formatted_details['item_description'])
            desc_row = [''] * len(row)
            if formatted_details['array_of_objects']:
                desc_row[0] = indentation_string + '} ]'
            else:
                desc_row[0] = indentation_string + ']'
            formatted.append(self.make_row(desc_row))

        return({'row': '\n'.join(formatted), 'details':formatted_details['prop_details'],
                'action_details':formatted_details.get('action_details')})


    def format_property_details(self, prop_name, prop_type, enum, enum_details,
                                supplemental_details):
        """Generate a formatted table of enum information for inclusion in Property Details."""

        contents = []
        contents.append(self.head_four(html.escape(prop_name, False) + ':'))

        if isinstance(prop_type, list):
            prop_type = ', '.join([html.escape(x, False) for x in prop_type])
        else:
            prop_type = html.escape(prop_type, False)

        if supplemental_details:
            contents.append(self.markdown_to_html(supplemental_details))

        if enum_details:
            header_row = self.make_header_row([prop_type, 'Description'])
            table_rows = []
            enum.sort()
            for enum_item in enum:
                table_rows.append(self.make_row([html.escape(enum_item, False),
                                                 html.escape(enum_details.get(enum_item, ''),
                                                             False)]))
            contents.append(self.make_table(table_rows, [header_row], 'enum enum-details'))

        elif enum:
            header_row = self.make_header_row([prop_type])
            table_rows = []
            enum.sort()
            for enum_item in enum:
                table_rows.append(self.make_row([html.escape(enum_item, False)]))
            contents.append(self.make_table(table_rows, [header_row], 'enum'))

        return '\n'.join(contents) + '\n'


    def format_action_details(self, prop_name, action_details):
        """Generate a formatted Actions section.

        Currently, Actions details are entirely derived from the supplemental documentation."""

        contents = []
        contents.append(self.head_four(action_details.get('action_name', prop_name)))
        contents.append(self.markdown_to_html(action_details.get('text', '')))
        if action_details.get('example'):
            example = '```json\n' + action_details['example'] + '\n```\n'
            contents.append(self.para('Example Action POST:'))
            contents.append(self.markdown_to_html(example))

        return '\n'.join(contents) + '\n'


    def emit(self):
        """ Output contents thus far """

        contents = []

        for section in self.sections:
            contents.append(section.get('heading'))

            if section.get('description'):
                contents.append(section['description'])
            # something is awry if there are no properties
            if section.get('properties'):
                contents.append(self.make_table(section['properties'], None, 'properties'))
            if section.get('property_details'):
                deets = []
                deets.append(self.head_three('Property Details'))
                deets.append(self.make_div('\n'.join(section['property_details']),
                                           'property-details-content'))
                contents.append(self.make_div('\n'.join(deets), 'property-details'))
            if len(section.get('action_details', [])):
                action_details = '\n'.join(section['action_details'])
                deets = []
                deets.append(self.head_three('Actions'))
                deets.append(self.make_div(action_details, 'property-details-content'))
                contents.append(self.make_div('\n'.join(deets), 'property-details'))
            if section.get('json_payload'):
                contents.append(self.head_three('Example Response'))
                contents.append(section['json_payload'])

        self.sections = []
        return '\n'.join(contents)


    def output_document(self):
        """Return full contents of document"""
        body = self.emit()
        supplemental = self.config['supplemental']

        intro = supplemental.get('Introduction')
        if intro:
            intro = self.process_intro(intro)
            body = intro + body

        if 'Postscript' in supplemental:
            body += self.markdown_to_html(supplemental['Postscript'])

        if 'Title' in supplemental:
            doc_title = supplemental['Title']
        else:
            doc_title = ''

        headlines = ['<head>', '<meta charset="utf-8">', '<title>' + doc_title + '</title>']
        styles = self.css_content
        headlines.append(styles)
        headlines.append('</head>')
        head = '\n'.join(headlines)
        return '\n'.join(['<!doctype html>', '<html>', head, '<body>', body, '</body></html>'])


    def process_intro(self, intro_blob):
        """ Process the Intro markdown, pulling in any schema fragments """

        parts = []
        intro = []
        part_text = []

        fragment_config = {
            'schema_root_uri': self.config['schema_root_uri'],
            'output_format': 'html',
            'normative': self.config['normative'],
            'cwd': self.config['cwd'],
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
                intro.append(self.markdown_to_html(part['content']))
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
            if link_id:
                section_text = html.escape(text, False)
                section_text = '<a name="' + link_id + '"></a>' + section_text
            else:
                section_text = html.escape(text, False)

            self.this_section['head'] = text
            self.this_section['heading'] = self.head_two(section_text)

        self.sections.append(self.this_section)


    def add_description(self, text):
        """ Add the schema description """
        self.this_section['description'] = self.markdown_to_html(text)


    def add_json_payload(self, json_payload):
        """ Add a JSON payload for the current section

        This may include comments as well as a ```json block. """
        if json_payload:

            self.this_section['json_payload'] = ('<div class="json-payload">' +
                                                 self.markdown_to_html(json_payload) + '</div>')
        else:
            self.this_section['json_payload'] = None


    def add_property_row(self, formatted_text):
        """Add a row (or group of rows) for an individual property in the current section/schema.

        formatted_row should be a chunk of text already formatted for output"""
        self.this_section['properties'].append(formatted_text)


    def add_property_details(self, formatted_details):
        """Add a chunk of property details information for the current section/schema."""
        self.this_section['property_details'].append(formatted_details)


    def link_to_own_schema(self, schema_name):
        """ Provide a link to schema_name, assuming it's in this project's namespace """

        if self.is_documented_schema(schema_name):
            return '<a href="#' + schema_name + '">' + schema_name + '</a>'
        else:
            uri = self.traverser.get_uri_for_schema(schema_name)
            if uri:
                return '<a href="' + uri + '" target="_blank">' + schema_name + '</a>'

        return schema_name


    def link_to_outside_schema(self, uri):
        """ Provide a link to a scheme in another namespace """
        return '<a href="' + uri + '" target="_blank">' + uri + '</a>'


    def get_documentation_link(self, ref_uri):
        """ Provide a link to documentation, if provided """

        target = self.get_documentation_uri(ref_uri)
        if target:
            return 'See <a href="' + target + '" target="_blank">' + target + '</a>'
        return False


    @staticmethod
    def bold(text):
        """Apply bold to text"""
        return '<b>' + text + '</b>'

    @staticmethod
    def italic(text):
        """Apply italic to text"""
        return '<i>' + text + '</i>'

    @staticmethod
    def make_div(text, css_class=None):
        """ Make a div, optionally applying a css class """
        div = []
        if css_class:
            div.append('<div class="' + css_class + '">')
        else:
            div.append('<div>')
        div.append(text)
        div.append('</div>')
        return '\n'.join(div)

    @staticmethod
    def make_row(cells):
        """ Make an HTML row """
        row = ''.join(['<td>' + cell + '</td>' for cell in cells])
        return '<tr>' + row + '</tr>'

    @staticmethod
    def make_header_row(cells):
        """ Make an HTML row, using table header markup """
        row = ''.join(['<th>' + cell + '</th>' for cell in cells])
        return '<tr>' + row + '</tr>'

    @staticmethod
    def make_table(rows, header_rows=None, css_class=None):
        """ Make an HTML table from the provided rows, which should be HTML markup """
        if header_rows:
            head = '<thead>\n' + '\n'.join(header_rows) + '\n</thead>\n'
        else:
            head = ''
        body = '<tbody>\n' + '\n'.join(rows) + '\n</tbody>'
        if css_class:
            table_tag = '<table class="' + css_class + '">'
        else:
            table_tag = '<table>'

        return table_tag + '\n' + head + body + '</table>'

    @staticmethod
    def para(text):
        """ Wrap text as HTML paragraph """
        return '<p>' + text + '</p>'

    @staticmethod
    def make_paras(text):
        """ Split text at linebreaks and output as paragraphs """
        return '\n'.join([HtmlGenerator.para(line) for line in '\n'.split(text) if line])

    def head_one(self, text):
        """ Make a top-level heading, relative to the current formatter level """
        level = str(self.level + 1)
        return '<h' + level + '>' + text + '</h' + level + '>'

    def head_two(self, text):
        """ Make a second-level heading, relative to the current formatter level """
        level = str(self.level + 2)
        return '<h' + level + '>' + text + '</h' + level + '>'

    def head_three(self, text):
        """ Make a third-level heading, relative to the current formatter level """
        level = str(self.level + 3)
        return '<h' + level + '>' + text + '</h' + level + '>'

    def head_four(self, text):
        """ Make a fourth-level heading, relative to the current formatter level """
        level = str(self.level + 4)
        return '<h' + level + '>' + text + '</h' + level + '>'

    @staticmethod
    def markdown_to_html(markdown_blob):
        """ Convert markdown to HTML """
        html_blob = markdown.markdown(markdown_blob,
                                      extensions=['markdown.extensions.codehilite',
                                                  'markdown.extensions.fenced_code',
                                                  'markdown.extensions.tables'])
        # Look for empty table rows; used to get tables without headers recognized:
        if '<table>' in html_blob:
            lines = []
            html_updated = False
            in_thead = False
            thead_lines = []
            discard_thead = False
            for line in html_blob.splitlines():
                if in_thead:
                    if line == '</thead>':
                        thead_lines.append(line)
                        in_thead = False
                        if discard_thead:
                            html_updated = True
                        else:
                            [lines.append(x) for x in thead_lines]
                    elif line not in ['<tr>', '<th></th>', '</tr>']:
                        discard_thead = False
                        continue
                    else:
                        thead_lines.append(line)
                elif line == '<thead>':
                    in_thead = True
                    discard_thead = True
                    thead_lines = [line]
                    continue
                else:
                    lines.append(line)

            if html_updated:
                html_blob = '\n'.join(lines)

        return html_blob
