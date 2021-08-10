[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="center">
  <img src="https://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2017-2021 DMTF. All rights reserved.

[[Redfish-Tools README]](../README.md#redfish-tools "../README.md#redfish-tools")

# CSDL-to-JSON converter

The CSDL-to-JSON converter, [csdl-to-json.py](csdl-to-json.py#L1 "csdl-to-json.py#L1"), is a Python tool that converts Redfish [Common Schema Definition Language (CSDL)](http://docs.oasis-open.org/odata/odata/v4.0/odata-v4.0-part3-csdl.html "http://docs.oasis-open.org/odata/odata/v4.0/odata-v4.0-part3-csdl.html") files to [JSON Schema](https://json-schema.org/ "https://json-schema.org/") files.

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

## Configuration

To configure the generated JSON Schema files, define configuration keys in a JSON configuration file. To specify the path to the configuration file, use the [--config](#usage "#usage") command‑line argument.

If you do not specify a configuration file or omit any configuration keys from the specified configuration file, the converter uses the key values in the default [dmtf&#8209;config.json](dmtf-config.json#L1 "dmtf-config.json#L1") configuration file. The configuration file defines these [configuration keys](#table-1--configuration-keys "#table-1--configuration-keys"):

<b id="table-1--configuration-keys">Table 1 &mdash; Configuration keys</b>

| Configuration key  | Description                                                     |
| :----------------- | :-------------------------------------------------------------- |
| [`Copyright`](dmtf-config.json#L2 "dmtf-config.json#L2") | Copyright string to include in the generated JSON Schema files. |
| [`RedfishSchema`](dmtf-config.json#L3 "dmtf-config.json#L3") | String. Location of Redfish Schema files. |
| [`ODataSchema`](dmtf-config.json#L4 "dmtf-config.json#L4") | String. Location of OData Schema files. |
| [`Location`](dmtf-config.json#L5 "dmtf-config.json#L5") | String. Directory for the generated JSON Schema files. |
| [`ResourceLocation`](dmtf-config.json#L6 "dmtf-config.json#L6") | String. Location of Redfish resources. |
| [`DoNotWrite`](dmtf-config.json#L7 "dmtf-config.json#L7") | Array of strings. Each string is the file name of the file to exclude from the generated JSON Schema files. |

## Usage

The required arguments are <code translate="no">--input <var>INPUT</var></code> and <code translate="no">--output <var>OUTPUT</var></code>.

The optional arguments are <code translate="no">--config <var>CONFIG</var></code>, which defaults to <code translate="no">dmtf&#8209;config.json</code>, and `--overwrite`, which defaults to `true`.

```text
usage: csdl-to-json.py [-h] --input INPUT --output OUTPUT [--config CONFIG]
                       [--overwrite OVERWRITE]

A tool used to convert Redfish CSDL files to Redfish JSON Schema files

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT, -I INPUT
                        The directory containing the CSDL files to convert
  --output OUTPUT, -O OUTPUT
                        The directory to write the converted JSON files
  --config CONFIG, -C CONFIG
                        The configuration file containing definitions for
                        various links and user strings
  --overwrite OVERWRITE, -W OVERWRITE
                        Overwrite the versioned files in the output directory
                        if they already exist (default is True)
```

## Example

To run the converter, navigate to the `Redfish-Tools/csdl-to-json-convertor` directory and use Python to run `csdl-to-json.py`:

```bash
$ python3 csdl-to-json.py --input ../../Redfish/metadata --output ../../Redfish/json-schema/ --config dmtf-config.json
```

This example converts the CSDL metadata files in the `Redfish/metadata` input directory to JSON Schema files in the <code translate="no">Redfish/json&#8209;schema</code> output directory. To configure the generated JSON Schema files, the converter reads the configuration keys in the <code translate="no">dmtf&#8209;config.json</code> configuration file.

## Processing

* [Assumptions](#assumptions)
* [Details](#details)

### Assumptions

The converter makes these assumptions about the format of the Redfish CSDL files:

* Each file that defines a resource follows the Redfish model for inheritance by copy.
    Other than the base `Resource` definition, each resource definition is contained in one file.
* Any referenced external namespaces have proper `Include` statements at the top of each CSDL file.
* All annotations have their expected facets filled.
    For example, the `OData.Description` annotation must use the `String=` facet.
* All namespaces follow the Redfish-defined format where a namespace is either unversioned or in the form <code translate="no"><var>NAME</var>.v<var>MAJOR&#8209;VERSION</var>&lowbar;<var>MINOR&#8209;VERSION</var>&lowbar;<var>ERRATA&#8209;VERSION</var></code>.

    > **Note:** References to another CSDL file assume that its JSON Schema file is in the same directory.

### Details

To process CSDL files, the converter:

1. Locates the `Resource_v1.xml` schema to cache base definition properties that all resources use.
    If the file is not in the input directory, the tool accesses it in the remote location.
1. Loops on all XML files in the input directory. For the definitions in every versioned and unversioned namespace in each XML file, the converter generates corresponding definitions in JSON Schema file or files.
    
    [Table 2](#table-2--mapping-of-csdl-definitions-to-json-definitions "#table-2--mapping-of-csdl-definitions-to-json-definitions") shows the mapping of CSDL file definitions to JSON file definitions.

    <table id="table-2--mapping-of-csdl-to-json-data" width="100%" id="table-mapping-of-csdl-definitions-to-json-definitions">
      <caption><b>Table 2 &mdash; Mapping of CSDL definitions to JSON definitions</b></caption>
      <col width="4%">
      <col width="48%">
      <col width="48%">
      <thead>
        <tr>
          <th align="left" valign="top" colspan="2">CSDL file</th>
          <th align="left" valign="top">JSON file</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th align="left" valign="top" colspan="2"><code>EntityType</code>&nbsp;and&nbsp;<code>ComplexType</code> definitions that are in</th>
          <th align="left" valign="top">Tool generates these files with corresponding definitions</th>
        </tr>
        <tr>
          <td/>
          <td align="left" valign="top">Unversioned namespace and marked as abstract</td>
          <td align="left" valign="top">Unversioned JSON Schema file, which uses <code>anyOf</code> statement to point to all versioned definitions</td>
        </tr>
        <tr>
          <td/>
          <td align="left" valign="top">Unversioned&nbsp;namespace&nbsp;and&nbsp;not&nbsp;marked&nbsp;as&nbsp;abstract</td>
          <td align="left" valign="top">Unversioned JSON Schema file</td>
        </tr>
        <tr>
          <td/>
          <td align="left" valign="top">Versioned namespace</td>
          <td align="left" valign="top">That JSON Schema file version and newer JSON Schema file versions</td>
        </tr>
        <tr>
          <th align="left" valign="top" colspan="2"><code>Action</code> definitions that are in</th>
          <th align="left" valign="top">Tool generates these files with corresponding definitions</th>
        </tr>
        <tr>
          <td/>
          <td align="left" valign="top">Unversioned namespace</td>
          <td align="left" valign="top">All JSON Schema file versions</td>
        </tr>
        <tr>
          <td/>
          <td align="left" valign="top">Versioned namespace</td>
          <td align="left" valign="top">That JSON Schema file version and newer JSON Schema file versions</td>
        </tr>
        <tr>
          <th align="left" valign="top" colspan="2"><code>EnumType</code> and <code>TypeDefinition</code> definitions that are in</th>
          <th align="left" valign="top">Tool generates these files with corresponding definitions</th>
        </tr>
        <tr>
          <td/>
          <td align="left" valign="top">Unversioned namespace</td>
          <td align="left" valign="top">Unversioned JSON Schema file</td>
        </tr>
        <tr>
          <td/>
          <td align="left" valign="top">Versioned namespace</td>
          <td align="left" valign="top">That JSON Schema file version and newer JSON Schema file versions</td>
        </tr>
      </tbody>
    </table>
