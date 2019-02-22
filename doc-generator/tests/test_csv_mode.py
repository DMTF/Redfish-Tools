# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_csv_mode.py

Brief: Tests for CSV output.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'csv_mode')

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
    'output_format': 'csv',
}

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_csv_basic_output(mockRequest):
    """ This initial test doesn't do much; really it's just here to make sure we don't introduce
    errors from unimplemented functionality """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'input'))
    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    lines = output.split('\n')

    assert lines[0].startswith('Schema Name')
    assert len(lines) == 11
