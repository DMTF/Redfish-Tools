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

        root_uri: is the string to strip from absolute refs.
                  Typically 'http://redfish.dmtf.org/schemas/v1/'
        schema_data: dict of schema_name: json_data
        """

        # Ensure root_uri has a trailing slash.
        if root_uri[-1] != '/':
            root_uri += '/'

        self.root_uri = root_uri
        self.schemas = schema_data


    def find_ref_data(self, ref):
        """Find data identified by ref within self.schemas."""

        if '#' not in ref:
            return None

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
        schema['_prop_name'] = element

        # Rebuild the ref for this item.
        ref_uri = self.root_uri + schema_name + '.json' + '#' + path
        schema['_ref_uri'] = ref_uri
        return schema


    def ref_to_own_schema(self, ref):
        """Does this $ref point to one of our own schemas? """

        if '#' not in ref:
            return False

        prop_ref_uri = ref.split('#')[0]

        if not prop_ref_uri:
            return True

        if prop_ref_uri.startswith(self.root_uri):
            return True

        dir_end = prop_ref_uri.rfind('/')
        if dir_end > -1:
            schema_name = prop_ref_uri[dir_end+1:]
            schema_name = schema_name[:-5] # remove '.json' suffix
            if self.schemas.get(schema_name):
                return True

        return False


    def parse_ref(self, ref, from_schema=''):
        """Given a $ref string, normalize it to schema_name#path.

        Removes path part of URI and, if the $ref is internal, adds back the from_schema name.
        """

        if '#' not in ref:
            return None

        if ref[0] == '#':
            ref = from_schema + ref
        else:
            # ref format is [url path/filename]#refpath
            prop_ref_uri, prop_ref_path = ref.split('#')
            _, _, target_schema = prop_ref_uri.rpartition('/')
            target_schema = target_schema[:-5] # remove '.json' suffix
            ref = target_schema + '#' + prop_ref_path

        return ref


    def is_versioned_schema(self, schema_name):
        """Given a schema name (unversioned), return True if it has refs to versioned schemas"""

        schema = self.schemas.get(schema_name, None)
        if schema:
            return schema.get('_is_versioned_schema')
        return None


    def is_collection_of(self, schema_name):
        """Given a schema name (unversioned), return True if it's a redfish collection schema"""

        schema = self.schemas.get(schema_name, None)
        if schema:
            return schema.get('_is_collection_of')
        return None


    def is_known_schema(self, schema_name):
        """Is this a schema we can traverse, basically."""

        schema = self.schemas.get(schema_name, None)
        if schema:
            return True
        return None



    def get_uri_for_schema(self, schema_name):
        """Given a schema name (versioned or unversioned), return the URI for it."""

        if self.schemas.get(schema_name, None):
            return self.root_uri + schema_name + '.json'
        return None
