"""
File : schema_traverser.py

Brief : Provides utilities for resolving references in a set of Redfish json schema objects.


Initial author: Second Rise LLC.

The Distributed Management Task Force (DMTF) grants rights under copyright in
this software on the terms of the BSD 3-Clause License as set forth below; no
other rights are granted by DMTF. This software might be subject to other rights
(such as patent rights) of other parties.

Copyrights.

Copyright (c) 2016, Contributing Member(s) of Distributed Management Task Force,
Inc.. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.

    Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

    Neither the name of the Distributed Management Task Force (DMTF) nor the
    names of its contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Patents.

This software may be subject to third party patent rights, including provisional
patent rights ("patent rights"). DMTF makes no representations to users of the
standard as to the existence of such rights, and is not responsible to
recognize, disclose, or identify any or all such third party patent right,
owners or claimants, nor for any incomplete or inaccurate identification or
disclosure of such rights, owners or claimants. DMTF shall have no liability to
any party, in any manner or circumstance, under any legal theory whatsoever, for
failure to recognize, disclose, or identify any such third party patent rights,
or for such party’s reliance on the software or incorporation thereof in its
product, protocols or testing procedures. DMTF shall have no liability to any
party using such software, whether such use is foreseeable or not, nor to any
patent owner or claimant, and shall have no liability or responsibility for
costs or losses incurred if software is withdrawn or modified after publication,
and shall be indemnified and held harmless by any party using the software from
any and all claims of infringement by a patent owner for such use.

DMTF Members that contributed to this software source code might have made
patent licensing commitments in connection with their participation in the DMTF.
For details, see http://dmtf.org/sites/default/files/patent-10-18-01.pdf and
http://www.dmtf.org/about/policies/disclosures.
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
