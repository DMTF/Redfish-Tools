# OData CSDL Validator

Copyright 2019-2022 DMTF. All rights reserved.

## About

The OData Validator is a Python3 tool which crawls through OData formatted CSDL, parses it, and validates that it conforms to the [OData V4.0 CSDL Specification](http://docs.oasis-open.org/odata/odata/v4.0/odata-v4.0-part3-csdl.html).

## Usage

Ensure that the machine running the tool has Python3 installed.

This tool requires one parameter which is used to navigate to the metadata files to validate.
The parameter can be in one of 3 formats.

1. The local path to a single CSDL file.  For example: `odata_validator.py test_metadata/ServiceRoot.xml`
2. The local path to a directory of CSDL files.  For example: `odata_validator.py test_metadata`
3. The URL of a CSDL file.  For example: `odata_validator.py http://redfish.dmtf.org/schemas/v1/ServiceRoot.xml`

The validator will parse and validate the files specified along with all referenced files.

If the tool finds an error, it will print to the screen a path starting from the metadata file the error is found in all the way to the error itsef along with a simple explanation of what the error is.

Example error:

```
MetaData:http://redfish.dmtf.org/schemas/v1/ServiceRoot.xml->DataServices->Sche
ma:ServiceRoot->EntityType:ServiceRoot->Resource.1.0.0.Resource is not a valid 
QualifiedName
```

## CSDL Rules Configuration

The tool also takes an optional `--config` argument to overlay additional CSDL rules found in the referenced JSON-formatted file.
The following terms can be specified:

| Name             | Description |
|:---              | :---        |
| `AppliesToOther` | Contains a dictionary where each name is the name of an annotation term and the value is an array of CSDL terms the annotation is allowed beyond the `AppliesTo` usage in the annotation's definition. |

Example rules configuration:

```
{
    "AppliesToOther": {
        "InsertRestrictions": [ "EntityType" ],
        "DeleteRestrictions": [ "EntityType" ],
        "UpdateRestrictions": [ "EntityType" ],
        "IsURL": [ "Parameter" ],
        "Unit": [ "Parameter" ]
    }
}
```
