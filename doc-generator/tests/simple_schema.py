# Copyright Notice:
# Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/LICENSE.md

"""
File: simple_schema.py

Brief: Defines a single variable, simple_schema, with a simplified schema for the SchemaTraverser tests
"""

simple_schema = {
    "Thermal": {
        "$schema": "http://redfish.dmtf.org/schemas/v1/redfish-schema.v1_1_0.json",
        "title": "#Thermal.v1_1_0.Thermal",
        "$ref": "#/definitions/Thermal",
        "definitions": {
            "Fan": {
                "type": "object",
                "properties": {
                    "Oem": {

                        "$ref": "http://redfish.dmtf.org/schemas/v1/Resource.json#/definitions/Oem",
                        "description": "This is the manufacturer/provider specific extension moniker used to divide the Oem object into sections.",
                        "longDescription": "The value of this string shall be of the format for the reserved word *Oem*."

                    },
                    "FanName": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "readonly": True,
                        "description": "Name of the fan",
                        "longDescription": "The value of this property shall be the name of the fan."
                    },
                    "Status": {
                        "$ref": "http://redfish.dmtf.org/schemas/v1/Resource.json#/definitions/Status"
                    },
                },
                "description": "This is the base type for addressable members of an array.",
                "longDescription": "Array members can be referenced using the value returned in the @odata.id property which may or may not be a dereferenceable URL. The @odata.id of this entity shall be the location of this element within an Item.",
            },
        },
    },
    "Resource": {
        "$schema": "http://redfish.dmtf.org/schemas/v1/redfish-schema.v1_1_0.json",
        "title": "#Resource.v1_1_0",
        "definitions": {
            "Oem": {
                "type": "object",
                "description": "Oem extension object.",
                "longDescription": "This object represents the Oem properties.  All values for resources described by this schema shall comply to the requirements as described in the Redfish specification.",
            },
            "Health": {
                "type": "string",
                "enumDescriptions": {
                    "Critical": "A critical condition exists that requires immediate attention",
                    "Warning": "A condition exists that requires attention",
                    "OK": "Normal"
                },
                "enum": [
                    "OK",
                    "Warning",
                    "Critical"
                ]
            }
        },
        "title": "#Resource",
        "$schema": "http://redfish.dmtf.org/schemas/v1/redfish-schema.v1_1_0.json",
    }
}
