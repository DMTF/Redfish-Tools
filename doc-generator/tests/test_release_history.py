# Copyright Notice:
# Copyright 2019 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_release_history.py

Brief: test(s) for correct generation of "Release History" information from "release" annotations.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

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
# The test sample is incomplete, so we will be warned of unavailable resources (odata, Resource, and more).
@pytest.mark.filterwarnings("ignore:Unable to find data")
@pytest.mark.filterwarnings("ignore:Unable to read")
@pytest.mark.filterwarnings("ignore:Unable to retrieve")
def test_release_history(mockRequest):
    """ TODO
    """

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'
    input_dir = os.path.abspath(os.path.join(testcase_path, 'release_history', 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    assert False
