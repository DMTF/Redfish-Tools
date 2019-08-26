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
        # doc generator will be looking for config['supplemental']['DescriptionOverrides']
        config['supplemental']['DescriptionOverrides'] = config_data.get('DescriptionOverrides', {})
        excluded_props =  config_data.get('ExcludedProperties', [])
        config['excluded_properties'].extend([x for x in excluded_props if not x.startswith('*')])
        config['excluded_by_match'].extend([x[1:] for x in excluded_props if x.startswith('*')])

        super(PropertyIndexGenerator, self).__init__(property_data, traverser, config, level)
        self.collapse_list_of_simple_type = False

        # If there's a file to write config to, check it now.
        self.write_config_fh = False
        if config.get('write_config_to'):
            try:
                config_out = open(config['write_config_to'], 'w', encoding="utf8")
                self.write_config_fh = config_out
            except (OSError) as ex:
                warnings.warn('Unable to open ' + config['write_config_to'] + ' to write: ' + str(ex))

        self.properties_by_name = {}
        self.coalesced_properties = {}
        # Shorthand for the overrides.
        self.overrides = config['supplemental']['DescriptionOverrides']

        # Force some config here:
        self.config['omit_version_in_headers'] = True # This puts just the schema name in the section head.
        self.config['wants_common_objects'] = True


    def emit(self):
        """ Return the data! """
        self.coalesce_properties()
        output_format = self.config.get('output_format', 'markdown')
        output = ''
        frontmatter = backmatter = ''
        if 'property_index_boilerplate' in self.config:
            boilerplate = self.config['property_index_boilerplate']
            frontmatter, backmatter = boilerplate.split('[insert property index]')
        if output_format == 'html':
            from format_utils import HtmlUtils
            formatter = HtmlUtils()
            if frontmatter:
                output = formatter.markdown_to_html(frontmatter)
            else:
                output = formatter.head_one("Property Index", 0)
            output += self.format_tabular_output(formatter)
            output += formatter.markdown_to_html(backmatter)
            toc = self.generate_toc(output)
            if '[add_toc]' in output:
                output = output.replace('[add_toc]', toc, 1)

            output = self.add_html_boilerplate(output)

        if output_format == 'markdown':
            from format_utils import FormatUtils
            formatter = FormatUtils()
            if frontmatter:
                output = frontmatter
            else:
                output = formatter.head_one("Property Index", 0)
            output += self.format_tabular_output(formatter)
            output += backmatter

        if output_format == 'csv':
            output = self.output_csv()

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
            # We've drilled down to a simple type.
            return

        within_action = prop_path == ['Actions']
        has_enum = False

        if isinstance(prop_info, list):
            has_enum = 'enum' in prop_info[0]
        elif isinstance(prop_info, dict):
            has_enum = 'enum' in prop_info

        if within_action:
            prop_name_parts = prop_name.split('.')
            if len(prop_name_parts) == 2:
                prop_name = prop_name_parts[1] + ' (Action)'

        details = self.parse_property_info(schema_ref, prop_name, prop_info, prop_path)

        schema_path_formatted = self.this_section['schema_name']
        schema_path = [ self.this_section['schema_name'] ]
        if len(prop_path):
            schema_path += prop_path

        prop_type = details.get('prop_type')
        if isinstance(prop_type, list):
            prop_type_values = []
            self.append_unique_values(prop_type, prop_type_values)
            prop_type = ', '.join(sorted(prop_type_values))

        if has_enum:
            prop_type += " (enum)"

        description_entry = {
            'schemas': [ schema_path ], 'prop_type': prop_type,
            }

        # Check for an override:
        override_description = False
        if self.overrides.get(prop_name):
            for override_entry in self.overrides.get(prop_name):
                if not override_entry.get('overrideDescription'):
                    continue
                if override_entry.get('globalOverride') and override_entry.get('type') == prop_type:
                    override_description = override_entry.get('overrideDescription')
                    if override_description:
                        break
                elif override_entry.get('type') == prop_type and '/'.join(schema_path) in override_entry.get('schemas', []):
                    override_description = override_entry.get('overrideDescription')
                    if override_description:
                        break


        if override_description:
            description_entry['description'] = override_description
        elif self.config.get('normative') and details.get('normative_descr'):
            description_entry['description'] = details.get('normative_descr')
        else:
            description_entry['description'] = details.get('descr')

        if prop_name not in self.properties_by_name:
            self.properties_by_name[prop_name] = []

        if description_entry['description']:
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
                                supplemental_details, parent_prop_info, anchor=None, profile=None):
        """ Handle enum information """
        pass


    def format_action_parameters(self, schema_ref, prop_name, prop_descr, action_parameters, profile):
        """Generate a formatted Actions section from parameters data"""
        pass


    def add_registry_reqs(self, registry_reqs):
        """ output doesn't include registry requirements. """
        pass


    # TODO: generate_toc is the same as in html_generator and could probably be moved to HtmlUtils
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
            prop_config = overrides.get(prop_name)
            info = self.coalesced_properties[prop_name]
            prop_types = sorted(info.keys())

            # If we don't already have prop_config and we have multiple types, capture them all:
            num_prop_types = len(prop_types)

            done_with_prop_name = False
            if not prop_config and num_prop_types > 1:
                prop_config = overrides[prop_name] = []
                for prop_type in prop_types:
                    descriptions = sorted(info[prop_type].keys())
                    for description in descriptions:
                        schemas = info[prop_type][description]
                        found_entry = {
                            "type": prop_type,
                            "description": description,
                            'knownException': False,
                            "schemas": ['/'.join(x) for x in schemas]
                            }
                        prop_config.append(found_entry)
                done_with_prop_name = True

            else:
                for prop_type in prop_types:
                    descriptions = sorted(info[prop_type].keys())
                    num_descriptions = len(descriptions)
                    done_with_prop_type = False

                    if not prop_config:
                        # If we found multiple descriptions and we have no overrides, capture each:
                        if num_descriptions > 1:
                            prop_config = overrides[prop_name] = []
                            for description in descriptions:
                                schemas = info[prop_type][description]
                                found_entry = {
                                    "type": prop_type,
                                    "description": description,
                                    'knownException': False,
                                    "schemas": ['/'.join(x) for x in schemas]
                                    }
                                prop_config.append(found_entry)
                            done_with_prop_name = True

                    else:
                        self.update_config_for_prop_name_and_type(prop_name, prop_type, info, prop_config)

        return updated


    def update_config_for_prop_name_and_type(self, prop_name, prop_type, info, prop_config):
        """ Update a property name/type selection of prop_config based on coalesced info. Updates prop_config. """

        # Do we have a globalOverride for this prop_type? If so, we're done. Again.
        for over_info in prop_config:
            if over_info.get('type') == prop_type and over_info.get('globalOverride', False):
                return

        # check each entry against prop_config
        descriptions = sorted(info[prop_type].keys())
        for description in descriptions:
            self.update_config_for_prop_name_and_type_and_description(prop_name, prop_type, description, info, prop_config)


    def update_config_for_prop_name_and_type_and_description(self, prop_name, prop_type, description, info, prop_config):
        """ Update a property name/type/description selection of prop_config based on coalesced info. Updates prop_config. """

        """ Info is arranged by prop_name: prop_type: description: schemas (list).
        prop_config, conversely, is arranged as a list of dicts with keys schemas, type, description, overrideDescription, knownException.

        If we applied an override, the description in "info" will match the overrideDescription in prop_config. """

        config_by_schema = {}
        for config in prop_config:
            # Note, we ignore globalOverrides in this method.
            if config.get('type') == prop_type:
                for schema in config.get('schemas', []):
                    config_by_schema[schema] = config

        schemas = info[prop_type][description]
        for schema_path in schemas:
            schema_name = '/'.join(schema_path)

            if config_by_schema.get(schema_name):
                # We have an entry for this schema name. It's still good if it has an overrideDescription, or if the description matches.
                if config_by_schema[schema_name].get('overrideDescription'):
                    break
                elif config_by_schema[schema_name].get('description') == description:
                    break
                else:
                    config_by_schema[schema_name]['description'] = description
                    config_by_schema[schema_name]['knownException'] = False

            else:
                # If we already have this description, add the schema there.
                for config in prop_config:
                    if config.get('type') == prop_type and config.get('description') == description:
                        config['schemas'].append(schema_name)
                        break

                # We didn't find a matching description, so create a new entry:
                found_entry = {
                    "type": prop_type,
                    "description": description,
                    'knownException': False,
                    "schemas": [ schema_name ]
                    }
                prop_config.append(found_entry)
                config_by_schema[schema_name] = found_entry


    def format_tabular_output(self, formatter):
        """ Format output in the 'usual' way, as a tabular document """

        rows = []
        property_names = sorted(self.coalesced_properties.keys())

        for prop_name in property_names:
            info = self.coalesced_properties[prop_name]
            prop_types = sorted(info.keys())
            first_row = True

            for prop_type in prop_types:
                descriptions = sorted(info[prop_type].keys())
                for description in descriptions:
                    schema_list = [self.format_schema_path(x) for x in info[prop_type][description] ]
                    if first_row:
                        first_col = formatter.bold(prop_name)
                        first_row = False
                    else:
                        first_col = ''
                    rows.append(formatter.make_row([first_col,
                                                    self.format_schema_list(schema_list, formatter),
                                                    prop_type, description]))

        if self.write_config_fh:
            config_out = self.write_config_fh
            updated_config = self.generate_updated_config()
            json.dump(updated_config, config_out, indent=4, sort_keys=True)
            config_out.close()

        headers = formatter.make_header_row(['Property Name', 'Defined In Schema(s)', 'Type', 'Description'])
        table = formatter.make_table(rows, [headers])
        return table


    @staticmethod
    def add_html_boilerplate(htmlblob):

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
        return '\n'.join(['<!doctype html>', '<html>', head, '<body>', htmlblob, '</body></html>'])


    @staticmethod
    def format_schema_list(schema_list, formatter):
        sep = ', ' + formatter.br()
        if len(schema_list) > 10:
            return formatter.italic('various') + formatter.br() + '(' + sep.join(schema_list[:2]) + ' ... )'
        else:
            return sep.join(schema_list)


    @staticmethod
    def format_schema_path(sl):
        formatted = sl[0]
        if len(sl) > 1:
            formatted += ' (' + ' > '.join(sl[1:]) + ')'
        return formatted


    def output_csv(self):
        """ Generate CSV output. """

        import csv
        import io

        csv_out = io.StringIO()
        writer = csv.writer(csv_out)

        rows = []
        rows.append(['Property Name', 'Schema', 'Type', 'Description'])

        property_names = sorted(self.coalesced_properties.keys())
        for prop_name in property_names:
            info = self.coalesced_properties[prop_name]
            prop_types = sorted(info.keys())

            for prop_type in prop_types:
                descriptions = sorted(info[prop_type].keys())
                for description in descriptions:
                    schema_list = [self.format_schema_path(x) for x in info[prop_type][description] ]
                    for schema_str in schema_list:
                        rows.append([prop_name, schema_str, prop_type, description])

        for row in rows:
            writer.writerow(row)

        result = csv_out.getvalue()
        csv_out.close()
        return result



    def add_description(self, text):
        """ This is for the schema description. We don't actually use this. """
        pass

    def add_uris(self, uris):
        """ omit URIs """
        pass


    def add_json_payload(self, json_payload):
        """ JSON payloads don't make sense for PropertyIndex  """
        pass
