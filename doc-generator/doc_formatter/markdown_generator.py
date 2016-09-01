"""
File : markdown_generator.py

Brief : This file contains definitions for the MarkdownGenerator class.

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

class MarkdownGenerator(DocFormatter):
    """Provides methods for generating markdown from Redfish schemas.

    Markdown is targeted to the Slate documentation tool: https://github.com/lord/slate
    """


    def __init__(self, property_data, traverser, config):
        super(MarkdownGenerator, self).__init__(property_data, traverser, config)
        self.sections = []
        self.separators = {
            'inline': ', ',
            'linebreak': '\n'
            }


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

        name_and_version = '**' + self.escape_for_markdown(prop_name, self.config['escape_chars']) + '**'
        if 'version' in meta:
            version_display = self.truncate_version(meta['version'], 2) + '+'
            if 'version_deprecated' in meta:
                deprecated_display = self.truncate_version(meta['version_deprecated'], 2)
                name_and_version += ' *(v' + version_display + ', deprecated v' + deprecated_display +  ')*'
            else:
                name_and_version += ' *(v' + version_display + ')*'
        elif 'version_deprecated' in meta:
            deprecated_display = self.truncate_version(meta['version_deprecated'], 2)
            name_and_version += ' *(deprecated v' + deprecated_display +  ')*'

        formatted_details = self.parse_property_info(schema_name, prop_name, traverser, prop_info, current_depth)

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

        # If there are prop_details (enum details), add a note to the description:
        if formatted_details['has_direct_prop_details']:
            formatted_details['descr'] += ' *See Property Details, below, for more information about this property.*'


        prop_type = formatted_details['prop_type']
        if formatted_details['prop_units']:
            prop_type += '<br>(' + formatted_details['prop_units'] + ')'

        if formatted_details['read_only']:
            prop_type += '<br><br>*' + 'read-only' + '*'
        else:
            prop_type += '<br><br>*' + 'read-write' + '*'

        row = []
        row.append(indentation_string + name_and_version)
        row.append(prop_type)
        row.append(formatted_details['descr'])

        formatted.append('| ' + ' | '.join(row) + ' |')

        if len(formatted_details['object_description']) > 0:
            formatted.append(formatted_details['object_description'])
            formatted.append('| ' + indentation_string + '} |   |   |')

        if len(formatted_details['item_description']) > 0:
            formatted.append(formatted_details['item_description'])
            formatted.append('| ' + indentation_string + '} ] |   |   |')

        return({'row': '\n'.join(formatted), 'details':formatted_details['prop_details']})


    def format_property_details(self, prop_name, prop_type, enum, enum_details, supplemental_details):
        """Generate a formatted table of enum information for inclusion in Property Details."""

        contents = []
        contents.append('### ' + prop_name + ':\n')

        if isinstance(prop_type, list):
            prop_type = ', '.join(prop_type)

        if supplemental_details:
            contents.append('\n' + supplemental_details + '\n')

        if enum_details:
            contents.append('| ' + prop_type + ' | Description |')
            contents.append('| --- | --- |')
            enum.sort()
            for enum_item in enum:
                contents.append('| ' + enum_item + ' | ' + enum_details.get(enum_item, '') + ' |')

        elif enum:
            contents.append('| ' + prop_type + ' |')
            contents.append('| --- |')
            for enum_item in enum:
                contents.append('| ' + enum_item + ' | ')

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
            if section['json_payload']:
                contents.append(section['json_payload'])
            # something is awry if there are no properties, but ...
            if section['properties']:
                contents.append('|     |     |     |')
                contents.append('| --- | --- | --- |')
                contents.append('\n'.join(section['properties']))
            if section['property_details']:
                contents.append('\n## Property Details\n')
                contents.append('\n'.join(section['property_details']))

        self.sections = []
        return '\n'.join(contents)


    def output_document(self):
        """Return full contents of document"""
        body = self.emit()

        supplemental = self.config['supplemental']

        if 'Title' in supplemental:
            doc_title = supplemental['Title']
        else:
            doc_title = 'Schema Documentation'

        prelude = "---\ntitle: " + doc_title + """

language tabs:
  - shell

search: true
---
"""

        if 'Introduction' in supplemental:
            prelude += '\n' + supplemental['Introduction'] + '\n'
        contents = [prelude, body]
        if 'Postscript' in supplemental:
            contents.append('\n' + supplemental['Postscript'])
        return '\n'.join(contents)


    def add_section(self, text):
        """ Add a top-level heading """
        self.this_section = {'head': text,
                             'heading': '\n# ' + text + '\n',
                             'properties': [],
                             'property_details': []
                             }

        self.sections.append(self.this_section)


    def add_description(self, text):
        """ Add the schema description """
        self.this_section['description'] = text + '\n'


    def add_json_payload(self, json_payload):
        """ Add a JSON payload for the current section """
        if json_payload:
            self.this_section['json_payload'] = '\n' + json_payload + '\n'
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
    def escape_for_markdown(text, chars):
        """Escape selected characters in text to prevent auto-formatting in markdown."""
        for char in chars:
            text = text.replace(char, '\\' + char)
        return text
