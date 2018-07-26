# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_referenced_objects.py

Brief: Tests for correct generation of the "Referenced Objects" (a.k.a. "Common Properties") documentation.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'referenced_objects')

base_config = {
    'expand_defs_from_non_output_schemas': False,
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'uri_replacements': {},
    'wants_common_objects': True,
    'profile': {},
    'escape_chars': [],
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_gather(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'markdown'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'network_sample'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    common_properties = docGen.generator.common_properties

    assert 'http://redfish.dmtf.org/schemas/v1/Resource.json#/definitions/Oem' in common_properties
    assert 'http://redfish.dmtf.org/schemas/v1/Resource.json#/definitions/Status' in common_properties
    assert len(common_properties) == 2


# @patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
# def test_gather_html(mockRequest):

#     config = copy.deepcopy(base_config)
#     config['output_format'] = 'html'
#     # The following is needed only if we want to inspect the output:
#     config['supplemental'] = {'Introduction': "# Common Objects\n\n[insert_common_objects]\n"},

#     input_dir = os.path.abspath(os.path.join(testcase_path, 'network_sample'))

#     config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
#     config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

#     docGen = DocGenerator([ input_dir ], '/dev/null', config)
#     output = docGen.generate_docs()
#     common_properties = docGen.generator.common_properties

#     assert 'http://redfish.dmtf.org/schemas/v1/Resource.json#/definitions/Oem' in common_properties
#     assert 'http://redfish.dmtf.org/schemas/v1/Resource.json#/definitions/Status' in common_properties
#     assert len(common_properties) == 2
