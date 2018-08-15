# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_openapi.py

Brief: Tests for correct handling of OpenAPI features (URIs)
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'openapi')

base_config = {
    'expand_defs_from_non_output_schemas': False,
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'uri_replacements': {},
    'wants_common_objects': False,
    'profile': {},
    'escape_chars': [],
    'output_format': 'html'
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_uri_capture(mockRequest):

    config = copy.deepcopy(base_config)

    input_dir = os.path.abspath(os.path.join(testcase_path, 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    event_properties = docGen.property_data.get('redfish.dmtf.org/schemas/v1/Event.json')
    logentry_properties = docGen.property_data.get('redfish.dmtf.org/schemas/v1/LogEntry.json')
    logentrycollection_properties = docGen.property_data.get('redfish.dmtf.org/schemas/v1/LogEntryCollection.json')

    assert event_properties['uris'] == []
    assert sorted(logentry_properties['uris']) == sorted([
        "/redfish/v1/Managers/{ManagerId}/LogServices/{LogServiceId}/Entries/{LogEntryId}",
        "/redfish/v1/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries/{LogEntryId}",
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries/{LogEntryId}"
        ])
    assert sorted(logentrycollection_properties['uris']) == sorted([
        "/redfish/v1/Managers/{ManagerId}/LogServices/{LogServiceId}/Entries",
        "/redfish/v1/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries",
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries"
        ])


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_collection_uris_captured_when_collections_excluded (mockRequest):

    config = copy.deepcopy(base_config)
    config['excluded_schemas_by_match'] = [ 'Collection' ]

    input_dir = os.path.abspath(os.path.join(testcase_path, 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    logentrycollection_properties = docGen.property_data.get('redfish.dmtf.org/schemas/v1/LogEntryCollection.json')

    assert sorted(logentrycollection_properties['uris']) == sorted([
        "/redfish/v1/Managers/{ManagerId}/LogServices/{LogServiceId}/Entries",
        "/redfish/v1/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries",
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries"
        ])
