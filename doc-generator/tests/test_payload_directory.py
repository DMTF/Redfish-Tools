# Copyright Notice:
# Copyright 2019-2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_payload_directory.py

Brief: test(s) for retrieving payload examples from the "payload_dir" option.
"""

import os
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator
from doc_gen_util import DocGenUtilities

testcase_path = os.path.join('tests', 'samples')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'uri_replacements': {},
    'payload_dir': os.path.join('tests', 'samples', 'payloads'),
    'profile': {},
    'escape_chars': [],

    'output_format': 'slate',
}


def test_payloads_read_directory():
    input_dir = os.path.abspath(testcase_path) # This test won't actually use the files in this directory.
    docGen = DocGenerator([ input_dir ], '/dev/null', base_config)

    expected_filenames = ['LogService-v1-example.json', 'ActionInfo-v1-example.json',
                              'Memory-v1-example.json']

    read_filenames = docGen.config['payloads'].keys()
    assert len(read_filenames) == 3
    for f in expected_filenames:
        assert f in read_filenames


def test_payloads_lookup():
    payload_name = DocGenUtilities.get_payload_name('LogService', '1.3.1')
    assert payload_name == 'LogService-v1-example.json'

    payload_name = DocGenUtilities.get_payload_name('LogService', '1.3.1', 'GoFish')
    assert payload_name == 'LogService-v1-action-GoFish.json'
