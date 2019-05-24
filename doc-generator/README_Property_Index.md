# Redfish Documentation Generator: Property Index Mode

Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.

## About

The `doc_generator` can be used to produce an index of property names and descriptions.
The resulting output will include property name, type, schema(s) where found, and description(s) found.

When run in "Property Index" mode, only a few of doc_generator.py's arguments are relevant, and the
configuration file takes a different form from that used for the other output modes.

Relevant arguments are:

```
positional arguments:
  import_from           Name of a file or directory to process (wild cards are
                        acceptable). Default: json-schema

optional arguments:
  -h, --help            show this help message and exit
  -n, --normative       Produce normative (developer-focused) output
  --format {markdown,html,csv}
                        Output format
  --property_index      Produce Property Index output.
  --property_index_config_out CONFIG_FILE_OUT
                        Generate updated config file, with specified filename
                        (property_index mode only).
  --out OUTFILE         Output file (default depends on output format:
                        output.md for Markdown, index.html for HTML,
                        output.csv for CSV
  --sup SUPFILE         Path to the supplemental material document. For
                        Property Index mode, this document should simply be
                        an HTML or markdown file containing any content
                        you want to include before/after the property index, and
                        a marker "[insert property index]" where the property index
                        output should go.
  --config CONFIG_FILE  Path to a config file, containing configuration in
                        JSON format. Used in property_index mode only.

Example:
   doc_generator.py --property_index --format=html --config=pi_config.json
```

## Config File

The config file for this mode is a json document. It should include the following elements:

* uri_mapping: Maps partial URIs (without protocol prefix) to local directories or files.
* ExcludedProperties: A list of property names to exclude from the output.
* DescriptionOverrides: an object keyed by property name, which can specify descriptions to "override" those found in the source schemas. (There's more about this below!)

Other properties may be included for the user's reference, and will be ignored by the Doc Generator.

A simple example config:

```
{
   "description": "Redfish Property Index generation file",
   "version": "2018.2",
    "uri_mapping": { "redfish.dmtf.org/schemas/v1": "./json-schema" },
   "ExcludedProperties": [
      "description",
      "Id",
      "@odata.context",
      "@odata.type",
      "@odata.id",
      "@odata.etag",
      "*@odata.count"
   ],
   "DescriptionOverrides": {
      "EventType": [
         {
            "overrideDescription": "This indicates the type of an event recorded in this log.",
            "globalOverride": true,
            "type": "string"
         }
      ],
       "FirmwareVersion": [
           {
               "description": "Firmware version.",
               "type": "string",
               "knownException": true,
               "overrideDescription": "Override text for FirmwareVersion",
               "schemas": [
                   "AttributeRegistry/SupportedSystems"
               ]
           },
           {
               "overrideDescription": "The firmware version of this thingamajig.",
               "type": "string",
               "knownException": true,
               "schemas": [
                   "Power/PowerSupplies",
                   "Manager",
                   "ComputerSystem/TrustedModules",
                   "Storage/StorageControllers"
               ]
           },
           {
               "description": "The version of firmware for this PCIe device.",
               "type": "string",
               "knownException": true,
               "schemas": [
                   "PCIeDevice"
               ]
           }
       ]
   }
}
```

### URI Mapping

This object maps partial URIs, as found in the schemas, to local directories. The partial URI should include the domain part of the URI but can omit the protocol (http:// or https://).

```
    "uri_mapping": { "redfish.dmtf.org/schemas/v1": "./json-schema" }
```

### Excluded Properties

To exclude properties from the output, simply include them in the ExcludedProperties list. An asterisk as the first character in a property acts as a wild card; in this example, any property name that ends with "@odata.count" will be omitted.

```
   "ExcludedProperties": [
      "description",
      "Id",
      "@odata.context",
      "@odata.type",
      "@odata.id",
      "@odata.etag",
      "*@odata.count"
   ],
```

### Description Overrides

Descriptions for individual properties can be overridden. The DescriptionOverrides object is keyed by property name. Values are lists, allowing you to specify different overrides for the same property in different schemas. Each object in the list can have the following entries:

* type: the property type
* schemas: a list of schemas this element applies to
* overrideDescription: a string to replace the description found in the schema
* globalOverride: indicates that the overrideDescription in this element applies to all instances of the property name where the type matches
* description: the description found in the schema
* knownException: indicates that a variant description is expected

The *description* and *knownException* entries are primarily for user reference; when generating configuration output the `doc_generator` will include the description and set knownException to false; the user can edit the resulting output to distinguish expected exceptions from those that need attention. Neither field affects the property index document itself.

Some examples:


```
      "EventType": [
         {
            "overrideDescription": "This indicates the type of an event recorded in this log.",
            "globalOverride": true,
            "type": "string"
         }
      ]

```

The combination of "globalOverride" and "overrideDescription" indicates that all instances of the EventType property that have type "string" should have their description replaced with "This indicates the type of an event recorded in this log."


```
       "FirmwareVersion": [
           {
               "description": "Firmware version.",
               "type": "string",
               "knownException": true,
               "overrideDescription": "Override text for FirmwareVersion",
               "schemas": [
                   "AttributeRegistry/SupportedSystems"
               ]
           },
           {
               "overrideDescription": "The firmware version of this thingamajig.",
               "type": "string",
               "knownException": true,
               "schemas": [
                   "Power/PowerSupplies",
                   "Manager",
                   "ComputerSystem/TrustedModules",
                   "Storage/StorageControllers"
               ]
           },
           {
               "description": "The version of firmware for this PCIe device.",
               "type": "string",
               "knownException": true,
               "schemas": [
                   "PCIeDevice"
               ]
           }
       ]
   }
```

The first two entries in this "FirmwareVersion" example override the description for FirmwareVersion, with type "string", in the specific schemas listed. The third entry identifies another instance of FirmwareVersion with another description, which should not be overridden but is expected.

## Config File Output

Use the --property_index_config_out flag to specify an output file for updated configuration information. The `doc_generator` will extend the input configuration by adding entries for any properties where:

* The property name appears with more than one type
* The property name appears with more than one description

If you have specified "globalOverride" for a property name or property name/type, no data will be added for matching instances.

All added entries will include *"knownException": false*. In addition, if an entry was flagged with *"knownException": true* in the input configuration, but the description no longer matches, *knownException* will be set to false. (In the example above, if FirmwareVersion in the PCIeDevice schema had a different description than the one listed in the example input, it would appear in the output with its new description and *"knownException": false*.