# Copyright Notice:
# Copyright 2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_local_python.py

Brief: test(s) for detection and use of "locale" specified in config -- on strings emedded in doc generator code.
"""

import os
import os.path
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'generate_docs_cases', 'general', 'input')

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

    'output_format': 'slate',
}

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_locale_default(mockRequest):
    """ Verify a few expected strings are output in the default way when no locale is specified.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(testcase_path)

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = {input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)

    files_to_process = docGen.get_files(docGen.import_from)
    output = docGen.generate_docs()

    expected_strings = ['*read-only*', '*read-write<br>(null)*',
                            '*For the possible property values, see WWNSource in Property details.*']

    for x in expected_strings:
        assert x in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_locale_en(mockRequest):
    """ Verify that our same test strings are output the same way when "en" is specified explicitly.
    """

    config = copy.deepcopy(base_config)
    config['locale'] = 'en'
    input_dir = os.path.abspath(testcase_path)

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = {input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)

    files_to_process = docGen.get_files(docGen.import_from)
    output = docGen.generate_docs()

    expected_strings = ['*read-only*', '*read-write<br>(null)*',
                            '*For the possible property values, see WWNSource in Property details.*']

    for x in expected_strings:
        assert x in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_locale_TEST(mockRequest):
    """ Verify that the test strings are output correctly when TEST is specified for the locale.
    """

    config = copy.deepcopy(base_config)
    config['locale'] = 'TEST'
    input_dir = os.path.abspath(testcase_path)

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = {input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)

    files_to_process = docGen.get_files(docGen.import_from)
    output = docGen.generate_docs()

    expected_strings = ['*READ-ONLY*', '*READ-WRITE<br>(NULL)*',
                            '*FOR THE POSSIBLE PROPERTY VALUES, SEE WWNSource IN PROPERTY DETAILS.*']

    for x in expected_strings:
        assert x in output
