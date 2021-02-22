[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="left">
  <img src="http://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2016-2021 DMTF. All rights reserved.

[[Redfish-Tools README]](../README.md#redfish-tools "../README.md#redfish-tools")

# Redfish doc generator

## Contents

* [About](#about)
* [Installation](#installation)
* [Configuration](#configuration)
* [Usage](#usage)
* [Examples](#examples)
* [Processing](#processing)

## About

<table bgcolor="black" border="2px">
   <tbody>
      <tr>
         <td align="left" valign="top">
            <p><b>IMPORTANT NOTICE ABOUT THE REDFISH DOC GENERATOR v3:</b></p>
            <p>The Redfish doc generator v3 contains <i><b>breaking configuration changes</b></i> and updates to the <code>README</code> files. For information about these changes, see <a href="CHANGES_v2_to_v3.md#redfish-doc-generator-v3-changes" title="CHANGES_v2_to_v3.md#redfish-doc-generator-v3-changes">Redfish doc generator v3 changes</a>. To use the previous version of the doc generator, see <a href="https://github.com/DMTF/Redfish-Tools/releases/tag/doc_gen_v2.0.0" title="https://github.com/DMTF/Redfish-Tools/releases/tag/doc_gen_v2.0.0">Doc Generator v2</a>.</p>
         </td>
      </tr>
   </tbody>
</table>

The **Redfish doc generator**, [`doc_generator.py`](doc_generator.py#L1 "doc_generator.py#L1"), is a Python tool that generates documentation from JSON Schema files and supplemental files in a specified or default [output mode and format](#output-modes-and-formats).

To [configure the generated documentation](#configuration), specify configuration options through either or both configuration keys and command-line arguments. 

## Installation

1. Clone the `Redfish-Tools` repository:
   ```zsh
   % git clone git@github.com:DMTF/Redfish-Tools.git
   % git remote add upstream git@github.com:DMTF/Redfish-Tools.git
   ```
1. [Download and install Python](https://www.python.org/downloads/ "https://www.python.org/downloads/") on the machine from which you will run the tools.
1. Install the following software, which is required for HTML output:
   * [Install Python‑Markdown](https://python-markdown.github.io/install/ "https://python-markdown.github.io/install/").
   * [Install Pygments](http://pygments.org/ "http://pygments.org/").
   * Install requirements:
      ```zsh
      % cd doc-generator
      % pip install -r requirements.txt
      ```
1. (Optional) To make changes to the `doc_generator.py` code, install [`pytest`](https://docs.pytest.org/en/latest/getting-started.html "https://docs.pytest.org/en/latest/getting-started.html"):

    ```zsh
    % pip install -r dev_requirements.txt
    ```

## Configuration

To configure the generated documentation, specify configuration options through either or both:

* [Configuration keys](#configuration-keys)
* [Command-line arguments](#usage)

If you specify a configuration option in more than one way, command&#8209;line arguments take precedence over configuration keys. For information about command&#8209;line arguments, see [Usage](#usage "#usage").

<a id="configuration-keys"></a>You define configuration keys in the [base configuration file](README_config_files.md#base-configuration-file "README_config_files.md#base-configuration-file") and, optionally, in the [content supplement configuration file](README_config_files.md#content-supplement-configuration-file "README_config_files.md#content-supplement-configuration-file").

* Use the `--config` command-line argument to specify the base configuration file.
* The `uri_mapping` configuration key is required but all other configuration keys are optional. Because this key is required, the `--config` command-line argument is also required to specify the base configuration file, which contains the required `uri_mapping` configuration key.
* You can specify some configuration information through configuration keys only and some through command&#8209;line arguments only.
* Depending on the output mode and format, the configuration keys in the base configuration file change. Consequently, several flavors of the base configuration file are available.
* The base configuration file can include pointers to the optional content supplement configuration file and supplemental files.
* The names of some configuration keys differ from their command&#8209;line argument equivalents. Unless otherwise noted, the configuration key has the same meaning as its command&#8209;line argument equivalent.

> **See also:**
> 
> * [`--config` command-line argument](#usage "#usage")
> * [Mapping of command-line arguments to configuration keys](#mapping-of-command-line-arguments-to-configuration-keys)
> * [Output modes and formats](#output-modes-and-formats "#output-modes-and-formats")
> * [Examples](#examples "#examples")
> * [Redfish doc generator configuration and supplemental files](README_config_files.md#redfish-doc-generator-configuration-and-supplemental-files "README_config_files.md#redfish-doc-generator-configuration-and-supplemental-files")

### Mapping of command-line arguments to configuration keys

You can specify some configuration information through configuration keys only and some through command&#8209;line arguments only.

This table maps configuration keys to command-line arguments:

<table>
   <col width="50%">
   <col width="50%">
   <thead>
      <tr>
         <th align="left" valign="top">Configuration key</th>
         <th align="left" valign="top">Command-line argument</th>
      </tr>
   </thead>
   <tbody>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#actions_in_property_table"><code>actions_in_property_table</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#add_toc"><code>add_toc</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#boilerplate_intro"><code>boilerplate_intro</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#boilerplate_postscript"><code>boilerplate_postscript</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#combine_multiple_refs"><code>combine_multiple_refs</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"></td>
         <td align="left" valign="top"><a href="#usage"><code>--config</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#content_supplement"><code>content_supplement</code></a></td>
         <td align="left" valign="top"><a href="#usage"><code>--sup</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#description"><code>description</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#description_overrides"><code>description_overrides</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"></td>
         <td align="left" valign="top"><a href="#usage"><code>--escape</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#excluded_annotations"><code>excluded_annotations</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#excluded_pattern_properties"><code>excluded_pattern_properties</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#excluded_properties"><code>excluded_properties</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#excluded_schemas"><code>excluded_schemas</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#format"><code>format</code></a></td>
         <td align="left" valign="top"><a href="#usage"><code>--format</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"></td>
         <td align="left" valign="top"><a href="#usage"><code>--help</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#html_title"><code>html_title</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#import_from"><code>import_from</code></a></td>
         <td align="left" valign="top"><a href="#usage"><code>import_from</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#normative"><code>normative</code></a></td>
         <td align="left" valign="top"><a href="#usage"><code>--normative</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#object_reference_disposition"><code>object_reference_disposition</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#outfile"><code>outfile</code></a></td>
         <td align="left" valign="top"><a href="#usage"><code>--out</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#payload_dir"><code>payload_dir</code></a></td>
         <td align="left" valign="top"><a href="#usage"><code>--payload_dir</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#profile_doc"><code>profile_doc</code></a></td>
         <td align="left" valign="top"><a href="#usage"><code>--profile</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#property_index"><code>property_index</code></a></td>
         <td align="left" valign="top"><a href="#usage"><code>--property_index</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"></td>
         <td align="left" valign="top"><a href="#usage"><code>--property_index_config_out</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#profile_uri_to_local"><code>profile_uri_to_local</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#registry_uri_to_local"><code>registry_uri_to_local</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#subset_doc"><code>subset_doc</code></a></td>
         <td align="left" valign="top"><a href="#usage"><code>--subset</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#suppress_version_history"><code>suppress_version_history</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#profile_terse"><code>profile_terse</code></a></td>
         <td align="left" valign="top"><a href="#usage"><code>--terse</code></a></td>
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#uri_mapping"><code>uri_mapping</code></a></td>
         <td align="left" valign="top">
      </tr>
      <tr>
         <td align="left" valign="top"><a href="README-base-configuration-file.md#version"><code>version</code></a></td>
         <td align="left" valign="top">
      </tr>
   </tbody>
</table>

### Output modes and formats

To generate documentation for a specific audience, such as a developer, in a specific format, such as Markdown, specify an output mode and output format through either or both command-line arguments and configuration keys. Command-line arguments take precedence over configuration keys. For example, you can produce a [standard normative](#standard-normative-mode) [HTML](#html-format) document for developers.

When you run the doc generator in a specific output mode, only certain command-line arguments and configuration keys apply.

The *output mode* defines the audience for and type of generated documentation:

<table>
   <caption><p align="left"><b>Table 2 &mdash; Output modes</b></p></caption>
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
            <p>For each property, this output includes the property name, list of schemas in which the property is defined, the property type, and property description.</p>
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
         <td align="left" valign="top">Standard guide with normative descriptions for developers. Normative output prefers long descriptions to descriptions.</td>
      </tr>
   </tbody>
</table>

The *output format* defines the format of the generated document:

<table id="output-formats">
   <caption><p align="left"><b>Table 3 &mdash; Output formats</b></p></caption>
   <thead>
      <tr>
         <th align="left" valign="top">Output&nbsp;format</th>
         <th align="left" valign="top">Description</th>
      </tr>
   </thead>
   <tbody>
      <tr id="markdown-format">
         <td align="left" valign="top"><code>markdown</code></td>
         <td align="left" valign="top">Markdown file targeted for the DMTF document publication process.</td>
      </tr>
      <tr id="slate-markdown-format">
         <td align="left" valign="top"><code>slate</code></td>
         <td align="left" valign="top">(Default) GitHub-flavored Markdown file targeted for the <a href="https://github.com/slatedocs/slate" title="https://github.com/slatedocs/slate">Slate API doc generator</a>. For Slate, place the <code>index.html.md</code>output in your Slate repository's source directory.</td>
      </tr>
      <tr id="html-format">
         <td align="left" valign="top"><code>html</code></td>
         <td align="left" valign="top">HyperText Markup Language (HTML) file.</td>
      </tr>
      <tr id="csv-format">
         <td align="left" valign="top"><code>csv</code></td>
         <td align="left" valign="top">Comma-separated values (CSV) file.</td>
      </tr>
   </tbody>
</table>

For the command-line arguments that produce specific output modes and formats, see [output modes and formats](#output-mode-and-format-related-command-line-arguments)

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
                        examples. Optional. Within this directory, use the
                        following naming scheme for example files:
                        <schema_name>-v<major_version>-example.json for JSON
                        payloads, <schema_name-v<major_version>-action-<action
                        _name>.json for action examples.
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

### Output mode and format-related command-line arguments

Use the following command-line arguments to define the output mode and format:

<table>
   <thead>
      <tr>
         <th align="left" valign="top">Command&#8209;line&nbsp;argument</th>
         <th align="left" valign="top">Description</th>
      </tr>
   </thead>
   <tbody>
      <tr>
         <td align="left" valign="top">
            <a href="#usage"><code>--normative</code></a>
         </td>
         <td align="left" valign="top">Generates <a href="#standard-normative-mode">standard normative mode</a>, or developer-focused, documentation.</td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <a href="#usage"><code>--format</code></a>
         </td>
         <td align="left" valign="top">
            <p>Defines the <a href="#output-formats">output format</a>. For the output formats, see <a href="#output-formats" title="#output-formats">output formats</a>.</p>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <a href="#usage"><code>--profile</code></a>
         </td>
         <td align="left" valign="top">Defines path to a JSON profile document, for <a href="#profile-mode">profile mode</a> output.</td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <a href="#usage"><code>--property_index_config_out</code></a>
         </td>
         <td align="left" valign="top">Specifies an output file for updated configuration information. The doc generator extends the input configuration by adding entries for any properties where the property name appears with more than one type or description.</td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <a href="#usage"><code>--terse</code></a>
         </td>
         <td align="left" valign="top">Generates <a href="#profile-mode">terse profile mode</a> documentation, which includes a subset of properties with profile requirements. Meaningful only with <a href="#usage"><code>--profile</code>.</td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <a href="#usage"><code>--subset</code></a>
         </td>
         <td align="left" valign="top">Defines path to a JSON profile document (<code>SUBSET_DOC</code>), which defines the subset. Generates <a href="#schema-subset-mode">schema subset mode</a> documentation.</td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <a href="#usage"><code>--property_index</code></a>
         </td>
         <td align="left" valign="top">Generates <a href="#property-index-mode">property index mode</a> documentation.</td>
      </tr>
   </tbody>
</table>

## Examples

These examples assume that you have clones of the `DMTF/Redfish` and the `DMTF/Redfish-Tools` repositories in the same parent directory, and that your working directory is the `DMTF/Redfish` clone. The schemas are in `./json-schema` and `doc_generator.py` is at `../Redfish-Tools/doc-generator/doc_generator.py` relative to your current working directory.

To run the doc generator, navigate to the `Redfish` directory and use Python to run `doc_generator.py`:

```zsh
% cd Redfish
% python3 ../Redfish-Tools/doc-generator/doc_generator.py --config CONFIG_FILE
```

The `--config` argument specifies the base configuration file. Depending on the [output mode and format](#output-modes-and-formats "#output-modes-and-formats"), the configuration keys in the base configuration file change. The `sample_inputs` directory provides sample configuration files that generate different types of documentation.

These examples show the sample base configuration files and their corresponding command&#8209;line invocations:

* [CSV format](#csv-format)
* [Terse profile mode in Markdown format](#terse-profile-mode-in-markdown-format)
* [Property index mode in HTML format](#property-index-mode-in-html-format)
* [Schema subset mode in HTML format](#schema-subset-mode-in-html-format)
* [Standard mode in HTML format](#standard-mode-in-html-format)
* [Standard normative mode in HTML format](#standard-normative-mode-in-html-format)

<dl>
   <dt id="csv-format-example">
      <h3>CSV format</h3>
   </dt>
   <dd>
      <dl>
         <dt>Base configuration file</dt>
         <dd>
            <table>
               <thead>
                  <tr>
                     <th align="left" valign="top">Sample file</th>
                     <th align="left" valign="top">Configuration keys</th>
                  </tr>
               </thead>
               <tbody>
                  <tr>
                     <td align="left" valign="top"><a href="sample_inputs/csv/config.json#L1" title="sample_inputs/csv/config.json#L1"><code>sample_inputs/csv/config.json</code></a></td>
                     <td align="left" valign="top">
                        <ul>
                           <li><a href="README-base-configuration-file.md#description">description</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_annotations">excluded_annotations</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_pattern_properties">excluded_pattern_properties</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_properties">excluded_properties</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_schemas">excluded_schemas</a></li>
                           <li><a href="README-base-configuration-file.md#format">format</a></li>
                           <li><a href="README-base-configuration-file.md#import_from">import_from</a></li>
                           <li><a href="README-base-configuration-file.md#outfile">outfile</a></li>
                           <li><a href="README-base-configuration-file.md#uri_mapping">uri_mapping</a></li>
                           <li><a href="README-base-configuration-file.md#version">version</a></li>
                        </ul>
                     </td>
                  </tr>
               </tbody>
            </table>
         </dd>
         <dt>Example command</dt>
         <dd>Generates <a href="README.md#csv-format" title="README.md#csv-format">CSV format</a> documentation.</dd>
         <dd>
            <pre lang="zsh">% cd Redfish
% python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/csv/config.json</pre>
         </dd>
      </dl>
   </dd>
   <dd><a href="README-base-configuration-file.md#examples">[Examples]</a></dd>
   <dt id="terse-profile-mode-in-markdown-format">
      <h3>Terse profile mode in Markdown format</h3>
   </dt>
   <dd>
      <dl>
         <dt>Base configuration file</dt>
         <dd>
            <table>
               <thead>
                  <tr>
                     <th align="left" valign="top">Sample file</th>
                     <th align="left" valign="top">Configuration keys</th>
                     <th align="left" valign="top">Referenced files</th>
                  </tr>
               </thead>
               <tbody>
                  <tr>
                     <td align="left" valign="top"><a href="sample_inputs/profile_mode/config.json#L1" title="sample_inputs/profile_mode/config.json#L1"><code>sample_inputs/profile_mode/config.json</code></a></td>
                     <td align="left" valign="top">
                        <ul>
                           <li><a href="README-base-configuration-file.md#boilerplate_intro">boilerplate_intro</a></li>
                           <li><a href="README-base-configuration-file.md#content_supplement">content_supplement</a></li>
                           <li><a href="README-base-configuration-file.md#description">description</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_annotations">excluded_annotations</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_properties">excluded_properties</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_schemas">excluded_schemas</a></li>
                           <li><a href="README-base-configuration-file.md#format">format</a></li>
                           <li><a href="README-base-configuration-file.md#import_from">import_from</a></li>
                           <li><a href="README-base-configuration-file.md#outfile">outfile</a></li>
                           <li><a href="README-base-configuration-file.md#profile_doc">profile_doc</a></li>
                           <li><a href="README-base-configuration-file.md#profile_terse">profile_terse</a></li>
                           <li><a href="README-base-configuration-file.md#profile_uri_to_local">profile_uri_to_local</a></li>
                           <li><a href="README-base-configuration-file.md#registry_uri_to_local">registry_uri_to_local</a></li>
                           <li><a href="README-base-configuration-file.md#uri_mapping">uri_mapping</a></li>
                           <li><a href="README-base-configuration-file.md#version">version</a></li>
                        </ul>
                     </td>
                     <td align="left" valign="top"><p><code>OCPBasicServer.v1_0_0.json</code> profile</p><p><code>OCPManagedDevice.v1_0_0.json</code></p></td>
                  </tr>
               </tbody>
            </table>
         </dd>
         <dt>Example command</dt>
         <dd>Generates <a href="README.md#profile-mode" title="README.md#profile-mode">profile mode</a> documentation.</dd>
         <dd>
            <pre lang="zsh">% cd Redfish
% python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/profile_mode/config.json</pre>
         </dd>
      </dl>
   </dd>
   <dd><a href="README-base-configuration-file.md#examples">[Examples]</a></dd>
   <dt id="property-index-mode-in-html-format">
      <h3>Property index mode in HTML format</h3>
   </dt>
   <dd>
      <dl>
         <dt>Base configuration file</dt>
         <dd>
            <table>
               <thead>
                  <tr>
                     <th align="left" valign="top">Sample file</th>
                     <th align="left" valign="top">Configuration keys</th>
                  </tr>
               </thead>
               <tbody>
                  <tr>
                     <td align="left" valign="top"><a href="sample_inputs/property_index/config.json#L1" title="sample_inputs/property_index/config.json#L1"><code>sample_inputs/property_index/config.json</code></a></td>
                     <td align="left" valign="top">
                        <ul>
                           <li><a href="README-base-configuration-file.md#description">description</a></li>
                           <li><a href="README-base-configuration-file.md#description_overrides">description_overrides</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_properties">excluded_properties</a></li>
                           <li><a href="README-base-configuration-file.md#format">format</a></li>
                           <li><a href="README-base-configuration-file.md#import_from">import_from</a></li>
                           <li><a href="README-base-configuration-file.md#outfile">outfile</a></li>
                           <li><a href="README-base-configuration-file.md#property_index">property_index</a></li>
                           <li><a href="README-base-configuration-file.md#uri_mapping">uri_mapping</a></li>
                           <li><a href="README-base-configuration-file.md#version">version</a></li>
                        </ul>
                     </td>
                  </tr>
               </tbody>
            </table>
         </dd>
         <dd>You can include other configuration keys for your own reference but the doc generator ignores these keys.</dd>
         <dt>Example command</dt>
         <dd>Generates <a href="README.md#property-index-mode" title="README.md#property-index-mode">property index mode</a> documentation.</dd>
         <dd>
            <pre lang="zsh">% cd Redfish
% python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/property_index/config.json</pre>
         </dd>
         <dd>
            <blockquote><b>Note:</b> The base configuration file for property index documentation includes the <code>description_overrides</code> key, which is specific to that mode.</blockquote>
         </dd>
      </dl>
   </dd>
   <dd><a href="README-base-configuration-file.md#examples">[Examples]</a></dd>
   <dt id="schema-subset-mode-in-html-format">
      <h3>Schema subset mode in HTML format</h3>
   </dt>
   <dd>
      <dl>
         <dt>Base configuration file</dt>
         <dd>
            <table>
               <thead>
                  <tr>
                     <th align="left" valign="top">Sample file</th>
                     <th align="left" valign="top">Configuration keys</th>
                     <th align="left" valign="top">Referenced files</th>
                  </tr>
               </thead>
               <tbody>
                  <tr>
                     <td align="left" valign="top"><a href="sample_inputs/subset/config.json#L1" title="sample_inputs/subset/config.json#L1"><code>sample_inputs/subset/config.json</code></a></td>
                     <td align="left" valign="top">
                        <ul>
                           <li><a href="README-base-configuration-file.md#boilerplate_intro">boilerplate_intro</a></li>
                           <li><a href="README-base-configuration-file.md#content_supplement">content_supplement</a></li>
                           <li><a href="README-base-configuration-file.md#description">description</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_annotations">excluded_annotations</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_properties">excluded_properties</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_schemas">excluded_schemas</a></li>
                           <li><a href="README-base-configuration-file.md#format">format</a></li>
                           <li><a href="README-base-configuration-file.md#html_title">html_title</a></li>
                           <li><a href="README-base-configuration-file.md#import_from">import_from</a></li>
                           <li><a href="README-base-configuration-file.md#outfile">outfile</a></li>
                           <li><a href="README-base-configuration-file.md#profile_uri_to_local">profile_uri_to_local</a></li>
                           <li><a href="README-base-configuration-file.md#subset_doc">subset_doc</a></li>
                           <li><a href="README-base-configuration-file.md#suppress_version_history">suppress_version_history</a></li>
                           <li><a href="README-base-configuration-file.md#uri_mapping">uri_mapping</a></li>
                           <li><a href="README-base-configuration-file.md#version">version</a></li>
                        </ul>
                     </td>
                     <td align="left" valign="top"><p><code>OCPBasicServer.v1_0_0.json</code> profile</p><p><code>OCPManagedDevice.v1_0_0.json</code></p></dd>
                  </tr>
               </tbody>
            </table>
         </dd>
         <dt>Example command</dt>
         <dd>Generates <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema&nbsp;subset mode</a> documentation. The JSON profile document defines the subset.</dd>
         <dd>
            <pre lang="zsh">% cd Redfish
% python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/subset/config.json</pre>
         </dd>
      </dl>
   </dd>
   <dd><a href="README-base-configuration-file.md#examples">[Examples]</a></dd>
   <dt id="standard-mode-in-html-format">
      <h3>Standard mode in HTML format</h3>
   </dt>
   <dd>
      <dl>
         <dt>Base configuration file</dt>
         <dd>
            <table>
               <thead>
                  <tr>
                     <th align="left" valign="top">Sample file</th>
                     <th align="left" valign="top">Configuration keys</th>
                  </tr>
               </thead>
               <tbody>
                  <tr>
                     <td align="left" valign="top"><a href="sample_inputs/standard_html/config.json#L1" title="sample_inputs/standard_html/config.json#L1"><code>sample_inputs/standard_html/config.json</code></a></td>
                     <td align="left" valign="top">
                        <ul>
                           <li><a href="README-base-configuration-file.md#add_toc">add_toc</a></li>
                           <li><a href="README-base-configuration-file.md#boilerplate_intro">boilerplate_intro</a></li>
                           <li><a href="README-base-configuration-file.md#boilerplate_postscript">boilerplate_postscript</a></li>
                           <li><a href="README-base-configuration-file.md#combine_multiple_refs">combine_multiple_refs</a></li>
                           <li><a href="README-base-configuration-file.md#content_supplement">content_supplement</a></li>
                           <li><a href="README-base-configuration-file.md#description">description</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_annotations">excluded_annotations</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_pattern_properties">excluded_pattern_properties</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_properties">excluded_properties</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_schemas">excluded_schemas</a></li>
                           <li><a href="README-base-configuration-file.md#format">format</a></li>
                           <li><a href="README-base-configuration-file.md#html_title">html_title</a></li>
                           <li><a href="README-base-configuration-file.md#import_from">import_from</a></li>
                           <li><a href="README-base-configuration-file.md#object_reference_disposition">object_reference_disposition</a></li>
                           <li><a href="README-base-configuration-file.md#outfile">outfile</a></li>
                           <li><a href="README-base-configuration-file.md#payload_dir">payload_dir</a></li>
                           <li><a href="README-base-configuration-file.md#uri_mapping">uri_mapping</a></li>
                           <li><a href="README-base-configuration-file.md#version">version</a></li>
                        </ul>
                     </td>
                  </tr>
               </tbody>
            </table>
         </dd>
         <dt>Example command</dt>
         <dd>Generates <a href="README.md#standard-mode" title="README.md#standard-mode">standard mode</a> documentation.</dd>
         <dd>
            <pre lang="zsh">% cd Redfish
% python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/standard_html/config.json</pre>
         </dd>
         <dd>
            <blockquote><b>Note:</b> The <code>object_reference_disposition</code> key in this configuration file identifies specific behavior for the <code>Redundancy</code> resource and for <code>PCIeInterface</code>, defined in <code>PCIeDevice</code>.</blockquote>
         </dd>
      </dl>
   </dd>
   <dd><a href="README-base-configuration-file.md#examples">[Examples]</a></dd>
   <dt id="standard-normative-mode-in-html-format">
      <h3>Standard normative mode in HTML format</h3>
   </dt>
   <dd>
      <dl>
         <dt>Base configuration file</dt>
         <dd>
            <table>
               <thead>
                  <tr>
                     <th align="left" valign="top">Sample file</th>
                     <th align="left" valign="top">Configuration keys</th>
                  </tr>
               </thead>
               <tbody>
                  <tr>
                     <td align="left" valign="top"><a href="sample_inputs/standard_html/config_normative.json#L1" title="sample_inputs/standard_html/config_normative.json#L1"><code>sample_inputs/standard_html/config_normative.json</code></a></td>
                     <td align="left" valign="top">
                        <ul>
                           <li><a href="README-base-configuration-file.md#add_toc">add_toc</a></li>
                           <li><a href="README-base-configuration-file.md#boilerplate_intro">boilerplate_intro</a></li>
                           <li><a href="README-base-configuration-file.md#boilerplate_postscript">boilerplate_postscript</a></li>
                           <li><a href="README-base-configuration-file.md#combine_multiple_refs">combine_multiple_refs</a></li>
                           <li><a href="README-base-configuration-file.md#content_supplement">content_supplement</a></li>
                           <li><a href="README-base-configuration-file.md#description">description</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_annotations">excluded_annotations</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_pattern_properties">excluded_pattern_properties</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_properties">excluded_properties</a></li>
                           <li><a href="README-base-configuration-file.md#excluded_schemas">excluded_schemas</a></li>
                           <li><a href="README-base-configuration-file.md#format">format</a></li>
                           <li><a href="README-base-configuration-file.md#html_title">html_title</a></li>
                           <li><a href="README-base-configuration-file.md#import_from">import_from</a></li>
                           <li><a href="README-base-configuration-file.md#normative">normative</a></li>
                           <li><a href="README-base-configuration-file.md#object_reference_disposition">object_reference_disposition</a></li>
                           <li><a href="README-base-configuration-file.md#outfile">outfile</a></li>
                           <li><a href="README-base-configuration-file.md#payload_dir">payload_dir</a></li>
                           <li><a href="README-base-configuration-file.md#uri_mapping">uri_mapping</a></li>
                           <li><a href="README-base-configuration-file.md#version">version</a></li>
                        </ul>
                     </td>
                  </tr>
               </tbody>
            </table>
         </dd>
         <dt>Example command</dt>
         <dd>Generates <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative mode</a> documentation.</dd>
         <dd>
            <pre lang="zsh">% cd Redfish
% python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/standard_html/config_normative.json</pre>
         </dd>
      </dl>
   </dd>
   <dd><a href="README-base-configuration-file.md#examples">[Examples]</a></dd>
</dl>

## Processing

The doc generator reads the [base configuration file](README_config_files.md#base-configuration-file "README_config_files.md#base-configuration-file") to locate the `json-schema` directory, the optional content supplement configuration file, and any supplemental files.

Typically, the tool processes an entire set of JSON Schema files for a version.
