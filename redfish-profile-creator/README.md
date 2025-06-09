# Redfish Profile Creator

Copyright 2025 DMTF. All rights reserved.

## About

The OData Validator is a Python3 tool which crawls through OData formatted CSDL, parses it, and validates that it conforms to the [OData V4.0 CSDL Specification](http://docs.oasis-open.org/odata/odata/v4.0/odata-v4.0-part3-csdl.html).

## Usage

## CSV Input Format

Each entry in the CSV file should be seperated by commas in the following order

| Schema | UseCase | Property Name | ReadRequirement | WriteRequirement | Conditional | Purpose | 
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |

example:

```
Chassis,SampleCase,Id,mandatory,None,False,Identifies this Object
Chassis,None,Power.Id
Chassis,None,Power.Name
```

| Parameter | Type | Optional | Usage | 
| :--- | :--- | :--- | :---
| Schema | str | no | True or False
| UseCase | str | no | True or False
| Property | str | no | True or False
| Name | str | no | True or False
| ReadRequirement | str | no | True or False
| WriteRequirement | str | no | True or False
| Conditional | str | no | True or False
| Purpose | str | no | True or False