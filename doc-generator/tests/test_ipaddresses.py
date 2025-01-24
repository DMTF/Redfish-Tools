# Copyright Notice:
# Copyright 2018-2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md

"""
File: test_ipaddresses.py

"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'referenced_objects')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'schema_link_replacements': {},
    'wants_common_objects': True,
    'profile': {},
    'escape_chars': [],
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_ipaddresses (mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'
    # The following is needed only if we want to inspect the output:
    config['intro_content'] = "# Common Objects\n\n[insert_common_objects]\n"

    input_dir = os.path.abspath(os.path.join(testcase_path, 'ipaddresses'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    common_properties = docGen.generator.common_properties

    assert 'http://redfish.dmtf.org/schemas/v1/IPAddresses.json#/definitions/IPv4Address' in common_properties
    assert 'http://redfish.dmtf.org/schemas/v1/IPAddresses.json#/definitions/IPv6Address' in common_properties
