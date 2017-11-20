# CSDL to JSON Converter

Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.

## About

The CSDL to JSON Converter is a python3 tool which processes Redfish CSDL files and converts them to the Redfish JSON Schema format.

## Usage

Ensure that the machine running the tool has a python 3 install.

Example: `python3 csdl-to-json.py --input <CSDL-Dir> --output <JSON-Dir> --config <Config-File>`

The tool will process all files found in the folder specified by the *input* argument.  It will convert the contents of the files to create JSON Schema files and save them to the folder specified by the *output* argument; the [Operation section](#operation) section describes this process in more detail.  There are some control parameters that are read in from the JSON file specified by the *config* argument; the [Config File section](#config-file) describes the contents of the file.

### Options

```
usage: csdl-to-json.py [-h] --input INPUT --output OUTPUT [--config CONFIG]
                       [--overwrite OVERWRITE]

A tool used to convert Redfish CSDL files to Redfish JSON Schema files

required arguments:
  --input INPUT, -I INPUT
                        The folder containing the CSDL files to convert
  --output OUTPUT, -O OUTPUT
                        The folder to write the converted JSON files
optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -C CONFIG
                        The configuration file containing definitions for
                        various links and user strings
  --overwrite OVERWRITE, -W OVERWRITE
                        Overwrite the versioned files in the output directory
                        if they already exist (default is True)
```

### Config File

The config file can contain up to five parameters; parameters not defined will have a default value in the tool:
  * Copyright: The copyright string to include in the JSON Schema files
  * RedfishSchema: A pointer to the Redfish extensions to JSON Schema
  * ODataSchema: A pointer to the OData extensions to JSON Schema
  * Location: A pointer to the web folder where the resulting JSON Schema files will be published
  * ResourceLocation: A pointer to the web folder where the core Resource_v1.xml file can be found

Sample File and Default Values:
```
{
    "Copyright": "Copyright 2014-2017 Distributed Management Task Force, Inc. (DMTF). For the full DMTF copyright policy, see http://www.dmtf.org/about/policies/copyright",
    "RedfishSchema": "http://redfish.dmtf.org/schemas/v1/redfish-schema.v1_2_0.json",
    "ODataSchema": "http://redfish.dmtf.org/schemas/v1/odata.4.0.0.json",
    "Location": "http://redfish.dmtf.org/schemas/v1/",
    "ResourceLocation": "http://redfish.dmtf.org/schemas/v1/"
}
```

## Operation

The tool makes several assumptions about the format of the Redfish CSDL files:
  * Each file that defines a resource follows the Redfish model for inheritance by copy; other than the base *Resource* definition, each resource definition is contained in one file
  * Any referenced external namespaces have proper *Include* statements found at the top of the CSL file
  * All annotations have their expected facets filled; for example, the OData.Description annotation must use the *String=* facet
  * All namespaces follow the Redfish defined format where a namespace is either unversioned, or is in the form *name.vX_Y_Z*
  * If a reference is made to another CSDL file, its JSON Schema file will be in the same folder

Before any translation is done, the tool will attempt to locate the Resource_v1.xml schema.  This is to cache properties for base definitions that all resources use.  The tool will first check to see if the file exists in the input directory; if it doesn't exist there, it will access the remote location for the file.

Once the Resource_v1.xml definitions are cached, the tool loops on all files ending in ".xml" in the input directory.  For every namespace found in the file, it will generate a corresponding ".json" file in the following manner:
  * For EntityType and ComplexType definitions...
    * ... that are in an unversioned namespace and are marked as abstract have a definition that contains an "anyOf" statement in the unversioned JSON Schema that points to all versioned definitions
    * ... that are in an unversioned namespace and are not marked as abstract have their definition translated only to the unversioned JSON Schema file
    * ... that are in a versioned namespace have their definitions translated to that version of the JSON Schema file, and newer JSON Schema files
  * Action definitions...
    * ... that are in an unversioned namespace are translated to all versioned JSON Schema files
    * ... that are in a versioned namespace have their definitions translated to that version of the JSON Schema file, and newer JSON Schema files
  * EnumType and TypeDefinition definitions...
    * ... that are in an unversioned namespace are translated to the unversioned JSON Schema file
    * ... that are in a versioned namespace have their definitions translated to that version of the JSON Schema file, and newer JSON Schema files
