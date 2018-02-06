# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/LICENSE.md

"""
File : csv_generator.py

Brief : This file contains definitions for the CsvGenerator class.

Initial author: Second Rise LLC.
"""

import copy
import csv
import io
import warnings
from . import DocFormatter

class CsvGenerator(DocFormatter):
    """Provides methods for generating CSV docs from Redfish schemas."""


    def __init__(self, property_data, traverser, config, level=0):
        super(CsvGenerator, self).__init__(property_data, traverser, config, level)
        self.sections = []
        self.separators = {
            'inline': ', ',
            'linebreak': '\n'
            }
        self.output = io.StringIO()
        self.writer = csv.writer(self.output)
        self.schema_name = self.schema_version = ''
        headings = [
            'Schema Name',
            'Schema Version',
            'Property Name (chain)',
            'Type',
            'Permissions',
            'Nullable',
            'Description',
            'Normative Description',
            'Units',
            'Minimum Value',
            'Maximum Value',
            'Enumerations',
            'Pattern',
            '']
        self.writer.writerow(headings)


    def format_property_row(self, schema_ref, prop_name, prop_info, current_depth=0):
        """Format information for a single property.

        Returns an object with 'row', 'details', and 'action_details':

        'row': content for the main table being generated.
        'details': content for the Property Details section.
        'action_details': content for the Actions section.

        This may include embedded objects with their own properties.
        CSV does not use depth, and instead includes the object path an extended name.
        """

        traverser = self.traverser
        row = []
        nextrows = []
        collapse_array = False # Should we collapse a list description into one row? For lists of simple types
        has_enum = False
        formatted_details = self.parse_property_info(schema_ref, prop_name, prop_info, current_depth)

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
                        if isinstance(val, list): # this is a nested description; chain the property name
                            for elt in val:
                                elt[2] = '.'.join([prop_name, elt[2]])
                                nextrows.append(elt)
                        else:
                            property_values.append(val)
                formatted_details[property_name] = delim.join(property_values)

        prop_type = formatted_details['prop_type']
        prop_units = formatted_details['prop_units']

        long_description = formatted_details['normative_descr']
        description = formatted_details['non_normative_descr']

        if formatted_details['read_only']:
            permissions = 'RO'
        else:
            permissions = 'RW'
        if formatted_details['nullable']:
            nullable = 'Yes'
        else:
            nullable = 'No'

        p_i = prop_info[0]
        min_val = p_i.get('minimum', '')
        max_val = p_i.get('maximum', '')
        pattern = ''

        pattern = formatted_details.get('pattern')

        enumerations = ''
        if 'enum' in p_i:
            enumerations = ', '.join(p_i['enum'])

        schema_name = self.schema_name
        version = self.schema_version

        row = [schema_name, version, prop_name, prop_type, permissions, nullable,
               description, long_description, prop_units, min_val, max_val, enumerations, pattern]
        rows = [row]
        for nextrow in nextrows:
            rows.append(nextrow)
        return { 'row': rows, 'details': {}, 'action_details': {} }


    def format_property_details(self, prop_name, prop_type, prop_description, enum, enum_details,
                                supplemental_details, meta, anchor=None, profile=None):
        """Generate a formatted table of enum information for inclusion in Property Details."""

        # TODO: use profile when in profile_mode
        contents = []
        contents.append(self.head_three(prop_name + ':'))

        parent_version = meta.get('version')
        enum_meta = meta.get('enum', {})

        if prop_description:
            contents.append(self.para(self.escape_for_markdown(prop_description, self.config['escape_chars'])))

        if isinstance(prop_type, list):
            prop_type = ', '.join(prop_type)

        if supplemental_details:
            contents.append('\n' + supplemental_details + '\n')

        if enum_details:
            contents.append('| ' + prop_type + ' | Description |')
            contents.append('| --- | --- |')
            enum.sort()
            for enum_item in enum:
                enum_name = enum_item
                enum_item_meta = enum_meta.get(enum_item, {})
                version_display = None
                deprecated_descr = None
                if 'version' in enum_item_meta:
                    version = enum_item_meta['version']
                    if not parent_version or self.compare_versions(version, parent_version) > 0:
                        version_display = self.truncate_version(version, 2) + '+'
                if version_display:
                    if 'version_deprecated' in enum_item_meta:
                        version_depr = enum_item_meta['version_deprecated']
                        enum_name += ' ' + self.italic('(v' + version_display + ', deprecated v' + version_depr + ')')
                        if enum_item_meta.get('version_deprecated_explanation'):
                            deprecated_descr = enum_item_meta['version_deprecated_explanation']
                    else:
                        enum_name += ' ' + self.italic('(v' + version_display + ')')
                else:
                    if 'version_deprecated' in enum_item_meta:
                        version_depr = enum_item_meta['version_deprecated']
                        enum_name += ' ' + self.italic('(deprecated v' + version_depr + ')')
                        if enum_item_meta.get('version_deprecated_explanation'):
                            deprecated_descr = enum_item_meta['version_deprecated_explanation']
                descr = enum_details.get(enum_item, '')
                if deprecated_descr:
                    if descr:
                        descr += ' ' + self.italic(deprecated_descr)
                    else:
                        descr = self.italic(deprecated_descr)
                contents.append('| ' + enum_name + ' | ' + descr + ' |')

        elif enum:
            contents.append('| ' + prop_type + ' |')
            contents.append('| --- |')
            for enum_item in enum:
                enum_name = enum_item
                enum_item_meta = enum_meta.get(enum_item, {})
                version_display = None

                if 'version' in enum_item_meta:
                    version = enum_item_meta['version']
                    if not parent_version or self.compare_versions(version, parent_version) > 0:
                        version_display = self.truncate_version(version, 2) + '+'
                if version_display:
                    if 'version_deprecated' in enum_item_meta:
                        version_depr = enum_item_meta['version_deprecated']
                        enum_name += ' ' + self.italic('(v' + version_display + ', deprecated v' + version_depr + ')')
                        if enum_item_meta.get('version_deprecated_explanation'):
                            deprecated_descr = enum_item_meta['version_deprecated_explanation']
                    else:
                        enum_name += ' ' + self.italic('(v' + version_display + ')')
                else:
                    if 'version_deprecated' in enum_item_meta:
                        version_depr = enum_item_meta['version_deprecated']
                        enum_name += ' ' + self.italic('(deprecated v' + version_depr + ')')
                        if enum_item_meta.get('version_deprecated_explanation'):
                            enum_name += ' ' + self.italic(enum_item_meta['version_deprecated_explanation'])

                contents.append('| ' + enum_name + ' | ')

        return '\n'.join(contents) + '\n'


    def format_action_details(self, prop_name, action_details):
        """Generate a formatted Actions section.

        Currently, Actions details are entirely derived from the supplemental documentation."""

        contents = []
        contents.append(self.head_three(action_details.get('action_name', prop_name)))
        if action_details.get('text'):
            contents.append(action_details.get('text'))
        if action_details.get('example'):
            example = '```json\n' + action_details['example'] + '\n```\n'
            contents.append('Example Action POST:\n')
            contents.append(example)

        return '\n'.join(contents) + '\n'


    def link_to_own_schema(self, schema_ref, schema_full_uri):
        """Format a reference to a schema."""
        result = super().link_to_own_schema(schema_ref, schema_full_uri)
        return self.italic(result)


    def link_to_outside_schema(self, schema_full_uri):
        """Format a reference to a schema_uri, which should be a valid URI"""
        return self.italic('['+ schema_full_uri + '](' + schema_full_uri + ')')


    def emit(self):
        """ Output contents thus far """

        contents = []

        for section in self.sections:
            contents.append(section.get('heading'))
            if section.get('description'):
                contents.append(section['description'])
            if section.get('json_payload'):
                contents.append(section['json_payload'])
            # something is awry if there are no properties, but ...
            if section.get('properties'):
                contents.append('|     |     |     |')
                contents.append('| --- | --- | --- |')
                contents.append('\n'.join(section['properties']))
            if section.get('property_details'):
                contents.append('\n' + self.head_two('Property Details'))
                contents.append('\n'.join(section['property_details']))
            if len(section.get('action_details', [])):
                contents.append('\n' + self.head_two('Actions'))
                contents.append('\n\n'.join(section.get('action_details')))

        self.sections = []
        return '\n'.join(contents)


    def output_document(self):
        """Return full contents of document"""

        result = self.output.getvalue()
        self.output.close()
        return result


    def process_intro(self, intro_blob):
        """ Process the intro text, generating and inserting any schema fragments """
        parts = []
        intro = []
        part_text = []

        fragment_config = {
            'output_format': 'markdown',
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
            'units_translation': self.config['units_translation'],
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


    def add_section(self, text, link_id=False):
        """ Rather than a top-level heading, for CSV we set the first column (schema name) """
        self.schema_name, self.schema_version = text.split(' ')
        self.this_section = {}

    def add_description(self, text):
        """  CSV omits schema description """
        pass


    def add_json_payload(self, json_payload):
        """ JSON payloads don't make sense for CSV  """
        if json_payload:
            warnings.warn("JSON payloads are ignored in CSV output")


    def add_property_row(self, rows):
        """ Add the row to the buffer. Unlike other formats, for CSV the argument is list of lists.  """
        for row in rows:
            self.writer.writerow(row)


    def add_property_details(self, formatted_details):
        """Add a chunk of property details information for the current section/schema."""
        self.this_section['property_details'].append(formatted_details)


    def head_one(self, text):
        """Add a top-level heading, relative to the generator's level"""
        add_level = '' + '#' * self.level
        return add_level + '# ' + text + "\n"

    def head_two(self, text):
        """Add a second-level heading, relative to the generator's level"""
        add_level = '' + '#' * self.level
        return add_level + '## ' + text + "\n"

    def head_three(self, text):
        """Add a third-level heading, relative to the generator's level"""
        add_level = '' + '#' * self.level
        return add_level + '### ' + text + "\n"

    def head_four(self, text):
        """Add a fourth-level heading, relative to the generator's level"""
        add_level = '' + '#' * self.level
        return add_level + '##### ' + text + "\n"

    def para(self, text):
        """Add a paragraph of text. Doesn't actually test for paragraph breaks within text"""
        return "\n" + text + "\n"

    @staticmethod
    def escape_for_markdown(text, chars):
        """Escape selected characters in text to prevent auto-formatting in markdown."""
        for char in chars:
            text = text.replace(char, '\\' + char)
        return text

    @staticmethod
    def bold(text):
        """Apply bold to text"""
        return '**' + text + '**'


    @staticmethod
    def italic(text):
        """Apply italic to text"""
        return '*' + text + '*'
