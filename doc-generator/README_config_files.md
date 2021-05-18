# Config Files

Config files support most of the command-line arguments of the doc_generator.py script (except for --help and --config). Additional configuration options are supported for some output modes.

If an option is specified in more than one way, command-line arguments override those in the config file.

Config files must be valid JSON.

The [Base Configuration file](#base-configuration-file-supported-attributes) is a JSON file that can specify most of the options available for the doc generator, including the command-line options. This file is also where you will specify the location of other configuration files, including the Content Supplement and boilerplate (intro and postscript) files.

The [Content Supplement file](#content-supplement-config-file-supported-attributes) is a JSON file that contains text replacements and additions to be applied to the generated schema documentation. It includes text overrides for property descriptions, units translation (replacements for unit abbreviations), and schema-specific content including intros, postscripts, and property description substitutions.


## Base Configuration file: Supported Attributes

Note that the names of some config keys differ from their command-line counterparts, as noted. Unless otherwise noted, the meaning of the parameter is the same as its command-line counterpart. The `uri_mapping` attribute is expected. All other attributes are optional in config files.

- actions_in_property_table: Boolean. If true, omit "Actions" from the property tables.
- add_toc: Boolean. If true, generate a table of contents and either substitute it for `[add_toc]` in the boilerplate (intro or postscript), or place it at the beginning of the output document. If `[add_toc]` appears anywhere in the boilerplate, this flag is automatically set to true.
- boilerplate_intro: location of a markdown file providing content to place at the beginning of the document (prior to the generated schema documentation). If a relative path, should be relative to the location of the config file.
- boilerplate_postscript: location of a markdown file providing content to place at the end of the document (after to the generated schema documentation). If a relative path, should be relative to the location of the config file.
- combine_multiple_refs: specifies a threshold at which multiple references to the same object within a schema will be moved into Property Details, instead of expanded in place. See below for more detail.
- content_supplement: location of a content supplement file. This is a JSON file that specifies content substitutions to be made within the generated schema documentation. If a relative path, should be relative to the location of the config file.
- escape_chars (command line: `escape`): Characters to escape in generated Markdown. For example, use --escape=@ if strings with embedded @ are being converted to mailto links by your markdown processor.
- excluded_annotations: A list of annotation names (strings) to omit. Wildcard match is supported for strings that begin with "*".
- excluded_pattern_properties: pattern properties to omit from output. Note that backslashes must be escaped in JSON ("\" becomes "\\").
- excluded_properties: A list of property names (strings) to omit. Wildcard match is supported for strings that begin with "*" ("*odata.count" matches "Members\@odata.count" and others).
- excluded_schemas: Schemas (by name) to omit from output.
- format (command line: `format`): Output format. One of `markdown`, `slate`, `html`, `csv`
- html_title: A string to use as the `title` element in HTML output.
- import_from: Name of a file or directory containing JSON schemas to process. Wild cards are acceptable. Default: json-schema.
- locale: specifies a locale code (case-sensitive) for localized output. Localization of strings supplied by the doc generator code uses gettext. Locale files go in the "locale" directory in the doc_generator root. Translated descriptions and annotations may be supplied in localized JSON schema files.
- normative: Produce normative (developer-focused) output.
- object_reference_disposition: a data structure that specifies properties that should be moved to the "Common Objects" section and/or objects that should be included inline where they are referenced, to override default behavior. See below.
- omit_version_in_headers: Boolean. If true, omit schema versions in section headers.
- outfile (command line: `out`): Output file (default depends on output format: output.md for Markdown, index.html for HTML, output.csv for CSV
- payload_dir (command line: `payload_dir`): Directory location for JSON payload and Action examples. Optional. See below for more detail.
- profile_doc (command line: `profile`): Path to a JSON profile document, for profile output.
- profile_terse (command line: `terse`): Boolean. Produce "terse" profile output; meaningful only in profile mode. See below for more detail.
- profile_uri_to_local: For profile mode only, an object like uri_mapping, for locations of profiles.
- property_index (command line: `property_index`): Boolean: Produce Property Index output. See README_Property_Index(README_Property_Index.md) for more information about this mode.
- property_index_config_out (command line: `property_index_config_out`): Generate an updated config file, with specified filename (property_index mode only).
- registry_uri_to_local: For profile mode only, an object like uri_mapping, for locations of registries.
- subset (command_line: `subset`): Path to a JSON profile document. Generates "Schema subset" output, with the subset defined in the JSON profile document.
- supplement_md_dir: Directory location for markdown files with supplemental text. Optional. See below for more detail.
- uri_mapping: this should be an object with the partial URL of schema repositories as attributes, and local directory paths as values.
- with_table_numbering: Boolean, default false. Applies to markdown output only! When true, table captions and references will be added to the output. You will need to run a post-processor on the output to complete the numbering. See TABLE_NUMBER_README.md[TABLE_NUMBER_README.md].


### In More Detail

#### combine_multiple_refs

The combine_multiple_refs attribute specifies a threshold at which multiple references to the same object within a schema will be moved into Property Details, instead of expanded in place. For example, include the following to specify that if an object is referred to three or more times, it should be moved into property details:

```
      "combine_multiple_refs": 3,
```

#### supplement_md_dir

The supplement_dir attribute specifies a directory location for supplemental markdown content, on a schema-by-schema basis. This directory should contain a separate file for each documented schema for which you intend to provide supplemental content. Each file should be named with the schema name and a .md suffix; for example "Chassis.md".

Within these markdown files, headings with a distinct format are used to identify different chunks of text:

| Field | Delimiter | Purpose |
| ----- | --------- | ------- |
| description | #-- description | Replaces the schema's description |
| jsonpayload | #-- jsonpayload | Example payload for this schema (or descriptive text to take the place of such a payload) |
| property_details | #-- property_details | Marks the beginning of a block of Property Details for specific properties |
| (property name)  | #-- PropertyName | Marks a property details block for PropertyName. Can be used to add a Property Details section for a property that is not an enum. |

Note that these properties may also be supplied in the schema_supplement attribute in the Content Supplement Config file. In the case of a conflict, the Content Supplement Config file takes precedence.

A very simple example can be found in doc_generator/tests/samples/supplement_tests/md_supplements/

#### object_reference_disposition

The object_reference_disposition attribute specifies a JSON object with "common_object" and "include" fields (either or both may be specified), each of which specifies a list. The "common_object" list consists of property names, for example "Redundancy." The "include" list specifies properties by their full path. For example:

```json
    "object_reference_disposition": {
        "common_object": [
            "Redundancy"
        ],
        "include": [
            "http://redfish.dmtf.org/schemas/v1/PCIeDevice.json#/definitions/PCIeInterface"
        ]
    }
```

#### payload_dir

The payload_dir attribute specifies a directory location for JSON payload and Action examples. If relative, this path is relative to the working directory in which the doc_generator.py script is run. Within the payload directory, use the following naming scheme for example files:

 * &lt;schema_name&gt;-v<major_version>-example.json for JSON payloads
 * &lt;schema_name&gt;-v&lt;major_version&gt;-action-&lt;action_name%gt;.json for action examples

#### profile_terse

The profile_terse attribute is meaningful only when a profile document is also specified. When true, "terse" output will be produced. By default, profile output is verbose and includes all properties regardless of profile requirements. "Terse" output is intended for use by Service developers, including only the subset of properties with profile requirements.


## Content Supplement Config file: Supported Attributes

- property_description_overrides: a dictionary mapping property names to strings to use to replace the descripions of the named properties.
- property_fulldescription_overrides: a dictionary just like property_description_overrides. These replacements are "full" in that any additional information the doc generator would normally append, like a reference to the definition of the property in another schema, will be omitted.
- schema_link_replacements: a dictionary mapping URIs of schema references to a structure specifying match type (full or partial) and replacement URIs. This can be used to substitute a link to documentation where a link to a specific schema would otherwise appear in the documentation. See below for details.
- schema_supplement: a dictionary mapping schema names to a dictionary of structured content, including introductory text and schema-specific text replacements. See below for details.
- units_translation: a dictionary mapping units as they appear in Redfish schemas to units as you want them to appear in the documentation.

### In More Detail

#### schema_link_replacements

The schema_link_replacements attribute defines a dictionary mapping URIs of schema references to replacement URIs. This can be used to substitute a link to documentation where a link to a specific schema would otherwise appear in the documentation. The structure of this dictionary is:

```json

    "schema_link_replacements": {
        "https://somewhere.example.com/some/path/to/a/some_schema.json": {
            "full_match": true,
            "replace_with": "https://docserver.example.org/some_schema_doc.html"
        },
        "fancy": {
            "full_match": false,
            "replace_with": "https://docserver.example.org/fancy_schemas.html"
        }
    }
```

#### schema_supplement

The schema_supplement attribute defines a dictionary of structured content, including text overrides for property descriptions, units translation (replacements for unit abbreviations), schema-specific intros, property description substitutions, and other supplementary data. The structure of this object looks like this (all fields are optional):

```json
    "schema_supplement": {
        "SchemaName": {
            "description": "A string to replace the schema description. Plain text or markdown.",
            "mockup": "A path or URI to a mockup file.",
            "jsonpayload": "A chunk of JSON.",
            "intro": "",
            "property_description_overrides": {
		"PropertyName": "a string, plain text or markdown.",
		"AnotherPropertyName": "a string, plain text or markdown."
            },
            "property_fulldescription_overrides": {
		"YetAnotherPropertyName": "a string, plain text or markdown. This string will also eliminate any additional data the doc generator would normally append to the description."
            },
            "property_details": {
                "EnumPropertyName": "A string, plain text or markdown. This will be inserted after the property description and prior to the table of enum details in the property information under Property Details.",
                "property_details": {
                   "UUID": "\nThe UUID property contains a value that represents the universal unique identifier number (UUID) of a system.\n\nThe UUID property is a string data type. The format of the string is the 35-character string format specified in RFC4122: \"xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\". Each x represents a hexadecimal digit (0-f).\n\nRegarding the case of the hex values, RFC4122 specifies that the hex values should be lowercase characters. Most modern scripting languages typically also represent hex values in lowercase characters following the RFC. However, dmidecode, WMI and some Redfish implementations currently use uppercase characters for UUID on output."
                }
            }
	}
```

Here, "SchemaName" may be a bare schema name, or it may be a schema name with an underscore and major version appended; e.g., "ComputerSystem" or "ComputerSystem_2".

If `description` or `intro` are specified for a schema, that value will replace the description of the schema. If both are specified, the `description` will be output, followed by the `intro`.

The `mockup` and `jsonpayload` attributes are mutually exclusive. If both are provided, the content found at `mockup` will take precedence. Using a payload directory (specified as `payload_dir` in the Base Configuration file) is preferred over using these attributes.

## Examples

Several files in the sample_inputs directory provide examples of configuration files that might be used to produce different types of documentation. Below are some example command-line invocations.

These assume that you have a clone of the DMTF/Redfish repo and the DMTF/Redfish-Tools repo in the same parent directory, and that your working directory is the Redfish clone -- so that the schemas are in ./json-schema and doc_generator.py is at ../Redfish-Tools/doc-generator/doc_generator.py relative to your current working directory.
n
Note that the config files themselves contain references to other files in this directory.


### Produce full documentation, in HTML format:

 python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/standard_html/config.json

Note that the "object_reference_disposition" part of this config identifies specific behavior for the Redundancy resource and for PCIeInterface (defined in PCIeDevice).

### Produce full documentation, with normative descriptions and in HTML format:

 python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/standard_html/config_normative.json

### Produce Profile output (terse mode, markdown format):

  python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/profile_mode/config.json

Config file references the profile OCPBasicServer.v1_0_0.json (which in turn references OCPManagedDevice.v1_0_0.json).

### Produce Subset documentation (HTML format):

  python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/subset/config.json

Config file references the profile OCPBasicServer.v1_0_0.json (which in turn references OCPManagedDevice.v1_0_0.json).


### Produce Property Index output (HTML format):

  python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/property_index/config.json

Note that the Base Configuration file for property index output includes some elements that are specific to that mode: description_overrides.

### Produce CSV output:

 python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/csv/config.json
