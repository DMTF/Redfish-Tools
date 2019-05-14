# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_version_deprecated.py

Brief: test(s) for correct detection of "Version Deprecated".
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator
from .discrepancy_list import DiscrepancyList

testcase_path = os.path.join('tests', 'samples')

base_config = {
    'expand_defs_from_non_output_schemas': False,
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'uri_replacements': {},

    'profile': {},
    'escape_chars': [],

    'output_format': 'markdown',
}

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_version_deprecated_metadata(mockRequest):
    """ Verify metadata contains expected version_deprecated info.
    Note that there is an additional step, after generating this metadata, for generating metadata
    within property data ... so possibly this test should be replaced.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'version_deprecated', 'Event'))

    # This is a partial list of versions that should be detected.
    expected_versions = {
        'Events': {},
        'definitions': {
        'Event': {
            'Context': {},
            },
        'EventRecord': {
            'Context': { 'version_deprecated': '1.2.0' },
            'MemberId': {},
            },
        'EventType': {},  # Event type was "deprecated" in 1.3 and moved to the unversioned schema
        }
        }

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    meta = docGen.property_data['redfish.dmtf.org/schemas/v1/Event.json']['doc_generator_meta']

    discrepancies = DiscrepancyList()
    for name, data in expected_versions.items():
        if name == 'version': continue
        _version_compare(meta, name, data, discrepancies, [])

    assert [] == discrepancies


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_version_deprecated_enum_metadata(mockRequest):
    """ Verify metadata contains expected version_deprecated info for enum properties.
    Note that there is an additional step, after generating this metadata, for generating metadata
    within property data ... so possibly this test should be replaced.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'version_deprecated', 'Chassis'))

    # This is a partial list of versions that should be detected.
    expected_versions = {
        'definitions': {
            'IndicatorLED': {
                'enum': {
                    "Lit": { },
                    "Unknown": { 'version_deprecated': '1.5.0' },
                    },
                },
            }
        }

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    meta = docGen.property_data['redfish.dmtf.org/schemas/v1/Chassis.json']['doc_generator_meta']

    discrepancies = DiscrepancyList()
    for name, data in expected_versions.items():
        if name == 'version': continue
        _version_compare(meta, name, data, discrepancies, [])

    assert [] == discrepancies


def _version_compare(meta, name, data, discrepancies, context):

    context = copy.copy(context)
    context.append(name)

    key_meta = meta.get(name)
    if key_meta is None:
        discrepancies.append(' > '.join(context) + ' not found in metadata')

    else:
        if data.get('version_deprecated', '(none)') != key_meta.get('version_deprecated', '(none)'):
            discrepancies.append(' > '.join(context) + ' version_deprecated is "' + key_meta.get('version_deprecated', '(none)') + '", expected "'
                                 + data.get('version_deprecated', '(none)') + '"')

        for childname, childdata in data.items():
            if childname == 'version_deprecated': continue
            _version_compare(key_meta, childname, childdata, discrepancies, context)


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_version_deprecated_output_Event(mockRequest):
    """ Verify markdown output contains expected version_deprecated info.
    The Event example gave us some distinct scenarios.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'version_deprecated', 'Event'))

    expected_version_strings = ['| **Events** [ { |', '| **Links** { |',  # string to match property without version
                                '**Context** *(deprecated v1.1)* |',
                                '**EventType** *(deprecated v1.3)* |',
                                ]


    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    discrepancies = DiscrepancyList()

    for expected in expected_version_strings:
        if expected not in output:
            discrepancies.append('"' + expected + '" not found')

    assert [] == discrepancies


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_version_deprecated_output_Chassis(mockRequest):
    """ Verify markdown output contains expected version_deprecated info.
    The Event example gave us some distinct scenarios.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'version_deprecated', 'Chassis'))

    expected_version_strings = ['| Lit |', # string to match property without version
                                'Unknown *(deprecated v1.5)* |',
                                ]


    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    discrepancies = DiscrepancyList()

    for expected in expected_version_strings:
        if expected not in output:
            discrepancies.append('"' + expected + '" not found')

    assert [] == discrepancies
