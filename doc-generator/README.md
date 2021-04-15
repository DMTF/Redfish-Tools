[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="left">
  <img src="https://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2016-2021 DMTF. All rights reserved.

[[Redfish-Tools README]](../README.md#redfish-tools "../README.md#redfish-tools")

# Redfish doc generator

<table bgcolor="black" border="2px">
   <tbody>
      <tr>
         <td align="left" valign="top">
            <p><b>IMPORTANT NOTICE ABOUT THE REDFISH DOC GENERATOR v3:</b></p>
            <p>The Redfish doc generator v3 contains <i><b>breaking configuration changes</b></i> and updates to the <code>README</code> files. For information about these changes, see <a href="CHANGES_v2_to_v3.md#whats-new-in-redfish-doc-generator-v3" title="CHANGES_v2_to_v3.md#whats-new-in-redfish-doc-generator-v3">What's new in Redfish doc generator v3</a>. To use the previous version of the doc generator, see <a href="https://github.com/DMTF/Redfish-Tools/releases/tag/doc_gen_v2.0.0" title="https://github.com/DMTF/Redfish-Tools/releases/tag/doc_gen_v2.0.0">Doc Generator v2</a>.</p>
         </td>
      </tr>
   </tbody>
</table>

The Redfish doc generator, [doc_generator.py](doc_generator.py#L1 "doc_generator.py#L1"), is a Python tool that generates documentation in a specified or default [output format and mode](#output-formats-and-modes "#output-formats-and-modes") from JSON Schema files and supplemental files.

## Table of contents

* [Installation](#installation)
* [Configuration](#configuration)
* [Output formats and modes](#output-formats-and-modes)
* [Usage](#usage)
* [Processing](#processing)

## Installation

1. Clone the `Redfish-Tools` repository:

   ```bash
   $  git clone git@github.com:DMTF/Redfish-Tools.git
   $  git remote add upstream git@github.com:DMTF/Redfish-Tools.git
   ```
1. [Download and install Python](https://www.python.org/downloads/ "https://www.python.org/downloads/").
1. Install the following software, which is required for HTML documentation:

   * [Install Python‑Markdown](https://python-markdown.github.io/install/ "https://python-markdown.github.io/install/").
   * [Install Pygments](https://pygments.org/ "https://pygments.org/").
   * Install requirements:

      ```bash
      $  cd doc-generator
      $  pip install -r requirements.txt
      ```
1. (Optional) To make changes to the `doc_generator.py` code, install [pytest](https://docs.pytest.org/en/latest/getting-started.html "https://docs.pytest.org/en/latest/getting-started.html"):

    ```bash
    $  pip install -r dev_requirements.txt
    ```

## Configuration

To configure the [output format and mode](#output-formats-and-modes) and other attributes of the generated documentation, define configuration options through [command-line arguments](#command-line-arguments "#command-line-arguments") and [configuration keys](#configuration-keys "#configuration-keys"):

<table id="table-1--configuration-options">
   <caption><b>Table 1 &mdash; Configuration options</b></caption>
   <thead>
      <tr>
         <th align="left" valign="top">Option</th>
         <th align="left" valign="top">Description</th>
      </tr>
   </thead>
   <tbody>
      <tr id="command-line-arguments">
         <td align="left" valign="top"><b>Command&#8209;line&nbsp;arguments</b></td>
         <td align="left" valign="top">
            <p>If you specify a configuration option in more than one way, command&#8209;line arguments take precedence over configuration keys.</p>
            <p>For descriptions of the command-line arguments, see <a href="#usage" title="#usage">Usage</a>.</p>
         </td>
      </tr>
      <tr id="configuration-keys">
         <td align="left" valign="top"><b>Configuration&nbsp;keys</b></td>
         <td align="left" valign="top">
            <p>You define configuration keys in the <a href="README_config_files.md#base-configuration-file" title="README_config_files.md#base-configuration-file">base configuration file</a>.</p>
            <p>The base configuration file can point to the optional <a href="README_config_files.md#content-supplement-configuration-file" title="README_config_files.md#content-supplement-configuration-file">content supplement configuration file</a>, which also contains configuration keys.</p>
            <p>To specify the path to the base configuration file, use the <a href="#usage" title="#usage">--config</a> command‑line argument.</p>
            <p>You can specify some configuration options through command-line arguments only, and some through configuration keys only.</p>
            <p>The names of some configuration keys differ from their command&#8209;line argument equivalents. Unless otherwise noted, configuration keys have the same meaning as their command&#8209;line argument equivalents. The following table maps command-line arguments to configuration keys:</p>
            <blockquote><b>Note:</b> You define all keys in the base configuration file unless otherwise noted.</blockquote>
            <table id="table-mapping-of-command-line-arguments-to-configuration-keys">
               <caption><b>Mapping of command-line-arguments to configuration keys</b></caption>
               <thead>
                  <tr>
                     <th align="left" valign="top">Configuration key</th>
                     <th align="left" valign="top">Command-line argument</th>
                  </tr>
               </thead>
               <tbody>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#actions_in_property_table" title="README_config_files.md#actions_in_property_table">actions_in_property_table</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#add_toc" title="README_config_files.md#add_toc">add_toc</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#boilerplate_intro" title="README_config_files.md#boilerplate_intro">boilerplate_intro</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#boilerplate_postscript" title="README_config_files.md#boilerplate_postscript">boilerplate_postscript</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#combine_multiple_refs" title="README_config_files.md#combine_multiple_refs">combine_multiple_refs</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--config</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#content_supplement" title="README_config_files.md#content_supplement">content_supplement</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--sup</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#description" title="README_config_files.md#description">description</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#description-1" title="README_config_files.md#description-1">description</a><a href="#footnote1"><b><sup>[1]</sup></b></a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#description_overrides" title="README_config_files.md#description_overrides">description_overrides</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#escape_chars" title="README_config_files.md#escape_chars">escape_chars</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--escape</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#excluded_annotations" title="README_config_files.md#excluded_annotations">excluded_annotations</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#excluded_pattern_properties" title="README_config_files.md#excluded_pattern_properties">excluded_pattern_properties</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#excluded_properties" title="README_config_files.md#excluded_properties">excluded_properties</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#excluded_schemas" title="README_config_files.md#excluded_schemas">excluded_schemas</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#format" title="README_config_files.md#format">format</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--format</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--help</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#html_title" title="README_config_files.md#html_title">html_title</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#import_from" title="README_config_files.md#import_from">import_from</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">import_from</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#keywords" title="README_config_files.md#keywords">keywords</a><a href="#footnote1"><b><sup>[1]</sup></b></a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#locale" title="README_config_files.md#locale">locale</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#normative" title="README_config_files.md#normative">normative</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--normative</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#object_reference_disposition" title="README_config_files.md#object_reference_disposition">object_reference_disposition</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#omit_version_in_headers" title="README_config_files.md#omit_version_in_headers">omit_version_in_headers</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#outfile" title="README_config_files.md#outfile">outfile</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--out</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#payload_dir" title="README_config_files.md#payload_dir">payload_dir</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--payload_dir</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#profile_doc" title="README_config_files.md#profile_doc">profile_doc</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--profile</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#profile_terse" title="README_config_files.md#profile_terse">profile_terse</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--terse</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#profile_uri_to_local" title="README_config_files.md#profile_uri_to_local">profile_uri_to_local</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#property_description_overrides" title="README_config_files.md#property_description_overrides">property_description_overrides</a><a href="#footnote1"><b><sup>[1]</sup></b></a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#property_fulldescription_overrides" title="README_config_files.md#property_fulldescription_overrides">property_fulldescription_overrides</a><a href="#footnote1"><b><sup>[1]</sup></b></a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#property_index" title="README_config_files.md#property_index">property_index</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--property_index</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#property_index_config_out" title="README_config_files.md#property_index_config_out">property_index_config_out</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--property_index_config_out</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#registry_uri_to_local" title="README_config_files.md#registry_uri_to_local">registry_uri_to_local</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#schema_link_replacements" title="README_config_files.md#schema_link_replacements">schema_link_replacements</a><a href="#footnote1"><b><sup>[1]</sup></b></a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#schema_supplement" title="README_config_files.md#schema_supplement">schema_supplement</a><a href="#footnote1"><b><sup>[1]</sup></b></a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#subset_doc" title="README_config_files.md#subset_doc">subset_doc</a></td>
                     <td align="left" valign="top"><a href="#usage" title="#usage">--subset</a></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#suppress_version_history" title="README_config_files.md#suppress_version_history">suppress_version_history</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#units_translation" title="README_config_files.md#units_translation">units_translation</a><a href="#footnote1"><b><sup>[1]</sup></b></a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#uri_mapping" title="README_config_files.md#uri_mapping">uri_mapping</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><a href="README_config_files.md#version" title="README_config_files.md#version">version</a></td>
                     <td align="left" valign="top"></td>
                  </tr>
               </tbody>
            </table>
            <p id="footnote1"><b><sup>[1]</sup></b> Define this key in the content supplement configuration file.</p>
         </td>
      </tr>
   </tbody>
</table>

## Output formats and modes

To generate documentation in a specific format for a specific audience, such as an HTML document for a developer, specify an output format and mode. For example, you can produce a [standard normative](#standard-normative-mode) [HTML](#html-format) document for developers.

Depending on the output format and mode, only certain command-line arguments and configuration keys apply. Consequently, [several flavors of the base configuration file](README_config_files.md#example-base-configuration-files-and-command-line-invocations "README_config_files.md#example-base-configuration-files-and-command-line-invocations") are available.

The *output format* defines the format of the generated document. Specify the format through either the <a href="README_config_files.md#format" title="README_config_files.md#format">format</a> configuration key or the <a href="#usage" title="#usage">--format</a> command-line argument. For a description of the output formats, see [Table 1 &mdash; Output formats](README_config_files.md#table-1--output-formats "README_config_files.md#table-1--output-formats").

<a id="output-formats-and-modes"></a>The *output mode* defines the audience for and the type of generated documentation. [Table 2](#table-2--output-modes "#table-2--output-modes") describes the output modes:

<table id="table-2--output-modes">
   <caption><b>Table 2 &mdash; Output modes</b></caption>
   <thead>
      <tr>
         <th align="left" valign="top">Output&nbsp;mode</th>
         <th align="left" valign="top">Description</th>
      </tr>
   </thead>
   <tbody>
      <tr id="profile-mode">
         <td align="left" valign="top">Profile</td>
         <td align="left" valign="top">Schema reference with a subset of properties with profile requirements for service developers. A profile mode document can be terse or verbose. Default is verbose.</td>
      </tr>
      <tr id="property-index-mode">
         <td align="left" valign="top">Property index</td>
         <td align="left" valign="top">
            <p>Property guide that contains an index of property names and descriptions for schema authors, which enables them to locate existing property definitions within the Redfish Schema.</p>
            <p>For each property, this guide includes the property name, list of schemas in which the property is defined, the property type, and property description.</p>
            <p>End users and other consumers of Redfish data can also use a property index to look up property definitions without regard to their location in the schema.</p>
            <p>An example of a property index document is DSP2053, <i>Redfish Property Guide</i> at <a href="https://www.dmtf.org/sites/default/files/standards/documents/DSP2053_2020.4.pdf" title="https://www.dmtf.org/sites/default/files/standards/documents/DSP2053_2020.4.pdf">https://www.dmtf.org/sites/default/files/standards/documents/DSP2053_2020.4.pdf</a>.</p>
         </td>
      </tr>
      <tr id="schema-subset-mode">
         <td align="left" valign="top">Schema subset</td>
         <td align="left" valign="top">Subset of a schema reference to include in white papers or other documents.</td>
      </tr>
      <tr id="standard-mode">
         <td align="left" valign="top">Standard</td>
         <td align="left" valign="top">Standard guide for novice&nbsp;and&nbsp;experienced&nbsp;developers.</td>
      </tr>
      <tr id="standard-normative-mode">
         <td align="left" valign="top">Standard&nbsp;normative</td>
         <td align="left" valign="top">Standard guide with normative descriptions for developers. Normative documentation prefers long descriptions to descriptions.</td>
      </tr>
   </tbody>
</table>

* For the output mode-related configuration keys, see [Example base configuration files and command-line invocations](README_config_files.md#example-base-configuration-files-and-command-line-invocations "README_config_files.md#example-base-configuration-files-and-command-line-invocations").
* For the output mode-related command-line arguments, see [Usage](#usage "#usage").

## Usage

```text
usage: doc_generator.py [-h] [--config CONFIG_FILE] [-n]
                        [--format {markdown,slate,html,csv}] [--out OUTFILE]
                        [--payload_dir payload_dir] [--profile PROFILE_DOC]
                        [-t] [--subset SUBSET_DOC] [--property_index]
                        [--property_index_config_out CONFIG_FILE_OUT]
                        [--escape ESCAPE_CHARS]
                        [import_from ...]

Generate documentation for Redfish JSON schema files.

positional arguments:
  import_from           Name of a file or directory to process (wild cards are
                        acceptable). Default: json-schema

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG_FILE  Path to a config file, containing configuration in
                        JSON format.
  -n, --normative       Produce normative (developer-focused) output
  --format {markdown,slate,html,csv}
                        Output format
  --out OUTFILE         Output file (default depends on output format:
                        output.md for Markdown, index.html for HTML,
                        output.csv for CSV
  --payload_dir payload_dir
                        Directory location for JSON payload and Action
                        examples. Optional.Within this directory, use the
                        following naming scheme for example files:
                        <schema_name>-v<major_version>-example.json for JSON
                        payloads for a documented schema,
                        <schema name>-v<major>-<action name>-request-example.json for
                        an Action request example,
                        <schema name>-v<major>-<action name>-request-example.json for
                        an Action response example.
  --profile PROFILE_DOC
                        Path to a JSON profile document, for profile output.
  -t, --terse           Terse output (meaningful only with --profile). By
                        default, profile output is verbose and includes all
                        properties regardless of profile requirements. "Terse"
                        output is intended for use by Service developers,
                        including only the subset of properties with profile
                        requirements.
  --subset SUBSET_DOC   Path to a JSON profile document. Generates "Schema
                        subset" output, with the subset defined in the JSON
                        profile document.
  --property_index      Produce Property Index output.
  --property_index_config_out CONFIG_FILE_OUT
                        Generate updated config file, with specified filename
                        (property_index mode only).
  --escape ESCAPE_CHARS
                        Characters to escape (\) in generated Markdown. For
                        example, --escape=@#. Use --escape=@ if strings with
                        embedded @ are being converted to mailto links.

Example:
   doc_generator.py --format=html
   doc_generator.py --format=html --out=/path/to/output/index.html /path/to/spmf/json-files
```

## Processing

The doc generator reads the [base configuration file](README_config_files.md#base-configuration-file "README_config_files.md#base-configuration-file") to locate:

* The `json-schema` directory
* The optional content supplement configuration file
* Any optional supplemental files

Typically, the tool processes an entire set of JSON Schema files for a version.
