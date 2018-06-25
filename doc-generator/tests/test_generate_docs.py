# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_generate_docs.py

Brief: These are nearly full-process integration tests (albeit without network calls).
The DocGenerator.generate_docs method produces a block of documentation (a string).
Each test here illustrates what should be output based on a specific set of JSON inputs.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'generate_docs_cases')
cases = {
    # each "case" directory will have subdirectories "input", with json schemas,
    # and "expected_output," with md and HTML samples.
    'NetworkPort': 'simple',
}

@pytest.mark.filterwarnings("ignore:Unable to read")
@pytest.mark.filterwarnings("ignore:Unable to find data")
@pytest.mark.filterwarnings("ignore:Unable to retrieve data")
@patch('urllib.request') # patch request so we don't make HTTP requests.
def test_all_cases(mockRequest):

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
    }

    html_config = copy.deepcopy(base_config)
    html_config['output_format'] = 'html'

    markdown_config = copy.deepcopy(base_config)
    markdown_config['output_format'] = 'markdown'

    for name, dirname in cases.items():
        dirpath = os.path.abspath(os.path.join(testcase_path, dirname))
        input_dir = os.path.join(dirpath, 'input')

        html_config['uri_to_local'] = markdown_config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
        html_config['local_to_uri'] = markdown_config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

        # HTML output
        expected_output = open(os.path.join(dirpath, 'expected_output', 'index.html')).read().strip()

        docGen = DocGenerator([ dirpath ], '/dev/null', html_config)
        output = docGen.generate_docs()
        output = output.strip()

        assert output == expected_output

        # markdown output
        expected_output = open(os.path.join(dirpath, 'expected_output', 'output.md')).read().strip()

        docGen = DocGenerator([ dirpath ], '/dev/null', markdown_config)
        output = docGen.generate_docs()
        output = output.strip()

        assert output == expected_output
