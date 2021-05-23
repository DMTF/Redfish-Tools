# Copyright Notice:
# Copyright 2021 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_fragments.py

Brief: Tests that exercise doc generation for "fragments."
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'fragments')
fragment_path = os.path.join(testcase_path, 'CommonPropertySchema.json#/definitions/CommonProperties/properties');

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
}

base_config['intro_content'] = "# FRAGMENT FOLLOWS\n\n#include_fragment " + fragment_path + "\n"


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_html_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'

    input_dir = os.path.join(testcase_path, 'json-schema')

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    expected_output = open(os.path.join(testcase_path, 'expected_output.html')).read()

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    assert expected_output in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_slate_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'slate'

    input_dir = os.path.join(testcase_path, 'json-schema')

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    expected_output = open(os.path.join(testcase_path, 'expected_slate_output.md')).read()

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    assert expected_output in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_markdown_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'markdown'

    input_dir = os.path.join(testcase_path, 'json-schema')

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    expected_output = open(os.path.join(testcase_path, 'expected_output.md')).read()

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    assert expected_output in output
