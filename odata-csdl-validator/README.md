# OData Validator - Version 1.0

## About
The OData Validator is a python3 tool which crawls through OData formatted metadata, parses it and validates that it conforms to OData V4.0.

## Usage
Ensure that the machine running the tool has a python 3 install.

This tool requires one parameter which is used to navigate to the metadata file(s) to be validated.
The parameter can be in one of 3 formats.

1. The local path to a single XML metadata file. Example - odata\_validator.py test\_metadata/ServiceRoot.xml
2. The local path to a directory of XML metadata files. Example - odata\_validator.py test\_metadata
3. The URL of an XML metadata file. Example - odata\_validator.py http://redfish.dmtf.org/schemas/v1/ServiceRoot.xml

The validator will parse and validate the file(s) pointed to along with all referenced files.

If the tool finds an error, it will print to the screen a path starting from the metadata file the error is found in all the way to the error itsef along with a simple explanation of what the error is.

Example:
MetaData:http://redfish.dmtf.org/schemas/v1/ServiceRoot.xml->DataServices->Schema:ServiceRoot->EntityType:ServiceRoot->Resource.1.0.0.Resource is not a valid QualifiedName
