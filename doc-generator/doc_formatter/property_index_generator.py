# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File : property_index_generator.py

Brief : This file contains definitions for the PropertyIndexGenerator class.

This deviates pretty significantly from what the other DocFormatters
(so far) do, but it still needs to follow the same rules about
identifying schemas and following $refs.

Initial author: Second Rise LLC.
"""

import copy
import html
import markdown
import warnings
from doc_gen_util import DocGenUtilities
from . import DocFormatter
from . import ToCParser

# Format user warnings simply
def simple_warning_format(message, category, filename, lineno, file=None, line=None):
    """ a basic format for warnings from this program """
    return '  Warning: %s (%s:%s)' % (message, filename, lineno) + "\n"

warnings.formatwarning = simple_warning_format

class PropertyIndexGenerator(DocFormatter):
    """Provides methods for generating Property Index docs from Redfish schemas."""

    def __init__(self, property_data, traverser, config, level=0):
        """
        property_data: pre-processed schemas.
        traverser: SchemaTraverser object
        config: configuration dict
        """
        super(PropertyIndexGenerator, self).__init__(property_data, traverser, config, level)

        self.properties_by_name = {}
        self.coalesced_properties = {}

        # Force some config here:
        self.config['omit_version_in_headers'] = True # This puts just the schema name in the section head.
        self.config['wants_common_objects'] = True


    def emit(self):
        """ Return the data! """
        self.coalesce_properties()
        output_format = self.config.get('output_format', 'markdown')
        output = ''
        if output_format == 'html':
            output = self.emit_html()
        if output_format == 'markdown':
            output = self.emit_markdown()
        if output_format == 'csv':
            output = self.emit_csv()
        return output


    def add_section(self, text, link_id=False):
        """ Start gathering info for this schema. """

        self.this_section = {
            'properties': [],
            'property_details': [],
            'head': '',
            'heading': '',
            'schema_name': text
            }

    def add_description(self, text):
        """ This is for the schema description. We don't actually use this. """
        pass

    def add_uris(self, uris):
        """ omit URIs """
        pass


    def add_json_payload(self, json_payload):
        """ JSON payloads don't make sense for PropertyIndex  """
        pass


    def format_property_row(self, schema_ref, prop_name, prop_info, prop_path=[], in_array=False):
        """ Instead of formatting this data, add info to self.properties_by_name. """

        if not prop_name:
            return

        details = self.parse_property_info(schema_ref, prop_name, prop_info, prop_path)

        schema_path_formatted = self.this_section['schema_name']
        if len(prop_path):
            schema_path_formatted += ' (' + ' > '.join(prop_path) + ')'

        prop_type = details.get('prop_type')
        if isinstance(prop_type, list):
            prop_type = ', '.join(prop_type)

        description_entry = {
            'schemas': [ schema_path_formatted ], 'prop_type': prop_type
            }

        if self.config.get('normative') and details.get('normative_descr'):
            description_entry['description'] = details.get('normative_descr')
        else:
            description_entry['description'] = details.get('descr')

        if prop_name not in self.properties_by_name:
            self.properties_by_name[prop_name] = []
        self.properties_by_name[prop_name].append(description_entry)


    def format_property_details(self, prop_name, prop_type, prop_description, enum, enum_details,
                                supplemental_details, meta, anchor=None, profile=None):
        """ Handle enum information """
        pass


    def add_registry_reqs(self, registry_reqs):
        """ output doesn't include registry requirements. """
        pass


    def coalesce_properties(self):
        """ Group the info in self.properties_by_name based on prop_type and description match. """

        # Group the property info by prop_name, type, description:
        coalesced_info = {}
        for property_name, property_infos in self.properties_by_name.items():
            if len(property_infos) == 1:
                continue # nothing to do here.
            coalesced_info[property_name] = {}
            for info in property_infos:
                prop_type = info['prop_type']
                description = info['description']
                schemas = info['schemas']
                if prop_type not in coalesced_info[property_name]:
                    coalesced_info[property_name][prop_type] = {}
                if description not in coalesced_info[property_name][prop_type]:
                    coalesced_info[property_name][prop_type][description] = []
                coalesced_info[property_name][prop_type][description] += schemas

        self.coalesced_properties = coalesced_info

    def emit_html(self):

        def make_row(cells):
            """ Make an HTML row """
            row = ''.join(['<td>' + cell + '</td>' for cell in cells])
            return '<tr>' + row + '</tr>'

        def make_header_row(cells):
            """ Make an HTML row, using table header markup """
            row = ''.join(['<th>' + cell + '</th>' for cell in cells])
            return '<tr>' + row + '</tr>'

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

        rows = []

        property_names = sorted(self.coalesced_properties.keys(), key=str.lower)
        for prop_name in property_names:
            info = self.coalesced_properties[prop_name]
            prop_types = sorted(info.keys(), key=str.lower)
            for prop_type in info.keys():
                descriptions = sorted(info[prop_type].keys(), key=str.lower) # TODO: what's the preferred sort?
                for description in descriptions:
                    schema_list = info[prop_type][description]
                    rows.append(make_row(['<b>' + prop_name + '</b>', ', <br>'.join(schema_list),
                                          prop_type, description]))

        headers = make_header_row(['Property Name', 'Defined In Schema(s)', 'Type', 'Description'])
        table = make_table(rows, [headers])

        headlines = ['<head>', '<meta charset="utf-8">', '<title>' + 'Property Index' + '</title>']
        styles = """
<style>
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
</style>
"""
        headlines.append(styles)
        headlines.append('</head>')
        head = '\n'.join(headlines)
        return '\n'.join(['<!doctype html>', '<html>', head, '<body>', table, '</body></html>'])




    def emit_markdown(self):
        raise NotImplementedError


    def emit_csv(self):
        raise NotImplementedError
