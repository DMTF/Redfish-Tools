# Example invocations and supporting files

The files in this directory are examples of configuration files that might be used to produce different types of documentation. Below are some example command-line invocations.

These assume that you have a clone of the DMTF/Redfish repo and the DMTF/Redfish-Tools repo in the same parent directory, and that your working directory is the Redfish clone -- so that the schemas are in ./json-schema and doc_generator.py is at ../Redfish-Tools/doc-generator/doc_generator.py relative to your current working directory.

Note that the config files themselves contain references to other files in this directory.


## Produce full documentation, with normative descriptions and in HTML format:

 python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/config_for_standard_html.json

## Produce Profile output (terse mode, HTML format):

  python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/config_for_profile_terse.json

## Produce Subset documentation (HTML format):

  python ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/config_for_subset.json
