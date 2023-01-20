#! /usr/bin/python3
# Copyright Notice:
# Copyright 2018 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
JSON Schema to OpenAPI YAML

File : json-to-openapi.py

Brief : This file contains the definitions and functionalities for converting
        Redfish JSON Schema files to Redfish OpenAPI YAML files
"""

import argparse
import errno
import json
import os
import re
import sys
import urllib.request
import yaml

# List of terms that have a simple one to one conversion
ONE_FOR_ONE_REPLACEMENTS = [ "longDescription", "enumDescriptions", "enumLongDescriptions", "enumDeprecated", "enumVersionDeprecated", "enumVersionAdded",
                             "units", "requiredOnCreate", "owningEntity", "autoExpand", "release", "versionDeprecated", "versionAdded", "filter",
                             "excerpt", "excerptCopy", "excerptCopyOnly", "translation", "enumTranslations", "language" ]

# List of terms that are removed from the file
REMOVED_TERMS = [ "insertable", "updatable", "deletable", "uris", "parameters", "requiredParameter", "actionResponse" ]

# Responses allowed
HEAD_RESPONSES = [ 204 ]
GET_RESPONSES = [ 200 ]
PATCH_RESPONSES = [ 200, 202, 204 ]
PUT_RESPONSES = [ 200, 202, 204 ]
CREATE_RESPONSES = [ 201, 202, 204 ]
ACTION_RESPONSES = [ 200, 201, 202, 204 ]
DELETE_RESPONSES = [ 200, 202, 204 ]

# Default configurations
CONFIG_DEF_MESSAGE_REF = "http://redfish.dmtf.org/schemas/v1/Message.v1_1_0.yaml#/components/schemas/Message_v1_1_0_Message"
CONFIG_DEF_TASK_REF = "http://redfish.dmtf.org/schemas/v1/Task.v1_4_3.yaml#/components/schemas/Task_v1_4_3_Task"
CONFIG_DEF_ODATA_SCHEMA_LOC = "http://redfish.dmtf.org/schemas/v1/odata-v4.yaml"
CONFIG_DEF_OUT_FILE = "openapi.yaml"
CONFIG_DEF_EXTENSIONS = {}

class JSONToYAML:
    """
    Class for managing translation data and processing

    Args:
        input: The folder containing the input JSON files
        output: The folder to store the resulting YAML files
        overwrite: Whether or not to overwrite versioned files
        base_file: The filename of the base OpenAPI Service Document
        service_file: The filename for the OpenAPI Service Document
        odata_schema: The location for the Redfish OData Schema file
        message_ref: The location for the Message schema file
        task_ref: The location for the Task schema file
        info_block: The info block to put in the OpenAPI Service Document
        extensions: The URI extensions to apply to given resource types
        do_not_write: A list of files to not write
    """

    def __init__( self, input, output, overwrite, base_file, service_file, odata_schema, message_ref, task_ref, info_block, extensions, do_not_write ):
        self.odata_schema = odata_schema
        self.message_ref = message_ref
        self.task_ref = task_ref
        self.info_block = info_block
        self.uri_cache = {}
        self.action_cache = {}
        self.input_dir = input
        self.current_schema = None

        # Initialize the caches if extending an existing definition
        if base_file is not None:
            self.load_base_file( base_file, extensions )

        # Create the output directory (if needed)
        if not os.path.exists( output ):
            os.makedirs( output )

        # Step through each file in the input directory
        for filename in os.listdir( input ):
            if filename.endswith( ".json" ):
                print( "Generating YAML for: {}".format( filename ) )
                self.current_schema = filename.rsplit( ".", 1 )[0].replace( ".", "_" )
                json_data = None
                try:
                    with open( input + os.path.sep + filename ) as json_file:
                        json_data = json.load( json_file )
                except json.JSONDecodeError:
                    print( "ERROR: {} contains a malformed JSON object".format( filename ) )
                except:
                    print( "ERROR: Could not open {}".format( filename ) )

                # Translate the JSON document
                if json_data is not None:
                    # Cache URI and method information (if available)
                    self.check_for_uri_info( json_data, filename )
                    self.check_for_actions( json_data, filename )

                    # Remove top level $schema and $ref
                    json_data.pop( "$schema", None )
                    json_data.pop( "$ref", None )
                    json_data.pop( "$id", None )

                    # Replace top level copyright and definitions
                    if "copyright" in json_data:
                        json_data["x-copyright"] = json_data.pop( "copyright" )
                    if "definitions" in json_data:
                        json_data["components"] = { "schemas": json_data.pop( "definitions" ) }
                        for definition in list( json_data["components"]["schemas"].keys() ):
                            json_data["components"]["schemas"][self.current_schema + "_" + definition] = json_data["components"]["schemas"].pop( definition )

                    # Process the object (and sub-objects) as needed for further conversion
                    self.update_object( json_data )

                    out_filename = output + os.path.sep + filename.rsplit( ".", 1 )[0] + ".yaml"
                    out_filename_short = filename.rsplit( ".", 1 )[0] + ".yaml"
                    if len( [ i for i in do_not_write if out_filename_short.startswith( i ) ] ) == 0:
                        if overwrite or is_unversioned( filename ) or ( not os.path.isfile( out_filename ) ):
                            out_string = yaml.dump( json_data, default_flow_style = False )
                            with open( out_filename, "w" ) as file:
                                file.write( out_string )

        # Update the URI information with the action information collected
        self.update_uri_info_with_actions()

        # Set up the start of the service document
        print( "Generating Service Document: " + config_data["OutputFile"] )
        service_doc = {}
        service_doc["openapi"] = "3.0.1"
        service_doc["info"] = info_block

        # Add in the general error definition
        service_doc["components"] = {}
        service_doc["components"]["schemas"] = {}
        service_doc["components"]["schemas"]["RedfishError"] = self.generate_redfish_error()

        # Build the paths for the service document
        service_doc["paths"] = {}
        for uri in self.uri_cache:
            service_doc["paths"][uri] = {}
            if not self.uri_cache[uri]["action"]:
                #service_doc["paths"][uri]["head"] = self.generate_operation( uri, HEAD_RESPONSES )
                service_doc["paths"][uri]["get"] = self.generate_operation( uri, GET_RESPONSES )
                if self.uri_cache[uri]["insertable"]:
                    service_doc["paths"][uri]["post"] = self.generate_operation( uri, CREATE_RESPONSES, True )
                if self.uri_cache[uri]["updatable"]:
                    service_doc["paths"][uri]["patch"] = self.generate_operation( uri, PATCH_RESPONSES, True )
                    service_doc["paths"][uri]["put"] = self.generate_operation( uri, PUT_RESPONSES, True )
                if self.uri_cache[uri]["deletable"]:
                    service_doc["paths"][uri]["delete"] = self.generate_operation( uri, DELETE_RESPONSES )
            else:
                service_doc["paths"][uri]["post"] = self.generate_operation( uri, ACTION_RESPONSES, True )
        service_doc["paths"]["/redfish/v1/$metadata"] = self.generate_metadata_operations()
        service_doc["paths"]["/redfish/v1/odata"] = self.generate_odata_operations()

        out_string = yaml.dump( service_doc, default_flow_style = False )
        with open( service_file, "w" ) as file:
            file.write( out_string )

    def load_base_file( self, filename, extensions ):
        """
        Loads an existing OpenAPI specification and initializes the caches from it

        Args:
            filename: The name of the file with the base definitions
            extensions: The URI extensions to apply to given resource types
        """
        try:
            with open( filename ) as yaml_file:
                yaml_data = yaml.load( yaml_file )
        except:
            print( "ERROR: Could not open {}".format( filename ) )
            return

        # Go through each URI
        for uri in yaml_data["paths"]:
            if "get" in yaml_data["paths"][uri]:
                # This is a resource; copy data to the URI cache
                self.uri_cache[uri] = {}
                self.uri_cache[uri]["reference"] = yaml_data["paths"][uri]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
                self.uri_cache[uri]["requestBody"] = self.uri_cache[uri]["reference"]
                self.uri_cache[uri]["insertable"] = False
                self.uri_cache[uri]["updatable"] = False
                self.uri_cache[uri]["deletable"] = False
                self.uri_cache[uri]["action"] = False
                self.uri_cache[uri]["actionResponse"] = None
                if "post" in yaml_data["paths"][uri]:
                    self.uri_cache[uri]["insertable"] = True
                    self.uri_cache[uri]["requestBody"] = yaml_data["paths"][uri]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"]
                if "patch" in yaml_data["paths"][uri]:
                    self.uri_cache[uri]["updatable"] = True
                if "delete" in yaml_data["paths"][uri]:
                    self.uri_cache[uri]["deletable"] = True
                self.uri_cache[uri]["type"] = self.uri_cache[uri]["reference"].rsplit( "/" )[-1]
                self.uri_cache[uri]["deprecated"] = yaml_data["paths"][uri]["get"].get( "deprecated", False )
                self.uri_cache[uri]["reasonDeprecated"] = yaml_data["paths"][uri]["get"].get( "x-deprecatedReason", None )
                self.uri_cache[uri]["versionDeprecated"] = yaml_data["paths"][uri]["get"].get( "x-versionDeprecated", None )

                # Apply any extensions if needed
                if self.uri_cache[uri]["type"] in extensions:
                    for ext_uri in extensions[self.uri_cache[uri]["type"]]:
                        self.uri_cache[ext_uri] = self.uri_cache[uri]
            else:
                # This is an action
                reference = yaml_data["paths"][uri]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"]
                response = yaml_data["paths"][uri]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
                action = "#" + uri.rsplit( "/" )[-1]
                yaml_file = re.search( "([A-Za-z0-9]+\.v[\d]+_[\d]+_[\d]+\.yaml)", reference ).group( 1 )

                if yaml_file not in self.action_cache:
                    self.action_cache[yaml_file] = {}
                self.action_cache[yaml_file][action] = {}
                self.action_cache[yaml_file][action]["reference"] = "#" + reference.rsplit( "#" )[-1]
                if response == "#/components/schemas/RedfishError":
                    self.action_cache[yaml_file][action]["actionResponse"] = None
                else:
                    self.action_cache[yaml_file][action]["actionResponse"] = "#" + response.rsplit( "#" )[-1]

    def check_for_uri_info( self, json_data, filename ):
        """
        Performs pre-processing of the JSON file to get URI and method info

        Args:
            json_data: The JSON object to process
            filename: The name of the file being processed
        """
        if "definitions" in json_data:
            for def_name, definition in json_data["definitions"].items():
                if "uris" in definition:
                    # Initialize defaults for the URI entry
                    insertable = False
                    updatable = False
                    deletable = False
                    deprecated = False
                    deprecated_reason = None
                    deprecated_version = None
                    reference = "UNKNOWN"
                    request_body = "UNKNOWN"

                    # Get the methods for the URI
                    if "insertable" in definition:
                        insertable = definition["insertable"]
                    else:
                        print( "ERROR: No insertable term found in {} for {}".format( filename, def_name ) )

                    if "updatable" in definition:
                        updatable = definition["updatable"]
                    else:
                        print( "ERROR: No updatable term found in {} for {}".format( filename, def_name ) )

                    if "deletable" in definition:
                        deletable = definition["deletable"]
                    else:
                        print( "ERROR: No deletable term found in {} for {}".format( filename, def_name ) )

                    # Get the deprecated info
                    if "deprecated" in definition:
                        deprecated = True
                        deprecated_reason = definition["deprecated"]
                    if "versionDeprecated" in definition:
                        deprecated = True
                        deprecated_version = definition["versionDeprecated"]

                    # Get the external reference
                    if "anyOf" in definition:
                        if self.is_collection( definition ):
                            # Determine what the reference will look like based on its members
                            reference = re.search( "^(.+)\/\w+\.json", definition["anyOf"][-1]["properties"]["Members"]["items"]["$ref"] ).group( 1 )
                            reference = reference + "/" + def_name + ".yaml#/components/schemas/" + def_name + "_" + def_name

                            # Pull out the filename of the collection members to see if it's being converted now
                            mem_filename_full = definition["anyOf"][-1]["properties"]["Members"]["items"]["$ref"].split( "#", 1 )[0]
                            mem_filename = mem_filename_full.rsplit( "/", 1 )[1]
                            mem_definition = definition["anyOf"][-1]["properties"]["Members"]["items"]["$ref"].rsplit( "/", 1 )[-1]
                            try:
                                with open( self.input_dir + os.path.sep + mem_filename ) as json_file:
                                    mem_json_data = json.load( json_file )
                                    request_body = build_external_reference( mem_json_data["definitions"][mem_definition]["anyOf"][-1]["$ref"] )
                            except:
                                retry_count = 0
                                retry_count_max = 20
                                while retry_count < retry_count_max:
                                    try:
                                        req = urllib.request.Request( mem_filename_full )
                                        response = urllib.request.urlopen( req )
                                        mem_json_data = json.loads( response.read().decode() )
                                        request_body = build_external_reference( mem_json_data["definitions"][mem_definition]["anyOf"][-1]["$ref"] )
                                        break
                                    except OSError as e:
                                        if e.errno != errno.ECONNRESET:
                                            break
                                        retry_count += 1
                        else:
                            reference = build_external_reference( definition["anyOf"][-1]["$ref"] )
                            request_body = reference
                    else:
                        print( "ERROR: No anyOf term found in {} for {}".format( filename, def_name ) )

                    # Create an entry for each URI listed
                    for uri in definition["uris"]:
                        self.uri_cache[uri] = {}
                        self.uri_cache[uri]["insertable"] = insertable
                        self.uri_cache[uri]["updatable"] = updatable
                        self.uri_cache[uri]["deletable"] = deletable
                        self.uri_cache[uri]["action"] = False
                        self.uri_cache[uri]["actionResponse"] = None
                        self.uri_cache[uri]["type"] = def_name
                        self.uri_cache[uri]["reference"] = reference
                        self.uri_cache[uri]["requestBody"] = request_body
                        self.uri_cache[uri]["deprecated"] = deprecated
                        self.uri_cache[uri]["reasonDeprecated"] = deprecated_reason
                        self.uri_cache[uri]["versionDeprecated"] = deprecated_version
                        # Specific URIs can be deprecated without deprecating the entire schema
                        if "urisDeprecated" in definition and uri in definition["urisDeprecated"]:
                            self.uri_cache[uri]["deprecated"] = True

    def check_for_actions( self, json_data, filename ):
        """
        Performs pre-processing of the JSON file to get action info

        Args:
            json_data: The JSON object to process
            filename: The name of the file being processed
        """

        yaml_file = filename.replace( ".json", ".yaml", 1 )

        # Get the resource name
        try:
            resource_name = json_data["$ref"].rsplit( "/" )[-1]
        except:
            # Not a resource
            return

        # Get the Actions location
        try:
            action_loc = json_data["definitions"][resource_name]["properties"]["Actions"]["$ref"].rsplit( "/" )[-1]
        except:
            # No actions
            return

        # Go through each action to set up the request body definition
        try:
            for action in json_data["definitions"][action_loc]["properties"]:
                if action == "Oem":
                    continue
                action_def = json_data["definitions"][action_loc]["properties"][action]["$ref"].rsplit( "/" )[-1]

                # Copy the parameters over to the root level definitions
                json_data["definitions"][action_def + "RequestBody"] = {}
                json_data["definitions"][action_def + "RequestBody"]["type"] = "object"
                json_data["definitions"][action_def + "RequestBody"]["additionalProperties"] = False
                json_data["definitions"][action_def + "RequestBody"]["description"] = json_data["definitions"][action_def]["description"]
                json_data["definitions"][action_def + "RequestBody"]["longDescription"] = json_data["definitions"][action_def]["longDescription"]
                json_data["definitions"][action_def + "RequestBody"]["properties"] = json_data["definitions"][action_def]["parameters"]

                # Determine which parameters are required
                for parameter, parameter_object in json_data["definitions"][action_def + "RequestBody"]["properties"].items():
                    if "requiredParameter" in parameter_object:
                        if "required" not in json_data["definitions"][action_def + "RequestBody"]:
                            json_data["definitions"][action_def + "RequestBody"]["required"] = []
                        json_data["definitions"][action_def + "RequestBody"]["required"].append( parameter )
                        json_data["definitions"][action_def + "RequestBody"]["required"].sort()

                # Add the action info to the cache
                if yaml_file not in self.action_cache:
                    self.action_cache[yaml_file] = {}
                self.action_cache[yaml_file][action] = {}
                self.action_cache[yaml_file][action]["reference"] = "#/components/schemas/" + self.current_schema + "_" + action_def + "RequestBody"
                if "actionResponse" in json_data["definitions"][action_def]:
                    self.action_cache[yaml_file][action]["actionResponse"] = "#/components/schemas/" + self.current_schema + "_" + json_data["definitions"][action_def]["actionResponse"]["$ref"].rsplit( "/" )[-1]
                else:
                    self.action_cache[yaml_file][action]["actionResponse"] = None

        except:
            print( "ERROR: Malformed action found in {}".format( filename ) )

    def update_uri_info_with_actions( self ):
        """
        Updates the URI cache with the action information
        """
        action_uri_cache = {}
        for action_filename in self.action_cache:
            for uri in self.uri_cache:
                if ( "/" + action_filename ) in self.uri_cache[uri]["reference"]:
                    # Match found; add the actions to the URI cache
                    for action in self.action_cache[action_filename]:
                        action_uri = uri + "/Actions/" + action[1:]
                        action_reference = self.uri_cache[uri]["reference"].split( "#" )[0]
                        action_uri_cache[action_uri] = {}
                        action_uri_cache[action_uri]["reference"] = action_reference + self.action_cache[action_filename][action]["reference"]
                        action_uri_cache[action_uri]["requestBody"] = action_reference + self.action_cache[action_filename][action]["reference"]
                        action_uri_cache[action_uri]["actionResponse"] = None
                        if self.action_cache[action_filename][action]["actionResponse"] is not None:
                            action_uri_cache[action_uri]["actionResponse"] = action_reference + self.action_cache[action_filename][action]["actionResponse"]
                        action_uri_cache[action_uri]["insertable"] = False
                        action_uri_cache[action_uri]["updatable"] = False
                        action_uri_cache[action_uri]["deletable"] = False
                        action_uri_cache[action_uri]["action"] = True
                        action_uri_cache[action_uri]["deprecated"] = self.uri_cache[uri]["deprecated"]
                        action_uri_cache[action_uri]["reasonDeprecated"] = self.uri_cache[uri]["reasonDeprecated"]
                        action_uri_cache[action_uri]["versionDeprecated"] = self.uri_cache[uri]["versionDeprecated"]

        self.uri_cache.update( action_uri_cache )

    def update_object( self, json_data ):
        """
        Performs a recursive update of all objects in the JSON object

        Args:
            json_data: The JSON object to process
        """

        # Perform one for one replacements (meaning "term" becomes "x-term")
        for replacement in ONE_FOR_ONE_REPLACEMENTS:
            if replacement in json_data:
                json_data["x-" + replacement] = json_data.pop( replacement )

        # Perform simple removals
        for removal in REMOVED_TERMS:
            json_data.pop( removal, None )

        # Update readonly
        # The "o" is capitalized in OpenAPI
        if "readonly" in json_data:
            json_data["readOnly"] = json_data.pop( "readonly" )

        # Update the deprecated info
        # "deprecated" is a built in term, but we don't want to lose track of the reason info
        if "deprecated" in json_data:
            json_data["x-deprecatedReason"] = json_data.pop( "deprecated" )
            json_data["deprecated"] = True

        # Update the patternProperties info
        # "patternProperties" is not in OpenAPI, and some of its inner structures needs special conversion
        if "patternProperties" in json_data:
            json_data["x-patternProperties"] = json_data.pop( "patternProperties" )
            # Remove the type property from patternProperties
            for pattern in json_data["x-patternProperties"]:
                if "type" in json_data["x-patternProperties"][pattern]:
                    json_data["x-patternProperties"][pattern].pop( "type" )

        # Update type to be singular
        # OpenAPI doesn't allow type to be an array; in the Redfish usage, this is for when something is nullable
        if "type" in json_data:
            if isinstance( json_data["type"], list ):
                json_data["type"] = json_data["type"][0]
                json_data["nullable"] = True
        # If the type is an integer, specify it to be 64-bit
        if "type" in json_data:
            if json_data["type"] == "integer":
                json_data["format"] = "int64"

        # Update anyOf to remove null types; OpenAPI defines a "nullable" term
        if "anyOf" in json_data:
            obj_count = 0
            is_nullable = False
            for i, item in enumerate( json_data["anyOf"] ):
                if item == { "type": "null" }:
                    is_nullable = True
                else:
                    obj_count += 1
            if ( obj_count == 1 ) and ( "$ref" in json_data["anyOf"][0] ) and is_nullable:
                json_data["$ref"] = json_data["anyOf"][0]["$ref"]
                json_data.pop( "anyOf" )
                json_data["nullable"] = True

        # Update Resource Collections to remove the anyOf term
        for definition in json_data:
            if self.is_collection( json_data[definition] ):
                try:
                    if len( json_data[definition]["anyOf"] ) == 2:
                        json_data[definition] = json_data[definition]["anyOf"][1]
                except:
                    pass

        # Update $ref to use the form "/components/schemas/" instead of "/definitions/"
        if "$ref" in json_data:
            if json_data["$ref"][0] == "#":
                # Local reference
                json_data["$ref"] = json_data["$ref"].replace( "#/definitions/", "#/components/schemas/" + self.current_schema + "_", 1 )
            else:
                # External reference; find the definition and check if it's a link to a resource or some other definition
                id_ref = False

                # Check if the type name is the same as the schema name
                ref_match = re.match( "^.+\\/(.+).json#\\/definitions\\/(.+)$", json_data["$ref"] )
                if ref_match:
                    if ref_match.group( 1 ) == ref_match.group( 2 ) and ref_match.group( 1 ) != "Redundancy":
                        # They are the same; this MIGHT be a resource link
                        ref_search = re.search( "\/([\w\d_\.\-]+\.json)", json_data["$ref"] )
                        if ref_search:
                            # Check if the file being referenced is also being converted
                            json_file_path = self.input_dir + os.path.sep + ref_search.group( 1 )
                            json_ref_data = {}
                            if os.path.isfile( json_file_path ):
                                with open( json_file_path ) as json_file:
                                    json_ref_data = json.load( json_file )
                            else:
                                # Not local; need to download a copy
                                json_file_path = json_data["$ref"].split( "#" )[0]
                                retry_count = 0
                                retry_count_max = 20
                                while retry_count < retry_count_max:
                                    try:
                                        req = urllib.request.Request( json_file_path )
                                        response = urllib.request.urlopen( req )
                                        json_ref_data = json.loads( response.read().decode() )
                                        break
                                    except OSError as e:
                                        if e.errno != errno.ECONNRESET:
                                            break
                                        retry_count += 1

                            # Get the reference definition
                            ref_definition = json_ref_data.get( "definitions", {} ).get( json_data["$ref"].rsplit( "/" )[-1], None )
                            if ref_definition is None:
                                print( "ERROR: Could not get {}".format( json_data["$ref"] ) )
                            else:
                                # Check if the definition contains an anyOf where the $ref of the first item points to idRef
                                try:
                                    if "/definitions/idRef" in ref_definition["anyOf"][0]["$ref"]:
                                        id_ref = True
                                except:
                                    pass

                # If idRef was found, this is a link; otherwise this is another data type (like an enum or an object)
                if id_ref:
                    json_data["$ref"] = self.odata_schema + "#/components/schemas/odata-v4_idRef"
                else:
                    json_data["$ref"] = build_external_reference( json_data["$ref"] )

        # Perform the same process on all other objects in the structure
        for key in json_data:
            if isinstance( json_data[key], dict ):
                self.update_object( json_data[key] )
            elif isinstance( json_data[key], list ):
                for i, item in enumerate( json_data[key] ):
                    if isinstance( json_data[key][i], dict ):
                        self.update_object( json_data[key][i] )

    def generate_redfish_error( self ):
        """
        Creates the Redfish Error payload

        Returns:
            An object containing the definition of the Redfish Error payload
        """
        redfish_error = {
            "description": "The error payload from a Redfish service.",
            "x-longDescription": "The Redfish Specification-described type shall contain an error payload from a Redfish service.",
            "type": "object",
            "properties": {
                "error": {
                    "description": "The properties that describe an error from a Redfish service.",
                    "x-longDescription": "The Redfish Specification-described type shall contain properties that describe an error from a Redfish service.",
                    "type": "object",
                    "properties": {
                        "code": {
                            "description": "A string indicating a specific MessageId from a message registry.",
                            "x-longDescription": "This property shall contain a string indicating a specific MessageId from a message registry.",
                            "readOnly": True,
                            "type": "string"
                        },
                        "message": {
                            "description": "A human-readable error message corresponding to the message in a message registry.",
                            "x-longDescription": "This property shall contain a human-readable error message corresponding to the message in a message registry.",
                            "readOnly": True,
                            "type": "string"
                        },
                        "@Message.ExtendedInfo": {
                            "description": "An array of messages describing one or more error messages.",
                            "x-longDescription": "This property shall be an array of message objects describing one or more error messages.",
                            "type": "array",
                            "items": {
                                "$ref": self.message_ref
                            }
                        }
                    },
                    "required": [
                        "code",
                        "message"
                    ]
                }
            },
            "required": [
                "error"
            ]
        }
        return redfish_error

    def generate_operation( self, uri, responses, add_request_body = False ):
        """
        Creates an operation object for a given resource

        Args:
            uri: The URI string of the resource
            responses: A list of HTTP responses allowed for the operation
            add_request_body: Flag to indicate if a request body is needed

        Returns:
            An operation object
        """
        operation = {}

        # Build the parameters for the operation
        parameters = self.generate_parameters( uri )
        if parameters is not None:
            operation["parameters"] = parameters

        # Build the request body for the operation
        if ( add_request_body == True ) and ( "requestBody" in self.uri_cache[uri] ):
            operation["requestBody"] = self.generate_request_body( uri )

        # Build the responses for the operation
        operation["responses"] = {}
        for response in responses:
            operation["responses"][str( response )] = self.generate_response( uri, response )
        operation["responses"]["default"] = self.generate_response( uri, 500 )

        # Add deprecation info
        if self.uri_cache[uri]["deprecated"]:
            operation["deprecated"] = True
        if self.uri_cache[uri]["reasonDeprecated"] is not None:
            operation["x-deprecatedReason"] = self.uri_cache[uri]["reasonDeprecated"]
        if self.uri_cache[uri]["versionDeprecated"] is not None:
            operation["x-versionDeprecated"] = self.uri_cache[uri]["versionDeprecated"]

        return operation

    def generate_request_body( self, uri ):
        """
        Creates a request body object for a given resource

        Args:
            uri: The URI string of the resource

        Returns:
            A request body object
        """
        request_body = {}
        request_body["required"] = True
        request_body["content"] = { "application/json": { "schema": { "$ref": self.uri_cache[uri]["requestBody"] } } }
        return request_body

    def generate_response( self, uri, http_status ):
        """
        Creates a response object for a HTTP status

        Args:
            uri: The URI string of the resource
            http_status: The HTTP status of the response

        Returns:
            A response object
        """
        response = {}
        content_resource = { "application/json": { "schema": { "$ref": self.uri_cache[uri]["reference"] } } }
        content_created = { "application/json": { "schema": { "$ref": self.uri_cache[uri]["requestBody"] } } }
        content_task = { "application/json": { "schema": { "$ref": self.task_ref } } }
        content_error = { "application/json": { "schema": { "$ref": "#/components/schemas/RedfishError" } } }
        content_action_response = { "application/json": { "schema": { "$ref": self.uri_cache[uri]["actionResponse"] } } }

        # Build the response descriptor based on the HTTP status code
        if http_status == 200:
            # 200 OK: Resource is returned
            if not self.uri_cache[uri]["action"]:
                response["description"] = "The response contains a representation of the {} resource".format( self.uri_cache[uri]["reference"].rsplit( "/" )[-1].split( "_", 1 )[0] )
                response["content"] = content_resource
            else:
                response["description"] = "The response contains the results of the {} action".format( uri.rsplit( "." )[-1] )
                if self.uri_cache[uri]["actionResponse"] is not None:
                    response["content"] = content_action_response
                else:
                    response["content"] = content_error
        elif http_status == 201:
            # 201 Created: Resource is returned
            if not self.uri_cache[uri]["action"]:
                response["description"] = "A resource of type {} has been created".format( self.uri_cache[uri]["requestBody"].rsplit( "/" )[-1].split( "_", 1 )[0] )
                response["content"] = content_created
            else:
                response["description"] = "The response contains the results of the {} action".format( uri.rsplit( "." )[-1] )
                if self.uri_cache[uri]["actionResponse"] is not None:
                    response["content"] = content_action_response
                else:
                    response["content"] = content_error
        elif http_status == 202:
            # 202 Accepted: Task is returned
            response["description"] = "Accepted; a task has been generated"
            if content_task is not None:
                response["content"] = content_task
        elif http_status == 204:
            # 204 No Content: Nothing is returned
            response["description"] = "Success, but no response data"
        elif http_status == 301:
            # 301 Moved Permanently: Resource is returned
            response["description"] = "Resource moved"
            response["content"] = content_resource
        elif http_status == 302:
            # 302 Found: Resource is returned
            response["description"] = "Resource found"
            response["content"] = content_resource
        elif http_status == 304:
            # 304 Not Modified: Nothing is returned
            response["description"] = "Resource not modified"
        else:
            # Some other code (4xx or 5xx): Error
            response["description"] = "Error condition"
            response["content"] = content_error

        return response

    def generate_parameters( self, uri ):
        """
        Creates a parameters array for a given resource from the URI

        Args:
            uri: The URI string of the resource

        Returns:
            A parameters array
        """
        parameters = None

        # Pull out the URI parameters
        uri_parameters = re.findall( "{[A-Za-z0-9]+}", uri )
        if uri_parameters:
            parameters = []

            # Build the parameter info for each segment of the URI
            for param in uri_parameters:
                parameter = {}
                param_name = re.sub( "[{}]", "", param )
                parameter["name"] = param_name
                parameter["in"] = "path"
                parameter["required"] = True
                parameter["schema"] = { "type": "string" }
                try:
                    parameter["description"] = "The value of the Id property of the " + re.search( "(.+)Id\d?", param_name ).group( 1 ) + " resource"
                except:
                    print( "ERROR: Token {} in {} does not end in 'Id'".format( param, uri ) )
                parameters.append( parameter )

        return parameters

    def is_collection( self, definition ):
        """
        Determines if a given definition structure is for a resource collection

        Args:
            definition: The definition structure to examine

        Returns:
            True if a resource collection; False otherwise
        """
        try:
            if len( definition["anyOf"] ) == 2:
                if "Members" in definition["anyOf"][-1]["properties"]:
                    return True
        except:
            pass

        return False

    def generate_metadata_operations( self ):
        """
        Creates the operation objects for /redfish/v1/$metadata

        Returns:
            The operation objects for /redfish/v1/$metadata
        """

        metadata = {
            "get": {
                "responses": {
                    "200": {
                        "content": {
                            "application/xml": {}
                        },
                        "description": "OData $metadata."
                    },
                    "default": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/RedfishError"
                                }
                            }
                        },
                        "description": "Error condition"
                    }
                }
            }
        }
        return metadata

    def generate_odata_operations( self ):
        """
        Creates the operation objects for /redfish/v1/odata

        Returns:
            The operation objects for /redfish/v1/odata
        """

        odata = {
            "get": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "description": "The OData service document from a Redfish service.",
                                    "type": "object",
                                    "properties": {
                                        "@odata.context": {
                                            "$ref": "http://redfish.dmtf.org/schemas/v1/odata-v4.yaml#/components/schemas/odata-v4_context"
                                        },
                                        "value": {
                                            "description": "The list of services provided by the Redfish service.",
                                            "items": {
                                                "properties": {
                                                    "name": {
                                                        "description": "User-friendly resource name of the resource.",
                                                        "readOnly": True,
                                                        "type": "string"
                                                    },
                                                    "kind": {
                                                        "description": "Type of resource.  Value is `Singleton` for all cases defined by Redfish.",
                                                        "readOnly": True,
                                                        "type": "string"
                                                    },
                                                    "url": {
                                                        "description": "Relative URL for the top-level resource.",
                                                        "readOnly": True,
                                                        "type": "string"
                                                    }
                                                },
                                                "required": [
                                                    "name",
                                                    "kind",
                                                    "url"
                                                ],
                                                "type": "object"
                                            },
                                            "type": "array"
                                        }
                                    },
                                    "required": [
                                        "@odata.context",
                                        "value"
                                    ]
                                }
                            }
                        },
                        "description": "OData service document"
                    },
                    "default": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/RedfishError"
                                }
                            }
                        },
                        "description": "Error condition"
                    }
                }
            }
        }
        return odata

def is_unversioned( name ):
    """
    Checks if a JSON Schema file name is unversioned

    Args:
        name: The string name of the file

    Returns:
        True if the file is unversioned, False otherwise
    """

    # Versioned filename match the form NAME.vX_Y_Z.json
    if re.search( "v([0-9]+)_([0-9]+)_([0-9]+).json$", name ) is None:
        return True
    return False

def build_external_reference( ref ):
    """
    Builds a reference link based on a JSON Schema reference

    Args:
        ref: The external reference

    Returns:
        A string for the OpenAPI external reference
    """
    filename = ref.split( "#", 1 )[0].rsplit( ".", 1 )[0].rsplit( "/", 1 )[1].replace( ".", "_" )
    return ref.replace( ".json#/definitions/", ".yaml#/components/schemas/" + filename + "_", 1 )

if __name__ == '__main__':

    # Get the input arguments
    argget = argparse.ArgumentParser( description = "A tool used to convert Redfish JSON Schema files to Redfish OpenAPI YAML files along with the OpenAPI Service Document" )
    argget.add_argument( "--input", "-I", type = str, required = True, help = "The folder containing the JSON files to convert" )
    argget.add_argument( "--output", "-O",  type = str, required = True, help = "The folder to write the converted YAML files" )
    argget.add_argument( "--config", "-C", type = str, required = True, help = "The JSON file that describes configuration options for the output" )
    argget.add_argument( "--base", "-B", type = str, required = False, help = "The base OpenAPI Service Document if extending an existing one" )
    argget.add_argument( "--overwrite", "-W", type = str, help = "Overwrite the versioned files in the output directory if they already exist (default is True)" )
    args = argget.parse_args()

    # Get the overwrite flag
    overwrite = True
    if args.overwrite is not None:
        if ( args.overwrite == "False" ) or ( args.overwrite == "false" ):
            overwrite = False

    # Read the configuration file
    config_data = {}
    try:
        with open( args.config ) as config_file:
            config_data = json.load( config_file )
    except json.JSONDecodeError:
        print( "ERROR: {} contains a malformed JSON object".format( args.config ) )
        sys.exit( 1 )
    except:
        print( "ERROR: Could not open {}".format( args.config ) )
        sys.exit( 1 )

    # Manage the configuration data
    if "OutputFile" not in config_data:
        config_data["OutputFile"] = CONFIG_DEF_OUT_FILE
    config_data["ODataSchema"] = CONFIG_DEF_ODATA_SCHEMA_LOC
    if "MessageRef" not in config_data:
        config_data["MessageRef"] = CONFIG_DEF_MESSAGE_REF
    if "TaskRef" not in config_data:
        config_data["TaskRef"] = CONFIG_DEF_TASK_REF
    if "Extensions" not in config_data:
        config_data["Extensions"] = CONFIG_DEF_EXTENSIONS
    if "DoNotWrite" not in config_data:
        config_data["DoNotWrite"] = []
    if "info" not in config_data:
        print( "ERROR: Configuration file does not contain 'info' data" )
        sys.exit( 1 )

    # Funnel everything to the translator
    JSONToYAML( args.input, args.output, overwrite, args.base, config_data["OutputFile"], config_data["ODataSchema"], config_data["MessageRef"], config_data["TaskRef"], config_data["info"], config_data["Extensions"], config_data["DoNotWrite"] )

    sys.exit( 0 )
