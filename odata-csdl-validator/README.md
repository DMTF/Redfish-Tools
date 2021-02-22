[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="center">
  <img src="http://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2016-2021 DMTF. All rights reserved.

[[Redfish-Tools README]](../README.md#redfish-tools "../README.md#redfish-tools")

# OData CSDL validator

The OData CSDL validator, [`odata_validator.py`](odata_validator.py#L1 "odata_validator.py#L1"), is a Python tool that validates that the metadata in *OData CSDL XML* files and all referenced files conforms to [OData v4.0](http://docs.oasis-open.org/odata/odata-csdl-xml/v4.01/odata-csdl-xml-v4.01.html "http://docs.oasis-open.org/odata/odata-csdl-xml/v4.01/odata-csdl-xml-v4.01.html").

> **Note:** OData CSDL XML is a full representation of the OData Common Schema Definition Language (CSDL) in the [Extensible Markup Language (XML) 1.1 (Second Edition)](https://www.w3.org/TR/2006/REC-xml11-20060816/ "https://www.w3.org/TR/2006/REC-xml11-20060816/").

## Contents

* [Installation](#installation)
* [Usage](#usage)
* [Examples](#examples)
* [Processing](#processing)

## Installation

1. Clone the `Redfish-Tools` repository:

   ```zsh
   % git clone git@github.com:DMTF/Redfish-Tools.git
   % git remote add upstream git@github.com:DMTF/Redfish-Tools.git
   ```
1. [Download and install Python](https://www.python.org/downloads/ "https://www.python.org/downloads/") on the machine from which you will run this tool.

## Usage

```
usage: odata_validator.py [-h] MetaData

OData Validation Tool

positional arguments:
  MetaData    Path to the metadata to be parsed, could be a url (start with
              http), file or folder

optional arguments:
  -h, --help  show this help message and exit
```

## Examples

To run the validator, navigate to the `Redfish-Tools/odata-csdl-validator` directory and use Python to run `odata_validator.py`:

```zsh
% cd Redfish-Tools/odata-csdl-validator
% python3 odata_validator.py METADATA
```

The validator accepts the `METADATA` command-line argument in one of these formats:

* [Local path to an OData CSDL XML file](#local-path-to-an-odata-csdl-xml-file)
* [Local path to directory of OData CSDL XML files](#local-path-to-directory-of-odata-csdl-xml-files)
* [URL of an OData CSDL XML file](#url-of-an-odata-csdl-xml-file)

### Local path to an OData CSDL XML file

This example command validates that the metadata in the `test_metadata/ServiceRoot.xml` file conforms to OData v4.0:

```zsh
% cd Redfish-Tools/odata-csdl-validator
% python3 odata_validator.py ../../Redfish/test_metadata/ServiceRoot.xml
```

### Local path to directory of OData CSDL XML files

This example command validates that the metadata in the files in the `test_metadata` directory conforms to OData v4.0:
         
```zsh
% cd Redfish-Tools/odata-csdl-validator
% python3 odata_validator.py ../../Redfish/test_metadata
```

### URL of an OData CSDL XML file

This example command validates that the metadata in the `http://redfish.dmtf.org/schemas/v1/ServiceRoot.xml` file conforms to OData v4.0:
         
```zsh
$ cd Redfish-Tools/odata-csdl-validator
% python3 odata_validator.py http://redfish.dmtf.org/schemas/v1/ServiceRoot.xml
```

## Processing

The validator validates that the metadata in the specified OData CSDL XML file or files and all referenced OData CSDL XML files conforms to [OData v4.0](http://docs.oasis-open.org/odata/odata-csdl-xml/v4.01/odata-csdl-xml-v4.01.html "http://docs.oasis-open.org/odata/odata-csdl-xml/v4.01/odata-csdl-xml-v4.01.html"). 

If the validator finds an error, it prints the path to the metadata file that contains the error with a simple explanation of the error.

Example error message:

```text
MetaData:http://redfish.dmtf.org/schemas/v1/ServiceRoot.xml->DataServices->Schema:ServiceRoot->EntityType:ServiceRoot->Resource.1.0.0.Resource is not a valid QualifiedName
```
