#! /usr/bin/python
# Copyright Notice:
# Copyright 2022 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md

"""
Registry Document Generator

File : registry-doc-generator.py

Brief : This script builds a document from a folder of message registries
"""

import argparse
import json
import os

from packaging import version


def verify_message(message_obj, registry, message):
    """
    Verifies the contents of a message object are valid

    Args:
        message_obj: The message object to verify
        registry: The name of the registry containing the message
        message: The name of the message

    Returns:
        True if valid; False otherwise
    """
    def containsRequiredProperties(r, msg, propertySet, mustContain):
        status = True
        for p in propertySet:
            if mustContain:
                if p not in msg:
                    status &= False
                    print("ERROR: {}.{} does not contain required property {}; skipping".format(
                        r, message, p))
            else:
                if p in msg:
                    status &= False
                    print("ERROR: {}.{} contains unnecessary property {}; skipping".format(
                        r, message, p))
        return status

    # Check that the message contains all expected definitions
    if not containsRequiredProperties(registry, message_obj,
                                      ["Description", "LongDescription", "Message",
                                          "MessageSeverity", "NumberOfArgs", "Resolution"],
                                      True):
        return False
    num_args = message_obj["NumberOfArgs"]
    parameterProperties = ["ParamTypes",
                           "ArgDescriptions", "ArgLongDescriptions"]
    status=True

    if num_args == 0:
        if not containsRequiredProperties(registry, message_obj,
                                          parameterProperties,
                                          False):
            return False
    else:
        if not containsRequiredProperties(registry, message_obj,
                                          parameterProperties,
                                          True):
            return False

        for p in parameterProperties:
            if len(message_obj[p]) != num_args:
                print("ERROR: {}.{} does not specify the correct number of {} descriptors \
                      based upon the advertised number of arguments; skipping".format(
                    registry, message, p))
                status &= False
    return status


# Get the input arguments
argget = argparse.ArgumentParser(
    description="A tool to build a document for message registries")
argget.add_argument("--input", "-I", type=str, required=True,
                    help="The folder containing the registry files to convert")
argget.add_argument("--output", "-O", type=str, required=True,
                    help="The output file to generate")
argget.add_argument("--intro", "-intro", type=str,
                    help="File containing intro text to insert at the beginning of the document")
argget.add_argument("--postscript", "-postscript", type=str,
                    help="File containing postscript text to insert at the end of the document")
argget.add_argument("--format", "-format", type=str, help="The format of the output file; default is 'Markdown'",
                    default="Markdown", choices=["Markdown", "CSV"])
args = argget.parse_args()

output = {}
output_str = ""

# Load each file into the output dictionary
registry_files = os.listdir(args.input)
for registry_file in registry_files:
    if registry_file.endswith(".json"):
        # Load the file
        with open(args.input + os.path.sep + registry_file) as file_contents:
            registry_data = json.load(file_contents)

        # Skip non-message registry files
        if not registry_data["@odata.type"].startswith("#MessageRegistry."):
            continue

        # Add the contents to the cache if the file is newer or if not cached at all
        if registry_data["RegistryPrefix"] in output:
            if version.parse(registry_data["RegistryVersion"]) > version.parse(output[registry_data["RegistryPrefix"]]["RegistryVersion"]):
                output[registry_data["RegistryPrefix"]] = registry_data
        else:
            output[registry_data["RegistryPrefix"]] = registry_data

