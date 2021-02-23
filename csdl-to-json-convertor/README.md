[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="center">
  <img src="http://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2017-2021 DMTF. All rights reserved.

[[Redfish-Tools README]](../README.md#redfish-tools "../README.md#redfish-tools")

# CSDL-to-JSON converter

The CSDL-to-JSON converter, [`csdl-to-json.py`](csdl-to-json.py#L1 "csdl-to-json.py#L1"), is a Python tool that converts Redfish [Common Schema Definition Language (CSDL)](http://docs.oasis-open.org/odata/odata/v4.0/odata-v4.0-part3-csdl.html "http://docs.oasis-open.org/odata/odata/v4.0/odata-v4.0-part3-csdl.html") files to Redfish [JSON Schema](https://json-schema.org/ "https://json-schema.org/") files.

## Contents

* [Installation](#installation "#installation")
* [Configuration](#configuration "#configuration")
* [Usage](#usage "#usage")
* [Example](#example "#example")
* [Processing](#processing "#processing")

## Installation

1. Clone the `Redfish-Tools` repository:

   ```zsh
   % git clone git@github.com:DMTF/Redfish-Tools.git
   % git remote add upstream git@github.com:DMTF/Redfish-Tools.git
   ```
1. [Download and install Python](https://www.python.org/downloads/ "https://www.python.org/downloads/") on the machine from which you will run the tools.

## Configuration

To configure the generated JSON Schema files, define configuration keys in a JSON configuration file and use the <a href="#usage" title="#usage"><code>--config</code> command&#8209;line argument</a> to specify the configuration file.

<!-- If you omit either any keys in the specified configuration file or the <code>--config</code> command-line argument, the converter uses the keys in the default <a href="dmtf-config.json#L1" title="dmtf-config.json#L1"><code>dmtf-config.json</code></a> configuration file. -->

The <a href="dmtf-config.json#L1" title="dmtf-config.json#L1"><code>dmtf-config.json</code></a> configuration file contains the default configuration key values.

### Sample configuration file

<a href="dmtf-config.json#L1" title="dmtf-config.json#L1"><code>dmtf-config.json</code></a>

### Configuration keys

<dl>
   <dt>
      <h4><code>Copyright</code></h4>
   </dt>
   <dd>String. Copyright string to include in the generated JSON Schema files.</dd>
   <dt>
      <h4><code>RedfishSchema</code></h4>
   </dt>
   <dd>String. Location of Redfish Schema files.</dd>
   <dt>
      <h4><code>ODataSchema</code></h4>
   </dt>
   <dd>String. Location of OData Schema files.</dd>
   <dt>
      <h4><code>Location</code></h4>
   </dt>
   <dd>String. Folder for the generated JSON Schema files.</dd>
   <dt>
      <h4><code>ResourceLocation</code></h4>
   </dt>
   <dd>String. Location of Redfish resources.</dd>
   <dt>
      <h4><code>DoNotWrite</code></h4>
   </dt>
   <dd>Array of strings. One or more files to exclude from the generated JSON Schema files.</dd>
</dl>

## Usage

```text
usage: csdl-to-json.py [-h] --input INPUT --output OUTPUT [--config CONFIG]
                       [--overwrite OVERWRITE]

A tool used to convert Redfish CSDL files to Redfish JSON Schema files

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT, -I INPUT
                        The folder containing the CSDL files to convert
  --output OUTPUT, -O OUTPUT
                        The folder to write the converted JSON files
  --config CONFIG, -C CONFIG
                        The configuration file containing definitions for
                        various links and user strings
  --overwrite OVERWRITE, -W OVERWRITE
                        Overwrite the versioned files in the output directory
                        if they already exist (default is True)
```

## Example

To run the converter, navigate to the `Redfish-Tools/csdl-to-json-convertor` directory and use Python to run `csdl-to-json.py`:

```zsh
% cd Redfish-Tools/csdl-to-json-convertor
% python3 csdl-to-json.py --input ../../Redfish/metadata --output ../../Redfish/json-schema/ --config dmtf-config.json
```

This example command converts the CSDL metadata files in the `Redfish/metadata` input directory to JSON Schema files in the `/Redfish/json-schema` output directory. The converter reads the configuration keys in the [`dmtf-config.json`](dmtf-config.json#L1 "dmtf-config.json#L1") configuration file to configure the generated JSON Schema files.

## Processing

* [Assumptions](#assumptions "#assumptions")
* [Details](#details "#details")

### Assumptions

The converter makes these assumptions about the format of the Redfish CSDL files:

* Each file that defines a resource follows the Redfish model for inheritance by copy.
    Other than the base `Resource` definition, each resource definition is contained in one file.
* Any referenced external namespaces have proper `Include` statements at the top of each CSDL file.
* All annotations have their expected facets filled.
    For example, the `OData.Description` annotation must use the `String=` facet.
* All namespaces follow the Redfish-defined format where a namespace is either unversioned or in the form, `<NAME>.v<MAJOR_VERSION>_<MINOR_VERSION>_<ERRATA_VERSION>`.

    > **Note:** References to another CSDL file assume that its JSON Schema file is in the same folder.

### Details

To process CSDL files, the converter:

1. Locates the `Resource_v1.xml` schema to cache base definition properties that all resources use.
    If the file is not in the input directory, the tool accesses it in the remote location.
1. Loops on all XML files in the input folder.
    For the following definitions in every versioned and unversioned namespace in each XML file, the converter generates corresponding JSON Schema file or files, as follows:

    <table width="100%">
      <col width="4%">
      <col width="48%">
      <col width="48%">
      <tbody>
        <tr>
          <th align="left" valign="top" colspan="3"><code>EntityType</code>&nbsp;and&nbsp;<code>ComplexType</code> definitions</th>
        </tr>
        <tr>
          <th rowspan="4"/>
          <th align="left" valign="top">That are in</th>
          <th align="left" valign="top">Tool converts definitions to</th>
        </tr>
        <tr>
          <td align="left" valign="top">Unversioned namespace and marked as abstract</td>
          <td align="left" valign="top">Unversioned JSON Schema file, which uses <code>anyOf</code> statement to point to all versioned definitions</td>
        </tr>
        <tr>
          <td align="left" valign="top">Unversioned&nbsp;namespace&nbsp;and&nbsp;not&nbsp;marked&nbsp;as&nbsp;abstract</td>
          <td align="left" valign="top">Unversioned JSON Schema file</td>
        </tr>
        <tr>
          <td align="left" valign="top">Versioned namespace</td>
          <td align="left" valign="top">That JSON Schema file version and newer JSON Schema file versions</td>
        </tr>
        <tr>
          <th align="left" valign="top" colspan="3"><code>Action</code> definitions</th>
        </tr>
        <tr>
          <th rowspan="3"/>
          <th align="left" valign="top">That are in</th>
          <th align="left" valign="top">Tool converts definitions to</th>
        </tr>
        <tr>
          <td align="left" valign="top">Unversioned namespace</td>
          <td align="left" valign="top">All versioned JSON Schema files</td>
        </tr>
        <tr>
          <td align="left" valign="top">Versioned namespace</td>
          <td align="left" valign="top">That JSON Schema file version and newer JSON Schema file versions</td>
        </tr>
        <tr>
          <th align="left" valign="top" colspan="3"><code>EnumType</code> and <code>TypeDefinition</code> definitions</th>
        </tr>
        <tr>
          <th rowspan="3"/>
          <th align="left" valign="top">That are in</th>
          <th align="left" valign="top">Tool converts definitions to</th>
        </tr>
        <tr>
          <td align="left" valign="top">Unversioned namespace</td>
          <td align="left" valign="top">Unversioned JSON Schema file</td>
        </tr>
        <tr>
          <td align="left" valign="top">Versioned namespace</td>
          <td align="left" valign="top">That JSON Schema file version and newer JSON Schema file versions</td>
        </tr>
      </tbody>
    </table>
