#! /usr/bin/python
# Copyright Notice:
# Copyright 2022 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tacklebox/blob/master/LICENSE.md

"""
Registry Document Generator

File : registry-doc-generator.py

Brief : This script builds a Markdown file from a folder of message registries
"""

import argparse
import json
import os

from packaging import version

# Get the input arguments
argget = argparse.ArgumentParser( description = "A tool to build a document for message registries" )
argget.add_argument( "--input", "-I", type = str, required = True, help = "The folder containing the registry files to convert" )
argget.add_argument( "--output", "-O", type = str, required = True, help = "The output Markdown file to generate" )
argget.add_argument( "--intro", "-intro", type = str, help = "File containing intro text to insert at the beginning of the document" )
argget.add_argument( "--postscript", "-postscript", type = str, help = "File containing postscript text to insert at the end of the document" )
args = argget.parse_args()

output = {}
output_str = ""

# Load each file into the output dictionary
registry_files = os.listdir( args.input )
for registry_file in registry_files:
    if registry_file.endswith( ".json" ):
        # Load the file
        with open( args.input + os.path.sep + registry_file ) as file_contents:
            registry_data = json.load( file_contents )

        # Skip non-message registry files
        if not registry_data["@odata.type"].startswith( "#MessageRegistry." ):
            continue

        # Add the contents to the cache if the file is newer or if not cached at all
        if registry_data["RegistryPrefix"] in output:
            if version.parse( registry_data["RegistryVersion"] ) > version.parse( output[registry_data["RegistryPrefix"]]["RegistryVersion"] ):
                output[registry_data["RegistryPrefix"]] = registry_data
        else:
            output[registry_data["RegistryPrefix"]] = registry_data

# Build the output Markdown
for registry in sorted( output.keys() ):
    # Registry heading
    output_str += "## {} {}\n\n".format( registry, output[registry]["RegistryVersion"] )
    output_str += "{}\n\n".format( output[registry]["Description"] )
    messages = sorted( output[registry]["Messages"].keys() )

    # Table of messages
    table_str = "| Message | Severity | Description                  |\n"
    table_str += "| :---    | :---     | :--------------------------- |\n"
    details_str = ""
    for message in messages:
        message_obj = output[registry]["Messages"][message]
        message_obj["MessageLink"] = "{}-{}".format( registry, message )

        # Check that the message contains all expected definitions
        if "Description" not in message_obj or "LongDescription" not in message_obj or "Message" not in message_obj or "MessageSeverity" not in message_obj or "NumberOfArgs" not in message_obj or "Resolution" not in message_obj:
            print( "ERROR: {}.{} does not contain all expected properties; skipping".format( registry, message ) )
            continue
        num_args = message_obj["NumberOfArgs"]
        if num_args == 0:
            if "ParamTypes" in message_obj or "ArgDescriptions" in message_obj or "ArgLongDescriptions" in message_obj:
                print( "ERROR: {}.{} specifies 0 arguments, but contains argument information; skipping".format( registry, message ) )
                continue
        else:
            if "ParamTypes" not in message_obj or "ArgDescriptions" not in message_obj or "ArgLongDescriptions" not in message_obj:
                print( "ERROR: {}.{} does not contain all argument descriptors, but lists a non-zero number of arguments; skipping".format( registry, message ) )
                continue
            if len( message_obj["ParamTypes"] ) != num_args or len( message_obj["ArgDescriptions"] ) != num_args or len( message_obj["ArgLongDescriptions"] ) != num_args:
                print( "ERROR: {}.{} does not specify the correct number of argument descriptors based upon the advertised number of arguments; skipping".format( registry, message ) )
                continue

        # Insert the message into the front table
        table_str += "| [{}](#{}) | {} | {} |\n".format( message, message_obj["MessageLink"], message_obj["MessageSeverity"], message_obj["Description"] )

        # Add the details for the message to the rest of the details body
        details_str += "### {}<a id=\"{}\"/>\n\n".format( message, message_obj["MessageLink"] )
        details_str += "{}\n\n".format( message_obj["Description"] )
        details_str += "* {}\n\n".format( message_obj["LongDescription"] )
        details_str += "Version Added: {}\n\n".format( message_obj.get( "VersionAdded", "1.0.0" ) )
        details_str += "Severity: {}\n\n".format( message_obj["MessageSeverity"] )
        details_str += "Resolution: {}\n\n".format( message_obj["Resolution"] )
        argument_str = ""
        for i in range( num_args ):
            message_obj["Message"] = message_obj["Message"].replace( "%{}".format( i + 1 ), "\<Arg{}\>".format( i + 1 ) )
            argument_str += "{}. *{}*: {}\n".format( i + 1, message_obj["ParamTypes"][i], message_obj["ArgDescriptions"][i] )
            argument_str += "    * {}\n".format( message_obj["ArgLongDescriptions"][i] )
        details_str += "Message and Arguments: \"{}\"\n\n".format( message_obj["Message"] )
        details_str += argument_str + "\n"

    output_str += table_str + "\n" + details_str

# Collect wrapper text
intro_str = ""
postscript_str = ""
if args.intro:
    with open( args.intro ) as file_contents:
        intro_str = file_contents.read()
        intro_str += "\n\n"
if args.postscript:
    with open( args.postscript ) as file_contents:
        postscript_str = file_contents.read()
        postscript_str = "\n\n" + postscript_str

with open( args.output, "w" ) as out_file:
    out_file.write( intro_str + output_str + postscript_str )
