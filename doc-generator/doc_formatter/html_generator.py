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
from . import DocFormatter
import markdown
import html

class HtmlGenerator(DocFormatter):
    """Provides methods for generating markdown from Redfish schemas. """


    def __init__(self, property_data, traverser, config):
        super(HtmlGenerator, self).__init__(property_data, traverser, config)
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
.property-details table{
    margin-left: 5em;
}
pre.code{
    font-size: 1em;
    margin-left: 5em;
    color: #0000FF
}
</style>
"""


    def format_property_row(self, schema_name, prop_name, prop_info, meta=None, current_depth=0):
        """Format information for a single property. Returns an object with 'row' and 'details'.

        'row': content for the main table being generated.
        'details': content for the Property Details section.

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
                name_and_version += ' ' + self.italic('(v' + version_display + ', deprecated v' + deprecated_display +  ')')
            else:
                name_and_version += ' ' + self.italic('(v' + version_display + ')')
        elif 'version_deprecated' in meta:
            version_depr = html.escape(meta['version_deprecated'], False)
            deprecated_display = self.truncate_version(version_depr, 2)
            name_and_version += ' ' + self.italic('(deprecated v' + deprecated_display +  ')')

        formatted_details = self.parse_property_info(schema_name, prop_name, traverser, prop_info, current_depth)

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
                name_and_version += ' {}'
            else:
                name_and_version += ' {'

        if formatted_details['prop_is_array']:
            if formatted_details['item_description'] == '':
                name_and_version += ' [ {} ]'
            else:
                name_and_version += ' [ {'

        formatted_details['descr'] = html.escape(formatted_details['descr'], False)
        # If there are prop_details (enum details), add a note to the description:
        if formatted_details['has_direct_prop_details']:
            formatted_details['descr'] += '<br>' + self.italic('See Property Details, below, for more information about this property.')


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
            desc_row[0] = indentation_string + '} ]'
            formatted.append(self.make_row(desc_row))


        return({'row': '\n'.join(formatted), 'details':formatted_details['prop_details']})


    def format_property_details(self, prop_name, prop_type, enum, enum_details, supplemental_details):
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
                table_rows.append(self.make_row([html.escape(enum_item, False), html.escape(enum_details.get(enum_item, ''), False)]))
            contents.append(self.make_table(table_rows, [header_row], 'enum enum-details'))

        elif enum:
            header_row = self.make_header_row([prop_type])
            table_rows = []
            enum.sort()
            for enum_item in enum:
                table_rows.append(self.make_row([html.escape(enum_item, False)]))
            contents.append(self.make_table(table_rows, [header_row], 'enum'))

        return '\n'.join(contents) + '\n'


    def format_list_of_object_descriptions(self, schema_name, prop_items, traverser, current_depth):
        """Format a (possibly nested) list of embedded objects.

        We expect this to amount to one definition, usually for 'items' in an array."""

        if isinstance(prop_items, dict):
            return self.format_object_description(schema_name, prop_items, traverser, current_depth)

        rows = []
        details = {}
        if isinstance(prop_items, list):
            for prop_item in prop_items:
                formatted = self.format_list_of_object_descriptions(schema_name, prop_item, traverser, current_depth)
                rows.extend(formatted['rows'])
                details.update(formatted['details'])
            return ({'rows': rows, 'details': details})

        return None


    def emit(self):
        """ Output contents thus far """

        contents = []

        for section in self.sections:
            contents.append(section['heading'])
            if section['description']:
                contents.append(section['description'])
            # something is awry if there are no properties, but ...
            if section['properties']:
                contents.append(self.make_table(section['properties'], None, 'properties'))
            if section['property_details']:
                deets = []
                deets.append(self.head_three('Property Details'))
                deets.append('\n'.join(section['property_details']))
                contents.append(self.make_div('\n'.join(deets), 'property-details'))
            if section['json_payload']:
                contents.append(self.head_three('Example Response'))
                contents.append(section['json_payload'])


        self.sections = []
        return '\n'.join(contents)


    def output_document(self):
        """Return full contents of document"""
        body = self.emit()
        supplemental = self.config['supplemental']

        if 'Introduction' in supplemental:
            body = self.markdown_to_html(supplemental['Introduction']) + body
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


    def add_section(self, text):
        """ Add a top-level heading """
        self.this_section = {
            'head': text,
            'heading': self.head_two(html.escape(text, False)),
            'properties': [],
            'property_details': []
            }

        self.sections.append(self.this_section)


    def add_description(self, text):
        """ Add the schema description """
        self.this_section['description'] = self.markdown_to_html(text)


    def add_json_payload(self, json_payload):
        """ Add a JSON payload for the current section

        This may include comments as well as a ```json block. """
        if json_payload:

            chunks = []
            chunk = ''
            chunk_is_json = False
            chunk_is_code = False
            for line in json_payload.splitlines():
                if line.startswith('```'):
                    if chunk_is_code:
                        if chunk_is_json:
                            code_type = 'json'
                        else:
                            code_type = 'code'
                        chunks.append({'content': chunk, 'content_type': code_type})
                        chunk = ''
                        chunk_is_json = chunk_is_code = False
                    else:
                        chunks.append({'content': chunk, 'content_type': 'text'})
                        chunk = ''
                        chunk_is_code = True
                        chunk_is_json = 'json' in line
                else:
                    chunk = chunk + '\n' + line
            if chunk:
                if chunk_is_code:
                    if chunk_is_json:
                        code_type = 'json'
                    else:
                        code_type = 'code'
                else:
                    code_type = 'text'
                chunks.append({'content': chunk, 'content_type': code_type})

            contents = []
            for chunk in chunks:
                if chunk['content_type'] == 'json':
                    contents.append('<pre class="code json">\n' +
                                    html.escape(chunk['content'], False) +
                                    '\n</pre>')
                elif chunk['content_type'] == 'code':
                    contents.append('<pre class="code">\n' +
                                    html.escape(chunk['content'], False) +
                                    '\n</pre>')
                else:
                    contents.append(self.markdown_to_html(chunk['content']))
            self.this_section['json_payload'] = ('<div class="json-payload">' +
                                                 '\n'.join(contents) + '</div>')
        else:
            self.this_section['json_payload'] = None


    def add_property_row(self, formatted_text):
        """Add a row (or group of rows) for an individual property in the current section/schema.

        formatted_row should be a chunk of text already formatted for output"""
        self.this_section['properties'].append(formatted_text)


    def add_property_details(self, formatted_details):
        """Add a chunk of property details information for the current section/schema."""
        self.this_section['property_details'].append(formatted_details)


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
        row = ''.join(['<td>' + cell + '</td>' for cell in cells])
        return '<tr>' + row + '</tr>'

    @staticmethod
    def make_header_row(cells):
        row = ''.join(['<th>' + cell + '</th>' for cell in cells])
        return '<tr>' + row + '</tr>'

    @staticmethod
    def make_table(rows, header_rows=None, css_class=None):
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
        return '<p>' + text + '</p>'

    @staticmethod
    def make_paras(text):
        return '\n'.join([HtmlGenerator.para(line) for line in '\n'.split(text) if line])

    @staticmethod
    def head_one(text):
        return '<h1>' + text + '</h1>'

    @staticmethod
    def head_two(text):
        return '<h2>' + text + '</h2>'

    @staticmethod
    def head_three(text):
        return '<h3>' + text + '</h3>'

    @staticmethod
    def head_four(text):
        return '<h4>' + text + '</h4>'

    @staticmethod
    def markdown_to_html(markdown_blob):
        """ Convert markdown to HTML """
        return markdown.markdown(markdown_blob)
