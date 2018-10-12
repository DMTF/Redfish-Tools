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
import json
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
        # parse the property index config data
        config_data = config['property_index_config']
        config['supplemental']['DescriptionOverrides'] = config_data.get('DescriptionOverrides', {})
        excluded_props =  config_data.get('ExcludedProperties', [])
        config['excluded_properties'].extend([x for x in excluded_props if not x.startswith('*')])
        config['excluded_by_match'].extend([x[1:] for x in excluded_props if x.startswith('*')])

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


    def format_property_row(self, schema_ref, prop_name, prop_info, prop_path=[], in_array=False):
        """ Instead of formatting this data, add info to self.properties_by_name. """

        if not prop_name:
            return

        details = self.parse_property_info(schema_ref, prop_name, prop_info, prop_path)

        schema_path_formatted = self.this_section['schema_name']
        schema_path = [ self.this_section['schema_name'] ]
        if len(prop_path):
            # schema_path_formatted += ' (' + ' > '.join(prop_path) + ')'
            schema_path += prop_path

        prop_type = details.get('prop_type')
        if isinstance(prop_type, list):
            prop_type_values = []
            self.append_unique_values(prop_type, prop_type_values)
            prop_type = ', '.join(sorted(prop_type_values))

        description_entry = {
            'schemas': [ schema_path ], 'prop_type': prop_type,
            }

        if self.config.get('normative') and details.get('normative_descr'):
            description_entry['description'] = details.get('normative_descr')
        else:
            description_entry['description'] = details.get('descr')

        if prop_name not in self.properties_by_name:
            self.properties_by_name[prop_name] = []

        self.properties_by_name[prop_name].append(description_entry)


    def append_unique_values(self, value_list, target_list):
        """ Unwind possibly-nested list, producing a list of unique strings found.

        We don't want nulls reflected in the property index!
        """
        super(PropertyIndexGenerator, self).append_unique_values(value_list, target_list)
        for i in range(0, len(target_list)):
            if target_list[i] == 'null':
                del target_list[i]


    def format_property_details(self, prop_name, prop_type, prop_description, enum, enum_details,
                                supplemental_details, meta, anchor=None, profile=None):
        """ Handle enum information """
        pass


    def add_registry_reqs(self, registry_reqs):
        """ output doesn't include registry requirements. """
        pass


    def is_excluded(self, prop_name):
        """ True if prop_name is in the excluded or excluded-by-match list.

        Many properties are excluded in the parent doc_generator code, but for other output
        modes we sometimes include them in sub-properties. """
        if prop_name in self.config['excluded_properties']:
            return True
        if prop_name in self.config['excluded_by_match']:
            pass

        return False


    def coalesce_properties(self):
        """ Group the info in self.properties_by_name based on prop_type and description match. """

        # Group the property info by prop_name, type, description:
        coalesced_info = {}
        prop_names = self.exclude_prop_names(self.properties_by_name.keys(),
                                             self.config['excluded_properties'],
                                             self.config['excluded_by_match'])

        for property_name in prop_names:
            property_infos = self.properties_by_name[property_name]
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


    def generate_updated_config(self):
        """ Update property_index_config data.

        Flag any properties that were found to have more than one type, or more than one
        description. If the property already appears in self.config['property_index_config']
        and it has a globalDescription, flag only entries with a different *type*. """

        updated = copy.deepcopy(self.config['property_index_config'])
        overrides = updated['DescriptionOverrides'] # NB: this should already be in place.

        # Sorting isn't necessary in this method, but it's nice to have for troubleshooting.
        property_names = sorted(self.coalesced_properties.keys())

        for prop_name in property_names:
            prop_overrides = overrides.get(prop_name)

            info = self.coalesced_properties[prop_name]
            prop_types = sorted(info.keys())
            add_all = False

            # If we don't already have prop_overrides and we have multiple types, output all:
            if len(prop_types) > 1 and not prop_overrides:
                overrides[prop_name] = []
                prop_overrides = overrides.get(prop_name)
                add_all = True

            for prop_type in prop_types:
                descriptions = sorted(info[prop_type].keys())
                for description in descriptions:
                    schemas = info[prop_type][description]
                    if add_all:
                        found_entry = {
                            "type": prop_type,
                            "description": description,
                            'knownException': False,
                            "schemas": ['/'.join(x) for x in schemas]
                            }
                        prop_overrides.append(found_entry)

        return updated


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

        property_names = sorted(self.coalesced_properties.keys())

        for prop_name in property_names:
            info = self.coalesced_properties[prop_name]
            prop_types = sorted(info.keys())
            for prop_type in prop_types:
                descriptions = sorted(info[prop_type].keys()) # TODO: what's the preferred sort?
                for description in descriptions:
                    schema_list = [self.format_schema_list(x) for x in info[prop_type][description] ]
                    # for x in info[prop_type][description]:

                    # schema_list = sorted(info[prop_type][description])
                    rows.append(make_row(['<b>' + prop_name + '</b>', ', <br>'.join(schema_list),
                                          prop_type, description]))

        if self.config.get('write_config_fh'):
            config_out = self.config.get('write_config_fh')
            # TODO: update config
            updated_config = self.generate_updated_config()
            print(json.dumps(updated_config, indent=3), file=config_out)
            config_out.close()

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


    def format_schema_list(self, sl):
        formatted = sl[0]
        if len(sl) > 1:
            formatted += ' (' + ' > '.join(sl[1:]) + ')'
        return formatted


    def emit_markdown(self):
        raise NotImplementedError


    def emit_csv(self):
        raise NotImplementedError


    def add_description(self, text):
        """ This is for the schema description. We don't actually use this. """
        pass

    def add_uris(self, uris):
        """ omit URIs """
        pass


    def add_json_payload(self, json_payload):
        """ JSON payloads don't make sense for PropertyIndex  """
        pass
