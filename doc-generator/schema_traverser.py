# Copyright Notice:
# Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File : schema_traverser.py

Brief : Provides utilities for resolving references in a set of Redfish json schema objects.


Initial author: Second Rise LLC.
"""

import types
import warnings
from doc_gen_util import DocGenUtilities

# Format user warnings simply
def simple_warning_format(message, category, filename, lineno, file=None, line=None):
    """ a basic format for warnings from this program """
    return '  Warning: %s (%s:%s)' % (message, filename, lineno) + "\n"

warnings.formatwarning = simple_warning_format


class SchemaTraverser:
    """Provides methods for traversing Redfish schemas (imported from JSON into objects). """

    def __init__(self, schema_data, meta_data, uri_to_local):
        """Set up the SchemaTraverser.

        schema_data: dict of normalized_schema_uri: json_data
        meta_data: metadata (versioning) by schema and property
        uri_to_local: dict of normalized URI: local path
        """
        self.schemas = types.MappingProxyType(schema_data)
        self.meta = types.MappingProxyType(meta_data)
        self.uri_to_local = types.MappingProxyType(uri_to_local)
        self.remote_schemas = types.MappingProxyType({}) # dict of uri:json_data retrieved dynamically


    def copy(self):
        """Create a traverser with equivalent state to this one's"""
        return SchemaTraverser(self.schemas, self.meta, self.uri_to_local)


    def add_schema(self, uri, data):
        """Add the specified schema data to self.schemas. Fails if uri is already present"""

        if not self.schemas.get(uri):
            mutable_schemas = dict(self.schemas)
            mutable_schemas[uri] = data
            self.schemas = types.MappingProxyType(mutable_schemas)
        else:
            warnings.warn("Not overwriting traverser's schema data for " + uri)


    def find_ref_data(self, ref):
        """Find data identified by ref within self.schemas."""

        if '#' not in ref:
            return None
        schema_ref, path = self.get_schema_ref_and_path(ref)
        if self.ref_to_own_schema(ref):
            schema = self.schemas.get(schema_ref, None)
            if not schema:
                return None

        else:
            schema = self.get_remote_schema(ref)
            if not schema:
                return None

        meta = self.meta.get(schema_ref, {})

        elements = [x for x in path.split('/') if x]
        element = ''
        for element in elements:
            if element in schema:
                schema = schema[element]
                meta = meta.get(element, {})
            else:
                return None

        schema = dict(schema)
        schema['_from_schema_ref'] = schema_ref
        if '_schema_name' not in schema:
            schema['_schema_name'] = self.get_schema_name(schema_ref)
        schema['_prop_name'] = element
        schema['_doc_generator_meta'] = meta
        schema['_ref_uri'] = ref
        return schema


    def find_meta_data(self, ref):
        """Find meta data identified by ref within self.meta."""

        schema_ref, path = self.get_schema_ref_and_path(ref)

        meta = self.meta.get(schema_ref)
        if not meta:
            return {}

        elements = [x for x in path.split('/') if x]
        for element in elements:
            if element in schema:
                meta = meta.get(element)
            else:
                return {}

        return meta


    def get_schema_name(self, ref):
        """Get the schema name for the given ref."""
        schema_ref, path = self.get_schema_ref_and_path(ref)
        schema = self.schemas.get(schema_ref)
        if schema:
            return schema.get('_schema_name')

        schema = self.get_remote_schema(ref)
        if schema:
            return schema.get('_schema_name', ref)

        return ref


    def ref_to_own_schema(self, ref):
        """Does this $ref point to one of our own schemas? """

        if '#' not in ref:
            return False

        schema_ref, path = self.get_schema_ref_and_path(ref)

        if self.schemas.get(schema_ref):
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


    def get_node_from_ref(self, ref):
        """Convenience method to get the final node from a $ref. """
        _, _, node = ref.rpartition('/')
        return node


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


    def get_remote_schema(self, uri):
        """Attempt to retrieve schema by URI (or find it in our cache)"""

        if '#' in uri:
            uri, path = uri.split('#')

        schema_data = self.remote_schemas.get(uri)

        if schema_data:
            return schema_data

        # Do we have a mapping for this remote URI to a local path?
        if '://' in uri:
            protocol, uri_part = uri.split('://')
        else:
            uri_part = uri
        for partial_uri in self.uri_to_local.keys():
            if uri_part.startswith(partial_uri):
                local_uri = self.uri_to_local[partial_uri] + uri_part[len(partial_uri):]
                schema_data = DocGenUtilities.load_as_json(local_uri)
                # This will fall through to getting the schema remotely if this fails. Correct?
                if schema_data:
                    return schema_data

        schema_data = DocGenUtilities.http_load_as_json(uri)
        if schema_data:
            schema_data['_schema_name'] = self.find_schema_name(uri, schema_data)
            self.add_remote_schema(uri, schema_data)
            return schema_data

        return None


    def add_remote_schema(self, uri, schema_data):
        """ Add an entry to remote_schemas. """

        mutable_remote_schemas = dict(self.remote_schemas)
        mutable_remote_schemas[uri] = schema_data
        self.remote_schemas = types.MappingProxyType(mutable_remote_schemas)


    @staticmethod
    def get_schema_ref_and_path(ref):
        """Get the normalized ref to the schema, and the path part.

        This is the full URI of the json file, minus protocol.
        """

        if '#' in ref:
            schema_ref, path = ref.split('#')
        else:
            schema_ref = ref
            path = ''

        if '://' in schema_ref:
            protocol, schema_ref = schema_ref.split('://')

        return schema_ref, path


    @staticmethod
    def find_schema_name(filename, data, unversioned=False):
        """Get the schema name, preferably from a 'title' found in the data, otherwise from filename

        Returns a string or None, the latter indicating that this is an old-style schema that
        should be skipped."""

        schema_name = None

        if 'title' not in data:
            schema_name = filename[:-5]
        else:
            title_parts = data['title'].split('.')
            if len(title_parts) > 3:
                return None

            schema_name = title_parts[-1]
            for tp in title_parts:
                if tp.startswith('v'):
                    schema_name += '.' + title_parts[1]
                    break

            if schema_name[0] == '#':
                schema_name = schema_name[1:]

        if unversioned:
            schema_name, _, _ = schema_name.partition('.')

        return schema_name
