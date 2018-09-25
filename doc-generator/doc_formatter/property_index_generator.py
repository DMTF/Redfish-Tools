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
        # Expected format of properties_by_name once populated:
        # { property_name: [ { schemas: [schema1, schema2], prop_type: type, description: description },
        #                    { schemas: [schema3], prop_type: type, description: description },
        #                    ]}
        #
        # Once we've generated this, we'll want to output by property_name (alpha),
        # combining definitions where prop_type and description are exact matches.

        # Force some config here:
        self.config['omit_version_in_headers'] = True # This puts just the schema name in the section head.


    def emit(self):
        """ Return the data! """
        import pdb; pdb.set_trace()
        pass


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

        details = self.parse_property_info(schema_ref, prop_name, prop_info, prop_path)

        schema_path_formatted = self.this_section['schema_name']
        if len(prop_path):
            schema_path_formatted += ' (' + ' > '.join(prop_path) + ')'

        description_entry = {
            'schemas': [ schema_path_formatted ], 'prop_type': details.get('prop_type')
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


    # def add_property_row(

    def add_registry_reqs(self, registry_reqs):
        """ output doesn't include registry requirements. """
        pass
