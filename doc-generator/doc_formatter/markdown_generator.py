# Copyright Notice:
# Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/LICENSE.md

"""
File : markdown_generator.py

Brief : This file contains definitions for the MarkdownGenerator class.

Initial author: Second Rise LLC.
"""
from . import DocFormatter

class MarkdownGenerator(DocFormatter):
    """Provides methods for generating markdown from Redfish schemas.

    Markdown is targeted to the Slate documentation tool: https://github.com/lord/slate
    """


    def __init__(self, property_data, traverser, config, level=0):
        super(MarkdownGenerator, self).__init__(property_data, traverser, config, level)
        self.sections = []
        self.separators = {
            'inline': ', ',
            'linebreak': '\n'
            }


    def format_property_row(self, schema_name, prop_name, prop_info, current_depth=0):
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
        collapse_array = False # Should we collapse a list description into one row? For lists of simple types

        if isinstance(prop_info, list):
            meta = prop_info[0].get('_doc_generator_meta')
        elif isinstance(prop_info, dict):
            meta = prop_info.get('_doc_generator_meta')
        if not meta:
            meta = {}

        if prop_name:
            name_and_version = self.bold(self.escape_for_markdown(prop_name,
                                                                  self.config['escape_chars']))
        else:
            name_and_version = ''

        deprecated_descr = None
        if 'version' in meta:
            version_display = self.truncate_version(meta['version'], 2) + '+'
            # if 'version_deprecated' in meta:
                # deprecated_display = self.truncate_version(meta['version_deprecated'], 2)
                # name_and_version += ' ' + self.italic('(v' + version_display +
                # ', deprecated v' + deprecated_display +  ')')
            # else:
            name_and_version += ' ' + self.italic('(v' + version_display + ')')
        # elif 'version_deprecated' in meta:
        if 'version_deprecated' in meta:
            import pdb; pdb.set_trace()
            # deprecated_display = self.truncate_version(meta['version_deprecated'], 2)
            # name_and_version += ' ' + self.italic('(deprecated v' + deprecated_display +  ')')
            deprecated_descr = self.escape_for_markdown(meta['version_deprecated'],
                                                        self.config['escape_chars'])

        formatted_details = self.parse_property_info(schema_name, prop_name, prop_info, current_depth)

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

        if formatted_details['add_link_text']:
            if formatted_details['descr']:
                formatted_details['descr'] += ' '
            formatted_details['descr'] += formatted_details['add_link_text']

        # If there are prop_details (enum details), add a note to the description:
        if formatted_details['has_direct_prop_details']:
            text_descr = 'See Property Details, below, for more information about this property.'
            formatted_details['descr'] += ' ' + self.italic(text_descr)

        if formatted_details['has_action_details']:
            text_descr = 'For more information, see the Action Details section below.'
            formatted_details['descr'] += ' ' + self.italic(text_descr)

        if deprecated_descr:
            formatted_details['descr'] += ' ' + self.italic(deprecated_descr)

        prop_type = formatted_details['prop_type']

        if formatted_details['prop_units']:
            prop_type += '<br>(' + formatted_details['prop_units'] + ')'

        if collapse_array:
            item_list = formatted_details['item_list']
            if len(item_list):
                if isinstance(item_list, list):
                    item_list = ', '.join(item_list)
                prop_type += ' (' + item_list + ')'


        if formatted_details['read_only']:
            prop_type += '<br><br>' + self.italic('read-only')
        else:
            prop_type += '<br><br>' + self.italic('read-write')

        row = []
        row.append(indentation_string + name_and_version)
        row.append(prop_type)
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
                'action_details':formatted_details.get('action_details')})


    def format_property_details(self, prop_name, prop_type, enum, enum_details,
                                supplemental_details):
        """Generate a formatted table of enum information for inclusion in Property Details."""

        contents = []
        contents.append(self.head_three(prop_name + ':'))

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


    def link_to_own_schema(self, schema_name):
        """Format a reference to a schema in this project's namespace"""
        return self.italic(schema_name)


    def link_to_outside_schema(self, schema_uri):
        """Format a reference to a schema_uri, which should be a valid URI"""
        return self.italic('['+ schema_uri + '](' + schema_uri + ')')


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

        intro = supplemental.get('Introduction')
        if intro:
            intro = self.process_intro(intro)
            prelude += '\n' + intro + '\n'
        contents = [prelude, body]
        if 'Postscript' in supplemental:
            contents.append('\n' + supplemental['Postscript'])
        return '\n'.join(contents)


    def process_intro(self, intro_blob):
        """ Process the intro text, generating and inserting any schema fragments """
        parts = []
        intro = []
        part_text = []

        fragment_config = {
            'schema_root_uri': self.config['schema_root_uri'],
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
        """ Add a top-level heading """
        self.this_section = {'head': text,
                             'heading': '\n' + self.head_one(text),
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
