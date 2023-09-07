# Copyright Notice:
# Copyright 2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md

"""
File: test_actions_with_versions.py

Brief: Test for correct output of version information in Action details.
"""

import os
import copy
import re
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'actions_with_versions')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'excluded_pattern_props': [r'^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\.[a-zA-Z_][a-zA-Z0-9_.]+$'],
    'schema_link_replacements': {},
    'wants_common_objects': False,
    'profile': {},
    'escape_chars': [],
    'output_format': 'slate',
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_action_has_version_added_markdown(mockRequest):
    """ This is the initial example, from the Processor schema """
    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'processor'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    expected_output = '''
##### Reset *(v1.6+)*
'''

    assert expected_output in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_action_has_version_added_html(mockRequest):
    """ This is the initial example, from the Processor schema """
    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'processor'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    config['output_format'] = 'html'
    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    assert re.search('<h4[^>]*>Reset <i>\\(v1\\.6\\+\\)</i></h4>', output)
