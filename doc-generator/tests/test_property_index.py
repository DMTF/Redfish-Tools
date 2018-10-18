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
    'expand_defs_from_non_output_schemas': False,
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

@pytest.mark.xfail       # This set actually doesn't output overrides, since list handling was fixed. Need a different sample.
@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_property_index_config_out(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'

    expected_config_out = {
    "ExcludedProperties": [
        "description",
        "Id",
        "@odata.context",
        "@odata.type",
        "@odata.id",
        "@odata.etag",
        "*@odata.count"
    ],
    "DescriptionOverrides": {
        "NetDevFuncCapabilities": [
            {
                "knownException": False,
                "description": "Capabilities of this network device function.",
                "schemas": [
                    "NetworkDeviceFunction"
                ],
                "type": "array"
            },
            {
                "knownException": False,
                "description": "Capabilities of this network device function.",
                "schemas": [
                    "NetworkDeviceFunction/NetDevFuncCapabilities"
                ],
                "type": "string"
            }
        ],
        "SupportedEthernetCapabilities": [
            {
                "knownException": False,
                "description": "The set of Ethernet capabilities that this port supports.",
                "schemas": [
                    "NetworkPort"
                ],
                "type": "array"
            },
            {
                "knownException": False,
                "description": "The set of Ethernet capabilities that this port supports.",
                "schemas": [
                    "NetworkPort/SupportedEthernetCapabilities"
                ],
                "type": "string"
            }
        ]
        }
    }


    dirpath = os.path.abspath(os.path.join(testcase_path, 'general'))
    input_dir = os.path.join(dirpath, 'input')

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # Get the property indexer and compare the config output it would produce with what we expect:
    updated_config = docGen.generator.generate_updated_config()
    assert updated_config == expected_config_out


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
