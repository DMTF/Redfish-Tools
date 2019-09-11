# Config Files

Config files support most of the command-line arguments of the doc_generator.py script (except for --help and --config). Additional configuration options are supported for some output modes.

Some options may be specified in the supplemental markdown document as well. If an option is specified in more than one way, command-line arguments override all others, and config file options override their counterparts in supplemental markdown.

Config files must be valid JSON.

## Supported Attributes

Note that the names of some config keys differ from their command-line counterparts, as noted. Unless otherwise noted, the meaning of the parameter is the same as its command-line counterpart. All attributes are optional in config files.

- import_from
- format
- normative
- outfile (command line: /out/)
- supfile (command line: /sup/)
- payload_dir
- profile_doc (command line: /profile/)
- profile_terse (command line: /terse/)
- subset
- property_index
- property_index_config_out
- escape_chars (command line: /escape/)

The following properties would otherwise be parsed from the supplemental markdown file. For examples, see the config files in the sample_inputs directory:

- uri_mapping: this should be an object with the partial URL of schema repositories as attributes, and local directory paths as values.
- add_toc: Boolean. If true, generate a table of contents and either substitute it for [add_toc] in the supplemental markdown, or place it at the beginning of the output document. Makes sense only for HTML mode.
- omit_version_in_headers: Boolean. If true, omit schema versions in section headers.
- actions_in_property_table: Boolean. If true, omit "Actions" from the property tables.
- excluded_properties: A list of property names (strings) to omit. Wildcard match is supported for strings that begin with "*" ("*odata.count" matches "Members@odata.count" and others).
- excluded_annotations: A list of annotation names (strings) to omit. Wildcard match is supported for strings that begin with "*".
- excluded_pattern_properties: pattern properties to omit from output. Note that backslashes must be escaped in JSON ("\" becomes "\\").
- excluded_schemas: Schemas (by name) to omit from output.
- ExcludedProperties: synonym for excluded_properties; supported for only for property index output (for backward compatibility).
- DescriptionOverrides: for property index output (only). See the config_for_property_index.json file for examples.


## Examples

Several files in the sample_inputs directory provide examples of configuration files that might be used to produce different types of documentation. Below are some example command-line invocations.

These assume that you have a clone of the DMTF/Redfish repo and the DMTF/Redfish-Tools repo in the same parent directory, and that your working directory is the Redfish clone -- so that the schemas are in ./json-schema and doc_generator.py is at ../Redfish-Tools/doc-generator/doc_generator.py relative to your current working directory.

Note that the config files themselves contain references to other files in this directory.


### Produce full documentation, in HTML format:

 python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/config_for_standard_html.json

Config file references supplemental file *supplement_for_standard_output.md*

### Produce full documentation, with normative descriptions and in HTML format:

 python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/config_for_normative_html.json

Config file references supplemental file *supplement_for_standard_output.md*

### Produce Profile output (terse mode, markdown format):

  python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/config_for_profile_terse.json

Config file references supplemental file *SampleProfileInput.md* and the profile OCPBasicServer.v1_0_0.json (which in turn references OCPManagedDevice.v1_0_0.json).

### Produce Subset documentation (HTML format):

  python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/config_for_subset.json

Config file references supplemental file *SampleProfileInput.md* and the profile OCPBasicServer.v1_0_0.json (which in turn references OCPManagedDevice.v1_0_0.json).


### Produce Property Index output (HTML format):

  python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/config_for_property_index.json

Note that the config file for property index output includes some elements that are specific to that mode: DescriptionOverrides. Property Index mode does not use a supplemental markdown document.

### Produce full documentation, in HTML format:

 python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/config_for_csv.json

Config file references supplemental file *supplement_for_standard_output.md*. (Note that there's a lot of detail in this supplemental file that's irrelevant to CSV output, and is simply ignored.)
