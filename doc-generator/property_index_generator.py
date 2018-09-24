# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File : property_index_generator.py

Brief : This file contains definitions for the PropertyIndexGenerator class.

Initial author: Second Rise LLC.
"""

import copy
import io
import warnings

class PropertyIndexGenerator():
    """Provides methods for generating Property Index docs from Redfish schemas."""

    def __init__(self, property_data, traverser, config):
        """
        property_data: pre-processed schemas.
        traverser: SchemaTraverser object
        config: configuration dict
        """
        self.property_data = property_data
        self.traverser = traverser
        self.config = config
        self.level = level
        self.this_section = None

        self.properties_by_name = {}
        # Expected format of properties_by_name once populated:
        # { property_name: [ { schemas: [schema1, schema2], type: type, description: description },
        #                    { schemas: [schema3], type: type, description: description },
        #                    ]}
        #
        # Once we've generated this, we'll want to output by property_name (alpha),
        # combining definitions where type and description are exact matches.


    def generate_output(self):
        # self.gather_property_definitions();
        # self.combine_property_definitions();
        # return self.output_formatted();
        return "TODO"


    def gather_property_definitions(self):
        """ Traverse schemas, gathering property definitions. """
        pass


    def combine_property_definitions(self):
        """ For each property_name in properties_by_name, combine any entries where both type and definition match. """
        pass


    def output_formatted(self):
        """ Output properties_by_name according to requested output format. """
        pass
