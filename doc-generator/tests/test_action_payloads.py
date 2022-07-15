# Copyright Notice:
# Copyright 2021 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_action_payloads.py

Brief: Test for insertion of JSON payload examples (extracted from files) for
Action requests/responses.

The doc generator should look for specially-named files in the
payload_dir provided by the user.

Action request:  <schema name>-v<major>-<action name>-request-example.json
Action response: <schema name>-v<major>-<action name>-response-example.json

In the examples here, these are:

  CertificateService-v1-GenerateCSR-request-example.json
  CertificateService-v1-GenerateCSR-response-example.json

These are to be inserted as code blocks in the output, following the
"Response Payload" section under an action's details, and headed
"Request Example", "Response Example".
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'action_payloads', 'input')
input_dir = os.path.abspath(os.path.join(testcase_path, 'json-schema'))
payload_dir = os.path.abspath(os.path.join(testcase_path, 'mockups'))
output_dir = os.path.abspath(os.path.join('tests', 'samples', 'action_payloads', 'expected_output'))

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
    'payload_dir': payload_dir,
    'uri_to_local': {'redfish.dmtf.org/schemas/v1': input_dir},
    'local_to_uri': { input_dir : 'redfish.dmtf.org/schemas/v1'},
}

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_html_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # This test used to compare a snippet, but with Pygments involved, the test became fragile.
    assert 'Placeholder for REQUEST' in output
    assert 'Placeholder for RESPONSE' in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_markdown_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'markdown'

    expected_output = open(os.path.join(output_dir, 'markdown.md')).read().strip()

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    assert expected_output in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_slate_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'slate'

    expected_output = open(os.path.join(output_dir, 'slate.md')).read().strip()

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    assert expected_output in output