if args.format == "CSV":
    # Build the output CSV
    for registry in sorted(output.keys()):
        # Registry heading
        output_str += "{},{}\n".format(registry,
                                       output[registry]["RegistryVersion"])
        messages = sorted(output[registry]["Messages"].keys())

        # Table of messages
        output_str += "MessageId,Severity,Message,Description,LongDescription,Resolution,Arg1Type,Arg1Description,Arg1LongDescription," \
                      "Arg2Type,Arg2Description,Arg2LongDescription,Arg3Type,Arg3Description,Arg3LongDescription," \
                      "Arg4Type,Arg4Description,Arg4LongDescription,Arg5Type,Arg5Description,Arg5LongDescription\n"
        for message in messages:
            # Insert the message, if valid
            message_obj = output[registry]["Messages"][message]
            if verify_message(message_obj, registry, message):
                output_str += "{},{},\"{}\",\"{}\",\"{}\",\"{}\"".format(message, message_obj["MessageSeverity"], message_obj["Message"], message_obj["Description"],
                                                                         message_obj["LongDescription"], message_obj["Resolution"])
                for i in range(message_obj["NumberOfArgs"]):
                    output_str += ",{},\"{}\",\"{}\"".format(
                        message_obj["ParamTypes"][i], message_obj["ArgDescriptions"][i], message_obj["ArgLongDescriptions"][i])
                output_str += "\n"
        output_str += "\n"
else:
    # Build the output Markdown
    for registry in sorted(output.keys()):
        # Registry heading
        output_str += "## {} {}\n\n".format(registry,
                                            output[registry]["RegistryVersion"])
        output_str += "### Overview\n\n"
        output_str += "{}\n\n".format(output[registry]["Description"])
        messages = sorted(output[registry]["Messages"].keys())

        # Table of messages
        table_str = "<div class=message_table>\n"
        table_str += "| Message | Severity | Description                  |\n"
        table_str += "| :-----------    | :---     | :------ |\n"
        details_str = ""
        for message in messages:
            # Insert the message, if valid
            message_obj = output[registry]["Messages"][message]
            message_obj["MessageLink"] = "{}-{}".format(registry, message)
            if verify_message(message_obj, registry, message):
                # Insert the message into the front table
                name = message
                if "Deprecated" in message_obj:
                    name = name+"<br>(Deprecated)"
                table_str += "| [{}](#{}) | {} | {} |\n".format(name, message_obj["MessageLink"],
                                                                message_obj["MessageSeverity"], message_obj["Description"])

                # Add the details for the message to the rest of the details body
                details_str += "### {}<a id=\"{}\"/>\n\n".format(
                    message, message_obj["MessageLink"])
                details_str += "{}\n\n".format(message_obj["Description"])
                details_str += "* {}\n\n".format(
                    message_obj["LongDescription"])
                details_str += "Version Added: {}\n\n".format(
                    message_obj.get("VersionAdded", "1.0.0"))
                details_str += "VersionDeprecated: {}\n\n".format(
                    message_obj.get("VersionDeprecated", "N/A"))
                details_str += "Deprecation Details: {}\n\n".format(
                    message_obj.get("Deprecated", "N/A"))
                details_str += "MessageSeverity: {}\n\n".format(
                    message_obj["MessageSeverity"])
                details_str += "Resolution: {}\n\n".format(
                    message_obj["Resolution"])
                argument_str = ""
                for i in range(message_obj["NumberOfArgs"]):
                    message_obj["Message"] = message_obj["Message"].replace(
                        "%{}".format(i + 1), "<Arg{}>".format(i + 1))
                    argument_str += "{}. *{}*: {}\n".format(
                        i + 1, message_obj["ParamTypes"][i], message_obj["ArgDescriptions"][i])
                    argument_str += "    * {}\n".format(
                        message_obj["ArgLongDescriptions"][i])
                details_str += "Message and Arguments: \"{}\"\n\n".format(
                    message_obj["Message"])
                details_str += argument_str + "\n"
        output_str += table_str + "</div>\n" + details_str

    # Collect wrapper text
    intro_str = ""
    postscript_str = ""
    if args.intro:
        with open(args.intro) as file_contents:
            intro_str = file_contents.read()
            intro_str += "\n\n"
    if args.postscript:
        with open(args.postscript) as file_contents:
            postscript_str = file_contents.read()
            postscript_str = "\n\n" + postscript_str
    output_str = intro_str + output_str + postscript_str

# Save the output file
with open(args.output, "w") as out_file:
    out_file.write(output_str)
