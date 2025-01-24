# Copyright Notice:
# Copyright 2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md

"""
File: test_readwrite_links.py

Brief: test(s) for proper detection of read/write properties on links
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator


testcase_path = os.path.join('tests', 'samples')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'schema_link_replacements': {},

    'profile': {},
    'escape_chars': [],

    'output_format': 'slate',
}

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_readwrite_links(mockRequest):
    """ Verify output contains expected read/write info. As it happens, all the links
        to Facility resources in this document should show as read-write."""

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'readwrite_links', 'Facility'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    assert '*read-write* | Link to another Facility resource' in output
    assert '*read-only* | Link to another Facility resource' not in output
