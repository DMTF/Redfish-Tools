[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="center">
  <img src="https://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2018-2021 DMTF. All rights reserved.

[[Redfish-Tools README]](../README.md#redfish-tools "../README.md#redfish-tools")

# JSON Schema-to-OpenAPI converter

The JSON Schema-to-OpenAPI converter, [json-to-yaml.py](json-to-yaml.py#L1 "json-to-yaml.py#L1"), is a Python tool that converts Redfish [JSON Schema](https://json-schema.org/ "https://json-schema.org/") files to [OpenAPI](https://swagger.io/specification/ "https://swagger.io/specification/") files.

## Table of contents

* [Installation](#installation)
* [Configuration](#configuration)
* [Usage](#usage)
* [Example](#example)
* [Processing](#processing)

## Installation

1. Clone the `Redfish-Tools` repository:

   ```bash
   $  git clone git@github.com:DMTF/Redfish-Tools.git
   $  git remote add upstream git@github.com:DMTF/Redfish-Tools.git
   ```
1. [Download and install Python](https://www.python.org/downloads/ "https://www.python.org/downloads/").
1. Install YAML for Python:

    ```bash
    $  pip install pyyaml
    ```

## Configuration

To configure the generated OpenAPI files, define configuration keys in a JSON configuration file. 

To specify the path to the configuration file, use the [--config](#usage "#usage") command‑line argument.

[Table 1](#table-1--configuration-keys "#table-1--configuration-keys") describes the configuration keys that the default [dmtf-config.json](dmtf-config.json#L1 "dmtf-config.json#L1") configuration file contains:

<table id="table-1--configuration-keys">
   <caption><b>Table 1 &mdash; Configuration keys</b></caption>
   <thead>
      <tr>
         <th align="left" valign="top">Configuration&nbsp;key</th>
         <th align="left" valign="top">Description</th>
      </tr>
   </thead>
   <tbody>
      <tr>
         <td align="left" valign="top">
            <a href="dmtf-config.json#L2" title="dmtf-config.json#L2"><code>info</code></a>
         </td>
         <td align="left" valign="top">
            <p>Required. Object that defines information for the OpenAPI service document.</p>
            <p>No default.</p>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <a href="dmtf-config.json#L12" title="dmtf-config.json#L12"><code>OutputFile</code></a>
         </td>
         <td align="left" valign="top">
            <p>Optional. String that defines the output file for the generated OpenAPI service document.</p>
            <p>Default is <code>openapi.yaml</code> in the directory from where you run the tool. </p>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <a href="dmtf-config.json#L13" title="dmtf-config.json#L13"><code>TaskRef</code></a>
         </td>
         <td align="left" valign="top">
            <p>Optional. String that defines the location of the JSON Schema definition of <code>Task</code>.</p>
            <p>Default is <code>http://redfish.dmtf.org/schemas/v1/Task.v1_5_1.yaml#/components/schemas/Task_v1_5_1_Task</code>. </p>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <a href="dmtf-config.json#L14" title="dmtf-config.json#L14"><code>MessageRef</code></a>
         </td>
         <td align="left" valign="top">
            <p>Optional. String that defines the location of the JSON Schema definition of <code>Message</code>.</p>
            <p>Default is <code>http://redfish.dmtf.org/schemas/v1/Message.v1_1_2.yaml#/components/schemas/Message_v1_1_2_Message</code>. </p>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <a href="dmtf-config.json#L15" title="dmtf-config.json#L15"><code>ODataSchema</code></a>
         </td>
         <td align="left" valign="top">
            <p>Optional. String that defines the location of the OData Schema.</p>
            <p>Default is <code>http://redfish.dmtf.org/schemas/v1/odata-v4.yaml</code>.</p>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <a href="dmtf-config.json#L16" title="dmtf-config.json#L16"><code>DoNotWrite</code></a>
         </td>
         <td align="left" valign="top">
            <p>Optional. Array&nbsp;of&nbsp;strings. Each string in the array defines a file to exclude from the generated YAML files.</p>
            <p>Default is:</p>
            <pre lang="json">[
  "Volume.",
  "VolumeCollection.",
  "redfish-error.",
  "redfish-payload-annotations.",
  "redfish-schema.",
  "redfish-schema-"
]</pre>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">
            <code>Extensions</code>
         </td>
         <td align="left" valign="top">
            <p>Optional. Structure of additional URIs to apply to a resource type if provided in the base OpenAPI service document.</p>
         </td>
      </tr>
   </tbody>
</table>

## Usage

```text
usage: json-to-yaml.py [-h] --input INPUT --output OUTPUT --config CONFIG
                       [--base BASE] [--overwrite OVERWRITE]

A tool used to convert Redfish JSON Schema files to Redfish OpenAPI YAML files
along with the OpenAPI Service Document

required arguments:
  --input INPUT, -I INPUT
                        The directory containing the JSON files to convert
  --output OUTPUT, -O OUTPUT
                        The directory to write the converted YAML files
  --config CONFIG, -C CONFIG
                        The JSON file that describes configuration options for
                        the output

optional arguments:
  -h, --help            show this help message and exit
  --base BASE, -B BASE  The base OpenAPI Service Document if extending an
                        existing one
  --overwrite OVERWRITE, -W OVERWRITE
                        Overwrite the versioned files in the output directory
                        if they already exist (default is True)
```

## Example

To run the converter, navigate to the `Redfish-Tools/json-to-openapi-converter` directory and use Python to run `json-to-yaml.py`:

```bash
$ python3 json-to-yaml.py --input ../../Redfish/json-schema --output ../../Redfish/openapi --config dmtf-config.json
```

This example converts the JSON Schema files in the `Redfish/json-schema` input directory to YAML files in the `Redfish/openapi` output directory. The converter reads the configuration keys in the [dmtf-config.json](dmtf-config.json#L1 "dmtf-config.json#L1") configuration file.

## Processing

* [Summary](#summary)
* [Details](#details)

### Summary

The converter processes and converts all JSON Schema files in the input directory to OpenAPI YAML files in the output directory. It also generates the OpenAPI service document that describes the URIs of the Redfish service.

If you specify the optional [--base](#usage "#usage") command-line argument, the converter loads, caches, and begins with the base OpenAPI service document definitions.

If the configuration file contains any URI extensions, the converter maps the new URIs, as needed.

### Details

The converter iterates over the JSON Schema files. During each iteration, the converter:

1. Scans the JSON file for and caches the URI and HTTP method information.
1. Scans the JSON file for and caches action definitions.
1. Converts all properties and objects in the JSON Schema file on a [one-to-one basis](#table-2--mapping-of-json-data-to-openapi-yaml-data "#table-2--mapping-of-json-data-to-openapi-yaml-data") to create OpenAPI YAML files.

    <table id="table-2--mapping-of-json-data-to-openapi-yaml-data">
      <caption><b>Table 2 &mdash; Mapping of JSON data to OpenAPI YAML data</b></caption>
      <thead>
         <tr>
            <th align="left" valign="top">JSON data</th>
            <th align="left" valign="top">OpenAPI YAML data</th>
         </tr>
      </thead>
      <tbody>
         <tr>
            <td align="left" valign="top"><code>longDescription</code></td>
            <td align="left" valign="top"><code>x-longDescription</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>enumDescriptions</code></td>
            <td align="left" valign="top"><code>x-enumLongDescriptions</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>enumDeprecated</code></td>
            <td align="left" valign="top"><code>x-enumDeprecated</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>enumVersionDeprecated</code></td>
            <td align="left" valign="top"><code>x-enumVersionDeprecated</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>enumVersionAdded</code></td>
            <td align="left" valign="top"><code>x-enumVersionAdded</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>units</code></td>
            <td align="left" valign="top"><code>x-units</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>requiredOnCreate</code></td>
            <td align="left" valign="top"><code>x-requiredOnCreate</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>owningEntity</code></td>
            <td align="left" valign="top"><code>x-owningEntity</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>autoExpand</code></td>
            <td align="left" valign="top"><code>x-autoExpand</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>release</code></td>
            <td align="left" valign="top"><code>x-release</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>versionDeprecated</code></td>
            <td align="left" valign="top"><code>x-versionDeprecated</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>versionAdded</code></td>
            <td align="left" valign="top"><code>x-versionAdded</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>filter</code></td>
            <td align="left" valign="top"><code>x-filter</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>excerpt</code></td>
            <td align="left" valign="top"><code>x-excerpt</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>excerptCopy</code></td>
            <td align="left" valign="top"><code>x-excerptCopy</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>excerptCopyOnly</code></td>
            <td align="left" valign="top"><code>x-excerptCopyOnly</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>translation</code></td>
            <td align="left" valign="top"><code>x-translation</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>enumTranslations</code></td>
            <td align="left" valign="top"><code>x-enumTranslations</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>language</code></td>
            <td align="left" valign="top"><code>x-language</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>insertable</code><br /><code>updatable</code><br /><code>deletable</code><br /><code>uris</code><br /><code>parameters</code><br /><code>requiredParameter</code><br /><code>actionResponse</code></td>
            <td align="left" valign="top">Removes these terms from the file.</td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>readonly</code></td>
            <td align="left" valign="top"><code>readOnly</code></td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>deprecated</code></td>
            <td align="left" valign="top">
               <p><code>x-deprecated</code></p>
               <p>Also adds <code>deprecated: true</code>.</p>
            </td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>patternProperties</code></td>
            <td align="left" valign="top">
               <p><code>x-patternProperties</code></p>
               <p>Also removes the nested type object.</p>
            </td>
         </tr>
         <tr>
            <td align="left" valign="top">Properties with an <code>anyOf</code> statement of <code>null</code></td>
            <td align="left" valign="top">
               <p>Adds <code>nullable: true</code> to those properties.</p>
               <p>Also removes the <code>anyOf</code>statement.</p>
            </td>
         </tr>
         <tr>
            <td align="left" valign="top"><code>definitions</code></td>
            <td align="left" valign="top"><code>components/schemas</code></td>
         </tr>
      </tbody>
   </table>
1. Processes the cached URI, HTTP, and action information in the converted JSON Schema files to generate the OpenAPI service document. For each URI, the tool creates the path entry with its HTTP methods, request body, and responses.
