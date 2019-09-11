# Copyright Notice:
# Copyright 2019 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_pattern_properties.py

Brief: Some properties are defined as type "object" with no properties, but with "patternProperties"
defined. These tests check for correct output, using the MessageRegistry schema.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'pattern_properties')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'uri_replacements': {},

    'profile': {},
    'escape_chars': [],
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_html_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'

    dirpath = os.path.abspath(os.path.join(testcase_path));
    input_dir = os.path.join(dirpath, 'input')

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    expected_output_main = open(os.path.join(dirpath, 'expected_output', 'MessagesProperty.html')).read().strip()
    expected_output_details = open(os.path.join(dirpath, 'expected_output', 'MessagesPropertyDetails.html')).read().strip()

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    pattern1 = r'[A-Za-z0-9]+'
    pattern2 = r'^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\.[a-zA-Z_][a-zA-Z0-9_.]+$'

    # These are redundant, in that the third assertion would always fail if either of the first two fails.
    # The first is more focused, though.
    assert pattern1 in output, "Expected pattern " + pattern1 + " not found in output"
    assert pattern2 in output, "Expected pattern " + pattern2 + " not in output. Was its backslash-escape changed by markdown-to-html conversion?"
    assert expected_output_main in output
    assert expected_output_details in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_markdown_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'markdown'

    dirpath = os.path.abspath(os.path.join(testcase_path));
    input_dir = os.path.join(dirpath, 'input')

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    expected_output_main = open(os.path.join(dirpath, 'expected_output', 'MessagesProperty.md')).read().strip()
    expected_output_details = open(os.path.join(dirpath, 'expected_output', 'MessagesPropertyDetails.md')).read().strip()

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    pattern1 = r'\[A\-Za\-z0\-9\]\+'
    pattern2 = r'^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\.[a-zA-Z_][a-zA-Z0-9_.]+$'
    pattern3 = r'^\(\[a\-zA\-Z\_\]\[a\-zA\-Z0\-9\_\]\*\)?@\(odata\|Redfish\|Message\)\\\.\[a\-zA\-Z\_\]\[a\-zA\-Z0\-9\_\.\]\+$'

    # These are redundant, in that the third assertion would always fail if either of the first two fails.
    # The first is more focused, though.
    assert pattern1 in output, "Expected pattern " + pattern1 + " not found in output"
    assert pattern3 in output, "Expected pattern " + pattern3 + " not in output. Was " + pattern2 + " escaped properly?"

    assert expected_output_main in output
    assert expected_output_details in output
