# Copyright Notice:
# Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/LICENSE.md

"""
File : schema_traverser.py

Brief : Provides utilities for resolving references in a set of Redfish json schema objects.


Initial author: Second Rise LLC.
"""

class SchemaTraverser:
    """Provides methods for traversing Redfish schemas (imported from JSON into objects). """

    def __init__(self, root_uri, schema_data):
        """Set up the SchemaTraverser.

        root_uri: is the string to strip from absolute refs. Typically 'http://redfish.dmtf.org/schemas/v1/'
        schema_data: dict of schema_name: json_data
        """
        self.root_uri = root_uri
        self.schemas = schema_data


    def find_ref_data(self, ref):
        """Find data identified by ref within self.schemas."""

        schema_name, path = ref.split('#')

        schema = self.schemas.get(schema_name, None)
        if not schema:
            return None

        elements = [x for x in path.split('/') if x]
        for element in elements:
            if element in schema:
                schema = schema[element]
            else:
                return None

        schema['_from_schema_name'] = schema_name
        return schema


    def parse_ref(self, ref, from_schema):
        """Given a $ref string, normalize it to schema_name#path.

        Removes root_uri and, if the $ref is internal, adds back the from_schema name.
        """
        if ref[0] == '#':
            ref = from_schema + ref
        else:
            # ref format is [url path/filename]#refpath
            prop_ref_uri, prop_ref_path = ref.split('#')
            skip, skip, target_schema = prop_ref_uri.rpartition('/')
            target_schema = target_schema[:-5]
            ref = target_schema + '#' + prop_ref_path

        return ref
