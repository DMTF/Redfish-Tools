#! /usr/bin/python3
# Copyright Notice:
# Copyright 2017-2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
CSDL to JSON Schema

File : csdl-to-json.py

Brief : This file contains the definitions and functionalities for converting
        Redfish CSDL files to Redfish JSON Schema files.
"""

import argparse
import copy
import errno
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

# Default configurations
CONFIG_DEF_COPYRIGHT = "Copyright 2014-2019 DMTF. For the full DMTF copyright policy, see http://www.dmtf.org/about/policies/copyright"
CONFIG_DEF_REDFISH_SCHEMA = "http://redfish.dmtf.org/schemas/v1/redfish-schema-v1.json"
CONFIG_DEF_ODATA_SCHEMA = "http://redfish.dmtf.org/schemas/v1/odata-v4.json"
CONFIG_DEF_LOCATION = "http://redfish.dmtf.org/schemas/v1/"
CONFIG_DEF_RESOURCE_LOCATION = "http://redfish.dmtf.org/schemas/v1/"

# Regex strings
VERSION_REGEX = "v([0-9]+)_([0-9]+)_([0-9]+)$"
PATTERN_PROP_REGEX = "^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\\.[a-zA-Z_][a-zA-Z0-9_]*$"
PATTERN_PROP_ACTION_REGEX = "^#([a-zA-Z_][a-zA-Z0-9_]*\\.)+[a-zA-Z_][a-zA-Z0-9_]*$"
DEFAULT_VER = "v1_0_0"
DEFAULT_ATTRIB = "UNKNOWN_ATTRIB"

# OData markup strings
ODATA_TAG_REFERENCE = "{http://docs.oasis-open.org/odata/ns/edmx}Reference"
ODATA_TAG_INCLUDE = "{http://docs.oasis-open.org/odata/ns/edmx}Include"
ODATA_TAG_SCHEMA = "{http://docs.oasis-open.org/odata/ns/edm}Schema"
ODATA_TAG_ENTITY = "{http://docs.oasis-open.org/odata/ns/edm}EntityType"
ODATA_TAG_COMPLEX = "{http://docs.oasis-open.org/odata/ns/edm}ComplexType"
ODATA_TAG_ENUM = "{http://docs.oasis-open.org/odata/ns/edm}EnumType"
ODATA_TAG_ACTION = "{http://docs.oasis-open.org/odata/ns/edm}Action"
ODATA_TAG_TYPE_DEF = "{http://docs.oasis-open.org/odata/ns/edm}TypeDefinition"
ODATA_TAG_ANNOTATION = "{http://docs.oasis-open.org/odata/ns/edm}Annotation"
ODATA_TAG_PROPERTY = "{http://docs.oasis-open.org/odata/ns/edm}Property"
ODATA_TAG_NAV_PROPERTY = "{http://docs.oasis-open.org/odata/ns/edm}NavigationProperty"
ODATA_TAG_PARAMETER = "{http://docs.oasis-open.org/odata/ns/edm}Parameter"
ODATA_TAG_MEMBER = "{http://docs.oasis-open.org/odata/ns/edm}Member"
ODATA_TAG_RECORD = "{http://docs.oasis-open.org/odata/ns/edm}Record"
ODATA_TAG_PROP_VAL = "{http://docs.oasis-open.org/odata/ns/edm}PropertyValue"
ODATA_TAG_COLLECTION = "{http://docs.oasis-open.org/odata/ns/edm}Collection"
ODATA_TAG_STRING = "{http://docs.oasis-open.org/odata/ns/edm}String"
ODATA_TAG_RETURN = "{http://docs.oasis-open.org/odata/ns/edm}ReturnType"

class CSDLToJSON:
    """
    Class for managing translation data and processing

    Args:
        copyright: The copyright string to use
        redfish_schema: The Redfish JSON Schema file to reference
        odata_schema: The OData JSON Schema file to reference
        location: The output location for the generated schemas
        root: The ET object of the XML file being processed
        resource_root: The ET object of the Resource XML file
    """

    def __init__( self, copyright, redfish_schema, odata_schema, location, resource_location, root, resource_root ):
        self.copyright = copyright
        self.redfish_schema = redfish_schema
        self.odata_schema = odata_schema
        self.location = location
        self.resource_location = resource_location
        self.root = root
        self.resource_root = resource_root
        self.resource_props = []
        self.ref_member_props = []
        self.resource_collection_props = []
        self.links_props = []
        self.cache_resource_definitions()
        self.namespace_under_process = None
        self.external_references = {}
        self.internal_references = {}
        self.build_references()
        self.json_out = {}
        self.errors = {}
        self.initialize_json_output()

    def cache_resource_definitions( self ):
        """
        Processes the Resource XML document to cache core definitions
        """

        # Look for the Resource, ReferenceableMembers, ResourceCollection, and Links definitions
        for schema in self.resource_root.iter( ODATA_TAG_SCHEMA ):
            for child in schema:
                if ( child.tag == ODATA_TAG_ENTITY ) or ( child.tag == ODATA_TAG_COMPLEX ):
                    name = self.get_attrib( schema, "Namespace" ) + "." + self.get_attrib( child, "Name" )

                    if ( name == "Resource.v1_0_0.Resource" ) or ( name == "Resource.Item" ):
                        for prop in child:
                            if ( prop.tag == ODATA_TAG_PROPERTY ) or ( prop.tag == ODATA_TAG_NAV_PROPERTY ):
                                self.resource_props.append( prop )

                    if ( name == "Resource.v1_0_0.ReferenceableMember" ) or ( name == "Resource.Item" ):
                        for prop in child:
                            if ( prop.tag == ODATA_TAG_PROPERTY ) or ( prop.tag == ODATA_TAG_NAV_PROPERTY ):
                                self.ref_member_props.append( prop )

                    if name == "Resource.v1_0_0.ResourceCollection":
                        for prop in child:
                            if ( prop.tag == ODATA_TAG_PROPERTY ) or ( prop.tag == ODATA_TAG_NAV_PROPERTY ):
                                self.resource_collection_props.append( prop )

                    if name == "Resource.Links":
                        for prop in child:
                            if ( prop.tag == ODATA_TAG_PROPERTY ) or ( prop.tag == ODATA_TAG_NAV_PROPERTY ):
                                self.links_props.append( prop )

    def build_references( self ):
        """
        Processes the references of the XML document
        """

        # Create the external references
        for reference in self.root.iter( ODATA_TAG_REFERENCE ):
            for include in reference.iter( ODATA_TAG_INCLUDE ):
                # Based on the URI and the namespace, build the expected JSON Schema reference
                namespace = self.get_attrib( include, "Namespace" )
                alias = self.get_attrib( include, "Alias", False, namespace )
                self.external_references[alias] = self.get_attrib( reference, "Uri" ).rsplit( "/", 1 )[0] + "/" + namespace + ".json"

        # Need to add the unversioned Resource namespace since we copy in its base definitions
        self.external_references["Resource"] = self.resource_location + "Resource.json"

        # Create the internal references
        for schema in self.root.iter( ODATA_TAG_SCHEMA ):
            # We just need the namespace for error checking when the definition is built later
            self.internal_references[self.get_attrib( schema, "Namespace" )] = True

    def initialize_json_output( self ):
        """
        Initializes the output JSON structures for a given XML file
        """

        for schema in self.root.iter( ODATA_TAG_SCHEMA ):
            namespace = self.get_attrib( schema, "Namespace" )
            self.json_out[namespace] = {}
            self.json_out[namespace]["$schema"] = self.redfish_schema
            self.json_out[namespace]["copyright"] = self.copyright
            self.json_out[namespace]["definitions"] = {}
            self.json_out[namespace]["title"] = "#" + namespace
            self.json_out[namespace]["$id"] = self.location + namespace + ".json"
            self.errors[namespace] = False

    def process( self ):
        """
        Processes the given data to generate the JSON output
        """

        # Loop on each namespace and build each definition
        for namespace in self.json_out:
            self.namespace_under_process = namespace
            # Process the namespace based on if it's versioned or unversioned
            if is_namespace_unversioned( namespace ):
                self.process_unversioned_namespace()
            else:
                self.process_versioned_namespace()

        # Find all of the excerpts and make additional definitions
        for namespace in sorted( self.json_out ):
            self.namespace_under_process = namespace
            if not is_namespace_unversioned( namespace ):
                self.process_excerpts()

    def process_unversioned_namespace( self ):
        """
        Adds the definitions to the JSON output for an unversioned namespace
        """

        # Go through each namespace in the XML file
        for schema in self.root.iter( ODATA_TAG_SCHEMA ):
            # Only process the matching namespace
            namespace = self.get_attrib( schema, "Namespace" )
            if namespace == self.namespace_under_process:
                for child in schema:
                    # Set up the top level title and $ref properties if needed
                    if child.tag == ODATA_TAG_ENTITY:
                        base_type = self.get_attrib( child, "BaseType", False )
                        name = self.get_attrib( child, "Name" )
                        if ( base_type == "Resource.v1_0_0.Resource" ) or ( base_type == "Resource.v1_0_0.ResourceCollection" ) or ( base_type == "LineOfService.v1_0_0.LineOfService" ):
                            self.json_out[self.namespace_under_process]["title"] = "#" + self.namespace_under_process + "." + name
                            self.json_out[self.namespace_under_process]["$ref"] = "#/definitions/" + name

                    # Process EntityType and ComplexType definitions
                    if ( child.tag == ODATA_TAG_ENTITY ) or ( child.tag == ODATA_TAG_COMPLEX ):
                        # Check if the definition is abstract
                        is_abstract = False
                        if self.get_attrib( child, "Abstract", False ) == "true":
                            is_abstract = True
                        if ( child.tag == ODATA_TAG_COMPLEX ) and ( self.namespace_under_process == "Resource" ) and ( self.get_attrib( child, "Name" ) == "Links" ):
                            # Special override for the Links base definition; it needs to be standalone
                            is_abstract = False
                        if is_abstract:
                            self.generate_abstract_object( child, self.json_out[self.namespace_under_process]["definitions"] )
                        else:
                            self.generate_object( child, namespace, self.json_out[self.namespace_under_process]["definitions"] )
                        self.generate_capabilities( child, self.json_out[self.namespace_under_process]["definitions"] )
                        self.add_version_details( child, self.json_out[self.namespace_under_process]["definitions"][self.get_attrib( child, "Name" )] )

                    # Process Action definitions
                    # This is needed for OEM actions since there's no strong tie between a standard resource and an OEM action
                    # The unversioned definition will contain an anyOf to point to each version
                    if child.tag == ODATA_TAG_ACTION:
                        if self.is_oem_action( child ):
                            self.generate_abstract_object( child, self.json_out[self.namespace_under_process]["definitions"] )

                    # Process EnumType definitions
                    if child.tag == ODATA_TAG_ENUM:
                        self.generate_enum( child, self.json_out[self.namespace_under_process]["definitions"] )

                    # Process TypeDefinition definitions
                    if child.tag == ODATA_TAG_TYPE_DEF:
                        self.generate_typedef( child, self.json_out[self.namespace_under_process]["definitions"] )

                    # Process top level annotations
                    if child.tag == ODATA_TAG_ANNOTATION:
                        term = self.get_attrib( child, "Term" )

                        # Owning Entity
                        if term == "Redfish.OwningEntity":
                            self.json_out[self.namespace_under_process]["owningEntity"] = self.get_attrib( child, "String" )

                        # Release
                        if term == "Redfish.Release":
                            self.json_out[self.namespace_under_process]["release"] = self.get_attrib( child, "String" )

                        # Language
                        if term == "Redfish.Language":
                            self.json_out[self.namespace_under_process]["language"] = self.get_attrib( child, "String" )

    def process_versioned_namespace( self ):
        """
        Adds the definitions to the JSON output for a versioned namespace
        """

        # Go through each namespace in the XML file
        for schema in self.root.iter( ODATA_TAG_SCHEMA ):
            # Check if the namespace applies based on its version number
            namespace = self.get_attrib( schema, "Namespace" )
            if does_version_apply( namespace, self.namespace_under_process ):
                for child in schema:
                    # Set up the top level title and $ref properties if needed
                    if child.tag == ODATA_TAG_ENTITY:
                        base_type = self.get_attrib( child, "BaseType", False )
                        name = self.get_attrib( child, "Name" )
                        if ( base_type == "Resource.v1_0_0.Resource" ) or ( base_type == "Resource.v1_0_0.ResourceCollection" ) or ( base_type == "LineOfService.v1_0_0.LineOfService" ):
                            self.json_out[self.namespace_under_process]["title"] = "#" + self.namespace_under_process + "." + name
                            self.json_out[self.namespace_under_process]["$ref"] = "#/definitions/" + name

                    # Process EntityType and ComplexType definitions
                    if ( child.tag == ODATA_TAG_ENTITY ) or ( child.tag == ODATA_TAG_COMPLEX ):
                        if not is_namespace_unversioned( namespace ):
                            self.generate_object( child, namespace, self.json_out[self.namespace_under_process]["definitions"] )

                    # Process Action definitions
                    if child.tag == ODATA_TAG_ACTION:
                        self.generate_action( child, self.json_out[self.namespace_under_process]["definitions"] )

                    # Process EnumType definitions if defined in versioned namespaces
                    if child.tag == ODATA_TAG_ENUM:
                        if not is_namespace_unversioned( namespace ):
                            self.generate_enum( child, self.json_out[self.namespace_under_process]["definitions"] )

                    # Process TypeDefinition definitions if the defined in versioned namespaces
                    if child.tag == ODATA_TAG_TYPE_DEF:
                        if not is_namespace_unversioned( namespace ):
                            self.generate_typedef( child, self.json_out[self.namespace_under_process]["definitions"] )

                    # Process top level annotations
                    if child.tag == ODATA_TAG_ANNOTATION:
                        term = self.get_attrib( child, "Term" )

                        # Owning Entity
                        if term == "Redfish.OwningEntity":
                            self.json_out[self.namespace_under_process]["owningEntity"] = self.get_attrib( child, "String" )

                        # Release
                        if term == "Redfish.Release":
                            # Only add if the major and minor versions are the same
                            if not is_namespace_unversioned( namespace ):
                                version1 = get_version_details( namespace )
                                version2 = get_version_details( self.namespace_under_process )
                                if version1[0] == version2[0] and version1[1] == version2[1]:
                                    self.json_out[self.namespace_under_process]["release"] = self.get_attrib( child, "String" )

                        # Language
                        if term == "Redfish.Language":
                            self.json_out[self.namespace_under_process]["language"] = self.get_attrib( child, "String" )

    def process_excerpts( self ):
        """
        Adds the excerpt definitions to the JSON output
        """

        base_name = self.namespace_under_process.split( "." )[0]
        if base_name not in self.json_out[self.namespace_under_process]["definitions"]:
            # Nothing to process; this file likely does not contain a resource definition
            return
        base_def = self.json_out[self.namespace_under_process]["definitions"][base_name]
        excerpt_list = [ base_name ]

        # Check to see if we need to make an excerpt definition
        count = 0
        for prop_name, prop in base_def["properties"].items():
            if "excerpt" in prop:
                count = count + 1
                for e in prop["excerpt"].split( "," ):
                    if e not in excerpt_list:
                         excerpt_list.append(e)
            if "excerptCopyOnly" in prop:
                count = count + 1
        if count == 1:
            # Exactly 1 excerpt; this happens if only the Name property is an excerpt
            # Do not make an excerpt definition for this
            base_def["properties"]["Name"].pop( "excerpt" )
            return
        elif count < 1:
            # No excerpts at all
            return

        # Create an excerpt definition for each type of excerpt found
        for excerpt in excerpt_list:
            excerpt_name = excerpt + "Excerpt"
            self.json_out[self.namespace_under_process]["definitions"][excerpt_name] = copy.deepcopy( base_def )
            excerpt_def = self.json_out[self.namespace_under_process]["definitions"][excerpt_name]
            excerpt_def["excerpt"] = excerpt

            # Strip out properties that do not apply
            remove_list = []
            for prop_name, prop in excerpt_def["properties"].items():
                if "excerpt" in prop:
                    if ( excerpt not in prop["excerpt"].split( "," ) ) and ( prop["excerpt"] != base_name ):
                        remove_list.append( prop_name )
                elif "excerptCopyOnly" not in prop:
                    remove_list.append( prop_name )
            for prop_name in remove_list:
                excerpt_def["properties"].pop( prop_name )
                if "required" in excerpt_def:
                    if prop_name in excerpt_def["required"]:
                        excerpt_def["required"].remove( prop_name )
                if "requiredOnCreate" in excerpt_def:
                    if prop_name in excerpt_def["requiredOnCreate"]:
                        excerpt_def["requiredOnCreate"].remove( prop_name )

            # Strip out the required and requiredOnCreate terms if needed
            if "required" in excerpt_def:
                if len( excerpt_def["required"] ) == 0:
                    excerpt_def.pop( "required" )
            if "requiredOnCreate" in excerpt_def:
                if len( excerpt_def["requiredOnCreate"] ) == 0:
                    excerpt_def.pop( "requiredOnCreate" )

            # Add the definition to the unversioned namespace if it's the latest errata
            if self.is_latest_errata( self.namespace_under_process ):
                if excerpt_name not in self.json_out[base_name]["definitions"]:
                    self.json_out[base_name]["definitions"][excerpt_name] = { "anyOf": [] }
                self.json_out[base_name]["definitions"][excerpt_name]["anyOf"].append( { "$ref": self.location + self.namespace_under_process + ".json#/definitions/" + excerpt_name } )

        # Remove any excerpt copy only properties from the base definition
        remove_list = []
        for prop_name, prop in base_def["properties"].items():
            if "excerptCopyOnly" in prop:
                remove_list.append( prop_name )
        for prop_name in remove_list:
            base_def["properties"].pop( prop_name )

    def generate_capabilities( self, object, json_def ):
        """
        Processes the capabilities of an object definition

        Args:
            object: The EntityType or ComplexType to process
            json_def: The JSON Definitions body to populate
        """

        name = self.get_attrib( object, "Name" )

        # Add the capabilities
        for child in object:
            if child.tag == ODATA_TAG_ANNOTATION:
                term = self.get_attrib( child, "Term" )

                # Capabilities
                if term.startswith( "Capabilities." ):
                    for record in child.iter( ODATA_TAG_RECORD ):
                        for prop_val in record.iter( ODATA_TAG_PROP_VAL ):
                            property = self.get_attrib( prop_val, "Property" )
                            value = self.get_attrib( prop_val, "Bool" )

                            # Convert the value from a string
                            if value == "true":
                                value = True
                            else:
                                value = False

                            # Assign the value based on the type of term being processed
                            if property == "Insertable":
                                json_def[name]["insertable"] = value
                            elif property == "Updatable":
                                json_def[name]["updatable"] = value
                            elif property == "Deletable":
                                json_def[name]["deletable"] = value

                # URIs
                if term == "Redfish.Uris":
                    for collection in child.iter( ODATA_TAG_COLLECTION ):
                        for string in collection.iter( ODATA_TAG_STRING ):
                            if "uris" not in json_def[name]:
                                json_def[name]["uris"] = []
                            json_def[name]["uris"].append( string.text )

                # Deprecated URIs
                if term == "Redfish.DeprecatedUris":
                    for collection in child.iter( ODATA_TAG_COLLECTION ):
                        for string in collection.iter( ODATA_TAG_STRING ):
                            if "urisDeprecated" not in json_def[name]:
                                json_def[name]["urisDeprecated"] = []
                            json_def[name]["urisDeprecated"].append( string.text )

    def generate_abstract_object( self, object, json_def ):
        """
        Processes an abstract EntityType or ComplexType to generate the JSON definition structure

        Args:
            object: The abstract EntityType or ComplexType to process
            json_def: The JSON Definitions body to populate
        """

        name = self.get_attrib( object, "Name" )

        # Some entities in the Resource namespace need to be processed in a special manner since they don't follow the Redfish model for object inheritance
        if ( self.namespace_under_process == "Resource" ) and ( object.tag == ODATA_TAG_ENTITY ) and ( name == "Item" or name == "ItemOrCollection" ):
            json_def[name] = { "anyOf": [ { "$ref": self.odata_schema + "#/definitions/idRef" } ] }

            # Append matching objects in the file to the anyOf list
            for schema in self.root.iter( ODATA_TAG_SCHEMA ):
                namespace = self.get_attrib( schema, "Namespace" )
                for child in schema:
                    if child.tag == object.tag:
                        if self.get_attrib( child, "BaseType", False ) == self.namespace_under_process + "." + name:
                            json_def[name]["anyOf"].append( { "$ref": "#/definitions/" + self.get_attrib( child, "Name" ) } )
        else:
            if object.tag == ODATA_TAG_ENTITY:
                json_def[name] = { "anyOf": [ { "$ref": self.odata_schema + "#/definitions/idRef" } ] }
            else:
                json_def[name] = { "anyOf": [] }

            # Find the oldest definition of the object
            oldest_version = None
            for schema in self.root.iter( ODATA_TAG_SCHEMA ):
                namespace = self.get_attrib( schema, "Namespace" )
                if namespace != self.namespace_under_process:
                    for child in schema:
                        if child.tag == object.tag:
                            if self.get_attrib( child, "Name" ) == name:
                                if oldest_version is None:
                                    oldest_version = namespace
                                else:
                                    if not does_version_apply( oldest_version, namespace ):
                                        oldest_version = namespace

            # Based on the oldest version, add the mapping for all namespaces
            if oldest_version is not None:
                for schema in self.root.iter( ODATA_TAG_SCHEMA ):
                    namespace = self.get_attrib( schema, "Namespace" )
                    if namespace != self.namespace_under_process:
                        if does_version_apply( oldest_version, namespace ) and self.is_latest_errata( namespace ):
                            json_def[name]["anyOf"].append( { "$ref": self.location + namespace + ".json#/definitions/" + name } )
            elif object.tag == ODATA_TAG_ACTION:
                # Actions only appear in the unversioned namespace; need to make assumptions based on the version tag
                for schema in self.root.iter( ODATA_TAG_SCHEMA ):
                    namespace = self.get_attrib( schema, "Namespace" )
                    if namespace != self.namespace_under_process:
                        if self.does_definition_apply( object, self.namespace_under_process ) and self.is_latest_errata( namespace ):
                            json_def[name]["anyOf"].append( { "$ref": self.location + namespace + ".json#/definitions/" + name } )

        # Add descriptions
        for child in object:
            if child.tag == ODATA_TAG_ANNOTATION:
                term = self.get_attrib( child, "Term" )

                # Object Description
                if term == "OData.Description":
                    json_def[name]["description"] = self.get_attrib( child, "String" )

                # Object Long Description
                if term == "OData.LongDescription":
                    json_def[name]["longDescription"] = self.get_attrib( child, "String" )

                # Object Translation
                if term == "Redfish.Translation":
                    json_def[name]["translation"] = self.get_attrib( child, "String" )

    def generate_object( self, object, namespace, json_def, name = None ):
        """
        Processes an EntityType or ComplexType to generate the JSON definition structure

        Args:
            object: The EntityType or ComplexType to process
            namespace: The namespace string where the object was found
            json_def: The JSON Definitions body to populate
            name: The name of the object to populate
        """

        # If the name isn't given, pull it from the object
        if name is None:
            name = self.get_attrib( object, "Name" )

        # Add the object to the definitions body if this is a new instance
        self.init_object_definition( name, json_def )

        # If this object is an Action, add the predefined title and target properties, as well as the parameters block
        if object.tag == ODATA_TAG_ACTION:
            json_def[name]["properties"]["title"] = { "type": "string", "description": "Friendly action name" }
            json_def[name]["properties"]["target"] = { "type": "string", "format": "uri-reference", "description": "Link to invoke action" }
            json_def[name]["parameters"] = {}

        # Process the items in the object
        first_parameter = True
        for child in object:
            # Process object level annotations
            if child.tag == ODATA_TAG_ANNOTATION:
                term = self.get_attrib( child, "Term" )

                # Object Description
                if ( term == "OData.Description" ) and ( "description" not in json_def[name] ):
                    json_def[name]["description"] = self.get_attrib( child, "String" )

                # Object Long Description
                if ( term == "OData.LongDescription" ) and ( "longDescription" not in json_def[name] ):
                    json_def[name]["longDescription"] = self.get_attrib( child, "String" )

                # Object Translation
                if ( term == "Redfish.Translation" ) and ( "translation" not in json_def[name] ):
                    json_def[name]["translation"] = self.get_attrib( child, "String" )

                # Additional Properties
                if term == "OData.AdditionalProperties":
                    if self.get_attrib( child, "Bool", False, "true" ) == "true":
                        json_def[name]["additionalProperties"] = True

                # Dynamic Property Patterns
                if term == "Redfish.DynamicPropertyPatterns":
                    # Need to update the pattern properties object based on the records found here
                    for record in child.iter( ODATA_TAG_RECORD ):
                        # Pull out the Pattern and Type of the dynamic property pattern
                        pattern_prop = None
                        type = None
                        is_nullable = False
                        for prop_val in record.iter( ODATA_TAG_PROP_VAL ):
                            property = self.get_attrib( prop_val, "Property" )
                            if property == "Pattern":
                                pattern_prop = self.get_attrib( prop_val, "String" )
                            if property == "Type":
                                type = self.get_attrib( prop_val, "String" )
                                if ( type == "Edm.PrimitiveType" ) or ( type == "Edm.Primitive" ):
                                    is_nullable = True

                        # If it's properly defined, add it to the pattern properties for the object
                        if ( pattern_prop is not None ) and ( type is not None ):
                            json_def[name]["patternProperties"][pattern_prop] = {}
                            json_type, ref, pattern, format = self.csdl_type_to_json_type( type, is_nullable )
                            if ref is None:
                                json_def[name]["patternProperties"][pattern_prop]["type"] = json_type
                            else:
                                json_def[name]["patternProperties"][pattern_prop]["$ref"] = ref

            # Process properties and navigation properties
            if ( child.tag == ODATA_TAG_PROPERTY ) or ( child.tag == ODATA_TAG_NAV_PROPERTY ):
                self.generate_property( child, json_def[name], namespace )

            # Process action parameters
            if child.tag == ODATA_TAG_PARAMETER:
                # Filter out the first parameter; this is the binding parameter, which does not get translated to JSON
                if first_parameter:
                    first_parameter = False
                else:
                    self.generate_parameter( child, namespace, json_def[name] )

            # Process action return payloads
            if child.tag == ODATA_TAG_RETURN:
                self.generate_action_response( child, json_def[name] )

        # Add OData specific properties
        self.generate_odata_properties( object, json_def[name] )

        # Add items from the BaseType
        self.generate_object_base( object, name, json_def )

        # Add version info
        self.add_version_details( object, json_def[name] )

    def generate_object_base( self, object, name, json_def ):
        """
        Processes the BaseType for an EntityType or ComplexType and adds it to the JSON output

        Args:
            object: The EntityType or ComplexType to process
            json_def: The JSON Definitions body to populate
            name: The name of the object to continue extending
        """

        # Check if there is a BaseType
        base_type = self.get_attrib( object, "BaseType", False )
        if base_type == DEFAULT_ATTRIB:
            return

        # Check if definitions from Resource need to be mapped
        if base_type == "Resource.v1_0_0.Resource":
            for prop in self.resource_props:
                self.generate_property( prop, json_def[name] )
            return
        elif base_type == "LineOfService.v1_0_0.LineOfService":
            for prop in self.resource_props:
                self.generate_property( prop, json_def[name] )
            return
        elif base_type == "Resource.v1_0_0.ResourceCollection":
            for prop in self.resource_collection_props:
                self.generate_property( prop, json_def[name] )

            # Resource Collections need an additional anyOf layer
            def_copy = json_def[name]
            json_def[name] = { "anyOf": [ { "$ref": self.odata_schema + "#/definitions/idRef" } ] }
            json_def[name]["anyOf"].append( def_copy )
            return
        elif base_type == "Resource.v1_0_0.ReferenceableMember":
            for prop in self.ref_member_props:
                self.generate_property( prop, json_def[name] )
            return
        elif base_type == "Resource.Links":
            for prop in self.links_props:
                self.generate_property( prop, json_def[name] )
            return

        # Loop on the namespaces to find the matching type
        for schema in self.root.iter( ODATA_TAG_SCHEMA ):
            for base_object in schema.iter( object.tag ):
                namespace = self.get_attrib( schema, "Namespace" )
                type_name = namespace + "." + self.get_attrib( base_object, "Name" )
                if type_name == base_type:
                    # Match; process it
                    self.generate_object( base_object, namespace, json_def, name )
                    return

    def generate_action( self, action, json_def ):
        """
        Processes an Action and adds it to the JSON output

        Args:
            action: The Action to process
            json_def: The JSON Definitions body to populate
        """

        # Check if this action applies to the namespace under process
        if not self.does_definition_apply( action, self.namespace_under_process ):
            return

        # Add the object for the Action itself
        self.generate_object( action, self.namespace_under_process, json_def )

        # Hook it into the Actions object definition to be one of its properties
        name = self.get_attrib( action, "Name" )
        if not self.is_oem_action( action ):
            self.init_object_definition( "Actions", json_def )
            action_prop = "#" + self.namespace_under_process.split( "." )[0] + "." + name
            json_def["Actions"]["properties"][action_prop] = { "$ref": "#/definitions/" + name }

        # Add version details to the Action
        self.add_version_details( action, json_def[name] )

    def generate_enum( self, enum, json_def ):
        """
        Processes an EnumType and adds it to the JSON output

        Args:
            enum: The EnumType to process
            json_def: The JSON Definitions body to populate
        """

        # Add the enum to the definitions body if this is a new instance
        # Unlike with objects, we don't check if the enum is already defined; this
        # is because in CSDL, you can't extend enums like you can with objects
        name = self.get_attrib( enum, "Name" )
        json_def[name] = {}
        json_def[name]["type"] = "string"
        self.add_version_details( enum, json_def[name] )

        # Process the items in the enum
        for child in enum:
            # Top level annotations
            if child.tag == ODATA_TAG_ANNOTATION:
                term = self.get_attrib( child, "Term" )

                # Enum Description
                if term == "OData.Description":
                    json_def[name]["description"] = self.get_attrib( child, "String" )
                # Enum Long Description
                if term == "OData.LongDescription":
                    json_def[name]["longDescription"] = self.get_attrib( child, "String" )
                # Enum Translation
                if term == "Redfish.Translation":
                    json_def[name]["translation"] = self.get_attrib( child, "String" )
                # Enum Deprecated
                if term == "Redfish.Deprecated":
                    json_def[name]["deprecated"] = self.get_attrib( child, "String" )

            # Enum members
            if child.tag == ODATA_TAG_MEMBER:
                # Check if the member should be skipped
                if not self.does_definition_apply( child, self.namespace_under_process ) and not is_namespace_unversioned( self.namespace_under_process ):
                    continue

                # Add to the enum list
                member_name = self.get_attrib( child, "Name" )
                if "enum" not in json_def[name]:
                    json_def[name]["enum"] = []
                json_def[name]["enum"].append( member_name )

                # Process the annotations of the current member
                for annotation in child.iter( ODATA_TAG_ANNOTATION ):
                    term = self.get_attrib( annotation, "Term" )

                    # Member Description
                    if term == "OData.Description":
                        if "enumDescriptions" not in json_def[name]:
                            json_def[name]["enumDescriptions"] = {}
                        json_def[name]["enumDescriptions"][member_name] = self.get_attrib( annotation, "String" )

                    # Member Long Description
                    if term == "OData.LongDescription":
                        if "enumLongDescriptions" not in json_def[name]:
                            json_def[name]["enumLongDescriptions"] = {}
                        json_def[name]["enumLongDescriptions"][member_name] = self.get_attrib( annotation, "String" )

                    # Member Translation
                    if term == "Redfish.Translation":
                        if "enumTranslations" not in json_def[name]:
                            json_def[name]["enumTranslations"] = {}
                        json_def[name]["enumTranslations"][member_name] = self.get_attrib( annotation, "String" )

                    # Member Deprecated
                    if term == "Redfish.Deprecated":
                        if "enumDeprecated" not in json_def[name]:
                            json_def[name]["enumDeprecated"] = {}
                        json_def[name]["enumDeprecated"][member_name] = self.get_attrib( annotation, "String" )

                # Add version details for the member
                self.add_version_details( child, json_def[name], member_name )

    def generate_typedef( self, typedef, json_def ):
        """
        Processes a TypeDefinition and adds it to the JSON output

        Args:
            typedef: The TypeDefinition to process
            json_def: The JSON Definitions body to populate
        """

        # Check if this is a Redfish Enum
        for child in typedef:
            if child.tag == ODATA_TAG_ANNOTATION:
                if self.get_attrib( child, "Term" ) == "Redfish.Enumeration":
                    # Special handling for Redfish Enums
                    self.generate_redfish_enum( typedef, json_def )
                    return

        # It's not a Redfish Enum; no special handling needed
        name = self.get_attrib( typedef, "Name" )
        type = self.get_attrib( typedef, "UnderlyingType" )
        json_def[name] = {}

        # Add the common type info
        self.add_type_info( typedef, type, False, json_def[name] )

    def generate_redfish_enum( self, enum, json_def ):
        """
        Processes a TypeDefinition that contains a Redfish Enum definition

        Args:
            enum: The Redfish Enum to process
            json_def: The JSON Definitions body to populate
        """

        # Add the enum to the definitions body if this is a new instance
        # Unlike with objects, we don't check if the enum is already defined; this
        # is because in CSDL, you can't extend enums like you can with objects
        name = self.get_attrib( enum, "Name" )
        json_def[name] = {}
        json_def[name]["type"] = "string"

        # Process the items in the enum
        for child in enum:
            # Only annotations should be at the top level of the definition
            if child.tag == ODATA_TAG_ANNOTATION:
                term = self.get_attrib( child, "Term" )

                # Enum Description
                if term == "OData.Description":
                    json_def[name]["description"] = self.get_attrib( child, "String" )

                # Enum Long Description
                if term == "OData.LongDescription":
                    json_def[name]["longDescription"] = self.get_attrib( child, "String" )

                # Enum Translation
                if term == "Redfish.Translation":
                    json_def[name]["translation"] = self.get_attrib( child, "String" )

                # Enum Members
                if term == "Redfish.Enumeration":
                    # Step into the Redfish Enumeration annotation to pull out the members
                    for record in child.iter( ODATA_TAG_RECORD ):
                        # Get the member name first
                        member_name = None
                        for prop_val in record.iter( ODATA_TAG_PROP_VAL ):
                            if self.get_attrib( prop_val, "Property" ) == "Member":
                                member_name = self.get_attrib( prop_val, "String" )

                        # If we were successful in getting the member name, add it to the list and process its annotations
                        if member_name is not None:
                            # Check if the member should be skipped
                            if not self.does_definition_apply( record, self.namespace_under_process ):
                                continue

                            # Add the member to the list
                            if "enum" not in json_def[name]:
                                json_def[name]["enum"] = []
                            json_def[name]["enum"].append( member_name )

                            # Add the annotations for the member
                            for rec_annotation in record.iter( ODATA_TAG_ANNOTATION ):
                                rec_term = self.get_attrib( rec_annotation, "Term" )

                                # Member Description
                                if rec_term == "OData.Description":
                                    if "enumDescriptions" not in json_def[name]:
                                        json_def[name]["enumDescriptions"] = {}
                                    json_def[name]["enumDescriptions"][member_name] = self.get_attrib( rec_annotation, "String" )

                                # Member Long Description
                                if rec_term == "OData.LongDescription":
                                    if "enumLongDescriptions" not in json_def[name]:
                                        json_def[name]["enumLongDescriptions"] = {}
                                    json_def[name]["enumLongDescriptions"][member_name] = self.get_attrib( rec_annotation, "String" )

                                # Member Translation
                                if rec_term == "Redfish.Translation":
                                    if "enumTranslations" not in json_def[name]:
                                        json_def[name]["enumTranslations"] = {}
                                    json_def[name]["enumTranslations"][member_name] = self.get_attrib( rec_annotation, "String" )

                                # Member Deprecated
                                if rec_term == "Redfish.Deprecated":
                                    if "enumDeprecated" not in json_def[name]:
                                        json_def[name]["enumDeprecated"] = {}
                                    json_def[name]["enumDeprecated"][member_name] = self.get_attrib( rec_annotation, "String" )

                            # Add version details for the member
                            self.add_version_details( record, json_def[name], member_name )

    def init_object_definition( self, name, json_def ):
        """
        Initializes an object definition

        Args:
            name: The name of the object
            json_def: The JSON Definitions body to populate
        """

        # Only initialize if this is not already defined
        # This is to allow for the fact that a complete object definition is put into each JSON Schema file
        if name not in json_def:
            json_def[name] = {}
            json_def[name]["type"] = "object"
            json_def[name]["additionalProperties"] = False
            json_def[name]["patternProperties"] = {}
            json_def[name]["patternProperties"][PATTERN_PROP_REGEX] = {}
            json_def[name]["patternProperties"][PATTERN_PROP_REGEX]["type"] = [ "array", "boolean", "integer", "number", "null", "object", "string" ]
            json_def[name]["patternProperties"][PATTERN_PROP_REGEX]["description"] = "This property shall specify a valid odata or Redfish property."
            json_def[name]["properties"] = {}

    def generate_property( self, property, json_obj_def, namespace = "Resource" ):
        """
        Processes a Property or NavigationProperty and adds it to the JSON object definition

        Args:
            property: The Property or NavigationProperty to process
            json_obj_def: The JSON object definition to place the property
            namespace: The namespace where the property was found
        """

        # Pull out property info
        prop_name = self.get_attrib( property, "Name" )
        prop_type = self.get_attrib( property, "Type" )
        json_obj_def["properties"][prop_name] = {}

        # Properties don't use the Revision annotation for adding new properties; need to add it manually
        version = namespace.rsplit( "." )[-1]
        if is_namespace_unversioned( namespace ):
            version = DEFAULT_VER
        if version != DEFAULT_VER:
            json_obj_def["properties"][prop_name]["versionAdded"] = version

        # Determine if this is an array
        is_array = prop_type.startswith( "Collection(" )
        if is_array:
            prop_type = prop_type[11:-1]

        # Add the common type info
        self.add_type_info( property, prop_type, is_array, json_obj_def["properties"][prop_name] )

        # Check for required annotations on the property
        for annotation in property.iter( ODATA_TAG_ANNOTATION ):
            term = self.get_attrib( annotation, "Term" )

            if term == "Redfish.Required":
                if "required" not in json_obj_def:
                    json_obj_def["required"] = []
                if prop_name not in json_obj_def["required"]:
                    json_obj_def["required"].append( prop_name )
                    if prop_name == "Members":
                        json_obj_def["required"].append( "Members@odata.count" )
            if term == "Redfish.RequiredOnCreate":
                if "requiredOnCreate" not in json_obj_def:
                    json_obj_def["requiredOnCreate"] = []
                if prop_name not in json_obj_def["requiredOnCreate"]:
                    json_obj_def["requiredOnCreate"].append( prop_name )

        # If this is a collection of navigation properties, add the @odata.count property
        if ( property.tag == ODATA_TAG_NAV_PROPERTY ) and is_array:
            json_obj_def["properties"][prop_name + "@odata.count"] = { "$ref": self.odata_schema + "#/definitions/count" }

    def generate_parameter( self, parameter, namespace, json_obj_def ):
        """
        Processes a Parameter and adds it to the JSON object definition

        Args:
            parameter: The Parameter to process
            json_obj_def: The JSON object definition to place the property
            namespace: The namespace string where the parameter was found
        """

        # Check if this action applies to the namespace under process
        if not self.does_definition_apply( parameter, namespace ):
            return

        # Pull out parameter info
        param_name = self.get_attrib( parameter, "Name" )
        param_type = self.get_attrib( parameter, "Type" )
        json_obj_def["parameters"][param_name] = {}

        # Determine if this is an array
        is_array = param_type.startswith( "Collection(" )
        if is_array:
            param_type = param_type[11:-1]

        # Add the common type info
        self.add_type_info( parameter, param_type, is_array, json_obj_def["parameters"][param_name] )

    def generate_action_response( self, return_type, json_obj_def ):
        """
        Processes a ReturnType and adds it to the JSON object definition for an action response

        Args:
            return_type: The ReturnType to process
            json_obj_def: The JSON object definition to place the property
        """

        # Pull out the return type info
        response_type = self.get_attrib( return_type, "Type" )
        json_obj_def["actionResponse"] = {}

        # Determine if this is an array
        # Note: For how we model things today, this should never be the case; this should always map to a singular ComplexType
        is_array = response_type.startswith( "Collection(" )
        if is_array:
            response_type = response_type[11:-1]

        # Add the common type info
        self.add_type_info( return_type, response_type, is_array, json_obj_def["actionResponse"] )

    def generate_odata_properties( self, object, json_obj_def ):
        """
        Adds OData properties to an object definition if needed

        Args:
            object: The object definition
            json_obj_def: The JSON object definition to place the property
        """

        name = self.get_attrib( object, "Name" )
        base_type = self.get_attrib( object, "BaseType", False )

        # These objects are not actual resources; not all OData properties apply
        id_skip = False
        context_skip = False
        etag_skip = False
        if self.namespace_under_process.startswith( "Event." ):
            # Events are just asynchronous notifications; there's no way for a client to perform a GET or PATCH on an event
            id_skip = True
            etag_skip = True
        if ( self.namespace_under_process.startswith( "AttributeRegistry." ) or
             self.namespace_under_process.startswith( "MessageRegistry." ) or
             self.namespace_under_process.startswith( "PrivilegeRegistry." ) ):
            # Registries do not contain any properties beyond the type since they are simply copied from the author as is
            id_skip = True
            context_skip = True
            etag_skip = True

        # If the object is the Resource or ResourceCollection object, or is derived from them, then we add the OData properties
        if ( name == "Resource" or name == "ResourceCollection" or
             name == "LineOfService" or base_type == "LineOfService.v1_0_0.LineOfService" or
             base_type == "Resource.v1_0_0.Resource" or base_type == "Resource.v1_0_0.ResourceCollection" ):
            json_obj_def["properties"]["@odata.type"] = { "$ref": self.odata_schema + "#/definitions/type" }
            if not id_skip:
                json_obj_def["properties"]["@odata.id"] = { "$ref": self.odata_schema + "#/definitions/id" }
            if not context_skip:
                json_obj_def["properties"]["@odata.context"] = {"$ref": self.odata_schema + "#/definitions/context"}
            if not etag_skip:
                json_obj_def["properties"]["@odata.etag"] = { "$ref": self.odata_schema + "#/definitions/etag" }
            if "required" not in json_obj_def:
                json_obj_def["required"] = []
            if "@odata.id" not in json_obj_def["required"] and not id_skip:
                json_obj_def["required"].append( "@odata.id" )
            if "@odata.type" not in json_obj_def["required"]:
                json_obj_def["required"].append( "@odata.type" )

        # If the object is the ReferenceableMember, or is derived from it, then we add the OData properties
        if ( name == "ReferenceableMember" or base_type == "Resource.v1_0_0.ReferenceableMember" ) and not id_skip:
            json_obj_def["properties"]["@odata.id"] = { "$ref": self.odata_schema + "#/definitions/id" }
            if "required" not in json_obj_def:
                json_obj_def["required"] = []
            if "@odata.id" not in json_obj_def["required"]:
                json_obj_def["required"].append( "@odata.id" )

        # Add Members@odata.nextLink for objects that inherit from ResourceCollection
        if base_type == "Resource.v1_0_0.ResourceCollection":
            json_obj_def["properties"]["Members@odata.nextLink"] = { "$ref": self.odata_schema + "#/definitions/nextLink" }

    def add_type_info( self, type_info, type, is_array, json_type_def ):
        """
        Adds common type information for a given definition

        Args:
            type_info: The structure to process; can be Property, NavigationProperty, TypeDefinition, or Parameter
            type: The type for the structure
            is_array: Flag if this definition is an array of some sorts
            json_type_def: The JSON object or property definition to populate
        """

        # Determine if this is nullable
        if type_info.tag == ODATA_TAG_TYPE_DEF:
            is_nullable = False
        elif ( type_info.tag == ODATA_TAG_NAV_PROPERTY ) and is_array:
            is_nullable = False
        elif type_info.tag == ODATA_TAG_PARAMETER:
            is_nullable = False
            if self.get_attrib( type_info, "Nullable", False, "true" ) == "false":
                json_type_def["requiredParameter"] = True
        else:
            is_nullable = True
            if self.get_attrib( type_info, "Nullable", False, "true" ) == "false":
                is_nullable = False

        # Loop through the annotations and add other definitions as needed
        for annotation in type_info.iter( ODATA_TAG_ANNOTATION ):
            term = self.get_attrib( annotation, "Term" )

            # Description
            if term == "OData.Description":
                json_type_def["description"] = self.get_attrib( annotation, "String" )

            # Long Description
            if term == "OData.LongDescription":
                json_type_def["longDescription"] = self.get_attrib( annotation, "String" )

            # Translation
            if term == "Redfish.Translation":
                json_type_def["translation"] = self.get_attrib( annotation, "String" )

            # Permissions
            if term == "OData.Permissions":
                permissions = self.get_attrib( annotation, "EnumMember" )
                if ( permissions == "OData.Permission/Read" ) or ( permissions == "OData.Permissions/Read" ):
                    json_type_def["readonly"] = True
                elif ( permissions == "OData.Permission/Write" ) or ( permissions == "OData.Permissions/Write" ):
                    json_type_def["writeOnly"] = True
                    json_type_def["readonly"] = False
                elif ( permissions == "OData.Permission/None" ) or ( permissions == "OData.Permissions/None" ):
                    json_type_def["writeOnly"] = False
                    json_type_def["readonly"] = True
                else:
                    json_type_def["readonly"] = False

            # Format
            if term == "OData.IsURL":
                if self.get_attrib( annotation, "Bool", False, "true" ) == "true":
                    json_type_def["format"] = "uri-reference"

            # Units
            if term == "Measures.Unit":
                json_type_def["units"] = self.get_attrib( annotation, "String" )

            # Minimum
            if term == "Validation.Minimum":
                json_type_def["minimum"] = int( self.get_attrib( annotation, "Int" ) )

            # Maximum
            if term == "Validation.Maximum":
                json_type_def["maximum"] = int( self.get_attrib( annotation, "Int" ) )

            # Pattern
            if term == "Validation.Pattern":
                json_type_def["pattern"] = self.get_attrib( annotation, "String" )

            # Deprecated
            if term == "Redfish.Deprecated":
                json_type_def["deprecated"] = self.get_attrib( annotation, "String" )

            # Auto Expand
            if term == "OData.AutoExpand":
                json_type_def["autoExpand"] = True

            # URI Segment
            if term == "Redfish.URISegment":
                json_type_def["uriSegment"] = self.get_attrib( annotation, "String" )

            # Filter
            if term == "Redfish.Filter":
                json_type_def["filter"] = self.get_attrib( annotation, "String" )

            # Excerpt Copy Only
            if term == "Redfish.ExcerptCopyOnly":
                json_type_def["excerptCopyOnly"] = True

            # Excerpt
            if term == "Redfish.Excerpt":
                excerpt_namespace = self.namespace_under_process.split( "." )[0]
                json_type_def["excerpt"] = excerpt_namespace + self.get_attrib( annotation, "String", False, "" ).replace( ",", "," + excerpt_namespace )

            # Excerpt Copy
            if term == "Redfish.ExcerptCopy":
                json_type_def["excerptCopy"] = type.split( "." )[0] + self.get_attrib( annotation, "String", False, "" ) + "Excerpt"

        # Convert the type as needed; some types will force a format, pattern, or reference
        json_type, ref, pattern, format = self.csdl_type_to_json_type( type, is_nullable )
        if pattern is not None:
            json_type_def["pattern"] = pattern
        if format is not None:
            json_type_def["format"] = format
        if ( ref is not None ) and ( "excerptCopy" in json_type_def ):
            # Update the reference to point to the excerpt copy
            ref = ref.rsplit( "/", 1 )[0] + "/" + json_type_def["excerptCopy"]

        # Set up the type and reference accordingly
        if is_array:
            json_type_def["type"] = "array"
            if ref is None:
                json_type_def["items"] = { "type": json_type }
            elif ( not is_nullable ) and ( ref is not None ):
                json_type_def["items"] = { "$ref": ref }
            else:
                json_type_def["items"] = { "anyOf": [ { "$ref": ref }, { "type": "null" } ] }
        else:
            if ref is None:
                json_type_def["type"] = json_type
            elif ( not is_nullable ) and ( ref is not None ):
                json_type_def["$ref"] = ref
            else:
                json_type_def["anyOf"] = [ { "$ref": ref }, { "type": "null" } ]

        # Add version info
        self.add_version_details( type_info, json_type_def )

    def csdl_type_to_json_type( self, type, is_nullable ):
        """
        Converts the CSDL type to a JSON type

        Args:
            type: The CSDL type
            is_nullable: Flag if this type is allowed to be null

        Returns:
            A single or set of basic JSON types this is allowed to be
            A reference to another definition if this can map elsewhere
            The pattern allowed by the type
            The format allowed by the type
        """

        # Initialize locals
        json_type = None
        ref = None
        pattern = None
        format = None

        # Perform the mapping based off the type
        if ( ( type == "Edm.SByte" ) or ( type == "Edm.Int16" ) or ( type == "Edm.Int32" ) or
             ( type == "Edm.Int64" ) ):
            if is_nullable:
                json_type = [ "integer", "null" ]
            else:
                json_type = "integer"
        elif type == "Edm.Decimal":
            if is_nullable:
                json_type = [ "number", "null" ]
            else:
                json_type = "number"
        elif type == "Edm.String":
            if is_nullable:
                json_type = [ "string", "null" ]
            else:
                json_type = "string"
        elif type == "Edm.DateTimeOffset":
            if is_nullable:
                json_type = [ "string", "null" ]
            else:
                json_type = "string"
            format = "date-time"
        elif type == "Edm.Duration":
            if is_nullable:
                json_type = [ "string", "null" ]
            else:
                json_type = "string"
            pattern = "^P(\d+D)?(T(\d+H)?(\d+M)?(\d+(.\d+)?S)?)?$"
        elif type == "Edm.TimeOfDay":
            if is_nullable:
                json_type = [ "string", "null" ]
            else:
                json_type = "string"
            pattern = "^([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])(.[0-9]{1,12})?$"
        elif type == "Edm.Guid":
            if is_nullable:
                json_type = [ "string", "null" ]
            else:
                json_type = "string"
            pattern = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        elif type == "Edm.Boolean":
            if is_nullable:
                json_type = [ "boolean", "null" ]
            else:
                json_type = "boolean"
        elif ( type == "Edm.PrimitiveType" ) or ( type == "Edm.Primitive" ):
            if is_nullable:
                json_type = [ "string", "boolean", "number", "null" ]
            else:
                json_type = [ "string", "boolean", "number" ]
        else:
            # Does not match the base CSDL types; need to map it via a reference

            if ( type == "Resource.Item" ) or ( type == "Resource.ItemOrCollection" ):
                # General reference; use the generic idRef term
                ref = self.odata_schema + "#/definitions/idRef"
            else:
                # Make a reference that maps to a specific JSON file
                namespace_ref = type.rsplit( ".", 1 )[0]
                type_ref = type.split( "." )[-1]
                if namespace_ref == "Resource" and self.namespace_under_process == "Resource":
                    # No crossing; local reference; needed since Resource is handled in a special manner for common definitions elsewhere
                    ref = "#/definitions/" + type_ref
                elif namespace_ref in self.external_references:
                    ref = self.external_references[namespace_ref] + "#/definitions/" + type_ref
                elif namespace_ref in self.internal_references:
                    # Check if this is a cross reference between versioned and unversioned namespaces
                    if is_namespace_unversioned( namespace_ref ) != is_namespace_unversioned( self.namespace_under_process ):
                        # It crosses; they'll be in different files
                        ref = self.location + namespace_ref + ".json#/definitions/" + type_ref
                    else:
                        # No crossing; local reference
                        ref = "#/definitions/" + type_ref
                else:
                    print( "-- ERROR: Could not resolve reference to \"{}\" for \"{}\"".format( namespace_ref, type ) )
                    self.errors[self.namespace_under_process] = True

        return json_type, ref, pattern, format

    def get_attrib( self, element, name, required = True, default = DEFAULT_ATTRIB ):
        """
        Gets a given attribute from an ET element in a safe manner, and provides warnings

        Args:
            element: The element with the attribute
            name: The name of the attribute
            required: Flag indicating if the attribute is expected to be present
            default: The value to return if not found

        Returns:
            The attribute value
        """
        if name in element.attrib:
            return element.attrib[name]
        else:
            if required:
                print( "-- ERROR: Missing \"{}\" attribute for tag \"{}\"".format( name, element.tag.split( "}" )[-1] ) )
                self.errors[self.namespace_under_process] = True

        return default

    def get_version_details( self, object ):
        """
        Gets the version info for a given object

        Args:
            object: The object to parse

        Returns:
            The version added string
            The version deprecated string
            The deprecated info string
        """
        version_added = None
        version_deprecated = None
        deprecated_info = None

        # Go through each annotation and find the Redfish.Revisions term
        for child in object:
            if child.tag == ODATA_TAG_ANNOTATION:
                term = self.get_attrib( child, "Term" )
                if term == "Redfish.Revisions":
                    for collection in child.iter( ODATA_TAG_COLLECTION ):
                        for record in collection.iter( ODATA_TAG_RECORD ):
                            revision_kind = None
                            revision_description = None
                            revision_string = None
                            for prop_val in record.iter( ODATA_TAG_PROP_VAL ):
                                property = self.get_attrib( prop_val, "Property" )
                                if property == "Kind":
                                    revision_kind = self.get_attrib( prop_val, "EnumMember" )
                                elif property == "Version":
                                    revision_string = self.get_attrib( prop_val, "String" )
                                elif property == "Description":
                                    revision_description = self.get_attrib( prop_val, "String" )
                            if revision_kind is None:
                                print( "-- ERROR: Missing \"Kind\" attribute for revision info for \"{}\"".format( self.get_attrib( object, "Name" ) ) )
                                self.errors[self.namespace_under_process] = True
                            elif revision_kind == "Redfish.RevisionKind/Added":
                                if revision_string is None:
                                    print( "-- ERROR: Missing \"Version\" attribute for revision info for \"{}\"".format( self.get_attrib( object, "Name" ) ) )
                                    self.errors[self.namespace_under_process] = True
                                else:
                                    version_added = revision_string
                            elif revision_kind == "Redfish.RevisionKind/Deprecated":
                                if revision_string is None or revision_description is None:
                                    print( "-- ERROR: Missing \"Version\" or \"Description\" attribute for revision info for \"{}\"".format( self.get_attrib( object, "Name" ) ) )
                                    self.errors[self.namespace_under_process] = True
                                else:
                                    version_deprecated = revision_string
                                    deprecated_info = revision_description
                            else:
                                print( "-- ERROR: Unknown \"Kind\" attribute for revision info for \"{}\"".format( self.get_attrib( object, "Name" ) ) )
                                self.errors[self.namespace_under_process] = True

        return version_added, version_deprecated, deprecated_info

    def does_definition_apply( self, definition, namespace ):
        """
        Determines if a given definition applies to a namespace being processed

        Args:
            definition: The definition to check
            namespace: The namespace in question

        Returns:
            True if the definition applies, false otherwise
        """
        version = namespace.rsplit( "." )[-1]
        if is_namespace_unversioned( namespace ):
            version = DEFAULT_VER
        added, deprecated, deprecated_info = self.get_version_details( definition )
        if added is None:
            return True
        return does_version_apply( added, version )

    def add_version_details( self, definition, json_def, enum_member = None ):
        """
        Adds version details to a given definition

        Args:
            definition: The definition to check
            json_def: The JSON term to populate
            enum_member: The name of the enum member with the version info
        """
        version = self.namespace_under_process.rsplit( "." )[-1]
        if is_namespace_unversioned( self.namespace_under_process ):
            version = DEFAULT_VER
        added, deprecated, deprecated_info = self.get_version_details( definition )
        if deprecated is not None and deprecated_info is not None:
            if does_version_apply( deprecated, version ) or is_namespace_unversioned( self.namespace_under_process ):
                if enum_member is not None:
                    if "enumVersionDeprecated" not in json_def:
                        json_def["enumVersionDeprecated"] = {}
                    if "enumDeprecated" not in json_def:
                        json_def["enumDeprecated"] = {}
                    json_def["enumVersionDeprecated"][enum_member] = deprecated
                    json_def["enumDeprecated"][enum_member] = deprecated_info
                else:
                    json_def["versionDeprecated"] = deprecated
                    json_def["deprecated"] = deprecated_info
        if added is not None:
            if enum_member is not None:
                if "enumVersionAdded" not in json_def:
                    json_def["enumVersionAdded"] = {}
                json_def["enumVersionAdded"][enum_member] = added
            else:
                json_def["versionAdded"] = added

    def is_latest_errata( self, namespace ):
        """
        Determines if the referenced namespace is the latest errata

        Args:
            namespace: The namespace to check

        Returns:
            True if the latest; False otherwise
        """

        # Go through each namespace in the schema to compare the versions
        is_latest = True
        for schema in self.root.iter( ODATA_TAG_SCHEMA ):
            schema_namespace = self.get_attrib( schema, "Namespace" )
            if not is_namespace_unversioned( schema_namespace ):
                version1 = get_version_details( namespace )
                version2 = get_version_details( schema_namespace )
                # If the major and minor versions are the same, and the schema version is higher, then this is not the latest
                if ( version1[0] == version2[0] ) and ( version1[1] == version2[1] ) and ( version1[2] < version2[2] ):
                    is_latest = False
        return is_latest

    def is_oem_action( self, action ):
        """
        Checks if an action is an OEM action

        Args:
            action: The action structure

        Returns:
            True if the action is an OEM action, False otherwise
        """

        # If the binding parameter points to an OemActions object, this is an OEM action
        for param in action:
            if param.tag == ODATA_TAG_PARAMETER:
                if self.get_attrib( param, "Type", True ).endswith( ".OemActions" ):
                    return True
        return False

def main():
    """
    Main entry point for the script
    """

    # Get the input arguments
    arg_get = argparse.ArgumentParser( description = "A tool used to convert Redfish CSDL files to Redfish JSON Schema files" )
    arg_get.add_argument( "--input", "-I", type = str, required = True, help = "The folder containing the CSDL files to convert" )
    arg_get.add_argument( "--output", "-O",  type = str, required = True, help = "The folder to write the converted JSON files" )
    arg_get.add_argument( "--config", "-C", type = str, help = "The configuration file containing definitions for various links and user strings" )
    arg_get.add_argument( "--overwrite", "-W", type = str, help = "Overwrite the versioned files in the output directory if they already exist (default is True)" )
    args = arg_get.parse_args()

    # Get the overwrite flag
    overwrite = True
    if args.overwrite is not None:
        if ( args.overwrite == "False" ) or ( args.overwrite == "false" ):
            overwrite = False

    # Create the output directory (if needed)
    if not os.path.exists( args.output ):
        os.makedirs( args.output )

    # Read the configuration file
    config_data = {}
    if args.config is not None:
        try:
            with open( args.config ) as config_file:
                config_data = json.load( config_file )
        except json.JSONDecodeError:
            print( "ERROR: {} contains a malformed JSON object".format( args.config ) )
            sys.exit( 1 )
        except:
            print( "ERROR: Could not open {}".format( args.config ) )
            sys.exit( 1 )

    # Set up defaults for missing configuration fields
    if "Copyright" not in config_data:
        config_data["Copyright"] = CONFIG_DEF_COPYRIGHT
    config_data["RedfishSchema"] = CONFIG_DEF_REDFISH_SCHEMA
    config_data["ODataSchema"] = CONFIG_DEF_ODATA_SCHEMA
    if "Location" not in config_data:
        config_data["Location"] = CONFIG_DEF_LOCATION
    config_data["ResourceLocation"] = CONFIG_DEF_RESOURCE_LOCATION
    if "DoNotWrite" not in config_data:
        config_data["DoNotWrite"] = []

    # Get the definition for Resource
    resource_file = args.input + os.path.sep + "Resource_v1.xml"
    resource_uri = config_data["ResourceLocation"] + "Resource_v1.xml"
    resource_root = None
    if os.path.isfile( resource_file ):
        # Local copy of Resource; use it
        try:
            resource_tree = ET.parse( resource_file )
            resource_root = resource_tree.getroot()
        except ET.ParseError:
            print( "ERROR: {} contains a malformed XML document".format( resource_file ) )
            sys.exit( 1 )
        except:
            print( "ERROR: Could not open {}".format( resource_file ) )
            sys.exit( 1 )
    else:
        # Fall back on using the remote copy of Resource
        retry_count = 0
        retry_count_max = 20
        while retry_count < retry_count_max:
            try:
                req = urllib.request.Request( resource_uri )
                response = urllib.request.urlopen( req )
                resource_data = response.read()
                resource_root = ET.fromstring( resource_data )
                break
            except OSError as e:
                if e.errno != errno.ECONNRESET:
                    print( "Could not open " + resource_uri )
                    print( e )
                    sys.exit( 1 )
                retry_count += 1
            if retry_count >= retry_count_max:
                print( "Could not open " + resource_uri )
                print( "Too many connection resets" )
                sys.exit( 1 )

    # Step through each file in the input directory
    for in_filename in os.listdir( args.input ):
        if in_filename.endswith( ".xml" ):
            print( "Generating JSON for: {}".format( in_filename ) )
            root = None
            try:
                tree = ET.parse( args.input + os.path.sep + in_filename )
                root = tree.getroot()
            except ET.ParseError:
                print( "ERROR: {} contains a malformed XML document".format( in_filename ) )
            except:
                print( "ERROR: Could not open {}".format( in_filename ) )
            if root is not None:
                # Translate and write the JSON files
                translator = CSDLToJSON( config_data["Copyright"], config_data["RedfishSchema"], config_data["ODataSchema"], config_data["Location"], config_data["ResourceLocation"], root, resource_root )
                translator.process()
                for namespace in translator.json_out:
                    out_filename = args.output + os.path.sep + namespace + ".json"
                    out_filename_short = namespace + ".json"
                    if translator.errors[namespace]:
                        print( "-- Errors detected while generating {}; not creating file".format( out_filename ) )
                    else:
                        if len( [ i for i in config_data["DoNotWrite"] if out_filename_short.startswith( i ) ] ) == 0:
                            if overwrite or is_namespace_unversioned( namespace ) or ( not os.path.isfile( out_filename ) ):
                                out_string = json.dumps( translator.json_out[namespace], sort_keys = True, indent = 4, separators = ( ",", ": " ) )
                                with open( out_filename, "w" ) as file:
                                    file.write( out_string )

def is_namespace_unversioned( namespace ):
    """
    Checks if a namespace is unversioned

    Args:
        namespace: The string name of the namespace

    Returns:
        True if the namespace is unversioned, False otherwise
    """

    # Versioned namespaces match the form NAME.vX_Y_Z
    if re.search( VERSION_REGEX, namespace ) is None:
        return True
    return False

def does_version_apply( version1, version2 ):
    """
    Checks if a version applies to another version

    Args:
        version1: The version in question, which may contain a namespace prepended
        version2: The version to compare against, which may contain a namespace prepended

    Returns:
        True if the version applies, False otherwise
    """

    # If the base name of the namespaces do not match, then it does not apply
    # Currently the only case this happens is in RedfishExtensions_v1.xml
    if "." in version1:
        if version1.split( "." )[0] != version2.split( "." )[0]:
            return False

    # Unversioned namespaces always apply
    if is_namespace_unversioned( version1 ):
        return True

    # Pull out the version numbers
    version1_array = get_version_details( version1 )
    version2_array = get_version_details( version2 )

    # Different major versions; not compatible
    if version1_array[0] != version2_array[0]:
        return False

    # The namespace has a newer minor version; skip
    if version1_array[1] > version2_array[1]:
        return False

    # The minor versions are equal, but the namespace has a newer errata version; skip
    if ( version1_array[1] == version2_array[1] ) and ( version1_array[2] > version2_array[2] ):
        return False

    return True

def get_version_details( version ):
    """
    Pulls the version numbers from a version string

    Args:
        version: The version string, which may contain a namespace prepended

    Returns:
        The major version
        The minor version
        The errata version
    """

    groups = re.search( VERSION_REGEX, version )
    return int( groups.group( 1 ) ), int( groups.group( 2 ) ), int( groups.group( 3 ) )

if __name__ == '__main__':
    sys.exit( main() )
