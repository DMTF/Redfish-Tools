# Copyright Notice:
# Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/LICENSE.md

"""
File : doc_formatter.py

Brief : Contains DocFormatter class

Initial author: Second Rise LLC.
"""

class DocFormatter:
    """Generic class for schema documentation formatter"""

    # How far to drill into objects/lists. 0-based.
    max_drilldown = 1

    def __init__(self, property_data, traverser, config):
        """Set up the markdown generator.

        property_data: pre-processed schemas.
        traverser: SchemaTraverser object
        config: configuration dict
        """
        self.property_data = property_data
        self.traverser = traverser
        self.config = config
        self.separators = {
            'inline': ', ',
            'linebreak': '<br>'
            }


    def emit(self):
        """ Output contents thus far """
        raise NotImplementedError


    def add_section(self, text):
        """ Add a top-level heading """
        raise NotImplementedError


    def add_description(self, text):
        """ Add the schema description """
        raise NotImplementedError


    def add_json_payload(self, json_payload):
        """ Add a JSON payload for the current section """
        raise NotImplementedError


    def add_property_row(self, formatted_row):
        """Add a row (or group of rows) for an individual property in the current section/schema.

        formatted_row should be a chunk of text already formatted for output"""
        raise NotImplementedError


    def add_property_details(self, formatted_details):
        """Add a chunk of property details information for the current section/schema."""
        raise NotImplementedError


    def format_property_row(self, schema_name, prop_name, prop_info, meta=None, current_depth=0):
        """Format information for a single property. Returns an object with 'row' and 'details'.

        'row': content for the main table being generated.
        'details': content for the Property Details section.

        This may include embedded objects with their own properties.
        """
        raise NotImplementedError


    def format_property_details(self, prop_name, prop_type, enum, enum_details, supplemental_details):
        """Generate a formatted table of enum information for inclusion in Property Details."""
        raise NotImplementedError


    def format_list_of_object_descriptions(self, schema_name, prop_items, traverser, current_depth):
        """Format a (possibly nested) list of embedded objects.

        We expect this to amount to one definition, usually for 'items' in an array."""
        raise NotImplementedError


    def output_document(self):
        """Return full contents of document"""
        body = self.emit()
        return body


    def generate_output(self):
        """Generate formatted from schemas and supplemental data.

        Iterates through property_data and traverses schemas for details.
        Format of output will depend on the format_* methods of the class.
        """

        property_data = self.property_data
        traverser = self.traverser
        config = self.config

        schema_names = [x for x in property_data.keys()]
        schema_names.sort()
        schema_supplement = config.get('schema_supplement', {})

        for schema_name in schema_names:
            # Skip schemas in the excluded list:
            if self.skip_schema(schema_name):
                continue
            details = property_data[schema_name]

            # Look up supplemental details for this schema/version
            version = details.get('latest_version', '1')
            major_version = version.split('.')[0]
            schema_key = schema_name + '_' + major_version
            supplemental = schema_supplement.get(schema_key, {})

            if 'doc_generator_meta' not in details:
                print("WARNING: no meta data for", schema_name)
                continue
            doc_generator_meta = details['doc_generator_meta']
            definitions = details['definitions']
            properties = details['properties']

            # No output for definition-only schema.
            if len(properties) == 0:
                continue

            self.add_section(details['name_and_version'])

            # Normative docs prefer longDescription to description
            if config['normative'] and 'longDescription' in definitions[schema_name]:
                description = definitions[schema_name].get('longDescription')
            else:
                description = definitions[schema_name].get('description')

            # Override with supplemental schema description, if provided
            description = supplemental.get('Description', description)

            if description:
                self.add_description(description)

            self.add_json_payload(supplemental.get('JSONPayload'))

            if 'properties' in details.keys():
                prop_details = {}

                properties = details['properties']
                prop_names = [x for x in properties.keys()]
                prop_names = self.organize_prop_names(prop_names)

                for prop_name in prop_names:

                    meta = doc_generator_meta.get(prop_name, {})
                    prop_info = properties[prop_name]
                    prop_info = self.extend_property_info(schema_name, prop_info, traverser)

                    formatted = self.format_property_row(schema_name, prop_name, prop_info, meta)
                    if formatted:
                        self.add_property_row(formatted['row'])
                        if formatted['details']:
                            prop_details.update(formatted['details'])

                if len(prop_details):
                    prop_details_sorted = []
                    detail_names = [x for x in prop_details.keys()]
                    detail_names.sort()
                    for x in detail_names:
                        self.add_property_details(prop_details[x])

        return self.output_document()


    def extend_property_info(self, schema_name, prop_info, traverser):
        """If prop_info contains a $ref or anyOf attribute, extend it with that information.

        Returns an array of objects. Arrays of arrays of objects are possible but not expected.
        """

        prop_ref = prop_info.get('$ref', None)
        prop_anyOf = prop_info.get('anyOf', None)
        prop_infos = []

        # Properties to carry through from parent when a ref is extended:
        parent_props = ['description', 'longDescription']

        if prop_ref:

            if '#/definitions/idRef' in prop_ref:
                # Bit of a hack here, because we don't currently parse odata
                ref_info = {
                    "type": "object",
                    "properties" :
                    {
                        "@odata.id": {
                            "type": "string",
                            "format": "uri",
                            "readonly": True,
                            "description": "The unique identifier for a resource.",
                            "longDescription": "The value of this property shall be the unique identifier for the resource and it shall be of thee form defined in the Redfish specification."
                        }
                    },
                    "description": "A reference to a resource.",
                    "longDescription": "The value of this property shall be used for references to a resource."
                    }

            else:
                prop_ref = traverser.parse_ref(prop_ref, schema_name)
                ref_info = traverser.find_ref_data(prop_ref)

            if ref_info:
                # if specific attributes were defined in addition to a $ref, update with them:
                for x in prop_info.keys():
                    if x in parent_props:
                        ref_info[x] = prop_info[x]

                prop_info = ref_info

                if '$ref' in ref_info or 'anyOf' in ref_info:
                    return self.extend_property_info(ref_info['_from_schema_name'], ref_info, traverser)

            prop_infos.append(prop_info)

        elif prop_anyOf:
            for elt in prop_anyOf:
                if '$ref' in elt:
                    for x in prop_info.keys():
                        if x in parent_props:
                            elt[x] = prop_info[x]

                elt = self.extend_property_info(schema_name, elt, traverser)
                prop_infos.append(elt)

        else:
            prop_infos.append(prop_info)

        return prop_infos


    def organize_prop_names(self, prop_names):
        """Strip out excluded property names, and sort the remainder."""

        # Strip out properties based on exact match:
        prop_names = [x for x in prop_names if x not in self.config['excluded_properties']]

        # Strip out properties based on partial match:
        included_prop_names = []
        for prop_name in prop_names:
            excluded = False
            for x in self.config['excluded_by_match']:
                if x in prop_name:
                    excluded = True
                    break
            if not excluded:
                included_prop_names.append(prop_name)

        included_prop_names.sort()
        return included_prop_names

    def skip_schema(self, schema_name):
        if schema_name in self.config['excluded_schemas']:
            return True
        for pattern in self.config['excluded_schemas_by_match']:
            if pattern in schema_name:
                return True
        return False


    def parse_property_info(self, schema_name, prop_name, traverser, prop_infos, current_depth):
        """Parse a list of one more more property info objects into strings for display.

        Returns a dict of 'prop_type', 'read_only', descr', 'prop_is_object',
        'prop_is_array', 'object_description', 'prop_details', 'item_description',
        'has_direct_prop_details'
        """

        if len(prop_infos) == 1:
            prop_info = prop_infos[0]
            if isinstance(prop_info, dict):
                return self._parse_single_property_info(schema_name, prop_name, prop_info, current_depth)
            else:
                return self.parse_property_info(schema_name, prop_name, prop_info, current_depth)

        parsed = {'prop_type': [],
                  'prop_units': False,
                  'read_only': False,
                  'descr': [],
                  'prop_is_object': False,
                  'prop_is_array': False,
                  'object_description': [],
                  'item_description': [],
                  'prop_details': {},
                  'has_direct_prop_details': False}

        anyOf_details = [self.parse_property_info(schema_name, prop_name, traverser, x, current_depth) for x in prop_infos]

        # Remove details for anyOf props with prop_type = 'null'.
        details = []
        has_null = False
        for det in anyOf_details:
            if len(det['prop_type']) == 1 and 'null' in det['prop_type']:
                has_null = True
            else:
                details.append(det)

        # Uniquify these properties and save as lists:
        props_to_combine = ['prop_type', 'descr', 'object_description', 'item_description']

        for property_name in props_to_combine:
            property_values = []
            for det in anyOf_details:
                if isinstance(det[property_name], list):
                    for val in det[property_name]:
                        if val and val not in property_values:
                            property_values.append(val)
                else:
                    val = det[property_name]
                    if val and val not in property_values:
                        property_values.append(val)

            parsed[property_name] = property_values

        # add back null if we found one:
        if has_null:
            parsed['prop_type'].append('null')

        # read_only and units should be the same for all
        parsed['read_only'] = details[0]['read_only']
        parsed['prop_units'] = details[0]['prop_units']

        for det in details:
            parsed['prop_is_object'] |= det['prop_is_object']
            parsed['prop_is_array'] |= det['prop_is_array']
            parsed['has_direct_prop_details'] |= det['has_direct_prop_details']
            parsed['prop_details'].update(det['prop_details'])

        return parsed


    def _parse_single_property_info(self, schema_name, prop_name, prop_info, current_depth):
        """Parse definition of a specific property into strings for display.

        Returns a dict of 'prop_type', 'prop_units', 'read_only', descr', 'prop_is_object',
        'prop_is_array', 'object_description', 'prop_details', 'item_description',
        'has_direct_prop_details'
        """

        traverser = self.traverser

        # type may be a string or a list.
        prop_details = {}
        prop_type = prop_info.get('type', [])
        prop_is_object = False; object_description = ''
        prop_is_array = False; item_description = ''
        has_prop_details = False

        if isinstance(prop_type, list):
            prop_is_object = 'object' in prop_type
            prop_is_array = 'array' in prop_type
        else:
            prop_is_object = prop_type == 'object'
            prop_is_array = prop_type == 'array'
            prop_type = [ prop_type ]

        prop_units = prop_info.get('units')

        read_only = prop_info.get('readonly')
        if self.config['normative'] and 'longDescription' in prop_info:
            descr = prop_info.get('longDescription', '')
        else:
            descr = prop_info.get('description', '')

        # Items, if present, will have a definition with either an object or a $ref:
        prop_item = prop_info.get('items')
        if isinstance(prop_item, dict):
            prop_items = self.extend_property_info(schema_name, prop_item, traverser)

        # Enumerations go into Property Details
        prop_enum = prop_info.get('enum')
        supplemental_details = None

        if 'supplemental' in self.config and 'Property Details' in self.config['supplemental']:
            detconfig = self.config['supplemental']['Property Details']
            if schema_name in detconfig and prop_name in detconfig[schema_name]:
                supplemental_details = detconfig[schema_name][prop_name]

        if prop_enum or supplemental_details:
            has_prop_details = True

            if self.config['normative'] and 'enumLongDescriptions' in prop_info:
                prop_enum_details = prop_info.get('enumLongDescriptions')
            else:
                prop_enum_details = prop_info.get('enumDescriptions')
            prop_details[prop_name] = self.format_property_details(prop_name, prop_type, prop_enum, prop_enum_details,
                                                              supplemental_details)

        # embedded object:
        if current_depth < self.max_drilldown and prop_is_object:
            object_formatted = self.format_object_description(schema_name, prop_info, traverser, current_depth)
            object_description = object_formatted['rows']
            if object_formatted['details']:
                prop_details.update(object_formatted['details'])

        # embedded items:
        if current_depth < self.max_drilldown and prop_is_array:
            item_formatted = self.format_list_of_object_descriptions(schema_name, prop_items, traverser, current_depth)
            item_description = item_formatted['rows']
            if item_formatted['details']:
                prop_details.update(item_formatted['details'])

        return {'prop_type': prop_type,
                'prop_units': prop_units,
                'read_only': read_only,
                'descr': descr,
                'prop_is_object': prop_is_object,
                'prop_is_array': prop_is_array,
                'object_description': object_description,
                'item_description': item_description,
                'prop_details': prop_details,
                'has_direct_prop_details': has_prop_details}


    def format_object_description(self, schema_name, prop_info, traverser, current_depth=0):
        """Format the properties for an embedded object."""

        properties = prop_info.get('properties')
        output = []
        details = {}

        # If prop_info was extracted from a different schema, it will be present as _from_schema_name
        schema_name = prop_info.get('_from_schema_name', schema_name)

        if properties:
            prop_names = [x for x in properties.keys()]
            prop_names = self.organize_prop_names(prop_names)
            for prop_name in prop_names:
                base_detail_info = properties[prop_name]
                detail_info = self.extend_property_info(schema_name, base_detail_info, traverser)

                depth = current_depth + 1
                formatted = self.format_property_row(schema_name, prop_name, detail_info,
                                                     {}, current_depth=depth)
                if formatted:
                    output.append(formatted['row'])
                    if formatted['details']:
                        details.update(formatted['details'])

        return {'rows': output, 'details': details}


    @staticmethod
    def truncate_version(version_string, num_parts):
        """Truncate the version string to the specified number of parts."""

        parts = version_string.split('.')
        return '.'.join(parts[0:num_parts])
