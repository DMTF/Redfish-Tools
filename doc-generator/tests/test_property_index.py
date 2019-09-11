# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_property_index.py

Brief: Tests for Property Index mode.

"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'property_index')

property_index_config = {
    'ExcludedProperties': [
    "description",
    "Id",
    "@odata.context",
    "@odata.type",
    "@odata.id",
    "@odata.etag",
    "*@odata.count",
    ],
    'DescriptionOverrides': {
    },
    }

base_config = {
    'output_content': 'property_index',
    'output_format': 'markdown',
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'uri_replacements': {},
    'property_index_config': property_index_config,
    'supplemental': {},

    'profile': {},
    'escape_chars': [],
}

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_property_index_config_out(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'

    # A selection of what we expect to find in the DescriptionOverrides *output* by the tool:
    expected = {
        "FanName": [
            {
                "schemas": [
                    "Thermal/Fans"
                ],
                "description": "Name of the fan.",
                "knownException": False,
                "type": "string"
            },
            {
                "schemas": [
                    "Thermal/Temperatures"
                ],
                "description": "This property was inserted to have an example of a variant description for the same type.",
                "knownException": False,
                "type": "string"
            }

        ],
        "LowerThresholdFatal": [
            {
                "schemas": [
                    "Thermal/Fans"
                ],
                "description": "Below normal range and is fatal.",
                "knownException": False,
                "type": "integer"
            },
            {
                "schemas": [
                    "Thermal/Temperatures"
                ],
                "description": "Below normal range and is fatal.",
                "knownException": False,
                "type": "number"
            }
        ],
        "RelatedItem": [
            {
                "type": "array",
                "schemas": [
                    "Thermal/Temperatures"
                ],
                "knownException": False,
                "description": "Describes the areas or devices to which this temperature measurement applies."
            },
            {
                "type": "array",
                "schemas": [
                    "Thermal/Fans"
                ],
                "knownException": False,
                "description": "The ID(s) of the resources serviced with this fan."
            }
        ],
    }



    dirpath = os.path.abspath(os.path.join(testcase_path, 'thermal_plus'))
    input_dir = os.path.join(dirpath, 'input')

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # Get the property indexer and compare the config output it would produce with what we expect:
    updated_config = docGen.generator.generate_updated_config()

    # Checking specific cases here.
    out = updated_config['DescriptionOverrides']
    assert out.get('LowerThresholdFatal') == expected['LowerThresholdFatal'], "Type mismatch not detected for LowerThresholdFatal"
    assert out.get('RelatedItem') == expected['RelatedItem'], "Description mismatch not detected for RelatedItem"
    assert out.get('FanName') == expected['FanName'], "Description mismatch not detected for FanName"


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_property_index_config_overrides(mockRequest):
    """ Test that overrides are applied. """

    config = copy.deepcopy(base_config)
    config['output_format'] = 'markdown'

    override_desc = "This is an override description for NetDevFuncCapbilities, a string."

    config['property_index_config']['DescriptionOverrides'] = {
        "NetDevFuncCapabilities": [
        {
        "overrideDescription": override_desc,
        "type": "array",
        "globalOverride": True
        },
        ],
        }

    dirpath = os.path.abspath(os.path.join(testcase_path, 'general'))
    input_dir = os.path.join(dirpath, 'input')

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    lines = [x for x in output.split('\n') if '*NetDevFuncCapabilities*' in x]

    assert len(lines) and len([x for x in lines if override_desc in x]) == len(lines)

    updated_config = docGen.generator.generate_updated_config()
