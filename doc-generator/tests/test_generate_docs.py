# Copyright Notice:
# Copyright 2018-2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_generate_docs.py

Brief: These are nearly full-process integration tests (albeit without network calls).
The DocGenerator.generate_docs method produces a block of documentation (a string).
Each test here illustrates what should be output based on a specific set of JSON inputs.

These tests will likely need to be updated frequently, as they expect an exact match on a
complete output document for a small schema set.
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
    'integer': 'Integer Support',
    'required': 'required and requiredOnCreate',
    'general': 'Example from NetworkPort',
}

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

def _strip_styles(htmlstring):
    """ Return a copy of htmlstring with the <style>...</style> block stripped out.

    The <style> block is boilerplate, we don't test it, and it gets tweaked periodically.
    We know there is just one <style> block, so we can keep this simple.
    """
    if '<style>' in htmlstring:
        startblock = htmlstring.find('<style>')
        endblock = htmlstring.find('</style>') + len('</style>')
        return htmlstring[0:startblock] + htmlstring[endblock:]
    else:
        return htmlstring


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_html_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'

    for dirname, name in cases.items():
        dirpath = os.path.abspath(os.path.join(testcase_path, dirname))
        input_dir = os.path.join(dirpath, 'input')

        config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
        config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

        expected_output = open(os.path.join(dirpath, 'expected_output', 'index.html')).read().strip()

        docGen = DocGenerator([ input_dir ], '/dev/null', config)
        output = docGen.generate_docs()
        output = output.strip()

        expected_output = _strip_styles(expected_output)
        output = _strip_styles(output)

        assert output == expected_output, "Failed on: " + name


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_markdown_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'markdown'

    for dirname, name in cases.items():
        dirpath = os.path.abspath(os.path.join(testcase_path, dirname))
        input_dir = os.path.join(dirpath, 'input')

        config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
        config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

        expected_output = open(os.path.join(dirpath, 'expected_output', 'markdown_output.md')).read().strip()

        docGen = DocGenerator([ input_dir ], '/dev/null', config)
        output = docGen.generate_docs()
        output = output.strip()

        assert output == expected_output, "Failed on: " + name


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_slate_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'slate'

    for dirname, name in cases.items():
        dirpath = os.path.abspath(os.path.join(testcase_path, dirname))
        input_dir = os.path.join(dirpath, 'input')

        config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
        config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

        expected_output = open(os.path.join(dirpath, 'expected_output', 'slate_output.md')).read().strip()

        docGen = DocGenerator([ input_dir ], '/dev/null', config)
        output = docGen.generate_docs()
        output = output.strip()

        assert output == expected_output, "Failed on: " + name


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_normative_html_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'
    config['normative'] = True

    dirname = 'normative'
    name = 'Normative'

    dirpath = os.path.abspath(os.path.join(testcase_path, dirname))
    input_dir = os.path.join(dirpath, 'input')

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    expected_output = open(os.path.join(dirpath, 'expected_output', 'index.html')).read().strip()

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    output = output.strip()

    expected_output = _strip_styles(expected_output)
    output = _strip_styles(output)

    assert output == expected_output, "Failed on: " + name


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_csv_output(mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'csv'

    dirname = 'general'
    name = 'CSV'

    dirpath = os.path.abspath(os.path.join(testcase_path, dirname))
    input_dir = os.path.join(dirpath, 'input')

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    expected_output = open(os.path.join(dirpath, 'expected_output', 'output.csv'), newline=None).read().strip()

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # "Universal newline" mode replaced '\r\n' with '\n' in the expected output.
    output = output.replace('\r\n', '\n').strip()

    assert output == expected_output, "Failed on: " + name
